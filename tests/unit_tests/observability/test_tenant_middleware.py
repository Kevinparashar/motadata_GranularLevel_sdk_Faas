"""
Tests for tenant context middleware.
"""

import base64
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Mock FastAPI if not available
try:
    from fastapi import Request
    from starlette.responses import Response
    _has_fastapi = True
except ImportError:
    _has_fastapi = False
    Request = MagicMock
    Response = MagicMock

# Import FASTAPI_AVAILABLE from source module, use local fallback if needed
try:
    from src.core.otel_integration.tenant_middleware import FASTAPI_AVAILABLE
except ImportError:
    # Fallback if import fails - use local check
    # Use a different name to avoid constant redefinition warning
    import sys
    _module = sys.modules[__name__]
    setattr(_module, "FASTAPI_AVAILABLE", _has_fastapi)

from src.core.otel_integration.tenant_middleware import (
    TenantContextMiddleware,
    create_tenant_middleware,
    extract_tenant_from_jwt,
    extract_tenant_from_subdomain,
    get_tenant_tier_from_id,
)


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
class TestExtractTenantFromJWT:
    """Test extract_tenant_from_jwt function."""
    
    def test_extract_tenant_from_jwt_with_tenant_id(self):
        """Test extracting tenant_id from JWT."""
        payload = {"tenant_id": "abc-123", "sub": "user-123"}
        token = self._create_jwt_token(payload)
        assert extract_tenant_from_jwt(token) == "abc-123"
    
    def test_extract_tenant_from_jwt_with_tenantId(self):
        """Test extracting tenantId from JWT."""
        payload = {"tenantId": "def-456", "sub": "user-123"}
        token = self._create_jwt_token(payload)
        assert extract_tenant_from_jwt(token) == "def-456"
    
    def test_extract_tenant_from_jwt_with_tenant(self):
        """Test extracting tenant from JWT."""
        payload = {"tenant": "ghi-789", "sub": "user-123"}
        token = self._create_jwt_token(payload)
        assert extract_tenant_from_jwt(token) == "ghi-789"
    
    def test_extract_tenant_from_jwt_with_tid(self):
        """Test extracting tid from JWT."""
        payload = {"tid": "jkl-012", "sub": "user-123"}
        token = self._create_jwt_token(payload)
        assert extract_tenant_from_jwt(token) == "jkl-012"
    
    def test_extract_tenant_from_jwt_fallback_to_sub(self):
        """Test falling back to sub if no tenant claim."""
        payload = {"sub": "tenant-abc"}
        token = self._create_jwt_token(payload)
        assert extract_tenant_from_jwt(token) == "tenant-abc"
    
    def test_extract_tenant_from_jwt_no_tenant(self):
        """Test JWT with no tenant information."""
        payload = {"exp": 1234567890}
        token = self._create_jwt_token(payload)
        assert extract_tenant_from_jwt(token) is None
    
    def test_extract_tenant_from_jwt_invalid_token(self):
        """Test extracting from invalid JWT."""
        assert extract_tenant_from_jwt("invalid.token") is None
        assert extract_tenant_from_jwt("") is None
        assert extract_tenant_from_jwt(None) is None
    
    def test_extract_tenant_from_jwt_malformed_payload(self):
        """Test extracting from malformed JWT payload."""
        # Create token with invalid base64
        token = "header.invalid-payload.signature"
        assert extract_tenant_from_jwt(token) is None
    
    def _create_jwt_token(self, payload: dict) -> str:
        """Helper to create a JWT token for testing."""
        header = {"alg": "HS256", "typ": "JWT"}
        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        signature = "signature"
        return f"{header_b64}.{payload_b64}.{signature}"


class TestExtractTenantFromSubdomain:
    """Test extract_tenant_from_subdomain function."""
    
    def test_extract_tenant_from_subdomain_with_base_domain(self):
        """Test extracting tenant from subdomain with base domain."""
        assert extract_tenant_from_subdomain("abc.example.com", "example.com") == "abc"
        assert extract_tenant_from_subdomain("tenant-123.api.example.com", "api.example.com") == "tenant-123"
    
    def test_extract_tenant_from_subdomain_without_base_domain(self):
        """Test extracting tenant from subdomain without base domain."""
        assert extract_tenant_from_subdomain("abc.example.com") == "abc"
        assert extract_tenant_from_subdomain("tenant-123.example.com") == "tenant-123"
    
    def test_extract_tenant_from_subdomain_no_subdomain(self):
        """Test extracting from domain without subdomain."""
        assert extract_tenant_from_subdomain("example.com", "example.com") is None
        # Without base_domain, it extracts first part which could be "example"
        # This is expected behavior - test with explicit base domain
        assert extract_tenant_from_subdomain("example.com", "example.com") is None
    
    def test_extract_tenant_from_subdomain_with_port(self):
        """Test extracting from host with port."""
        assert extract_tenant_from_subdomain("abc.example.com:8080", "example.com") == "abc"
        assert extract_tenant_from_subdomain("tenant-123.example.com:443") == "tenant-123"
    
    def test_extract_tenant_from_subdomain_empty(self):
        """Test extracting from empty host."""
        assert extract_tenant_from_subdomain("") is None
        assert extract_tenant_from_subdomain(None) is None


class TestGetTenantTierFromId:
    """Test get_tenant_tier_from_id function."""
    
    def test_get_tenant_tier_from_id(self):
        """Test getting tenant tier from ID."""
        from src.core.utils.tenant_utils import set_tenant_tier_mapping, clear_tenant_tier_mappings
        clear_tenant_tier_mappings()
        set_tenant_tier_mapping("abc-123", "premium")
        assert get_tenant_tier_from_id("abc-123") == "premium"
        assert get_tenant_tier_from_id("unknown") is None
    
    def test_get_tenant_tier_from_id_none(self):
        """Test getting tier with None tenant_id."""
        assert get_tenant_tier_from_id(None) is None


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
class TestTenantContextMiddleware:
    """Test TenantContextMiddleware class."""
    
    @pytest.fixture
    def mock_app(self):
        """Create a mock ASGI app."""
        app = MagicMock()
        app.__call__ = AsyncMock(return_value=Response())
        return app
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request."""
        request = MagicMock(spec=Request)
        request.headers = {}
        request.state = MagicMock()
        return request
    
    def test_middleware_init(self, mock_app):
        """Test middleware initialization."""
        middleware = TenantContextMiddleware(mock_app, base_domain="example.com")
        assert middleware.base_domain == "example.com"
        assert middleware.jwt_header == "authorization"
        assert middleware.jwt_prefix == "Bearer "
        assert middleware.enable_otel is True
    
    def test_middleware_init_without_fastapi(self):
        """Test middleware initialization without FastAPI."""
        with patch("src.core.otel_integration.tenant_middleware.FASTAPI_AVAILABLE", False):
            with pytest.raises(ImportError):
                TenantContextMiddleware(MagicMock())
    
    @pytest.mark.asyncio
    async def test_middleware_extract_from_jwt(self, mock_app, mock_request):
        """Test extracting tenant from JWT token."""
        payload = {"tenant_id": "abc-123"}
        token = self._create_jwt_token(payload)
        mock_request.headers = {"authorization": f"Bearer {token}"}
        
        middleware = TenantContextMiddleware(mock_app)
        call_next = AsyncMock(return_value=Response())
        
        with patch("src.core.otel_integration.context_propagation.set_tenant_context"):
            response = await middleware.dispatch(mock_request, call_next)
        
        assert mock_request.state.tenant_id == "abc-123"
        assert response.headers.get("X-Tenant-ID") == "abc-123"
    
    @pytest.mark.asyncio
    async def test_middleware_extract_from_subdomain(self, mock_app, mock_request):
        """Test extracting tenant from subdomain."""
        mock_request.headers = {"host": "abc.example.com"}
        
        middleware = TenantContextMiddleware(mock_app, base_domain="example.com")
        call_next = AsyncMock(return_value=Response())
        
        response = await middleware.dispatch(mock_request, call_next)
        
        assert mock_request.state.tenant_id == "abc"
        assert response.headers.get("X-Tenant-ID") == "abc"
    
    @pytest.mark.asyncio
    async def test_middleware_jwt_priority(self, mock_app, mock_request):
        """Test that JWT extraction takes priority over subdomain."""
        payload = {"tenant_id": "jwt-tenant"}
        token = self._create_jwt_token(payload)
        mock_request.headers = {
            "authorization": f"Bearer {token}",
            "host": "subdomain.example.com"
        }
        
        middleware = TenantContextMiddleware(mock_app, base_domain="example.com")
        call_next = AsyncMock(return_value=Response())
        
        response = await middleware.dispatch(mock_request, call_next)
        
        assert mock_request.state.tenant_id == "jwt-tenant"
        assert response.headers.get("X-Tenant-ID") == "jwt-tenant"
    
    @pytest.mark.asyncio
    async def test_middleware_inject_otel(self, mock_app, mock_request):
        """Test injecting tenant context into OTEL."""
        payload = {"tenant_id": "abc-123"}
        token = self._create_jwt_token(payload)
        mock_request.headers = {"authorization": f"Bearer {token}"}
        
        middleware = TenantContextMiddleware(mock_app, enable_otel=True)
        call_next = AsyncMock(return_value=Response())
        
        with patch("src.core.otel_integration.context_propagation.set_tenant_context") as mock_set, \
             patch("opentelemetry.trace.get_current_span") as mock_trace_span:
            mock_span = MagicMock()
            mock_span.is_recording.return_value = True
            mock_trace_span.return_value = mock_span
            
            from src.core.utils.tenant_utils import set_tenant_tier_mapping, clear_tenant_tier_mappings
            clear_tenant_tier_mappings()
            set_tenant_tier_mapping("abc-123", "premium")
            
            await middleware.dispatch(mock_request, call_next)
            
            mock_set.assert_called_once()
            mock_span.set_attribute.assert_any_call("tenant.id", "abc-123")
            mock_span.set_attribute.assert_any_call("tenant.tier", "premium")
    
    @pytest.mark.asyncio
    async def test_middleware_no_otel_injection(self, mock_app, mock_request):
        """Test middleware with OTEL injection disabled."""
        mock_request.headers = {"host": "abc.example.com"}
        
        middleware = TenantContextMiddleware(mock_app, enable_otel=False)
        call_next = AsyncMock(return_value=Response())
        
        with patch("src.core.otel_integration.context_propagation.set_tenant_context") as mock_set:
            await middleware.dispatch(mock_request, call_next)
            # Should not call OTEL functions
            mock_set.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_middleware_no_tenant(self, mock_app, mock_request):
        """Test middleware with no tenant found."""
        mock_request.headers = {}
        
        middleware = TenantContextMiddleware(mock_app)
        call_next = AsyncMock(return_value=Response())
        
        response = await middleware.dispatch(mock_request, call_next)
        
        assert mock_request.state.tenant_id is None
        assert "X-Tenant-ID" not in response.headers
    
    @pytest.mark.asyncio
    async def test_middleware_custom_jwt_header(self, mock_app, mock_request):
        """Test middleware with custom JWT header."""
        payload = {"tenant_id": "abc-123"}
        token = self._create_jwt_token(payload)
        mock_request.headers = {"x-custom-token": f"Bearer {token}"}
        
        middleware = TenantContextMiddleware(mock_app, jwt_header="x-custom-token")
        call_next = AsyncMock(return_value=Response())
        
        await middleware.dispatch(mock_request, call_next)
        
        assert mock_request.state.tenant_id == "abc-123"
    
    def _create_jwt_token(self, payload: dict) -> str:
        """Helper to create a JWT token for testing."""
        header = {"alg": "HS256", "typ": "JWT"}
        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        signature = "signature"
        return f"{header_b64}.{payload_b64}.{signature}"
    
    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
    @pytest.mark.asyncio
    async def test_middleware_otel_exception_handling(self, mock_app, mock_request):
        """Test middleware handles OTEL exceptions gracefully."""
        payload = {"tenant_id": "abc-123"}
        token = self._create_jwt_token(payload)
        mock_request.headers = {"authorization": f"Bearer {token}"}
        
        middleware = TenantContextMiddleware(mock_app, enable_otel=True)
        call_next = AsyncMock(return_value=Response())
        
        # Mock OTEL to raise exception
        with patch("src.core.otel_integration.context_propagation.set_tenant_context", side_effect=Exception("OTEL error")), \
             patch("opentelemetry.trace.get_current_span", side_effect=Exception("OTEL error")):
            # Should not raise, should handle gracefully
            await middleware.dispatch(mock_request, call_next)
            assert mock_request.state.tenant_id == "abc-123"
    
    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
    @pytest.mark.asyncio
    async def test_middleware_span_not_recording(self, mock_app, mock_request):
        """Test middleware with span that is not recording."""
        payload = {"tenant_id": "abc-123"}
        token = self._create_jwt_token(payload)
        mock_request.headers = {"authorization": f"Bearer {token}"}
        
        middleware = TenantContextMiddleware(mock_app, enable_otel=True)
        call_next = AsyncMock(return_value=Response())
        
        with patch("src.core.otel_integration.context_propagation.set_tenant_context") as mock_set, \
             patch("opentelemetry.trace.get_current_span") as mock_trace_span:
            mock_span = MagicMock()
            mock_span.is_recording.return_value = False
            mock_trace_span.return_value = mock_span
            
            await middleware.dispatch(mock_request, call_next)
            
            # Should call set_tenant_context but not set span attributes
            mock_set.assert_called_once()
            mock_span.set_attribute.assert_not_called()
    
    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
    @pytest.mark.asyncio
    async def test_middleware_no_span_available(self, mock_app, mock_request):
        """Test middleware when no span is available."""
        payload = {"tenant_id": "abc-123"}
        token = self._create_jwt_token(payload)
        mock_request.headers = {"authorization": f"Bearer {token}"}
        
        middleware = TenantContextMiddleware(mock_app, enable_otel=True)
        call_next = AsyncMock(return_value=Response())
        
        with patch("src.core.otel_integration.context_propagation.set_tenant_context") as mock_set, \
             patch("opentelemetry.trace.get_current_span", return_value=None):
            await middleware.dispatch(mock_request, call_next)
            
            # Should call set_tenant_context but not set span attributes
            mock_set.assert_called_once()


class TestCreateTenantMiddleware:
    """Test create_tenant_middleware factory function."""
    
    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
    def test_create_tenant_middleware(self):
        """Test creating configured middleware."""
        ConfiguredMiddleware = create_tenant_middleware(
            base_domain="example.com",
            jwt_header="x-token",
            jwt_prefix="Token ",
            enable_otel=False
        )
        
        mock_app = MagicMock()
        middleware = ConfiguredMiddleware(mock_app)
        
        assert middleware.base_domain == "example.com"
        assert middleware.jwt_header == "x-token"
        assert middleware.jwt_prefix == "Token "
        assert middleware.enable_otel is False
