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
]

