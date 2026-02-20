"""
Unit Tests for FaaS OTEL Integration

Tests for the FaaS OTEL integration wrapper that delegates to core implementation.
"""

from unittest.mock import MagicMock, patch

from src.faas.integrations.otel import OTELTracer, OTELSpan, create_otel_tracer


class TestFaaSOTELIntegration:
    """Tests for FaaS OTEL integration."""

    def test_imports_core_classes(self):
        """Test that FaaS integration exports core OTEL classes."""
        # Should be able to import from FaaS integration
        assert OTELTracer is not None
        assert OTELSpan is not None
        assert create_otel_tracer is not None

    def test_create_otel_tracer_with_config(self):
        """Test creating tracer with FaaS config."""
        with patch("src.faas.integrations.otel.get_config") as mock_get_config, \
             patch("src.faas.integrations.otel._create_otel_tracer") as mock_create:
            mock_config = MagicMock()
            mock_config.enable_otel = True
            mock_config.service_name = "test-service"
            mock_config.otel_exporter_otlp_endpoint = "http://localhost:4317"
            mock_config.environment = "production"
            mock_config.service_version = "1.0.0"
            mock_get_config.return_value = mock_config
            mock_tracer = MagicMock()
            mock_create.return_value = mock_tracer
            
            result = create_otel_tracer()
            
            assert result == mock_tracer
            mock_create.assert_called_once_with(
                service_name="test-service",
                otlp_endpoint="http://localhost:4317",
                environment="production",
                service_version="1.0.0",
            )

    def test_create_otel_tracer_disabled(self):
        """Test creating tracer when OTEL is disabled in config."""
        with patch("src.faas.integrations.otel.get_config") as mock_get_config:
            mock_config = MagicMock()
            mock_config.enable_otel = False
            mock_get_config.return_value = mock_config
            
            result = create_otel_tracer()
            
            assert result is None

    def test_create_otel_tracer_with_parameters(self):
        """Test creating tracer with explicit parameters."""
        with patch("src.faas.integrations.otel.get_config") as mock_get_config, \
             patch("src.faas.integrations.otel._create_otel_tracer") as mock_create:
            mock_config = MagicMock()
            mock_config.enable_otel = True
            mock_get_config.return_value = mock_config
            mock_tracer = MagicMock()
            mock_create.return_value = mock_tracer
            
            result = create_otel_tracer(
                service_name="custom-service",
                otlp_endpoint="http://custom:4317",
                environment="staging",
                service_version="2.0.0",
            )
            
            assert result == mock_tracer
            mock_create.assert_called_once_with(
                service_name="custom-service",
                otlp_endpoint="http://custom:4317",
                environment="staging",
                service_version="2.0.0",
            )

    def test_create_otel_tracer_config_not_loaded(self):
        """Test creating tracer when config is not loaded."""
        with patch("src.faas.integrations.otel.get_config") as mock_get_config, \
             patch("src.faas.integrations.otel._create_otel_tracer") as mock_create:
            mock_get_config.side_effect = RuntimeError("Config not loaded")
            mock_tracer = MagicMock()
            mock_create.return_value = mock_tracer
            
            result = create_otel_tracer(service_name="fallback-service")
            
            assert result == mock_tracer
            mock_create.assert_called_once_with(
                service_name="fallback-service",
                otlp_endpoint=None,
                environment=None,
                service_version=None,
            )

    def test_create_otel_tracer_default_service_name(self):
        """Test creating tracer with default service name when config not loaded."""
        with patch("src.faas.integrations.otel.get_config") as mock_get_config, \
             patch("src.faas.integrations.otel._create_otel_tracer") as mock_create:
            mock_get_config.side_effect = RuntimeError("Config not loaded")
            mock_tracer = MagicMock()
            mock_create.return_value = mock_tracer
            
            result = create_otel_tracer()
            
            assert result == mock_tracer
            mock_create.assert_called_once_with(
                service_name="faas-service",
                otlp_endpoint=None,
                environment=None,
                service_version=None,
            )

    def test_create_otel_tracer_partial_config(self):
        """Test creating tracer with partial config values."""
        with patch("src.faas.integrations.otel.get_config") as mock_get_config, \
             patch("src.faas.integrations.otel._create_otel_tracer") as mock_create:
            mock_config = MagicMock()
            mock_config.enable_otel = True
            mock_config.service_name = "test-service"
            mock_config.otel_exporter_otlp_endpoint = None
            # environment and service_version not set
            mock_get_config.return_value = mock_config
            mock_tracer = MagicMock()
            mock_create.return_value = mock_tracer
            
            result = create_otel_tracer()
            
            assert result == mock_tracer
            mock_create.assert_called_once_with(
                service_name="test-service",
                otlp_endpoint=None,
                environment="development",  # Default
                service_version=None,
            )

