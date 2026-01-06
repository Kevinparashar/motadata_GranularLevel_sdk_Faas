"""
Cache Mechanism

Provides cache utilities for SDK components.
"""

from .cache import CacheMechanism, CacheConfig
from .functions import (
    create_cache,
    create_memory_cache,
    create_redis_cache,
    configure_cache,
    cache_get,
    cache_set,
    cache_delete,
    cache_clear_pattern,
    cache_or_compute,
    batch_cache_set,
    batch_cache_get,
)

__all__ = [
    # Core classes
    "CacheMechanism",
    "CacheConfig",
    # Factory functions
    "create_cache",
    "create_memory_cache",
    "create_redis_cache",
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

