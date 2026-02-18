"""
Unit Tests for OTEL Tracer

Tests for OpenTelemetry tracer functionality.
"""

import pytest

from src.core.otel_integration import OTELTracer, create_otel_tracer


class TestOTELTracer:
    """Tests for OTELTracer class."""

    def test_init_with_service_name(self):
        """Test OTELTracer initialization with service name."""
        tracer = OTELTracer(service_name="test-service")
        
        assert tracer.service_name == "test-service"
        assert tracer.otlp_endpoint is None
        assert tracer.environment == "development"

    def test_init_with_endpoint(self):
        """Test OTELTracer initialization with endpoint."""
        tracer = OTELTracer(
            service_name="test-service",
            otlp_endpoint="http://localhost:4317",
        )
        
        assert tracer.service_name == "test-service"
        assert tracer.otlp_endpoint == "http://localhost:4317"

    def test_init_with_environment(self):
        """Test OTELTracer initialization with environment."""
        tracer = OTELTracer(
            service_name="test-service",
            environment="production",
        )
        
        assert tracer.environment == "production"

    def test_start_span(self):
        """Test starting a span."""
        tracer = OTELTracer(service_name="test-service")
        span = tracer.start_span("test.operation")
        
        assert span.name == "test.operation"
        assert span._attributes == {}

    def test_start_span_with_attributes(self):
        """Test starting a span with attributes."""
        tracer = OTELTracer(service_name="test-service")
        span = tracer.start_span("test.operation", attributes={"key": "value"})
        
        assert span.name == "test.operation"
        assert span._attributes == {"key": "value"}

    def test_start_span_with_parent(self):
        """Test starting a span with parent."""
        tracer = OTELTracer(service_name="test-service")
        parent_span = tracer.start_span("parent.operation")
        child_span = tracer.start_span("child.operation", parent=parent_span)
        
        assert child_span.name == "child.operation"

    def test_start_trace(self):
        """Test starting a trace (root span)."""
        tracer = OTELTracer(service_name="test-service")
        
        with tracer.start_trace("test.trace") as span:
            assert span.name == "test.trace"
            span.set_attribute("key", "value")
        
        assert span._ended is True

    def test_start_trace_with_exception(self):
        """Test trace handles exceptions correctly."""
        tracer = OTELTracer(service_name="test-service")
        
        with pytest.raises(ValueError):
            with tracer.start_trace("test.trace") as span:
                raise ValueError("Test error")
        
        assert span._ended is True

    def test_get_current_span(self):
        """Test getting current span."""
        tracer = OTELTracer(service_name="test-service")
        
        # When no active span, should return None
        current = tracer.get_current_span()
        assert current is None


class TestOTELSpan:
    """Tests for OTELSpan class."""

    def test_span_set_attribute(self):
        """Test setting span attribute."""
        tracer = OTELTracer(service_name="test-service")
        span = tracer.start_span("test.operation")
        
        span.set_attribute("key", "value")
        assert span._attributes["key"] == "value"

    def test_span_add_event(self):
        """Test adding event to span."""
        tracer = OTELTracer(service_name="test-service")
        span = tracer.start_span("test.operation")
        
        span.add_event("test.event", attributes={"event.key": "event.value"})
        # Should not raise exception

    def test_span_record_exception(self):
        """Test recording exception on span."""
        tracer = OTELTracer(service_name="test-service")
        span = tracer.start_span("test.operation")
        
        exception = ValueError("Test error")
        span.record_exception(exception)
        # Should not raise exception

    def test_span_set_status(self):
        """Test setting span status."""
        tracer = OTELTracer(service_name="test-service")
        span = tracer.start_span("test.operation")
        
        span.set_status(None, "Test status")
        # Should not raise exception

    def test_span_context_manager(self):
        """Test span as context manager."""
        tracer = OTELTracer(service_name="test-service")
        
        with tracer.start_span("test.operation") as span:
            assert span._ended is False
        
        assert span._ended is True

    def test_span_context_manager_with_exception(self):
        """Test span context manager handles exceptions."""
        tracer = OTELTracer(service_name="test-service")
        
        with pytest.raises(ValueError):
            with tracer.start_span("test.operation") as span:
                raise ValueError("Test error")
        
        assert span._ended is True


class TestCreateOTELTracer:
    """Tests for create_otel_tracer factory function."""

    def test_create_otel_tracer_with_service_name(self):
        """Test creating tracer with service name."""
        tracer = create_otel_tracer(service_name="test-service")
        
        assert tracer is not None
        assert tracer.service_name == "test-service"

    def test_create_otel_tracer_without_params(self):
        """Test creating tracer without parameters."""
        tracer = create_otel_tracer()
        
        # Should return None if config not available and no service_name provided
        # or return default tracer
        if tracer:
            assert tracer.service_name is not None

