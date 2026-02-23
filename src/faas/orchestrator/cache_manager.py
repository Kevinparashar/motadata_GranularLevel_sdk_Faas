"""
Unified Cache Manager for orchestrator-level caching.

Provides unified caching across all AI features at the entry point.
"""

import logging
from typing import Any, Dict, Optional

from ...core.cache_mechanism import CacheMechanism, CacheConfig
from .cache_strategy import CacheStrategy, CacheStrategyType, get_cache_strategy

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Unified cache manager for orchestrator-level caching.

    Provides caching across all AI features with standardized keys and strategies.
    """

    def __init__(
        self,
        cache: Optional[CacheMechanism] = None,
        cache_config: Optional[CacheConfig] = None,
        default_strategy: CacheStrategyType = CacheStrategyType.QUERY,
    ):
        """
        Initialize cache manager.

        Args:
            cache: Optional cache mechanism instance
            cache_config: Optional cache configuration
            default_strategy: Default cache strategy type
        """
        self.cache = cache or CacheMechanism(cache_config or CacheConfig())
        self.default_strategy = get_cache_strategy(default_strategy)

        # Feature-specific strategies
        self._strategies: Dict[str, CacheStrategy] = {
            "agent_chat": get_cache_strategy(CacheStrategyType.CONVERSATION),
            "agent_task": get_cache_strategy(CacheStrategyType.QUERY),
            "rag_query": get_cache_strategy(CacheStrategyType.QUERY),
            "direct_llm": get_cache_strategy(CacheStrategyType.QUERY),
            "document_ingestion": get_cache_strategy(CacheStrategyType.NONE),
            "prompt_generation": get_cache_strategy(CacheStrategyType.QUERY),
            "ml_prediction": get_cache_strategy(CacheStrategyType.QUERY),
        }

    def get_strategy(self, feature: str) -> CacheStrategy:
        """
        Get cache strategy for feature.

        Args:
            feature: AI feature name

        Returns:
            CacheStrategy instance
        """
        return self._strategies.get(feature, self.default_strategy)

    async def get(
        self,
        feature: str,
        query: str,
        tenant_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        """
        Get cached value for feature and query.

        Args:
            feature: AI feature name
            query: User query text
            tenant_id: Optional tenant ID
            context: Optional context

        Returns:
            Cached value if found, None otherwise
        """
        strategy = self.get_strategy(feature)

        # Check if should cache
        if not strategy.should_cache(feature, context):
            return None

        # Generate cache key
        cache_key = strategy.generate_cache_key(feature, query, tenant_id, context)
        if not cache_key:
            return None

        try:
            cached_value = await self.cache.get(cache_key, tenant_id=tenant_id)
            if cached_value:
                logger.debug(f"Cache hit for {feature}: {query[:50]}")
            return cached_value
        except Exception as e:
            logger.warning(f"Cache get failed for {feature}: {e}")
            return None

    async def set(
        self,
        feature: str,
        query: str,
        value: Any,
        tenant_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Set cached value for feature and query.

        Args:
            feature: AI feature name
            query: User query text
            value: Value to cache
            tenant_id: Optional tenant ID
            context: Optional context
        """
        strategy = self.get_strategy(feature)

        # Check if should cache
        if not strategy.should_cache(feature, context):
            return

        # Generate cache key
        cache_key = strategy.generate_cache_key(feature, query, tenant_id, context)
        if not cache_key:
            return

        # Get TTL
        ttl = strategy.get_ttl(feature)

        try:
            await self.cache.set(cache_key, value, tenant_id=tenant_id, ttl=ttl)
            logger.debug(f"Cached {feature}: {query[:50]} (TTL: {ttl}s)")
        except Exception as e:
            logger.warning(f"Cache set failed for {feature}: {e}")

    async def invalidate(
        self,
        feature: Optional[str] = None,
        tenant_id: Optional[str] = None,
        pattern: Optional[str] = None,
    ) -> None:
        """
        Invalidate cache entries.

        Args:
            feature: Optional feature name to invalidate
            tenant_id: Optional tenant ID to invalidate
            pattern: Optional pattern to match keys
        """
        try:
            if pattern:
                # Use pattern-based invalidation
                await self.cache.invalidate_pattern(pattern, tenant_id=tenant_id)
            elif feature and tenant_id:
                # Invalidate specific feature for tenant
                cache_key_pattern = f"orchestrator:{feature}:tenant:{tenant_id}:*"
                await self.cache.invalidate_pattern(cache_key_pattern, tenant_id=tenant_id)
            elif tenant_id:
                # Invalidate all for tenant
                cache_key_pattern = f"orchestrator:*:tenant:{tenant_id}:*"
                await self.cache.invalidate_pattern(cache_key_pattern, tenant_id=tenant_id)
            else:
                logger.warning("Cache invalidation requires feature, tenant_id, or pattern")
        except Exception as e:
            logger.warning(f"Cache invalidation failed: {e}")


def create_cache_manager(
    cache: Optional[CacheMechanism] = None,
    cache_config: Optional[CacheConfig] = None,
    default_strategy: CacheStrategyType = CacheStrategyType.QUERY,
) -> CacheManager:
    """
    Create a cache manager instance.

    Args:
        cache: Optional cache mechanism instance
        cache_config: Optional cache configuration
        default_strategy: Default cache strategy type

    Returns:
        CacheManager instance
    """
    return CacheManager(
        cache=cache,
        cache_config=cache_config,
        default_strategy=default_strategy,
    )

