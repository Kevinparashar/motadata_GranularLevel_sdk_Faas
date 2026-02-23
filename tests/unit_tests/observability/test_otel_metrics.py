"""
Unit Tests for OTEL Metrics

Tests for OpenTelemetry metrics functionality.
"""

from unittest.mock import MagicMock, patch

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


class TestOTELMetricsTenantAttributes:
    """Tests for tenant attribute merging in OTEL metrics."""

    def test_increment_counter_merges_tenant_attributes(self):
        """Test that increment_counter merges tenant attributes from baggage."""
        metrics = OTELMetrics(service_name="test-service")
        
        with patch.object(metrics, "_merge_tenant_attributes") as mock_merge:
            mock_merge.return_value = {"tenant.id": "abc-123", "tenant.tier": "premium", "custom": "value"}
            
            metrics.increment_counter("test.counter", attributes={"custom": "value"})
            
            mock_merge.assert_called_once_with({"custom": "value"})

    def test_record_histogram_merges_tenant_attributes(self):
        """Test that record_histogram merges tenant attributes from baggage."""
        metrics = OTELMetrics(service_name="test-service")
        
        with patch.object(metrics, "_merge_tenant_attributes") as mock_merge:
            mock_merge.return_value = {"tenant.id": "abc-123", "tenant.tier": "premium", "custom": "value"}
            
            metrics.record_histogram("test.histogram", value=1.5, attributes={"custom": "value"})
            
            mock_merge.assert_called_once_with({"custom": "value"})

    def test_set_gauge_merges_tenant_attributes(self):
        """Test that set_gauge merges tenant attributes from baggage."""
        metrics = OTELMetrics(service_name="test-service")
        
        with patch.object(metrics, "_merge_tenant_attributes") as mock_merge:
            mock_merge.return_value = {"tenant.id": "abc-123", "tenant.tier": "premium", "custom": "value"}
            
            metrics.set_gauge("test.gauge", value=10.0, attributes={"custom": "value"})
            
            mock_merge.assert_called_once_with({"custom": "value"})

    def test_merge_tenant_attributes_with_baggage(self):
        """Test _merge_tenant_attributes when baggage has tenant context."""
        metrics = OTELMetrics(service_name="test-service")
        
        with patch("opentelemetry.baggage.get_baggage") as mock_get_baggage, \
             patch("opentelemetry.context.get_current") as mock_get_current:
            mock_ctx = MagicMock()
            mock_get_current.return_value = mock_ctx
            mock_get_baggage.side_effect = ["abc-123", "premium"]
            
            result = metrics._merge_tenant_attributes({"custom": "value"})
            
            assert result == {
                "custom": "value",
                "tenant.id": "abc-123",
                "tenant.tier": "premium",
            }

    def test_merge_tenant_attributes_no_baggage(self):
        """Test _merge_tenant_attributes when baggage has no tenant context."""
        metrics = OTELMetrics(service_name="test-service")
        
        with patch("opentelemetry.baggage.get_baggage") as mock_get_baggage, \
             patch("opentelemetry.context.get_current") as mock_get_current:
            mock_ctx = MagicMock()
            mock_get_current.return_value = mock_ctx
            mock_get_baggage.return_value = None
            
            result = metrics._merge_tenant_attributes({"custom": "value"})
            
            assert result == {"custom": "value"}

    def test_merge_tenant_attributes_existing_tenant_id(self):
        """Test _merge_tenant_attributes when tenant.id already exists in attributes."""
        metrics = OTELMetrics(service_name="test-service")
        
        with patch("opentelemetry.baggage.get_baggage") as mock_get_baggage, \
             patch("opentelemetry.context.get_current") as mock_get_current:
            mock_ctx = MagicMock()
            mock_get_current.return_value = mock_ctx
            
            # Should not override existing tenant.id
            result = metrics._merge_tenant_attributes({"tenant.id": "existing", "custom": "value"})
            
            assert result == {"tenant.id": "existing", "custom": "value"}
            # Should not call baggage.get_baggage if tenant.id already exists
            mock_get_baggage.assert_not_called()

    def test_merge_tenant_attributes_otel_not_available(self):
        """Test _merge_tenant_attributes when OTEL is not available."""
        metrics = OTELMetrics(service_name="test-service")
        
        with patch("opentelemetry.baggage.get_baggage", side_effect=ImportError("OTEL not available")):
            result = metrics._merge_tenant_attributes({"custom": "value"})
            
            assert result == {"custom": "value"}

    def test_merge_tenant_attributes_exception_handling(self):
        """Test _merge_tenant_attributes exception handling."""
        metrics = OTELMetrics(service_name="test-service")
        
        with patch("opentelemetry.context.get_current", side_effect=Exception("OTEL error")):
            result = metrics._merge_tenant_attributes({"custom": "value"})
            
            # Should return original attributes on exception
            assert result == {"custom": "value"}

