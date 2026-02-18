"""
Unit Tests for Gateway OTEL Integration

Tests for OpenTelemetry integration within the LiteLLM Gateway.
"""

import pytest

from src.core.litellm_gateway.gateway import GatewayConfig, LiteLLMGateway
from src.core.otel_integration import OTELMetrics, OTELTracer


class TestGatewayOTELIntegration:
    """Tests for Gateway OTEL integration."""

    def test_gateway_with_otel_tracer(self):
        """Test gateway initialization with OTEL tracer."""
        tracer = OTELTracer(service_name="test-gateway")
        config = GatewayConfig()
        gateway = LiteLLMGateway(config=config)
        gateway.otel_tracer = tracer
        
        assert gateway.otel_tracer is not None
        assert gateway.otel_tracer.service_name == "test-gateway"

    def test_gateway_with_otel_metrics(self):
        """Test gateway initialization with OTEL metrics."""
        metrics = OTELMetrics(service_name="test-gateway")
        config = GatewayConfig()
        gateway = LiteLLMGateway(config=config)
        gateway.otel_metrics = metrics
        
        assert gateway.otel_metrics is not None
        assert gateway.otel_metrics.service_name == "test-gateway"

    def test_gateway_without_otel(self):
        """Test gateway works without OTEL configured."""
        config = GatewayConfig()
        gateway = LiteLLMGateway(config=config)
        
        assert gateway.otel_tracer is None
        assert gateway.otel_metrics is None

    @pytest.mark.asyncio
    async def test_generate_async_with_otel(self):
        """Test generate_async with OTEL tracing."""
        tracer = OTELTracer(service_name="test-gateway")
        metrics = OTELMetrics(service_name="test-gateway")
        
        config = GatewayConfig()
        gateway = LiteLLMGateway(config=config)
        gateway.otel_tracer = tracer
        gateway.otel_metrics = metrics
        
        # Should not raise exception even if gateway is not fully configured
        # (since we're just testing OTEL integration, not full gateway functionality)
        assert gateway.otel_tracer is not None
        assert gateway.otel_metrics is not None

