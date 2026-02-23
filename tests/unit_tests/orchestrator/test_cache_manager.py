"""
Tests for CacheManager.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.cache_mechanism import CacheConfig
from src.faas.orchestrator.cache_manager import CacheManager, create_cache_manager
from src.faas.orchestrator.cache_strategy import CacheStrategyType


class TestCacheManager:
    """Test CacheManager class."""

    @pytest.fixture
    def mock_cache(self):
        """Create mock cache mechanism."""
        cache = MagicMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        cache.invalidate_pattern = AsyncMock()
        return cache

    @pytest.fixture
    def cache_manager(self, mock_cache):
        """Create CacheManager instance."""
        return CacheManager(cache=mock_cache)

    @pytest.mark.asyncio
    async def test_get_cache_hit(self, cache_manager, mock_cache):
        """Test cache get with hit."""
        cached_value = {"data": "result", "intent": "agent_chat"}
        mock_cache.get = AsyncMock(return_value=cached_value)

        result = await cache_manager.get(
            feature="agent_chat",
            query="Hello",
            tenant_id="tenant_123",
        )
        assert result == cached_value
        mock_cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cache_miss(self, cache_manager, mock_cache):
        """Test cache get with miss."""
        mock_cache.get = AsyncMock(return_value=None)

        result = await cache_manager.get(
            feature="agent_chat",
            query="Hello",
            tenant_id="tenant_123",
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_get_should_not_cache(self, cache_manager, mock_cache):
        """Test cache get when should not cache."""
        result = await cache_manager.get(
            feature="document_ingestion",
            query="Upload document",
            tenant_id="tenant_123",
        )
        assert result is None
        mock_cache.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_set_cache(self, cache_manager, mock_cache):
        """Test cache set."""
        await cache_manager.set(
            feature="agent_chat",
            query="Hello",
            value={"data": "result"},
            tenant_id="tenant_123",
        )
        mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_should_not_cache(self, cache_manager, mock_cache):
        """Test cache set when should not cache."""
        await cache_manager.set(
            feature="document_ingestion",
            query="Upload document",
            value={"data": "result"},
            tenant_id="tenant_123",
        )
        mock_cache.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_set_cache_exception(self, cache_manager, mock_cache):
        """Test cache set with exception."""
        mock_cache.set = AsyncMock(side_effect=Exception("Cache error"))
        # Should not raise, just log warning
        await cache_manager.set(
            feature="agent_chat",
            query="Hello",
            value={"data": "result"},
            tenant_id="tenant_123",
        )

    @pytest.mark.asyncio
    async def test_invalidate_with_pattern(self, cache_manager, mock_cache):
        """Test cache invalidation with pattern."""
        await cache_manager.invalidate(pattern="orchestrator:agent_chat:*", tenant_id="tenant_123")
        mock_cache.invalidate_pattern.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_with_feature(self, cache_manager, mock_cache):
        """Test cache invalidation with feature."""
        await cache_manager.invalidate(feature="agent_chat", tenant_id="tenant_123")
        mock_cache.invalidate_pattern.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_with_tenant_only(self, cache_manager, mock_cache):
        """Test cache invalidation with tenant only."""
        await cache_manager.invalidate(tenant_id="tenant_123")
        mock_cache.invalidate_pattern.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_no_params(self, cache_manager, mock_cache):
        """Test cache invalidation with no parameters."""
        await cache_manager.invalidate()
        # Should log warning, not call invalidate_pattern
        mock_cache.invalidate_pattern.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalidate_exception(self, cache_manager, mock_cache):
        """Test cache invalidation with exception."""
        mock_cache.invalidate_pattern = AsyncMock(side_effect=Exception("Invalidation error"))
        # Should not raise, just log warning
        await cache_manager.invalidate(feature="agent_chat", tenant_id="tenant_123")

    def test_get_strategy_agent_chat(self, cache_manager):
        """Test getting strategy for agent chat."""
        strategy = cache_manager.get_strategy("agent_chat")
        assert strategy.strategy_type == CacheStrategyType.CONVERSATION

    def test_get_strategy_rag_query(self, cache_manager):
        """Test getting strategy for RAG query."""
        strategy = cache_manager.get_strategy("rag_query")
        assert strategy.strategy_type == CacheStrategyType.QUERY

    def test_get_strategy_unknown(self, cache_manager):
        """Test getting strategy for unknown feature."""
        strategy = cache_manager.get_strategy("unknown_feature")
        assert strategy.strategy_type == CacheStrategyType.QUERY  # Default

    def test_create_cache_manager_with_cache(self, mock_cache):
        """Test create_cache_manager with cache instance."""
        manager = create_cache_manager(cache=mock_cache)
        assert isinstance(manager, CacheManager)
        assert manager.cache == mock_cache

    def test_create_cache_manager_with_config(self):
        """Test create_cache_manager with cache config."""
        cache_config = CacheConfig(backend="memory", default_ttl=300)
        manager = create_cache_manager(cache_config=cache_config)
        assert isinstance(manager, CacheManager)
        assert manager.cache is not None

    def test_create_cache_manager_with_strategy(self, mock_cache):
        """Test create_cache_manager with strategy."""
        manager = create_cache_manager(
            cache=mock_cache,
            default_strategy=CacheStrategyType.CONVERSATION,
        )
        assert manager.default_strategy.strategy_type == CacheStrategyType.CONVERSATION

