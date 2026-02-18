"""
OTEL Integration - High-Level Functions

Factory functions and convenience functions for OTEL operations.
"""

from typing import Dict, Optional

from .context_propagation import get_trace_context
from .otel_metrics import OTELMetrics
from .otel_tracer import OTELTracer

# ============================================================================
# Factory Functions
# ============================================================================


def create_otel_tracer(
    service_name: Optional[str] = None,
    otlp_endpoint: Optional[str] = None,
    environment: Optional[str] = None,
) -> Optional[OTELTracer]:
    """
    Create and configure an OTEL tracer with default settings.
    
    Args:
        service_name: Service name
        otlp_endpoint: OTLP exporter endpoint
        environment: Environment name
        
    Returns:
        Configured OTELTracer instance or None if OTEL is disabled
        
    Example:
        >>> tracer = create_otel_tracer(service_name="ai-sdk")
        >>> with tracer.start_trace("operation") as span:
        ...     span.set_attribute("key", "value")
    """
    try:
        from ...faas.shared.config import get_config
        
        config = get_config()
        if not getattr(config, "enable_otel", True):
            return None
        
        if service_name is None:
            service_name = getattr(config, "service_name", "ai-sdk")
        
        if otlp_endpoint is None:
            otlp_endpoint = getattr(config, "otel_exporter_otlp_endpoint", None)
        
        if environment is None:
            environment = getattr(config, "environment", "development")
        
        # Ensure service_name is not None
        final_service_name = service_name or "ai-sdk"
        return OTELTracer(final_service_name, otlp_endpoint, environment)
    except (RuntimeError, ImportError, AttributeError):
        # Config not loaded or not available, use provided values
        final_service_name = service_name or "ai-sdk"
        return OTELTracer(final_service_name, otlp_endpoint, environment)


def create_otel_metrics(
    service_name: Optional[str] = None,
    otlp_endpoint: Optional[str] = None,
    environment: Optional[str] = None,
) -> Optional[OTELMetrics]:
    """
    Create and configure OTEL metrics with default settings.
    
    Args:
        service_name: Service name
        otlp_endpoint: OTLP exporter endpoint
        environment: Environment name
        
    Returns:
        Configured OTELMetrics instance or None if OTEL is disabled
        
    Example:
        >>> metrics = create_otel_metrics(service_name="ai-sdk")
        >>> metrics.increment_counter("operation.count")
    """
    try:
        from ...faas.shared.config import get_config
        
        config = get_config()
        if not getattr(config, "enable_otel", True):
            return None
        
        if service_name is None:
            service_name = getattr(config, "service_name", "ai-sdk")
        
        if otlp_endpoint is None:
            otlp_endpoint = getattr(config, "otel_exporter_otlp_endpoint", None)
        
        if environment is None:
            environment = getattr(config, "environment", "development")
        
        # Ensure service_name is not None
        final_service_name = service_name or "ai-sdk"
        return OTELMetrics(final_service_name, otlp_endpoint, environment)
    except (RuntimeError, ImportError, AttributeError):
        # Config not loaded or not available, use provided values
        final_service_name = service_name or "ai-sdk"
        return OTELMetrics(final_service_name, otlp_endpoint, environment)


def get_current_trace_context() -> Optional[Dict[str, str]]:
    """
    Get current trace context as a dictionary.
    
    Returns:
        Dictionary containing trace context or None
        
    Example:
        >>> context = get_current_trace_context()
        >>> if context:
        ...     # Pass context to another component
        ...     result = await other_component.process(data, trace_context=context)
    """
    return get_trace_context()

