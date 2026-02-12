"""
Unit tests for otel.py
"""

from unittest.mock import MagicMock, patch

import pytest

from src.faas.integrations.otel import OTELSpan, OTELTracer, create_otel_tracer


class TestOTELTracer:
    """Tests for OTELTracer class."""

    def test_init(self):
        """Test OTELTracer initialization."""
        tracer = OTELTracer(service_name="test-service")

        assert tracer.service_name == "test-service"
        assert tracer.otlp_endpoint is None

    def test_init_with_endpoint(self):
        """Test OTELTracer initialization with endpoint."""
        tracer = OTELTracer(service_name="test-service", otlp_endpoint="http://otel:4317")

        assert tracer.service_name == "test-service"
        assert tracer.otlp_endpoint == "http://otel:4317"

    def test_start_span(self):
        """Test start_span method."""
        tracer = OTELTracer(service_name="test-service")

        span = tracer.start_span("test-span")

        assert isinstance(span, OTELSpan)
        assert span.name == "test-span"

    def test_start_span_with_kwargs(self):
        """Test start_span with kwargs."""
        tracer = OTELTracer(service_name="test-service")

        span = tracer.start_span("test-span", attribute1="value1", attribute2="value2")

        assert span.name == "test-span"
        assert span.attributes["attribute1"] == "value1"
        assert span.attributes["attribute2"] == "value2"

    def test_get_current_span(self):
        """Test get_current_span method."""
        tracer = OTELTracer(service_name="test-service")

        span = tracer.get_current_span()

        assert span is None


class TestOTELSpan:
    """Tests for OTELSpan class."""

    def test_init(self):
        """Test OTELSpan initialization."""
        span = OTELSpan("test-span")

        assert span.name == "test-span"
        assert span.attributes == {}
        assert span._ended is False

    def test_init_with_attributes(self):
        """Test OTELSpan initialization with attributes."""
        span = OTELSpan("test-span", key1="value1", key2="value2")

        assert span.name == "test-span"
        assert span.attributes["key1"] == "value1"
        assert span.attributes["key2"] == "value2"
        assert span._ended is False

    def test_set_attribute(self):
        """Test set_attribute method."""
        span = OTELSpan("test-span")

        span.set_attribute("key", "value")

        assert span.attributes["key"] == "value"

    def test_set_attribute_multiple(self):
        """Test set_attribute with multiple attributes."""
        span = OTELSpan("test-span")

        span.set_attribute("key1", "value1")
        span.set_attribute("key2", "value2")

        assert span.attributes["key1"] == "value1"
        assert span.attributes["key2"] == "value2"

    def test_set_attribute_overwrite(self):
        """Test set_attribute overwrites existing attribute."""
        span = OTELSpan("test-span", key="old_value")

        span.set_attribute("key", "new_value")

        assert span.attributes["key"] == "new_value"

    def test_add_event(self):
        """Test add_event method."""
        span = OTELSpan("test-span")

        span.add_event("test-event")

        # Should not raise

    def test_add_event_with_attributes(self):
        """Test add_event with attributes."""
        span = OTELSpan("test-span")

        span.add_event("test-event", {"key": "value"})

        # Should not raise

    def test_end(self):
        """Test end method."""
        span = OTELSpan("test-span")

        span.end()

        assert span._ended is True

    def test_end_multiple_times(self):
        """Test end can be called multiple times."""
        span = OTELSpan("test-span")

        span.end()
        span.end()
        span.end()

        assert span._ended is True

    def test_context_manager(self):
        """Test OTELSpan as context manager."""
        with OTELSpan("test-span") as span:
            assert span.name == "test-span"
            assert span._ended is False

        assert span._ended is True

    def test_context_manager_with_exception(self):
        """Test OTELSpan context manager with exception."""
        with pytest.raises(ValueError):
            with OTELSpan("test-span") as span:
                assert span._ended is False
                raise ValueError("Test error")

        assert span._ended is True


class TestCreateOTELTracer:
    """Tests for create_otel_tracer factory function."""

    def test_create_otel_tracer_with_params(self):
        """Test create_otel_tracer with explicit parameters."""
        tracer = create_otel_tracer(service_name="test-service", otlp_endpoint="http://otel:4317")

        assert tracer is not None
        assert isinstance(tracer, OTELTracer)
        assert tracer.service_name == "test-service"
        assert tracer.otlp_endpoint == "http://otel:4317"

    def test_create_otel_tracer_with_config_enabled(self):
        """Test create_otel_tracer with config when OTEL is enabled."""
        mock_config = MagicMock()
        mock_config.enable_otel = True
        mock_config.service_name = "config-service"
        mock_config.otel_exporter_otlp_endpoint = "http://config:4317"

        with patch("src.faas.shared.config.get_config", return_value=mock_config):
            tracer = create_otel_tracer()

            assert tracer is not None
            assert isinstance(tracer, OTELTracer)
            assert tracer.service_name == "config-service"
            assert tracer.otlp_endpoint == "http://config:4317"

    def test_create_otel_tracer_with_config_disabled(self):
        """Test create_otel_tracer with config when OTEL is disabled."""
        mock_config = MagicMock()
        mock_config.enable_otel = False

        with patch("src.faas.shared.config.get_config", return_value=mock_config):
            tracer = create_otel_tracer()

            assert tracer is None

    def test_create_otel_tracer_with_config_partial_params(self):
        """Test create_otel_tracer with config and partial parameters."""
        mock_config = MagicMock()
        mock_config.enable_otel = True
        mock_config.service_name = "config-service"
        mock_config.otel_exporter_otlp_endpoint = "http://config:4317"

        with patch("src.faas.shared.config.get_config", return_value=mock_config):
            tracer = create_otel_tracer(service_name="override-service")

            assert tracer is not None
            assert tracer.service_name == "override-service"
            assert tracer.otlp_endpoint == "http://config:4317"

    def test_create_otel_tracer_config_not_loaded_with_service_name(self):
        """Test create_otel_tracer when config not loaded but service_name provided."""
        with patch("src.faas.shared.config.get_config", side_effect=RuntimeError("Config not loaded")):
            tracer = create_otel_tracer(service_name="fallback-service")

            assert tracer is not None
            assert isinstance(tracer, OTELTracer)
            assert tracer.service_name == "fallback-service"
            assert tracer.otlp_endpoint is None

    def test_create_otel_tracer_config_not_loaded_with_endpoint(self):
        """Test create_otel_tracer when config not loaded but both params provided."""
        with patch("src.faas.shared.config.get_config", side_effect=RuntimeError("Config not loaded")):
            tracer = create_otel_tracer(
                service_name="fallback-service", otlp_endpoint="http://fallback:4317"
            )

            assert tracer is not None
            assert tracer.service_name == "fallback-service"
            assert tracer.otlp_endpoint == "http://fallback:4317"

    def test_create_otel_tracer_config_not_loaded_no_params(self):
        """Test create_otel_tracer when config not loaded and no params provided."""
        with patch("src.faas.shared.config.get_config", side_effect=RuntimeError("Config not loaded")):
            tracer = create_otel_tracer()

            assert tracer is None

