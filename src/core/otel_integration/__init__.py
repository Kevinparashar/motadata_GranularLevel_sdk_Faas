"""
OTEL Integration Module

Provides OpenTelemetry observability (distributed tracing, metrics, logging)
for comprehensive monitoring and debugging across AI SDK components.
"""

from .exceptions import (
    OTELError,
    OTELTracingError,
    OTELMetricsError,
    OTELContextError,
)
from .functions import (
    create_otel_tracer,
    create_otel_metrics,
    get_current_trace_context,
)
from .otel_tracer import OTELTracer
from .otel_metrics import OTELMetrics
from .context_propagation import (
    inject_trace_context,
    extract_trace_context,
    get_trace_context,
    set_baggage,
    get_baggage,
    set_tenant_context,
    get_tenant_context,
)
from .auto_instrumentation import (
    setup_fastapi_instrumentation,
    setup_httpx_instrumentation,
    setup_requests_instrumentation,
    setup_asyncpg_instrumentation,
    setup_sqlalchemy_instrumentation,
    setup_redis_instrumentation,
    setup_all_instrumentation,
    get_enabled_instrumentations,
    is_instrumentation_enabled,
)
from .tenant_middleware import (
    TenantContextMiddleware,
    create_tenant_middleware,
    extract_tenant_from_jwt,
    extract_tenant_from_subdomain,
    get_tenant_tier_from_id,
)
from .tenant_context import (
    extract_tenant_from_context,
    ensure_tenant_attributes_on_span,
    set_tenant_context_in_baggage,
    get_tenant_attributes_for_metrics,
)

__all__ = [
    # Core classes
    "OTELTracer",
    "OTELMetrics",
    # Exceptions
    "OTELError",
    "OTELTracingError",
    "OTELMetricsError",
    "OTELContextError",
    # Factory functions
    "create_otel_tracer",
    "create_otel_metrics",
    # Context propagation
    "inject_trace_context",
    "extract_trace_context",
    "get_trace_context",
    "get_current_trace_context",
    # Baggage propagation
    "set_baggage",
    "get_baggage",
    "set_tenant_context",
    "get_tenant_context",
    # Auto-instrumentation
    "setup_fastapi_instrumentation",
    "setup_httpx_instrumentation",
    "setup_requests_instrumentation",
    "setup_asyncpg_instrumentation",
    "setup_sqlalchemy_instrumentation",
    "setup_redis_instrumentation",
    "setup_all_instrumentation",
    "get_enabled_instrumentations",
    "is_instrumentation_enabled",
    # Tenant context middleware
    "TenantContextMiddleware",
    "create_tenant_middleware",
    "extract_tenant_from_jwt",
    "extract_tenant_from_subdomain",
    "get_tenant_tier_from_id",
    # Tenant context utilities
    "extract_tenant_from_context",
    "ensure_tenant_attributes_on_span",
    "set_tenant_context_in_baggage",
    "get_tenant_attributes_for_metrics",
]

