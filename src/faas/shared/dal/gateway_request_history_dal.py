"""
Data Access Layer for Gateway Request History.

Abstracts all database operations for gateway request/response history persistence.
Tables are assumed to exist (managed by migrations/DAL).
"""


import json
import logging
from typing import Any, Dict, List, Optional

from src.core.postgresql_database import DatabaseConnection

logger = logging.getLogger(__name__)


class GatewayRequestHistoryDAL:
    """Data Access Layer for gateway request/response history persistence."""

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize GatewayRequestHistoryDAL.

        Args:
            db_connection: Database connection instance.
        """
        self.db = db_connection

    async def save_request(
        self,
        request_id: str,
        operation_type: str,  # "generate", "embed"
        model: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        session_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        response_text: Optional[str] = None,
        response_data: Optional[Dict[str, Any]] = None,
        usage: Optional[Dict[str, Any]] = None,
        latency_ms: Optional[float] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        error_type: Optional[str] = None,
        retry_count: int = 0,
        fallback_used: bool = False,
        fallback_model: Optional[str] = None,
        cache_hit: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Save gateway request/response to history.

        Args:
            request_id: Unique request identifier.
            operation_type: Operation type (generate, embed).
            model: Model name used.
            tenant_id: Tenant identifier for tenant isolation.
            user_id: Optional user identifier.
            conversation_id: Optional conversation identifier.
            session_id: Optional session identifier.
            correlation_id: Optional correlation ID for request tracking.
            prompt: Optional prompt text.
            messages: Optional chat messages.
            response_text: Optional response text.
            response_data: Optional full response data.
            usage: Optional token usage information.
            latency_ms: Request latency in milliseconds.
            status: Request status (success, error, timeout).
            error_message: Optional error message.
            error_type: Optional error type.
            retry_count: Number of retries attempted.
            fallback_used: Whether fallback model was used.
            fallback_model: Optional fallback model name.
            cache_hit: Whether response was from cache.
            metadata: Optional metadata.

        Returns:
            Request record ID.
        """
        result = await self.db.execute_query(
            """
            INSERT INTO gateway_request_history (
                request_id, operation_type, model, tenant_id, user_id,
                conversation_id, session_id, correlation_id, prompt, messages,
                response_text, response_data, usage, latency_ms, status,
                error_message, error_type, retry_count, fallback_used,
                fallback_model, cache_hit, metadata, created_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb,
                $11, $12::jsonb, $13::jsonb, $14, $15, $16, $17, $18, $19,
                $20, $21, $22::jsonb, CURRENT_TIMESTAMP
            )
            RETURNING request_id;
            """,
            params=(
                request_id,
                operation_type,
                model,
                tenant_id,
                user_id,
                conversation_id,
                session_id,
                correlation_id,
                prompt,
                json.dumps(messages) if messages else None,
                response_text,
                json.dumps(response_data) if response_data else None,
                json.dumps(usage) if usage else None,
                latency_ms,
                status,
                error_message,
                error_type,
                retry_count,
                fallback_used,
                fallback_model,
                cache_hit,
                json.dumps(metadata or {}),
            ),
            fetch_one=True,
        )
        return str(result["request_id"]) if result else request_id

    async def get_request_history(
        self,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        operation_type: Optional[str] = None,
        model: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get gateway request history.

        Args:
            tenant_id: Tenant identifier for tenant isolation.
            user_id: Optional user identifier.
            conversation_id: Optional conversation identifier.
            operation_type: Optional operation type filter.
            model: Optional model filter.
            status: Optional status filter.
            limit: Maximum number of records to return.
            offset: Offset for pagination.

        Returns:
            List of request history records.
        """
        query = """
        SELECT 
            request_id, operation_type, model, tenant_id, user_id,
            conversation_id, session_id, correlation_id, prompt, messages,
            response_text, response_data, usage, latency_ms, status,
            error_message, error_type, retry_count, fallback_used,
            fallback_model, cache_hit, metadata, created_at
        FROM gateway_request_history
        WHERE 1=1
        """
        params: List[Any] = []
        param_count = 0

        if tenant_id:
            param_count += 1
            query += f" AND tenant_id = ${param_count}"
            params.append(tenant_id)
        if user_id:
            param_count += 1
            query += f" AND user_id = ${param_count}"
            params.append(user_id)
        if conversation_id:
            param_count += 1
            query += f" AND conversation_id = ${param_count}"
            params.append(conversation_id)
        if operation_type:
            param_count += 1
            query += f" AND operation_type = ${param_count}"
            params.append(operation_type)
        if model:
            param_count += 1
            query += f" AND model = ${param_count}"
            params.append(model)
        if status:
            param_count += 1
            query += f" AND status = ${param_count}"
            params.append(status)

        query += f" ORDER BY created_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
        params.extend([limit, offset])

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        if results:
            for record in results:
                if record.get("messages"):
                    record["messages"] = (
                        json.loads(record["messages"])
                        if isinstance(record["messages"], str)
                        else record["messages"]
                    )
                if record.get("response_data"):
                    record["response_data"] = (
                        json.loads(record["response_data"])
                        if isinstance(record["response_data"], str)
                        else record["response_data"]
                    )
                if record.get("usage"):
                    record["usage"] = (
                        json.loads(record["usage"])
                        if isinstance(record["usage"], str)
                        else record["usage"]
                    )
                if record.get("metadata"):
                    record["metadata"] = (
                        json.loads(record["metadata"])
                        if isinstance(record["metadata"], str)
                        else record["metadata"]
                    )
        return results if results else []

    async def get_request_by_correlation_id(
        self,
        correlation_id: str,
        tenant_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get requests by correlation ID.

        Args:
            correlation_id: Correlation identifier.
            tenant_id: Optional tenant identifier.

        Returns:
            List of request records with the same correlation ID.
        """
        query = """
        SELECT 
            request_id, operation_type, model, tenant_id, user_id,
            conversation_id, session_id, correlation_id, prompt, messages,
            response_text, response_data, usage, latency_ms, status,
            error_message, error_type, retry_count, fallback_used,
            fallback_model, cache_hit, metadata, created_at
        FROM gateway_request_history
        WHERE correlation_id = $1
        """
        params: List[Any] = [correlation_id]

        if tenant_id:
            query += " AND tenant_id = $2"
            params.append(tenant_id)

        query += " ORDER BY created_at ASC"

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        if results:
            for record in results:
                if record.get("messages"):
                    record["messages"] = (
                        json.loads(record["messages"])
                        if isinstance(record["messages"], str)
                        else record["messages"]
                    )
                if record.get("response_data"):
                    record["response_data"] = (
                        json.loads(record["response_data"])
                        if isinstance(record["response_data"], str)
                        else record["response_data"]
                    )
                if record.get("usage"):
                    record["usage"] = (
                        json.loads(record["usage"])
                        if isinstance(record["usage"], str)
                        else record["usage"]
                    )
                if record.get("metadata"):
                    record["metadata"] = (
                        json.loads(record["metadata"])
                        if isinstance(record["metadata"], str)
                        else record["metadata"]
                    )
        return results if results else []

    async def get_model_selection_patterns(
        self,
        tenant_id: Optional[str] = None,
        time_range_hours: Optional[int] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Get model selection patterns and usage statistics.

        Args:
            tenant_id: Tenant identifier for tenant isolation.
            time_range_hours: Optional time range in hours.
            limit: Maximum number of patterns to return.

        Returns:
            List of model selection patterns.
        """
        query = """
        SELECT 
            model,
            operation_type,
            COUNT(*) as request_count,
            COUNT(CASE WHEN status = 'success' THEN 1 END) as success_count,
            COUNT(CASE WHEN status = 'error' THEN 1 END) as error_count,
            AVG(latency_ms) as avg_latency_ms,
            COUNT(CASE WHEN fallback_used = true THEN 1 END) as fallback_count,
            COUNT(CASE WHEN cache_hit = true THEN 1 END) as cache_hit_count,
            AVG(retry_count) as avg_retry_count
        FROM gateway_request_history
        WHERE 1=1
        """
        params: List[Any] = []
        param_count = 0

        if tenant_id:
            param_count += 1
            query += f" AND tenant_id = ${param_count}"
            params.append(tenant_id)
        if time_range_hours:
            param_count += 1
            query += f" AND created_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour' * ${param_count}"
            params.append(time_range_hours)

        query += """
        GROUP BY model, operation_type
        ORDER BY request_count DESC
        LIMIT $%d
        """ % (param_count + 1)
        params.append(limit)

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        if results:
            for record in results:
                record["avg_latency_ms"] = float(record.get("avg_latency_ms", 0) or 0)
                record["avg_retry_count"] = float(record.get("avg_retry_count", 0) or 0)
                record["success_rate"] = (
                    (record["success_count"] / record["request_count"]) * 100
                    if record["request_count"] > 0
                    else 0.0
                )
        return results if results else []

    async def get_operation_context_stats(
        self,
        tenant_id: Optional[str] = None,
        time_range_hours: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get operation context statistics (retries, fallbacks, errors).

        Args:
            tenant_id: Tenant identifier for tenant isolation.
            time_range_hours: Optional time range in hours.

        Returns:
            Dictionary with operation context statistics.
        """
        query = """
        SELECT 
            COUNT(*) as total_requests,
            COUNT(CASE WHEN retry_count > 0 THEN 1 END) as requests_with_retries,
            AVG(retry_count) as avg_retry_count,
            MAX(retry_count) as max_retry_count,
            COUNT(CASE WHEN fallback_used = true THEN 1 END) as fallback_requests,
            COUNT(CASE WHEN status = 'error' THEN 1 END) as error_requests,
            COUNT(DISTINCT error_type) as unique_error_types,
            COUNT(CASE WHEN cache_hit = true THEN 1 END) as cache_hits,
            AVG(latency_ms) as avg_latency_ms
        FROM gateway_request_history
        WHERE 1=1
        """
        params: List[Any] = []
        param_count = 0

        if tenant_id:
            param_count += 1
            query += f" AND tenant_id = ${param_count}"
            params.append(tenant_id)
        if time_range_hours:
            param_count += 1
            query += f" AND created_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour' * ${param_count}"
            params.append(time_range_hours)

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_one=True,
        )

        if result:
            total = result.get("total_requests", 0) or 0
            retries = result.get("requests_with_retries", 0) or 0
            errors = result.get("error_requests", 0) or 0
            fallbacks = result.get("fallback_requests", 0) or 0

            return {
                "total_requests": total,
                "requests_with_retries": retries,
                "retry_rate": (retries / total * 100) if total > 0 else 0.0,
                "avg_retry_count": float(result.get("avg_retry_count", 0) or 0),
                "max_retry_count": result.get("max_retry_count", 0) or 0,
                "fallback_requests": fallbacks,
                "fallback_rate": (fallbacks / total * 100) if total > 0 else 0.0,
                "error_requests": errors,
                "error_rate": (errors / total * 100) if total > 0 else 0.0,
                "unique_error_types": result.get("unique_error_types", 0) or 0,
                "cache_hits": result.get("cache_hits", 0) or 0,
                "cache_hit_rate": (result.get("cache_hits", 0) or 0) / total * 100 if total > 0 else 0.0,
                "avg_latency_ms": float(result.get("avg_latency_ms", 0) or 0),
            }
        return {
            "total_requests": 0,
            "requests_with_retries": 0,
            "retry_rate": 0.0,
            "avg_retry_count": 0.0,
            "max_retry_count": 0,
            "fallback_requests": 0,
            "fallback_rate": 0.0,
            "error_requests": 0,
            "error_rate": 0.0,
            "unique_error_types": 0,
            "cache_hits": 0,
            "cache_hit_rate": 0.0,
            "avg_latency_ms": 0.0,
        }

    async def get_conversation_history(
        self,
        conversation_id: str,
        tenant_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history.

        Args:
            conversation_id: Conversation identifier.
            tenant_id: Optional tenant identifier.
            limit: Maximum number of records to return.

        Returns:
            List of request records for the conversation.
        """
        query = """
        SELECT 
            request_id, operation_type, model, tenant_id, user_id,
            conversation_id, session_id, correlation_id, prompt, messages,
            response_text, response_data, usage, latency_ms, status,
            error_message, error_type, retry_count, fallback_used,
            fallback_model, cache_hit, metadata, created_at
        FROM gateway_request_history
        WHERE conversation_id = $1
        """
        params: List[Any] = [conversation_id]

        if tenant_id:
            query += " AND tenant_id = $2"
            params.append(tenant_id)

        query += f" ORDER BY created_at ASC LIMIT ${len(params) + 1}"
        params.append(limit)

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        if results:
            for record in results:
                if record.get("messages"):
                    record["messages"] = (
                        json.loads(record["messages"])
                        if isinstance(record["messages"], str)
                        else record["messages"]
                    )
                if record.get("response_data"):
                    record["response_data"] = (
                        json.loads(record["response_data"])
                        if isinstance(record["response_data"], str)
                        else record["response_data"]
                    )
                if record.get("usage"):
                    record["usage"] = (
                        json.loads(record["usage"])
                        if isinstance(record["usage"], str)
                        else record["usage"]
                    )
                if record.get("metadata"):
                    record["metadata"] = (
                        json.loads(record["metadata"])
                        if isinstance(record["metadata"], str)
                        else record["metadata"]
                    )
        return results if results else []

    async def cleanup_old_history(
        self,
        days: int = 90,
        tenant_id: Optional[str] = None,
    ) -> int:
        """
        Clean up old request history records.

        Args:
            days: Number of days to keep (delete older records).
            tenant_id: Optional tenant identifier.

        Returns:
            Number of records deleted.
        """
        query = """
        DELETE FROM gateway_request_history
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

