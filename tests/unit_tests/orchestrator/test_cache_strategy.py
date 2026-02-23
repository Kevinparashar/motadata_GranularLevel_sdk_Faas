"""
Tests for CacheStrategy.
"""

import pytest

from src.faas.orchestrator.cache_strategy import (
    CacheStrategy,
    CacheStrategyType,
    get_cache_strategy,
)


class TestCacheStrategy:
    """Test CacheStrategy class."""

    @pytest.fixture
    def strategy(self):
        """Create CacheStrategy instance."""
        return CacheStrategy(strategy_type=CacheStrategyType.QUERY)

    def test_generate_cache_key_query_strategy(self, strategy):
        """Test cache key generation with query strategy."""
        key = strategy.generate_cache_key(
            feature="agent_chat",
            query="Hello, how are you?",
            tenant_id="tenant_123",
        )
        assert key.startswith("orchestrator:agent_chat")
        assert "tenant:tenant_123" in key
        assert "query:" in key

    def test_generate_cache_key_conversation_strategy(self):
        """Test cache key generation with conversation strategy."""
        strategy = CacheStrategy(strategy_type=CacheStrategyType.CONVERSATION)
        context = {"session_id": "session_123", "agent_id": "agent_456"}
        key = strategy.generate_cache_key(
            feature="agent_chat",
            query="Hello",
            tenant_id="tenant_123",
            context=context,
        )
        assert key.startswith("orchestrator:agent_chat")
        assert "tenant:tenant_123" in key
        assert "session:session_123" in key
        assert "query:" in key

    def test_generate_cache_key_none_strategy(self):
        """Test cache key generation with none strategy."""
        strategy = CacheStrategy(strategy_type=CacheStrategyType.NONE)
        key = strategy.generate_cache_key(
            feature="agent_chat",
            query="Hello",
            tenant_id="tenant_123",
        )
        assert key == ""

    def test_generate_cache_key_with_context(self, strategy):
        """Test cache key generation with context."""
        context = {"agent_id": "agent_123", "model": "gpt-4", "top_k": 5}
        key = strategy.generate_cache_key(
            feature="rag_query",
            query="Search documents",
            tenant_id="tenant_123",
            context=context,
        )
        assert "ctx:" in key

    def test_generate_cache_key_normalizes_query(self, strategy):
        """Test that cache key generation normalizes query."""
        key1 = strategy.generate_cache_key(
            feature="agent_chat",
            query="Hello, how are you?",
            tenant_id="tenant_123",
        )
        key2 = strategy.generate_cache_key(
            feature="agent_chat",
            query="  hello, how are you?  ",
            tenant_id="tenant_123",
        )
        assert key1 == key2

    def test_get_ttl_agent_chat(self, strategy):
        """Test TTL for agent chat."""
        ttl = strategy.get_ttl("agent_chat")
        assert ttl == 300

    def test_get_ttl_agent_task(self, strategy):
        """Test TTL for agent task."""
        ttl = strategy.get_ttl("agent_task")
        assert ttl == 600

    def test_get_ttl_rag_query(self, strategy):
        """Test TTL for RAG query."""
        ttl = strategy.get_ttl("rag_query")
        assert ttl == 3600

    def test_get_ttl_document_ingestion(self, strategy):
        """Test TTL for document ingestion."""
        ttl = strategy.get_ttl("document_ingestion")
        assert ttl == 0

    def test_get_ttl_default(self, strategy):
        """Test default TTL."""
        ttl = strategy.get_ttl("unknown_feature")
        assert ttl == 300

    def test_should_cache_agent_chat(self, strategy):
        """Test should_cache for agent chat."""
        assert strategy.should_cache("agent_chat") is True

    def test_should_cache_document_ingestion(self, strategy):
        """Test should_cache for document ingestion."""
        assert strategy.should_cache("document_ingestion") is False

    def test_should_cache_with_cache_disabled(self, strategy):
        """Test should_cache when cache is disabled in context."""
        context = {"cache_enabled": False}
        assert strategy.should_cache("agent_chat", context) is False

    def test_should_cache_with_cache_enabled(self, strategy):
        """Test should_cache when cache is enabled in context."""
        context = {"cache_enabled": True}
        assert strategy.should_cache("agent_chat", context) is True

    def test_get_cache_strategy(self):
        """Test get_cache_strategy factory function."""
        strategy = get_cache_strategy(CacheStrategyType.CONVERSATION)
        assert isinstance(strategy, CacheStrategy)
        assert strategy.strategy_type == CacheStrategyType.CONVERSATION

