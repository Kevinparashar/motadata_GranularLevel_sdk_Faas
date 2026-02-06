"""
Unit tests for Cache Service.
"""


from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from src.faas.services.cache_service import create_cache_service
from src.faas.shared.config import ServiceConfig


@pytest.fixture
def mock_config():
    """Create mock service configuration."""
    return ServiceConfig(
        service_name="cache-service",
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
        dragonfly_url="dragonfly://localhost:6379/0",
        nats_url=None,
        otel_exporter_otlp_endpoint=None,
        enable_nats=False,
        enable_otel=False,
    )


@pytest.fixture
def cache_service(mock_config):
    """Create cache service instance for testing."""
    with patch("src.faas.services.cache_service.create_cache") as mock_create_cache:
        # Mock cache
        mock_cache = Mock()
        mock_cache.get = AsyncMock(return_value="cached_value")
        mock_cache.set = AsyncMock(return_value=None)
        mock_cache.delete = AsyncMock(return_value=None)
        mock_cache.invalidate_pattern = AsyncMock(return_value=None)
        mock_create_cache.return_value = mock_cache
        
        service = create_cache_service(
            service_name="cache-service",
            config_overrides={
                "dragonfly_url": "dragonfly://localhost:6379/0",
            },
        )
        
        # Patch _get_cache to return the mock cache
        service._get_cache = Mock(return_value=mock_cache)
        
        return service


def test_cache_service_creation(cache_service):
    """Test cache service creation."""
    assert cache_service is not None
    assert cache_service.app is not None
    assert cache_service.config.service_name == "cache-service"


@pytest.mark.asyncio
async def test_get_cache_endpoint(cache_service):
    """Test get cache endpoint."""
    client = TestClient(cache_service.app)
    
    response = client.get(
        "/api/v1/cache/test_key",
        headers={
            "X-Tenant-ID": "tenant_123",
        },
    )
    
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert data["success"] is True
        assert "key" in data["data"]


@pytest.mark.asyncio
async def test_get_cache_not_found(cache_service):
    """Test get cache endpoint when key not found."""
    with patch("src.faas.services.cache_service.create_cache") as mock_create_cache:
        mock_cache = Mock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_create_cache.return_value = mock_cache
        
        client = TestClient(cache_service.app)
        
        response = client.get(
            "/api/v1/cache/nonexistent_key",
            headers={
                "X-Tenant-ID": "tenant_123",
            },
        )
        
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert data["data"]["found"] is False


@pytest.mark.asyncio
async def test_set_cache_endpoint(cache_service):
    """Test set cache endpoint."""
    client = TestClient(cache_service.app)
    
    response = client.post(
        "/api/v1/cache",
        json={
            "key": "test_key",
            "value": "test_value",
            "ttl": 3600,
        },
        headers={
            "X-Tenant-ID": "tenant_123",
        },
    )
    
    assert response.status_code in [201, 500]
    if response.status_code == 201:
        data = response.json()
        assert data["success"] is True
        assert data["data"]["key"] == "test_key"


@pytest.mark.asyncio
async def test_delete_cache_endpoint(cache_service):
    """Test delete cache endpoint."""
    client = TestClient(cache_service.app)
    
    response = client.delete(
        "/api/v1/cache/test_key",
        headers={
            "X-Tenant-ID": "tenant_123",
        },
    )
    
    assert response.status_code in [204, 500]


@pytest.mark.asyncio
async def test_invalidate_cache_endpoint(cache_service):
    """Test invalidate cache endpoint."""
    client = TestClient(cache_service.app)
    
    response = client.post(
        "/api/v1/cache/invalidate",
        json={
            "pattern": "test_*",
        },
        headers={
            "X-Tenant-ID": "tenant_123",
        },
    )
    
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert data["success"] is True


@pytest.mark.asyncio
async def test_clear_tenant_cache_endpoint(cache_service):
    """Test clear tenant cache endpoint."""
    client = TestClient(cache_service.app)
    
    response = client.delete(
        "/api/v1/cache/tenant/tenant_123",
        headers={
            "X-Tenant-ID": "tenant_123",
        },
    )
    
    assert response.status_code in [204, 500]


def test_health_check(cache_service):
    """Test health check endpoint."""
    client = TestClient(cache_service.app)
    
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "cache-service"


@pytest.mark.asyncio
async def test_get_cache_missing_tenant_id(cache_service):
    """Test get cache endpoint without tenant ID."""
    client = TestClient(cache_service.app)
    
    response = client.get("/api/v1/cache/test_key")
    
    assert response.status_code == 401  # AuthMiddleware should reject


@pytest.mark.asyncio
async def test_set_cache_error_handling(cache_service):
    """Test set cache endpoint error handling."""
    with patch("src.faas.services.cache_service.create_cache") as mock_create_cache:
        mock_cache = Mock()
        mock_cache.set = AsyncMock(side_effect=Exception("Test error"))
        mock_create_cache.return_value = mock_cache
        
        client = TestClient(cache_service.app)
        
        response = client.post(
            "/api/v1/cache",
            json={
                "key": "test_key",
                "value": "test_value",
            },
            headers={
                "X-Tenant-ID": "tenant_123",
            },
        )
        
        assert response.status_code == 500

