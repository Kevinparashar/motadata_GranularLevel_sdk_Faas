"""
Comprehensive tests for OTEL functions to improve coverage.

Tests missing paths in functions.py to achieve >85% coverage.
"""

from unittest.mock import MagicMock, patch

from src.core.otel_integration.functions import (
    create_otel_tracer,
    create_otel_metrics,
    get_current_trace_context,
)


class TestCreateOTELTracerCoverage:
    """Test create_otel_tracer() for missing coverage paths."""

    def test_create_otel_tracer_with_config_disabled(self):
        """Test create_otel_tracer() when OTEL is disabled in config (covers line 46)."""
        with patch("src.faas.shared.config.get_config") as mock_get_config:
            mock_config = MagicMock()
            mock_config.enable_otel = False
            mock_get_config.return_value = mock_config
            
            _result = create_otel_tracer(service_name="test-service")
            
            assert _result is None

    def test_create_otel_tracer_with_config_service_name(self):
        """Test create_otel_tracer() gets service_name from config (covers line 49)."""
        with patch("src.faas.shared.config.get_config") as mock_get_config, \
             patch("src.core.otel_integration.functions.OTELTracer") as mock_tracer_class:
            mock_config = MagicMock()
            mock_config.enable_otel = True
            mock_config.service_name = "config-service"
            mock_get_config.return_value = mock_config
            mock_tracer = MagicMock()
            mock_tracer_class.return_value = mock_tracer
            
            _result = create_otel_tracer()
            
            assert _result == mock_tracer
            mock_tracer_class.assert_called_once()
            # Should use service_name from config
            call_args = mock_tracer_class.call_args
            assert call_args[0][0] == "config-service"

    def test_create_otel_tracer_with_config_otlp_endpoint(self):
        """Test create_otel_tracer() gets otlp_endpoint from config (covers line 52)."""
        with patch("src.faas.shared.config.get_config") as mock_get_config, \
             patch("src.core.otel_integration.functions.OTELTracer") as mock_tracer_class:
            mock_config = MagicMock()
            mock_config.enable_otel = True
            mock_config.service_name = "test-service"
            mock_config.otel_exporter_otlp_endpoint = "http://otel:4317"
            mock_get_config.return_value = mock_config
            mock_tracer = MagicMock()
            mock_tracer_class.return_value = mock_tracer
            
            _result = create_otel_tracer()
            
            call_args = mock_tracer_class.call_args
            assert call_args[0][1] == "http://otel:4317"  # otlp_endpoint

    def test_create_otel_tracer_with_config_environment(self):
        """Test create_otel_tracer() gets environment from config (covers line 55)."""
        with patch("src.faas.shared.config.get_config") as mock_get_config, \
             patch("src.core.otel_integration.functions.OTELTracer") as mock_tracer_class:
            mock_config = MagicMock()
            mock_config.enable_otel = True
            mock_config.service_name = "test-service"
            mock_config.environment = "production"
            mock_get_config.return_value = mock_config
            mock_tracer = MagicMock()
            mock_tracer_class.return_value = mock_tracer
            
            _result = create_otel_tracer()
            
            call_args = mock_tracer_class.call_args
            assert call_args[0][2] == "production"  # environment

    def test_create_otel_tracer_with_config_service_version(self):
        """Test create_otel_tracer() gets service_version from config (covers line 58)."""
        with patch("src.faas.shared.config.get_config") as mock_get_config, \
             patch("src.core.otel_integration.functions.OTELTracer") as mock_tracer_class:
            mock_config = MagicMock()
            mock_config.enable_otel = True
            mock_config.service_name = "test-service"
            mock_config.service_version = "1.2.3"
            mock_get_config.return_value = mock_config
            mock_tracer = MagicMock()
            mock_tracer_class.return_value = mock_tracer
            
            _result = create_otel_tracer()
            
            call_args = mock_tracer_class.call_args
            assert call_args[0][3] == "1.2.3"  # service_version

    def test_create_otel_tracer_config_exception(self):
        """Test create_otel_tracer() when config raises exception (covers lines 63-66)."""
        with patch("src.faas.shared.config.get_config", side_effect=RuntimeError("Config error")), \
             patch("src.core.otel_integration.functions.OTELTracer") as mock_tracer_class:
            mock_tracer = MagicMock()
            mock_tracer_class.return_value = mock_tracer
            
            _result = create_otel_tracer(service_name="test-service")
            
            assert _result == mock_tracer
            # Should use provided service_name when config fails
            call_args = mock_tracer_class.call_args
            assert call_args[0][0] == "test-service"

    def test_create_otel_tracer_config_import_error(self):
        """Test create_otel_tracer() when config import fails."""
        with patch("src.faas.shared.config.get_config", side_effect=ImportError("No config")), \
             patch("src.core.otel_integration.functions.OTELTracer") as mock_tracer_class:
            mock_tracer = MagicMock()
            mock_tracer_class.return_value = mock_tracer
            
            _result = create_otel_tracer(service_name="test-service")
            
            assert _result == mock_tracer

    def test_create_otel_tracer_config_attribute_error(self):
        """Test create_otel_tracer() when config attribute access fails."""
        with patch("src.faas.shared.config.get_config", side_effect=AttributeError("No attr")), \
             patch("src.core.otel_integration.functions.OTELTracer") as mock_tracer_class:
            mock_tracer = MagicMock()
            mock_tracer_class.return_value = mock_tracer
            
            _result = create_otel_tracer(service_name="test-service")
            
            assert _result == mock_tracer

    def test_create_otel_tracer_none_service_name_fallback(self):
        """Test create_otel_tracer() when service_name is None (covers line 61)."""
        with patch("src.faas.shared.config.get_config", side_effect=RuntimeError("Config error")), \
             patch("src.core.otel_integration.functions.OTELTracer") as mock_tracer_class:
            mock_tracer = MagicMock()
            mock_tracer_class.return_value = mock_tracer
            
            _result = create_otel_tracer(service_name=None)
            
            assert _result == mock_tracer
            # Should use default "ai-sdk" when service_name is None
            call_args = mock_tracer_class.call_args
            assert call_args[0][0] == "ai-sdk"


class TestCreateOTELMetricsCoverage:
    """Test create_otel_metrics() for missing coverage paths."""

    def test_create_otel_metrics_with_config_disabled(self):
        """Test create_otel_metrics() when OTEL is disabled in config (covers line 93)."""
        with patch("src.faas.shared.config.get_config") as mock_get_config:
            mock_config = MagicMock()
            mock_config.enable_otel = False
            mock_get_config.return_value = mock_config
            
            _result = create_otel_metrics(service_name="test-service")
            
            assert _result is None

    def test_create_otel_metrics_with_config_service_name(self):
        """Test create_otel_metrics() gets service_name from config (covers line 97)."""
        with patch("src.faas.shared.config.get_config") as mock_get_config, \
             patch("src.core.otel_integration.functions.OTELMetrics") as mock_metrics_class:
            mock_config = MagicMock()
            mock_config.enable_otel = True
            mock_config.service_name = "config-service"
            mock_get_config.return_value = mock_config
            mock_metrics = MagicMock()
            mock_metrics_class.return_value = mock_metrics
            
            _result = create_otel_metrics()
            
            assert _result == mock_metrics
            call_args = mock_metrics_class.call_args
            assert call_args[0][0] == "config-service"

    def test_create_otel_metrics_with_config_otlp_endpoint(self):
        """Test create_otel_metrics() gets otlp_endpoint from config (covers line 100)."""
        with patch("src.faas.shared.config.get_config") as mock_get_config, \
             patch("src.core.otel_integration.functions.OTELMetrics") as mock_metrics_class:
            mock_config = MagicMock()
            mock_config.enable_otel = True
            mock_config.service_name = "test-service"
            mock_config.otel_exporter_otlp_endpoint = "http://otel:4317"
            mock_get_config.return_value = mock_config
            mock_metrics = MagicMock()
            mock_metrics_class.return_value = mock_metrics
            
            _result = create_otel_metrics()
            
            call_args = mock_metrics_class.call_args
            assert call_args[0][1] == "http://otel:4317"  # otlp_endpoint

    def test_create_otel_metrics_with_config_environment(self):
        """Test create_otel_metrics() gets environment from config (covers line 103)."""
        with patch("src.faas.shared.config.get_config") as mock_get_config, \
             patch("src.core.otel_integration.functions.OTELMetrics") as mock_metrics_class:
            mock_config = MagicMock()
            mock_config.enable_otel = True
            mock_config.service_name = "test-service"
            mock_config.environment = "production"
            mock_get_config.return_value = mock_config
            mock_metrics = MagicMock()
            mock_metrics_class.return_value = mock_metrics
            
            _result = create_otel_metrics()
            
            call_args = mock_metrics_class.call_args
            assert call_args[0][2] == "production"  # environment

    def test_create_otel_metrics_config_exception(self):
        """Test create_otel_metrics() when config raises exception (covers lines 108-111)."""
        with patch("src.faas.shared.config.get_config", side_effect=RuntimeError("Config error")), \
             patch("src.core.otel_integration.functions.OTELMetrics") as mock_metrics_class:
            mock_metrics = MagicMock()
            mock_metrics_class.return_value = mock_metrics
            
            _result = create_otel_metrics(service_name="test-service")
            
            assert _result == mock_metrics
            call_args = mock_metrics_class.call_args
            assert call_args[0][0] == "test-service"

    def test_create_otel_metrics_none_service_name_fallback(self):
        """Test create_otel_metrics() when service_name is None (covers line 106)."""
        with patch("src.faas.shared.config.get_config", side_effect=RuntimeError("Config error")), \
             patch("src.core.otel_integration.functions.OTELMetrics") as mock_metrics_class:
            mock_metrics = MagicMock()
            mock_metrics_class.return_value = mock_metrics
            
            _result = create_otel_metrics(service_name=None)
            
            assert _result == mock_metrics
            call_args = mock_metrics_class.call_args
            assert call_args[0][0] == "ai-sdk"  # Default fallback


class TestGetCurrentTraceContext:
    """Test get_current_trace_context() function."""

    def test_get_current_trace_context(self):
        """Test get_current_trace_context() basic functionality."""
        with patch("src.core.otel_integration.functions.get_trace_context") as mock_get_context:
            mock_get_context.return_value = {"trace_id": "123", "span_id": "456"}
            
            _result = get_current_trace_context()
            
            assert _result == {"trace_id": "123", "span_id": "456"}
            mock_get_context.assert_called_once()

    def test_get_current_trace_context_none(self):
        """Test get_current_trace_context() when no context available."""
        with patch("src.core.otel_integration.functions.get_trace_context") as mock_get_context:
            mock_get_context.return_value = None
            
            _result = get_current_trace_context()
            
            assert _result is None

