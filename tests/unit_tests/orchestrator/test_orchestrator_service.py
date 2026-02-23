"""
Tests for OrchestratorService.
"""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Mock dependencies
sys.modules['src.faas.services.ml_service'] = MagicMock()

from src.faas.orchestrator.query_router import QueryIntent
from src.faas.services.orchestrator_service.service import OrchestratorService
from src.faas.shared.config import ServiceConfig


@pytest.fixture
def mock_config():
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
def mock_db():
    """Create mock database connection."""
    db = MagicMock()
    db.fetch_one = AsyncMock(return_value=None)
    db.fetch_all = AsyncMock(return_value=[])
    db.execute = AsyncMock()
    return db


@pytest.fixture
def orchestrator_service(mock_config, mock_db):
    """Create orchestrator service instance for testing."""
    with patch("src.faas.services.orchestrator_service.service.create_gateway") as mock_create_gateway, \
         patch("src.core.litellm_gateway.create_gateway") as mock_core_gateway, \
         patch("src.faas.integrations.codec.create_codec_manager", return_value=None), \
         patch("src.faas.integrations.otel.create_otel_tracer", return_value=None):
        
        # Mock gateway
        mock_gateway = MagicMock()
        mock_gateway.generate_async = AsyncMock()
        mock_create_gateway.return_value = mock_gateway
        mock_core_gateway.return_value = mock_gateway
        
        service = OrchestratorService(
            config=mock_config,
            db_connection=mock_db,
        )
        
        # Mock cache mechanism
        service.cache_mechanism.get = AsyncMock(return_value=None)
        service.cache_mechanism.set = AsyncMock()
        
        # Mock query router
        service.query_router.analyze_intent = AsyncMock(return_value={
            "intent": QueryIntent.AGENT_CHAT.value,
            "confidence": 0.95,
            "reasoning": "Test",
        })
        
        # Mock service clients
        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value={
            "success": True,
            "data": {"message": "Hello"},
            "metadata": {},
        })
        service.service_clients.get_client = MagicMock(return_value=mock_client)
        
        return service


def test_orchestrator_service_creation(orchestrator_service):
    """Test orchestrator service creation."""
    assert orchestrator_service is not None
    assert orchestrator_service.app is not None


def test_orchestrator_service_health_check(orchestrator_service):
    """Test health check endpoint."""
    client = TestClient(orchestrator_service.app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "orchestrator"


@pytest.mark.asyncio
async def test_handle_orchestrate_cache_hit(orchestrator_service):
    """Test orchestrate endpoint with cache hit."""
    cached_value = {
        "data": {"message": "Cached response"},
        "intent": QueryIntent.AGENT_CHAT.value,
        "service": "agent",
        "endpoint": "/api/v1/agents/agent_123/chat",
        "metadata": {},
    }
    orchestrator_service.cache_manager.get = AsyncMock(return_value=cached_value)
    
    client = TestClient(orchestrator_service.app)
    response = client.post(
        "/api/v1/orchestrate",
        json={
            "query": "Hello",
            "cache_enabled": True,
        },
        headers={
            "X-Tenant-ID": "tenant_123",
            "X-User-ID": "user_123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["cached"] is True
    assert data["intent"] == QueryIntent.AGENT_CHAT.value


@pytest.mark.asyncio
async def test_handle_orchestrate_no_cache(orchestrator_service):
    """Test orchestrate endpoint without cache."""
    orchestrator_service.cache_manager.get = AsyncMock(return_value=None)
    orchestrator_service.cache_manager.set = AsyncMock()
    
    client = TestClient(orchestrator_service.app)
    response = client.post(
        "/api/v1/orchestrate",
        json={
            "query": "Hello",
            "cache_enabled": False,
        },
        headers={
            "X-Tenant-ID": "tenant_123",
            "X-User-ID": "user_123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["cached"] is False
    orchestrator_service.service_clients.get_client().post.assert_called_once()


@pytest.mark.asyncio
async def test_handle_orchestrate_with_explicit_intent(orchestrator_service):
    """Test orchestrate endpoint with explicit intent."""
    orchestrator_service.cache_manager.get = AsyncMock(return_value=None)
    orchestrator_service.cache_manager.set = AsyncMock()
    
    client = TestClient(orchestrator_service.app)
    response = client.post(
        "/api/v1/orchestrate",
        json={
            "query": "Hello",
            "intent": QueryIntent.RAG_QUERY.value,
            "cache_enabled": True,
        },
        headers={
            "X-Tenant-ID": "tenant_123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == QueryIntent.RAG_QUERY.value
    # Should not call analyze_intent when explicit intent provided
    orchestrator_service.query_router.analyze_intent.assert_not_called()


@pytest.mark.asyncio
async def test_handle_orchestrate_service_unavailable(orchestrator_service):
    """Test orchestrate endpoint when service is unavailable."""
    orchestrator_service.cache_manager.get = AsyncMock(return_value=None)
    orchestrator_service.service_clients.get_client = MagicMock(return_value=None)
    
    client = TestClient(orchestrator_service.app)
    response = client.post(
        "/api/v1/orchestrate",
        json={
            "query": "Hello",
        },
        headers={
            "X-Tenant-ID": "tenant_123",
        },
    )
    assert response.status_code == 503


@pytest.mark.asyncio
async def test_handle_orchestrate_service_error(orchestrator_service):
    """Test orchestrate endpoint when service call fails."""
    from src.faas.shared.http_client import ServiceClientError
    
    orchestrator_service.cache_manager.get = AsyncMock(return_value=None)
    mock_client = MagicMock()
    mock_client.post = AsyncMock(side_effect=ServiceClientError("Service error"))
    orchestrator_service.service_clients.get_client = MagicMock(return_value=mock_client)
    
    client = TestClient(orchestrator_service.app)
    response = client.post(
        "/api/v1/orchestrate",
        json={
            "query": "Hello",
        },
        headers={
            "X-Tenant-ID": "tenant_123",
        },
    )
    assert response.status_code == 502


@pytest.mark.asyncio
async def test_handle_analyze_intent(orchestrator_service):
    """Test intent analysis endpoint."""
    client = TestClient(orchestrator_service.app)
    response = client.post(
        "/api/v1/intent/analyze",
        json={
            "query": "Hello, how are you?",
        },
        headers={
            "X-Tenant-ID": "tenant_123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "intent" in data
    assert "confidence" in data
    assert "reasoning" in data
    assert "suggested_service" in data
    assert "suggested_endpoint" in data


@pytest.mark.asyncio
async def test_handle_invalidate_cache(orchestrator_service):
    """Test cache invalidation endpoint."""
    orchestrator_service.cache_manager.invalidate = AsyncMock()
    
    client = TestClient(orchestrator_service.app)
    response = client.post(
        "/api/v1/cache/invalidate",
        json={
            "feature": "agent_chat",
            "tenant_id": "tenant_123",
        },
        headers={
            "X-Tenant-ID": "tenant_123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    orchestrator_service.cache_manager.invalidate.assert_called_once()


@pytest.mark.asyncio
async def test_handle_invalidate_cache_with_pattern(orchestrator_service):
    """Test cache invalidation endpoint with pattern."""
    orchestrator_service.cache_manager.invalidate = AsyncMock()
    
    client = TestClient(orchestrator_service.app)
    response = client.post(
        "/api/v1/cache/invalidate",
        json={
            "pattern": "orchestrator:agent_chat:*",
        },
        headers={
            "X-Tenant-ID": "tenant_123",
        },
    )
    assert response.status_code == 200
    orchestrator_service.cache_manager.invalidate.assert_called_once_with(
        feature=None,
        tenant_id="tenant_123",
        pattern="orchestrator:agent_chat:*",
    )

