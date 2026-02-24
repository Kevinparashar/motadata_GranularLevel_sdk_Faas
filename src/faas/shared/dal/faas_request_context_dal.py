"""
Data Access Layer for FaaS Request Context.

Abstracts all database operations for cross-service request context persistence.
Tables are assumed to exist (managed by migrations/DAL).
"""


import json
import logging
from typing import Any, Dict, List, Optional

from src.core.postgresql_database import DatabaseConnection

logger = logging.getLogger(__name__)


class FaaSRequestContextDAL:
    """Data Access Layer for FaaS request context and service call chain persistence."""

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize FaaSRequestContextDAL.

        Args:
            db_connection: Database connection instance.
        """
        self.db = db_connection

    async def save_service_call(
        self,
        service_name: str,
        endpoint: str,
        method: str,  # "GET", "POST", "PUT", "DELETE"
        correlation_id: str,
        request_id: str,
        parent_request_id: Optional[str] = None,
        parent_service: Optional[str] = None,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status_code: Optional[int] = None,
        status: str = "success",  # "success", "error", "timeout"
        error_message: Optional[str] = None,
        latency_ms: Optional[float] = None,
        request_data: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        context_state: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Save service call to context history.

        Args:
            service_name: Name of the service.
            endpoint: API endpoint called.
            method: HTTP method.
            correlation_id: Correlation identifier for request tracking.
            request_id: Unique request identifier.
            parent_request_id: Optional parent request ID (for call chains).
            parent_service: Optional parent service name.
            tenant_id: Tenant identifier for tenant isolation.
            user_id: Optional user identifier.
            status_code: Optional HTTP status code.
            status: Request status (success, error, timeout).
            error_message: Optional error message.
            latency_ms: Request latency in milliseconds.
            request_data: Optional request payload.
            response_data: Optional response payload.
            context_state: Optional service-specific context state.
            metadata: Optional metadata.

        Returns:
            Service call record ID.
        """
        result = await self.db.execute_query(
            """
            INSERT INTO faas_request_context (
                service_name, endpoint, method, correlation_id, request_id,
                parent_request_id, parent_service, tenant_id, user_id,
                status_code, status, error_message, latency_ms, request_data,
                response_data, context_state, metadata, created_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,
                $14::jsonb, $15::jsonb, $16::jsonb, $17::jsonb, CURRENT_TIMESTAMP
            )
            RETURNING request_id;
            """,
            params=(
                service_name,
                endpoint,
                method,
                correlation_id,
                request_id,
                parent_request_id,
                parent_service,
                tenant_id,
                user_id,
                status_code,
                status,
                error_message,
                latency_ms,
                json.dumps(request_data) if request_data else None,
                json.dumps(response_data) if response_data else None,
                json.dumps(context_state) if context_state else None,
                json.dumps(metadata or {}),
            ),
            fetch_one=True,
        )
        return str(result["request_id"]) if result else request_id

    async def get_service_call_chain(
        self,
        correlation_id: str,
        tenant_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get complete service call chain for a correlation ID.

        Args:
            correlation_id: Correlation identifier.
            tenant_id: Optional tenant identifier.

        Returns:
            List of service calls in the chain, ordered by creation time.
        """
        query = """
        SELECT 
            service_name, endpoint, method, correlation_id, request_id,
            parent_request_id, parent_service, tenant_id, user_id,
            status_code, status, error_message, latency_ms, request_data,
            response_data, context_state, metadata, created_at
        FROM faas_request_context
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
                if record.get("request_data"):
                    record["request_data"] = (
                        json.loads(record["request_data"])
                        if isinstance(record["request_data"], str)
                        else record["request_data"]
                    )
                if record.get("response_data"):
                    record["response_data"] = (
                        json.loads(record["response_data"])
                        if isinstance(record["response_data"], str)
                        else record["response_data"]
                    )
                if record.get("context_state"):
                    record["context_state"] = (
                        json.loads(record["context_state"])
                        if isinstance(record["context_state"], str)
                        else record["context_state"]
                    )
                if record.get("metadata"):
                    record["metadata"] = (
                        json.loads(record["metadata"])
                        if isinstance(record["metadata"], str)
                        else record["metadata"]
                    )
        return results if results else []

    async def get_request_by_id(
        self,
        request_id: str,
        tenant_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get service call by request ID.

        Args:
            request_id: Request identifier.
            tenant_id: Optional tenant identifier.

        Returns:
            Service call record or None.
        """
        query = """
        SELECT 
            service_name, endpoint, method, correlation_id, request_id,
            parent_request_id, parent_service, tenant_id, user_id,
            status_code, status, error_message, latency_ms, request_data,
            response_data, context_state, metadata, created_at
        FROM faas_request_context
        WHERE request_id = $1
        """
        params: List[Any] = [request_id]

        if tenant_id:
            query += " AND tenant_id = $2"
            params.append(tenant_id)

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_one=True,
        )

        if result:
            if result.get("request_data"):
                result["request_data"] = (
                    json.loads(result["request_data"])
                    if isinstance(result["request_data"], str)
                    else result["request_data"]
                )
            if result.get("response_data"):
                result["response_data"] = (
                    json.loads(result["response_data"])
                    if isinstance(result["response_data"], str)
                    else result["response_data"]
                )
            if result.get("context_state"):
                result["context_state"] = (
                    json.loads(result["context_state"])
                    if isinstance(result["context_state"], str)
                    else result["context_state"]
                )
            if result.get("metadata"):
                result["metadata"] = (
                    json.loads(result["metadata"])
                    if isinstance(result["metadata"], str)
                    else result["metadata"]
                )
        return result

    async def get_child_calls(
        self,
        parent_request_id: str,
        tenant_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all child service calls for a parent request.

        Args:
            parent_request_id: Parent request identifier.
            tenant_id: Optional tenant identifier.

        Returns:
            List of child service calls.
        """
        query = """
        SELECT 
            service_name, endpoint, method, correlation_id, request_id,
            parent_request_id, parent_service, tenant_id, user_id,
            status_code, status, error_message, latency_ms, request_data,
            response_data, context_state, metadata, created_at
        FROM faas_request_context
        WHERE parent_request_id = $1
        """
        params: List[Any] = [parent_request_id]

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
                if record.get("request_data"):
                    record["request_data"] = (
                        json.loads(record["request_data"])
                        if isinstance(record["request_data"], str)
                        else record["request_data"]
                    )
                if record.get("response_data"):
                    record["response_data"] = (
                        json.loads(record["response_data"])
                        if isinstance(record["response_data"], str)
                        else record["response_data"]
                    )
                if record.get("context_state"):
                    record["context_state"] = (
                        json.loads(record["context_state"])
                        if isinstance(record["context_state"], str)
                        else record["context_state"]
                    )
                if record.get("metadata"):
                    record["metadata"] = (
                        json.loads(record["metadata"])
                        if isinstance(record["metadata"], str)
                        else record["metadata"]
                    )
        return results if results else []

    async def get_service_history(
        self,
        service_name: Optional[str] = None,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get service call history.

        Args:
            service_name: Optional service name filter.
            tenant_id: Tenant identifier for tenant isolation.
            user_id: Optional user identifier.
            status: Optional status filter.
            limit: Maximum number of records to return.
            offset: Offset for pagination.

        Returns:
            List of service call records.
        """
        query = """
        SELECT 
            service_name, endpoint, method, correlation_id, request_id,
            parent_request_id, parent_service, tenant_id, user_id,
            status_code, status, error_message, latency_ms, request_data,
            response_data, context_state, metadata, created_at
        FROM faas_request_context
        WHERE 1=1
        """
        params: List[Any] = []
        param_count = 0

        if service_name:
            param_count += 1
            query += f" AND service_name = ${param_count}"
            params.append(service_name)
        if tenant_id:
            param_count += 1
            query += f" AND tenant_id = ${param_count}"
            params.append(tenant_id)
        if user_id:
            param_count += 1
            query += f" AND user_id = ${param_count}"
            params.append(user_id)
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
                if record.get("request_data"):
                    record["request_data"] = (
                        json.loads(record["request_data"])
                        if isinstance(record["request_data"], str)
                        else record["request_data"]
                    )
                if record.get("response_data"):
                    record["response_data"] = (
                        json.loads(record["response_data"])
                        if isinstance(record["response_data"], str)
                        else record["response_data"]
                    )
                if record.get("context_state"):
                    record["context_state"] = (
                        json.loads(record["context_state"])
                        if isinstance(record["context_state"], str)
                        else record["context_state"]
                    )
                if record.get("metadata"):
                    record["metadata"] = (
                        json.loads(record["metadata"])
                        if isinstance(record["metadata"], str)
                        else record["metadata"]
                    )
        return results if results else []

    async def get_service_call_stats(
        self,
        service_name: Optional[str] = None,
        tenant_id: Optional[str] = None,
        time_range_hours: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get service call statistics.

        Args:
            service_name: Optional service name filter.
            tenant_id: Tenant identifier for tenant isolation.
            time_range_hours: Optional time range in hours.

        Returns:
            Dictionary with service call statistics.
        """
        query = """
        SELECT 
            COUNT(*) as total_calls,
            COUNT(DISTINCT correlation_id) as unique_correlations,
            COUNT(DISTINCT service_name) as unique_services,
            COUNT(CASE WHEN status = 'success' THEN 1 END) as success_calls,
            COUNT(CASE WHEN status = 'error' THEN 1 END) as error_calls,
            COUNT(CASE WHEN parent_request_id IS NOT NULL THEN 1 END) as child_calls,
            AVG(latency_ms) as avg_latency_ms,
            MAX(latency_ms) as max_latency_ms,
            MIN(latency_ms) as min_latency_ms
        FROM faas_request_context
        WHERE 1=1
        """
        params: List[Any] = []
        param_count = 0

        if service_name:
            param_count += 1
            query += f" AND service_name = ${param_count}"
            params.append(service_name)
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
            total = result.get("total_calls", 0) or 0
            successes = result.get("success_calls", 0) or 0
            errors = result.get("error_calls", 0) or 0

            return {
                "total_calls": total,
                "unique_correlations": result.get("unique_correlations", 0) or 0,
                "unique_services": result.get("unique_services", 0) or 0,
                "success_calls": successes,
                "error_calls": errors,
                "success_rate": (successes / total * 100) if total > 0 else 0.0,
                "error_rate": (errors / total * 100) if total > 0 else 0.0,
                "child_calls": result.get("child_calls", 0) or 0,
                "avg_latency_ms": float(result.get("avg_latency_ms", 0) or 0),
                "max_latency_ms": float(result.get("max_latency_ms", 0) or 0),
                "min_latency_ms": float(result.get("min_latency_ms", 0) or 0),
            }
        return {
            "total_calls": 0,
            "unique_correlations": 0,
            "unique_services": 0,
            "success_calls": 0,
            "error_calls": 0,
            "success_rate": 0.0,
            "error_rate": 0.0,
            "child_calls": 0,
            "avg_latency_ms": 0.0,
            "max_latency_ms": 0.0,
            "min_latency_ms": 0.0,
        }

    async def get_service_dependency_graph(
        self,
        correlation_id: str,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get service dependency graph for a correlation ID.

        Args:
            correlation_id: Correlation identifier.
            tenant_id: Optional tenant identifier.

        Returns:
            Dictionary representing the service call dependency graph.
        """
        calls = await self.get_service_call_chain(correlation_id, tenant_id=tenant_id)

        # Build graph structure
        graph = {
            "correlation_id": correlation_id,
            "services": {},
            "edges": [],
            "root_requests": [],
        }

        # Index all calls by request_id
        call_index: Dict[str, Dict[str, Any]] = {}
        for call in calls:
            call_index[call["request_id"]] = call

        # Build graph
        for call in calls:
            service_name = call["service_name"]
            request_id = call["request_id"]
            parent_request_id = call.get("parent_request_id")

            # Add service node
            if service_name not in graph["services"]:
                graph["services"][service_name] = {
                    "calls": [],
                    "total_calls": 0,
                    "success_calls": 0,
                    "error_calls": 0,
                }

            graph["services"][service_name]["calls"].append(request_id)
            graph["services"][service_name]["total_calls"] += 1
            if call.get("status") == "success":
                graph["services"][service_name]["success_calls"] += 1
            elif call.get("status") == "error":
                graph["services"][service_name]["error_calls"] += 1

            # Add edge if has parent
            if parent_request_id:
                parent_call = call_index.get(parent_request_id)
                if parent_call:
                    graph["edges"].append({
                        "from": parent_call["service_name"],
                        "to": service_name,
                        "from_request_id": parent_request_id,
                        "to_request_id": request_id,
                    })
            else:
                # Root request
                graph["root_requests"].append({
                    "service": service_name,
                    "request_id": request_id,
                })

        return graph

    async def cleanup_old_context(
        self,
        days: int = 90,
        tenant_id: Optional[str] = None,
    ) -> int:
        """
        Clean up old request context records.

        Args:
            days: Number of days to keep (delete older records).
            tenant_id: Optional tenant identifier.

        Returns:
            Number of records deleted.
        """
        query = """
        DELETE FROM faas_request_context
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

