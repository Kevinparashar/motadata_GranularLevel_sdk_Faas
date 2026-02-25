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

    def test_build_context_aware_key(self):
        """Test context-aware key building."""
        cache = CacheMechanism(config=CacheConfig(namespace="test"))
        
        # Test with all context parameters
        key = cache._build_context_aware_key(
            "base_key",
            tenant_id="tenant1",
            user_id="user1",
            conversation_id="conv1",
            session_id="session1"
        )
        assert "session:session1" in key
        assert "user:user1" in key
        assert "conv:conv1" in key
        assert "base_key" in key
        assert "test:tenant1" in key
        
        # Test with partial context
        key2 = cache._build_context_aware_key("base_key", tenant_id="tenant1", user_id="user1")
        assert "user:user1" in key2
        assert "base_key" in key2

    @pytest.mark.asyncio
    async def test_set_with_context_and_dal(self):
        """Test set operation with context and DAL."""
        mock_dal = AsyncMock()
        mock_dal.save_cache_operation = AsyncMock(return_value="op_id")
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            cache_context_dal=mock_dal
        )
        
        await cache.set(
            "key1",
            "value1",
            tenant_id="tenant1",
            user_id="user1",
            conversation_id="conv1",
            session_id="session1",
            reason="test_reason"
        )
        
        # Verify DAL was called
        assert mock_dal.save_cache_operation.called
        call_args = mock_dal.save_cache_operation.call_args
        assert call_args[1]["cache_key"] == "key1"
        assert call_args[1]["operation"] == "set"
        assert call_args[1]["tenant_id"] == "tenant1"
        assert call_args[1]["reason"] == "test_reason"

    @pytest.mark.asyncio
    async def test_set_with_dal_error(self):
        """Test set operation when DAL raises error."""
        mock_dal = AsyncMock()
        mock_dal.save_cache_operation = AsyncMock(side_effect=Exception("DAL error"))
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            cache_context_dal=mock_dal
        )
        
        # Should not raise error, just log
        await cache.set("key1", "value1", tenant_id="tenant1")
        
        # Verify value was still set
        assert await cache.get("key1", tenant_id="tenant1") == "value1"

    @pytest.mark.asyncio
    async def test_get_with_context_and_dal(self):
        """Test get operation with context and DAL."""
        mock_dal = AsyncMock()
        mock_dal.save_cache_operation = AsyncMock(return_value="op_id")
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            cache_context_dal=mock_dal
        )
        
        await cache.set("key1", "value1", tenant_id="tenant1")
        await cache.get("key1", tenant_id="tenant1", user_id="user1")
        
        # Verify DAL was called for get
        assert mock_dal.save_cache_operation.call_count >= 2  # set + get

    @pytest.mark.asyncio
    async def test_get_expired_entry(self):
        """Test get operation with expired entry."""
        cache = CacheMechanism(config=CacheConfig(backend="memory", namespace="test"))
        
        # Set entry with past expiration
        cache._store["test:key1"] = ("value1", time.time() - 10)
        
        result = await cache.get("key1")
        assert result is None
        # Entry should be removed from store (checked in the get method)
        # Note: The removal happens inside the get method when checking expiration

    @pytest.mark.asyncio
    async def test_get_with_dal_error(self):
        """Test get operation when DAL raises error."""
        mock_dal = AsyncMock()
        mock_dal.save_cache_operation = AsyncMock(side_effect=Exception("DAL error"))
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            cache_context_dal=mock_dal
        )
        
        await cache.set("key1", "value1")
        # Should not raise error, just log
        result = await cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_delete_with_context_and_dal(self):
        """Test delete operation with context and DAL."""
        mock_dal = AsyncMock()
        mock_dal.save_cache_operation = AsyncMock(return_value="op_id")
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            cache_context_dal=mock_dal
        )
        
        await cache.set("key1", "value1", tenant_id="tenant1")
        await cache.delete("key1", tenant_id="tenant1", user_id="user1")
        
        # Verify DAL was called
        assert mock_dal.save_cache_operation.called

    @pytest.mark.asyncio
    async def test_delete_with_dal_error(self):
        """Test delete operation when DAL raises error."""
        mock_dal = AsyncMock()
        mock_dal.save_cache_operation = AsyncMock(side_effect=Exception("DAL error"))
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            cache_context_dal=mock_dal
        )
        
        await cache.set("key1", "value1")
        # Should not raise error, just log
        await cache.delete("key1")
        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    @patch("src.core.cache_mechanism.cache.aioredis")
    async def test_set_dragonfly_with_error(self, mock_aioredis_module):
        """Test set operation with Dragonfly backend error handling."""
        mock_redis_client = AsyncMock()
        mock_aioredis_module.from_url = AsyncMock(return_value=mock_redis_client)
        mock_redis_client.set = AsyncMock(side_effect=Exception("Redis error"))
        
        config = CacheConfig(backend="dragonfly")
        cache = CacheMechanism(config=config)
        
        with pytest.raises(Exception, match="Redis error"):
            await cache.set("key1", "value1")

    @pytest.mark.asyncio
    @patch("src.core.cache_mechanism.cache.aioredis")
    async def test_get_dragonfly_with_error(self, mock_aioredis_module):
        """Test get operation with Dragonfly backend error handling."""
        mock_redis_client = AsyncMock()
        mock_aioredis_module.from_url = AsyncMock(return_value=mock_redis_client)
        mock_redis_client.get = AsyncMock(side_effect=Exception("Redis error"))
        
        config = CacheConfig(backend="dragonfly")
        cache = CacheMechanism(config=config)
        
        with pytest.raises(Exception, match="Redis error"):
            await cache.get("key1")

    @pytest.mark.asyncio
    @patch("src.core.cache_mechanism.cache.aioredis")
    async def test_delete_dragonfly_with_error(self, mock_aioredis_module):
        """Test delete operation with Dragonfly backend error handling."""
        mock_redis_client = AsyncMock()
        mock_aioredis_module.from_url = AsyncMock(return_value=mock_redis_client)
        mock_redis_client.delete = AsyncMock(side_effect=Exception("Redis error"))
        
        config = CacheConfig(backend="dragonfly")
        cache = CacheMechanism(config=config)
        
        with pytest.raises(Exception, match="Redis error"):
            await cache.delete("key1")

    @pytest.mark.asyncio
    @patch("src.core.cache_mechanism.cache.aioredis")
    async def test_invalidate_pattern_dragonfly_with_error(self, mock_aioredis_module):
        """Test invalidate_pattern with Dragonfly backend error handling."""
        mock_redis_client = AsyncMock()
        mock_aioredis_module.from_url = AsyncMock(return_value=mock_redis_client)
        mock_redis_client.scan = AsyncMock(side_effect=Exception("Redis error"))
        
        config = CacheConfig(backend="dragonfly")
        cache = CacheMechanism(config=config)
        
        with pytest.raises(Exception, match="Redis error"):
            await cache.invalidate_pattern("pattern")

    @pytest.mark.asyncio
    async def test_invalidate_pattern_memory_no_otel(self):
        """Test invalidate_pattern with memory backend without OTEL."""
        cache = CacheMechanism(config=CacheConfig(backend="memory"))
        
        await cache.set("user:1", "value1")
        await cache.set("user:2", "value2")
        await cache.set("post:1", "value3")
        
        await cache.invalidate_pattern("user:")
        
        assert await cache.get("user:1") is None
        assert await cache.get("user:2") is None
        assert await cache.get("post:1") == "value3"

    @pytest.mark.asyncio
    @patch("src.core.cache_mechanism.cache.aioredis")
    async def test_invalidate_pattern_dragonfly_no_otel(self, mock_aioredis_module):
        """Test invalidate_pattern with Dragonfly backend without OTEL."""
        mock_redis_client = AsyncMock()
        mock_aioredis_module.from_url = AsyncMock(return_value=mock_redis_client)
        mock_redis_client.scan = AsyncMock(return_value=(b'0', [b'key1', b'key2']))
        mock_redis_client.delete = AsyncMock(return_value=2)
        
        config = CacheConfig(backend="dragonfly")
        cache = CacheMechanism(config=config)
        
        await cache.invalidate_pattern("pattern")
        
        assert mock_redis_client.scan.called
        assert mock_redis_client.delete.called

    @pytest.mark.asyncio
    @patch("src.core.cache_mechanism.cache.aioredis")
    async def test_clear_dragonfly_no_otel(self, mock_aioredis_module):
        """Test clear with Dragonfly backend without OTEL."""
        mock_redis_client = AsyncMock()
        mock_aioredis_module.from_url = AsyncMock(return_value=mock_redis_client)
        mock_redis_client.scan = AsyncMock(return_value=(b'0', []))
        
        config = CacheConfig(backend="dragonfly")
        cache = CacheMechanism(config=config)
        
        await cache.clear()
        
        assert mock_redis_client.scan.called

    @pytest.mark.asyncio
    async def test_invalidate_conversation_with_dal(self):
        """Test invalidate_conversation with DAL."""
        mock_dal = AsyncMock()
        mock_dal.invalidate_conversation_cache = AsyncMock(return_value=["key1", "key2"])
        mock_dal.save_cache_operation = AsyncMock(return_value="op_id")
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            cache_context_dal=mock_dal
        )
        
        await cache.set("key1", "value1", tenant_id="tenant1")
        await cache.set("key2", "value2", tenant_id="tenant1")
        
        deleted_count = await cache.invalidate_conversation("conv1", tenant_id="tenant1")
        
        assert deleted_count == 2
        assert mock_dal.invalidate_conversation_cache.called

    @pytest.mark.asyncio
    async def test_invalidate_conversation_no_dal(self):
        """Test invalidate_conversation without DAL."""
        cache = CacheMechanism(config=CacheConfig(backend="memory"))
        
        deleted_count = await cache.invalidate_conversation("conv1")
        assert deleted_count == 0

    @pytest.mark.asyncio
    async def test_invalidate_conversation_with_error(self):
        """Test invalidate_conversation with error handling."""
        mock_dal = AsyncMock()
        mock_dal.invalidate_conversation_cache = AsyncMock(side_effect=Exception("DAL error"))
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            cache_context_dal=mock_dal
        )
        
        deleted_count = await cache.invalidate_conversation("conv1")
        assert deleted_count == 0

    @pytest.mark.asyncio
    async def test_invalidate_session_with_dal(self):
        """Test invalidate_session with DAL."""
        mock_dal = AsyncMock()
        mock_dal.invalidate_session_cache = AsyncMock(return_value=["key1", "key2"])
        mock_dal.save_cache_operation = AsyncMock(return_value="op_id")
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            cache_context_dal=mock_dal
        )
        
        await cache.set("key1", "value1", tenant_id="tenant1")
        await cache.set("key2", "value2", tenant_id="tenant1")
        
        deleted_count = await cache.invalidate_session("session1", tenant_id="tenant1")
        
        assert deleted_count == 2
        assert mock_dal.invalidate_session_cache.called

    @pytest.mark.asyncio
    async def test_invalidate_session_no_dal(self):
        """Test invalidate_session without DAL."""
        cache = CacheMechanism(config=CacheConfig(backend="memory"))
        
        deleted_count = await cache.invalidate_session("session1")
        assert deleted_count == 0

    @pytest.mark.asyncio
    async def test_invalidate_session_with_error(self):
        """Test invalidate_session with error handling."""
        mock_dal = AsyncMock()
        mock_dal.invalidate_session_cache = AsyncMock(side_effect=Exception("DAL error"))
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            cache_context_dal=mock_dal
        )
        
        deleted_count = await cache.invalidate_session("session1")
        assert deleted_count == 0

    @pytest.mark.asyncio
    async def test_invalidate_by_reason_with_dal(self):
        """Test invalidate_by_reason with DAL."""
        mock_dal = AsyncMock()
        mock_dal.get_cache_keys_by_reason = AsyncMock(return_value=["key1", "key2"])
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            cache_context_dal=mock_dal
        )
        
        await cache.set("key1", "value1", tenant_id="tenant1", reason="query_result")
        await cache.set("key2", "value2", tenant_id="tenant1", reason="query_result")
        
        deleted_count = await cache.invalidate_by_reason("query_result", tenant_id="tenant1")
        
        assert deleted_count == 2
        assert mock_dal.get_cache_keys_by_reason.called

    @pytest.mark.asyncio
    async def test_invalidate_by_reason_no_dal(self):
        """Test invalidate_by_reason without DAL."""
        cache = CacheMechanism(config=CacheConfig(backend="memory"))
        
        deleted_count = await cache.invalidate_by_reason("query_result")
        assert deleted_count == 0

    @pytest.mark.asyncio
    async def test_invalidate_by_reason_with_error(self):
        """Test invalidate_by_reason with error handling."""
        mock_dal = AsyncMock()
        mock_dal.get_cache_keys_by_reason = AsyncMock(side_effect=Exception("DAL error"))
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            cache_context_dal=mock_dal
        )
        
        deleted_count = await cache.invalidate_by_reason("query_result")
        assert deleted_count == 0

    @pytest.mark.asyncio
    async def test_get_cache_stats_with_dal(self):
        """Test get_cache_stats with DAL."""
        mock_dal = AsyncMock()
        mock_dal.get_cache_stats = AsyncMock(return_value={
            "total_operations": 10,
            "cache_hits": 8,
            "cache_misses": 2,
            "hit_rate": 0.8
        })
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            cache_context_dal=mock_dal
        )
        
        stats = await cache.get_cache_stats(tenant_id="tenant1")
        
        assert stats["total_operations"] == 10
        assert stats["hit_rate"] == 0.8
        assert mock_dal.get_cache_stats.called

    @pytest.mark.asyncio
    async def test_get_cache_stats_no_dal(self):
        """Test get_cache_stats without DAL."""
        cache = CacheMechanism(config=CacheConfig(backend="memory"))
        
        stats = await cache.get_cache_stats()
        
        assert stats["total_operations"] == 0
        assert stats["hit_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_set_value_size_calculation(self):
        """Test value size calculation in set operation."""
        mock_dal = AsyncMock()
        mock_dal.save_cache_operation = AsyncMock(return_value="op_id")
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            cache_context_dal=mock_dal
        )
        
        await cache.set("key1", {"test": "value"}, tenant_id="tenant1")
        
        # Verify value_size was calculated
        call_args = mock_dal.save_cache_operation.call_args
        assert call_args[1]["value_size"] is not None

    @pytest.mark.asyncio
    async def test_set_value_size_calculation_error(self):
        """Test value size calculation error handling."""
        mock_dal = AsyncMock()
        mock_dal.save_cache_operation = AsyncMock(return_value="op_id")
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            cache_context_dal=mock_dal
        )
        
        # Set a value that can't be JSON serialized (circular reference)
        class Circular:
            def __init__(self):
                self.ref = self
        
        circular = Circular()
        await cache.set("key1", circular, tenant_id="tenant1")
        
        # Should still work, value_size might be None
        assert await cache.get("key1", tenant_id="tenant1") is not None

    @pytest.mark.asyncio
    async def test_set_with_otel_tracer(self):
        """Test set operation with OTEL tracer."""
        class MockTrace:
            def set_attribute(self, key, value):
                pass
            def record_exception(self, exc):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        
        class MockTracer:
            def start_trace(self, name):
                return MockTrace()
        
        class MockMetrics:
            def record_histogram(self, name, value, attrs):
                pass
            def increment_counter(self, name, amount, attributes):
                pass
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            otel_tracer=MockTracer(),
            otel_metrics=MockMetrics()
        )
        
        await cache.set("key1", "value1", tenant_id="tenant1")
        assert await cache.get("key1", tenant_id="tenant1") == "value1"

    @pytest.mark.asyncio
    async def test_get_with_otel_tracer(self):
        """Test get operation with OTEL tracer."""
        class MockTrace:
            def set_attribute(self, key, value):
                pass
            def record_exception(self, exc):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        
        class MockTracer:
            def start_trace(self, name):
                return MockTrace()
        
        class MockMetrics:
            def record_histogram(self, name, value, attrs):
                pass
            def increment_counter(self, name, amount, attributes):
                pass
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            otel_tracer=MockTracer(),
            otel_metrics=MockMetrics()
        )
        
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_cache_hit_with_otel(self):
        """Test get operation with cache hit and OTEL metrics."""
        hit_counter = {'count': 0}
        miss_counter = {'count': 0}
        
        class MockTrace:
            def set_attribute(self, key, value):
                pass
            def record_exception(self, exc):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        
        class MockTracer:
            def start_trace(self, name):
                return MockTrace()
        
        class MockMetrics:
            def record_histogram(self, name, value, attrs):
                pass
            def increment_counter(self, name, amount, attributes):
                if name == "cache.hits":
                    hit_counter['count'] += 1
                elif name == "cache.misses":
                    miss_counter['count'] += 1
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            otel_tracer=MockTracer(),
            otel_metrics=MockMetrics()
        )
        
        await cache.set("key1", "value1")
        await cache.get("key1")  # Cache hit
        await cache.get("key2")  # Cache miss
        
        assert hit_counter['count'] >= 1
        assert miss_counter['count'] >= 1

    @pytest.mark.asyncio
    async def test_delete_with_otel_tracer(self):
        """Test delete operation with OTEL tracer."""
        class MockTrace:
            def set_attribute(self, key, value):
                pass
            def record_exception(self, exc):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        
        class MockTracer:
            def start_trace(self, name):
                return MockTrace()
        
        class MockMetrics:
            def record_histogram(self, name, value, attrs):
                pass
            def increment_counter(self, name, amount, attributes):
                pass
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            otel_tracer=MockTracer(),
            otel_metrics=MockMetrics()
        )
        
        await cache.set("key1", "value1")
        await cache.delete("key1")
        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_invalidate_pattern_with_otel_tracer(self):
        """Test invalidate_pattern with OTEL tracer."""
        class MockTrace:
            def set_attribute(self, key, value):
                pass
            def record_exception(self, exc):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        
        class MockTracer:
            def start_trace(self, name):
                return MockTrace()
        
        class MockMetrics:
            def record_histogram(self, name, value, attrs):
                pass
            def increment_counter(self, name, amount, attributes):
                pass
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            otel_tracer=MockTracer(),
            otel_metrics=MockMetrics()
        )
        
        await cache.set("user:1", "value1")
        await cache.set("user:2", "value2")
        await cache.invalidate_pattern("user:")
        
        assert await cache.get("user:1") is None
        assert await cache.get("user:2") is None

    @pytest.mark.asyncio
    async def test_clear_with_otel_tracer(self):
        """Test clear with OTEL tracer."""
        class MockTrace:
            def set_attribute(self, key, value):
                pass
            def record_exception(self, exc):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        
        class MockTracer:
            def start_trace(self, name):
                return MockTrace()
        
        class MockMetrics:
            def record_histogram(self, name, value, attrs):
                pass
            def increment_counter(self, name, amount, attributes):
                pass
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            otel_tracer=MockTracer(),
            otel_metrics=MockMetrics()
        )
        
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.clear()
        
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_set_with_otel_error(self):
        """Test set operation with OTEL error handling."""
        class MockTrace:
            def set_attribute(self, key, value):
                pass
            def record_exception(self, exc):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        
        class MockTracer:
            def start_trace(self, name):
                return MockTrace()
        
        class MockMetrics:
            def record_histogram(self, name, value, attrs):
                pass
            def increment_counter(self, name, amount, attributes):
                pass
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            otel_tracer=MockTracer(),
            otel_metrics=MockMetrics()
        )
        
        # This should work normally
        await cache.set("key1", "value1")
        assert await cache.get("key1") == "value1"

    @pytest.mark.asyncio
    @patch("src.core.cache_mechanism.cache.aioredis")
    async def test_invalidate_pattern_dragonfly_cursor_loop(self, mock_aioredis_module):
        """Test invalidate_pattern with Dragonfly cursor loop."""
        mock_redis_client = AsyncMock()
        mock_aioredis_module.from_url = AsyncMock(return_value=mock_redis_client)
        mock_redis_client.scan = AsyncMock(side_effect=[
            (b'1', [b'key1', b'key2']),
            (b'2', [b'key3']),
            (b'0', [b'key4'])
        ])
        mock_redis_client.delete = AsyncMock(return_value=4)
        
        config = CacheConfig(backend="dragonfly", namespace="test")
        cache = CacheMechanism(config=config)
        
        await cache.invalidate_pattern("pattern")
        
        assert mock_redis_client.scan.call_count >= 2
        assert mock_redis_client.delete.called

    @pytest.mark.asyncio
    @patch("src.core.cache_mechanism.cache.aioredis")
    async def test_get_dragonfly_with_otel(self, mock_aioredis_module):
        """Test get operation with Dragonfly backend and OTEL."""
        mock_redis_client = AsyncMock()
        mock_aioredis_module.from_url = AsyncMock(return_value=mock_redis_client)
        mock_redis_client.get = AsyncMock(return_value=b"value1")
        
        class MockTrace:
            def set_attribute(self, key, value):
                pass
            def record_exception(self, exc):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        
        class MockTracer:
            def start_trace(self, name):
                return MockTrace()
        
        class MockMetrics:
            def record_histogram(self, name, value, attrs):
                pass
            def increment_counter(self, name, amount, attributes):
                pass
        
        cache = CacheMechanism(
            config=CacheConfig(backend="dragonfly"),
            otel_tracer=MockTracer(),
            otel_metrics=MockMetrics()
        )
        
        result = await cache.get("key1")
        assert result is not None

    @pytest.mark.asyncio
    @patch("src.core.cache_mechanism.cache.aioredis")
    async def test_get_dragonfly_with_otel_error(self, mock_aioredis_module):
        """Test get operation with Dragonfly backend, OTEL, and error."""
        mock_redis_client = AsyncMock()
        mock_aioredis_module.from_url = AsyncMock(return_value=mock_redis_client)
        mock_redis_client.get = AsyncMock(side_effect=Exception("Redis error"))
        
        class MockTrace:
            def set_attribute(self, key, value):
                pass
            def record_exception(self, exc):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        
        class MockTracer:
            def start_trace(self, name):
                return MockTrace()
        
        class MockMetrics:
            def record_histogram(self, name, value, attrs):
                pass
            def increment_counter(self, name, amount, attributes):
                pass
        
        cache = CacheMechanism(
            config=CacheConfig(backend="dragonfly"),
            otel_tracer=MockTracer(),
            otel_metrics=MockMetrics()
        )
        
        with pytest.raises(Exception, match="Redis error"):
            await cache.get("key1")

    @pytest.mark.asyncio
    @patch("src.core.cache_mechanism.cache.aioredis")
    async def test_delete_dragonfly_with_otel_error(self, mock_aioredis_module):
        """Test delete operation with Dragonfly backend, OTEL, and error."""
        mock_redis_client = AsyncMock()
        mock_aioredis_module.from_url = AsyncMock(return_value=mock_redis_client)
        mock_redis_client.delete = AsyncMock(side_effect=Exception("Redis error"))
        
        class MockTrace:
            def set_attribute(self, key, value):
                pass
            def record_exception(self, exc):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        
        class MockTracer:
            def start_trace(self, name):
                return MockTrace()
        
        class MockMetrics:
            def record_histogram(self, name, value, attrs):
                pass
            def increment_counter(self, name, amount, attributes):
                pass
        
        cache = CacheMechanism(
            config=CacheConfig(backend="dragonfly"),
            otel_tracer=MockTracer(),
            otel_metrics=MockMetrics()
        )
        
        with pytest.raises(Exception, match="Redis error"):
            await cache.delete("key1")

    @pytest.mark.asyncio
    @patch("src.core.cache_mechanism.cache.aioredis")
    async def test_invalidate_pattern_dragonfly_with_otel_error(self, mock_aioredis_module):
        """Test invalidate_pattern with Dragonfly backend, OTEL, and error."""
        mock_redis_client = AsyncMock()
        mock_aioredis_module.from_url = AsyncMock(return_value=mock_redis_client)
        mock_redis_client.scan = AsyncMock(side_effect=Exception("Redis error"))
        
        class MockTrace:
            def set_attribute(self, key, value):
                pass
            def record_exception(self, exc):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        
        class MockTracer:
            def start_trace(self, name):
                return MockTrace()
        
        class MockMetrics:
            def record_histogram(self, name, value, attrs):
                pass
            def increment_counter(self, name, amount, attributes):
                pass
        
        cache = CacheMechanism(
            config=CacheConfig(backend="dragonfly"),
            otel_tracer=MockTracer(),
            otel_metrics=MockMetrics()
        )
        
        with pytest.raises(Exception, match="Redis error"):
            await cache.invalidate_pattern("pattern")

    @pytest.mark.asyncio
    @patch("src.core.cache_mechanism.cache.aioredis")
    async def test_clear_dragonfly_with_otel_error(self, mock_aioredis_module):
        """Test clear with Dragonfly backend, OTEL, and error."""
        mock_redis_client = AsyncMock()
        mock_aioredis_module.from_url = AsyncMock(return_value=mock_redis_client)
        mock_redis_client.scan = AsyncMock(side_effect=Exception("Redis error"))
        
        class MockTrace:
            def set_attribute(self, key, value):
                pass
            def record_exception(self, exc):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        
        class MockTracer:
            def start_trace(self, name):
                return MockTrace()
        
        class MockMetrics:
            def record_histogram(self, name, value, attrs):
                pass
            def increment_counter(self, name, amount, attributes):
                pass
        
        cache = CacheMechanism(
            config=CacheConfig(backend="dragonfly"),
            otel_tracer=MockTracer(),
            otel_metrics=MockMetrics()
        )
        
        with pytest.raises(Exception, match="Redis error"):
            await cache.clear()

    @pytest.mark.asyncio
    @patch("src.core.cache_mechanism.cache.aioredis")
    async def test_set_dragonfly_with_otel_error(self, mock_aioredis_module):
        """Test set operation with Dragonfly backend, OTEL, and error."""
        mock_redis_client = AsyncMock()
        mock_aioredis_module.from_url = AsyncMock(return_value=mock_redis_client)
        mock_redis_client.set = AsyncMock(side_effect=Exception("Redis error"))
        
        class MockTrace:
            def set_attribute(self, key, value):
                pass
            def record_exception(self, exc):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        
        class MockTracer:
            def start_trace(self, name):
                return MockTrace()
        
        class MockMetrics:
            def record_histogram(self, name, value, attrs):
                pass
            def increment_counter(self, name, amount, attributes):
                pass
        
        cache = CacheMechanism(
            config=CacheConfig(backend="dragonfly"),
            otel_tracer=MockTracer(),
            otel_metrics=MockMetrics()
        )
        
        with pytest.raises(Exception, match="Redis error"):
            await cache.set("key1", "value1")

    @pytest.mark.asyncio
    async def test_get_with_otel_cache_hit(self):
        """Test get operation with OTEL and cache hit."""
        class MockTrace:
            def set_attribute(self, key, value):
                pass
            def record_exception(self, exc):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        
        class MockTracer:
            def start_trace(self, name):
                return MockTrace()
        
        class MockMetrics:
            def record_histogram(self, name, value, attrs):
                pass
            def increment_counter(self, name, amount, attributes):
                pass
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            otel_tracer=MockTracer(),
            otel_metrics=MockMetrics()
        )
        
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_with_otel_cache_miss(self):
        """Test get operation with OTEL and cache miss."""
        class MockTrace:
            def set_attribute(self, key, value):
                pass
            def record_exception(self, exc):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        
        class MockTracer:
            def start_trace(self, name):
                return MockTrace()
        
        class MockMetrics:
            def record_histogram(self, name, value, attrs):
                pass
            def increment_counter(self, name, amount, attributes):
                pass
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            otel_tracer=MockTracer(),
            otel_metrics=MockMetrics()
        )
        
        result = await cache.get("nonexistent")
        assert result is None


    @pytest.mark.asyncio
    async def test_invalidate_pattern_with_otel_memory_backend(self):
        """Test invalidate_pattern with OTEL and memory backend."""
        class MockTrace:
            def set_attribute(self, key, value):
                pass
            def record_exception(self, exc):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        
        class MockTracer:
            def start_trace(self, name):
                return MockTrace()
        
        class MockMetrics:
            def record_histogram(self, name, value, attrs):
                pass
            def increment_counter(self, name, amount, attributes):
                pass
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory", namespace="test"),
            otel_tracer=MockTracer(),
            otel_metrics=MockMetrics()
        )
        
        await cache.set("user:1", "value1")
        await cache.set("user:2", "value2")
        await cache.set("post:1", "value3")
        
        await cache.invalidate_pattern("user:")
        
        assert await cache.get("user:1") is None
        assert await cache.get("user:2") is None
        assert await cache.get("post:1") == "value3"

    @pytest.mark.asyncio
    async def test_invalidate_pattern_with_otel_and_tenant_id(self):
        """Test invalidate_pattern with OTEL and tenant_id."""
        class MockTrace:
            def set_attribute(self, key, value):
                pass
            def record_exception(self, exc):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        
        class MockTracer:
            def start_trace(self, name):
                return MockTrace()
        
        class MockMetrics:
            def record_histogram(self, name, value, attrs):
                pass
            def increment_counter(self, name, amount, attributes):
                pass
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            otel_tracer=MockTracer(),
            otel_metrics=MockMetrics()
        )
        
        await cache.set("key1", "value1", tenant_id="tenant1")
        await cache.set("key2", "value2", tenant_id="tenant1")
        
        await cache.invalidate_pattern("key", tenant_id="tenant1")
        
        assert await cache.get("key1", tenant_id="tenant1") is None
        assert await cache.get("key2", tenant_id="tenant1") is None

    @pytest.mark.asyncio
    async def test_clear_with_otel_memory_backend(self):
        """Test clear with OTEL and memory backend."""
        class MockTrace:
            def set_attribute(self, key, value):
                pass
            def record_exception(self, exc):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        
        class MockTracer:
            def start_trace(self, name):
                return MockTrace()
        
        class MockMetrics:
            def record_histogram(self, name, value, attrs):
                pass
            def increment_counter(self, name, amount, attributes):
                pass
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            otel_tracer=MockTracer(),
            otel_metrics=MockMetrics()
        )
        
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.clear()
        
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_clear_with_otel_memory_backend_tenant_id(self):
        """Test clear with OTEL, memory backend, and tenant_id."""
        class MockTrace:
            def set_attribute(self, key, value):
                pass
            def record_exception(self, exc):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        
        class MockTracer:
            def start_trace(self, name):
                return MockTrace()
        
        class MockMetrics:
            def record_histogram(self, name, value, attrs):
                pass
            def increment_counter(self, name, amount, attributes):
                pass
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory", namespace="test"),
            otel_tracer=MockTracer(),
            otel_metrics=MockMetrics()
        )
        
        await cache.set("key1", "value1", tenant_id="tenant1")
        await cache.set("key2", "value2", tenant_id="tenant1")
        await cache.set("key3", "value3", tenant_id="tenant2")
        
        await cache.clear(tenant_id="tenant1")
        
        assert await cache.get("key1", tenant_id="tenant1") is None
        assert await cache.get("key2", tenant_id="tenant1") is None
        assert await cache.get("key3", tenant_id="tenant2") == "value3"

    @pytest.mark.asyncio
    @patch("src.core.cache_mechanism.cache.aioredis")
    async def test_invalidate_pattern_dragonfly_with_otel_keys_found(self, mock_aioredis_module):
        """Test invalidate_pattern with Dragonfly, OTEL, and keys found."""
        mock_redis_client = AsyncMock()
        mock_aioredis_module.from_url = AsyncMock(return_value=mock_redis_client)
        mock_redis_client.scan = AsyncMock(return_value=(b'0', [b'key1', b'key2']))
        mock_redis_client.delete = AsyncMock(return_value=2)
        
        class MockTrace:
            def set_attribute(self, key, value):
                pass
            def record_exception(self, exc):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        
        class MockTracer:
            def start_trace(self, name):
                return MockTrace()
        
        class MockMetrics:
            def record_histogram(self, name, value, attrs):
                pass
            def increment_counter(self, name, amount, attributes):
                pass
        
        cache = CacheMechanism(
            config=CacheConfig(backend="dragonfly", namespace="test"),
            otel_tracer=MockTracer(),
            otel_metrics=MockMetrics()
        )
        
        await cache.invalidate_pattern("pattern")
        
        assert mock_redis_client.scan.called
        assert mock_redis_client.delete.called

    @pytest.mark.asyncio
    async def test_get_with_otel_expired_entry(self):
        """Test get operation with OTEL and expired entry."""
        class MockTrace:
            def set_attribute(self, key, value):
                pass
            def record_exception(self, exc):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        
        class MockTracer:
            def start_trace(self, name):
                return MockTrace()
        
        class MockMetrics:
            def record_histogram(self, name, value, attrs):
                pass
            def increment_counter(self, name, amount, attributes):
                pass
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory", namespace="test"),
            otel_tracer=MockTracer(),
            otel_metrics=MockMetrics()
        )
        
        # Set entry with past expiration
        cache._store["test:key1"] = ("value1", time.time() - 10)
        
        result = await cache.get("key1")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_with_otel_existing_entry(self):
        """Test get operation with OTEL and existing entry."""
        class MockTrace:
            def set_attribute(self, key, value):
                pass
            def record_exception(self, exc):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        
        class MockTracer:
            def start_trace(self, name):
                return MockTrace()
        
        class MockMetrics:
            def record_histogram(self, name, value, attrs):
                pass
            def increment_counter(self, name, amount, attributes):
                pass
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory", namespace="test"),
            otel_tracer=MockTracer(),
            otel_metrics=MockMetrics()
        )
        
        # Set entry with future expiration
        cache._store["test:key1"] = ("value1", time.time() + 100)
        
        result = await cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    @patch("src.core.cache_mechanism.cache.aioredis")
    async def test_invalidate_pattern_dragonfly_with_otel_no_keys(self, mock_aioredis_module):
        """Test invalidate_pattern with Dragonfly, OTEL, and no keys found."""
        mock_redis_client = AsyncMock()
        mock_aioredis_module.from_url = AsyncMock(return_value=mock_redis_client)
        mock_redis_client.scan = AsyncMock(return_value=(b'0', []))
        mock_redis_client.delete = AsyncMock(return_value=0)
        
        class MockTrace:
            def set_attribute(self, key, value):
                pass
            def record_exception(self, exc):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        
        class MockTracer:
            def start_trace(self, name):
                return MockTrace()
        
        class MockMetrics:
            def record_histogram(self, name, value, attrs):
                pass
            def increment_counter(self, name, amount, attributes):
                pass
        
        cache = CacheMechanism(
            config=CacheConfig(backend="dragonfly", namespace="test"),
            otel_tracer=MockTracer(),
            otel_metrics=MockMetrics()
        )
        
        await cache.invalidate_pattern("pattern")
        
        assert mock_redis_client.scan.called

    @pytest.mark.asyncio
    async def test_set_without_otel_and_dal(self):
        """Test set operation without OTEL and with DAL."""
        mock_dal = AsyncMock()
        mock_dal.save_cache_operation = AsyncMock(return_value="op_id")
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            cache_context_dal=mock_dal,
            otel_tracer=None,
            otel_metrics=None
        )
        
        await cache.set("key1", "value1", tenant_id="tenant1", reason="test")
        assert await cache.get("key1", tenant_id="tenant1") == "value1"
        assert mock_dal.save_cache_operation.called

    @pytest.mark.asyncio
    async def test_get_without_otel_and_dal(self):
        """Test get operation without OTEL and with DAL."""
        mock_dal = AsyncMock()
        mock_dal.save_cache_operation = AsyncMock(return_value="op_id")
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            cache_context_dal=mock_dal,
            otel_tracer=None,
            otel_metrics=None
        )
        
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        assert result == "value1"
        assert mock_dal.save_cache_operation.call_count >= 2  # set + get

    @pytest.mark.asyncio
    async def test_delete_without_otel_and_dal(self):
        """Test delete operation without OTEL and with DAL."""
        mock_dal = AsyncMock()
        mock_dal.save_cache_operation = AsyncMock(return_value="op_id")
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            cache_context_dal=mock_dal,
            otel_tracer=None,
            otel_metrics=None
        )
        
        await cache.set("key1", "value1")
        await cache.delete("key1")
        assert await cache.get("key1") is None
        assert mock_dal.save_cache_operation.call_count >= 2  # set + delete

    @pytest.mark.asyncio
    async def test_invalidate_pattern_without_otel(self):
        """Test invalidate_pattern without OTEL."""
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            otel_tracer=None,
            otel_metrics=None
        )
        
        await cache.set("user:1", "value1")
        await cache.set("user:2", "value2")
        await cache.set("post:1", "value3")
        
        await cache.invalidate_pattern("user:")
        
        assert await cache.get("user:1") is None
        assert await cache.get("user:2") is None
        assert await cache.get("post:1") == "value3"

    @pytest.mark.asyncio
    async def test_clear_without_otel(self):
        """Test clear without OTEL."""
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            otel_tracer=None,
            otel_metrics=None
        )
        
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.clear()
        
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_clear_without_otel_with_tenant(self):
        """Test clear without OTEL with tenant_id."""
        cache = CacheMechanism(
            config=CacheConfig(backend="memory", namespace="test"),
            otel_tracer=None,
            otel_metrics=None
        )
        
        await cache.set("key1", "value1", tenant_id="tenant1")
        await cache.set("key2", "value2", tenant_id="tenant1")
        await cache.set("key3", "value3", tenant_id="tenant2")
        
        await cache.clear(tenant_id="tenant1")
        
        assert await cache.get("key1", tenant_id="tenant1") is None
        assert await cache.get("key2", tenant_id="tenant1") is None
        assert await cache.get("key3", tenant_id="tenant2") == "value3"

    @pytest.mark.asyncio
    async def test_invalidate_conversation_delete_error(self):
        """Test invalidate_conversation with delete error."""
        mock_dal = AsyncMock()
        mock_dal.invalidate_conversation_cache = AsyncMock(return_value=["key1", "key2"])
        mock_dal.save_cache_operation = AsyncMock(return_value="op_id")
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            cache_context_dal=mock_dal
        )
        
        # Mock delete to raise error for one key
        original_delete = cache.delete
        call_count = [0]
        async def mock_delete(key, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Delete error")
            return await original_delete(key, **kwargs)
        
        cache.delete = mock_delete
        
        deleted_count = await cache.invalidate_conversation("conv1")
        assert deleted_count == 1  # Only one key deleted successfully

    @pytest.mark.asyncio
    async def test_invalidate_session_delete_error(self):
        """Test invalidate_session with delete error."""
        mock_dal = AsyncMock()
        mock_dal.invalidate_session_cache = AsyncMock(return_value=["key1", "key2"])
        mock_dal.save_cache_operation = AsyncMock(return_value="op_id")
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            cache_context_dal=mock_dal
        )
        
        # Mock delete to raise error for one key
        original_delete = cache.delete
        call_count = [0]
        async def mock_delete(key, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Delete error")
            return await original_delete(key, **kwargs)
        
        cache.delete = mock_delete
        
        deleted_count = await cache.invalidate_session("session1")
        assert deleted_count == 1  # Only one key deleted successfully

    @pytest.mark.asyncio
    async def test_invalidate_by_reason_delete_error(self):
        """Test invalidate_by_reason with delete error."""
        mock_dal = AsyncMock()
        mock_dal.get_cache_keys_by_reason = AsyncMock(return_value=["key1", "key2"])
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            cache_context_dal=mock_dal
        )
        
        # Mock delete to raise error for one key
        original_delete = cache.delete
        call_count = [0]
        async def mock_delete(key, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Delete error")
            return await original_delete(key, **kwargs)
        
        cache.delete = mock_delete
        
        deleted_count = await cache.invalidate_by_reason("query_result")
        assert deleted_count == 1  # Only one key deleted successfully

    @pytest.mark.asyncio
    @patch("src.core.cache_mechanism.cache.aioredis")
    async def test_set_dragonfly_without_otel(self, mock_aioredis_module):
        """Test set operation with Dragonfly backend without OTEL."""
        mock_redis_client = AsyncMock()
        mock_aioredis_module.from_url = AsyncMock(return_value=mock_redis_client)
        mock_redis_client.set = AsyncMock(return_value=True)
        
        cache = CacheMechanism(
            config=CacheConfig(backend="dragonfly"),
            otel_tracer=None,
            otel_metrics=None
        )
        
        await cache.set("key1", "value1")
        assert mock_redis_client.set.called

    @pytest.mark.asyncio
    @patch("src.core.cache_mechanism.cache.aioredis")
    async def test_get_dragonfly_without_otel(self, mock_aioredis_module):
        """Test get operation with Dragonfly backend without OTEL."""
        mock_redis_client = AsyncMock()
        mock_aioredis_module.from_url = AsyncMock(return_value=mock_redis_client)
        mock_redis_client.get = AsyncMock(return_value=b"value1")
        
        cache = CacheMechanism(
            config=CacheConfig(backend="dragonfly"),
            otel_tracer=None,
            otel_metrics=None
        )
        
        result = await cache.get("key1")
        assert result is not None
        assert mock_redis_client.get.called

    @pytest.mark.asyncio
    @patch("src.core.cache_mechanism.cache.aioredis")
    async def test_delete_dragonfly_without_otel(self, mock_aioredis_module):
        """Test delete operation with Dragonfly backend without OTEL."""
        mock_redis_client = AsyncMock()
        mock_aioredis_module.from_url = AsyncMock(return_value=mock_redis_client)
        mock_redis_client.delete = AsyncMock(return_value=1)
        
        cache = CacheMechanism(
            config=CacheConfig(backend="dragonfly"),
            otel_tracer=None,
            otel_metrics=None
        )
        
        await cache.delete("key1")
        assert mock_redis_client.delete.called

    @pytest.mark.asyncio
    @patch("src.core.cache_mechanism.cache.aioredis")
    async def test_invalidate_pattern_dragonfly_without_otel(self, mock_aioredis_module):
        """Test invalidate_pattern with Dragonfly backend without OTEL."""
        mock_redis_client = AsyncMock()
        mock_aioredis_module.from_url = AsyncMock(return_value=mock_redis_client)
        mock_redis_client.scan = AsyncMock(return_value=(b'0', [b'key1', b'key2']))
        mock_redis_client.delete = AsyncMock(return_value=2)
        
        cache = CacheMechanism(
            config=CacheConfig(backend="dragonfly", namespace="test"),
            otel_tracer=None,
            otel_metrics=None
        )
        
        await cache.invalidate_pattern("pattern")
        assert mock_redis_client.scan.called
        assert mock_redis_client.delete.called

    @pytest.mark.asyncio
    @patch("src.core.cache_mechanism.cache.aioredis")
    async def test_clear_dragonfly_without_otel(self, mock_aioredis_module):
        """Test clear with Dragonfly backend without OTEL."""
        mock_redis_client = AsyncMock()
        mock_aioredis_module.from_url = AsyncMock(return_value=mock_redis_client)
        mock_redis_client.scan = AsyncMock(return_value=(b'0', []))
        
        cache = CacheMechanism(
            config=CacheConfig(backend="dragonfly", namespace="test"),
            otel_tracer=None,
            otel_metrics=None
        )
        
        await cache.clear()
        assert mock_redis_client.scan.called

    @pytest.mark.asyncio
    async def test_invalidate_conversation_dal_save_error(self):
        """Test invalidate_conversation with DAL save error."""
        mock_dal = AsyncMock()
        mock_dal.invalidate_conversation_cache = AsyncMock(return_value=["key1"])
        mock_dal.save_cache_operation = AsyncMock(side_effect=Exception("Save error"))
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            cache_context_dal=mock_dal
        )
        
        await cache.set("key1", "value1")
        deleted_count = await cache.invalidate_conversation("conv1")
        assert deleted_count == 1  # Should still delete even if save fails

    @pytest.mark.asyncio
    async def test_invalidate_session_dal_save_error(self):
        """Test invalidate_session with DAL save error."""
        mock_dal = AsyncMock()
        mock_dal.invalidate_session_cache = AsyncMock(return_value=["key1"])
        mock_dal.save_cache_operation = AsyncMock(side_effect=Exception("Save error"))
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            cache_context_dal=mock_dal
        )
        
        await cache.set("key1", "value1")
        deleted_count = await cache.invalidate_session("session1")
        assert deleted_count == 1  # Should still delete even if save fails


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
