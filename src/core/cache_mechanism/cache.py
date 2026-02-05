"""
Cache Mechanism

Provides async-first cache layer with in-memory and Dragonfly backends.
Production-ready implementation for scalable deployments.
"""

import asyncio
import json
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Optional

try:
    import aioredis  # type: ignore[import]
except ImportError:
    aioredis = None


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

    def __init__(self, config: Optional[CacheConfig] = None) -> None:
        """Initialize cache mechanism."""
        self.config = config or CacheConfig()
        self.backend = self.config.backend
        self._async_client: Optional[Any] = None
        self._lock = asyncio.Lock()
        self._store: OrderedDict[str, tuple[Any, float]] = OrderedDict()

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

    async def set(
        self, key: str, value: Any, tenant_id: Optional[str] = None, ttl: Optional[int] = None
    ) -> None:
        """Store value in cache asynchronously."""
        ttl = ttl or self.config.default_ttl
        expires_at = time.time() + ttl
        namespaced = self._namespaced_key(key, tenant_id=tenant_id)

        if self.backend == "dragonfly":
            client = await self._ensure_async_client()
            await client.set(namespaced, value, ex=ttl)
            return

        async with self._lock:
            self._store[namespaced] = (value, expires_at)
            self._store.move_to_end(namespaced)
            self._evict_if_needed()

    async def get(self, key: str, tenant_id: Optional[str] = None) -> Optional[Any]:
        """Retrieve value from cache asynchronously."""
        namespaced = self._namespaced_key(key, tenant_id=tenant_id)

        if self.backend == "dragonfly":
            client = await self._ensure_async_client()
            return await client.get(namespaced)

        if namespaced not in self._store:
            return None

        value, expires_at = self._store[namespaced]
        if expires_at < time.time():
            self._store.pop(namespaced, None)
            return None

        async with self._lock:
            self._store.move_to_end(namespaced)
        return value

    async def delete(self, key: str, tenant_id: Optional[str] = None) -> None:
        """Delete key from cache asynchronously."""
        namespaced = self._namespaced_key(key, tenant_id=tenant_id)
        if self.backend == "dragonfly":
            client = await self._ensure_async_client()
            await client.delete(namespaced)
        else:
            async with self._lock:
                self._store.pop(namespaced, None)

    async def invalidate_pattern(self, pattern: str, tenant_id: Optional[str] = None) -> None:
        """Invalidate keys matching pattern asynchronously."""
        if tenant_id:
            pattern = f"{tenant_id}:{pattern}"
        
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
            return

        async with self._lock:
            to_delete = [k for k in self._store if pattern in k]
            for k in to_delete:
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
            except Exception:
                return None
        return None

    async def clear(self, tenant_id: Optional[str] = None) -> None:
        """Clear cache entries asynchronously."""
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

    async def close(self) -> None:
        """Close async client connections."""
        if self._async_client:
            await self._async_client.close()
            self._async_client = None
