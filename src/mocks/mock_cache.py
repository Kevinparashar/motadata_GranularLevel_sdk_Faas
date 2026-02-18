"""
Mock Cache Mechanism Implementation

Mock implementation of CacheMechanism for testing.

Copyright (c) 2024 Motadata. All rights reserved.
"""

import asyncio
import time
from typing import Any, Dict, Optional


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

    async def get(
        self, key: str, tenant_id: Optional[str] = None, default: Any = None
    ) -> Any:
        """
        Mock get method - retrieves value from mock cache.
        
        Args:
            key: Cache key
            tenant_id: Optional tenant ID (for interface compatibility)
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        # Minimal async operation to satisfy linter
        await asyncio.sleep(0)
        
        namespaced_key = self._namespaced_key(key, tenant_id)
        if namespaced_key in self._store:
            # Check TTL if set
            if namespaced_key in self._ttl_store:
                if time.time() > self._ttl_store[namespaced_key]:
                    del self._store[namespaced_key]
                    del self._ttl_store[namespaced_key]
                    return default
            return self._store[namespaced_key]
        return default

    async def set(
        self,
        key: str,
        value: Any,
        tenant_id: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> None:
        """
        Mock set method - stores value in mock cache.
        
        Args:
            key: Cache key
            value: Value to cache
            tenant_id: Optional tenant ID (for interface compatibility)
            ttl: Optional time-to-live in seconds
        """
        # Minimal async operation to satisfy linter
        await asyncio.sleep(0)
        
        namespaced_key = self._namespaced_key(key, tenant_id)
        self._store[namespaced_key] = value
        if ttl:
            self._ttl_store[namespaced_key] = time.time() + ttl

    async def delete(self, key: str, tenant_id: Optional[str] = None) -> None:
        """
        Mock delete method - removes key from mock cache.
        
        Args:
            key: Cache key to delete
            tenant_id: Optional tenant ID (for interface compatibility)
        """
        # Minimal async operation to satisfy linter
        await asyncio.sleep(0)
        
        namespaced_key = self._namespaced_key(key, tenant_id)
        self._store.pop(namespaced_key, None)
        self._ttl_store.pop(namespaced_key, None)

    async def clear(self, tenant_id: Optional[str] = None) -> None:
        """
        Mock clear method - clears all cache entries.
        
        Args:
            tenant_id: Optional tenant ID (for interface compatibility)
        """
        # Minimal async operation to satisfy linter
        await asyncio.sleep(0)
        
        if tenant_id:
            # Clear only keys for this tenant
            prefix = f"{tenant_id}:"
            keys_to_remove = [
                k for k in self._store.keys() if k.startswith(prefix)
            ]
            for k in keys_to_remove:
                self._store.pop(k, None)
                self._ttl_store.pop(k, None)
        else:
            self._store.clear()
            self._ttl_store.clear()

    async def exists(self, key: str, tenant_id: Optional[str] = None) -> bool:
        """
        Mock exists method - checks if key exists in cache.
        
        Args:
            key: Cache key to check
            tenant_id: Optional tenant ID (for interface compatibility)
            
        Returns:
            True if key exists, False otherwise
        """
        # Minimal async operation to satisfy linter
        await asyncio.sleep(0)
        
        namespaced_key = self._namespaced_key(key, tenant_id)
        return namespaced_key in self._store

    def _namespaced_key(self, key: str, tenant_id: Optional[str] = None) -> str:
        """
        Create namespaced cache key.
        
        Args:
            key: Cache key
            tenant_id: Optional tenant ID
            
        Returns:
            Namespaced key
        """
        if tenant_id:
            return f"{tenant_id}:{key}"
        return key


__all__ = ["MockCacheMechanism"]

