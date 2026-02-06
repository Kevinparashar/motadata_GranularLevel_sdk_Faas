"""
Unit Tests for Cache Component

Tests caching operations for LLM responses and embeddings.
"""


from unittest.mock import patch

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
        from unittest.mock import AsyncMock
        mock_redis_client = AsyncMock()
        mock_aioredis_module.from_url.return_value = mock_redis_client
        mock_redis_client.get.return_value = b"value1"
        mock_redis_client.set.return_value = True

        config = CacheConfig(backend="dragonfly", dragonfly_url="dragonfly://localhost:6379/0")
        cache = CacheMechanism(config=config)

        await cache.set("key1", "value1")
        value = await cache.get("key1")
        # Dragonfly (Redis-compatible) returns bytes, so we check it's not None
        assert value is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
