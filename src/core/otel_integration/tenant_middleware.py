"""
Tenant Context Middleware

FastAPI middleware for automatic tenant extraction and context injection.
Extracts tenant_id from JWT tokens or subdomain and injects into OTEL context.
"""

import logging
from typing import TYPE_CHECKING, Any, Callable, Optional

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from fastapi import Request, Response
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.types import ASGIApp
else:
    # Runtime imports
    try:
        from fastapi import Request, Response
        from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.types import ASGIApp
        _fastapi_available = True
    except ImportError:
        _fastapi_available = False
        # Type stubs for when FastAPI is not available
        Request = Any
        Response = Any
        ASGIApp = Any
        BaseHTTPMiddleware = object

# Export FASTAPI_AVAILABLE for use in tests and other modules
FASTAPI_AVAILABLE = _fastapi_available if not TYPE_CHECKING else True


def extract_tenant_from_jwt(token: Optional[str]) -> Optional[str]:
    """
    Extract tenant_id from JWT token.
    
    Args:
        token: JWT token string (without "Bearer " prefix)
        
    Returns:
        Tenant ID if found, None otherwise
        
    Example:
        >>> extract_tenant_from_jwt("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
        'abc-123'
    """
    if not token:
        return None
    
    try:
        import base64
        import json
        
        # Decode JWT payload (without verification for extraction)
        parts = token.split(".")
        if len(parts) < 2:
            return None
        
        # Decode payload
        payload_b64 = parts[1]
        # Add padding if needed
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_bytes)
        
        # Try common tenant claim names
        tenant_id = (
            payload.get("tenant_id") or
            payload.get("tenantId") or
            payload.get("tenant") or
            payload.get("tid") or
            payload.get("sub")  # Subject can sometimes be tenant-scoped
        )
        
        return str(tenant_id) if tenant_id else None
    except Exception as e:
        logger.debug(f"Failed to extract tenant from JWT: {e}")
        return None


def extract_tenant_from_subdomain(host: Optional[str], base_domain: Optional[str] = None) -> Optional[str]:
    """
    Extract tenant_id from subdomain.
    
    Args:
        host: Host header value (e.g., "abc.example.com")
        base_domain: Base domain (e.g., "example.com"). If None, extracts first subdomain.
        
    Returns:
        Tenant ID if found, None otherwise
        
    Example:
        >>> extract_tenant_from_subdomain("abc.example.com", "example.com")
        'abc'
        >>> extract_tenant_from_subdomain("tenant-123.api.example.com", "api.example.com")
        'tenant-123'
    """
    if not host:
        return None
    
    try:
        # Remove port if present
        host = host.split(":")[0]
        
        if base_domain:
            # Extract subdomain before base domain
            if host.endswith(base_domain):
                subdomain = host[: -len(base_domain)].rstrip(".")
                return subdomain if subdomain else None
        else:
            # Extract first subdomain
            parts = host.split(".")
            if len(parts) > 1:
                return parts[0] if parts[0] else None
        
        return None
    except Exception:
        return None


def get_tenant_tier_from_id(tenant_id: Optional[str]) -> Optional[str]:
    """
    Get tenant tier from tenant ID.
    
    Uses tenant_utils.get_tenant_tier to look up tier.
    
    Args:
        tenant_id: Tenant identifier
        
    Returns:
        Tenant tier ("basic", "standard", "premium") or None
    """
    if not tenant_id:
        return None
    
    try:
        from ..utils.tenant_utils import get_tenant_tier
        return get_tenant_tier(tenant_id)
    except Exception:
        return None


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatic tenant context extraction and injection.
    
    Extracts tenant_id from:
    1. JWT token (Authorization header)
    2. Subdomain (Host header)
    
    Injects tenant context into:
    1. OpenTelemetry baggage
    2. OpenTelemetry span attributes
    3. Request state (for application use)
    
    Example:
        >>> from fastapi import FastAPI
        >>> from src.core.otel_integration.tenant_middleware import TenantContextMiddleware
        >>> app = FastAPI()
        >>> app.add_middleware(TenantContextMiddleware, base_domain="example.com")
    """
    
    def __init__(
        self,
        app: ASGIApp,
        base_domain: Optional[str] = None,
        jwt_header: str = "Authorization",
        jwt_prefix: str = "Bearer ",
        enable_otel: bool = True,
    ):
        """
        Initialize tenant context middleware.
        
        Args:
            app: ASGI application
            base_domain: Base domain for subdomain extraction (e.g., "example.com")
            jwt_header: HTTP header name for JWT token (default: "Authorization")
            jwt_prefix: Prefix to strip from JWT header value (default: "Bearer ")
            enable_otel: Whether to inject tenant context into OTEL (default: True)
        """
        if not FASTAPI_AVAILABLE:
            raise ImportError(
                "FastAPI is required for TenantContextMiddleware. "
                "Install with: pip install fastapi"
            )
        
        super().__init__(app)
        self.base_domain = base_domain
        self.jwt_header = jwt_header.lower()
        self.jwt_prefix = jwt_prefix
        self.enable_otel = enable_otel
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and inject tenant context.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain
            
        Returns:
            FastAPI response object
        """
        tenant_id: Optional[str] = None
        tenant_tier: Optional[str] = None
        
        # Try JWT extraction first
        auth_header = request.headers.get(self.jwt_header)
        if auth_header and auth_header.startswith(self.jwt_prefix):
            token = auth_header[len(self.jwt_prefix):].strip()
            tenant_id = extract_tenant_from_jwt(token)
        
        # Fallback to subdomain extraction
        if not tenant_id:
            host = request.headers.get("host") or request.headers.get("Host")
            if host:
                tenant_id = extract_tenant_from_subdomain(host, self.base_domain)
        
        # Get tenant tier if tenant_id found
        if tenant_id:
            tenant_tier = get_tenant_tier_from_id(tenant_id)
        
        # Store in request state for application use
        request.state.tenant_id = tenant_id
        request.state.tenant_tier = tenant_tier
        
        # Inject into OTEL context if enabled
        if self.enable_otel and tenant_id:
            try:
                from ..otel_integration.context_propagation import set_tenant_context
                from opentelemetry import trace
                
                # Set in baggage for propagation
                set_tenant_context(tenant_id, tenant_tier)
                
                # Add to current span if available
                span = trace.get_current_span()
                if span and span.is_recording():
                    span.set_attribute("tenant.id", tenant_id)
                    if tenant_tier:
                        span.set_attribute("tenant.tier", tenant_tier)
            except Exception as e:
                logger.debug(f"Failed to inject tenant context into OTEL: {e}")
        
        # Process request
        response = await call_next(request)
        
        # Optionally add tenant headers to response (for debugging)
        if tenant_id:
            response.headers["X-Tenant-ID"] = tenant_id
            if tenant_tier:
                response.headers["X-Tenant-Tier"] = tenant_tier
        
        return response


def create_tenant_middleware(
    base_domain: Optional[str] = None,
    jwt_header: str = "Authorization",
    jwt_prefix: str = "Bearer ",
    enable_otel: bool = True,
) -> type[TenantContextMiddleware]:
    """
    Factory function to create TenantContextMiddleware class with custom configuration.
    
    Args:
        base_domain: Base domain for subdomain extraction
        jwt_header: HTTP header name for JWT token
        jwt_prefix: Prefix to strip from JWT header value
        enable_otel: Whether to inject tenant context into OTEL
        
    Returns:
        Configured TenantContextMiddleware class
        
    Example:
        >>> TenantMiddleware = create_tenant_middleware(base_domain="example.com")
        >>> app.add_middleware(TenantMiddleware)
    """
    class ConfiguredTenantContextMiddleware(TenantContextMiddleware):
        def __init__(self, app: ASGIApp):
            super().__init__(
                app=app,
                base_domain=base_domain,
                jwt_header=jwt_header,
                jwt_prefix=jwt_prefix,
                enable_otel=enable_otel,
            )
    
    return ConfiguredTenantContextMiddleware

