"""
OTEL Tracer

OpenTelemetry tracer implementation for distributed tracing.
"""

import logging
from contextlib import contextmanager
from typing import Any, Dict, Optional

# Initialize _OTEL_AVAILABLE before try/except to avoid constant redefinition warning
_OTEL_AVAILABLE = False

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter  # type: ignore
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry.propagate import set_global_textmap
    from opentelemetry.propagators.composite import CompositeHTTPPropagator
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
    from opentelemetry.baggage.propagation import W3CBaggagePropagator

    _OTEL_AVAILABLE = True  # pyright: ignore[reportConstantRedefinition]
except ImportError:
    # Create mock classes for type hints
    trace = None
    Status = None
    StatusCode = None
    set_global_textmap = None
    CompositeHTTPPropagator = None
    TraceContextTextMapPropagator = None
    W3CBaggagePropagator = None

from .exceptions import OTELTracingError

logger = logging.getLogger(__name__)


class OTELTracer:
    """
    OpenTelemetry tracer for distributed tracing.
    
    Provides span creation, context management, and trace propagation.
    """

    def __init__(
        self,
        service_name: str,
        otlp_endpoint: Optional[str] = None,
        environment: Optional[str] = None,
        service_version: Optional[str] = None,
    ):
        """
        Initialize OTEL tracer.
        
        Args:
            service_name: Name of the service
            otlp_endpoint: OTLP exporter endpoint (optional)
            environment: Environment name (e.g., "production", "development")
            service_version: Service version (optional)
        """
        self.service_name = service_name
        self.otlp_endpoint = otlp_endpoint
        self.environment = environment or "development"
        self.service_version = service_version
        
        if _OTEL_AVAILABLE and otlp_endpoint:
            try:
                # Create resource with service version
                resource_attrs = {
                    "service.name": service_name,
                    "service.environment": self.environment,
                }
                if service_version:
                    resource_attrs["service.version"] = service_version
                resource = Resource.create(resource_attrs)
                
                # Create tracer provider
                provider = TracerProvider(resource=resource)
                
                # Create OTLP exporter
                exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
                
                # Add span processor
                provider.add_span_processor(BatchSpanProcessor(exporter))
                
                # Set global tracer provider
                trace.set_tracer_provider(provider)
                
                # Configure composite propagator (TraceContext + Baggage)
                if set_global_textmap and CompositeHTTPPropagator and TraceContextTextMapPropagator and W3CBaggagePropagator:
                    set_global_textmap(
                        CompositeHTTPPropagator([
                            TraceContextTextMapPropagator(),
                            W3CBaggagePropagator(),
                        ])
                    )
                    logger.debug("Composite propagator (TraceContext + Baggage) configured")
                
                # Get tracer
                self._tracer = trace.get_tracer(service_name)
                self._enabled = True
                logger.info(f"OTEL tracer initialized - service: {service_name}, endpoint: {otlp_endpoint}")
            except Exception as e:
                logger.warning(f"Failed to initialize OTEL tracer: {e}, using no-op implementation")
                self._tracer = None
                self._enabled = False
        else:
            if not _OTEL_AVAILABLE:
                logger.debug("OpenTelemetry SDK not available, using no-op implementation")
            self._tracer = None
            self._enabled = False

    @contextmanager
    def start_trace(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Start a new trace (root span).
        
        Args:
            name: Trace/span name
            attributes: Optional attributes to set on the span
            
        Yields:
            OTELSpan: Span context manager
        """
        span = self.start_span(name, attributes=attributes)
        try:
            yield span
        except Exception as e:
            span.record_exception(e)
            span.set_status(StatusCode.ERROR if _OTEL_AVAILABLE and StatusCode else None, str(e))
            raise
        finally:
            span.end()

    def start_span(
        self,
        name: str,
        parent: Optional[Any] = None,
        attributes: Optional[Dict[str, Any]] = None,
        kind: Optional[str] = None,
    ) -> "OTELSpan":
        """
        Start a new span.
        
        Args:
            name: Span name
            parent: Parent span (optional)
            attributes: Optional attributes to set on the span
            kind: Span kind ("server", "client", "internal", "producer", "consumer")
            
        Returns:
            OTELSpan instance
        """
        if not self._enabled or not self._tracer:
            return OTELSpan(name, attributes=attributes or {})
        
        try:
            # Determine span kind
            span_kind = trace.SpanKind.INTERNAL
            if kind and _OTEL_AVAILABLE:
                kind_map = {
                    "server": trace.SpanKind.SERVER,
                    "client": trace.SpanKind.CLIENT,
                    "internal": trace.SpanKind.INTERNAL,
                    "producer": trace.SpanKind.PRODUCER,
                    "consumer": trace.SpanKind.CONSUMER,
                }
                span_kind = kind_map.get(kind, trace.SpanKind.INTERNAL)
            
            # Get parent context if provided
            parent_context = None
            if parent and hasattr(parent, "_span") and parent._span:
                parent_context = trace.set_span_in_context(parent._span)
            
            # Start span
            if parent_context:
                span = self._tracer.start_span(name, context=parent_context, kind=span_kind)
            else:
                span = self._tracer.start_span(name, kind=span_kind)
            
            # Set attributes
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            
            return OTELSpan(name, span=span, attributes=attributes or {})
        except Exception as e:
            logger.error(f"Failed to start span '{name}': {e}")
            raise OTELTracingError(f"Failed to start span: {e}", span_name=name, original_error=e)

    def get_current_span(self) -> Optional["OTELSpan"]:
        """
        Get current active span.
        
        Returns:
            OTELSpan instance or None if no active span
        """
        if not self._enabled or not _OTEL_AVAILABLE:
            return None
        
        try:
            current_span = trace.get_current_span()
            if current_span and trace.is_recording(current_span):
                return OTELSpan(current_span.name, span=current_span)
            return None
        except Exception:
            return None


class OTELSpan:
    """
    OpenTelemetry span wrapper.
    
    Provides span operations with graceful fallback when OTEL is not available.
    """

    def __init__(
        self,
        name: str,
        span: Optional[Any] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize span.
        
        Args:
            name: Span name
            span: OpenTelemetry span object (optional)
            attributes: Span attributes dictionary
        """
        self.name = name
        self._span = span
        self._attributes = attributes or {}
        self._ended = False

    def set_attribute(self, key: str, value: Any) -> None:
        """
        Set span attribute.
        
        Args:
            key: Attribute key
            value: Attribute value
        """
        self._attributes[key] = value
        if self._span and _OTEL_AVAILABLE:
            try:
                self._span.set_attribute(key, value)
            except Exception as e:
                logger.debug(f"Failed to set span attribute '{key}': {e}")

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """
        Add event to span.
        
        Args:
            name: Event name
            attributes: Optional event attributes
        """
        if self._span and _OTEL_AVAILABLE:
            try:
                self._span.add_event(name, attributes=attributes or {})
            except Exception as e:
                logger.debug(f"Failed to add event '{name}': {e}")

    def record_exception(self, exception: Exception, attributes: Optional[Dict[str, Any]] = None) -> None:
        """
        Record exception on span.
        
        Args:
            exception: Exception to record
            attributes: Optional exception attributes
        """
        if self._span and _OTEL_AVAILABLE:
            try:
                self._span.record_exception(exception, attributes=attributes or {})
            except Exception as e:
                logger.debug(f"Failed to record exception: {e}")

    def set_status(self, status_code: Any, description: Optional[str] = None) -> None:
        """
        Set span status.
        
        Args:
            status_code: Status code (StatusCode.OK, StatusCode.ERROR)
            description: Optional status description
        """
        if self._span and _OTEL_AVAILABLE and Status:
            try:
                status = Status(status_code, description)
                self._span.set_status(status)
            except Exception as e:
                logger.debug(f"Failed to set span status: {e}")

    def end(self) -> None:
        """End span."""
        if self._ended:
            return
        
        self._ended = True
        if self._span and _OTEL_AVAILABLE:
            try:
                self._span.end()
            except Exception as e:
                logger.debug(f"Failed to end span: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type:
            self.record_exception(exc_val)
            if _OTEL_AVAILABLE and StatusCode:
                self.set_status(StatusCode.ERROR, str(exc_val))
        self.end()

