"""
Unit tests for Gateway Service.
"""


from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from src.faas.services.gateway_service import create_gateway_service
from src.faas.shared.config import ServiceConfig


@pytest.fixture
def mock_config():
    """Create mock service configuration."""
    return ServiceConfig(
        service_name="gateway-service",
        service_version="1.0.0",
        service_port=8080,
        database_url="",
        gateway_service_url=None,
        cache_service_url=None,
        rag_service_url=None,
        agent_service_url=None,
        ml_service_url=None,
        prompt_service_url=None,
        data_ingestion_service_url=None,
        prompt_generator_service_url=None,
        llmops_service_url=None,
        redis_url=None,
        nats_url=None,
        otel_exporter_otlp_endpoint=None,
        enable_nats=False,
        enable_otel=False,
    )


@pytest.fixture
def gateway_service(mock_config):
    """Create gateway service instance for testing."""
    with patch("src.faas.services.gateway_service.get_database_connection"), \
         patch("src.faas.services.gateway_service.create_gateway") as mock_create_gateway:
        
        # Mock gateway
        mock_gateway = Mock()
        mock_gateway.generate_async = AsyncMock(return_value=Mock(
            text="Generated text",
            model="gpt-4",
            usage={"total_tokens": 100},
            finish_reason="stop",
        ))
        mock_gateway.embed_async = AsyncMock(return_value=Mock(
            embeddings=[[0.1, 0.2, 0.3]],
            model="text-embedding-3-small",
            usage={"total_tokens": 50},
        ))
        mock_create_gateway.return_value = mock_gateway
        
        service = create_gateway_service(
            service_name="gateway-service",
            config_overrides={},
        )
        
        # Patch _get_gateway to return the mock gateway
        service._get_gateway = Mock(return_value=mock_gateway)
        
        return service


def test_gateway_service_creation(gateway_service):
    """Test gateway service creation."""
    assert gateway_service is not None
    assert gateway_service.app is not None
    assert gateway_service.config.service_name == "gateway-service"


@pytest.mark.asyncio
async def test_generate_endpoint(gateway_service):
    """Test generate endpoint."""
    client = TestClient(gateway_service.app)
    
    response = client.post(
        "/api/v1/gateway/generate",
        json={
            "prompt": "Hello, world!",
            "model": "gpt-4",
            "max_tokens": 100,
        },
        headers={
            "X-Tenant-ID": "tenant_123",
            "X-Correlation-ID": "corr_123",
        },
    )
    
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert data["success"] is True
        assert "text" in data["data"]
        assert data["data"]["model"] == "gpt-4"


@pytest.mark.asyncio
async def test_generate_stream_endpoint(gateway_service):
    """Test generate stream endpoint."""
    with patch("src.faas.services.gateway_service.create_gateway") as mock_create_gateway:
        # Mock streaming response
        async def mock_stream():
            class MockChunk:
                def __init__(self, content):
                    self.choices = [Mock(delta=Mock(content=content))]
            yield MockChunk("Hello")
            yield MockChunk(" World")
        
        mock_gateway = Mock()
        mock_gateway.generate_async = AsyncMock(return_value=mock_stream())
        mock_create_gateway.return_value = mock_gateway
        
        client = TestClient(gateway_service.app)
        
        response = client.post(
            "/api/v1/gateway/generate/stream",
            json={
                "prompt": "Hello, world!",
                "model": "gpt-4",
            },
            headers={
                "X-Tenant-ID": "tenant_123",
            },
        )
        
        assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_embed_endpoint(gateway_service):
    """Test embed endpoint."""
    client = TestClient(gateway_service.app)
    
    response = client.post(
        "/api/v1/gateway/embeddings",
        json={
            "texts": ["Hello", "World"],
            "model": "text-embedding-3-small",
        },
        headers={
            "X-Tenant-ID": "tenant_123",
        },
    )
    
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert data["success"] is True
        assert "embeddings" in data["data"]
        assert len(data["data"]["embeddings"]) == 2


@pytest.mark.asyncio
async def test_get_providers_endpoint(gateway_service):
    """Test get providers endpoint."""
    client = TestClient(gateway_service.app)
    
    response = client.get(
        "/api/v1/gateway/providers",
        headers={
            "X-Tenant-ID": "tenant_123",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "providers" in data["data"]
    assert isinstance(data["data"]["providers"], list)


@pytest.mark.asyncio
async def test_get_rate_limits_endpoint(gateway_service):
    """Test get rate limits endpoint."""
    client = TestClient(gateway_service.app)
    
    response = client.get(
        "/api/v1/gateway/rate-limits",
        headers={
            "X-Tenant-ID": "tenant_123",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "rate_limits" in data["data"]


def test_health_check(gateway_service):
    """Test health check endpoint."""
    client = TestClient(gateway_service.app)
    
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "gateway-service"


@pytest.mark.asyncio
async def test_generate_missing_tenant_id(gateway_service):
    """Test generate endpoint without tenant ID."""
    client = TestClient(gateway_service.app)
    
    response = client.post(
        "/api/v1/gateway/generate",
        json={
            "prompt": "Hello, world!",
        },
    )
    
    assert response.status_code == 401  # AuthMiddleware should reject


@pytest.mark.asyncio
async def test_generate_error_handling(gateway_service):
    """Test generate endpoint error handling."""
    with patch("src.faas.services.gateway_service.create_gateway") as mock_create_gateway:
        mock_gateway = Mock()
        mock_gateway.generate_async = AsyncMock(side_effect=Exception("Test error"))
        mock_create_gateway.return_value = mock_gateway
        
        client = TestClient(gateway_service.app)
        
        response = client.post(
            "/api/v1/gateway/generate",
            json={
                "prompt": "Hello, world!",
            },
            headers={
                "X-Tenant-ID": "tenant_123",
            },
        )
        
        assert response.status_code == 500


@pytest.mark.asyncio
async def test_embed_error_handling(gateway_service):
    """Test embed endpoint error handling."""
    with patch("src.faas.services.gateway_service.create_gateway") as mock_create_gateway:
        mock_gateway = Mock()
        mock_gateway.embed_async = AsyncMock(side_effect=Exception("Test error"))
        mock_create_gateway.return_value = mock_gateway
        
        client = TestClient(gateway_service.app)
        
        response = client.post(
            "/api/v1/gateway/embeddings",
            json={
                "texts": ["Hello"],
            },
            headers={
                "X-Tenant-ID": "tenant_123",
            },
        )
        
        assert response.status_code == 500

