"""
Integration Tests for Orchestrator

Tests the integration between Orchestrator and other services/components.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.cache_mechanism import CacheConfig, CacheMechanism
from src.faas.orchestrator import (
    create_cache_manager,
    create_query_router,
    create_service_selector,
)
from src.faas.orchestrator.query_router import QueryIntent
from src.faas.shared.config import ServiceConfig


@pytest.mark.integration
class TestOrchestratorCacheIntegration:
    """Test Orchestrator-Cache integration."""

    @pytest.fixture
    def cache(self):
        """Create cache mechanism."""
        return CacheMechanism(CacheConfig(default_ttl=300, backend="memory"))

    @pytest.fixture
    def cache_manager(self, cache):
        """Create cache manager."""
        return create_cache_manager(cache=cache)

    @pytest.mark.asyncio
    async def test_cache_manager_integrates_with_cache_mechanism(self, cache_manager, cache):
        """Test that CacheManager integrates with CacheMechanism."""
        # Set value through cache manager
        await cache_manager.set(
            feature="agent_chat",
            query="Hello",
            value={"data": "Response"},
            tenant_id="tenant_123",
        )

        # Get value through cache manager
        cached = await cache_manager.get(
            feature="agent_chat",
            query="Hello",
            tenant_id="tenant_123",
        )

        assert cached is not None
        assert cached["data"] == "Response"

    @pytest.mark.asyncio
    async def test_cache_manager_tenant_isolation(self, cache_manager):
        """Test that CacheManager maintains tenant isolation."""
        # Set value for tenant A
        await cache_manager.set(
            feature="agent_chat",
            query="Hello",
            value={"data": "Response A"},
            tenant_id="tenant_a",
        )

        # Set value for tenant B
        await cache_manager.set(
            feature="agent_chat",
            query="Hello",
            value={"data": "Response B"},
            tenant_id="tenant_b",
        )

        # Get value for tenant A
        cached_a = await cache_manager.get(
            feature="agent_chat",
            query="Hello",
            tenant_id="tenant_a",
        )

        # Get value for tenant B
        cached_b = await cache_manager.get(
            feature="agent_chat",
            query="Hello",
            tenant_id="tenant_b",
        )

        assert cached_a["data"] == "Response A"
        assert cached_b["data"] == "Response B"
        assert cached_a != cached_b

    @pytest.mark.asyncio
    async def test_cache_manager_invalidation(self, cache_manager):
        """Test cache invalidation through CacheManager."""
        # Set multiple values
        await cache_manager.set(
            feature="agent_chat",
            query="Query 1",
            value={"data": "Response 1"},
            tenant_id="tenant_123",
        )
        await cache_manager.set(
            feature="agent_chat",
            query="Query 2",
            value={"data": "Response 2"},
            tenant_id="tenant_123",
        )

        # Verify both are cached
        assert await cache_manager.get("agent_chat", "Query 1", "tenant_123") is not None
        assert await cache_manager.get("agent_chat", "Query 2", "tenant_123") is not None

        # Invalidate all for tenant
        await cache_manager.invalidate(tenant_id="tenant_123")

        # Verify both are invalidated
        assert await cache_manager.get("agent_chat", "Query 1", "tenant_123") is None
        assert await cache_manager.get("agent_chat", "Query 2", "tenant_123") is None


@pytest.mark.integration
class TestOrchestratorGatewayIntegration:
    """Test Orchestrator-Gateway integration."""

    @pytest.fixture
    def gateway(self):
        """Create mock gateway."""
        gateway = MagicMock()
        gateway.generate_async = AsyncMock()
        return gateway

    @pytest.fixture
    def cache(self):
        """Create cache mechanism."""
        return CacheMechanism(CacheConfig(default_ttl=300, backend="memory"))

    @pytest.fixture
    def query_router(self, gateway, cache):
        """Create query router."""
        return create_query_router(
            gateway=gateway,
            enable_llm_classification=True,
            cache=cache,
        )

    @pytest.mark.asyncio
    async def test_query_router_integrates_with_gateway(self, query_router, gateway):
        """Test that QueryRouter integrates with Gateway for intent classification."""
        # Mock LLM response
        llm_response = MagicMock()
        llm_response.text = '{"intent": "agent_chat", "confidence": 0.95, "reasoning": "Conversational"}'
        gateway.generate_async = AsyncMock(return_value=llm_response)

        # Analyze intent
        result = await query_router.analyze_intent(
            query="Hello, how are you?",
            tenant_id="tenant_123",
        )

        # Verify gateway was called
        gateway.generate_async.assert_called_once()
        assert result["intent"] == QueryIntent.AGENT_CHAT.value
        assert result["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_query_router_caches_intent_results(self, query_router, gateway, cache):
        """Test that QueryRouter caches intent classification results."""
        # Mock LLM response
        llm_response = MagicMock()
        llm_response.text = '{"intent": "rag_query", "confidence": 0.9, "reasoning": "Document query"}'
        gateway.generate_async = AsyncMock(return_value=llm_response)

        # First call - should call gateway
        result1 = await query_router.analyze_intent(
            query="Search documents",
            tenant_id="tenant_123",
        )
        assert gateway.generate_async.call_count == 1

        # Second call - should use cache
        result2 = await query_router.analyze_intent(
            query="Search documents",
            tenant_id="tenant_123",
        )
        # Should still be 1 (cached, no new gateway call)
        assert gateway.generate_async.call_count == 1
        assert result1 == result2


@pytest.mark.integration
class TestOrchestratorServiceIntegration:
    """Test Orchestrator-Service integration."""

    @pytest.fixture
    def mock_config(self):
        """Create mock service configuration."""
        return ServiceConfig(
            service_name="orchestrator-service",
            service_version="1.0.0",
            service_port=8080,
            database_url="postgresql://test:test@localhost/test",
            gateway_service_url="http://gateway-service:8080",
            agent_service_url="http://agent-service:8080",
            rag_service_url="http://rag-service:8080",
            cache_service_url="http://cache-service:8080",
            ml_service_url=None,
            prompt_service_url=None,
            data_ingestion_service_url=None,
            prompt_generator_service_url=None,
            llmops_service_url=None,
            orchestrator_service_url=None,
            dragonfly_url=None,
            nats_url=None,
            otel_exporter_otlp_endpoint=None,
            enable_nats=False,
            enable_otel=False,
        )

    @pytest.fixture
    def service_selector(self, mock_config):
        """Create service selector."""
        return create_service_selector(config=mock_config)

    @pytest.mark.asyncio
    async def test_service_selector_routes_to_agent_service(self, service_selector):
        """Test that ServiceSelector routes agent chat to Agent Service."""
        context = {"agent_id": "agent_123"}
        routing = service_selector.select_service(
            intent=QueryIntent.AGENT_CHAT.value,
            query="Hello",
            context=context,
            tenant_id="tenant_123",
        )

        assert routing["service"] == "agent"
        assert "/api/v1/agents/agent_123/chat" in routing["endpoint"]
        assert routing["method"] == "POST"
        assert "message" in routing["payload"]

    @pytest.mark.asyncio
    async def test_service_selector_routes_to_rag_service(self, service_selector):
        """Test that ServiceSelector routes RAG queries to RAG Service."""
        routing = service_selector.select_service(
            intent=QueryIntent.RAG_QUERY.value,
            query="Search documents",
            context=None,
            tenant_id="tenant_123",
        )

        assert routing["service"] == "rag"
        assert routing["endpoint"] == "/api/v1/rag/query"
        assert routing["method"] == "POST"
        assert routing["payload"]["query"] == "Search documents"

    @pytest.mark.asyncio
    async def test_service_selector_routes_to_gateway_service(self, service_selector):
        """Test that ServiceSelector routes direct LLM to Gateway Service."""
        routing = service_selector.select_service(
            intent=QueryIntent.DIRECT_LLM.value,
            query="Generate text",
            context=None,
            tenant_id="tenant_123",
        )

        assert routing["service"] == "gateway"
        assert routing["endpoint"] == "/api/v1/gateway/generate"
        assert routing["method"] == "POST"
        assert routing["payload"]["prompt"] == "Generate text"


@pytest.mark.integration
class TestOrchestratorEndToEndIntegration:
    """Test end-to-end Orchestrator integration."""

    @pytest.fixture
    def cache(self):
        """Create cache mechanism."""
        return CacheMechanism(CacheConfig(default_ttl=300, backend="memory"))

    @pytest.fixture
    def gateway(self):
        """Create mock gateway."""
        gateway = MagicMock()
        gateway.generate_async = AsyncMock()
        return gateway

    @pytest.fixture
    def query_router(self, gateway, cache):
        """Create query router."""
        return create_query_router(
            gateway=gateway,
            enable_llm_classification=False,  # Use pattern matching for faster tests
            cache=cache,
        )

    @pytest.fixture
    def cache_manager(self, cache):
        """Create cache manager."""
        return create_cache_manager(cache=cache)

    @pytest.mark.asyncio
    async def test_end_to_end_orchestration_flow(self, query_router, cache_manager):
        """Test complete orchestration flow: intent → routing → caching."""
        # Step 1: Analyze intent
        intent_result = await query_router.analyze_intent(
            query="create agent for customer support",
            tenant_id="tenant_123",
        )
        assert intent_result["intent"] == QueryIntent.PROMPT_GENERATION.value

        # Step 2: Cache intent result
        await cache_manager.set(
            feature=intent_result["intent"],
            query="create agent for customer support",
            value={"intent": intent_result["intent"], "data": "Cached result"},
            tenant_id="tenant_123",
        )

        # Step 3: Retrieve from cache
        cached = await cache_manager.get(
            feature=intent_result["intent"],
            query="create agent for customer support",
            tenant_id="tenant_123",
        )

        assert cached is not None
        assert cached["intent"] == QueryIntent.PROMPT_GENERATION.value

    @pytest.mark.asyncio
    async def test_end_to_end_tenant_isolation(self, query_router, cache_manager):
        """Test end-to-end tenant isolation."""
        # Tenant A: Analyze and cache
        intent_a = await query_router.analyze_intent(
            query="Hello",
            tenant_id="tenant_a",
        )
        await cache_manager.set(
            feature=intent_a["intent"],
            query="Hello",
            value={"data": "Response A"},
            tenant_id="tenant_a",
        )

        # Tenant B: Analyze and cache
        intent_b = await query_router.analyze_intent(
            query="Hello",
            tenant_id="tenant_b",
        )
        await cache_manager.set(
            feature=intent_b["intent"],
            query="Hello",
            value={"data": "Response B"},
            tenant_id="tenant_b",
        )

        # Verify isolation
        cached_a = await cache_manager.get("agent_chat", "Hello", "tenant_a")
        cached_b = await cache_manager.get("agent_chat", "Hello", "tenant_b")

        # Both should be cached separately
        if cached_a:
            assert cached_a["data"] == "Response A"
        if cached_b:
            assert cached_b["data"] == "Response B"

