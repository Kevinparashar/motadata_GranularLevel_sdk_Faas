"""
Mock Cache Mechanism Implementation

Mock implementation of CacheMechanism for testing.
"""

from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock


class MockCacheMechanism:
    """
    Mock implementation of CacheMechanism for testing.
    
    Provides an in-memory mock cache that can be used in tests
    without requiring an actual cache backend.
    """

    def __init__(self, config: Optional[Any] = None):
        """
        Initialize mock cache mechanism.
        
        Args:
            config: Optional cache configuration (not used in mock)
        """
        self.config = config
        self._store: Dict[str, Any] = {}
        self._ttl_store: Dict[str, float] = {}

    async def get(self, key: str, default: Any = None) -> Any:
        """
        Mock get method - retrieves value from mock cache.
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        if key in self._store:
            # Check TTL if set
            if key in self._ttl_store:
                import time
                if time.time() > self._ttl_store[key]:
                    del self._store[key]
                    del self._ttl_store[key]
                    return default
            return self._store[key]
        return default

    async def set(
        self, key: str, value: Any, ttl: Optional[int] = None
    ) -> None:
        """
        Mock set method - stores value in mock cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional time-to-live in seconds
        """
        self._store[key] = value
        if ttl:
            import time
            self._ttl_store[key] = time.time() + ttl

    async def delete(self, key: str) -> None:
        """
        Mock delete method - removes key from mock cache.
        
        Args:
            key: Cache key to delete
        """
        self._store.pop(key, None)
        self._ttl_store.pop(key, None)

    async def clear(self) -> None:
        """Mock clear method - clears all cache entries."""
        self._store.clear()
        self._ttl_store.clear()

    async def exists(self, key: str) -> bool:
        """
        Mock exists method - checks if key exists in cache.
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists, False otherwise
        """
        return key in self._store


__all__ = ["MockCacheMechanism"]

