"""
Data Access Layer for OTEL Trace Context.

Abstracts all database operations for OpenTelemetry trace context persistence.
Tables are assumed to exist (managed by migrations/DAL).
"""


import json
import logging
from typing import Any, Dict, List, Optional

from src.core.postgresql_database import DatabaseConnection

logger = logging.getLogger(__name__)


class OTELTraceContextDAL:
    """Data Access Layer for OTEL trace context persistence."""

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize OTELTraceContextDAL.

        Args:
            db_connection: Database connection instance.
        """
        self.db = db_connection

    async def save_trace_context(
        self,
        trace_id: str,
        span_id: str,
        correlation_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        trace_flags: Optional[int] = None,
        trace_state: Optional[str] = None,
        baggage: Optional[Dict[str, str]] = None,
        service_name: Optional[str] = None,
        span_name: Optional[str] = None,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        operation_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Save trace context to persistence.

        Args:
            trace_id: OpenTelemetry trace ID.
            span_id: OpenTelemetry span ID.
            correlation_id: Optional correlation ID for cross-service correlation.
            parent_span_id: Optional parent span ID.
            trace_flags: Optional trace flags.
            trace_state: Optional trace state string.
            baggage: Optional baggage dictionary.
            service_name: Optional service name.
            span_name: Optional span name.
            tenant_id: Tenant identifier for tenant isolation.
            user_id: Optional user identifier.
            operation_name: Optional operation name.
            metadata: Optional metadata.

        Returns:
            Trace context record ID (trace_id).
        """
        result = await self.db.execute_query(
            """
            INSERT INTO otel_trace_context (
                trace_id, span_id, correlation_id, parent_span_id,
                trace_flags, trace_state, baggage, service_name,
                span_name, tenant_id, user_id, operation_name,
                metadata, created_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7::jsonb, $8, $9, $10, $11, $12,
                $13::jsonb, CURRENT_TIMESTAMP
            )
            ON CONFLICT (trace_id, span_id) DO UPDATE SET
                correlation_id = EXCLUDED.correlation_id,
                parent_span_id = EXCLUDED.parent_span_id,
                trace_flags = EXCLUDED.trace_flags,
                trace_state = EXCLUDED.trace_state,
                baggage = EXCLUDED.baggage,
                service_name = EXCLUDED.service_name,
                span_name = EXCLUDED.span_name,
                tenant_id = EXCLUDED.tenant_id,
                user_id = EXCLUDED.user_id,
                operation_name = EXCLUDED.operation_name,
                metadata = EXCLUDED.metadata,
                updated_at = CURRENT_TIMESTAMP
            RETURNING trace_id;
            """,
            params=(
                trace_id,
                span_id,
                correlation_id,
                parent_span_id,
                trace_flags,
                trace_state,
                json.dumps(baggage) if baggage else None,
                service_name,
                span_name,
                tenant_id,
                user_id,
                operation_name,
                json.dumps(metadata or {}),
            ),
            fetch_one=True,
        )
        return str(result["trace_id"]) if result else trace_id

    async def get_trace_context(
        self,
        trace_id: str,
        span_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get trace context by trace ID and optional span ID.

        Args:
            trace_id: OpenTelemetry trace ID.
            span_id: Optional span ID.
            tenant_id: Optional tenant identifier.

        Returns:
            Trace context record or None.
        """
        query = """
        SELECT 
            trace_id, span_id, correlation_id, parent_span_id,
            trace_flags, trace_state, baggage, service_name,
            span_name, tenant_id, user_id, operation_name,
            metadata, created_at, updated_at
        FROM otel_trace_context
        WHERE trace_id = $1
        """
        params: List[Any] = [trace_id]

        if span_id:
            query += " AND span_id = $2"
            params.append(span_id)
            param_count = 2
        else:
            param_count = 1

        if tenant_id:
            query += f" AND tenant_id = ${param_count + 1}"
            params.append(tenant_id)

        query += " ORDER BY created_at DESC LIMIT 1"

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_one=True,
        )

        if result:
            if result.get("baggage"):
                result["baggage"] = (
                    json.loads(result["baggage"])
                    if isinstance(result["baggage"], str)
                    else result["baggage"]
                )
            if result.get("metadata"):
                result["metadata"] = (
                    json.loads(result["metadata"])
                    if isinstance(result["metadata"], str)
                    else result["metadata"]
                )
        return result

    async def get_trace_by_correlation_id(
        self,
        correlation_id: str,
        tenant_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all traces for a correlation ID.

        Args:
            correlation_id: Correlation identifier.
            tenant_id: Optional tenant identifier.

        Returns:
            List of trace context records.
        """
        query = """
        SELECT 
            trace_id, span_id, correlation_id, parent_span_id,
            trace_flags, trace_state, baggage, service_name,
            span_name, tenant_id, user_id, operation_name,
            metadata, created_at, updated_at
        FROM otel_trace_context
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
                if record.get("baggage"):
                    record["baggage"] = (
                        json.loads(record["baggage"])
                        if isinstance(record["baggage"], str)
                        else record["baggage"]
                    )
                if record.get("metadata"):
                    record["metadata"] = (
                        json.loads(record["metadata"])
                        if isinstance(record["metadata"], str)
                        else record["metadata"]
                    )
        return results if results else []

    async def get_trace_chain(
        self,
        trace_id: str,
        tenant_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get complete trace chain (all spans in a trace).

        Args:
            trace_id: OpenTelemetry trace ID.
            tenant_id: Optional tenant identifier.

        Returns:
            List of trace context records ordered by creation time.
        """
        query = """
        SELECT 
            trace_id, span_id, correlation_id, parent_span_id,
            trace_flags, trace_state, baggage, service_name,
            span_name, tenant_id, user_id, operation_name,
            metadata, created_at, updated_at
        FROM otel_trace_context
        WHERE trace_id = $1
        """
        params: List[Any] = [trace_id]

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
                if record.get("baggage"):
                    record["baggage"] = (
                        json.loads(record["baggage"])
                        if isinstance(record["baggage"], str)
                        else record["baggage"]
                    )
                if record.get("metadata"):
                    record["metadata"] = (
                        json.loads(record["metadata"])
                        if isinstance(record["metadata"], str)
                        else record["metadata"]
                    )
        return results if results else []

    async def get_child_spans(
        self,
        parent_span_id: str,
        trace_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all child spans for a parent span.

        Args:
            parent_span_id: Parent span ID.
            trace_id: Optional trace ID filter.
            tenant_id: Optional tenant identifier.

        Returns:
            List of child span context records.
        """
        query = """
        SELECT 
            trace_id, span_id, correlation_id, parent_span_id,
            trace_flags, trace_state, baggage, service_name,
            span_name, tenant_id, user_id, operation_name,
            metadata, created_at, updated_at
        FROM otel_trace_context
        WHERE parent_span_id = $1
        """
        params: List[Any] = [parent_span_id]

        if trace_id:
            query += " AND trace_id = $2"
            params.append(trace_id)
            param_count = 2
        else:
            param_count = 1

        if tenant_id:
            query += f" AND tenant_id = ${param_count + 1}"
            params.append(tenant_id)

        query += " ORDER BY created_at ASC"

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        if results:
            for record in results:
                if record.get("baggage"):
                    record["baggage"] = (
                        json.loads(record["baggage"])
                        if isinstance(record["baggage"], str)
                        else record["baggage"]
                    )
                if record.get("metadata"):
                    record["metadata"] = (
                        json.loads(record["metadata"])
                        if isinstance(record["metadata"], str)
                        else record["metadata"]
                    )
        return results if results else []

    async def get_trace_history(
        self,
        service_name: Optional[str] = None,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        operation_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get trace context history.

        Args:
            service_name: Optional service name filter.
            tenant_id: Tenant identifier for tenant isolation.
            user_id: Optional user identifier.
            operation_name: Optional operation name filter.
            limit: Maximum number of records to return.
            offset: Offset for pagination.

        Returns:
            List of trace context records.
        """
        query = """
        SELECT 
            trace_id, span_id, correlation_id, parent_span_id,
            trace_flags, trace_state, baggage, service_name,
            span_name, tenant_id, user_id, operation_name,
            metadata, created_at, updated_at
        FROM otel_trace_context
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
        if operation_name:
            param_count += 1
            query += f" AND operation_name = ${param_count}"
            params.append(operation_name)

        query += f" ORDER BY created_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
        params.extend([limit, offset])

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        if results:
            for record in results:
                if record.get("baggage"):
                    record["baggage"] = (
                        json.loads(record["baggage"])
                        if isinstance(record["baggage"], str)
                        else record["baggage"]
                    )
                if record.get("metadata"):
                    record["metadata"] = (
                        json.loads(record["metadata"])
                        if isinstance(record["metadata"], str)
                        else record["metadata"]
                    )
        return results if results else []

    async def get_baggage_context(
        self,
        trace_id: str,
        span_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> Optional[Dict[str, str]]:
        """
        Get baggage context for a trace/span.

        Args:
            trace_id: OpenTelemetry trace ID.
            span_id: Optional span ID.
            tenant_id: Optional tenant identifier.

        Returns:
            Baggage dictionary or None.
        """
        context = await self.get_trace_context(trace_id, span_id=span_id, tenant_id=tenant_id)
        if context and context.get("baggage"):
            return context["baggage"]
        return None

    async def cleanup_old_traces(
        self,
        days: int = 90,
        tenant_id: Optional[str] = None,
    ) -> int:
        """
        Clean up old trace context records.

        Args:
            days: Number of days to keep (delete older records).
            tenant_id: Optional tenant identifier.

        Returns:
            Number of records deleted.
        """
        query = """
        DELETE FROM otel_trace_context
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

