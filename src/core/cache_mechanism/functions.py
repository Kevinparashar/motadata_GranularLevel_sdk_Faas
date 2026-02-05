"""
Cache Mechanism - High-Level Functions

Factory functions, convenience functions, and utilities for cache mechanism.
"""


from typing import Any, Dict, Optional

from .cache import CacheConfig, CacheMechanism

# ============================================================================
# Factory Functions
# ============================================================================


def create_cache(
    backend: str = "memory",
    default_ttl: int = 300,
    max_size: int = 1024,
    dragonfly_url: Optional[str] = None,
    namespace: str = "sdk_cache",
    **kwargs: Any,
) -> CacheMechanism:
    """
    Create and configure a cache with default settings.

    Args:
        backend: Cache backend ("memory" or "dragonfly")
        default_ttl: Default TTL in seconds
        max_size: Maximum cache size (only for memory backend)
        dragonfly_url: Dragonfly connection URL (required for Dragonfly backend)
        namespace: Cache namespace to prevent key collisions
        **kwargs: Additional cache configuration

    Returns:
        Configured CacheMechanism instance

    Example:
        >>> # In-memory cache
        >>> cache = create_cache(backend="memory", default_ttl=600)

        >>> # Dragonfly cache
        >>> cache = create_cache(
        ...     backend="dragonfly",
        ...     dragonfly_url="dragonfly://localhost:6379/0"
        ... )
    """
    config = CacheConfig(
        backend=backend,
        default_ttl=default_ttl,
        max_size=max_size,
        dragonfly_url=dragonfly_url,
        namespace=namespace,
    )
    return CacheMechanism(config=config)


def create_memory_cache(
    default_ttl: int = 300, max_size: int = 1024, namespace: str = "sdk_cache"
) -> CacheMechanism:
    """
    Create an in-memory cache with LRU eviction.

    Args:
        default_ttl: Default TTL in seconds
        max_size: Maximum cache size
        namespace: Cache namespace

    Returns:
        CacheMechanism instance with memory backend

    Example:
        >>> cache = create_memory_cache(default_ttl=600, max_size=2048)
    """
    return create_cache(
        backend="memory", default_ttl=default_ttl, max_size=max_size, namespace=namespace
    )


def create_dragonfly_cache(
    dragonfly_url: str = "dragonfly://localhost:6379/0",
    default_ttl: int = 300,
    namespace: str = "sdk_cache",
) -> CacheMechanism:
    """
    Create a Dragonfly cache.

    Args:
        dragonfly_url: Dragonfly connection URL
        default_ttl: Default TTL in seconds
        namespace: Cache namespace

    Returns:
        CacheMechanism instance with Dragonfly backend

    Example:
        >>> cache = create_dragonfly_cache(
        ...     dragonfly_url="dragonfly://localhost:6379/0",
        ...     default_ttl=600
        ... )
    """
    return create_cache(
        backend="dragonfly",
        dragonfly_url=dragonfly_url,
        default_ttl=default_ttl,
        namespace=namespace,
    )


def configure_cache(
    backend: str = "memory",
    default_ttl: int = 300,
    max_size: int = 1024,
    dragonfly_url: Optional[str] = None,
    namespace: str = "sdk_cache",
) -> CacheConfig:
    """
    Create a CacheConfig with specified settings.

    Args:
        backend: Cache backend ("memory" or "dragonfly")
        default_ttl: Default TTL in seconds
        max_size: Maximum cache size (only for memory backend)
        dragonfly_url: Dragonfly connection URL
        namespace: Cache namespace

    Returns:
        CacheConfig instance

    Example:
        >>> config = configure_cache(
        ...     backend="memory",
        ...     default_ttl=600,
        ...     max_size=2048
        ... )
        >>> cache = CacheMechanism(config=config)
    """
    return CacheConfig(
        backend=backend,
        default_ttl=default_ttl,
        max_size=max_size,
        dragonfly_url=dragonfly_url,
        namespace=namespace,
    )


# ============================================================================
# High-Level Convenience Functions
# ============================================================================


async def cache_get(cache: CacheMechanism, key: str) -> Optional[Any]:
    """
    Get a value from cache asynchronously (high-level convenience).

    Args:
        cache: CacheMechanism instance
        key: Cache key

    Returns:
        Cached value or None if not found/expired

    Example:
        >>> value = await cache_get(cache, "user:123")
    """
    return await cache.get(key)


async def cache_set(cache: CacheMechanism, key: str, value: Any, ttl: Optional[int] = None) -> None:
    """
    Set a value in cache asynchronously (high-level convenience).
    
    Example:
                            >>> await cache_set(cache, "user:123", {"name": "John"}, ttl=600)
    
    Args:
        cache (CacheMechanism): Cache instance used to store and fetch cached results.
        key (str): Input parameter for this operation.
        value (Any): Input parameter for this operation.
        ttl (Optional[int]): Input parameter for this operation.
    
    Returns:
        None: Result of the operation.
    """
    await cache.set(key, value, ttl=ttl)


async def cache_delete(cache: CacheMechanism, key: str) -> None:
    """
    Delete a value from cache asynchronously (high-level convenience).
    
    Example:
                            >>> await cache_delete(cache, "user:123")
    
    Args:
        cache (CacheMechanism): Cache instance used to store and fetch cached results.
        key (str): Input parameter for this operation.
    
    Returns:
        None: Result of the operation.
    """
    await cache.delete(key)


async def cache_clear_pattern(cache: CacheMechanism, pattern: str) -> None:
    """
    Clear all keys matching a pattern asynchronously (high-level convenience).
    
    Example:
                            >>> await cache_clear_pattern(cache, "user:*")
    
    Args:
        cache (CacheMechanism): Cache instance used to store and fetch cached results.
        pattern (str): Input parameter for this operation.
    
    Returns:
        None: Result of the operation.
    """
    await cache.invalidate_pattern(pattern)


# ============================================================================
# Utility Functions
# ============================================================================


async def cache_or_compute(
    cache: CacheMechanism, key: str, compute_func: Any, ttl: Optional[int] = None
) -> Any:
    """
    Get from cache or compute and cache the result asynchronously (utility function).

    Args:
        cache: CacheMechanism instance
        key: Cache key
        compute_func: Function to compute value if not cached (can be sync or async)
        ttl: Optional TTL in seconds

    Returns:
        Cached or computed value

    Example:
        >>> async def expensive_operation():
        ...     # Expensive computation
        ...     return result
        >>> value = await cache_or_compute(cache, "expensive:key", expensive_operation, ttl=3600)
    """
    import asyncio
    
    cached = await cache.get(key)
    if cached is not None:
        return cached

    # Support both sync and async compute functions
    if asyncio.iscoroutinefunction(compute_func):
        value = await compute_func()
    else:
        value = compute_func()
    
    await cache.set(key, value, ttl=ttl)
    return value


async def batch_cache_set(
    cache: CacheMechanism, items: Dict[str, Any], ttl: Optional[int] = None
) -> None:
    """
    Set multiple values in cache at once asynchronously (utility function).
    
    Example:
                            >>> items = {"user:1": {"name": "John"}, "user:2": {"name": "Jane"}}
                            >>> await batch_cache_set(cache, items, ttl=600)
    
    Args:
        cache (CacheMechanism): Cache instance used to store and fetch cached results.
        items (Dict[str, Any]): Input parameter for this operation.
        ttl (Optional[int]): Input parameter for this operation.
    
    Returns:
        None: Result of the operation.
    """
    import asyncio
    # Use asyncio.gather for parallel cache operations
    await asyncio.gather(*[cache.set(key, value, ttl=ttl) for key, value in items.items()])


def batch_cache_get(cache: CacheMechanism, keys: list[str]) -> Dict[str, Optional[Any]]:
    """
    Get multiple values from cache at once (utility function).

    Args:
        cache: CacheMechanism instance
        keys: List of cache keys

    Returns:
        Dictionary mapping keys to values (None if not found)

    Example:
        >>> values = batch_cache_get(cache, ["user:1", "user:2", "user:3"])
        >>> print(values["user:1"])
    """
    return {key: cache.get(key) for key in keys}


__all__ = [
    # Factory functions
    "create_cache",
    "create_memory_cache",
    "create_dragonfly_cache",
    "configure_cache",
    # High-level convenience functions
    "cache_get",
    "cache_set",
    "cache_delete",
    "cache_clear_pattern",
    # Utility functions
    "cache_or_compute",
    "batch_cache_set",
    "batch_cache_get",
]
