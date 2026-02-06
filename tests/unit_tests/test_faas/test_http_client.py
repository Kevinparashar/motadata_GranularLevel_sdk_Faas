"""
Unit tests for ServiceHTTPClient.
"""


from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from src.core.utils.circuit_breaker import CircuitBreakerConfig
from src.faas.shared.http_client import (
    ServiceClientError,
    ServiceHTTPClient,
    ServiceTimeoutError,
    ServiceUnavailableError,
)


@pytest.fixture
def mock_httpx_client():
    """Create mock httpx client."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_response = Mock()
        mock_response.json = Mock(return_value={"success": True})
        mock_response.raise_for_status = Mock()
        mock_response.status_code = 200
        
        mock_client_instance = AsyncMock()
        mock_client_instance.request = AsyncMock(return_value=mock_response)
        mock_client_instance.aclose = AsyncMock()
        mock_client_class.return_value = mock_client_instance
        
        yield mock_client_instance


@pytest.fixture
def http_client(mock_httpx_client):
    """Create ServiceHTTPClient instance for testing."""
    return ServiceHTTPClient(
        service_name="test-service",
        service_url="http://test-service:8080",
        timeout=30.0,
        max_retries=3,
    )


@pytest.mark.asyncio
async def test_http_client_initialization(http_client):
    """Test HTTP client initialization."""
    assert http_client.service_name == "test-service"
    assert http_client.service_url == "http://test-service:8080"
    assert abs(http_client.timeout - 30.0) < 0.001
    assert http_client.max_retries == 3
    assert http_client.circuit_breaker is not None


@pytest.mark.asyncio
async def test_get_request_success(http_client, mock_httpx_client):
    """Test successful GET request."""
    response = await http_client.get("/api/v1/test")
    
    assert response == {"success": True}
    mock_httpx_client.request.assert_called_once()


@pytest.mark.asyncio
async def test_post_request_success(http_client, mock_httpx_client):
    """Test successful POST request."""
    response = await http_client.post(
        "/api/v1/test",
        json_data={"key": "value"},
    )
    
    assert response == {"success": True}
    mock_httpx_client.request.assert_called_once()


@pytest.mark.asyncio
async def test_put_request_success(http_client, mock_httpx_client):
    """Test successful PUT request."""
    response = await http_client.put(
        "/api/v1/test",
        json_data={"key": "value"},
    )
    
    assert response == {"success": True}
    mock_httpx_client.request.assert_called_once()


@pytest.mark.asyncio
async def test_delete_request_success(http_client, mock_httpx_client):
    """Test successful DELETE request."""
    response = await http_client.delete("/api/v1/test")
    
    assert response == {"success": True}
    mock_httpx_client.request.assert_called_once()


@pytest.mark.asyncio
async def test_get_request_with_headers(http_client, mock_httpx_client):
    """Test GET request with custom headers."""
    await http_client.get(
        "/api/v1/test",
        headers={"X-Custom-Header": "value"},
    )
    
    call_args = mock_httpx_client.request.call_args
    assert "X-Custom-Header" in call_args[1]["headers"]


@pytest.mark.asyncio
async def test_get_request_with_params(http_client, mock_httpx_client):
    """Test GET request with query parameters."""
    await http_client.get(
        "/api/v1/test",
        params={"key": "value"},
    )
    
    call_args = mock_httpx_client.request.call_args
    assert call_args[1]["params"] == {"key": "value"}


@pytest.mark.asyncio
async def test_timeout_error(http_client, mock_httpx_client):
    """Test timeout error handling."""
    mock_httpx_client.request.side_effect = httpx.TimeoutException("Timeout")
    
    with pytest.raises(ServiceTimeoutError):
        await http_client.get("/api/v1/test")


@pytest.mark.asyncio
async def test_http_status_error(http_client, mock_httpx_client):
    """Test HTTP status error handling."""
    mock_response = Mock()
    mock_response.status_code = 404
    mock_httpx_client.request.side_effect = httpx.HTTPStatusError(
        "Not found", request=Mock(), response=mock_response
    )
    
    with pytest.raises(ServiceClientError):
        await http_client.get("/api/v1/test")


@pytest.mark.asyncio
async def test_request_error(http_client, mock_httpx_client):
    """Test request error handling."""
    mock_httpx_client.request.side_effect = httpx.RequestError("Request failed")
    
    with pytest.raises(ServiceClientError):
        await http_client.get("/api/v1/test")


@pytest.mark.asyncio
async def test_circuit_breaker_open(http_client, mock_httpx_client):
    """Test circuit breaker open error."""
    # Force circuit breaker to open state
    http_client.circuit_breaker.state = "OPEN"
    
    with pytest.raises(ServiceUnavailableError):
        await http_client.get("/api/v1/test")


@pytest.mark.asyncio
async def test_retry_on_error(http_client, mock_httpx_client):
    """Test retry logic on error."""
    # First call fails, second succeeds
    mock_response = Mock()
    mock_response.json = Mock(return_value={"success": True})
    mock_response.raise_for_status = Mock()
    mock_response.status_code = 200
    
    mock_httpx_client.request.side_effect = [
        httpx.RequestError("Request failed"),
        mock_response,
    ]
    
    with patch("asyncio.sleep", new_callable=AsyncMock):
        response = await http_client.get("/api/v1/test")
        assert response == {"success": True}
        assert mock_httpx_client.request.call_count == 2


@pytest.mark.asyncio
async def test_retry_max_attempts(http_client, mock_httpx_client):
    """Test retry max attempts."""
    mock_httpx_client.request.side_effect = httpx.RequestError("Request failed")
    
    with patch("asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(ServiceClientError):
            await http_client.get("/api/v1/test")
        
        # Should retry max_retries times
        assert mock_httpx_client.request.call_count == http_client.max_retries


@pytest.mark.asyncio
async def test_get_headers(http_client):
    """Test get_headers method."""
    headers = http_client.get_headers(
        tenant_id="tenant_123",
        user_id="user_456",
        correlation_id="corr_789",
        request_id="req_012",
    )
    
    assert headers["X-Tenant-ID"] == "tenant_123"
    assert headers["X-User-ID"] == "user_456"
    assert headers["X-Correlation-ID"] == "corr_789"
    assert headers["X-Request-ID"] == "req_012"


@pytest.mark.asyncio
async def test_get_headers_minimal(http_client):
    """Test get_headers with minimal parameters."""
    headers = http_client.get_headers(tenant_id="tenant_123")
    
    assert headers["X-Tenant-ID"] == "tenant_123"
    assert "X-User-ID" not in headers


@pytest.mark.asyncio
async def test_close_client(http_client, mock_httpx_client):
    """Test closing HTTP client."""
    await http_client.close()
    
    mock_httpx_client.aclose.assert_called_once()


@pytest.mark.asyncio
async def test_circuit_breaker_config(http_client):
    """Test circuit breaker configuration."""
    assert http_client.circuit_breaker is not None
    assert http_client.circuit_breaker.name == "http_client_test-service"


@pytest.mark.asyncio
async def test_custom_circuit_breaker_config():
    """Test custom circuit breaker configuration."""
    custom_config = CircuitBreakerConfig(
        failure_threshold=10,
        success_threshold=5,
        timeout=120.0,
    )
    
    client = ServiceHTTPClient(
        service_name="test-service",
        service_url="http://test-service:8080",
        circuit_breaker_config=custom_config,
    )
    
    assert client.circuit_breaker.config.failure_threshold == 10
    assert client.circuit_breaker.config.success_threshold == 5
    assert abs(client.circuit_breaker.config.timeout - 120.0) < 0.001

