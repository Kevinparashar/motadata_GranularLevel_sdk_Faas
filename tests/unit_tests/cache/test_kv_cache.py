"""
Unit tests for kv_cache.py
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.litellm_gateway.kv_cache import (
    KVCacheEntry,
    KVCacheManager,
    create_kv_cache_manager,
)


class TestKVCacheEntry:
    """Tests for KVCacheEntry class."""

    def test_kv_cache_entry_init_minimal(self):
        """Test KVCacheEntry initialization with minimal parameters."""
        keys = [[0.1, 0.2], [0.3, 0.4]]
        values = [[0.5, 0.6], [0.7, 0.8]]
        entry = KVCacheEntry(cache_key="test-key", keys=keys, values=values)

        assert entry.cache_key == "test-key"
        assert entry.keys == keys
        assert entry.values == values
        assert entry.metadata == {}

    def test_kv_cache_entry_init_all_params(self):
        """Test KVCacheEntry initialization with all parameters."""
        keys = [[0.1, 0.2], [0.3, 0.4]]
        values = [[0.5, 0.6], [0.7, 0.8]]
        metadata = {"model": "gpt-4", "layer": 0}
        entry = KVCacheEntry(
            cache_key="test-key", keys=keys, values=values, metadata=metadata
        )

        assert entry.cache_key == "test-key"
        assert entry.keys == keys
        assert entry.values == values
        assert entry.metadata == metadata

    def test_kv_cache_entry_to_dict(self):
        """Test KVCacheEntry.to_dict()."""
        keys = [[0.1, 0.2], [0.3, 0.4]]
        values = [[0.5, 0.6], [0.7, 0.8]]
        metadata = {"model": "gpt-4"}
        entry = KVCacheEntry(
            cache_key="test-key", keys=keys, values=values, metadata=metadata
        )

        result = entry.to_dict()

        assert result["cache_key"] == "test-key"
        assert result["keys"] == keys
        assert result["values"] == values
        assert result["metadata"] == metadata

    def test_kv_cache_entry_from_dict(self):
        """Test KVCacheEntry.from_dict()."""
        data = {
            "cache_key": "test-key",
            "keys": [[0.1, 0.2], [0.3, 0.4]],
            "values": [[0.5, 0.6], [0.7, 0.8]],
            "metadata": {"model": "gpt-4"},
        }

        entry = KVCacheEntry.from_dict(data)

        assert entry.cache_key == "test-key"
        assert entry.keys == [[0.1, 0.2], [0.3, 0.4]]
        assert entry.values == [[0.5, 0.6], [0.7, 0.8]]
        assert entry.metadata == {"model": "gpt-4"}

    def test_kv_cache_entry_from_dict_no_metadata(self):
        """Test KVCacheEntry.from_dict() without metadata."""
        data = {
            "cache_key": "test-key",
            "keys": [[0.1, 0.2]],
            "values": [[0.5, 0.6]],
        }

        entry = KVCacheEntry.from_dict(data)

        assert entry.cache_key == "test-key"
        assert entry.metadata == {}


class TestKVCacheManager:
    """Tests for KVCacheManager class."""

    def test_init_default(self):
        """Test KVCacheManager initialization with default parameters."""
        manager = KVCacheManager()

        assert manager.cache is None
        assert manager.enable_kv_cache is True
        assert manager.kv_cache_ttl == 3600
        assert manager.max_cache_size_mb == 1000
        assert manager._memory_cache == {}

    def test_init_with_cache(self):
        """Test KVCacheManager initialization with cache."""
        mock_cache = MagicMock()
        manager = KVCacheManager(cache=mock_cache)

        assert manager.cache == mock_cache
        assert manager.enable_kv_cache is True

    def test_init_with_custom_params(self):
        """Test KVCacheManager initialization with custom parameters."""
        manager = KVCacheManager(
            enable_kv_cache=False, kv_cache_ttl=7200, max_cache_size_mb=2000
        )

        assert manager.enable_kv_cache is False
        assert manager.kv_cache_ttl == 7200
        assert manager.max_cache_size_mb == 2000

    def test_generate_cache_key_with_prompt(self):
        """Test generate_cache_key() with prompt."""
        manager = KVCacheManager()
        key = manager.generate_cache_key(prompt="test prompt", model="gpt-4")

        assert key.startswith("kv_cache:gpt-4:")
        assert len(key) > len("kv_cache:gpt-4:")

    def test_generate_cache_key_with_messages(self):
        """Test generate_cache_key() with messages."""
        manager = KVCacheManager()
        messages = [{"role": "user", "content": "Hello"}]
        key = manager.generate_cache_key(
            prompt="", model="gpt-4", messages=messages
        )

        assert key.startswith("kv_cache:gpt-4:")
        assert len(key) > len("kv_cache:gpt-4:")

    def test_generate_cache_key_with_prefix_length(self):
        """Test generate_cache_key() with prefix_length."""
        manager = KVCacheManager()
        key1 = manager.generate_cache_key(
            prompt="very long prompt text", model="gpt-4", prefix_length=5
        )
        key2 = manager.generate_cache_key(
            prompt="very long prompt text", model="gpt-4", prefix_length=10
        )

        # Different prefix lengths should produce different keys
        assert key1 != key2

    def test_generate_cache_key_same_input_same_key(self):
        """Test generate_cache_key() produces same key for same input."""
        manager = KVCacheManager()
        key1 = manager.generate_cache_key(prompt="test", model="gpt-4")
        key2 = manager.generate_cache_key(prompt="test", model="gpt-4")

        assert key1 == key2

    @pytest.mark.asyncio
    async def test_get_kv_cache_disabled(self):
        """Test get_kv_cache() when cache is disabled."""
        manager = KVCacheManager(enable_kv_cache=False)

        result = await manager.get_kv_cache("test-key")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_kv_cache_memory_hit(self):
        """Test get_kv_cache() with memory cache hit."""
        manager = KVCacheManager(enable_kv_cache=True)
        entry = KVCacheEntry(
            cache_key="test-key", keys=[[0.1]], values=[[0.2]]
        )
        manager._memory_cache["test-key"] = entry

        result = await manager.get_kv_cache("test-key")

        assert result is not None
        assert result.cache_key == "test-key"

    @pytest.mark.asyncio
    async def test_get_kv_cache_persistent_hit(self):
        """Test get_kv_cache() with persistent cache hit."""
        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(
            return_value={
                "cache_key": "test-key",
                "keys": [[0.1]],
                "values": [[0.2]],
                "metadata": {},
            }
        )
        manager = KVCacheManager(cache=mock_cache, enable_kv_cache=True)

        result = await manager.get_kv_cache("test-key")

        assert result is not None
        assert result.cache_key == "test-key"
        # Should also be stored in memory cache
        assert "test-key" in manager._memory_cache

    @pytest.mark.asyncio
    async def test_get_kv_cache_persistent_hit_with_tenant(self):
        """Test get_kv_cache() with persistent cache hit and tenant_id."""
        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(
            return_value={
                "cache_key": "test-key",
                "keys": [[0.1]],
                "values": [[0.2]],
                "metadata": {},
            }
        )
        manager = KVCacheManager(cache=mock_cache, enable_kv_cache=True)

        result = await manager.get_kv_cache("test-key", tenant_id="tenant-1")

        assert result is not None
        mock_cache.get.assert_called_once_with("test-key", tenant_id="tenant-1")

    @pytest.mark.asyncio
    async def test_get_kv_cache_persistent_error(self):
        """Test get_kv_cache() handles persistent cache errors gracefully."""
        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(side_effect=Exception("Cache error"))
        manager = KVCacheManager(cache=mock_cache, enable_kv_cache=True)

        result = await manager.get_kv_cache("test-key")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_kv_cache_persistent_not_dict(self):
        """Test get_kv_cache() when persistent cache returns non-dict."""
        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(return_value="not a dict")
        manager = KVCacheManager(cache=mock_cache, enable_kv_cache=True)

        result = await manager.get_kv_cache("test-key")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_kv_cache_miss(self):
        """Test get_kv_cache() with cache miss."""
        manager = KVCacheManager(enable_kv_cache=True)

        result = await manager.get_kv_cache("test-key")

        assert result is None

    @pytest.mark.asyncio
    async def test_set_kv_cache_disabled(self):
        """Test set_kv_cache() when cache is disabled."""
        manager = KVCacheManager(enable_kv_cache=False)
        entry = KVCacheEntry(cache_key="test-key", keys=[[0.1]], values=[[0.2]])

        result = await manager.set_kv_cache(entry)

        assert result is False
        assert "test-key" not in manager._memory_cache

    @pytest.mark.asyncio
    async def test_set_kv_cache_memory_only(self):
        """Test set_kv_cache() with memory cache only."""
        manager = KVCacheManager(enable_kv_cache=True, cache=None)
        entry = KVCacheEntry(cache_key="test-key", keys=[[0.1]], values=[[0.2]])

        result = await manager.set_kv_cache(entry)

        assert result is True
        assert "test-key" in manager._memory_cache
        assert manager._memory_cache["test-key"] == entry

    @pytest.mark.asyncio
    async def test_set_kv_cache_with_persistent(self):
        """Test set_kv_cache() with persistent cache."""
        mock_cache = MagicMock()
        mock_cache.set = AsyncMock(return_value=None)
        manager = KVCacheManager(cache=mock_cache, enable_kv_cache=True)
        entry = KVCacheEntry(cache_key="test-key", keys=[[0.1]], values=[[0.2]])

        result = await manager.set_kv_cache(entry)

        assert result is True
        assert "test-key" in manager._memory_cache
        mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_kv_cache_with_persistent_and_tenant(self):
        """Test set_kv_cache() with persistent cache and tenant_id."""
        mock_cache = MagicMock()
        mock_cache.set = AsyncMock(return_value=None)
        manager = KVCacheManager(cache=mock_cache, enable_kv_cache=True)
        entry = KVCacheEntry(cache_key="test-key", keys=[[0.1]], values=[[0.2]])

        result = await manager.set_kv_cache(entry, tenant_id="tenant-1")

        assert result is True
        # Verify tenant_id was passed
        call_kwargs = mock_cache.set.call_args[1]
        assert call_kwargs.get("tenant_id") == "tenant-1"

    @pytest.mark.asyncio
    async def test_set_kv_cache_persistent_error(self):
        """Test set_kv_cache() handles persistent cache errors gracefully."""
        mock_cache = MagicMock()
        mock_cache.set = AsyncMock(side_effect=Exception("Cache error"))
        manager = KVCacheManager(cache=mock_cache, enable_kv_cache=True)
        entry = KVCacheEntry(cache_key="test-key", keys=[[0.1]], values=[[0.2]])

        result = await manager.set_kv_cache(entry)

        assert result is False
        # Should still be in memory cache
        assert "test-key" in manager._memory_cache

    @pytest.mark.asyncio
    async def test_invalidate_specific_key_memory_only(self):
        """Test _invalidate_specific_key() with memory cache only."""
        manager = KVCacheManager(enable_kv_cache=True, cache=None)
        entry = KVCacheEntry(cache_key="test-key", keys=[[0.1]], values=[[0.2]])
        manager._memory_cache["test-key"] = entry

        result = await manager._invalidate_specific_key("test-key", None)

        assert result == 1
        assert "test-key" not in manager._memory_cache

    @pytest.mark.asyncio
    async def test_invalidate_specific_key_with_persistent(self):
        """Test _invalidate_specific_key() with persistent cache."""
        mock_cache = MagicMock()
        mock_cache.delete = AsyncMock(return_value=None)
        manager = KVCacheManager(cache=mock_cache, enable_kv_cache=True)
        entry = KVCacheEntry(cache_key="test-key", keys=[[0.1]], values=[[0.2]])
        manager._memory_cache["test-key"] = entry

        result = await manager._invalidate_specific_key("test-key", "tenant-1")

        assert result == 2  # Both memory and persistent
        assert "test-key" not in manager._memory_cache
        mock_cache.delete.assert_called_once_with("test-key", tenant_id="tenant-1")

    @pytest.mark.asyncio
    async def test_invalidate_specific_key_persistent_error(self):
        """Test _invalidate_specific_key() handles persistent cache errors."""
        mock_cache = MagicMock()
        mock_cache.delete = AsyncMock(side_effect=Exception("Cache error"))
        manager = KVCacheManager(cache=mock_cache, enable_kv_cache=True)
        entry = KVCacheEntry(cache_key="test-key", keys=[[0.1]], values=[[0.2]])
        manager._memory_cache["test-key"] = entry

        result = await manager._invalidate_specific_key("test-key", None)

        assert result == 1  # Only memory cache cleared
        assert "test-key" not in manager._memory_cache

    def test_get_keys_to_invalidate_no_model(self):
        """Test _get_keys_to_invalidate() without model filter."""
        manager = KVCacheManager()
        manager._memory_cache["kv_cache:gpt-4:hash1"] = KVCacheEntry(
            cache_key="kv_cache:gpt-4:hash1", keys=[[]], values=[[]]
        )
        manager._memory_cache["kv_cache:gpt-3:hash2"] = KVCacheEntry(
            cache_key="kv_cache:gpt-3:hash2", keys=[[]], values=[[]]
        )

        result = manager._get_keys_to_invalidate(None)

        assert len(result) == 2

    def test_get_keys_to_invalidate_with_model(self):
        """Test _get_keys_to_invalidate() with model filter."""
        manager = KVCacheManager()
        manager._memory_cache["kv_cache:gpt-4:hash1"] = KVCacheEntry(
            cache_key="kv_cache:gpt-4:hash1", keys=[[]], values=[[]]
        )
        manager._memory_cache["kv_cache:gpt-3:hash2"] = KVCacheEntry(
            cache_key="kv_cache:gpt-3:hash2", keys=[[]], values=[[]]
        )

        result = manager._get_keys_to_invalidate("gpt-4")

        assert len(result) == 1
        assert result[0] == "kv_cache:gpt-4:hash1"

    def test_invalidate_memory_keys(self):
        """Test _invalidate_memory_keys()."""
        manager = KVCacheManager()
        manager._memory_cache["key1"] = KVCacheEntry(
            cache_key="key1", keys=[[]], values=[[]]
        )
        manager._memory_cache["key2"] = KVCacheEntry(
            cache_key="key2", keys=[[]], values=[[]]
        )

        result = manager._invalidate_memory_keys(["key1", "key2"])

        assert result == 2
        assert len(manager._memory_cache) == 0

    @pytest.mark.asyncio
    async def test_invalidate_kv_cache_specific_key(self):
        """Test invalidate_kv_cache() with specific cache_key."""
        manager = KVCacheManager(enable_kv_cache=True)
        entry = KVCacheEntry(cache_key="test-key", keys=[[0.1]], values=[[0.2]])
        manager._memory_cache["test-key"] = entry

        result = await manager.invalidate_kv_cache(cache_key="test-key")

        assert result == 1
        assert "test-key" not in manager._memory_cache

    @pytest.mark.asyncio
    async def test_invalidate_kv_cache_by_model(self):
        """Test invalidate_kv_cache() by model."""
        manager = KVCacheManager(enable_kv_cache=True)
        manager._memory_cache["kv_cache:gpt-4:hash1"] = KVCacheEntry(
            cache_key="kv_cache:gpt-4:hash1", keys=[[]], values=[[]]
        )
        manager._memory_cache["kv_cache:gpt-3:hash2"] = KVCacheEntry(
            cache_key="kv_cache:gpt-3:hash2", keys=[[]], values=[[]]
        )

        result = await manager.invalidate_kv_cache(model="gpt-4")

        assert result == 1
        assert "kv_cache:gpt-4:hash1" not in manager._memory_cache
        assert "kv_cache:gpt-3:hash2" in manager._memory_cache

    @pytest.mark.asyncio
    async def test_invalidate_kv_cache_all(self):
        """Test invalidate_kv_cache() without filters."""
        manager = KVCacheManager(enable_kv_cache=True)
        manager._memory_cache["key1"] = KVCacheEntry(
            cache_key="key1", keys=[[]], values=[[]]
        )
        manager._memory_cache["key2"] = KVCacheEntry(
            cache_key="key2", keys=[[]], values=[[]]
        )

        result = await manager.invalidate_kv_cache()

        assert result == 2
        assert len(manager._memory_cache) == 0

    @pytest.mark.asyncio
    async def test_invalidate_kv_cache_by_model_with_persistent(self):
        """Test invalidate_kv_cache() by model with persistent cache."""
        mock_cache = MagicMock()
        manager = KVCacheManager(cache=mock_cache, enable_kv_cache=True)
        manager._memory_cache["kv_cache:gpt-4:hash1"] = KVCacheEntry(
            cache_key="kv_cache:gpt-4:hash1", keys=[[]], values=[[]]
        )

        result = await manager.invalidate_kv_cache(model="gpt-4", tenant_id="tenant-1")

        assert result == 1

    def test_get_cache_stats_empty(self):
        """Test get_cache_stats() with empty cache."""
        manager = KVCacheManager()

        stats = manager.get_cache_stats()

        assert stats["enabled"] is True
        assert stats["memory_entries"] == 0
        assert abs(stats["memory_size_mb"] - 0.0) < 0.001
        assert stats["max_cache_size_mb"] == 1000
        assert stats["ttl_seconds"] == 3600
        assert stats["has_persistent_cache"] is False

    def test_get_cache_stats_with_entries(self):
        """Test get_cache_stats() with cache entries."""
        manager = KVCacheManager()
        # Add entries with keys and values
        # Structure: keys/values are lists of layers, each layer is a list of vectors
        # Each vector is a list of floats
        # Use larger data to ensure non-zero MB calculation
        # 10 layers, 100 vectors per layer, 768 floats per vector = 10 * 100 * 768 * 4 bytes = ~3MB
        large_vector = [0.1] * 768
        large_layer = [large_vector] * 100
        large_keys = [large_layer] * 10
        large_values = [large_layer] * 10
        
        entry1 = KVCacheEntry(
            cache_key="key1",
            keys=large_keys,  # type: ignore[arg-type]
            values=large_values,  # type: ignore[arg-type]
        )
        manager._memory_cache["key1"] = entry1

        stats = manager.get_cache_stats()

        assert stats["memory_entries"] == 1
        assert stats["memory_size_mb"] > 0

    def test_get_cache_stats_with_persistent_cache(self):
        """Test get_cache_stats() with persistent cache."""
        mock_cache = MagicMock()
        manager = KVCacheManager(cache=mock_cache)

        stats = manager.get_cache_stats()

        assert stats["has_persistent_cache"] is True

    def test_get_cache_stats_disabled(self):
        """Test get_cache_stats() when cache is disabled."""
        manager = KVCacheManager(enable_kv_cache=False)

        stats = manager.get_cache_stats()

        assert stats["enabled"] is False

    def test_get_cache_stats_with_empty_layers(self):
        """Test get_cache_stats() handles empty layers correctly."""
        manager = KVCacheManager()
        # Entry with empty or invalid layers
        entry1 = KVCacheEntry(
            cache_key="key1", keys=[], values=[]
        )
        entry2 = KVCacheEntry(
            cache_key="key2", keys=[[]], values=[[]]  # Empty inner lists
        )
        manager._memory_cache["key1"] = entry1
        manager._memory_cache["key2"] = entry2

        stats = manager.get_cache_stats()

        assert stats["memory_entries"] == 2
        # Should handle empty layers gracefully
        assert stats["memory_size_mb"] >= 0

    def test_clear_cache(self):
        """Test clear_cache()."""
        manager = KVCacheManager()
        manager._memory_cache["key1"] = KVCacheEntry(
            cache_key="key1", keys=[[]], values=[[]]
        )
        manager._memory_cache["key2"] = KVCacheEntry(
            cache_key="key2", keys=[[]], values=[[]]
        )

        result = manager.clear_cache()

        assert result == 2
        assert len(manager._memory_cache) == 0

    def test_clear_cache_empty(self):
        """Test clear_cache() with empty cache."""
        manager = KVCacheManager()

        result = manager.clear_cache()

        assert result == 0


class TestCreateKVCacheManager:
    """Tests for create_kv_cache_manager factory function."""

    def test_create_kv_cache_manager_default(self):
        """Test create_kv_cache_manager() with default parameters."""
        manager = create_kv_cache_manager()

        assert isinstance(manager, KVCacheManager)
        assert manager.cache is None
        assert manager.enable_kv_cache is True

    def test_create_kv_cache_manager_with_cache(self):
        """Test create_kv_cache_manager() with cache."""
        mock_cache = MagicMock()
        manager = create_kv_cache_manager(cache=mock_cache)

        assert manager.cache == mock_cache

    def test_create_kv_cache_manager_with_kwargs(self):
        """Test create_kv_cache_manager() with additional kwargs."""
        manager = create_kv_cache_manager(
            enable_kv_cache=False, kv_cache_ttl=7200, max_cache_size_mb=2000
        )

        assert manager.enable_kv_cache is False
        assert manager.kv_cache_ttl == 7200
        assert manager.max_cache_size_mb == 2000

