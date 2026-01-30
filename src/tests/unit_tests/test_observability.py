"""
Unit Tests for Evaluation & Observability Component

Tests distributed tracing, logging, and metrics collection.
"""

from unittest.mock import Mock, patch

import pytest

from src.core.evaluation_observability import (
    MetricCollector,
    ObservabilityManager,
    StructuredLogger,
    TraceContext,
)


class TestObservabilityManager:
    """Test ObservabilityManager."""

    def test_initialization(self):
        """Test observability manager initialization."""
        manager = ObservabilityManager(service_name="test-service", environment="test")
        assert manager.service_name == "test-service"
        assert manager.environment == "test"

    def test_get_logger(self):
        """Test logger retrieval."""
        manager = ObservabilityManager("test-service", "test")
        logger = manager.get_logger("test_module")
        assert logger is not None
        assert isinstance(logger, StructuredLogger)

    def test_start_trace(self):
        """Test trace creation."""
        manager = ObservabilityManager("test-service", "test")

        with manager.start_trace("test_operation") as span:
            assert span is not None
            span.set_attribute("test.key", "test.value")

    def test_start_span(self):
        """Test span creation."""
        manager = ObservabilityManager("test-service", "test")

        with manager.start_trace("parent") as parent:
            with manager.start_span("child", parent=parent) as child:
                assert child is not None
                child.set_attribute("child.key", "child.value")

    def test_get_metrics(self):
        """Test metrics collector retrieval."""
        manager = ObservabilityManager("test-service", "test")
        metrics = manager.get_metrics()
        assert metrics is not None
        assert isinstance(metrics, MetricCollector)


class TestStructuredLogger:
    """Test StructuredLogger."""

    def test_info_logging(self):
        """Test info level logging."""
        logger = StructuredLogger("test_module")
        # Should not raise exception
        logger.info("Test message", extra={"key": "value"})

    def test_warning_logging(self):
        """Test warning level logging."""
        logger = StructuredLogger("test_module")
        logger.warning("Warning message", extra={"key": "value"})

    def test_error_logging(self):
        """Test error level logging."""
        logger = StructuredLogger("test_module")
        logger.error("Error message", extra={"error_code": "E001"})


class TestMetricCollector:
    """Test MetricCollector."""

    def test_increment_counter(self):
        """Test counter increment."""
        collector = MetricCollector()
        collector.increment_counter("test.counter")
        collector.increment_counter("test.counter", amount=5)
        # Verify no exceptions

    def test_set_gauge(self):
        """Test gauge setting."""
        collector = MetricCollector()
        collector.set_gauge("test.gauge", 42, tags={"type": "test"})

    def test_record_histogram(self):
        """Test histogram recording."""
        collector = MetricCollector()
        collector.record_histogram("test.histogram", 0.125, tags={"endpoint": "/test"})


class TestTraceContext:
    """Test TraceContext."""

    def test_trace_context_manager(self):
        """Test trace context as context manager."""
        manager = ObservabilityManager("test-service", "test")

        with manager.start_trace("test") as span:
            assert span is not None
            span.set_attribute("key", "value")


class TestExceptionTracking:
    """Test exception tracking."""

    def test_capture_exception(self):
        """Test exception capture."""
        manager = ObservabilityManager("test-service", "test")

        try:
            raise ValueError("Test exception")
        except ValueError as e:
            manager.capture_exception(e, context={"user_id": "test123"})
            # Should not raise exception
        except Exception as e:
            manager.capture_exception(e, context={"user_id": "test123"})
            # Should not raise exception


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
