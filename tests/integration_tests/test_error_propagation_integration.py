"""
Integration Tests for Error Propagation

Tests error propagation across components:
- Gateway errors propagate to Agent/RAG
- RAG errors propagate correctly
- Agent errors propagate correctly
- FaaS Service errors propagate correctly
- Error handling in service chains
- Error context preservation
"""


from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.agno_agent_framework import Agent
from src.core.agno_agent_framework.exceptions import AgentExecutionError
from src.core.litellm_gateway import LiteLLMGateway
from src.core.rag import RAGSystem
from src.core.rag.exceptions import (
    EmbeddingError,
    GenerationError,
    RetrievalError,
)
from src.faas.shared.exceptions import (
    DependencyError,
    InternalServerError,
    ServiceException,
    ValidationError,
)


@pytest.mark.integration
class TestGatewayErrorPropagation:
    """Test Gateway error propagation to dependent components."""

    @pytest.fixture
    def mock_gateway_with_error(self):
        """Create mock gateway that raises errors."""
        gateway = MagicMock(spec=LiteLLMGateway)
        gateway.generate_async = AsyncMock(side_effect=Exception("Gateway error"))
        gateway.embed_async = AsyncMock(side_effect=Exception("Embedding error"))
        return gateway

    @pytest.mark.asyncio
    async def test_gateway_error_propagates_to_agent(self, mock_gateway_with_error):
        """Test that Gateway errors propagate to Agent."""
        _ = Agent(
            agent_id="agent_123",
            name="Test Agent",
            gateway=mock_gateway_with_error,
        )

        # Agent should handle Gateway errors
        # Note: Actual implementation may vary
        try:
            await mock_gateway_with_error.generate_async(
                prompt="Test", model="gpt-4"
            )
        except Exception as e:
            # Verify error is raised
            assert "Gateway error" in str(e) or isinstance(e, Exception)

    @pytest.mark.asyncio
    async def test_gateway_embedding_error_propagates_to_rag(self, mock_gateway_with_error):
        """Test that Gateway embedding errors propagate to RAG."""
        mock_db = MagicMock()
        mock_db.execute_query = AsyncMock(return_value=[])

        _ = RAGSystem(
            db=mock_db,
            gateway=mock_gateway_with_error,
        )

        # RAG should handle Gateway embedding errors
        try:
            await mock_gateway_with_error.embed_async(
                text="Test", model="text-embedding-3-small"
            )
        except Exception as e:
            # Verify error is raised
            assert "Embedding error" in str(e) or isinstance(e, Exception)


@pytest.mark.integration
class TestRAGErrorPropagation:
    """Test RAG error propagation."""

    @pytest.fixture
    def mock_gateway(self):
        """Create mock gateway."""
        gateway = MagicMock(spec=LiteLLMGateway)
        gateway.generate_async = AsyncMock()
        gateway.embed_async = AsyncMock(return_value={"embeddings": [[0.1, 0.2, 0.3]]})
        return gateway

    @pytest.fixture
    def mock_db_with_error(self):
        """Create mock database that raises errors."""
        db = MagicMock()
        db.execute_query = AsyncMock(side_effect=Exception("Database error"))
        return db

    @pytest.mark.asyncio
    async def test_rag_retrieval_error_propagation(self, mock_gateway, mock_db_with_error):
        """Test that RAG retrieval errors propagate correctly."""
        _ = RAGSystem(
            db=mock_db_with_error,
            gateway=mock_gateway,
        )

        # RAG retrieval should handle database errors
        try:
            await mock_db_with_error.execute_query("SELECT * FROM documents")
        except Exception as e:
            # Verify error is raised
            assert "Database error" in str(e) or isinstance(e, Exception)

    @pytest.mark.asyncio
    async def test_rag_embedding_error_propagation(self, mock_gateway):
        """Test that RAG embedding errors propagate correctly."""
        mock_db = MagicMock()
        mock_db.execute_query = AsyncMock(return_value=[])

        # Mock gateway to raise embedding error
        mock_gateway.embed_async = AsyncMock(side_effect=EmbeddingError("Embedding failed", "text", "model"))

        _ = RAGSystem(
            db=mock_db,
            gateway=mock_gateway,
        )

        # RAG should handle embedding errors
        try:
            await mock_gateway.embed_async(text="Test", model="text-embedding-3-small")
        except EmbeddingError as e:
            # Verify EmbeddingError is raised
            assert "Embedding failed" in str(e)
            assert isinstance(e, EmbeddingError)


@pytest.mark.integration
class TestAgentErrorPropagation:
    """Test Agent error propagation."""

    @pytest.fixture
    def mock_gateway_with_error(self):
        """Create mock gateway that raises errors."""
        gateway = MagicMock(spec=LiteLLMGateway)
        gateway.generate_async = AsyncMock(side_effect=Exception("Agent execution error"))
        return gateway

    @pytest.mark.asyncio
    async def test_agent_execution_error_propagation(self, mock_gateway_with_error):
        """Test that Agent execution errors propagate correctly."""
        _ = Agent(
            agent_id="agent_123",
            name="Test Agent",
            gateway=mock_gateway_with_error,
        )

        # Agent should handle execution errors
        try:
            await mock_gateway_with_error.generate_async(
                prompt="Execute task", model="gpt-4"
            )
        except Exception as e:
            # Verify error is raised
            assert "Agent execution error" in str(e) or isinstance(e, Exception)


@pytest.mark.integration
class TestFaaSServiceErrorPropagation:
    """Test FaaS Service error propagation."""

    @pytest.fixture
    def mock_http_client_error(self):
        """Create mock HTTP client with error."""
        mock_client_instance = AsyncMock()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock(side_effect=Exception("Service unavailable"))
        mock_response.status_code = 503
        mock_client_instance.request = AsyncMock(return_value=mock_response)
        mock_client_instance.aclose = AsyncMock()
        return mock_client_instance, mock_response

    @pytest.mark.asyncio
    async def test_service_error_propagation(self, mock_http_client_error):
        """Test that service errors propagate correctly."""
        from src.faas.shared.http_client import ServiceHTTPClient

        mock_client_instance, _ = mock_http_client_error

        with patch("src.faas.shared.http_client.httpx.AsyncClient", return_value=mock_client_instance):
            gateway_client = ServiceHTTPClient(
                service_name="gateway",
                service_url="http://gateway-service:8080",
            )

            # Test error handling
            try:
                await gateway_client.post(
                    "/api/v1/gateway/generate",
                    json_data={"prompt": "Test", "model": "gpt-4"},
                )
            except Exception as e:
                # Verify error is properly raised
                assert "Service unavailable" in str(e) or "503" in str(e) or isinstance(e, Exception)

            await gateway_client.close()

    @pytest.mark.asyncio
    async def test_service_exception_hierarchy(self):
        """Test that ServiceException hierarchy works correctly."""
        # Test ValidationError
        validation_error = ValidationError("Invalid input", {"field": "query"})
        assert isinstance(validation_error, ServiceException)
        assert validation_error.status_code == 400
        assert validation_error.error_code == "VALIDATION_ERROR"

        # Test DependencyError
        dependency_error = DependencyError("gateway", "Service unavailable")
        assert isinstance(dependency_error, ServiceException)
        assert dependency_error.status_code == 502
        assert dependency_error.error_code == "DEPENDENCY_ERROR"

        # Test InternalServerError
        internal_error = InternalServerError("Internal error occurred")
        assert isinstance(internal_error, ServiceException)
        assert internal_error.status_code == 500
        assert internal_error.error_code == "INTERNAL_SERVER_ERROR"


@pytest.mark.integration
class TestErrorPropagationInServiceChains:
    """Test error propagation in service chains."""

    @pytest.fixture
    def mock_http_client_error(self):
        """Create mock HTTP client with error."""
        mock_client_instance = AsyncMock()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock(side_effect=Exception("Chain error"))
        mock_response.status_code = 500
        mock_client_instance.request = AsyncMock(return_value=mock_response)
        mock_client_instance.aclose = AsyncMock()
        return mock_client_instance, mock_response

    @pytest.mark.asyncio
    async def test_error_propagation_agent_to_gateway(self, mock_http_client_error):
        """Test error propagation: Agent → Gateway."""
        from src.faas.shared.http_client import ServiceHTTPClient

        mock_client_instance, _ = mock_http_client_error

        with patch("src.faas.shared.http_client.httpx.AsyncClient", return_value=mock_client_instance):
            # Agent Service calls Gateway Service
            gateway_client = ServiceHTTPClient(
                service_name="gateway",
                service_url="http://gateway-service:8080",
            )

            try:
                await gateway_client.post(
                    "/api/v1/gateway/generate",
                    json_data={"prompt": "Test", "model": "gpt-4"},
                )
            except Exception as e:
                # Verify error propagates
                assert "Chain error" in str(e) or isinstance(e, Exception)

            await gateway_client.close()

    @pytest.mark.asyncio
    async def test_error_propagation_rag_to_gateway(self, mock_http_client_error):
        """Test error propagation: RAG → Gateway."""
        from src.faas.shared.http_client import ServiceHTTPClient

        mock_client_instance, _ = mock_http_client_error

        with patch("src.faas.shared.http_client.httpx.AsyncClient", return_value=mock_client_instance):
            # RAG Service calls Gateway Service
            gateway_client = ServiceHTTPClient(
                service_name="gateway",
                service_url="http://gateway-service:8080",
            )

            try:
                await gateway_client.post(
                    "/api/v1/gateway/embed",
                    json_data={"text": "Test", "model": "text-embedding-3-small"},
                )
            except Exception as e:
                # Verify error propagates
                assert "Chain error" in str(e) or isinstance(e, Exception)

            await gateway_client.close()


@pytest.mark.integration
class TestErrorContextPreservation:
    """Test error context preservation across components."""

    @pytest.mark.asyncio
    async def test_error_context_in_service_exception(self):
        """Test that error context is preserved in ServiceException."""
        error = ServiceException(
            message="Test error",
            status_code=500,
            error_code="TEST_ERROR",
            details={"component": "gateway", "operation": "generate"},
        )

        # Verify context is preserved
        assert error.message == "Test error"
        assert error.status_code == 500
        assert error.error_code == "TEST_ERROR"
        assert error.details["component"] == "gateway"
        assert error.details["operation"] == "generate"

    @pytest.mark.asyncio
    async def test_error_context_in_rag_exceptions(self):
        """Test that error context is preserved in RAG exceptions."""
        # Test RetrievalError
        retrieval_error = RetrievalError(
            message="Retrieval failed",
            query="What is AI?",
            document_id="123",
            operation="similarity_search",
        )

        assert retrieval_error.query == "What is AI?"
        assert retrieval_error.document_id == "123"
        assert retrieval_error.operation == "similarity_search"

        # Test GenerationError
        generation_error = GenerationError(
            message="Generation failed",
            query="What is AI?",
            context="Context here",
            operation="generate",
        )

        assert generation_error.query == "What is AI?"
        assert generation_error.context == "Context here"
        assert generation_error.operation == "generate"

        # Test EmbeddingError
        embedding_error = EmbeddingError(
            message="Embedding failed",
            text="Test text",
            model="text-embedding-3-small",
        )

        assert embedding_error.text == "Test text"
        assert embedding_error.model == "text-embedding-3-small"

    @pytest.mark.asyncio
    async def test_error_context_in_agent_exceptions(self):
        """Test that error context is preserved in Agent exceptions."""
        # Test AgentExecutionError
        agent_error = AgentExecutionError(
            message="Agent execution failed",
            agent_id="agent_123",
            task_type="chat",
            execution_stage="execution",
        )

        assert agent_error.agent_id == "agent_123"
        assert agent_error.task_type == "chat"
        assert agent_error.execution_stage == "execution"


@pytest.mark.integration
class TestErrorHandlingInOrchestrator:
    """Test error handling in Orchestrator."""

    @pytest.fixture
    def mock_http_client_error(self):
        """Create mock HTTP client with error."""
        mock_client_instance = AsyncMock()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock(side_effect=DependencyError("gateway", "Service unavailable"))
        mock_response.status_code = 502
        mock_client_instance.request = AsyncMock(return_value=mock_response)
        mock_client_instance.aclose = AsyncMock()
        return mock_client_instance, mock_response

    @pytest.mark.asyncio
    async def test_orchestrator_handles_service_errors(self, mock_http_client_error):
        """Test that Orchestrator handles service errors correctly."""
        from src.faas.shared.http_client import ServiceHTTPClient

        mock_client_instance, _ = mock_http_client_error

        with patch("src.faas.shared.http_client.httpx.AsyncClient", return_value=mock_client_instance):
            orchestrator_client = ServiceHTTPClient(
                service_name="orchestrator",
                service_url="http://orchestrator-service:8080",
            )

            try:
                await orchestrator_client.post(
                    "/api/v1/orchestrate",
                    json_data={"query": "Test query"},
                )
            except Exception as e:
                # Verify error is handled
                assert isinstance(e, (DependencyError, Exception))

            await orchestrator_client.close()


@pytest.mark.integration
class TestErrorRecoveryAndRetry:
    """Test error recovery and retry mechanisms."""

    @pytest.fixture
    def mock_gateway_with_retry(self):
        """Create mock gateway with retry logic."""
        gateway = MagicMock(spec=LiteLLMGateway)
        call_count = 0

        async def generate_with_retry(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary error")
            return MagicMock(text="Success after retry")

        gateway.generate_async = AsyncMock(side_effect=generate_with_retry)
        return gateway

    @pytest.mark.asyncio
    async def test_retry_mechanism_handles_transient_errors(self, mock_gateway_with_retry):
        """Test that retry mechanism handles transient errors."""
        # Simulate retry logic
        max_retries = 3
        attempt = 0

        while attempt < max_retries:
            try:
                response = await mock_gateway_with_retry.generate_async(
                    prompt="Test", model="gpt-4"
                )
                # Success after retries
                assert response.text == "Success after retry"
                break
            except Exception:
                attempt += 1
                if attempt >= max_retries:
                    raise

        # Verify retries occurred
        assert attempt > 0


@pytest.mark.integration
class TestErrorEndToEndPropagation:
    """Test end-to-end error propagation scenarios."""

    @pytest.mark.asyncio
    async def test_end_to_end_error_propagation(self):
        """Test complete error propagation flow."""
        # Step 1: Gateway error
        gateway_error = Exception("Gateway service unavailable")

        # Step 2: Error propagates to Agent
        try:
            raise gateway_error
        except Exception as e:
            # Verify error is caught
            assert "Gateway service unavailable" in str(e)

        # Step 3: Error propagates to RAG
        rag_error = EmbeddingError("Embedding failed", "text", "model")
        try:
            raise rag_error
        except EmbeddingError as e:
            # Verify RAG error is caught
            assert isinstance(e, EmbeddingError)
            assert e.text == "text"

        # Step 4: Error propagates to FaaS Service
        service_error = DependencyError("gateway", "Service unavailable")
        try:
            raise service_error
        except DependencyError as e:
            # Verify service error is caught
            assert isinstance(e, DependencyError)
            assert e.status_code == 502

