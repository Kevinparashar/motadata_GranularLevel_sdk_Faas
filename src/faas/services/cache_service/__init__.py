"""
Cache Service - FaaS implementation of Cache Mechanism.

Provides distributed caching for performance optimization.
"""

from .service import CacheService, create_cache_service
from .models import (
    GetCacheRequest,
    SetCacheRequest,
    InvalidateCacheRequest,
    CacheResponse,
)

__all__ = [
    "CacheService",
    "create_cache_service",
    "GetCacheRequest",
    "SetCacheRequest",
    "InvalidateCacheRequest",
    "CacheResponse",
]

