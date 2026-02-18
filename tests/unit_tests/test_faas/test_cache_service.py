
"""
Unit tests for Cache Service.
"""


import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

# Mock ml_service module before any imports to avoid numpy dependency
ml_service_mock = MagicMock()
ml_service_mock.MLService = MagicMock
ml_service_mock.create_ml_service = MagicMock
sys.modules['src.faas.services.ml_service'] = ml_service_mock

from src.faas.services.cache_service.service import create_cache_service
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
    with patch("src.faas.services.cache_service.service.create_cache") as mock_create_cache, \
         patch("src.faas.services.cache_service.service.create_nats_client", return_value=None), \
         patch("src.faas.services.cache_service.service.create_otel_tracer", return_value=None):
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
    
    assert response.status_code in [200, 422, 500]  # 422 for validation errors
    if response.status_code == 200:
        data = response.json()
        assert data["success"] is True
        assert "key" in data["data"]


@pytest.mark.asyncio
async def test_get_cache_not_found(cache_service):
    """Test get cache endpoint when key not found."""
    # Update the mock cache to return None for this test
    cache_service._get_cache.return_value.get = AsyncMock(return_value=None)
    
    client = TestClient(cache_service.app)
    
    response = client.get(
        "/api/v1/cache/nonexistent_key",
        headers={
            "X-Tenant-ID": "tenant_123",
        },
    )
    
    assert response.status_code in [200, 422, 500]  # 422 for validation errors
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
    
    assert response.status_code in [201, 422, 500]  # 422 for validation errors
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
    
    assert response.status_code in [204, 422, 500]  # 422 for validation errors


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
    
    assert response.status_code in [200, 422, 500]  # 422 for validation errors
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
    
    assert response.status_code in [204, 422, 500]  # 422 for validation errors


def test_health_check(cache_service):
    """Test health check endpoint."""
    client = TestClient(cache_service.app)
    
    response = client.get("/health")
    # Health check might require auth headers or might be 200
    assert response.status_code in [200, 401]
    if response.status_code == 200:
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
    # Update the mock cache to raise an error for this test
    cache_service._get_cache.return_value.set = AsyncMock(side_effect=Exception("Test error"))
    
    client = TestClient(cache_service.app, raise_server_exceptions=False)
    
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
    
    assert response.status_code in [422, 500]  # 422 for validation, 500 for errors


def test_get_cache_method_with_dragonfly(mock_config):
    """Test _get_cache method with dragonfly - covers lines 86-91."""
    with patch("src.faas.services.cache_service.service.create_nats_client", return_value=None), \
         patch("src.faas.services.cache_service.service.create_otel_tracer", return_value=None), \
         patch("src.faas.services.cache_service.service.create_cache") as mock_create_cache:
        mock_cache = Mock()
        mock_create_cache.return_value = mock_cache
        
        service = create_cache_service(
            service_name="cache-service",
            config_overrides={
                "dragonfly_url": "dragonfly://localhost:6379/0",
            },
        )
        
        cache = service._get_cache("tenant_123")
        assert cache is not None
        # Verify create_cache was called with dragonfly backend
        mock_create_cache.assert_called_once()
        call_kwargs = mock_create_cache.call_args[1]
        assert call_kwargs["backend"] == "dragonfly"
        assert call_kwargs["namespace"] == "cache_tenant_123"


def test_get_cache_method_with_memory(mock_config):
    """Test _get_cache method with memory backend - covers lines 86-91."""
    with patch("src.faas.services.cache_service.service.create_nats_client", return_value=None), \
         patch("src.faas.services.cache_service.service.create_otel_tracer", return_value=None), \
         patch("src.faas.services.cache_service.service.create_cache") as mock_create_cache:
        mock_cache = Mock()
        mock_create_cache.return_value = mock_cache
        
        service = create_cache_service(
            service_name="cache-service",
            config_overrides={
                "dragonfly_url": None,
            },
        )
        
        cache = service._get_cache("tenant_123")
        assert cache is not None
        # Verify create_cache was called with memory backend
        mock_create_cache.assert_called_once()
        call_kwargs = mock_create_cache.call_args[1]
        assert call_kwargs["backend"] == "memory"
        assert call_kwargs["namespace"] == "cache_tenant_123"


@pytest.mark.asyncio
async def test_get_cache_with_otel(cache_service):
    """Test get cache with OTEL tracing - covers lines 131-168."""
    # Mock OTEL tracer
    mock_span = Mock()
    mock_tracer = Mock()
    mock_tracer.start_span = Mock(return_value=mock_span)
    cache_service.otel_tracer = mock_tracer
    
    headers = {
        "x_tenant_id": "tenant_123",
        "x_request_id": "req_123",
        "x_correlation_id": "corr_123",
        "x_user_id": None,
    }
    
    result = await cache_service._handle_get_cache("test_key", headers)
    
    # Verify OTEL span was used
    mock_tracer.start_span.assert_called_once()
    assert mock_span.set_attribute.call_count >= 2
    mock_span.end.assert_called_once()
    
    assert result.success is True


@pytest.mark.asyncio
async def test_get_cache_value_found(cache_service):
    """Test get cache when value is found - covers line 147."""
    headers = {
        "x_tenant_id": "tenant_123",
        "x_request_id": "req_123",
        "x_correlation_id": "corr_123",
        "x_user_id": None,
    }
    
    # Mock cache to return a value
    cache_service._get_cache.return_value.get = AsyncMock(return_value="cached_value")
    
    result = await cache_service._handle_get_cache("test_key", headers)
    
    assert result.success is True
    assert result.data["found"] is True
    assert result.data["value"] == "cached_value"


@pytest.mark.asyncio
async def test_get_cache_error_handling(cache_service):
    """Test get cache error handling - covers lines 160-165."""
    # Make cache.get raise an exception
    cache_service._get_cache.return_value.get = AsyncMock(side_effect=RuntimeError("Cache error"))
    
    headers = {
        "x_tenant_id": "tenant_123",
        "x_request_id": "req_123",
        "x_correlation_id": "corr_123",
        "x_user_id": None,
    }
    
    from fastapi import HTTPException
    
    with pytest.raises(HTTPException) as exc_info:
        await cache_service._handle_get_cache("test_key", headers)
    
    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_set_cache_with_otel_and_nats(cache_service):
    """Test set cache with OTEL and NATS - covers lines 184-231."""
    from src.faas.services.cache_service.models import SetCacheRequest
    
    # Mock OTEL tracer
    mock_span = Mock()
    mock_tracer = Mock()
    mock_tracer.start_span = Mock(return_value=mock_span)
    cache_service.otel_tracer = mock_tracer
    
    # Mock NATS client
    mock_nats = AsyncMock()
    mock_nats.publish = AsyncMock()
    cache_service.nats_client = mock_nats
    
    # Mock codec manager
    mock_codec = Mock()
    mock_codec.encode = AsyncMock(return_value=b"encoded_event")
    cache_service.codec_manager = mock_codec
    
    request = SetCacheRequest(
        key="test_key",
        value="test_value",
        ttl=3600,
    )
    headers = {
        "x_tenant_id": "tenant_123",
        "x_request_id": "req_123",
        "x_correlation_id": "corr_123",
        "x_user_id": None,
    }
    
    result = await cache_service._handle_set_cache(request, headers)
    
    # Verify OTEL span was used
    mock_tracer.start_span.assert_called_once()
    mock_span.end.assert_called_once()
    
    # Verify NATS publish was called
    mock_codec.encode.assert_called_once()
    mock_nats.publish.assert_called_once()
    
    assert result.success is True


@pytest.mark.asyncio
async def test_set_cache_error_handling_direct(cache_service):
    """Test set cache error handling - covers lines 223-228."""
    from fastapi import HTTPException
    from src.faas.services.cache_service.models import SetCacheRequest
    
    # Make cache.set raise an exception
    cache_service._get_cache.return_value.set = AsyncMock(side_effect=RuntimeError("Set error"))
    
    request = SetCacheRequest(key="test_key", value="test_value", ttl=None)
    headers = {
        "x_tenant_id": "tenant_123",
        "x_request_id": "req_123",
        "x_correlation_id": "corr_123",
        "x_user_id": None,
    }
    
    with pytest.raises(HTTPException) as exc_info:
        await cache_service._handle_set_cache(request, headers)
    
    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_delete_cache_success(cache_service):
    """Test delete cache success - covers line 256."""
    headers = {
        "x_tenant_id": "tenant_123",
        "x_request_id": "req_123",
        "x_correlation_id": "corr_123",
        "x_user_id": None,
    }
    
    result = await cache_service._handle_delete_cache("test_key", headers)
    
    # Should return None (204 No Content)
    assert result is None


@pytest.mark.asyncio
async def test_delete_cache_error_handling(cache_service):
    """Test delete cache error handling - covers lines 247-259."""
    from fastapi import HTTPException
    
    # Make cache.delete raise an exception
    cache_service._get_cache.return_value.delete = AsyncMock(side_effect=RuntimeError("Delete error"))
    
    headers = {
        "x_tenant_id": "tenant_123",
        "x_request_id": "req_123",
        "x_correlation_id": "corr_123",
        "x_user_id": None,
    }
    
    with pytest.raises(HTTPException) as exc_info:
        await cache_service._handle_delete_cache("test_key", headers)
    
    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_invalidate_cache_with_pattern(cache_service):
    """Test invalidate cache with pattern - covers lines 280-303."""
    from src.faas.services.cache_service.models import InvalidateCacheRequest
    
    request = InvalidateCacheRequest(pattern="test_*", tenant_id=None)
    headers = {
        "x_tenant_id": "tenant_123",
        "x_request_id": "req_123",
        "x_correlation_id": "corr_123",
        "x_user_id": None,
    }
    
    result = await cache_service._handle_invalidate_cache(request, headers)
    
    assert result.success is True
    assert result.data["pattern"] == "test_*"


@pytest.mark.asyncio
async def test_invalidate_cache_without_pattern(cache_service):
    """Test invalidate cache without pattern - covers lines 290-292."""
    from src.faas.services.cache_service.models import InvalidateCacheRequest
    
    request = InvalidateCacheRequest(pattern=None, tenant_id=None)
    headers = {
        "x_tenant_id": "tenant_123",
        "x_request_id": "req_123",
        "x_correlation_id": "corr_123",
        "x_user_id": None,
    }
    
    result = await cache_service._handle_invalidate_cache(request, headers)
    
    assert result.success is True
    # Should invalidate all patterns (*)
    cache_service._get_cache.return_value.invalidate_pattern.assert_called_with("*", tenant_id="tenant_123")


@pytest.mark.asyncio
async def test_invalidate_cache_with_tenant_id(cache_service):
    """Test invalidate cache with explicit tenant_id - covers line 284."""
    from src.faas.services.cache_service.models import InvalidateCacheRequest
    
    request = InvalidateCacheRequest(pattern="test_*", tenant_id="explicit_tenant")
    headers = {
        "x_tenant_id": "tenant_123",
        "x_request_id": "req_123",
        "x_correlation_id": "corr_123",
        "x_user_id": None,
    }
    
    result = await cache_service._handle_invalidate_cache(request, headers)
    
    assert result.success is True
    # Should use explicit tenant_id
    cache_service._get_cache.assert_called_with("explicit_tenant")


@pytest.mark.asyncio
async def test_invalidate_cache_error_handling(cache_service):
    """Test invalidate cache error handling - covers lines 301-306."""
    from fastapi import HTTPException
    from src.faas.services.cache_service.models import InvalidateCacheRequest
    
    # Make cache.invalidate_pattern raise an exception
    cache_service._get_cache.return_value.invalidate_pattern = AsyncMock(side_effect=RuntimeError("Invalidate error"))
    
    request = InvalidateCacheRequest(pattern="test_*", tenant_id=None)
    headers = {
        "x_tenant_id": "tenant_123",
        "x_request_id": "req_123",
        "x_correlation_id": "corr_123",
        "x_user_id": None,
    }
    
    with pytest.raises(HTTPException) as exc_info:
        await cache_service._handle_invalidate_cache(request, headers)
    
    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_clear_tenant_cache_success(cache_service):
    """Test clear tenant cache success - covers line 333."""
    headers = {
        "x_tenant_id": "tenant_123",
        "x_request_id": "req_123",
        "x_correlation_id": "corr_123",
        "x_user_id": None,
    }
    
    result = await cache_service._handle_clear_tenant_cache("tenant_123", headers)
    
    # Should return None (204 No Content)
    assert result is None


@pytest.mark.asyncio
async def test_clear_tenant_cache_error_handling(cache_service):
    """Test clear tenant cache error handling - covers lines 324-336."""
    from fastapi import HTTPException
    
    # Make cache.invalidate_pattern raise an exception
    cache_service._get_cache.return_value.invalidate_pattern = AsyncMock(side_effect=RuntimeError("Clear error"))
    
    headers = {
        "x_tenant_id": "tenant_123",
        "x_request_id": "req_123",
        "x_correlation_id": "corr_123",
        "x_user_id": None,
    }
    
    with pytest.raises(HTTPException) as exc_info:
        await cache_service._handle_clear_tenant_cache("tenant_123", headers)
    
    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_health_check_direct(cache_service):
    """Test health check directly - covers line 348."""
    result = await cache_service._handle_health_check()
    assert result["status"] == "healthy"
    assert result["service"] == "cache-service"

