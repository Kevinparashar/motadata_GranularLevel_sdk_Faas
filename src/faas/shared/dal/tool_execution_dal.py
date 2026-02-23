"""
Data Access Layer for Tool Executions.

Abstracts all database operations for tool execution history persistence.
"""


import json
import logging
from typing import Any, Dict, List, Optional

from src.core.postgresql_database import DatabaseConnection 

logger = logging.getLogger(__name__)


class ToolExecutionDAL:
    """Data Access Layer for tool execution history persistence."""

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize ToolExecutionDAL.

        Args:
            db_connection: Database connection instance.
        """
        self.db = db_connection

    async def save_execution(
        self,
        tool_id: str,
        agent_id: Optional[str] = None,
        arguments: Optional[Dict[str, Any]] = None,
        result: Optional[Any] = None,
        status: str = "success",
        error: Optional[str] = None,
        tenant_id: Optional[str] = None,
        execution_time_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Save tool execution to history.

        Args:
            tool_id: Tool identifier.
            agent_id: Optional agent identifier that executed the tool.
            arguments: Tool execution arguments.
            result: Tool execution result.
            status: Execution status (success, error, timeout).
            error: Optional error message.
            tenant_id: Tenant identifier for tenant isolation.
            execution_time_ms: Optional execution time in milliseconds.
            metadata: Optional execution metadata.

        Returns:
            Execution record ID.
        """
        # Serialize result if it's not a simple type
        result_json = None
        if result is not None:
            try:
                result_json = json.dumps(result) if not isinstance(result, (str, int, float, bool, type(None))) else result
            except (TypeError, ValueError):
                result_json = str(result)

        result = await self.db.execute_query(
            """
            INSERT INTO tool_executions (
                tool_id, agent_id, arguments, result, status, error,
                tenant_id, execution_time_ms, metadata, created_at
            ) VALUES ($1, $2, $3::jsonb, $4, $5, $6, $7, $8, $9::jsonb, CURRENT_TIMESTAMP)
            RETURNING id;
            """,
            params=(
                tool_id,
                agent_id,
                json.dumps(arguments or {}),
                result_json,
                status,
                error,
                tenant_id,
                execution_time_ms,
                json.dumps(metadata or {}),
            ),
            fetch_one=True,
        )
        return str(result["id"])

    async def get_executions(
        self,
        tool_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get tool execution history.

        Args:
            tool_id: Optional tool identifier filter.
            agent_id: Optional agent identifier filter.
            tenant_id: Tenant identifier for tenant isolation.
            status: Optional status filter (success, error, timeout).
            limit: Maximum number of records to return.
            offset: Offset for pagination.

        Returns:
            List of execution records.
        """
        query = """
        SELECT id, tool_id, agent_id, arguments, result, status, error,
               execution_time_ms, metadata, created_at
        FROM tool_executions
        WHERE 1=1
        """
        params: List[Any] = []
        if tool_id:
            query += f" AND tool_id = ${len(params) + 1}"
            params.append(tool_id)
        if agent_id:
            query += f" AND agent_id = ${len(params) + 1}"
            params.append(agent_id)
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

        if results:
            for record in results:
                if record.get("arguments"):
                    record["arguments"] = (
                        json.loads(record["arguments"])
                        if isinstance(record["arguments"], str)
                        else record["arguments"]
                    )
                if record.get("metadata"):
                    record["metadata"] = (
                        json.loads(record["metadata"])
                        if isinstance(record["metadata"], str)
                        else record["metadata"]
                    )
                # Try to parse result if it's JSON
                if record.get("result") and isinstance(record["result"], str):
                    try:
                        record["result"] = json.loads(record["result"])
                    except (json.JSONDecodeError, TypeError):
                        pass  # Keep as string if not JSON
        return results if results else []

    async def cleanup_old_executions(
        self,
        days: int = 30,
        tenant_id: Optional[str] = None,
    ) -> int:
        """
        Clean up old tool execution records.

        Args:
            days: Number of days to keep (delete older records).
            tenant_id: Optional tenant identifier.

        Returns:
            Number of records deleted.
        """
        query = """
        DELETE FROM tool_executions
        WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
        """ % days
        params: List[Any] = []
        if tenant_id:
            query = query.replace("WHERE", "WHERE tenant_id = $1 AND")
            params.append(tenant_id)

        result = await self.db.execute_query(
            query,
            params=tuple(params) if params else None,
            fetch_all=False,
        )
        return result if result else 0

