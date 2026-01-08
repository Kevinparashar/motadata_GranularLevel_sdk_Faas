"""
Cache Mechanism

Provides a simple pluggable cache layer with in-memory and Redis backends,
supporting TTL, basic LRU eviction, and pattern-based invalidation.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Optional

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    redis = None


@dataclass
class CacheConfig:
    backend: str = "memory"  # "memory" or "redis"
    default_ttl: int = 300
    max_size: int = 1024  # only applies to memory backend
    redis_url: Optional[str] = None
    namespace: str = "sdk_cache"


class CacheMechanism:
    """
    Cache wrapper that supports in-memory and Redis backends with TTL support.
    """

    def __init__(self, config: Optional[CacheConfig] = None) -> None:
        self.config = config or CacheConfig()
        self.backend = self.config.backend

        if self.backend == "redis":
            if redis is None:
                raise ImportError("redis package is required for Redis backend")
            self._client = redis.Redis.from_url(self.config.redis_url or "redis://localhost:6379/0")
        else:
            # Simple in-memory LRU with TTL
            self._store: OrderedDict[str, tuple[Any, float]] = OrderedDict()

    def _namespaced_key(self, key: str, tenant_id: Optional[str] = None) -> str:
        """Create namespaced cache key with optional tenant isolation."""
        if tenant_id:
            return f"{self.config.namespace}:{tenant_id}:{key}"
        return f"{self.config.namespace}:{key}"

    def set(self, key: str, value: Any, tenant_id: Optional[str] = None, ttl: Optional[int] = None) -> None:
        ttl = ttl or self.config.default_ttl
        expires_at = time.time() + ttl
        namespaced = self._namespaced_key(key, tenant_id=tenant_id)

        if self.backend == "redis":
            self._client.set(namespaced, value, ex=ttl)
            return

        # memory backend with LRU eviction
        self._store[namespaced] = (value, expires_at)
        self._store.move_to_end(namespaced)
        self._evict_if_needed()

    def get(self, key: str, tenant_id: Optional[str] = None) -> Optional[Any]:
        namespaced = self._namespaced_key(key, tenant_id=tenant_id)

        if self.backend == "redis":
            value = self._client.get(namespaced)
            return value

        if namespaced not in self._store:
            return None

        value, expires_at = self._store[namespaced]
        if expires_at < time.time():
            # expired
            self._store.pop(namespaced, None)
            return None

        # refresh LRU ordering
        self._store.move_to_end(namespaced)
        return value

    def delete(self, key: str, tenant_id: Optional[str] = None) -> None:
        namespaced = self._namespaced_key(key, tenant_id=tenant_id)
        if self.backend == "redis":
            self._client.delete(namespaced)
        else:
            self._store.pop(namespaced, None)

    def invalidate_pattern(self, pattern: str, tenant_id: Optional[str] = None) -> None:
        """
        Invalidate all keys matching pattern (simple substring match for memory).

        Args:
            pattern: Pattern to match
            tenant_id: Optional tenant ID to limit invalidation to specific tenant
        """
        if tenant_id:
            pattern = f"{tenant_id}:{pattern}"
        if self.backend == "redis":
            keys = self._client.keys(f"{self.config.namespace}:{pattern}*")
            if keys:
                self._client.delete(*keys)
            return

        to_delete = [k for k in self._store if pattern in k]
        for k in to_delete:
            self._store.pop(k, None)

    def _evict_if_needed(self) -> None:
        while len(self._store) > self.config.max_size:
            # Pop oldest (LRU)
            self._store.popitem(last=False)


