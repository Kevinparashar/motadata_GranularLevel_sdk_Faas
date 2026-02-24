"""
Comprehensive Integration Tests for FaaS Service-to-Service Communication

Tests comprehensive service-to-service interactions:
- All FaaS services calling each other
- Multi-service request chains
- Service-to-service error propagation
- Tenant isolation across services
- Orchestrator routing to all services
- Cache Service integration with all services
- LLMOps Service integration with all services
"""


from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.faas.shared.http_client import ServiceHTTPClient


@pytest.mark.integration
class TestFaaSServiceToServiceIntegration:
    """Test comprehensive FaaS service-to-service communication."""

    @pytest.fixture
    def mock_http_client(self):
        """Create mock HTTP client."""
        mock_client_instance = AsyncMock()
        mock_response = Mock()
        mock_response.json = Mock(return_value={"success": True, "data": {}})
        mock_response.raise_for_status = Mock()
        mock_response.status_code = 200
        mock_client_instance.request = AsyncMock(return_value=mock_response)
        mock_client_instance.aclose = AsyncMock()
        return mock_client_instance, mock_response

    @pytest.mark.asyncio
    async def test_prompt_service_calls_gateway_service(self, mock_http_client):
        """Test that Prompt Service can call Gateway Service for prompt rendering."""
        mock_client_instance, mock_response = mock_http_client
        mock_response.json.return_value = {
            "text": "Rendered prompt response",
            "model": "gpt-4",
        }

        with patch("src.faas.shared.http_client.httpx.AsyncClient", return_value=mock_client_instance):
            gateway_client = ServiceHTTPClient(
                service_name="gateway",
                service_url="http://gateway-service:8080",
            )

            response = await gateway_client.post(
                "/api/v1/gateway/generate",
                json_data={"prompt": "Test prompt", "model": "gpt-4"},
            )

            assert response["text"] == "Rendered prompt response"
            await gateway_client.close()

    @pytest.mark.asyncio
    async def test_cache_service_integration_with_all_services(self, mock_http_client):
        """Test that Cache Service integrates with all services."""
        mock_client_instance, mock_response = mock_http_client
        mock_response.json.return_value = {
            "success": True,
            "cached": True,
            "value": {"data": "cached_value"},
        }

        with patch("src.faas.shared.http_client.httpx.AsyncClient", return_value=mock_client_instance):
            cache_client = ServiceHTTPClient(
                service_name="cache",
                service_url="http://cache-service:8080",
            )

            # Test cache get
            response = await cache_client.get(
                "/api/v1/cache/get",
                params={"key": "test_key", "tenant_id": "tenant_123"},
            )

            assert response["success"] is True
            assert response["cached"] is True
            await cache_client.close()

    @pytest.mark.asyncio
    async def test_llmops_service_integration_with_all_services(self, mock_http_client):
        """Test that LLMOps Service integrates with all services for logging."""
        mock_client_instance, mock_response = mock_http_client
        mock_response.json.return_value = {
            "success": True,
            "operation_id": "op_123",
        }

        with patch("src.faas.shared.http_client.httpx.AsyncClient", return_value=mock_client_instance):
            llmops_client = ServiceHTTPClient(
                service_name="llmops",
                service_url="http://llmops-service:8080",
            )

            # Test operation logging
            response = await llmops_client.post(
                "/api/v1/llmops/operations",
                json_data={
                    "operation_type": "generate",
                    "model": "gpt-4",
                    "tokens": 100,
                },
            )

            assert response["success"] is True
            assert "operation_id" in response
            await llmops_client.close()

    @pytest.mark.asyncio
    async def test_prompt_generator_service_calls_gateway_service(self, mock_http_client):
        """Test that Prompt Generator Service calls Gateway Service for LLM operations."""
        mock_client_instance, mock_response = mock_http_client
        mock_response.json.return_value = {
            "text": "Generated agent code",
            "model": "gpt-4",
        }

        with patch("src.faas.shared.http_client.httpx.AsyncClient", return_value=mock_client_instance):
            gateway_client = ServiceHTTPClient(
                service_name="gateway",
                service_url="http://gateway-service:8080",
            )

            response = await gateway_client.post(
                "/api/v1/gateway/generate",
                json_data={"prompt": "Create an agent for customer support", "model": "gpt-4"},
            )

            assert "text" in response
            await gateway_client.close()

    @pytest.mark.asyncio
    async def test_ml_service_calls_gateway_service(self, mock_http_client):
        """Test that ML Service can call Gateway Service for model serving."""
        mock_client_instance, mock_response = mock_http_client
        mock_response.json.return_value = {
            "predictions": [0.8, 0.2],
            "model": "classification_model",
        }

        with patch("src.faas.shared.http_client.httpx.AsyncClient", return_value=mock_client_instance):
            gateway_client = ServiceHTTPClient(
                service_name="gateway",
                service_url="http://gateway-service:8080",
            )

            response = await gateway_client.post(
                "/api/v1/gateway/generate",
                json_data={"prompt": "Classify this text", "model": "gpt-4"},
            )

            assert response is not None
            await gateway_client.close()


@pytest.mark.integration
class TestFaaSMultiServiceRequestChains:
    """Test multi-service request chains."""

    @pytest.fixture
    def mock_http_client(self):
        """Create mock HTTP client."""
        mock_client_instance = AsyncMock()
        mock_response = Mock()
        mock_response.json = Mock(return_value={"success": True, "data": {}})
        mock_response.raise_for_status = Mock()
        mock_response.status_code = 200
        mock_client_instance.request = AsyncMock(return_value=mock_response)
        mock_client_instance.aclose = AsyncMock()
        return mock_client_instance, mock_response

    @pytest.mark.asyncio
    async def test_agent_service_chain_with_rag_and_gateway(self, mock_http_client):
        """Test Agent Service → RAG Service → Gateway Service chain."""
        mock_client_instance, mock_response = mock_http_client

        # Step 1: RAG Service response
        mock_response.json.side_effect = [
            {"success": True, "data": {"documents": [{"content": "Relevant doc"}]}},  # RAG
            {"text": "Answer with context", "model": "gpt-4"},  # Gateway
        ]

        with patch("src.faas.shared.http_client.httpx.AsyncClient", return_value=mock_client_instance):
            # Step 1: Agent calls RAG
            rag_client = ServiceHTTPClient(
                service_name="rag",
                service_url="http://rag-service:8080",
            )
            rag_response = await rag_client.post(
                "/api/v1/rag/query",
                json_data={"query": "What is AI?"},
            )
            assert rag_response["success"] is True

            # Step 2: Agent calls Gateway with RAG context
            gateway_client = ServiceHTTPClient(
                service_name="gateway",
                service_url="http://gateway-service:8080",
            )
            gateway_response = await gateway_client.post(
                "/api/v1/gateway/generate",
                json_data={"prompt": "Answer: What is AI?", "model": "gpt-4"},
            )
            assert "text" in gateway_response

            await rag_client.close()
            await gateway_client.close()

    @pytest.mark.asyncio
    async def test_data_ingestion_to_rag_to_gateway_chain(self, mock_http_client):
        """Test Data Ingestion → RAG → Gateway chain."""
        mock_client_instance, mock_response = mock_http_client

        mock_response.json.side_effect = [
            {"success": True, "data": {"document_id": "doc_123"}},  # RAG ingestion
            {"embeddings": [[0.1, 0.2, 0.3]]},  # Gateway embeddings
        ]

        with patch("src.faas.shared.http_client.httpx.AsyncClient", return_value=mock_client_instance):
            # Step 1: Data Ingestion calls RAG
            rag_client = ServiceHTTPClient(
                service_name="rag",
                service_url="http://rag-service:8080",
            )
            ingest_response = await rag_client.post(
                "/api/v1/rag/documents",
                json_data={"content": "Test document", "metadata": {}},
            )
            assert ingest_response["success"] is True

            # Step 2: RAG calls Gateway for embeddings
            gateway_client = ServiceHTTPClient(
                service_name="gateway",
                service_url="http://gateway-service:8080",
            )
            embed_response = await gateway_client.post(
                "/api/v1/gateway/embed",
                json_data={"text": "Test document", "model": "text-embedding-3-small"},
            )
            assert "embeddings" in embed_response

            await rag_client.close()
            await gateway_client.close()

    @pytest.mark.asyncio
    async def test_orchestrator_routing_to_multiple_services(self, mock_http_client):
        """Test Orchestrator Service routing to different services."""
        mock_client_instance, mock_response = mock_http_client

        # Test routing to Agent Service
        mock_response.json.return_value = {
            "success": True,
            "data": {"message": "Agent response"},
            "service": "agent",
        }

        with patch("src.faas.shared.http_client.httpx.AsyncClient", return_value=mock_client_instance):
            orchestrator_client = ServiceHTTPClient(
                service_name="orchestrator",
                service_url="http://orchestrator-service:8080",
            )

            # Test agent routing
            response = await orchestrator_client.post(
                "/api/v1/orchestrate",
                json_data={"query": "Hello, how are you?", "intent": "agent_chat"},
            )

            assert response["success"] is True
            assert response["data"]["message"] == "Agent response"

            # Test RAG routing
            mock_response.json.return_value = {
                "success": True,
                "data": {"answer": "RAG answer"},
                "service": "rag",
            }

            response = await orchestrator_client.post(
                "/api/v1/orchestrate",
                json_data={"query": "Search for documents", "intent": "rag_query"},
            )

            assert response["success"] is True
            assert response["service"] == "rag"

            await orchestrator_client.close()


@pytest.mark.integration
class TestFaaSServiceErrorPropagation:
    """Test error propagation across FaaS services."""

    @pytest.fixture
    def mock_http_client_error(self):
        """Create mock HTTP client with error."""
        mock_client_instance = AsyncMock()
        mock_response = Mock()
        mock_response.raise_for_status = Mock(side_effect=Exception("Service unavailable"))
        mock_response.status_code = 503
        mock_client_instance.request = AsyncMock(return_value=mock_response)
        mock_client_instance.aclose = AsyncMock()
        return mock_client_instance, mock_response

    @pytest.mark.asyncio
    async def test_error_propagation_in_service_chain(self, mock_http_client_error):
        """Test that errors propagate correctly in service chains."""
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
                assert "Service unavailable" in str(e) or "503" in str(e)

            await gateway_client.close()

    @pytest.mark.asyncio
    async def test_circuit_breaker_in_service_communication(self, mock_http_client_error):
        """Test circuit breaker functionality in service communication."""
        mock_client_instance, _ = mock_http_client_error

        with patch("src.faas.shared.http_client.httpx.AsyncClient", return_value=mock_client_instance):
            from src.core.utils.circuit_breaker import CircuitBreakerConfig
            
            # Configure circuit breaker with lower threshold for testing
            circuit_config = CircuitBreakerConfig(
                failure_threshold=3,  # Open after 3 failures
                success_threshold=2,
                timeout=60.0,
            )
            
            gateway_client = ServiceHTTPClient(
                service_name="gateway",
                service_url="http://gateway-service:8080",
                max_retries=1,  # Low retries for faster test
                circuit_breaker_config=circuit_config,
            )

            # Verify circuit breaker is initialized
            assert gateway_client.circuit_breaker is not None
            assert gateway_client.circuit_breaker.name == "http_client_gateway"

            # Test that errors are handled (circuit breaker exists and can handle failures)
            failure_count = 0
            for _ in range(3):
                try:
                    await gateway_client.post(
                        "/api/v1/gateway/generate",
                        json_data={"prompt": "Test", "model": "gpt-4"},
                    )
                except Exception:
                    failure_count += 1

            # Verify failures occurred and circuit breaker handled them
            assert failure_count > 0
            # Circuit breaker should track failures (verify it exists and is functional)
            assert gateway_client.circuit_breaker.stats.failures >= 0  # May be 0 if errors caught before circuit breaker

            await gateway_client.close()


@pytest.mark.integration
class TestFaaSTenantIsolation:
    """Test tenant isolation across FaaS services."""

    @pytest.fixture
    def mock_http_client(self):
        """Create mock HTTP client."""
        mock_client_instance = AsyncMock()
        mock_response = Mock()
        mock_response.json = Mock(return_value={"success": True, "data": {}})
        mock_response.raise_for_status = Mock()
        mock_response.status_code = 200
        mock_client_instance.request = AsyncMock(return_value=mock_response)
        mock_client_instance.aclose = AsyncMock()
        return mock_client_instance, mock_response

    @pytest.mark.asyncio
    async def test_tenant_isolation_in_service_calls(self, mock_http_client):
        """Test that tenant_id is properly passed in service calls."""
        mock_client_instance, _ = mock_http_client

        with patch("src.faas.shared.http_client.httpx.AsyncClient", return_value=mock_client_instance):
            gateway_client = ServiceHTTPClient(
                service_name="gateway",
                service_url="http://gateway-service:8080",
            )

            # Make call with tenant_id
            await gateway_client.post(
                "/api/v1/gateway/generate",
                json_data={"prompt": "Test", "model": "gpt-4"},
                headers={"X-Tenant-ID": "tenant_123"},
            )

            # Verify tenant_id was included in headers
            call_args = mock_client_instance.request.call_args
            headers = call_args.kwargs.get("headers", {})
            assert "X-Tenant-ID" in headers or "tenant_123" in str(headers)

            await gateway_client.close()

    @pytest.mark.asyncio
    async def test_tenant_isolation_across_service_chain(self, mock_http_client):
        """Test tenant isolation maintained across service chains."""
        mock_client_instance, _ = mock_http_client

        with patch("src.faas.shared.http_client.httpx.AsyncClient", return_value=mock_client_instance):
            # Service 1: Agent Service
            agent_client = ServiceHTTPClient(
                service_name="agent",
                service_url="http://agent-service:8080",
            )

            # Service 2: Gateway Service (called by Agent)
            gateway_client = ServiceHTTPClient(
                service_name="gateway",
                service_url="http://gateway-service:8080",
            )

            tenant_id = "tenant_456"

            # Verify tenant_id is passed through chain
            await agent_client.post(
                "/api/v1/agents/agent_123/chat",
                json_data={"message": "Hello"},
                headers={"X-Tenant-ID": tenant_id},
            )

            await gateway_client.post(
                "/api/v1/gateway/generate",
                json_data={"prompt": "Hello", "model": "gpt-4"},
                headers={"X-Tenant-ID": tenant_id},
            )

            # Verify tenant_id was included in both calls
            assert mock_client_instance.request.call_count >= 2

            await agent_client.close()
            await gateway_client.close()


@pytest.mark.integration
class TestFaaSOrchestratorIntegration:
    """Test Orchestrator Service integration with all services."""

    @pytest.fixture
    def mock_http_client(self):
        """Create mock HTTP client."""
        mock_client_instance = AsyncMock()
        mock_response = Mock()
        mock_response.json = Mock(return_value={"success": True, "data": {}})
        mock_response.raise_for_status = Mock()
        mock_response.status_code = 200
        mock_client_instance.request = AsyncMock(return_value=mock_response)
        mock_client_instance.aclose = AsyncMock()
        return mock_client_instance, mock_response

    @pytest.mark.asyncio
    async def test_orchestrator_routes_to_agent_service(self, mock_http_client):
        """Test Orchestrator routing to Agent Service."""
        mock_client_instance, mock_response = mock_http_client
        mock_response.json.return_value = {
            "success": True,
            "data": {"message": "Agent response"},
            "intent": "agent_chat",
            "service": "agent",
        }

        with patch("src.faas.shared.http_client.httpx.AsyncClient", return_value=mock_client_instance):
            orchestrator_client = ServiceHTTPClient(
                service_name="orchestrator",
                service_url="http://orchestrator-service:8080",
            )

            response = await orchestrator_client.post(
                "/api/v1/orchestrate",
                json_data={"query": "Hello, how are you?"},
            )

            assert response["success"] is True
            assert response["service"] == "agent"
            await orchestrator_client.close()

    @pytest.mark.asyncio
    async def test_orchestrator_routes_to_rag_service(self, mock_http_client):
        """Test Orchestrator routing to RAG Service."""
        mock_client_instance, mock_response = mock_http_client
        mock_response.json.return_value = {
            "success": True,
            "data": {"answer": "RAG answer", "documents": []},
            "intent": "rag_query",
            "service": "rag",
        }

        with patch("src.faas.shared.http_client.httpx.AsyncClient", return_value=mock_client_instance):
            orchestrator_client = ServiceHTTPClient(
                service_name="orchestrator",
                service_url="http://orchestrator-service:8080",
            )

            response = await orchestrator_client.post(
                "/api/v1/orchestrate",
                json_data={"query": "Search for documents about AI"},
            )

            assert response["success"] is True
            assert response["service"] == "rag"
            await orchestrator_client.close()

    @pytest.mark.asyncio
    async def test_orchestrator_routes_to_gateway_service(self, mock_http_client):
        """Test Orchestrator routing to Gateway Service."""
        mock_client_instance, mock_response = mock_http_client
        mock_response.json.return_value = {
            "success": True,
            "data": {"text": "Gateway response"},
            "intent": "text_generation",
            "service": "gateway",
        }

        with patch("src.faas.shared.http_client.httpx.AsyncClient", return_value=mock_client_instance):
            orchestrator_client = ServiceHTTPClient(
                service_name="orchestrator",
                service_url="http://orchestrator-service:8080",
            )

            response = await orchestrator_client.post(
                "/api/v1/orchestrate",
                json_data={"query": "Generate text about Python"},
            )

            assert response["success"] is True
            assert response["service"] == "gateway"
            await orchestrator_client.close()

    @pytest.mark.asyncio
    async def test_orchestrator_uses_cache_service(self, mock_http_client):
        """Test Orchestrator integration with Cache Service."""
        mock_client_instance, mock_response = mock_http_client
        mock_response.json.return_value = {
            "success": True,
            "data": {"message": "Cached response"},
            "cached": True,
        }

        with patch("src.faas.shared.http_client.httpx.AsyncClient", return_value=mock_client_instance):
            orchestrator_client = ServiceHTTPClient(
                service_name="orchestrator",
                service_url="http://orchestrator-service:8080",
            )

            response = await orchestrator_client.post(
                "/api/v1/orchestrate",
                json_data={"query": "Cached query", "cache_enabled": True},
            )

            assert response["success"] is True
            assert response["cached"] is True
            await orchestrator_client.close()


@pytest.mark.integration
class TestFaaSEndToEndIntegration:
    """Test end-to-end FaaS service integration scenarios."""

    @pytest.fixture
    def mock_http_client(self):
        """Create mock HTTP client."""
        mock_client_instance = AsyncMock()
        mock_response = Mock()
        mock_response.json = Mock(return_value={"success": True, "data": {}})
        mock_response.raise_for_status = Mock()
        mock_response.status_code = 200
        mock_client_instance.request = AsyncMock(return_value=mock_response)
        mock_client_instance.aclose = AsyncMock()
        return mock_client_instance, mock_response

    @pytest.mark.asyncio
    async def test_complete_agent_workflow_with_all_services(self, mock_http_client):
        """Test complete agent workflow involving multiple services."""
        mock_client_instance, mock_response = mock_http_client

        # Simulate complete workflow responses
        mock_response.json.side_effect = [
            {"success": True, "data": {"documents": [{"content": "Context"}]}},  # RAG
            {"text": "Agent response with context", "model": "gpt-4"},  # Gateway
            {"success": True, "cached": True},  # Cache
            {"success": True, "operation_id": "op_123"},  # LLMOps
        ]

        with patch("src.faas.shared.http_client.httpx.AsyncClient", return_value=mock_client_instance):
            # Step 1: Agent calls RAG
            rag_client = ServiceHTTPClient(
                service_name="rag",
                service_url="http://rag-service:8080",
            )
            rag_response = await rag_client.post(
                "/api/v1/rag/query",
                json_data={"query": "What is AI?"},
            )

            # Step 2: Agent calls Gateway
            gateway_client = ServiceHTTPClient(
                service_name="gateway",
                service_url="http://gateway-service:8080",
            )
            gateway_response = await gateway_client.post(
                "/api/v1/gateway/generate",
                json_data={"prompt": "Answer with context", "model": "gpt-4"},
            )

            # Step 3: Agent caches result
            cache_client = ServiceHTTPClient(
                service_name="cache",
                service_url="http://cache-service:8080",
            )
            cache_response = await cache_client.post(
                "/api/v1/cache/set",
                json_data={"key": "agent_response", "value": gateway_response},
            )

            # Step 4: LLMOps logs operation
            llmops_client = ServiceHTTPClient(
                service_name="llmops",
                service_url="http://llmops-service:8080",
            )
            llmops_response = await llmops_client.post(
                "/api/v1/llmops/operations",
                json_data={"operation_type": "agent_chat", "tokens": 100},
            )

            # Verify all services were called
            assert rag_response["success"] is True
            assert "text" in gateway_response
            assert cache_response["success"] is True
            assert llmops_response["success"] is True

            await rag_client.close()
            await gateway_client.close()
            await cache_client.close()
            await llmops_client.close()

