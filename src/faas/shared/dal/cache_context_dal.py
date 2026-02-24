"""
Data Access Layer for Cache Context.

Abstracts all database operations for cache metadata and history persistence.
Tables are assumed to exist (managed by migrations/DAL).
"""


import json
import logging
from typing import Any, Dict, List, Optional

from src.core.postgresql_database import DatabaseConnection

logger = logging.getLogger(__name__)


class CacheContextDAL:
    """Data Access Layer for cache context and history persistence."""

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize CacheContextDAL.

        Args:
            db_connection: Database connection instance.
        """
        self.db = db_connection

    async def save_cache_operation(
        self,
        cache_key: str,
        operation: str,  # "set", "get", "delete", "invalidate"
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        session_id: Optional[str] = None,
        cache_hit: Optional[bool] = None,
        value_size: Optional[int] = None,
        ttl: Optional[int] = None,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Save cache operation to history.

        Args:
            cache_key: Cache key.
            operation: Operation type (set, get, delete, invalidate).
            tenant_id: Tenant identifier for tenant isolation.
            user_id: Optional user identifier.
            conversation_id: Optional conversation identifier.
            session_id: Optional session identifier.
            cache_hit: Whether cache hit occurred (for get operations).
            value_size: Size of cached value in bytes.
            ttl: Time-to-live in seconds.
            reason: Reason for caching (e.g., "query_result", "embedding").
            metadata: Optional metadata.

        Returns:
            Operation record ID.
        """
        import uuid
        operation_id = f"cache_op_{uuid.uuid4().hex[:16]}"

        result = await self.db.execute_query(
            """
            INSERT INTO cache_context (
                operation_id, cache_key, operation, tenant_id, user_id,
                conversation_id, session_id, cache_hit, value_size, ttl,
                reason, metadata, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12::jsonb, CURRENT_TIMESTAMP)
            RETURNING operation_id;
            """,
            params=(
                operation_id,
                cache_key,
                operation,
                tenant_id,
                user_id,
                conversation_id,
                session_id,
                cache_hit,
                value_size,
                ttl,
                reason,
                json.dumps(metadata or {}),
            ),
            fetch_one=True,
        )
        return str(result["operation_id"]) if result else operation_id

    async def get_cache_history(
        self,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        operation: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get cache operation history.

        Args:
            tenant_id: Tenant identifier for tenant isolation.
            user_id: Optional user identifier.
            conversation_id: Optional conversation identifier.
            operation: Optional operation type filter.
            limit: Maximum number of records to return.
            offset: Offset for pagination.

        Returns:
            List of cache operation records.
        """
        query = """
        SELECT 
            operation_id, cache_key, operation, tenant_id, user_id,
            conversation_id, session_id, cache_hit, value_size, ttl,
            reason, metadata, created_at
        FROM cache_context
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
        if operation:
            param_count += 1
            query += f" AND operation = ${param_count}"
            params.append(operation)

        query += f" ORDER BY created_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
        params.extend([limit, offset])

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        if results:
            for record in results:
                if record.get("metadata"):
                    record["metadata"] = (
                        json.loads(record["metadata"])
                        if isinstance(record["metadata"], str)
                        else record["metadata"]
                    )
        return results if results else []

    async def get_cache_stats(
        self,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        time_range_hours: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get cache statistics.

        Args:
            tenant_id: Tenant identifier for tenant isolation.
            user_id: Optional user identifier.
            conversation_id: Optional conversation identifier.
            time_range_hours: Optional time range in hours.

        Returns:
            Dictionary with cache statistics.
        """
        query = """
        SELECT 
            COUNT(*) as total_operations,
            COUNT(CASE WHEN operation = 'get' THEN 1 END) as get_operations,
            COUNT(CASE WHEN operation = 'set' THEN 1 END) as set_operations,
            COUNT(CASE WHEN operation = 'delete' THEN 1 END) as delete_operations,
            COUNT(CASE WHEN cache_hit = true THEN 1 END) as cache_hits,
            COUNT(CASE WHEN cache_hit = false THEN 1 END) as cache_misses,
            AVG(value_size) as avg_value_size,
            SUM(value_size) as total_value_size
        FROM cache_context
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
        if time_range_hours:
            param_count += 1
            # Use parameterized interval
            query += f" AND created_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour' * ${param_count}"
            params.append(time_range_hours)

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_one=True,
        )

        if result:
            total_ops = result.get("total_operations", 0) or 0
            hits = result.get("cache_hits", 0) or 0
            misses = result.get("cache_misses", 0) or 0
            hit_rate = (hits / (hits + misses)) * 100 if (hits + misses) > 0 else 0.0

            return {
                "total_operations": total_ops,
                "get_operations": result.get("get_operations", 0) or 0,
                "set_operations": result.get("set_operations", 0) or 0,
                "delete_operations": result.get("delete_operations", 0) or 0,
                "cache_hits": hits,
                "cache_misses": misses,
                "hit_rate": round(hit_rate, 2),
                "avg_value_size": float(result.get("avg_value_size", 0) or 0),
                "total_value_size": result.get("total_value_size", 0) or 0,
            }
        return {
            "total_operations": 0,
            "get_operations": 0,
            "set_operations": 0,
            "delete_operations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "hit_rate": 0.0,
            "avg_value_size": 0.0,
            "total_value_size": 0,
        }

    async def invalidate_conversation_cache(
        self,
        conversation_id: str,
        tenant_id: Optional[str] = None,
    ) -> List[str]:
        """
        Get cache keys for a conversation to enable invalidation.

        Args:
            conversation_id: Conversation identifier.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            List of cache keys associated with the conversation.
        """
        query = """
        SELECT DISTINCT cache_key
        FROM cache_context
        WHERE conversation_id = $1
        """
        params: List[Any] = [conversation_id]

        if tenant_id:
            query += " AND tenant_id = $2"
            params.append(tenant_id)

        query += " ORDER BY created_at DESC"

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        return [row["cache_key"] for row in results] if results else []

    async def invalidate_session_cache(
        self,
        session_id: str,
        tenant_id: Optional[str] = None,
    ) -> List[str]:
        """
        Get cache keys for a session to enable invalidation.

        Args:
            session_id: Session identifier.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            List of cache keys associated with the session.
        """
        query = """
        SELECT DISTINCT cache_key
        FROM cache_context
        WHERE session_id = $1
        """
        params: List[Any] = [session_id]

        if tenant_id:
            query += " AND tenant_id = $2"
            params.append(tenant_id)

        query += " ORDER BY created_at DESC"

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        return [row["cache_key"] for row in results] if results else []

    async def get_cache_keys_by_reason(
        self,
        reason: str,
        tenant_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[str]:
        """
        Get cache keys by reason (e.g., "query_result", "embedding").

        Args:
            reason: Reason for caching.
            tenant_id: Tenant identifier for tenant isolation.
            limit: Maximum number of keys to return.

        Returns:
            List of cache keys.
        """
        query = """
        SELECT DISTINCT cache_key
        FROM cache_context
        WHERE reason = $1
        """
        params: List[Any] = [reason]

        if tenant_id:
            query += " AND tenant_id = $2"
            params.append(tenant_id)
            query += " ORDER BY created_at DESC LIMIT $3"
            params.append(limit)
        else:
            query += " ORDER BY created_at DESC LIMIT $2"
            params.append(limit)

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        return [row["cache_key"] for row in results] if results else []

    async def cleanup_old_history(
        self,
        days: int = 90,
        tenant_id: Optional[str] = None,
    ) -> int:
        """
        Clean up old cache history records.

        Args:
            days: Number of days to keep (delete older records).
            tenant_id: Optional tenant identifier.

        Returns:
            Number of records deleted.
        """
        query = """
        DELETE FROM cache_context
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

    async def get_conversation_cache_keys(
        self,
        conversation_id: str,
        tenant_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get cache keys with metadata for a conversation.

        Args:
            conversation_id: Conversation identifier.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            List of cache key records with metadata.
        """
        query = """
        SELECT 
            cache_key, operation, cache_hit, value_size, ttl, reason,
            metadata, created_at
        FROM cache_context
        WHERE conversation_id = $1
        """
        params: List[Any] = [conversation_id]

        if tenant_id:
            query += " AND tenant_id = $2"
            params.append(tenant_id)

        query += " ORDER BY created_at DESC"

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        if results:
            for record in results:
                if record.get("metadata"):
                    record["metadata"] = (
                        json.loads(record["metadata"])
                        if isinstance(record["metadata"], str)
                        else record["metadata"]
                    )
        return results if results else []

