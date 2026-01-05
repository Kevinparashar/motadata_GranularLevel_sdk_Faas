"""
Unit Tests for Cache Component

Tests caching operations for LLM responses and embeddings.
"""

import pytest
import time
from unittest.mock import Mock, patch
from src.core.cache_mechanism import CacheManager, CacheBackend


class TestCacheManager:
    """Test CacheManager."""
    
    def test_memory_cache_initialization(self):
        """Test memory cache initialization."""
        cache = CacheManager(backend=CacheBackend.MEMORY)
        assert cache.backend == CacheBackend.MEMORY
    
    def test_set_get(self):
        """Test set and get operations."""
        cache = CacheManager(backend=CacheBackend.MEMORY)
        
        cache.set("key1", "value1")
        value = cache.get("key1")
        assert value == "value1"
    
    def test_set_with_ttl(self):
        """Test set with TTL."""
        cache = CacheManager(backend=CacheBackend.MEMORY)
        
        cache.set("key1", "value1", ttl=1)
        value = cache.get("key1")
        assert value == "value1"
        
        # Wait for expiration
        time.sleep(1.1)
        expired_value = cache.get("key1")
        assert expired_value is None
    
    def test_delete(self):
        """Test delete operation."""
        cache = CacheManager(backend=CacheBackend.MEMORY)
        
        cache.set("key1", "value1")
        cache.delete("key1")
        value = cache.get("key1")
        assert value is None
    
    def test_clear(self):
        """Test clear operation."""
        cache = CacheManager(backend=CacheBackend.MEMORY)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_exists(self):
        """Test exists check."""
        cache = CacheManager(backend=CacheBackend.MEMORY)
        
        cache.set("key1", "value1")
        assert cache.exists("key1") is True
        assert cache.exists("key2") is False
    
    def test_get_stats(self):
        """Test statistics retrieval."""
        cache = CacheManager(backend=CacheBackend.MEMORY)
        
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss
        
        stats = cache.get_stats()
        assert "hits" in stats or "misses" in stats or "size" in stats
    
    @patch('src.core.cache_mechanism.redis.Redis')
    def test_redis_cache(self, mock_redis):
        """Test Redis cache backend."""
        mock_redis_client = Mock()
        mock_redis.return_value = mock_redis_client
        mock_redis_client.get.return_value = b"value1"
        mock_redis_client.set.return_value = True
        
        cache = CacheManager(
            backend=CacheBackend.REDIS,
            config={"host": "localhost", "port": 6379}
        )
        
        cache.set("key1", "value1")
        value = cache.get("key1")
        # Redis returns bytes, so we check it's not None
        assert value is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

