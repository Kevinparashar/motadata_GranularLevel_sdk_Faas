"""
Tests for ServiceSelector.
"""

from unittest.mock import MagicMock

import pytest

from src.faas.orchestrator.query_router import QueryIntent
from src.faas.orchestrator.service_selector import ServiceSelector, create_service_selector


class TestServiceSelector:
    """Test ServiceSelector class."""

    @pytest.fixture
    def mock_config(self):
        """Create mock config."""
        return MagicMock()

    @pytest.fixture
    def selector(self, mock_config):
        """Create ServiceSelector instance."""
        return ServiceSelector(config=mock_config)

    def test_select_service_agent_chat(self, selector):
        """Test service selection for agent chat."""
        context = {"agent_id": "agent_123"}
        result = selector.select_service(
            intent=QueryIntent.AGENT_CHAT.value,
            query="Hello",
            context=context,
            tenant_id="tenant_123",
        )
        assert result["service"] == "agent"
        assert "/api/v1/agents/agent_123/chat" in result["endpoint"]
        assert result["method"] == "POST"
        assert "message" in result["payload"]

    def test_select_service_agent_chat_no_agent_id(self, selector):
        """Test service selection for agent chat without agent_id falls back to gateway."""
        result = selector.select_service(
            intent=QueryIntent.AGENT_CHAT.value,
            query="Hello",
            context=None,
            tenant_id="tenant_123",
        )
        assert result["service"] == "gateway"
        assert result["endpoint"] == "/api/v1/gateway/generate"

    def test_select_service_agent_task(self, selector):
        """Test service selection for agent task."""
        context = {"agent_id": "agent_123", "task_type": "process", "parameters": {"data": "test"}}
        result = selector.select_service(
            intent=QueryIntent.AGENT_TASK.value,
            query="Execute task",
            context=context,
            tenant_id="tenant_123",
        )
        assert result["service"] == "agent"
        assert "/api/v1/agents/agent_123/execute" in result["endpoint"]
        assert result["payload"]["task_type"] == "process"

    def test_select_service_rag_query(self, selector):
        """Test service selection for RAG query."""
        context = {"top_k": 10, "threshold": 0.8}
        result = selector.select_service(
            intent=QueryIntent.RAG_QUERY.value,
            query="Search documents",
            context=context,
            tenant_id="tenant_123",
        )
        assert result["service"] == "rag"
        assert result["endpoint"] == "/api/v1/rag/query"
        assert result["payload"]["query"] == "Search documents"
        assert result["payload"]["top_k"] == 10
        assert result["payload"]["threshold"] == 0.8

    def test_select_service_direct_llm(self, selector):
        """Test service selection for direct LLM."""
        context = {"model": "gpt-3.5-turbo", "max_tokens": 500}
        result = selector.select_service(
            intent=QueryIntent.DIRECT_LLM.value,
            query="Generate text",
            context=context,
            tenant_id="tenant_123",
        )
        assert result["service"] == "gateway"
        assert result["endpoint"] == "/api/v1/gateway/generate"
        assert result["payload"]["prompt"] == "Generate text"
        assert result["payload"]["model"] == "gpt-3.5-turbo"
        assert result["payload"]["max_tokens"] == 500

    def test_select_service_document_ingestion(self, selector):
        """Test service selection for document ingestion."""
        context = {"title": "Test Doc", "metadata": {"source": "upload"}}
        result = selector.select_service(
            intent=QueryIntent.DOCUMENT_INGESTION.value,
            query="Document content here",
            context=context,
            tenant_id="tenant_123",
        )
        assert result["service"] == "rag"
        assert result["endpoint"] == "/api/v1/rag/documents"
        assert result["payload"]["title"] == "Test Doc"

    def test_select_service_prompt_generation(self, selector):
        """Test service selection for prompt generation."""
        context = {"agent_id": "agent_123", "llm_model": "gpt-4"}
        result = selector.select_service(
            intent=QueryIntent.PROMPT_GENERATION.value,
            query="Create agent for support",
            context=context,
            tenant_id="tenant_123",
        )
        assert result["service"] == "prompt_generator"
        assert result["endpoint"] == "/api/v1/prompt/agents"
        assert result["payload"]["prompt"] == "Create agent for support"

    def test_select_service_ml_prediction(self, selector):
        """Test service selection for ML prediction."""
        context = {"model_id": "model_123", "input_data": {"feature": "value"}}
        result = selector.select_service(
            intent=QueryIntent.ML_PREDICTION.value,
            query="Predict",
            context=context,
            tenant_id="tenant_123",
        )
        assert result["service"] == "ml"
        assert "/api/v1/ml/models/model_123/predict" in result["endpoint"]
        assert result["payload"]["input_data"]["feature"] == "value"

    def test_select_service_unknown(self, selector):
        """Test service selection for unknown intent."""
        result = selector.select_service(
            intent=QueryIntent.UNKNOWN.value,
            query="Random query",
            context=None,
            tenant_id="tenant_123",
        )
        assert result["service"] == "gateway"
        assert result["endpoint"] == "/api/v1/gateway/generate"

    def test_extract_agent_id_from_context(self, selector):
        """Test agent ID extraction from context."""
        context = {"agent_id": "agent_123"}
        agent_id = selector._extract_agent_id(context, "query")
        assert agent_id == "agent_123"

    def test_extract_agent_id_from_query(self, selector):
        """Test agent ID extraction from query."""
        agent_id = selector._extract_agent_id(None, "use agent_123 to help")
        assert agent_id == "123"

    def test_extract_agent_id_not_found(self, selector):
        """Test agent ID extraction when not found."""
        agent_id = selector._extract_agent_id(None, "regular query")
        assert agent_id is None

    def test_extract_model_id_from_context(self, selector):
        """Test model ID extraction from context."""
        context = {"model_id": "model_123"}
        model_id = selector._extract_model_id(context, "query")
        assert model_id == "model_123"

    def test_extract_model_id_not_found(self, selector):
        """Test model ID extraction when not found."""
        model_id = selector._extract_model_id(None, "query")
        assert model_id is None

    def test_build_payload_agent_chat(self, selector):
        """Test payload building for agent chat."""
        context = {"session_id": "session_123", "stream": True}
        payload = selector._build_payload(QueryIntent.AGENT_CHAT.value, "Hello", context)
        assert payload["message"] == "Hello"
        assert payload["session_id"] == "session_123"
        assert payload["stream"] is True

    def test_build_payload_agent_task(self, selector):
        """Test payload building for agent task."""
        context = {"task_type": "process", "parameters": {"data": "test"}, "priority": 1}
        payload = selector._build_payload(QueryIntent.AGENT_TASK.value, "Execute", context)
        assert payload["task_type"] == "process"
        assert payload["parameters"]["data"] == "test"
        assert payload["priority"] == 1

    def test_build_payload_rag_query(self, selector):
        """Test payload building for RAG query."""
        context = {"top_k": 10, "threshold": 0.8, "metadata_filters": {"category": "tech"}}
        payload = selector._build_payload(QueryIntent.RAG_QUERY.value, "Search", context)
        assert payload["query"] == "Search"
        assert payload["top_k"] == 10
        assert payload["threshold"] == 0.8
        assert payload["metadata_filters"]["category"] == "tech"

    def test_build_payload_direct_llm(self, selector):
        """Test payload building for direct LLM."""
        context = {"model": "gpt-3.5-turbo", "max_tokens": 500, "temperature": 0.8}
        payload = selector._build_payload(QueryIntent.DIRECT_LLM.value, "Generate", context)
        assert payload["prompt"] == "Generate"
        assert payload["model"] == "gpt-3.5-turbo"
        assert payload["max_tokens"] == 500
        assert payload["temperature"] == 0.8

    def test_build_payload_defaults(self, selector):
        """Test payload building with defaults."""
        payload = selector._build_payload(QueryIntent.DIRECT_LLM.value, "Generate", None)
        assert payload["prompt"] == "Generate"
        assert payload["model"] == "gpt-4"
        assert payload["max_tokens"] == 1000

    def test_get_fallback_config(self, selector):
        """Test fallback configuration."""
        config = selector._get_fallback_config("gateway", "query")
        assert config["service"] == "gateway"
        assert config["endpoint"] == "/api/v1/gateway/generate"
        assert config["payload"]["prompt"] == "query"

    def test_create_service_selector(self, mock_config):
        """Test create_service_selector factory function."""
        selector = create_service_selector(config=mock_config)
        assert isinstance(selector, ServiceSelector)
        assert selector.config == mock_config

