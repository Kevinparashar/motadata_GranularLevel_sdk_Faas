"""
Data Access Layer for Orchestrator Context.

Abstracts all database operations for orchestration request context, intent analysis,
and service routing decision persistence.
Tables are assumed to exist (managed by migrations/DAL).
"""


import json
import logging
from typing import Any, Dict, List, Optional

from src.core.postgresql_database import DatabaseConnection

logger = logging.getLogger(__name__)


class OrchestratorContextDAL:
    """Data Access Layer for orchestrator context and request history persistence."""

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize OrchestratorContextDAL.

        Args:
            db_connection: Database connection instance.
        """
        self.db = db_connection

    async def save_orchestration_request(
        self,
        request_id: str,
        correlation_id: str,
        query: str,
        intent: str,
        service_name: str,
        endpoint: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        session_id: Optional[str] = None,
        parent_request_id: Optional[str] = None,
        request_context: Optional[Dict[str, Any]] = None,
        routing_config: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        status: str = "success",  # "success", "error", "timeout", "service_unavailable"
        error_message: Optional[str] = None,
        latency_ms: float = 0.0,
        cached: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Save orchestration request to history.

        Args:
            request_id: Unique request identifier.
            correlation_id: Correlation ID for request tracking.
            query: User query text.
            intent: Detected or provided intent.
            service_name: Selected service name.
            endpoint: Selected service endpoint.
            tenant_id: Optional tenant identifier.
            user_id: Optional user identifier.
            conversation_id: Optional conversation identifier.
            session_id: Optional session identifier.
            parent_request_id: Optional parent request ID for nested requests.
            request_context: Optional request context dictionary.
            routing_config: Optional routing configuration used.
            response_data: Optional response data.
            status: Request status.
            error_message: Optional error message.
            latency_ms: Request latency in milliseconds.
            cached: Whether response was cached.
            metadata: Optional metadata.

        Returns:
            Request ID.
        """
        result = await self.db.execute_query(
            """
            INSERT INTO orchestrator_request_history (
                request_id, correlation_id, query, intent, service_name, endpoint,
                tenant_id, user_id, conversation_id, session_id, parent_request_id,
                request_context, routing_config, response_data, status, error_message,
                latency_ms, cached, metadata, created_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12::jsonb, $13::jsonb,
                $14::jsonb, $15, $16, $17, $18, $19::jsonb, CURRENT_TIMESTAMP
            )
            RETURNING request_id;
            """,
            params=(
                request_id,
                correlation_id,
                query,
                intent,
                service_name,
                endpoint,
                tenant_id,
                user_id,
                conversation_id,
                session_id,
                parent_request_id,
                json.dumps(request_context) if request_context else None,
                json.dumps(routing_config) if routing_config else None,
                json.dumps(response_data) if response_data else None,
                status,
                error_message,
                latency_ms,
                cached,
                json.dumps(metadata or {}),
            ),
            fetch_one=True,
        )
        return str(result["request_id"]) if result else request_id

    async def save_intent_analysis(
        self,
        query: str,
        intent: str,
        confidence: float,
        reasoning: Optional[str] = None,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        session_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        analysis_method: str = "llm",  # "llm", "pattern", "cached"
        cache_hit: bool = False,
        context_used: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Save intent analysis result to history.

        Args:
            query: User query text.
            intent: Detected intent.
            confidence: Confidence score (0.0-1.0).
            reasoning: Optional reasoning for the intent.
            tenant_id: Optional tenant identifier.
            user_id: Optional user identifier.
            conversation_id: Optional conversation identifier.
            session_id: Optional session identifier.
            correlation_id: Optional correlation ID.
            analysis_method: Method used for analysis ("llm", "pattern", "cached").
            cache_hit: Whether result was from cache.
            context_used: Optional context used for analysis.
            metadata: Optional metadata.

        Returns:
            Analysis record ID.
        """
        import uuid
        analysis_id = f"intent_analysis_{uuid.uuid4().hex[:16]}"

        result = await self.db.execute_query(
            """
            INSERT INTO orchestrator_intent_analysis_history (
                analysis_id, query, intent, confidence, reasoning, tenant_id, user_id,
                conversation_id, session_id, correlation_id, analysis_method, cache_hit,
                context_used, metadata, created_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13::jsonb, $14::jsonb, CURRENT_TIMESTAMP
            )
            RETURNING analysis_id;
            """,
            params=(
                analysis_id,
                query,
                intent,
                confidence,
                reasoning,
                tenant_id,
                user_id,
                conversation_id,
                session_id,
                correlation_id,
                analysis_method,
                cache_hit,
                json.dumps(context_used) if context_used else None,
                json.dumps(metadata or {}),
            ),
            fetch_one=True,
        )
        return str(result["analysis_id"]) if result else analysis_id

    async def save_routing_decision(
        self,
        intent: str,
        query: str,
        service_name: str,
        endpoint: str,
        routing_reason: Optional[str] = None,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        request_id: Optional[str] = None,
        fallback_used: bool = False,
        fallback_service: Optional[str] = None,
        routing_config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Save service routing decision to history.

        Args:
            intent: Query intent.
            query: User query text.
            service_name: Selected service name.
            endpoint: Selected endpoint.
            routing_reason: Optional reason for routing decision.
            tenant_id: Optional tenant identifier.
            user_id: Optional user identifier.
            correlation_id: Optional correlation ID.
            request_id: Optional request ID.
            fallback_used: Whether fallback service was used.
            fallback_service: Optional fallback service name.
            routing_config: Optional routing configuration.
            metadata: Optional metadata.

        Returns:
            Routing decision record ID.
        """
        import uuid
        decision_id = f"routing_decision_{uuid.uuid4().hex[:16]}"

        result = await self.db.execute_query(
            """
            INSERT INTO orchestrator_routing_decision_history (
                decision_id, intent, query, service_name, endpoint, routing_reason,
                tenant_id, user_id, correlation_id, request_id, fallback_used,
                fallback_service, routing_config, metadata, created_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13::jsonb, $14::jsonb, CURRENT_TIMESTAMP
            )
            RETURNING decision_id;
            """,
            params=(
                decision_id,
                intent,
                query,
                service_name,
                endpoint,
                routing_reason,
                tenant_id,
                user_id,
                correlation_id,
                request_id,
                fallback_used,
                fallback_service,
                json.dumps(routing_config) if routing_config else None,
                json.dumps(metadata or {}),
            ),
            fetch_one=True,
        )
        return str(result["decision_id"]) if result else decision_id

    async def save_cross_request_context(
        self,
        correlation_id: str,
        context_key: str,
        context_value: Dict[str, Any],
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Save cross-request orchestration context.

        Args:
            correlation_id: Correlation ID for context grouping.
            context_key: Context key identifier.
            context_value: Context value dictionary.
            tenant_id: Optional tenant identifier.
            user_id: Optional user identifier.
            conversation_id: Optional conversation identifier.
            session_id: Optional session identifier.
            ttl_seconds: Optional time-to-live in seconds.
            metadata: Optional metadata.

        Returns:
            Context record ID.
        """
        import uuid
        context_id = f"orchestrator_context_{uuid.uuid4().hex[:16]}"

        result = await self.db.execute_query(
            """
            INSERT INTO orchestrator_cross_request_context (
                context_id, correlation_id, context_key, context_value, tenant_id,
                user_id, conversation_id, session_id, ttl_seconds, metadata, created_at, expires_at
            ) VALUES (
                $1, $2, $3, $4::jsonb, $5, $6, $7, $8, $9, $10::jsonb, CURRENT_TIMESTAMP,
                CASE WHEN $9 IS NOT NULL THEN CURRENT_TIMESTAMP + INTERVAL '1 second' * $9 ELSE NULL END
            )
            RETURNING context_id;
            """,
            params=(
                context_id,
                correlation_id,
                context_key,
                json.dumps(context_value),
                tenant_id,
                user_id,
                conversation_id,
                session_id,
                ttl_seconds,
                json.dumps(metadata or {}),
            ),
            fetch_one=True,
        )
        return str(result["context_id"]) if result else context_id

    async def get_orchestration_request_history(
        self,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        session_id: Optional[str] = None,
        intent: Optional[str] = None,
        service_name: Optional[str] = None,
        status: Optional[str] = None,
        time_range_hours: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get orchestration request history.

        Args:
            tenant_id: Optional tenant identifier filter.
            user_id: Optional user identifier filter.
            conversation_id: Optional conversation identifier filter.
            session_id: Optional session identifier filter.
            intent: Optional intent filter.
            service_name: Optional service name filter.
            status: Optional status filter.
            time_range_hours: Optional time range in hours.
            limit: Maximum number of records to return.
            offset: Offset for pagination.

        Returns:
            List of orchestration request records.
        """
        query = """
        SELECT 
            request_id, correlation_id, query, intent, service_name, endpoint,
            tenant_id, user_id, conversation_id, session_id, parent_request_id,
            request_context, routing_config, response_data, status, error_message,
            latency_ms, cached, metadata, created_at
        FROM orchestrator_request_history
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
        if session_id:
            param_count += 1
            query += f" AND session_id = ${param_count}"
            params.append(session_id)
        if intent:
            param_count += 1
            query += f" AND intent = ${param_count}"
            params.append(intent)
        if service_name:
            param_count += 1
            query += f" AND service_name = ${param_count}"
            params.append(service_name)
        if status:
            param_count += 1
            query += f" AND status = ${param_count}"
            params.append(status)
        if time_range_hours:
            param_count += 1
            query += f" AND created_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour' * ${param_count}"
            params.append(time_range_hours)

        query += f" ORDER BY created_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
        params.extend([limit, offset])

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        if results:
            for record in results:
                for field in ["request_context", "routing_config", "response_data", "metadata"]:
                    if record.get(field):
                        record[field] = (
                            json.loads(record[field])
                            if isinstance(record[field], str)
                            else record[field]
                        )
        return results if results else []

    async def get_intent_analysis_history(
        self,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        intent: Optional[str] = None,
        analysis_method: Optional[str] = None,
        time_range_hours: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get intent analysis history.

        Args:
            tenant_id: Optional tenant identifier filter.
            user_id: Optional user identifier filter.
            conversation_id: Optional conversation identifier filter.
            intent: Optional intent filter.
            analysis_method: Optional analysis method filter.
            time_range_hours: Optional time range in hours.
            limit: Maximum number of records to return.
            offset: Offset for pagination.

        Returns:
            List of intent analysis records.
        """
        query = """
        SELECT 
            analysis_id, query, intent, confidence, reasoning, tenant_id, user_id,
            conversation_id, session_id, correlation_id, analysis_method, cache_hit,
            context_used, metadata, created_at
        FROM orchestrator_intent_analysis_history
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
        if intent:
            param_count += 1
            query += f" AND intent = ${param_count}"
            params.append(intent)
        if analysis_method:
            param_count += 1
            query += f" AND analysis_method = ${param_count}"
            params.append(analysis_method)
        if time_range_hours:
            param_count += 1
            query += f" AND created_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour' * ${param_count}"
            params.append(time_range_hours)

        query += f" ORDER BY created_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
        params.extend([limit, offset])

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        if results:
            for record in results:
                for field in ["context_used", "metadata"]:
                    if record.get(field):
                        record[field] = (
                            json.loads(record[field])
                            if isinstance(record[field], str)
                            else record[field]
                        )
        return results if results else []

    async def get_routing_decision_history(
        self,
        tenant_id: Optional[str] = None,
        intent: Optional[str] = None,
        service_name: Optional[str] = None,
        time_range_hours: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get service routing decision history.

        Args:
            tenant_id: Optional tenant identifier filter.
            intent: Optional intent filter.
            service_name: Optional service name filter.
            time_range_hours: Optional time range in hours.
            limit: Maximum number of records to return.
            offset: Offset for pagination.

        Returns:
            List of routing decision records.
        """
        query = """
        SELECT 
            decision_id, intent, query, service_name, endpoint, routing_reason,
            tenant_id, user_id, correlation_id, request_id, fallback_used,
            fallback_service, routing_config, metadata, created_at
        FROM orchestrator_routing_decision_history
        WHERE 1=1
        """
        params: List[Any] = []
        param_count = 0

        if tenant_id:
            param_count += 1
            query += f" AND tenant_id = ${param_count}"
            params.append(tenant_id)
        if intent:
            param_count += 1
            query += f" AND intent = ${param_count}"
            params.append(intent)
        if service_name:
            param_count += 1
            query += f" AND service_name = ${param_count}"
            params.append(service_name)
        if time_range_hours:
            param_count += 1
            query += f" AND created_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour' * ${param_count}"
            params.append(time_range_hours)

        query += f" ORDER BY created_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
        params.extend([limit, offset])

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        if results:
            for record in results:
                for field in ["routing_config", "metadata"]:
                    if record.get(field):
                        record[field] = (
                            json.loads(record[field])
                            if isinstance(record[field], str)
                            else record[field]
                        )
        return results if results else []

    async def get_cross_request_context(
        self,
        correlation_id: str,
        context_key: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get cross-request orchestration context.

        Args:
            correlation_id: Correlation ID for context grouping.
            context_key: Optional context key filter.
            tenant_id: Optional tenant identifier filter.

        Returns:
            List of context records.
        """
        query = """
        SELECT 
            context_id, correlation_id, context_key, context_value, tenant_id,
            user_id, conversation_id, session_id, ttl_seconds, metadata, created_at, expires_at
        FROM orchestrator_cross_request_context
        WHERE correlation_id = $1 AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
        """
        params: List[Any] = [correlation_id]
        param_count = 1

        if context_key:
            param_count += 1
            query += f" AND context_key = ${param_count}"
            params.append(context_key)
        if tenant_id:
            param_count += 1
            query += f" AND tenant_id = ${param_count}"
            params.append(tenant_id)

        query += " ORDER BY created_at DESC"

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        if results:
            for record in results:
                if record.get("context_value"):
                    record["context_value"] = (
                        json.loads(record["context_value"])
                        if isinstance(record["context_value"], str)
                        else record["context_value"]
                    )
                if record.get("metadata"):
                    record["metadata"] = (
                        json.loads(record["metadata"])
                        if isinstance(record["metadata"], str)
                        else record["metadata"]
                    )
        return results if results else []

    async def get_orchestration_stats(
        self,
        tenant_id: Optional[str] = None,
        time_range_hours: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get orchestration statistics.

        Args:
            tenant_id: Optional tenant identifier filter.
            time_range_hours: Optional time range in hours.

        Returns:
            Dictionary with orchestration statistics.
        """
        query = """
        SELECT 
            COUNT(*) as total_requests,
            COUNT(DISTINCT intent) as unique_intents,
            COUNT(DISTINCT service_name) as unique_services,
            COUNT(DISTINCT user_id) as unique_users,
            AVG(latency_ms) as avg_latency_ms,
            COUNT(CASE WHEN cached = true THEN 1 END) as cached_requests,
            COUNT(CASE WHEN status = 'error' THEN 1 END) as error_requests
        FROM orchestrator_request_history
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
            params=tuple(params) if params else None,
            fetch_one=True,
        )

        if result:
            return {
                "total_requests": result.get("total_requests", 0) or 0,
                "unique_intents": result.get("unique_intents", 0) or 0,
                "unique_services": result.get("unique_services", 0) or 0,
                "unique_users": result.get("unique_users", 0) or 0,
                "avg_latency_ms": float(result.get("avg_latency_ms", 0.0) or 0.0),
                "cached_requests": result.get("cached_requests", 0) or 0,
                "error_requests": result.get("error_requests", 0) or 0,
            }
        return {
            "total_requests": 0,
            "unique_intents": 0,
            "unique_services": 0,
            "unique_users": 0,
            "avg_latency_ms": 0.0,
            "cached_requests": 0,
            "error_requests": 0,
        }

    async def get_intent_distribution(
        self,
        tenant_id: Optional[str] = None,
        time_range_hours: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get intent distribution statistics.

        Args:
            tenant_id: Optional tenant identifier filter.
            time_range_hours: Optional time range in hours.

        Returns:
            List of intent distribution records.
        """
        query = """
        SELECT 
            intent,
            COUNT(*) as count,
            AVG(confidence) as avg_confidence
        FROM orchestrator_intent_analysis_history
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

        query += " GROUP BY intent ORDER BY count DESC"

        results = await self.db.execute_query(
            query,
            params=tuple(params) if params else None,
            fetch_all=True,
        )

        if results:
            for record in results:
                record["avg_confidence"] = float(record.get("avg_confidence", 0.0) or 0.0)
        return results if results else []

    async def cleanup_old_context(
        self,
        days: int = 90,
        tenant_id: Optional[str] = None,
    ) -> int:
        """
        Clean up old orchestration context records.

        Args:
            days: Number of days to keep (delete older records).
            tenant_id: Optional tenant identifier.

        Returns:
            Number of records deleted.
        """
        query = """
        DELETE FROM orchestrator_cross_request_context
        WHERE expires_at < CURRENT_TIMESTAMP OR created_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
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

