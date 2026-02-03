"""
Cache Mechanism

Provides cache utilities for SDK components.
"""


from .cache import CacheConfig, CacheMechanism
from .functions import (
    batch_cache_get,
    batch_cache_set,
    cache_clear_pattern,
    cache_delete,
    cache_get,
    cache_or_compute,
    cache_set,
    configure_cache,
    create_cache,
    create_dragonfly_cache,
    create_memory_cache,
)

__all__ = [
    # Core classes
    "CacheMechanism",
    "CacheConfig",
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
