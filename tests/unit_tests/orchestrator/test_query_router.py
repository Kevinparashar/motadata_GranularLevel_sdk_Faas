"""
Tests for QueryRouter.
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.faas.orchestrator.query_router import QueryIntent, QueryRouter, create_query_router


class TestQueryRouter:
    """Test QueryRouter class."""

    @pytest.fixture
    def mock_gateway(self):
        """Create mock gateway."""
        gateway = MagicMock()
        gateway.generate_async = AsyncMock()
        return gateway

    @pytest.fixture
    def mock_cache(self):
        """Create mock cache."""
        cache = MagicMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        return cache

    @pytest.fixture
    def router(self, mock_gateway, mock_cache):
        """Create QueryRouter instance."""
        return QueryRouter(
            gateway=mock_gateway,
            enable_llm_classification=True,
            cache=mock_cache,
        )

    @pytest.mark.asyncio
    async def test_analyze_intent_empty_query(self, router):
        """Test intent analysis with empty query."""
        result = await router.analyze_intent("")
        assert result["intent"] == QueryIntent.UNKNOWN.value
        assert result["confidence"] == 0.0

    @pytest.mark.asyncio
    async def test_analyze_intent_cached(self, router, mock_cache):
        """Test intent analysis with cached result."""
        cached_result = {
            "intent": QueryIntent.AGENT_CHAT.value,
            "confidence": 0.95,
            "reasoning": "Cached",
        }
        mock_cache.get = AsyncMock(return_value=cached_result)

        result = await router.analyze_intent("Hello, how are you?", tenant_id="tenant_123")
        assert result == cached_result
        mock_cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_intent_llm_classification_success(self, router, mock_gateway, mock_cache):
        """Test LLM-based intent classification success."""
        llm_response = MagicMock()
        llm_response.text = json.dumps({
            "intent": "agent_chat",
            "confidence": 0.95,
            "reasoning": "Conversational query",
        })
        mock_gateway.generate_async = AsyncMock(return_value=llm_response)
        mock_cache.get = AsyncMock(return_value=None)

        result = await router.analyze_intent("Hello, how are you?", tenant_id="tenant_123")
        assert result["intent"] == QueryIntent.AGENT_CHAT.value
        assert result["confidence"] == 0.95
        mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_intent_llm_classification_invalid_intent(self, router, mock_gateway, mock_cache):
        """Test LLM classification with invalid intent falls back to pattern matching."""
        llm_response = MagicMock()
        llm_response.text = json.dumps({
            "intent": "invalid_intent",
            "confidence": 0.95,
            "reasoning": "Invalid",
        })
        mock_gateway.generate_async = AsyncMock(return_value=llm_response)
        mock_cache.get = AsyncMock(return_value=None)

        result = await router.analyze_intent("create agent for me")
        # Should fall back to pattern matching
        assert result["intent"] in [QueryIntent.PROMPT_GENERATION.value, QueryIntent.UNKNOWN.value]

    @pytest.mark.asyncio
    async def test_analyze_intent_llm_classification_json_error(self, router, mock_gateway, mock_cache):
        """Test LLM classification with JSON parse error falls back to pattern matching."""
        llm_response = MagicMock()
        llm_response.text = "Invalid JSON response"
        mock_gateway.generate_async = AsyncMock(return_value=llm_response)
        mock_cache.get = AsyncMock(return_value=None)

        result = await router.analyze_intent("create agent for me")
        # Should fall back to pattern matching
        assert result["intent"] == QueryIntent.PROMPT_GENERATION.value

    @pytest.mark.asyncio
    async def test_analyze_intent_llm_classification_exception(self, router, mock_gateway, mock_cache):
        """Test LLM classification with exception falls back to pattern matching."""
        mock_gateway.generate_async = AsyncMock(side_effect=Exception("LLM error"))
        mock_cache.get = AsyncMock(return_value=None)

        result = await router.analyze_intent("create agent for me")
        # Should fall back to pattern matching
        assert result["intent"] == QueryIntent.PROMPT_GENERATION.value

    @pytest.mark.asyncio
    async def test_analyze_intent_pattern_matching_agent_creation(self, router):
        """Test pattern matching for agent creation."""
        router.enable_llm_classification = False
        result = await router.analyze_intent("create agent for customer support")
        assert result["intent"] == QueryIntent.PROMPT_GENERATION.value
        assert result["confidence"] == 0.8

    @pytest.mark.asyncio
    async def test_analyze_intent_pattern_matching_tool_creation(self, router):
        """Test pattern matching for tool creation."""
        router.enable_llm_classification = False
        result = await router.analyze_intent("generate tool to calculate priority")
        assert result["intent"] == QueryIntent.PROMPT_GENERATION.value
        assert result["confidence"] == 0.8

    @pytest.mark.asyncio
    async def test_analyze_intent_pattern_matching_document_ingestion(self, router):
        """Test pattern matching for document ingestion."""
        router.enable_llm_classification = False
        result = await router.analyze_intent("upload document to knowledge base")
        assert result["intent"] == QueryIntent.DOCUMENT_INGESTION.value
        assert result["confidence"] == 0.8

    @pytest.mark.asyncio
    async def test_analyze_intent_pattern_matching_rag_query(self, router):
        """Test pattern matching for RAG query."""
        router.enable_llm_classification = False
        result = await router.analyze_intent("search in documents for AI information")
        assert result["intent"] == QueryIntent.RAG_QUERY.value
        assert result["confidence"] == 0.75

    @pytest.mark.asyncio
    async def test_analyze_intent_pattern_matching_agent_task(self, router):
        """Test pattern matching for agent task."""
        router.enable_llm_classification = False
        result = await router.analyze_intent("execute task to process data")
        assert result["intent"] == QueryIntent.AGENT_TASK.value
        assert result["confidence"] == 0.7

    @pytest.mark.asyncio
    async def test_analyze_intent_pattern_matching_agent_chat(self, router):
        """Test pattern matching for agent chat."""
        router.enable_llm_classification = False
        result = await router.analyze_intent("chat with assistant about help")
        assert result["intent"] == QueryIntent.AGENT_CHAT.value
        assert result["confidence"] == 0.7

    @pytest.mark.asyncio
    async def test_analyze_intent_pattern_matching_short_query(self, router):
        """Test pattern matching for short query (direct LLM)."""
        router.enable_llm_classification = False
        result = await router.analyze_intent("summarize this")
        assert result["intent"] == QueryIntent.DIRECT_LLM.value
        assert result["confidence"] == 0.6

    @pytest.mark.asyncio
    async def test_analyze_intent_pattern_matching_unknown(self, router):
        """Test pattern matching for unknown intent."""
        router.enable_llm_classification = False
        result = await router.analyze_intent("random text without keywords")
        assert result["intent"] == QueryIntent.UNKNOWN.value
        assert result["confidence"] == 0.5

    @pytest.mark.asyncio
    async def test_analyze_intent_with_context(self, router, mock_gateway, mock_cache):
        """Test intent analysis with context."""
        llm_response = MagicMock()
        llm_response.text = json.dumps({
            "intent": "agent_chat",
            "confidence": 0.95,
            "reasoning": "With context",
        })
        mock_gateway.generate_async = AsyncMock(return_value=llm_response)
        mock_cache.get = AsyncMock(return_value=None)

        context = {"session_id": "session_123", "agent_id": "agent_456"}
        result = await router.analyze_intent("Hello", tenant_id="tenant_123", context=context)
        assert result["intent"] == QueryIntent.AGENT_CHAT.value

    def test_hash_query(self, router):
        """Test query hashing."""
        hash1 = router._hash_query("test query")
        hash2 = router._hash_query("test query")
        hash3 = router._hash_query("different query")

        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 64  # SHA-256 hex length

    def test_create_query_router(self, mock_gateway):
        """Test create_query_router factory function."""
        router = create_query_router(gateway=mock_gateway, enable_llm_classification=True)
        assert isinstance(router, QueryRouter)
        assert router.gateway == mock_gateway
        assert router.enable_llm_classification is True

