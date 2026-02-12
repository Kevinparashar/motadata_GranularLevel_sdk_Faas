"""
Unit tests for FaaS Middleware.
"""


from unittest.mock import Mock

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from src.faas.shared.exceptions import ServiceException, ValidationError
from src.faas.shared.middleware import (
    AuthMiddleware,
    LoggingMiddleware,
    error_handler,
    setup_middleware,
)


@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint(request: Request):
        return {"status": "ok"}
    
    @app.get("/error")
    async def error_endpoint(request: Request):
        raise ValueError("Test error")
    
    @app.get("/service_error")
    async def service_error_endpoint(request: Request):
        raise ServiceException("Service error", status_code=400)
    
    return app


@pytest.mark.asyncio
async def test_logging_middleware(app):
    """Test logging middleware."""
    app.add_middleware(LoggingMiddleware)
    
    client = TestClient(app)
    
    response = client.get(
        "/test",
        headers={
            "X-Tenant-ID": "tenant_123",
            "X-Correlation-ID": "corr_123",
        },
    )
    
    assert response.status_code == 200
    assert "X-Process-Time" in response.headers


@pytest.mark.asyncio
async def test_auth_middleware_success(app):
    """Test auth middleware with valid tenant ID."""
    app.add_middleware(AuthMiddleware)
    
    client = TestClient(app)
    
    response = client.get(
        "/test",
        headers={
            "X-Tenant-ID": "tenant_123",
        },
    )
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_auth_middleware_missing_tenant_id(app):
    """Test auth middleware without tenant ID."""
    app.add_middleware(AuthMiddleware)
    
    client = TestClient(app)
    
    response = client.get("/test")
    
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "MISSING_TENANT_ID"


@pytest.mark.asyncio
async def test_error_handler_generic_exception(app):
    """Test error handler with generic exception."""
    app.add_exception_handler(Exception, error_handler)
    
    client = TestClient(app, raise_server_exceptions=False)
    
    response = client.get(
        "/error",
        headers={
            "X-Tenant-ID": "tenant_123",
            "X-Correlation-ID": "corr_123",
            "X-Request-ID": "req_123",
        },
    )
    
    assert response.status_code == 500
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert data["correlation_id"] == "corr_123"
    assert data["request_id"] == "req_123"


@pytest.mark.asyncio
async def test_error_handler_service_exception(app):
    """Test error handler with ServiceException."""
    app.add_exception_handler(Exception, error_handler)
    
    client = TestClient(app, raise_server_exceptions=False)
    
    response = client.get(
        "/service_error",
        headers={
            "X-Tenant-ID": "tenant_123",
            "X-Correlation-ID": "corr_123",
        },
    )
    
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "SERVICE_ERROR"


@pytest.mark.asyncio
async def test_error_handler_validation_error():
    """Test error handler with ValidationError."""
    app = FastAPI()
    
    @app.get("/validation_error")
    async def validation_error_endpoint(request: Request):
        raise ValidationError("Validation failed")
    
    app.add_exception_handler(Exception, error_handler)
    
    client = TestClient(app, raise_server_exceptions=False)
    
    response = client.get(
        "/validation_error",
        headers={
            "X-Tenant-ID": "tenant_123",
        },
    )
    
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_setup_middleware(app):
    """Test setup_middleware function."""
    setup_middleware(app)
    
    client = TestClient(app)
    
    # Test with tenant ID
    response = client.get(
        "/test",
        headers={
            "X-Tenant-ID": "tenant_123",
        },
    )
    
    assert response.status_code == 200
    
    # Test without tenant ID
    response = client.get("/test")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logging_middleware_process_time(app):
    """Test logging middleware adds process time header."""
    app.add_middleware(LoggingMiddleware)
    
    client = TestClient(app)
    
    response = client.get(
        "/test",
        headers={
            "X-Tenant-ID": "tenant_123",
        },
    )
    
    assert "X-Process-Time" in response.headers
    process_time = float(response.headers["X-Process-Time"])
    assert process_time >= 0


@pytest.mark.asyncio
async def test_auth_middleware_passes_request(app):
    """Test auth middleware passes request when tenant ID is present."""
    app.add_middleware(AuthMiddleware)
    
    client = TestClient(app)
    
    response = client.get(
        "/test",
        headers={
            "X-Tenant-ID": "tenant_123",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_error_handler_exception_handling():
    """Test error handler exception handling - covers lines 157-160."""
    from fastapi import FastAPI, Request
    from unittest.mock import patch
    from src.faas.shared.middleware import error_handler
    
    app = FastAPI()
    
    @app.get("/handler_error")
    async def handler_error_endpoint(request: Request):
        raise ValueError("Test error")
    
    app.add_exception_handler(Exception, error_handler)
    
    # Mock ErrorResponse.model_dump to raise an exception
    with patch("src.faas.shared.middleware.ErrorResponse") as mock_error_response_class:
        mock_error_response = Mock()
        mock_error_response.model_dump.side_effect = RuntimeError("model_dump failed")
        mock_error_response_class.return_value = mock_error_response
        
        client = TestClient(app, raise_server_exceptions=False)
        
        response = client.get(
            "/handler_error",
            headers={
                "X-Tenant-ID": "tenant_123",
                "X-Correlation-ID": "corr_123",
                "X-Request-ID": "req_123",
            },
        )
        
        # Should return 500 with fallback error response
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
        assert "error occurred while processing the error" in data["error"]["message"]


def test_auth_middleware_function_success():
    """Test auth_middleware function with valid tenant ID - covers lines 208-214."""
    from fastapi import Request
    from src.faas.shared.middleware import auth_middleware
    
    # Create a mock request with tenant ID
    request = Request(
        scope={
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [(b"x-tenant-id", b"tenant_123")],
        }
    )
    
    tenant_id = auth_middleware(request)
    assert tenant_id == "tenant_123"


def test_auth_middleware_function_missing_tenant_id():
    """Test auth_middleware function without tenant ID - covers lines 209-212."""
    from fastapi import Request
    from src.faas.shared.exceptions import ValidationError
    from src.faas.shared.middleware import auth_middleware
    
    # Create a mock request without tenant ID
    request = Request(
        scope={
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [],
        }
    )
    
    with pytest.raises(ValidationError) as exc_info:
        auth_middleware(request)
    
    assert "X-Tenant-ID header is required" in str(exc_info.value)


@pytest.mark.asyncio
async def test_logging_middleware_decorator_success():
    """Test logging_middleware decorator success - covers lines 227-240."""
    from src.faas.shared.middleware import logging_middleware
    
    @logging_middleware
    async def test_function():
        return {"result": "success"}
    
    result = await test_function()
    assert result == {"result": "success"}


@pytest.mark.asyncio
async def test_logging_middleware_decorator_error():
    """Test logging_middleware decorator error handling - covers lines 236-238."""
    from src.faas.shared.middleware import logging_middleware
    
    @logging_middleware
    async def test_function():
        raise ValueError("Test error")
    
    with pytest.raises(ValueError, match="Test error"):
        await test_function()


@pytest.mark.asyncio
async def test_logging_middleware_decorator_with_args():
    """Test logging_middleware decorator with function arguments - covers lines 230-234."""
    from src.faas.shared.middleware import logging_middleware
    
    @logging_middleware
    async def test_function(arg1: str, arg2: int, kwarg1: str = "default"):
        return {"arg1": arg1, "arg2": arg2, "kwarg1": kwarg1}
    
    result = await test_function("test", 123, kwarg1="custom")
    assert result == {"arg1": "test", "arg2": 123, "kwarg1": "custom"}

