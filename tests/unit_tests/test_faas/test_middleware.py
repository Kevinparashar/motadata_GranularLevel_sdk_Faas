"""
Unit tests for FaaS Middleware.
"""


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
    
    client = TestClient(app)
    
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
    
    client = TestClient(app)
    
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
    
    client = TestClient(app)
    
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

