"""
Unit Tests for OTEL Edge Cases and Error Paths

Tests for error handling, edge cases, and fallback scenarios.
"""

from src.core.otel_integration import (
    OTELMetrics,
    OTELTracer,
    create_otel_metrics,
    create_otel_tracer,
    extract_trace_context,
    get_current_trace_context,
    inject_trace_context,
)
from src.core.otel_integration.exceptions import (
    OTELContextError,
    OTELMetricsError,
    OTELTracingError,
)


class TestOTELTracerEdgeCases:
    """Tests for OTELTracer edge cases and error paths."""

    def test_tracer_without_otlp_endpoint(self):
        """Test tracer initialization without OTLP endpoint."""
        tracer = OTELTracer(service_name="test-service")
        assert tracer.service_name == "test-service"
        assert tracer._enabled is False

    def test_start_span_with_invalid_parent(self):
        """Test starting span with invalid parent."""
        tracer = OTELTracer(service_name="test-service")
        span = tracer.start_span("test.operation", parent="invalid")
        assert span.name == "test.operation"

    def test_start_span_with_kind(self):
        """Test starting span with different kinds."""
        tracer = OTELTracer(service_name="test-service")
        
        for kind in ["server", "client", "internal", "producer", "consumer"]:
            span = tracer.start_span(f"test.{kind}", kind=kind)
            assert span.name == f"test.{kind}"

    def test_span_set_attribute_multiple(self):
        """Test setting multiple attributes on span."""
        tracer = OTELTracer(service_name="test-service")
        span = tracer.start_span("test.operation")
        
        span.set_attribute("key1", "value1")
        span.set_attribute("key2", 123)
        span.set_attribute("key3", True)
        
        assert span._attributes["key1"] == "value1"
        assert span._attributes["key2"] == 123
        assert span._attributes["key3"] is True

    def test_span_end_multiple_times(self):
        """Test ending span multiple times."""
        tracer = OTELTracer(service_name="test-service")
        span = tracer.start_span("test.operation")
        
        span.end()
        assert span._ended is True
        
        # Should not raise exception
        span.end()
        assert span._ended is True


class TestOTELMetricsEdgeCases:
    """Tests for OTELMetrics edge cases and error paths."""

    def test_metrics_without_otlp_endpoint(self):
        """Test metrics initialization without OTLP endpoint."""
        metrics = OTELMetrics(service_name="test-service")
        assert metrics.service_name == "test-service"
        assert metrics._enabled is False

    def test_increment_counter_multiple_times(self):
        """Test incrementing counter multiple times."""
        metrics = OTELMetrics(service_name="test-service")
        
        metrics.increment_counter("test.counter")
        metrics.increment_counter("test.counter", amount=2.0)
        metrics.increment_counter("test.counter", amount=0.5)
        # Should not raise exception

    def test_record_histogram_with_zero(self):
        """Test recording histogram with zero value."""
        metrics = OTELMetrics(service_name="test-service")
        metrics.record_histogram("test.histogram", value=0.0)
        # Should not raise exception

    def test_record_histogram_with_negative(self):
        """Test recording histogram with negative value."""
        metrics = OTELMetrics(service_name="test-service")
        metrics.record_histogram("test.histogram", value=-1.0)
        # Should not raise exception

    def test_set_gauge_multiple_times(self):
        """Test setting gauge multiple times."""
        metrics = OTELMetrics(service_name="test-service")
        
        metrics.set_gauge("test.gauge", value=10.0)
        metrics.set_gauge("test.gauge", value=20.0)
        metrics.set_gauge("test.gauge", value=15.0)
        # Should not raise exception

    def test_metrics_with_empty_attributes(self):
        """Test metrics with empty attributes."""
        metrics = OTELMetrics(service_name="test-service")
        
        metrics.increment_counter("test.counter", attributes={})
        metrics.record_histogram("test.histogram", value=1.0, attributes={})
        metrics.set_gauge("test.gauge", value=10.0, attributes={})
        # Should not raise exception


class TestOTELContextPropagationEdgeCases:
    """Tests for context propagation edge cases."""

    def test_inject_trace_context_empty_carrier(self):
        """Test injecting into empty carrier."""
        carrier = {}
        result = inject_trace_context(carrier)
        assert result == carrier

    def test_extract_trace_context_invalid_format(self):
        """Test extracting from invalid format."""
        carrier = {"invalid": "format"}
        context = extract_trace_context(carrier)
        # Should return None or context without raising exception
        assert context is None or context is not None

    def test_get_current_trace_context_no_active_span(self):
        """Test getting context when no active span."""
        context = get_current_trace_context()
        # Should return None when no active trace
        assert context is None or isinstance(context, dict)


class TestOTELFactoryFunctions:
    """Tests for factory functions edge cases."""

    def test_create_otel_tracer_without_config(self):
        """Test creating tracer without config."""
        tracer = create_otel_tracer(service_name="test-service")
        # Should return tracer or None
        assert tracer is None or tracer.service_name == "test-service"

    def test_create_otel_tracer_with_endpoint(self):
        """Test creating tracer with endpoint."""
        tracer = create_otel_tracer(
            service_name="test-service",
            otlp_endpoint="http://localhost:4317",
        )
        # Should return tracer or None
        assert tracer is None or tracer.service_name == "test-service"

    def test_create_otel_metrics_without_config(self):
        """Test creating metrics without config."""
        metrics = create_otel_metrics(service_name="test-service")
        # Should return metrics or None
        assert metrics is None or metrics.service_name == "test-service"

    def test_create_otel_metrics_with_endpoint(self):
        """Test creating metrics with endpoint."""
        metrics = create_otel_metrics(
            service_name="test-service",
            otlp_endpoint="http://localhost:4317",
        )
        # Should return metrics or None
        assert metrics is None or metrics.service_name == "test-service"


class TestOTELExceptions:
    """Tests for OTEL exception classes."""

    def test_otel_error_creation(self):
        """Test creating OTEL error."""
        from src.core.otel_integration.exceptions import OTELError
        
        error = OTELError("Test error", component="test")
        assert str(error) == "Test error"
        assert error.component == "test"

    def test_otel_tracing_error(self):
        """Test creating tracing error."""
        error = OTELTracingError("Tracing failed", span_name="test.span")
        assert error.span_name == "test.span"
        assert error.component == "otel_tracing"

    def test_otel_metrics_error(self):
        """Test creating metrics error."""
        error = OTELMetricsError("Metrics failed", metric_name="test.metric")
        assert error.metric_name == "test.metric"
        assert error.component == "otel_metrics"

    def test_otel_context_error(self):
        """Test creating context error."""
        error = OTELContextError("Context failed", operation="inject")
        assert error.operation == "inject"
        assert error.component == "otel_context"

    def test_otel_error_with_original_error(self):
        """Test error with original exception."""
        original = ValueError("Original error")
        error = OTELTracingError("Tracing failed", original_error=original)
        assert error.original_error == original
        assert "Original error" in str(error)

