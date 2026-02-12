"""
Unit tests for ServiceHTTPClient.
"""


from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from src.core.utils.circuit_breaker import CircuitBreakerConfig, CircuitState
from src.faas.shared.http_client import (
    ServiceClientError,
    ServiceClientManager,
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
    # Need to set _opened_at to prevent automatic transition to HALF_OPEN
    from datetime import datetime, timedelta
    http_client.circuit_breaker.state = CircuitState.OPEN
    http_client.circuit_breaker._opened_at = datetime.now() - timedelta(seconds=1)
    http_client.circuit_breaker.stats.last_failure_time = datetime.now()
    
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


@pytest.mark.asyncio
async def test_make_request_circuit_breaker_runtime_error(http_client, mock_httpx_client):
    """Test _make_request with RuntimeError that is not circuit breaker open - covers line 157."""
    # Make circuit breaker call raise a RuntimeError that is not "is OPEN"
    http_client.circuit_breaker.call = AsyncMock(side_effect=RuntimeError("Some other error"))
    
    with pytest.raises(ServiceClientError) as exc_info:
        await http_client._make_request("GET", "/api/v1/test")
    
    assert "error" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_get_max_retries_exceeded(http_client, mock_httpx_client):
    """Test get() with max retries exceeded - covers lines 201-203."""
    mock_httpx_client.request.side_effect = httpx.RequestError("Request failed")
    
    with patch("asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(ServiceClientError):
            await http_client.get("/api/v1/test")
        
        # Should have tried max_retries times
        assert mock_httpx_client.request.call_count == http_client.max_retries


@pytest.mark.asyncio
async def test_get_no_last_error(http_client, mock_httpx_client):
    """Test get() when no last_error is set - covers line 203."""
    # This scenario is hard to trigger, but we can test by making max_retries=0
    http_client.max_retries = 0
    
    # Make request fail immediately
    mock_httpx_client.request.side_effect = httpx.RequestError("Request failed")
    
    with pytest.raises(ServiceClientError, match="Failed to make GET request"):
        await http_client.get("/api/v1/test")


@pytest.mark.asyncio
async def test_post_retry_logic(http_client, mock_httpx_client):
    """Test post() retry logic - covers lines 237-250."""
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
        response = await http_client.post("/api/v1/test", json_data={"key": "value"})
        assert response == {"success": True}
        assert mock_httpx_client.request.call_count == 2


@pytest.mark.asyncio
async def test_post_max_retries_exceeded(http_client, mock_httpx_client):
    """Test post() with max retries exceeded - covers lines 248-250."""
    mock_httpx_client.request.side_effect = httpx.RequestError("Request failed")
    
    with patch("asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(ServiceClientError):
            await http_client.post("/api/v1/test", json_data={"key": "value"})
        
        assert mock_httpx_client.request.call_count == http_client.max_retries


@pytest.mark.asyncio
async def test_post_no_last_error(http_client, mock_httpx_client):
    """Test post() when no last_error is set - covers line 250."""
    http_client.max_retries = 0
    mock_httpx_client.request.side_effect = httpx.RequestError("Request failed")
    
    with pytest.raises(ServiceClientError, match="Failed to make POST request"):
        await http_client.post("/api/v1/test", json_data={"key": "value"})


@pytest.mark.asyncio
async def test_put_retry_logic(http_client, mock_httpx_client):
    """Test put() retry logic - covers lines 284-297."""
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
        response = await http_client.put("/api/v1/test", json_data={"key": "value"})
        assert response == {"success": True}
        assert mock_httpx_client.request.call_count == 2


@pytest.mark.asyncio
async def test_put_max_retries_exceeded(http_client, mock_httpx_client):
    """Test put() with max retries exceeded - covers lines 295-297."""
    mock_httpx_client.request.side_effect = httpx.RequestError("Request failed")
    
    with patch("asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(ServiceClientError):
            await http_client.put("/api/v1/test", json_data={"key": "value"})
        
        assert mock_httpx_client.request.call_count == http_client.max_retries


@pytest.mark.asyncio
async def test_put_no_last_error(http_client, mock_httpx_client):
    """Test put() when no last_error is set - covers line 297."""
    http_client.max_retries = 0
    mock_httpx_client.request.side_effect = httpx.RequestError("Request failed")
    
    with pytest.raises(ServiceClientError, match="Failed to make PUT request"):
        await http_client.put("/api/v1/test", json_data={"key": "value"})


@pytest.mark.asyncio
async def test_delete_retry_logic(http_client, mock_httpx_client):
    """Test delete() retry logic - covers lines 329-342."""
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
        response = await http_client.delete("/api/v1/test")
        assert response == {"success": True}
        assert mock_httpx_client.request.call_count == 2


@pytest.mark.asyncio
async def test_delete_max_retries_exceeded(http_client, mock_httpx_client):
    """Test delete() with max retries exceeded - covers lines 340-342."""
    mock_httpx_client.request.side_effect = httpx.RequestError("Request failed")
    
    with patch("asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(ServiceClientError):
            await http_client.delete("/api/v1/test")
        
        assert mock_httpx_client.request.call_count == http_client.max_retries


@pytest.mark.asyncio
async def test_delete_no_last_error(http_client, mock_httpx_client):
    """Test delete() when no last_error is set - covers line 342."""
    http_client.max_retries = 0
    mock_httpx_client.request.side_effect = httpx.RequestError("Request failed")
    
    with pytest.raises(ServiceClientError, match="Failed to make DELETE request"):
        await http_client.delete("/api/v1/test")


@pytest.mark.asyncio
async def test_post_wait_time_capped(http_client, mock_httpx_client):
    """Test post() wait time is capped at 10 seconds - covers line 243."""
    # Make multiple failures to test exponential backoff capping
    mock_httpx_client.request.side_effect = httpx.RequestError("Request failed")
    http_client.max_retries = 5  # More retries to test capping
    
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        with pytest.raises(ServiceClientError):
            await http_client.post("/api/v1/test", json_data={"key": "value"})
        
        # Check that sleep was called with capped values
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        # All wait times should be <= 10
        assert all(wait <= 10 for wait in sleep_calls)


@pytest.mark.asyncio
async def test_put_wait_time_capped(http_client, mock_httpx_client):
    """Test put() wait time is capped at 10 seconds - covers line 290."""
    mock_httpx_client.request.side_effect = httpx.RequestError("Request failed")
    http_client.max_retries = 5
    
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        with pytest.raises(ServiceClientError):
            await http_client.put("/api/v1/test", json_data={"key": "value"})
        
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert all(wait <= 10 for wait in sleep_calls)


@pytest.mark.asyncio
async def test_delete_wait_time_capped(http_client, mock_httpx_client):
    """Test delete() wait time is capped at 10 seconds - covers line 335."""
    mock_httpx_client.request.side_effect = httpx.RequestError("Request failed")
    http_client.max_retries = 5
    
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        with pytest.raises(ServiceClientError):
            await http_client.delete("/api/v1/test")
        
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert all(wait <= 10 for wait in sleep_calls)


@pytest.mark.asyncio
async def test_make_request_with_full_url(http_client, mock_httpx_client):
    """Test _make_request with full URL - covers line 124."""
    await http_client._make_request("GET", "http://full-url.com/api/test")
    
    # Verify the full URL was used
    call_args = mock_httpx_client.request.call_args
    assert call_args[1]["url"] == "http://full-url.com/api/test"


@pytest.mark.asyncio
async def test_make_request_with_json_data(http_client, mock_httpx_client):
    """Test _make_request with json_data - covers line 133."""
    await http_client._make_request("POST", "/api/v1/test", json_data={"key": "value"})
    
    call_args = mock_httpx_client.request.call_args
    assert call_args[1]["json"] == {"key": "value"}


def test_service_client_manager_initialization():
    """Test ServiceClientManager initialization - covers lines 399-400."""
    from src.faas.shared.config import ServiceConfig
    
    config = ServiceConfig(
        service_name="test-manager",
        service_version="1.0.0",
        service_port=8080,
        database_url="",
        gateway_service_url="http://gateway:8080",
        cache_service_url="http://cache:8080",
        rag_service_url=None,
        agent_service_url=None,
        ml_service_url=None,
        prompt_service_url=None,
        data_ingestion_service_url=None,
        prompt_generator_service_url=None,
        llmops_service_url=None,
        dragonfly_url=None,
        nats_url=None,
        otel_exporter_otlp_endpoint=None,
        enable_nats=False,
        enable_otel=False,
    )
    
    manager = ServiceClientManager(config)
    assert manager.config == config
    assert manager._clients == {}


def test_service_client_manager_get_client_existing():
    """Test ServiceClientManager.get_client with existing client - covers line 413."""
    from src.faas.shared.config import ServiceConfig
    
    config = ServiceConfig(
        service_name="test-manager",
        service_version="1.0.0",
        service_port=8080,
        database_url="",
        gateway_service_url="http://gateway:8080",
        cache_service_url=None,
        rag_service_url=None,
        agent_service_url=None,
        ml_service_url=None,
        prompt_service_url=None,
        data_ingestion_service_url=None,
        prompt_generator_service_url=None,
        llmops_service_url=None,
        dragonfly_url=None,
        nats_url=None,
        otel_exporter_otlp_endpoint=None,
        enable_nats=False,
        enable_otel=False,
    )
    
    manager = ServiceClientManager(config)
    
    # Get client first time (creates it)
    client1 = manager.get_client("gateway")
    assert client1 is not None
    
    # Get client second time (returns cached)
    client2 = manager.get_client("gateway")
    assert client1 is client2


def test_service_client_manager_get_client_new():
    """Test ServiceClientManager.get_client creating new client - covers lines 412-430."""
    from src.faas.shared.config import ServiceConfig
    
    config = ServiceConfig(
        service_name="test-manager",
        service_version="1.0.0",
        service_port=8080,
        database_url="",
        gateway_service_url="http://gateway:8080",
        cache_service_url="http://cache:8080",
        rag_service_url=None,
        agent_service_url=None,
        ml_service_url=None,
        prompt_service_url=None,
        data_ingestion_service_url=None,
        prompt_generator_service_url=None,
        llmops_service_url=None,
        dragonfly_url=None,
        nats_url=None,
        otel_exporter_otlp_endpoint=None,
        enable_nats=False,
        enable_otel=False,
    )
    
    manager = ServiceClientManager(config)
    
    client = manager.get_client("gateway")
    assert client is not None
    assert client.service_name == "gateway"
    assert client.service_url == "http://gateway:8080"


def test_service_client_manager_get_client_no_url():
    """Test ServiceClientManager.get_client when URL not configured - covers lines 419-421."""
    from src.faas.shared.config import ServiceConfig
    
    config = ServiceConfig(
        service_name="test-manager",
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
        dragonfly_url=None,
        nats_url=None,
        otel_exporter_otlp_endpoint=None,
        enable_nats=False,
        enable_otel=False,
    )
    
    manager = ServiceClientManager(config)
    
    client = manager.get_client("unknown_service")
    assert client is None


@pytest.mark.asyncio
async def test_service_client_manager_close_all():
    """Test ServiceClientManager.close_all - covers lines 434-436."""
    from src.faas.shared.config import ServiceConfig
    
    config = ServiceConfig(
        service_name="test-manager",
        service_version="1.0.0",
        service_port=8080,
        database_url="",
        gateway_service_url="http://gateway:8080",
        cache_service_url="http://cache:8080",
        rag_service_url=None,
        agent_service_url=None,
        ml_service_url=None,
        prompt_service_url=None,
        data_ingestion_service_url=None,
        prompt_generator_service_url=None,
        llmops_service_url=None,
        dragonfly_url=None,
        nats_url=None,
        otel_exporter_otlp_endpoint=None,
        enable_nats=False,
        enable_otel=False,
    )
    
    manager = ServiceClientManager(config)
    
    # Create some clients
    manager.get_client("gateway")
    manager.get_client("cache")
    
    # Close all
    await manager.close_all()
    
    # Verify clients are closed and cleared
    assert manager._clients == {}


def test_create_service_client():
    """Test create_service_client factory function - covers line 455."""
    from src.faas.shared.http_client import create_service_client
    
    client = create_service_client(
        service_name="test-service",
        service_url="http://test-service:8080",
    )
    
    assert client.service_name == "test-service"
    assert client.service_url == "http://test-service:8080"


def test_create_service_client_with_config():
    """Test create_service_client with config - covers line 455."""
    from src.faas.shared.config import ServiceConfig
    from src.faas.shared.http_client import create_service_client
    
    config = ServiceConfig(
        service_name="test-service",
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
        dragonfly_url=None,
        nats_url=None,
        otel_exporter_otlp_endpoint=None,
        enable_nats=False,
        enable_otel=False,
    )
    
    client = create_service_client(
        service_name="test-service",
        service_url="http://test-service:8080",
        config=config,
    )
    
    assert client.config == config

