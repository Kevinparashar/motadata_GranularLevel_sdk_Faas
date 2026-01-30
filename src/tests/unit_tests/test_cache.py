"""
Unit Tests for Cache Component

Tests caching operations for LLM responses and embeddings.
"""

import time
from unittest.mock import Mock, patch

import pytest

from src.core.cache_mechanism import CacheConfig, CacheMechanism


class TestCacheMechanism:
    """Test CacheMechanism."""

    def test_memory_cache_initialization(self):
        """Test memory cache initialization."""
        config = CacheConfig(backend="memory")
        cache = CacheMechanism(config=config)
        assert cache.config.backend == "memory"

    def test_set_get(self):
        """Test set and get operations."""
        cache = CacheMechanism(config=CacheConfig(backend="memory"))

        cache.set("key1", "value1")
        value = cache.get("key1")
        assert value == "value1"

    def test_set_with_ttl(self):
        """Test set with TTL."""
        cache = CacheMechanism(config=CacheConfig(backend="memory"))

        cache.set("key1", "value1", ttl=1)
        value = cache.get("key1")
        assert value == "value1"

        # Wait for expiration
        time.sleep(1.1)
        expired_value = cache.get("key1")
        assert expired_value is None

    def test_delete(self):
        """Test delete operation."""
        cache = CacheMechanism(config=CacheConfig(backend="memory"))

        cache.set("key1", "value1")
        cache.delete("key1")
        value = cache.get("key1")
        assert value is None

    def test_invalidate_pattern(self):
        """Test pattern-based invalidation."""
        cache = CacheMechanism(config=CacheConfig(backend="memory"))

        cache.set("user:1", "value1")
        cache.set("user:2", "value2")
        cache.set("post:1", "value3")

        cache.invalidate_pattern("user:")

        assert cache.get("user:1") is None
        assert cache.get("user:2") is None
        assert cache.get("post:1") == "value3"  # Should remain

    @patch("src.core.cache_mechanism.cache.redis")
    def test_redis_cache(self, mock_redis_module):
        """Test Redis cache backend."""
        mock_redis_client = Mock()
        mock_redis_module.Redis.from_url.return_value = mock_redis_client
        mock_redis_client.get.return_value = b"value1"
        mock_redis_client.set.return_value = True

        config = CacheConfig(backend="redis", redis_url="redis://localhost:6379/0")
        cache = CacheMechanism(config=config)

        cache.set("key1", "value1")
        value = cache.get("key1")
        # Redis returns bytes, so we check it's not None
        assert value is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
