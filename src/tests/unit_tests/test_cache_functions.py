"""
Unit Tests for Cache Mechanism Functions

Tests factory functions, convenience functions, and utilities for cache mechanism.
"""

import pytest

from src.core.cache_mechanism import (  # Core classes; Factory functions; High-level convenience functions; Utility functions
    CacheConfig,
    CacheMechanism,
    batch_cache_get,
    batch_cache_set,
    cache_clear_pattern,
    cache_delete,
    cache_get,
    cache_or_compute,
    cache_set,
    configure_cache,
    create_cache,
    create_memory_cache,
)


class TestFactoryFunctions:
    """Test factory functions for cache creation."""

    def test_create_cache_memory(self):
        """Test create_cache with memory backend."""
        cache = create_cache(
            backend="memory", default_ttl=600, max_size=2048, namespace="test_cache"
        )

        assert isinstance(cache, CacheMechanism)
        assert cache.config.backend == "memory"
        assert cache.config.default_ttl == 600
        assert cache.config.max_size == 2048
        assert cache.config.namespace == "test_cache"

    def test_create_cache_defaults(self):
        """Test create_cache with default parameters."""
        cache = create_cache()

        assert isinstance(cache, CacheMechanism)
        assert cache.config.backend == "memory"
        assert cache.config.default_ttl == 300
        assert cache.config.max_size == 1024

    def test_create_memory_cache(self):
        """Test create_memory_cache factory function."""
        cache = create_memory_cache(default_ttl=600, max_size=2048, namespace="memory_cache")

        assert isinstance(cache, CacheMechanism)
        assert cache.config.backend == "memory"
        assert cache.config.default_ttl == 600
        assert cache.config.max_size == 2048
        assert cache.config.namespace == "memory_cache"

    def test_create_memory_cache_defaults(self):
        """Test create_memory_cache with default parameters."""
        cache = create_memory_cache()

        assert isinstance(cache, CacheMechanism)
        assert cache.config.backend == "memory"
        assert cache.config.default_ttl == 300
        assert cache.config.max_size == 1024

    def test_configure_cache(self):
        """Test configure_cache factory function."""
        config = configure_cache(backend="memory", default_ttl=600, max_size=2048, namespace="test")

        assert isinstance(config, CacheConfig)
        assert config.backend == "memory"
        assert config.default_ttl == 600
        assert config.max_size == 2048
        assert config.namespace == "test"


class TestConvenienceFunctions:
    """Test high-level convenience functions."""

    @pytest.fixture
    def cache(self):
        """Create a memory cache for testing."""
        return create_memory_cache(default_ttl=300)

    def test_cache_get(self, cache):
        """Test cache_get convenience function."""
        cache.set("test_key", "test_value")

        value = cache_get(cache, "test_key")

        assert value == "test_value"

    def test_cache_get_not_found(self, cache):
        """Test cache_get with non-existent key."""
        value = cache_get(cache, "non_existent")

        assert value is None

    def test_cache_set(self, cache):
        """Test cache_set convenience function."""
        cache_set(cache, "key1", "value1", ttl=600)

        value = cache.get("key1")
        assert value == "value1"

    def test_cache_set_default_ttl(self, cache):
        """Test cache_set with default TTL."""
        cache_set(cache, "key1", "value1")

        value = cache.get("key1")
        assert value == "value1"

    def test_cache_delete(self, cache):
        """Test cache_delete convenience function."""
        cache.set("key1", "value1")
        cache_delete(cache, "key1")

        value = cache.get("key1")
        assert value is None

    def test_cache_delete_nonexistent(self, cache):
        """Test cache_delete with non-existent key."""
        # Should not raise exception
        cache_delete(cache, "non_existent")

    def test_cache_clear_pattern(self, cache):
        """Test cache_clear_pattern convenience function."""
        cache.set("user:1", "value1")
        cache.set("user:2", "value2")
        cache.set("post:1", "value3")

        cache_clear_pattern(cache, "user:")

        assert cache.get("user:1") is None
        assert cache.get("user:2") is None
        assert cache.get("post:1") == "value3"  # Should remain


class TestUtilityFunctions:
    """Test utility functions."""

    @pytest.fixture
    def cache(self):
        """Create a memory cache for testing."""
        return create_memory_cache(default_ttl=300)

    def test_cache_or_compute_cache_hit(self, cache):
        """Test cache_or_compute with cache hit."""
        cache.set("key1", "cached_value")

        def compute_func():
            return "computed_value"

        value = cache_or_compute(cache, "key1", compute_func, ttl=600)

        assert value == "cached_value"

    def test_cache_or_compute_cache_miss(self, cache):
        """Test cache_or_compute with cache miss."""

        def compute_func():
            return "computed_value"

        value = cache_or_compute(cache, "key1", compute_func, ttl=600)

        assert value == "computed_value"
        # Verify value was cached
        assert cache.get("key1") == "computed_value"

    def test_cache_or_compute_with_ttl(self, cache):
        """Test cache_or_compute with custom TTL."""

        def compute_func():
            return "computed_value"

        cache_or_compute(cache, "key1", compute_func, ttl=60)

        # Value should be cached
        assert cache.get("key1") == "computed_value"

    def test_batch_cache_set(self, cache):
        """Test batch_cache_set utility function."""
        items = {"key1": "value1", "key2": "value2", "key3": "value3"}

        batch_cache_set(cache, items, ttl=600)

        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

    def test_batch_cache_set_empty(self, cache):
        """Test batch_cache_set with empty dictionary."""
        batch_cache_set(cache, {}, ttl=600)

        # Should not raise exception - verify no items were cached
        # This is a no-op operation with empty dictionary

    def test_batch_cache_get(self, cache):
        """Test batch_cache_get utility function."""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        keys = ["key1", "key2", "key4"]  # key4 doesn't exist
        results = batch_cache_get(cache, keys)

        assert results["key1"] == "value1"
        assert results["key2"] == "value2"
        assert results["key4"] is None

    def test_batch_cache_get_empty(self, cache):
        """Test batch_cache_get with empty key list."""
        results = batch_cache_get(cache, [])

        assert results == {}

    def test_batch_cache_get_all_missing(self, cache):
        """Test batch_cache_get with all missing keys."""
        results = batch_cache_get(cache, ["key1", "key2", "key3"])

        assert results["key1"] is None
        assert results["key2"] is None
        assert results["key3"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
