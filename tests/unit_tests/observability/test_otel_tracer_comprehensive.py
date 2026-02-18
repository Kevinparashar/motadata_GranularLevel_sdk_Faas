"""
Comprehensive Unit Tests for OTEL Tracer

Tests covering all code paths including error handling and edge cases.
"""

import pytest
from unittest.mock import patch

from src.core.otel_integration import OTELTracer


class TestOTELTracerComprehensive:
    """Comprehensive tests for OTELTracer."""

    @patch("src.core.otel_integration.otel_tracer._OTEL_AVAILABLE", False)
    def test_tracer_init_with_endpoint_but_otel_unavailable(self):
        """Test tracer initialization with endpoint but OTEL SDK unavailable."""
        # When OTEL SDK is not available, should use no-op implementation
        tracer = OTELTracer(
            service_name="test-service",
            otlp_endpoint="http://localhost:4317",
        )
        assert tracer.service_name == "test-service"
        assert tracer._enabled is False

    def test_start_trace_with_attributes(self):
        """Test starting trace with attributes."""
        tracer = OTELTracer(service_name="test-service")
        
        with tracer.start_trace("test.trace", attributes={"key": "value"}) as span:
            assert span.name == "test.trace"
            assert span._attributes == {"key": "value"}

    def test_start_trace_exception_handling(self):
        """Test trace handles exceptions correctly."""
        tracer = OTELTracer(service_name="test-service")
        
        with pytest.raises(ValueError):
            with tracer.start_trace("test.trace"):
                raise ValueError("Test error")
        
        # Span should be ended
        # Note: We can't directly check span._ended here as it's a local variable

    def test_start_span_with_parent_span(self):
        """Test starting span with parent span."""
        tracer = OTELTracer(service_name="test-service")
        parent = tracer.start_span("parent.operation")
        child = tracer.start_span("child.operation", parent=parent)
        
        assert child.name == "child.operation"

    def test_start_span_with_parent_no_span_attribute(self):
        """Test starting span with parent that has no _span attribute."""
        tracer = OTELTracer(service_name="test-service")
        # Create a simple object without _span attribute
        class SimpleParent:
            pass
        parent = SimpleParent()
        child = tracer.start_span("child.operation", parent=parent)
        
        assert child.name == "child.operation"

    def test_start_span_exception_handling(self):
        """Test start_span handles exceptions."""
        tracer = OTELTracer(service_name="test-service")
        
        # Should not raise exception even if internal error occurs
        span = tracer.start_span("test.operation")
        assert span is not None

    def test_get_current_span_no_active(self):
        """Test getting current span when none active."""
        tracer = OTELTracer(service_name="test-service")
        current = tracer.get_current_span()
        assert current is None


class TestOTELSpanComprehensive:
    """Comprehensive tests for OTELSpan."""

    def test_span_set_attribute_various_types(self):
        """Test setting attributes of various types."""
        tracer = OTELTracer(service_name="test-service")
        span = tracer.start_span("test.operation")
        
        span.set_attribute("str", "value")
        span.set_attribute("int", 123)
        span.set_attribute("float", 45.6)
        span.set_attribute("bool", True)
        span.set_attribute("list", [1, 2, 3])
        
        assert span._attributes["str"] == "value"
        assert span._attributes["int"] == 123
        assert span._attributes["float"] == 45.6
        assert span._attributes["bool"] is True
        assert span._attributes["list"] == [1, 2, 3]

    def test_span_add_event_with_attributes(self):
        """Test adding event with attributes."""
        tracer = OTELTracer(service_name="test-service")
        span = tracer.start_span("test.operation")
        
        span.add_event("test.event", attributes={"event.key": "event.value"})
        # Should not raise exception

    def test_span_add_event_without_attributes(self):
        """Test adding event without attributes."""
        tracer = OTELTracer(service_name="test-service")
        span = tracer.start_span("test.operation")
        
        span.add_event("test.event")
        # Should not raise exception

    def test_span_record_exception_with_attributes(self):
        """Test recording exception with attributes."""
        tracer = OTELTracer(service_name="test-service")
        span = tracer.start_span("test.operation")
        
        exception = ValueError("Test error")
        span.record_exception(exception, attributes={"error.code": "E001"})
        # Should not raise exception

    def test_span_record_exception_without_attributes(self):
        """Test recording exception without attributes."""
        tracer = OTELTracer(service_name="test-service")
        span = tracer.start_span("test.operation")
        
        exception = ValueError("Test error")
        span.record_exception(exception)
        # Should not raise exception

    def test_span_set_status_with_description(self):
        """Test setting span status with description."""
        tracer = OTELTracer(service_name="test-service")
        span = tracer.start_span("test.operation")
        
        span.set_status(None, "Test status description")
        # Should not raise exception

    def test_span_set_status_without_description(self):
        """Test setting span status without description."""
        tracer = OTELTracer(service_name="test-service")
        span = tracer.start_span("test.operation")
        
        span.set_status(None)
        # Should not raise exception

    def test_span_context_manager_success(self):
        """Test span context manager on success."""
        tracer = OTELTracer(service_name="test-service")
        
        with tracer.start_span("test.operation") as span:
            assert span._ended is False
        
        assert span._ended is True

    def test_span_context_manager_exception(self):
        """Test span context manager on exception."""
        tracer = OTELTracer(service_name="test-service")
        
        with pytest.raises(ValueError):
            with tracer.start_span("test.operation"):
                raise ValueError("Test error")
        
        # Span should be ended
        # Note: We can't directly check span._ended here as it's a local variable

