"""
Unit Tests for OTEL Metrics

Tests for OpenTelemetry metrics functionality.
"""

from src.core.otel_integration import OTELMetrics, create_otel_metrics


class TestOTELMetrics:
    """Tests for OTELMetrics class."""

    def test_init_with_service_name(self):
        """Test OTELMetrics initialization with service name."""
        metrics = OTELMetrics(service_name="test-service")
        
        assert metrics.service_name == "test-service"
        assert metrics.otlp_endpoint is None
        assert metrics.environment == "development"

    def test_init_with_endpoint(self):
        """Test OTELMetrics initialization with endpoint."""
        metrics = OTELMetrics(
            service_name="test-service",
            otlp_endpoint="http://localhost:4317",
        )
        
        assert metrics.service_name == "test-service"
        assert metrics.otlp_endpoint == "http://localhost:4317"

    def test_increment_counter(self):
        """Test incrementing a counter."""
        metrics = OTELMetrics(service_name="test-service")
        
        metrics.increment_counter("test.counter")
        # Should not raise exception

    def test_increment_counter_with_amount(self):
        """Test incrementing counter with custom amount."""
        metrics = OTELMetrics(service_name="test-service")
        
        metrics.increment_counter("test.counter", amount=5.0)
        # Should not raise exception

    def test_increment_counter_with_attributes(self):
        """Test incrementing counter with attributes."""
        metrics = OTELMetrics(service_name="test-service")
        
        metrics.increment_counter(
            "test.counter",
            attributes={"tenant_id": "tenant_123", "status": "success"},
        )
        # Should not raise exception

    def test_record_histogram(self):
        """Test recording histogram metric."""
        metrics = OTELMetrics(service_name="test-service")
        
        metrics.record_histogram("test.histogram", value=1.5)
        # Should not raise exception

    def test_record_histogram_with_attributes(self):
        """Test recording histogram with attributes."""
        metrics = OTELMetrics(service_name="test-service")
        
        metrics.record_histogram(
            "test.histogram",
            value=2.5,
            attributes={"operation": "query"},
        )
        # Should not raise exception

    def test_set_gauge(self):
        """Test setting gauge metric."""
        metrics = OTELMetrics(service_name="test-service")
        
        metrics.set_gauge("test.gauge", value=10.0)
        # Should not raise exception

    def test_set_gauge_with_attributes(self):
        """Test setting gauge with attributes."""
        metrics = OTELMetrics(service_name="test-service")
        
        metrics.set_gauge(
            "test.gauge",
            value=20.0,
            attributes={"type": "database"},
        )
        # Should not raise exception


class TestCreateOTELMetrics:
    """Tests for create_otel_metrics factory function."""

    def test_create_otel_metrics_with_service_name(self):
        """Test creating metrics with service name."""
        metrics = create_otel_metrics(service_name="test-service")
        
        assert metrics is not None
        assert metrics.service_name == "test-service"

    def test_create_otel_metrics_without_params(self):
        """Test creating metrics without parameters."""
        metrics = create_otel_metrics()
        
        # Should return None if config not available and no service_name provided
        # or return default metrics
        if metrics:
            assert metrics.service_name is not None

