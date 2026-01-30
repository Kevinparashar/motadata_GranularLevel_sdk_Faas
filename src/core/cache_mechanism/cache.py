"""
Cache Mechanism

Provides a simple pluggable cache layer with in-memory and Dragonfly backends,
supporting TTL, basic LRU eviction, and pattern-based invalidation.
"""


import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, List, Optional, cast

try:
    import redis  # Dragonfly is Redis-compatible
except ImportError:  # pragma: no cover - optional dependency
    redis = None


@dataclass
class CacheConfig:
    backend: str = "memory"  # "memory" or "dragonfly"
    default_ttl: int = 300
    max_size: int = 1024  # only applies to memory backend
    dragonfly_url: Optional[str] = None
    namespace: str = "sdk_cache"


class CacheMechanism:
    """
    Cache wrapper that supports in-memory and Dragonfly backends with TTL support.
    """

    def __init__(self, config: Optional[CacheConfig] = None) -> None:
        self.config = config or CacheConfig()
        self.backend = self.config.backend

        if self.backend == "dragonfly":
            if redis is None:
                raise ImportError(
                    "redis package is required for Dragonfly backend (Dragonfly is Redis-compatible)"
                )
            self._client = redis.Redis.from_url(
                self.config.dragonfly_url or "dragonfly://localhost:6379/0"
            )
        else:
            # Simple in-memory LRU with TTL
            self._store: OrderedDict[str, tuple[Any, float]] = OrderedDict()

    def _namespaced_key(self, key: str, tenant_id: Optional[str] = None) -> str:
        """Create namespaced cache key with optional tenant isolation."""
        if tenant_id:
            return f"{self.config.namespace}:{tenant_id}:{key}"
        return f"{self.config.namespace}:{key}"

    def set(
        self, key: str, value: Any, tenant_id: Optional[str] = None, ttl: Optional[int] = None
    ) -> None:
        """
        Store a value in cache with TTL.

        COST IMPACT: Caching responses saves LLM API costs.
        - Cache hit = $0 cost (no API call)
        - Cache miss = normal API cost (~$0.001-0.01 per call)
        - Typical savings: 50-90% cost reduction for repeated queries
        """
        ttl = ttl or self.config.default_ttl
        expires_at = time.time() + ttl
        namespaced = self._namespaced_key(key, tenant_id=tenant_id)

        if self.backend == "dragonfly":
            # Dragonfly backend: Distributed cache, survives process restarts
            self._client.set(namespaced, value, ex=ttl)
            return

        # MEMORY BACKEND: In-memory LRU cache with TTL
        # LRU (Least Recently Used) eviction: removes least recently accessed items when full
        # This keeps frequently accessed items in cache, maximizing cache hit rate
        self._store[namespaced] = (value, expires_at)
        self._store.move_to_end(namespaced)  # Mark as recently used (LRU)
        self._evict_if_needed()  # Remove oldest items if cache is full

    def get(self, key: str, tenant_id: Optional[str] = None) -> Optional[Any]:
        """
        Retrieve a value from cache.

        PERFORMANCE: Cache hits are instant (<1ms), avoiding expensive API calls.
        Returns None if key not found or expired (cache miss).
        """
        namespaced = self._namespaced_key(key, tenant_id=tenant_id)

        if self.backend == "dragonfly":
            value = self._client.get(namespaced)
            return value

        if namespaced not in self._store:
            return None  # Cache miss

        value, expires_at = self._store[namespaced]
        if expires_at < time.time():
            # TTL expired: Remove from cache (cache miss)
            self._store.pop(namespaced, None)
            return None

        # LRU: Mark as recently used (move to end of OrderedDict)
        # This ensures frequently accessed items stay in cache longer
        self._store.move_to_end(namespaced)
        return value  # Cache hit: return cached value

    def delete(self, key: str, tenant_id: Optional[str] = None) -> None:
        namespaced = self._namespaced_key(key, tenant_id=tenant_id)
        if self.backend == "dragonfly":
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
        if self.backend == "dragonfly":
            # Redis keys() returns a list synchronously
            keys_result = self._client.keys(f"{self.config.namespace}:{pattern}*")
            keys: List[Any] = cast(List[Any], keys_result)
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

    def cache_prompt_interpretation(
        self,
        prompt_hash: str,
        interpretation: Any,
        tenant_id: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> None:
        """
        Cache prompt interpretation result.

        Args:
            prompt_hash: Hash of the prompt
            interpretation: Interpretation result (will be JSON serialized)
            tenant_id: Optional tenant ID
            ttl: Optional TTL override
        """
        import json

        if isinstance(interpretation, dict):
            interpretation = json.dumps(interpretation)
        self.set(f"prompt_interp:{prompt_hash}", interpretation, tenant_id=tenant_id, ttl=ttl)

    def get_prompt_interpretation(
        self, prompt_hash: str, tenant_id: Optional[str] = None
    ) -> Optional[Any]:
        """
        Get cached prompt interpretation.

        Args:
            prompt_hash: Hash of the prompt
            tenant_id: Optional tenant ID

        Returns:
            Cached interpretation or None
        """
        import json

        cached = self.get(f"prompt_interp:{prompt_hash}", tenant_id=tenant_id)
        if cached:
            try:
                if isinstance(cached, str):
                    return json.loads(cached)
                return cached
            except Exception:
                return None
        return None
