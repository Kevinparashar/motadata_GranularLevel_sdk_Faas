"""
Data Access Layer for Workflows.

Abstracts all database operations for workflow state persistence.
"""


import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.core.postgresql_database import DatabaseConnection  

logger = logging.getLogger(__name__)


class WorkflowDAL:
    """Data Access Layer for workflow state persistence."""

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize WorkflowDAL.

        Args:
            db_connection: Database connection instance.
        """
        self.db = db_connection

    async def save_workflow_state(
        self,
        workflow_id: str,
        status: str,
        current_step: Optional[str] = None,
        completed_steps: Optional[List[str]] = None,
        failed_steps: Optional[List[str]] = None,
        step_results: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        tenant_id: Optional[str] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ) -> None:
        """
        Save workflow state to database.

        Args:
            workflow_id: Workflow identifier.
            status: Workflow status (pending, running, completed, failed, cancelled, paused).
            current_step: Optional current step identifier.
            completed_steps: List of completed step IDs.
            failed_steps: List of failed step IDs.
            step_results: Dictionary of step results.
            context: Workflow context variables.
            error: Optional error message.
            tenant_id: Tenant identifier for tenant isolation.
            started_at: Optional workflow start time.
            completed_at: Optional workflow completion time.
        """
        await self.db.execute_query(
            """
            INSERT INTO workflows (
                workflow_id, status, current_step, completed_steps, failed_steps,
                step_results, context, error, tenant_id, started_at, completed_at,
                created_at, updated_at
            ) VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6::jsonb, $7::jsonb, $8, $9, $10, $11, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (workflow_id, tenant_id) DO UPDATE SET
                status = EXCLUDED.status,
                current_step = EXCLUDED.current_step,
                completed_steps = EXCLUDED.completed_steps,
                failed_steps = EXCLUDED.failed_steps,
                step_results = EXCLUDED.step_results,
                context = EXCLUDED.context,
                error = EXCLUDED.error,
                started_at = EXCLUDED.started_at,
                completed_at = EXCLUDED.completed_at,
                updated_at = CURRENT_TIMESTAMP
            """,
            params=(
                workflow_id,
                status,
                current_step,
                json.dumps(completed_steps or []),
                json.dumps(failed_steps or []),
                json.dumps(step_results or {}),
                json.dumps(context or {}),
                error,
                tenant_id,
                started_at,
                completed_at,
            ),
            fetch_all=False,
        )

    async def load_workflow_state(
        self, workflow_id: str, tenant_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Load workflow state from database.

        Args:
            workflow_id: Workflow identifier.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            Workflow state data if found, else None.
        """
        query = """
        SELECT workflow_id, status, current_step, completed_steps, failed_steps,
               step_results, context, error, started_at, completed_at, created_at, updated_at
        FROM workflows
        WHERE workflow_id = $1
        """
        params: List[Any] = [workflow_id]
        if tenant_id:
            query += " AND tenant_id = $2"
            params.append(tenant_id)

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_one=True,
        )

        if not result:
            return None

        workflow = dict(result)
        # Parse JSON fields
        if workflow.get("completed_steps"):
            workflow["completed_steps"] = (
                json.loads(workflow["completed_steps"])
                if isinstance(workflow["completed_steps"], str)
                else workflow["completed_steps"]
            )
        if workflow.get("failed_steps"):
            workflow["failed_steps"] = (
                json.loads(workflow["failed_steps"])
                if isinstance(workflow["failed_steps"], str)
                else workflow["failed_steps"]
            )
        if workflow.get("step_results"):
            workflow["step_results"] = (
                json.loads(workflow["step_results"])
                if isinstance(workflow["step_results"], str)
                else workflow["step_results"]
            )
        if workflow.get("context"):
            workflow["context"] = (
                json.loads(workflow["context"])
                if isinstance(workflow["context"], str)
                else workflow["context"]
            )
        return workflow

    async def list_workflows(
        self,
        tenant_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List all workflows.

        Args:
            tenant_id: Tenant identifier for tenant isolation.
            status: Optional status filter.
            limit: Maximum number of workflows to return.
            offset: Offset for pagination.

        Returns:
            List of workflow dictionaries.
        """
        query = """
        SELECT workflow_id, status, current_step, error, started_at, completed_at, created_at, updated_at
        FROM workflows
        WHERE 1=1
        """
        params: List[Any] = []
        if tenant_id:
            query += f" AND tenant_id = ${len(params) + 1}"
            params.append(tenant_id)
        if status:
            query += f" AND status = ${len(params) + 1}"
            params.append(status)
        query += f" ORDER BY created_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
        params.extend([limit, offset])

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )
        return results if results else []

    async def delete_workflow(
        self, workflow_id: str, tenant_id: Optional[str] = None
    ) -> bool:
        """
        Delete workflow state.

        Args:
            workflow_id: Workflow identifier.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            True if deleted, False if not found.
        """
        query = """
        DELETE FROM workflows
        WHERE workflow_id = $1
        """
        params: List[Any] = [workflow_id]
        if tenant_id:
            query += " AND tenant_id = $2"
            params.append(tenant_id)

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=False,
        )
        return result > 0

    async def cleanup_old_workflows(
        self,
        days: int = 90,
        tenant_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> int:
        """
        Clean up old workflow records.

        Args:
            days: Number of days to keep (delete older records).
            tenant_id: Optional tenant identifier.
            status: Optional status filter (only delete workflows with this status).

        Returns:
            Number of records deleted.
        """
        query = """
        DELETE FROM workflows
        WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
        """ % days
        params: List[Any] = []
        if tenant_id:
            query = query.replace("WHERE", "WHERE tenant_id = $1 AND")
            params.append(tenant_id)
        if status:
            query += f" AND status = ${len(params) + 1}"
            params.append(status)

        result = await self.db.execute_query(
            query,
            params=tuple(params) if params else None,
            fetch_all=False,
        )
        return result if result else 0

