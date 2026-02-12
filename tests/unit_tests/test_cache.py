"""
Unit Tests for Cache Component

Tests caching operations for LLM responses and embeddings.
"""

import time
from unittest.mock import AsyncMock, patch

import pytest

from src.core.cache_mechanism import CacheConfig, CacheMechanism


class TestCacheMechanism:
    """Test CacheMechanism."""

    def test_memory_cache_initialization(self):
        """Test memory cache initialization."""
        config = CacheConfig(backend="memory")
        cache = CacheMechanism(config=config)
        assert cache.config.backend == "memory"

    @pytest.mark.asyncio
    async def test_set_get(self):
        """Test set and get operations."""
        cache = CacheMechanism(config=CacheConfig(backend="memory"))

        await cache.set("key1", "value1")
        value = await cache.get("key1")
        assert value == "value1"

    @pytest.mark.asyncio
    async def test_set_with_ttl(self):
        """Test set with TTL."""
        import asyncio
        cache = CacheMechanism(config=CacheConfig(backend="memory"))

        await cache.set("key1", "value1", ttl=1)
        value = await cache.get("key1")
        assert value == "value1"

        # Wait for expiration
        await asyncio.sleep(1.1)
        expired_value = await cache.get("key1")
        assert expired_value is None

    @pytest.mark.asyncio
    async def test_delete(self):
        """Test delete operation."""
        cache = CacheMechanism(config=CacheConfig(backend="memory"))

        await cache.set("key1", "value1")
        await cache.delete("key1")
        value = await cache.get("key1")
        assert value is None

    @pytest.mark.asyncio
    async def test_invalidate_pattern(self):
        """Test pattern-based invalidation."""
        cache = CacheMechanism(config=CacheConfig(backend="memory"))

        await cache.set("user:1", "value1")
        await cache.set("user:2", "value2")
        await cache.set("post:1", "value3")

        await cache.invalidate_pattern("user:")

        assert await cache.get("user:1") is None
        assert await cache.get("user:2") is None
        assert await cache.get("post:1") == "value3"  # Should remain

    @pytest.mark.asyncio
    @patch("src.core.cache_mechanism.cache.aioredis")
    async def test_dragonfly_cache(self, mock_aioredis_module):
        """Test Dragonfly cache backend."""
        mock_redis_client = AsyncMock()
        # from_url is an async function, so it should return a coroutine
        mock_aioredis_module.from_url = AsyncMock(return_value=mock_redis_client)
        mock_redis_client.get = AsyncMock(return_value=b"value1")
        mock_redis_client.set = AsyncMock(return_value=True)

        config = CacheConfig(backend="dragonfly", dragonfly_url="dragonfly://localhost:6379/0")
        cache = CacheMechanism(config=config)

        await cache.set("key1", "value1")
        value = await cache.get("key1")
        # Dragonfly (Redis-compatible) returns bytes, so we check it's not None
        assert value is not None

    def test_namespaced_key_with_tenant(self):
        """Test namespaced key generation with tenant_id."""
        cache = CacheMechanism(config=CacheConfig(namespace="test"))
        key = cache._namespaced_key("mykey", tenant_id="tenant1")
        assert key == "test:tenant1:mykey"

    def test_namespaced_key_without_tenant(self):
        """Test namespaced key generation without tenant_id."""
        cache = CacheMechanism(config=CacheConfig(namespace="test"))
        key = cache._namespaced_key("mykey")
        assert key == "test:mykey"

    @pytest.mark.asyncio
    @patch("src.core.cache_mechanism.cache.aioredis", None)
    async def test_dragonfly_import_error(self):
        """Test ImportError when aioredis is not available."""
        config = CacheConfig(backend="dragonfly")
        cache = CacheMechanism(config=config)
        
        with pytest.raises(ImportError, match="aioredis required for Dragonfly backend"):
            await cache._ensure_async_client()

    @pytest.mark.asyncio
    @patch("src.core.cache_mechanism.cache.aioredis")
    async def test_delete_dragonfly(self, mock_aioredis_module):
        """Test delete operation with Dragonfly backend."""
        mock_redis_client = AsyncMock()
        mock_aioredis_module.from_url = AsyncMock(return_value=mock_redis_client)
        mock_redis_client.delete = AsyncMock(return_value=1)

        config = CacheConfig(backend="dragonfly")
        cache = CacheMechanism(config=config)
        
        await cache.delete("key1", tenant_id="tenant1")
        mock_redis_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_pattern_with_tenant(self):
        """Test pattern invalidation with tenant_id."""
        cache = CacheMechanism(config=CacheConfig(backend="memory"))
        
        await cache.set("key1", "value1", tenant_id="tenant1")
        await cache.set("key2", "value2", tenant_id="tenant1")
        await cache.set("key3", "value3", tenant_id="tenant2")
        
        await cache.invalidate_pattern("key", tenant_id="tenant1")
        
        assert await cache.get("key1", tenant_id="tenant1") is None
        assert await cache.get("key2", tenant_id="tenant1") is None
        assert await cache.get("key3", tenant_id="tenant2") == "value3"

    @pytest.mark.asyncio
    @patch("src.core.cache_mechanism.cache.aioredis")
    async def test_invalidate_pattern_dragonfly(self, mock_aioredis_module):
        """Test pattern invalidation with Dragonfly backend."""
        mock_redis_client = AsyncMock()
        mock_aioredis_module.from_url = AsyncMock(return_value=mock_redis_client)
        mock_redis_client.scan = AsyncMock(side_effect=[
            (b'1', [b'key1', b'key2']),
            (b'0', [b'key3'])
        ])
        mock_redis_client.delete = AsyncMock(return_value=3)

        config = CacheConfig(backend="dragonfly", namespace="test")
        cache = CacheMechanism(config=config)
        
        await cache.invalidate_pattern("pattern", tenant_id="tenant1")
        
        assert mock_redis_client.scan.called
        assert mock_redis_client.delete.called

    def test_evict_if_needed(self):
        """Test cache eviction when max size exceeded."""
        config = CacheConfig(backend="memory", max_size=2)
        cache = CacheMechanism(config=config)
        
        # Fill cache beyond max size
        cache._store["key1"] = ("value1", time.time() + 100)
        cache._store["key2"] = ("value2", time.time() + 100)
        cache._store["key3"] = ("value3", time.time() + 100)
        
        cache._evict_if_needed()
        
        assert len(cache._store) == 2
        assert "key1" not in cache._store  # Oldest should be evicted

    @pytest.mark.asyncio
    async def test_cache_prompt_interpretation_dict(self):
        """Test caching prompt interpretation as dict."""
        cache = CacheMechanism(config=CacheConfig(backend="memory"))
        
        interpretation = {"key": "value", "number": 42}
        await cache.cache_prompt_interpretation("hash123", interpretation)
        
        cached = await cache.get("prompt_interp:hash123")
        assert isinstance(cached, str)
        assert "key" in cached

    @pytest.mark.asyncio
    async def test_cache_prompt_interpretation_string(self):
        """Test caching prompt interpretation as string."""
        cache = CacheMechanism(config=CacheConfig(backend="memory"))
        
        interpretation = "simple string"
        await cache.cache_prompt_interpretation("hash123", interpretation)
        
        cached = await cache.get("prompt_interp:hash123")
        assert cached == "simple string"

    @pytest.mark.asyncio
    async def test_get_prompt_interpretation_json(self):
        """Test getting cached prompt interpretation from JSON."""
        cache = CacheMechanism(config=CacheConfig(backend="memory"))
        
        interpretation = {"key": "value"}
        await cache.cache_prompt_interpretation("hash123", interpretation)
        
        result = await cache.get_prompt_interpretation("hash123")
        assert result == interpretation

    @pytest.mark.asyncio
    async def test_get_prompt_interpretation_invalid_json(self):
        """Test getting prompt interpretation with invalid JSON."""
        cache = CacheMechanism(config=CacheConfig(backend="memory"))
        
        # Store invalid JSON string
        await cache.set("prompt_interp:hash123", "invalid json {")
        
        result = await cache.get_prompt_interpretation("hash123")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_prompt_interpretation_not_string(self):
        """Test getting prompt interpretation that's not a string."""
        cache = CacheMechanism(config=CacheConfig(backend="memory"))
        
        # Store non-string value
        await cache.set("prompt_interp:hash123", {"already": "dict"})
        
        result = await cache.get_prompt_interpretation("hash123")
        assert result == {"already": "dict"}

    @pytest.mark.asyncio
    async def test_get_prompt_interpretation_not_found(self):
        """Test getting prompt interpretation when not cached - covers line 161."""
        cache = CacheMechanism(config=CacheConfig(backend="memory"))
        
        # Try to get non-existent interpretation
        result = await cache.get_prompt_interpretation("nonexistent_hash")
        assert result is None

    @pytest.mark.asyncio
    async def test_clear_memory_with_tenant(self):
        """Test clearing cache with tenant_id for memory backend."""
        cache = CacheMechanism(config=CacheConfig(backend="memory", namespace="test"))
        
        await cache.set("key1", "value1", tenant_id="tenant1")
        await cache.set("key2", "value2", tenant_id="tenant1")
        await cache.set("key3", "value3", tenant_id="tenant2")
        
        await cache.clear(tenant_id="tenant1")
        
        assert await cache.get("key1", tenant_id="tenant1") is None
        assert await cache.get("key2", tenant_id="tenant1") is None
        assert await cache.get("key3", tenant_id="tenant2") == "value3"

    @pytest.mark.asyncio
    async def test_clear_memory_all(self):
        """Test clearing all cache entries for memory backend."""
        cache = CacheMechanism(config=CacheConfig(backend="memory"))
        
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        
        await cache.clear()
        
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    @pytest.mark.asyncio
    @patch("src.core.cache_mechanism.cache.aioredis")
    async def test_clear_dragonfly(self, mock_aioredis_module):
        """Test clearing cache with Dragonfly backend."""
        mock_redis_client = AsyncMock()
        mock_aioredis_module.from_url = AsyncMock(return_value=mock_redis_client)
        mock_redis_client.scan = AsyncMock(return_value=(b'0', []))
        mock_redis_client.delete = AsyncMock(return_value=0)

        config = CacheConfig(backend="dragonfly", namespace="test")
        cache = CacheMechanism(config=config)
        
        await cache.clear(tenant_id="tenant1")
        
        assert mock_redis_client.scan.called

    @pytest.mark.asyncio
    @patch("src.core.cache_mechanism.cache.aioredis")
    async def test_close(self, mock_aioredis_module):
        """Test closing async client connections."""
        mock_redis_client = AsyncMock()
        mock_aioredis_module.from_url = AsyncMock(return_value=mock_redis_client)
        mock_redis_client.close = AsyncMock()

        config = CacheConfig(backend="dragonfly")
        cache = CacheMechanism(config=config)
        
        # Initialize client
        await cache._ensure_async_client()
        
        # Close it
        await cache.close()
        
        mock_redis_client.close.assert_called_once()
        assert cache._async_client is None

    @pytest.mark.asyncio
    async def test_close_no_client(self):
        """Test close when no client exists."""
        cache = CacheMechanism(config=CacheConfig(backend="memory"))
        
        # Should not raise error
        await cache.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
