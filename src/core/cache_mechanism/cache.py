"""
Cache Mechanism

Provides async-first cache layer with in-memory and Dragonfly backends.
Production-ready implementation for scalable deployments.
"""

import asyncio
import json
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Dict, Optional

try:
    import aioredis
except ImportError:
    aioredis = None

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Cache configuration."""
    backend: str = "memory"
    default_ttl: int = 300
    max_size: int = 1024
    dragonfly_url: Optional[str] = None
    namespace: str = "sdk_cache"


class CacheMechanism:
    """
    Async-first cache wrapper supporting in-memory and Dragonfly backends.
    """

    def __init__(
        self,
        config: Optional[CacheConfig] = None,
        otel_tracer: Optional[Any] = None,
        otel_metrics: Optional[Any] = None,
        cache_context_dal: Optional[Any] = None,
    ) -> None:
        """
        Initialize cache mechanism.
        
        Args:
            config: Cache configuration
            otel_tracer: Optional OTEL tracer for distributed tracing
            otel_metrics: Optional OTEL metrics for metrics collection
            cache_context_dal: Optional CacheContextDAL for context persistence
        """
        self.config = config or CacheConfig()
        self.backend = self.config.backend
        self._async_client: Optional[Any] = None
        self._lock = asyncio.Lock()
        self._store: OrderedDict[str, tuple[Any, float]] = OrderedDict()

        # Cache Context DAL (optional)
        self.cache_context_dal = cache_context_dal

        # OTEL Integration (optional)
        self.otel_tracer: Optional[Any] = otel_tracer
        self.otel_metrics: Optional[Any] = otel_metrics

        # Initialize OTEL if not provided
        if self.otel_tracer is None:
            try:
                from ..otel_integration import create_otel_tracer

                self.otel_tracer = create_otel_tracer(service_name="cache-mechanism")
            except (ImportError, Exception):
                self.otel_tracer = None

        if self.otel_metrics is None:
            try:
                from ..otel_integration import create_otel_metrics

                self.otel_metrics = create_otel_metrics(service_name="cache-mechanism")
            except (ImportError, Exception):
                self.otel_metrics = None

    async def _ensure_async_client(self) -> Any:
        """Ensure async Dragonfly client is initialized."""
        if self._async_client is None and self.backend == "dragonfly":
            if aioredis is None:
                raise ImportError("aioredis required for Dragonfly backend")
            self._async_client = await aioredis.from_url(
                self.config.dragonfly_url or "redis://localhost:6379/0",
                encoding="utf-8",
                decode_responses=False
            )
        return self._async_client

    def _namespaced_key(self, key: str, tenant_id: Optional[str] = None) -> str:
        """Create namespaced cache key."""
        if tenant_id:
            return f"{self.config.namespace}:{tenant_id}:{key}"
        return f"{self.config.namespace}:{key}"

    def _build_context_aware_key(
        self,
        base_key: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """
        Build context-aware cache key.

        Args:
            base_key: Base cache key.
            tenant_id: Optional tenant ID.
            user_id: Optional user ID.
            conversation_id: Optional conversation ID.
            session_id: Optional session ID.

        Returns:
            Context-aware cache key.
        """
        key_parts = [base_key]
        if conversation_id:
            key_parts.insert(0, f"conv:{conversation_id}")
        if session_id:
            key_parts.insert(0, f"session:{session_id}")
        if user_id:
            key_parts.insert(0, f"user:{user_id}")
        
        context_key = ":".join(key_parts)
        return self._namespaced_key(context_key, tenant_id=tenant_id)

    async def set(
        self,
        key: str,
        value: Any,
        tenant_id: Optional[str] = None,
        ttl: Optional[int] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        session_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> None:
        """
        Store value in cache asynchronously.
        
        Args:
            key: Cache key.
            value: Value to cache.
            tenant_id: Optional tenant ID.
            ttl: Optional time-to-live in seconds.
            user_id: Optional user ID for context.
            conversation_id: Optional conversation ID for context.
            session_id: Optional session ID for context.
            reason: Optional reason for caching (e.g., "query_result", "embedding").
        """
        start_time = time.time()
        ttl = ttl or self.config.default_ttl
        expires_at = time.time() + ttl
        namespaced = self._namespaced_key(key, tenant_id=tenant_id)
        
        # Calculate value size for tracking
        try:
            value_size = len(json.dumps(value).encode('utf-8')) if value else 0
        except (TypeError, ValueError):
            value_size = None

        # OTEL Integration
        if self.otel_tracer:
            with self.otel_tracer.start_trace("cache.set") as trace:
                trace.set_attribute("cache.backend", self.backend)
                trace.set_attribute("cache.key", key)
                trace.set_attribute("cache.ttl", ttl)
                from ..utils.tenant_utils import add_tenant_attributes_to_span
                add_tenant_attributes_to_span(trace, tenant_id, attribute_prefix="cache")

                try:
                    if self.backend == "dragonfly":
                        client = await self._ensure_async_client()
                        await client.set(namespaced, value, ex=ttl)
                    else:
                        async with self._lock:
                            self._store[namespaced] = (value, expires_at)
                            self._store.move_to_end(namespaced)
                            self._evict_if_needed()

                    duration = time.time() - start_time
                    if self.otel_metrics:
                        self.otel_metrics.record_histogram(
                            "cache.set.duration", duration, {"backend": self.backend}
                        )
                        self.otel_metrics.increment_counter(
                            "cache.operations",
                            amount=1.0,
                            attributes={"operation": "set", "backend": self.backend, "status": "success"},
                        )
                    
                    # Save cache context (non-blocking)
                    if self.cache_context_dal:
                        try:
                            await self.cache_context_dal.save_cache_operation(
                                cache_key=key,
                                operation="set",
                                tenant_id=tenant_id,
                                user_id=user_id,
                                conversation_id=conversation_id,
                                session_id=session_id,
                                cache_hit=None,
                                value_size=value_size,
                                ttl=ttl,
                                reason=reason,
                                metadata={"backend": self.backend, "duration_ms": duration * 1000},
                            )
                        except Exception as e:
                            logger.debug(f"Failed to save cache context (non-critical): {e}")
                except Exception as e:
                    trace.record_exception(e)
                    duration = time.time() - start_time
                    if self.otel_metrics:
                        self.otel_metrics.record_histogram(
                            "cache.set.duration", duration, {"backend": self.backend}
                        )
                        self.otel_metrics.increment_counter(
                            "cache.operations",
                            amount=1.0,
                            attributes={"operation": "set", "backend": self.backend, "status": "error"},
                        )
                    raise
        else:
            # No OTEL - execute without tracing
            if self.backend == "dragonfly":
                client = await self._ensure_async_client()
                await client.set(namespaced, value, ex=ttl)
            else:
                async with self._lock:
                    self._store[namespaced] = (value, expires_at)
                    self._store.move_to_end(namespaced)
                    self._evict_if_needed()
            
            # Save cache context (non-blocking)
            if self.cache_context_dal:
                try:
                    await self.cache_context_dal.save_cache_operation(
                        cache_key=key,
                        operation="set",
                        tenant_id=tenant_id,
                        user_id=user_id,
                        conversation_id=conversation_id,
                        session_id=session_id,
                        cache_hit=None,
                        value_size=value_size,
                        ttl=ttl,
                        reason=reason,
                        metadata={"backend": self.backend},
                    )
                except Exception as e:
                    logger.debug(f"Failed to save cache context (non-critical): {e}")

    async def get(
        self,
        key: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Optional[Any]:
        """
        Retrieve value from cache asynchronously.
        
        Args:
            key: Cache key.
            tenant_id: Optional tenant ID.
            user_id: Optional user ID for context.
            conversation_id: Optional conversation ID for context.
            session_id: Optional session ID for context.
        
        Returns:
            Cached value or None.
        """
        start_time = time.time()
        namespaced = self._namespaced_key(key, tenant_id=tenant_id)

        # OTEL Integration
        if self.otel_tracer:
            with self.otel_tracer.start_trace("cache.get") as trace:
                trace.set_attribute("cache.backend", self.backend)
                trace.set_attribute("cache.key", key)
                if tenant_id:
                    trace.set_attribute("cache.tenant_id", tenant_id)

                try:
                    if self.backend == "dragonfly":
                        client = await self._ensure_async_client()
                        result = await client.get(namespaced)
                    else:
                        if namespaced not in self._store:
                            result = None
                        else:
                            value, expires_at = self._store[namespaced]
                            if expires_at < time.time():
                                self._store.pop(namespaced, None)
                                result = None
                            else:
                                async with self._lock:
                                    self._store.move_to_end(namespaced)
                                result = value

                    duration = time.time() - start_time
                    cache_hit = result is not None
                    trace.set_attribute("cache.hit", cache_hit)

                    if self.otel_metrics:
                        self.otel_metrics.record_histogram(
                            "cache.get.duration", duration, {"backend": self.backend}
                        )
                        self.otel_metrics.increment_counter(
                            "cache.operations",
                            amount=1.0,
                            attributes={
                                "operation": "get",
                                "backend": self.backend,
                                "status": "success",
                            },
                        )
                        if cache_hit:
                            self.otel_metrics.increment_counter(
                                "cache.hits",
                                amount=1.0,
                                attributes={"backend": self.backend},
                            )
                        else:
                            self.otel_metrics.increment_counter(
                                "cache.misses",
                                amount=1.0,
                                attributes={"backend": self.backend},
                            )
                    
                    # Save cache context (non-blocking)
                    if self.cache_context_dal:
                        try:
                            await self.cache_context_dal.save_cache_operation(
                                cache_key=key,
                                operation="get",
                                tenant_id=tenant_id,
                                user_id=user_id,
                                conversation_id=conversation_id,
                                session_id=session_id,
                                cache_hit=cache_hit,
                                value_size=None,
                                ttl=None,
                                reason=None,
                                metadata={"backend": self.backend, "duration_ms": duration * 1000},
                            )
                        except Exception as e:
                            logger.debug(f"Failed to save cache context (non-critical): {e}")

                    return result
                except Exception as e:
                    trace.record_exception(e)
                    duration = time.time() - start_time
                    if self.otel_metrics:
                        self.otel_metrics.record_histogram(
                            "cache.get.duration", duration, {"backend": self.backend}
                        )
                        self.otel_metrics.increment_counter(
                            "cache.operations",
                            amount=1.0,
                            attributes={"operation": "get", "backend": self.backend, "status": "error"},
                        )
                    raise
        else:
            # No OTEL - execute without tracing
            if self.backend == "dragonfly":
                client = await self._ensure_async_client()
                result = await client.get(namespaced)
            else:
                if namespaced not in self._store:
                    result = None
                else:
                    value, expires_at = self._store[namespaced]
                    if expires_at < time.time():
                        self._store.pop(namespaced, None)
                        result = None
                    else:
                        async with self._lock:
                            self._store.move_to_end(namespaced)
                        result = value
            
            # Save cache context (non-blocking)
            if self.cache_context_dal:
                try:
                    cache_hit = result is not None
                    await self.cache_context_dal.save_cache_operation(
                        cache_key=key,
                        operation="get",
                        tenant_id=tenant_id,
                        user_id=user_id,
                        conversation_id=conversation_id,
                        session_id=session_id,
                        cache_hit=cache_hit,
                        value_size=None,
                        ttl=None,
                        reason=None,
                        metadata={"backend": self.backend},
                    )
                except Exception as e:
                    logger.debug(f"Failed to save cache context (non-critical): {e}")
            
            return result

    async def delete(
        self,
        key: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """
        Delete key from cache asynchronously.
        
        Args:
            key: Cache key.
            tenant_id: Optional tenant ID.
            user_id: Optional user ID for context.
            conversation_id: Optional conversation ID for context.
            session_id: Optional session ID for context.
        """
        start_time = time.time()
        namespaced = self._namespaced_key(key, tenant_id=tenant_id)

        # OTEL Integration
        if self.otel_tracer:
            with self.otel_tracer.start_trace("cache.delete") as trace:
                trace.set_attribute("cache.backend", self.backend)
                trace.set_attribute("cache.key", key)
                if tenant_id:
                    trace.set_attribute("cache.tenant_id", tenant_id)

                try:
                    if self.backend == "dragonfly":
                        client = await self._ensure_async_client()
                        await client.delete(namespaced)
                    else:
                        async with self._lock:
                            self._store.pop(namespaced, None)

                    duration = time.time() - start_time
                    if self.otel_metrics:
                        self.otel_metrics.record_histogram(
                            "cache.delete.duration", duration, {"backend": self.backend}
                        )
                        self.otel_metrics.increment_counter(
                            "cache.operations",
                            amount=1.0,
                            attributes={"operation": "delete", "backend": self.backend, "status": "success"},
                        )
                    
                    # Save cache context (non-blocking)
                    if self.cache_context_dal:
                        try:
                            await self.cache_context_dal.save_cache_operation(
                                cache_key=key,
                                operation="delete",
                                tenant_id=tenant_id,
                                user_id=user_id,
                                conversation_id=conversation_id,
                                session_id=session_id,
                                cache_hit=None,
                                value_size=None,
                                ttl=None,
                                reason=None,
                                metadata={"backend": self.backend, "duration_ms": duration * 1000},
                            )
                        except Exception as e:
                            logger.debug(f"Failed to save cache context (non-critical): {e}")
                except Exception as e:
                    trace.record_exception(e)
                    duration = time.time() - start_time
                    if self.otel_metrics:
                        self.otel_metrics.record_histogram(
                            "cache.delete.duration", duration, {"backend": self.backend}
                        )
                        self.otel_metrics.increment_counter(
                            "cache.operations",
                            amount=1.0,
                            attributes={"operation": "delete", "backend": self.backend, "status": "error"},
                        )
                    raise
        else:
            # No OTEL - execute without tracing
            if self.backend == "dragonfly":
                client = await self._ensure_async_client()
                await client.delete(namespaced)
            else:
                async with self._lock:
                    self._store.pop(namespaced, None)
            
            # Save cache context (non-blocking)
            if self.cache_context_dal:
                try:
                    await self.cache_context_dal.save_cache_operation(
                        cache_key=key,
                        operation="delete",
                        tenant_id=tenant_id,
                        user_id=user_id,
                        conversation_id=conversation_id,
                        session_id=session_id,
                        cache_hit=None,
                        value_size=None,
                        ttl=None,
                        reason=None,
                        metadata={"backend": self.backend},
                    )
                except Exception as e:
                    logger.debug(f"Failed to save cache context (non-critical): {e}")

    async def invalidate_pattern(self, pattern: str, tenant_id: Optional[str] = None) -> None:
        """Invalidate keys matching pattern asynchronously."""
        start_time = time.time()
        if tenant_id:
            pattern = f"{tenant_id}:{pattern}"

        # OTEL Integration
        if self.otel_tracer:
            with self.otel_tracer.start_trace("cache.invalidate_pattern") as trace:
                trace.set_attribute("cache.backend", self.backend)
                trace.set_attribute("cache.pattern", pattern)
                if tenant_id:
                    trace.set_attribute("cache.tenant_id", tenant_id)

                try:
                    keys_deleted = 0
                    if self.backend == "dragonfly":
                        client = await self._ensure_async_client()
                        keys_to_delete = []
                        cursor = b'0'
                        while cursor:
                            cursor, keys = await client.scan(
                                cursor, match=f"{self.config.namespace}:{pattern}*", count=100
                            )
                            keys_to_delete.extend(keys)
                            if cursor == b'0':
                                break
                        if keys_to_delete:
                            await client.delete(*keys_to_delete)
                            keys_deleted = len(keys_to_delete)
                    else:
                        async with self._lock:
                            # Use fnmatch for wildcard pattern matching
                            import fnmatch
                            # Build full pattern with namespace
                            full_pattern = f"{self.config.namespace}:{pattern}*"
                            keys_to_delete = [k for k in self._store.keys() if fnmatch.fnmatch(k, full_pattern)]
                            keys_deleted = len(keys_to_delete)
                            for k in keys_to_delete:
                                self._store.pop(k, None)

                    duration = time.time() - start_time
                    trace.set_attribute("cache.keys_deleted", keys_deleted)

                    if self.otel_metrics:
                        self.otel_metrics.record_histogram(
                            "cache.invalidate_pattern.duration", duration, {"backend": self.backend}
                        )
                        self.otel_metrics.increment_counter(
                            "cache.operations",
                            amount=1.0,
                            attributes={
                                "operation": "invalidate_pattern",
                                "backend": self.backend,
                                "status": "success",
                            },
                        )
                except Exception as e:
                    trace.record_exception(e)
                    duration = time.time() - start_time
                    if self.otel_metrics:
                        self.otel_metrics.record_histogram(
                            "cache.invalidate_pattern.duration", duration, {"backend": self.backend}
                        )
                        self.otel_metrics.increment_counter(
                            "cache.operations",
                            amount=1.0,
                            attributes={
                                "operation": "invalidate_pattern",
                                "backend": self.backend,
                                "status": "error",
                            },
                        )
                    raise
        else:
            # No OTEL - execute without tracing
            if self.backend == "dragonfly":
                client = await self._ensure_async_client()
                keys_to_delete = []
                cursor = b'0'
                while cursor:
                    cursor, keys = await client.scan(
                        cursor, match=f"{self.config.namespace}:{pattern}*", count=100
                    )
                    keys_to_delete.extend(keys)
                    if cursor == b'0':
                        break
                if keys_to_delete:
                    await client.delete(*keys_to_delete)
            else:
                async with self._lock:
                    # More efficient: iterate once and delete in place
                    keys_to_delete = [k for k in self._store.keys() if pattern in k]
                    for k in keys_to_delete:
                        self._store.pop(k, None)

    def _evict_if_needed(self) -> None:
        """Evict oldest entries if cache exceeds max size."""
        while len(self._store) > self.config.max_size:
            self._store.popitem(last=False)

    async def cache_prompt_interpretation(
        self, prompt_hash: str, interpretation: Any, tenant_id: Optional[str] = None, ttl: Optional[int] = None
    ) -> None:
        """Cache prompt interpretation asynchronously."""
        if isinstance(interpretation, dict):
            interpretation = json.dumps(interpretation)
        await self.set(f"prompt_interp:{prompt_hash}", interpretation, tenant_id=tenant_id, ttl=ttl)

    async def get_prompt_interpretation(
        self, prompt_hash: str, tenant_id: Optional[str] = None
    ) -> Optional[Any]:
        """Get cached prompt interpretation asynchronously."""
        cached = await self.get(f"prompt_interp:{prompt_hash}", tenant_id=tenant_id)
        if cached:
            try:
                if isinstance(cached, str):
                    return json.loads(cached)
                return cached
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    async def clear(self, tenant_id: Optional[str] = None) -> None:
        """Clear cache entries asynchronously."""
        start_time = time.time()

        # OTEL Integration
        if self.otel_tracer:
            with self.otel_tracer.start_trace("cache.clear") as trace:
                trace.set_attribute("cache.backend", self.backend)
                if tenant_id:
                    trace.set_attribute("cache.tenant_id", tenant_id)

                try:
                    keys_deleted = 0
                    if self.backend == "dragonfly":
                        pattern = f"{tenant_id}:*" if tenant_id else "*"
                        await self.invalidate_pattern(pattern.replace(f"{self.config.namespace}:", ""))
                        # Note: keys_deleted would be set by invalidate_pattern, but we can't easily get it here
                        # This is acceptable as invalidate_pattern has its own tracing
                    else:
                        async with self._lock:
                            if tenant_id:
                                to_delete = [k for k in self._store if f":{tenant_id}:" in k]
                                keys_deleted = len(to_delete)
                                for k in to_delete:
                                    self._store.pop(k, None)
                            else:
                                keys_deleted = len(self._store)
                                self._store.clear()

                    duration = time.time() - start_time
                    trace.set_attribute("cache.keys_deleted", keys_deleted)

                    if self.otel_metrics:
                        self.otel_metrics.record_histogram(
                            "cache.clear.duration", duration, {"backend": self.backend}
                        )
                        self.otel_metrics.increment_counter(
                            "cache.operations",
                            amount=1.0,
                            attributes={"operation": "clear", "backend": self.backend, "status": "success"},
                        )
                except Exception as e:
                    trace.record_exception(e)
                    duration = time.time() - start_time
                    if self.otel_metrics:
                        self.otel_metrics.record_histogram(
                            "cache.clear.duration", duration, {"backend": self.backend}
                        )
                        self.otel_metrics.increment_counter(
                            "cache.operations",
                            amount=1.0,
                            attributes={"operation": "clear", "backend": self.backend, "status": "error"},
                        )
                    raise
        else:
            # No OTEL - execute without tracing
            if self.backend == "dragonfly":
                pattern = f"{tenant_id}:*" if tenant_id else "*"
                await self.invalidate_pattern(pattern.replace(f"{self.config.namespace}:", ""))
            else:
                async with self._lock:
                    if tenant_id:
                        to_delete = [k for k in self._store if f":{tenant_id}:" in k]
                        for k in to_delete:
                            self._store.pop(k, None)
                    else:
                        self._store.clear()

    async def invalidate_conversation(
        self,
        conversation_id: str,
        tenant_id: Optional[str] = None,
    ) -> int:
        """
        Invalidate all cache entries for a conversation.

        Args:
            conversation_id: Conversation identifier.
            tenant_id: Optional tenant ID.

        Returns:
            Number of keys invalidated.
        """
        if not self.cache_context_dal:
            logger.warning("CacheContextDAL not available for conversation invalidation")
            return 0

        try:
            # Get cache keys for conversation
            cache_keys = await self.cache_context_dal.invalidate_conversation_cache(
                conversation_id=conversation_id,
                tenant_id=tenant_id,
            )

            # Delete each key
            deleted_count = 0
            for key in cache_keys:
                try:
                    await self.delete(key, tenant_id=tenant_id)
                    deleted_count += 1
                except Exception as e:
                    logger.debug(f"Failed to delete cache key {key}: {e}")

            # Log invalidation operation
            if self.cache_context_dal:
                try:
                    await self.cache_context_dal.save_cache_operation(
                        cache_key=f"conversation:{conversation_id}",
                        operation="invalidate",
                        tenant_id=tenant_id,
                        conversation_id=conversation_id,
                        cache_hit=None,
                        value_size=None,
                        ttl=None,
                        reason="conversation_invalidation",
                        metadata={"keys_invalidated": deleted_count},
                    )
                except Exception as e:
                    logger.debug(f"Failed to save invalidation context: {e}")

            return deleted_count
        except Exception as e:
            logger.error(f"Failed to invalidate conversation cache: {e}")
            return 0

    async def invalidate_session(
        self,
        session_id: str,
        tenant_id: Optional[str] = None,
    ) -> int:
        """
        Invalidate all cache entries for a session.

        Args:
            session_id: Session identifier.
            tenant_id: Optional tenant ID.

        Returns:
            Number of keys invalidated.
        """
        if not self.cache_context_dal:
            logger.warning("CacheContextDAL not available for session invalidation")
            return 0

        try:
            # Get cache keys for session
            cache_keys = await self.cache_context_dal.invalidate_session_cache(
                session_id=session_id,
                tenant_id=tenant_id,
            )

            # Delete each key
            deleted_count = 0
            for key in cache_keys:
                try:
                    await self.delete(key, tenant_id=tenant_id)
                    deleted_count += 1
                except Exception as e:
                    logger.debug(f"Failed to delete cache key {key}: {e}")

            # Log invalidation operation
            if self.cache_context_dal:
                try:
                    await self.cache_context_dal.save_cache_operation(
                        cache_key=f"session:{session_id}",
                        operation="invalidate",
                        tenant_id=tenant_id,
                        session_id=session_id,
                        cache_hit=None,
                        value_size=None,
                        ttl=None,
                        reason="session_invalidation",
                        metadata={"keys_invalidated": deleted_count},
                    )
                except Exception as e:
                    logger.debug(f"Failed to save invalidation context: {e}")

            return deleted_count
        except Exception as e:
            logger.error(f"Failed to invalidate session cache: {e}")
            return 0

    async def invalidate_by_reason(
        self,
        reason: str,
        tenant_id: Optional[str] = None,
        limit: int = 100,
    ) -> int:
        """
        Invalidate cache entries by reason (e.g., "query_result", "embedding").

        Args:
            reason: Reason for caching.
            tenant_id: Optional tenant ID.
            limit: Maximum number of keys to invalidate.

        Returns:
            Number of keys invalidated.
        """
        if not self.cache_context_dal:
            logger.warning("CacheContextDAL not available for reason-based invalidation")
            return 0

        try:
            # Get cache keys by reason
            cache_keys = await self.cache_context_dal.get_cache_keys_by_reason(
                reason=reason,
                tenant_id=tenant_id,
                limit=limit,
            )

            # Delete each key
            deleted_count = 0
            for key in cache_keys:
                try:
                    await self.delete(key, tenant_id=tenant_id)
                    deleted_count += 1
                except Exception as e:
                    logger.debug(f"Failed to delete cache key {key}: {e}")

            return deleted_count
        except Exception as e:
            logger.error(f"Failed to invalidate cache by reason: {e}")
            return 0

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
            tenant_id: Optional tenant ID.
            user_id: Optional user ID.
            conversation_id: Optional conversation ID.
            time_range_hours: Optional time range in hours.

        Returns:
            Dictionary with cache statistics.
        """
        if not self.cache_context_dal:
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

        return await self.cache_context_dal.get_cache_stats(
            tenant_id=tenant_id,
            user_id=user_id,
            conversation_id=conversation_id,
            time_range_hours=time_range_hours,
        )

    async def close(self) -> None:
        """Close async client connections."""
        if self._async_client:
            await self._async_client.close()
            self._async_client = None
