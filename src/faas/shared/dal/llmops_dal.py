"""
LLMOps Data Access Layer (DAL)

Provides database abstraction for LLM operations logging and metrics.
Tables are assumed to exist (managed by migrations/DAL).
"""


import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from src.core.postgresql_database import DatabaseConnection 

logger = logging.getLogger(__name__)


class LLMOpsDAL:
    """
    Data Access Layer for LLM operations persistence.

    Handles all database operations for LLM operation logging and metrics.
    Tables are assumed to exist (managed by migrations/DAL).
    """

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize LLMOps DAL.

        Args:
            db_connection: Database connection instance.
        """
        self.db = db_connection

    async def save_operation(
        self,
        operation_id: str,
        operation_type: str,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        latency_ms: float = 0.0,
        cost_usd: float = 0.0,
        status: str = "success",
        error_message: Optional[str] = None,
        tenant_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Save LLM operation to database.

        Args:
            operation_id: Operation identifier.
            operation_type: Type of operation (completion, embedding, chat, etc.).
            model: Model name or identifier.
            prompt_tokens: Number of prompt tokens.
            completion_tokens: Number of completion tokens.
            total_tokens: Total tokens used.
            latency_ms: Operation latency in milliseconds.
            cost_usd: Operation cost in USD.
            status: Operation status (success, error, etc.).
            error_message: Optional error message.
            tenant_id: Tenant identifier for tenant isolation.
            agent_id: Optional agent identifier.
            metadata: Optional operation metadata.

        Returns:
            str: Operation record ID.
        """
        query = """
        INSERT INTO llm_operations (
            operation_id, operation_type, model, prompt_tokens, completion_tokens,
            total_tokens, latency_ms, cost_usd, status, error_message,
            tenant_id, agent_id, metadata, created_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13::jsonb, $14)
        RETURNING id;
        """

        metadata_json = json.dumps(metadata or {})
        now = datetime.now(timezone.utc)

        result = await self.db.execute_query(
            query,
            params=(
                operation_id,
                operation_type,
                model,
                prompt_tokens,
                completion_tokens,
                total_tokens,
                latency_ms,
                cost_usd,
                status,
                error_message,
                tenant_id,
                agent_id,
                metadata_json,
                now,
            ),
            fetch_one=True,
        )

        return str(result["id"]) if result else ""

    async def get_operations(
        self,
        tenant_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        time_range_hours: Optional[int] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get LLM operations with filters.

        Args:
            tenant_id: Tenant identifier for tenant isolation.
            agent_id: Optional agent identifier filter.
            time_range_hours: Optional time range in hours.
            limit: Maximum number of operations to return.
            offset: Number of operations to skip.

        Returns:
            List[Dict[str, Any]]: List of operation dictionaries.
        """
        query = """
        SELECT * FROM llm_operations
        WHERE 1=1
        """
        params: List[Any] = []

        if tenant_id:
            query += f" AND tenant_id = ${len(params) + 1}"
            params.append(tenant_id)

        if agent_id:
            query += f" AND agent_id = ${len(params) + 1}"
            params.append(agent_id)

        if time_range_hours:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=time_range_hours)
            query += f" AND created_at >= ${len(params) + 1}"
            params.append(cutoff)

        query += f" ORDER BY created_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
        params.extend([limit, offset])

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        # Parse JSON metadata for each result
        if results:
            for result in results:
                if result.get("metadata"):
                    result["metadata"] = (
                        json.loads(result["metadata"])
                        if isinstance(result["metadata"], str)
                        else result["metadata"]
                    )

        return results if results else []

    async def get_metrics(
        self,
        tenant_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        time_range_hours: Optional[int] = 24,
    ) -> Dict[str, Any]:
        """
        Get LLM operation metrics.

        Args:
            tenant_id: Tenant identifier for tenant isolation.
            agent_id: Optional agent identifier filter.
            time_range_hours: Time range in hours (default: 24).

        Returns:
            Dict[str, Any]: Metrics dictionary.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=time_range_hours or 24)

        query = """
        SELECT 
            COUNT(*) as total_operations,
            SUM(total_tokens) as total_tokens,
            SUM(cost_usd) as total_cost_usd,
            AVG(latency_ms) as average_latency_ms,
            COUNT(CASE WHEN status = 'success' THEN 1 END) as success_count,
            COUNT(CASE WHEN status = 'error' THEN 1 END) as error_count
        FROM llm_operations
        WHERE created_at >= $1
        """
        params: List[Any] = [cutoff]

        if tenant_id:
            query += f" AND tenant_id = ${len(params) + 1}"
            params.append(tenant_id)

        if agent_id:
            query += f" AND agent_id = ${len(params) + 1}"
            params.append(agent_id)

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_one=True,
        )

        if not result or result.get("total_operations", 0) == 0:
            return {
                "total_operations": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "average_latency_ms": 0.0,
                "success_rate": 0.0,
                "error_rate": 0.0,
                "by_model": {},
                "by_type": {},
            }

        total_operations = result.get("total_operations", 0)
        total_tokens = result.get("total_tokens", 0) or 0
        total_cost = result.get("total_cost_usd", 0.0) or 0.0
        avg_latency = result.get("average_latency_ms", 0.0) or 0.0
        success_count = result.get("success_count", 0) or 0
        error_count = result.get("error_count", 0) or 0

        success_rate = success_count / total_operations if total_operations > 0 else 0.0
        error_rate = error_count / total_operations if total_operations > 0 else 0.0

        # Get metrics by model
        by_model_query = """
        SELECT 
            model,
            COUNT(*) as count,
            SUM(total_tokens) as tokens,
            SUM(cost_usd) as cost_usd,
            AVG(latency_ms) as avg_latency_ms
        FROM llm_operations
        WHERE created_at >= $1
        """
        by_model_params: List[Any] = [cutoff]

        if tenant_id:
            by_model_query += f" AND tenant_id = ${len(by_model_params) + 1}"
            by_model_params.append(tenant_id)

        if agent_id:
            by_model_query += f" AND agent_id = ${len(by_model_params) + 1}"
            by_model_params.append(agent_id)

        by_model_query += " GROUP BY model"

        by_model_results = await self.db.execute_query(
            by_model_query,
            params=tuple(by_model_params),
            fetch_all=True,
        )

        by_model = {}
        if by_model_results:
            for row in by_model_results:
                by_model[row["model"]] = {
                    "count": row.get("count", 0),
                    "tokens": row.get("tokens", 0) or 0,
                    "cost_usd": row.get("cost_usd", 0.0) or 0.0,
                    "avg_latency_ms": row.get("avg_latency_ms", 0.0) or 0.0,
                }

        # Get metrics by type
        by_type_query = """
        SELECT 
            operation_type,
            COUNT(*) as count,
            SUM(total_tokens) as tokens
        FROM llm_operations
        WHERE created_at >= $1
        """
        by_type_params: List[Any] = [cutoff]

        if tenant_id:
            by_type_query += f" AND tenant_id = ${len(by_type_params) + 1}"
            by_type_params.append(tenant_id)

        if agent_id:
            by_type_query += f" AND agent_id = ${len(by_type_params) + 1}"
            by_type_params.append(agent_id)

        by_type_query += " GROUP BY operation_type"

        by_type_results = await self.db.execute_query(
            by_type_query,
            params=tuple(by_type_params),
            fetch_all=True,
        )

        by_type = {}
        if by_type_results:
            for row in by_type_results:
                by_type[row["operation_type"]] = {
                    "count": row.get("count", 0),
                    "tokens": row.get("tokens", 0) or 0,
                }

        return {
            "total_operations": total_operations,
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost,
            "average_latency_ms": avg_latency,
            "success_rate": success_rate,
            "error_rate": error_rate,
            "by_model": by_model,
            "by_type": by_type,
        }

    async def get_cost_analysis(
        self,
        tenant_id: Optional[str] = None,
        time_range_hours: Optional[int] = 30 * 24,  # 30 days default
    ) -> Dict[str, Any]:
        """
        Get cost analysis for LLM operations.

        Args:
            tenant_id: Tenant identifier for tenant isolation.
            time_range_hours: Time range in hours (default: 30 days).

        Returns:
            Dict[str, Any]: Cost analysis dictionary.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=time_range_hours or (30 * 24))

        query = """
        SELECT 
            SUM(cost_usd) as total_cost,
            AVG(cost_usd) as avg_cost_per_operation,
            model,
            COUNT(*) as operation_count
        FROM llm_operations
        WHERE created_at >= $1
        """
        params: List[Any] = [cutoff]

        if tenant_id:
            query += f" AND tenant_id = ${len(params) + 1}"
            params.append(tenant_id)

        query += " GROUP BY model ORDER BY total_cost DESC"

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        total_cost = sum(row.get("total_cost", 0.0) or 0.0 for row in results) if results else 0.0

        by_model = {}
        if results:
            for row in results:
                by_model[row["model"]] = {
                    "total_cost": row.get("total_cost", 0.0) or 0.0,
                    "avg_cost_per_operation": row.get("avg_cost_per_operation", 0.0) or 0.0,
                    "operation_count": row.get("operation_count", 0),
                }

        return {
            "total_cost_usd": total_cost,
            "by_model": by_model,
            "time_range_hours": time_range_hours or (30 * 24),
        }

    async def delete_old_operations(
        self,
        tenant_id: Optional[str] = None,
        older_than_days: int = 90,
    ) -> int:
        """
        Delete old operations.

        Args:
            tenant_id: Tenant identifier for tenant isolation.
            older_than_days: Delete operations older than this many days.

        Returns:
            int: Number of operations deleted.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)

        query = """
        DELETE FROM llm_operations
        WHERE created_at < $1
        """
        params: List[Any] = [cutoff]

        if tenant_id:
            query += f" AND tenant_id = ${len(params) + 1}"
            params.append(tenant_id)

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=False,
        )

        return result if result else 0

    async def get_operation(
        self, operation_id: str, tenant_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a single operation by ID.

        Args:
            operation_id: Operation identifier.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            Optional[Dict[str, Any]]: Operation data if found, else None.
        """
        query = """
        SELECT * FROM llm_operations
        WHERE operation_id = $1
        """
        params: List[Any] = [operation_id]

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

        # Parse JSON metadata
        if result.get("metadata"):
            result["metadata"] = (
                json.loads(result["metadata"])
                if isinstance(result["metadata"], str)
                else result["metadata"]
            )

        return result

