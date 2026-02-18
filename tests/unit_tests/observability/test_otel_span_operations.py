"""
Unit Tests for OTEL Span Operations

Tests covering span operations and edge cases.
"""

import pytest
from unittest.mock import Mock

from src.core.otel_integration import OTELTracer


class TestOTELSpanOperations:
    """Tests for span operations."""

    def test_span_set_attribute_error_handling(self):
        """Test span set_attribute error handling."""
        tracer = OTELTracer(service_name="test-service")
        span = tracer.start_span("test.operation")
        
        # Set attribute - should work even if underlying span fails
        span.set_attribute("key", "value")
        assert span._attributes["key"] == "value"

    def test_span_add_event_error_handling(self):
        """Test span add_event error handling."""
        tracer = OTELTracer(service_name="test-service")
        span = tracer.start_span("test.operation")
        
        # Add event - should not raise exception even if underlying span fails
        span.add_event("test.event", attributes={"key": "value"})
        span.add_event("test.event2")  # Without attributes

    def test_span_record_exception_error_handling(self):
        """Test span record_exception error handling."""
        tracer = OTELTracer(service_name="test-service")
        span = tracer.start_span("test.operation")
        
        # Record exception - should not raise exception
        exception = ValueError("Test error")
        span.record_exception(exception)
        span.record_exception(exception, attributes={"error.code": "E001"})

    def test_span_set_status_error_handling(self):
        """Test span set_status error handling."""
        tracer = OTELTracer(service_name="test-service")
        span = tracer.start_span("test.operation")
        
        # Set status - should not raise exception
        span.set_status(None)
        span.set_status(None, "Description")

    def test_span_end_error_handling(self):
        """Test span end error handling."""
        tracer = OTELTracer(service_name="test-service")
        span = tracer.start_span("test.operation")
        
        # End span - should not raise exception
        span.end()
        span.end()  # Multiple calls should be safe

    def test_span_context_manager_no_exception(self):
        """Test span context manager without exception."""
        tracer = OTELTracer(service_name="test-service")
        
        with tracer.start_span("test.operation") as span:
            assert span._ended is False
        
        assert span._ended is True

    def test_span_context_manager_with_exception(self):
        """Test span context manager with exception."""
        tracer = OTELTracer(service_name="test-service")
        
        with pytest.raises(ValueError):
            with tracer.start_span("test.operation"):
                raise ValueError("Test error")
        
        # Span should be ended

    def test_start_span_exception_raises_tracing_error(self):
        """Test start_span raises OTELTracingError on exception."""
        from src.core.otel_integration.exceptions import OTELTracingError
        
        tracer = OTELTracer(service_name="test-service")
        tracer._enabled = True
        tracer._tracer = Mock()
        tracer._tracer.start_span.side_effect = Exception("Span creation failed")
        
        # Should raise OTELTracingError
        with pytest.raises(OTELTracingError):
            tracer.start_span("test.operation")

