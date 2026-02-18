"""
Unit Tests for OTEL Error Paths

Tests covering error handling and exception paths.
"""

import pytest
from unittest.mock import Mock, patch

from src.core.otel_integration import OTELMetrics, OTELTracer
from src.core.otel_integration.context_propagation import (
    extract_trace_context,
    get_trace_context,
    inject_trace_context,
)
from src.core.otel_integration.exceptions import OTELContextError


class TestOTELContextPropagationErrorPaths:
    """Tests for context propagation error handling."""

    def test_inject_trace_context_exception(self):
        """Test inject_trace_context raises OTELContextError on exception."""
        tracer = OTELTracer(
            service_name="test-service",
            otlp_endpoint="http://localhost:4317",
        )
        
        if tracer._enabled and tracer._tracer:
            with tracer.start_trace("test.trace"):
                # Mock inject to raise exception
                with patch("src.core.otel_integration.context_propagation.inject") as mock_inject:
                    mock_inject.side_effect = Exception("Injection failed")
                    
                    carrier = {}
                    with pytest.raises(OTELContextError):
                        inject_trace_context(carrier)

    def test_extract_trace_context_exception(self):
        """Test extract_trace_context raises OTELContextError on exception."""
        tracer = OTELTracer(
            service_name="test-service",
            otlp_endpoint="http://localhost:4317",
        )
        
        if tracer._enabled and tracer._tracer:
            with tracer.start_trace("test.trace"):
                # Inject context first
                carrier = {}
                inject_trace_context(carrier)
                
                # Mock extract to raise exception
                with patch("src.core.otel_integration.context_propagation.extract") as mock_extract:
                    mock_extract.side_effect = Exception("Extraction failed")
                    
                    with pytest.raises(OTELContextError):
                        extract_trace_context(carrier)

    def test_get_trace_context_exception(self):
        """Test get_trace_context handles exceptions gracefully."""
        tracer = OTELTracer(
            service_name="test-service",
            otlp_endpoint="http://localhost:4317",
        )
        
        if tracer._enabled and tracer._tracer:
            with tracer.start_trace("test.trace"):
                # Mock trace.get_current_span to raise exception
                with patch("src.core.otel_integration.context_propagation.trace.get_current_span") as mock_get_span:
                    mock_get_span.side_effect = Exception("Get span failed")
                    
                    result = get_trace_context()
                    # Should return None on exception
                    assert result is None

    def test_get_trace_context_no_span_context(self):
        """Test get_trace_context when span has no context."""
        tracer = OTELTracer(
            service_name="test-service",
            otlp_endpoint="http://localhost:4317",
        )
        
        if tracer._enabled and tracer._tracer:
            with tracer.start_trace("test.trace"):
                # Mock get_current_span to return a span with no context
                import src.core.otel_integration.context_propagation as ctx_module
                original_get_current_span = ctx_module.trace.get_current_span
                
                mock_span = Mock()
                mock_span.get_span_context.return_value = None
                
                def mock_get_span():
                    return mock_span
                
                ctx_module.trace.get_current_span = mock_get_span
                ctx_module.trace.is_recording = lambda span: True
                
                try:
                    result = get_trace_context()
                    # Should return None when context is None
                    assert result is None
                finally:
                    ctx_module.trace.get_current_span = original_get_current_span


class TestOTELTracerErrorPaths:
    """Tests for tracer error handling."""

    def test_tracer_init_exception_handling(self):
        """Test tracer initialization handles exceptions."""
        # Mock Resource.create to raise exception
        with patch("src.core.otel_integration.otel_tracer.Resource.create") as mock_resource:
            mock_resource.side_effect = Exception("Resource creation failed")
            
            tracer = OTELTracer(
                service_name="test-service",
                otlp_endpoint="http://localhost:4317",
            )
            
            # Should fall back to no-op on exception
            assert tracer.service_name == "test-service"
            assert tracer._enabled is False

    def test_span_set_attribute_exception(self):
        """Test span set_attribute handles exceptions."""
        tracer = OTELTracer(
            service_name="test-service",
            otlp_endpoint="http://localhost:4317",
        )
        
        if tracer._enabled and tracer._tracer:
            span = tracer.start_span("test.operation")
            
            if span._span:
                # Mock span.set_attribute to raise exception
                span._span.set_attribute = Mock(side_effect=Exception("Set attribute failed"))
                
                # Should not raise exception, just log debug
                span.set_attribute("key", "value")
                assert span._attributes["key"] == "value"

    def test_span_add_event_exception(self):
        """Test span add_event handles exceptions."""
        tracer = OTELTracer(
            service_name="test-service",
            otlp_endpoint="http://localhost:4317",
        )
        
        if tracer._enabled and tracer._tracer:
            span = tracer.start_span("test.operation")
            
            if span._span:
                # Mock span.add_event to raise exception
                span._span.add_event = Mock(side_effect=Exception("Add event failed"))
                
                # Should not raise exception, just log debug
                span.add_event("test.event")

    def test_span_record_exception_exception(self):
        """Test span record_exception handles exceptions."""
        tracer = OTELTracer(
            service_name="test-service",
            otlp_endpoint="http://localhost:4317",
        )
        
        if tracer._enabled and tracer._tracer:
            span = tracer.start_span("test.operation")
            
            if span._span:
                # Mock span.record_exception to raise exception
                span._span.record_exception = Mock(side_effect=Exception("Record exception failed"))
                
                # Should not raise exception, just log debug
                exception = ValueError("Test error")
                span.record_exception(exception)

    def test_span_set_status_exception(self):
        """Test span set_status handles exceptions."""
        tracer = OTELTracer(
            service_name="test-service",
            otlp_endpoint="http://localhost:4317",
        )
        
        if tracer._enabled and tracer._tracer:
            span = tracer.start_span("test.operation")
            
            if span._span:
                # Mock span.set_status to raise exception
                span._span.set_status = Mock(side_effect=Exception("Set status failed"))
                
                # Should not raise exception, just log debug
                from opentelemetry.trace import StatusCode
                span.set_status(StatusCode.OK, "Success")

    def test_span_end_exception(self):
        """Test span end handles exceptions."""
        tracer = OTELTracer(
            service_name="test-service",
            otlp_endpoint="http://localhost:4317",
        )
        
        if tracer._enabled and tracer._tracer:
            span = tracer.start_span("test.operation")
            
            if span._span:
                # Mock span.end to raise exception
                span._span.end = Mock(side_effect=Exception("End failed"))
                
                # Should not raise exception, just log debug
                span.end()
                assert span._ended is True


class TestOTELMetricsErrorPaths:
    """Tests for metrics error handling."""

    def test_metrics_init_exception_handling(self):
        """Test metrics initialization handles exceptions."""
        # Mock Resource.create to raise exception
        with patch("src.core.otel_integration.otel_metrics.Resource.create") as mock_resource:
            mock_resource.side_effect = Exception("Resource creation failed")
            
            metrics = OTELMetrics(
                service_name="test-service",
                otlp_endpoint="http://localhost:4317",
            )
            
            # Should fall back to no-op on exception
            assert metrics.service_name == "test-service"
            assert metrics._enabled is False

    def test_increment_counter_exception(self):
        """Test increment_counter raises OTELMetricsError on exception."""
        metrics = OTELMetrics(
            service_name="test-service",
            otlp_endpoint="http://localhost:4317",
        )
        
        if metrics._enabled and metrics._meter:
            # Mock meter.create_counter to raise exception
            metrics._meter.create_counter = Mock(side_effect=Exception("Create counter failed"))
            
            from src.core.otel_integration.exceptions import OTELMetricsError
            
            with pytest.raises(OTELMetricsError):
                metrics.increment_counter("test.counter")

    def test_record_histogram_exception(self):
        """Test record_histogram raises OTELMetricsError on exception."""
        metrics = OTELMetrics(
            service_name="test-service",
            otlp_endpoint="http://localhost:4317",
        )
        
        if metrics._enabled and metrics._meter:
            # Mock meter.create_histogram to raise exception
            metrics._meter.create_histogram = Mock(side_effect=Exception("Create histogram failed"))
            
            from src.core.otel_integration.exceptions import OTELMetricsError
            
            with pytest.raises(OTELMetricsError):
                metrics.record_histogram("test.histogram", value=1.0)

    def test_set_gauge_exception(self):
        """Test set_gauge raises OTELMetricsError on exception."""
        metrics = OTELMetrics(
            service_name="test-service",
            otlp_endpoint="http://localhost:4317",
        )
        
        if metrics._enabled and metrics._meter:
            # Mock meter.create_up_down_counter to raise exception
            metrics._meter.create_up_down_counter = Mock(side_effect=Exception("Create gauge failed"))
            
            from src.core.otel_integration.exceptions import OTELMetricsError
            
            with pytest.raises(OTELMetricsError):
                metrics.set_gauge("test.gauge", value=10.0)

