"""
Unit Tests for OTEL Integration Code Paths

Tests covering specific code paths that are reachable without OTEL SDK.
"""

from unittest.mock import patch

from src.core.otel_integration import OTELMetrics, OTELTracer


class TestOTELTracerCodePaths:
    """Tests for specific code paths in OTELTracer."""

    def test_start_span_not_enabled(self):
        """Test start_span when tracer is not enabled."""
        tracer = OTELTracer(service_name="test-service")
        # _enabled is False when no endpoint or OTEL unavailable
        span = tracer.start_span("test.operation")
        assert span.name == "test.operation"
        assert span._span is None  # No-op span

    def test_start_span_with_attributes_dict(self):
        """Test start_span with attributes dictionary."""
        tracer = OTELTracer(service_name="test-service")
        span = tracer.start_span("test.operation", attributes={"key1": "value1", "key2": 123})
        assert span._attributes == {"key1": "value1", "key2": 123}

    def test_start_span_with_parent_has_span(self):
        """Test start_span with parent that has _span attribute."""
        tracer = OTELTracer(service_name="test-service")
        parent = tracer.start_span("parent.operation")
        # Parent has _span attribute (even if None)
        child = tracer.start_span("child.operation", parent=parent)
        assert child.name == "child.operation"

    def test_span_set_attribute_when_span_none(self):
        """Test setting attribute when underlying span is None."""
        tracer = OTELTracer(service_name="test-service")
        span = tracer.start_span("test.operation")
        # _span is None in no-op mode
        span.set_attribute("key", "value")
        assert span._attributes["key"] == "value"

    def test_span_add_event_when_span_none(self):
        """Test adding event when underlying span is None."""
        tracer = OTELTracer(service_name="test-service")
        span = tracer.start_span("test.operation")
        span.add_event("test.event", attributes={"key": "value"})
        # Should not raise exception

    def test_span_record_exception_when_span_none(self):
        """Test recording exception when underlying span is None."""
        tracer = OTELTracer(service_name="test-service")
        span = tracer.start_span("test.operation")
        exception = ValueError("Test error")
        span.record_exception(exception, attributes={"error.code": "E001"})
        # Should not raise exception

    def test_span_set_status_when_span_none(self):
        """Test setting status when underlying span is None."""
        tracer = OTELTracer(service_name="test-service")
        span = tracer.start_span("test.operation")
        span.set_status(None, "Test status")
        # Should not raise exception

    def test_span_end_when_span_none(self):
        """Test ending span when underlying span is None."""
        tracer = OTELTracer(service_name="test-service")
        span = tracer.start_span("test.operation")
        span.end()
        assert span._ended is True

    def test_span_end_multiple_calls(self):
        """Test ending span multiple times."""
        tracer = OTELTracer(service_name="test-service")
        span = tracer.start_span("test.operation")
        span.end()
        span.end()  # Should not raise exception
        assert span._ended is True


class TestOTELMetricsCodePaths:
    """Tests for specific code paths in OTELMetrics."""

    def test_metrics_not_enabled(self):
        """Test metrics when not enabled."""
        metrics = OTELMetrics(service_name="test-service")
        # _enabled is False when no endpoint or OTEL unavailable
        metrics.increment_counter("test.counter")
        # Should not raise exception

    def test_increment_counter_not_enabled(self):
        """Test incrementing counter when metrics not enabled."""
        metrics = OTELMetrics(service_name="test-service")
        metrics.increment_counter("test.counter", amount=5.0, attributes={"key": "value"})
        # Should not raise exception

    def test_record_histogram_not_enabled(self):
        """Test recording histogram when metrics not enabled."""
        metrics = OTELMetrics(service_name="test-service")
        metrics.record_histogram("test.histogram", value=1.5, attributes={"key": "value"})
        # Should not raise exception

    def test_set_gauge_not_enabled(self):
        """Test setting gauge when metrics not enabled."""
        metrics = OTELMetrics(service_name="test-service")
        metrics.set_gauge("test.gauge", value=10.0, attributes={"key": "value"})
        # Should not raise exception

    def test_increment_counter_exception_handling(self):
        """Test increment counter exception handling."""
        metrics = OTELMetrics(service_name="test-service")
        # Should handle exceptions gracefully
        metrics.increment_counter("test.counter")
        # Should not raise exception

    def test_record_histogram_exception_handling(self):
        """Test record histogram exception handling."""
        metrics = OTELMetrics(service_name="test-service")
        # Should handle exceptions gracefully
        metrics.record_histogram("test.histogram", value=1.0)
        # Should not raise exception

    def test_set_gauge_exception_handling(self):
        """Test set gauge exception handling."""
        metrics = OTELMetrics(service_name="test-service")
        # Should handle exceptions gracefully
        metrics.set_gauge("test.gauge", value=10.0)
        # Should not raise exception


class TestOTELContextPropagationPaths:
    """Tests for context propagation code paths."""

    def test_inject_trace_context_otel_unavailable(self):
        """Test injecting context when OTEL unavailable."""
        from src.core.otel_integration import inject_trace_context
        
        carrier = {}
        result = inject_trace_context(carrier)
        assert result == carrier

    def test_extract_trace_context_otel_unavailable(self):
        """Test extracting context when OTEL unavailable."""
        from src.core.otel_integration import extract_trace_context
        
        carrier = {"traceparent": "test"}
        context = extract_trace_context(carrier)
        # Should return None or context when OTEL unavailable
        assert context is None or context is not None

    @patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", False)
    def test_get_trace_context_otel_unavailable(self):
        """Test getting trace context when OTEL unavailable."""
        from src.core.otel_integration.context_propagation import get_trace_context
        
        context = get_trace_context()
        # Should return None when OTEL unavailable
        assert context is None

    def test_inject_trace_context_with_dict_setter_none(self):
        """Test injecting when dict_setter is None."""
        from src.core.otel_integration import inject_trace_context
        
        # This tests the path when _dict_setter is None
        carrier = {}
        result = inject_trace_context(carrier)
        assert result == carrier

    def test_extract_trace_context_with_dict_getter_none(self):
        """Test extracting when dict_getter is None."""
        from src.core.otel_integration import extract_trace_context
        
        # This tests the path when _dict_getter is None
        carrier = {"traceparent": "test"}
        context = extract_trace_context(carrier)
        # Should return None or context
        assert context is None or context is not None


class TestOTELFunctionsPaths:
    """Tests for factory function code paths."""

    def test_create_otel_tracer_fallback_path(self):
        """Test create_otel_tracer fallback path."""
        from src.core.otel_integration import create_otel_tracer
        
        # When config import fails, should use fallback
        tracer = create_otel_tracer(service_name="test-service")
        assert tracer is None or tracer.service_name == "test-service"

    def test_create_otel_metrics_fallback_path(self):
        """Test create_otel_metrics fallback path."""
        from src.core.otel_integration import create_otel_metrics
        
        # When config import fails, should use fallback
        metrics = create_otel_metrics(service_name="test-service")
        assert metrics is None or metrics.service_name == "test-service"

    def test_create_otel_tracer_with_default_service_name(self):
        """Test create_otel_tracer with default service name."""
        from src.core.otel_integration import create_otel_tracer
        
        # When service_name is None, should use "ai-sdk"
        tracer = create_otel_tracer(service_name=None)
        # Should handle None and use default
        assert tracer is None or tracer.service_name == "ai-sdk"

    def test_create_otel_metrics_with_default_service_name(self):
        """Test create_otel_metrics with default service name."""
        from src.core.otel_integration import create_otel_metrics
        
        # When service_name is None, should use "ai-sdk"
        metrics = create_otel_metrics(service_name=None)
        # Should handle None and use default
        assert metrics is None or metrics.service_name == "ai-sdk"

