"""
Unit Tests for LLMOps OTEL Integration

Tests for OpenTelemetry integration within the LLMOps component.
"""

import pytest

from src.core.llmops.llmops import LLMOps, LLMOperationType, LLMOperationStatus
from src.core.otel_integration import OTELMetrics, OTELTracer


class TestLLMOpsOTELIntegration:
    """Tests for LLMOps OTEL integration."""

    def test_llmops_with_otel_tracer(self):
        """Test LLMOps initialization with OTEL tracer."""
        tracer = OTELTracer(service_name="test-llmops")
        llmops = LLMOps(
            otel_tracer=tracer,
        )
        
        assert llmops.otel_tracer is not None
        assert llmops.otel_tracer.service_name == "test-llmops"

    def test_llmops_with_otel_metrics(self):
        """Test LLMOps initialization with OTEL metrics."""
        metrics = OTELMetrics(service_name="test-llmops")
        llmops = LLMOps(
            otel_metrics=metrics,
        )
        
        assert llmops.otel_metrics is not None
        assert llmops.otel_metrics.service_name == "test-llmops"

    def test_llmops_without_otel(self):
        """Test LLMOps works without OTEL configured."""
        llmops = LLMOps()
        
        # OTEL should be auto-initialized if available
        # But it may be None if OTEL SDK is not installed
        assert llmops is not None

    @pytest.mark.asyncio
    async def test_log_operation_with_otel(self):
        """Test log_operation with OTEL tracing."""
        tracer = OTELTracer(service_name="test-llmops")
        metrics = OTELMetrics(service_name="test-llmops")
        
        llmops = LLMOps(
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        # Execute log_operation - should not raise exception
        operation_id = await llmops.log_operation(
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            latency_ms=500.0,
        )
        
        assert operation_id is not None
        assert len(operation_id) > 0
        assert llmops.otel_tracer is not None
        assert llmops.otel_metrics is not None

    @pytest.mark.asyncio
    async def test_log_operation_without_otel(self):
        """Test log_operation without OTEL."""
        llmops = LLMOps()
        llmops.otel_tracer = None
        llmops.otel_metrics = None
        
        operation_id = await llmops.log_operation(
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            latency_ms=500.0,
        )
        
        assert operation_id is not None
        assert len(operation_id) > 0

    @pytest.mark.asyncio
    async def test_log_operation_error_with_otel(self):
        """Test log_operation error handling with OTEL."""
        tracer = OTELTracer(service_name="test-llmops")
        metrics = OTELMetrics(service_name="test-llmops")
        
        llmops = LLMOps(
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        # Log multiple operations
        await llmops.log_operation(
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            latency_ms=500.0,
            status=LLMOperationStatus.SUCCESS,
        )
        
        await llmops.log_operation(
            operation_type=LLMOperationType.EMBEDDING,
            model="text-embedding-3-small",
            prompt_tokens=50,
            completion_tokens=0,
            latency_ms=200.0,
            status=LLMOperationStatus.ERROR,
            error_message="Test error",
        )
        
        assert len(llmops.operations) == 2
        assert llmops.otel_tracer is not None

    def test_get_metrics_with_otel(self):
        """Test get_metrics with OTEL tracing."""
        tracer = OTELTracer(service_name="test-llmops")
        metrics = OTELMetrics(service_name="test-llmops")
        
        llmops = LLMOps(
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        # Execute get_metrics - should not raise exception
        result = llmops.get_metrics()
        
        assert result is not None
        assert "total_operations" in result
        assert "total_tokens" in result
        assert "total_cost_usd" in result
        assert llmops.otel_tracer is not None

    def test_get_metrics_without_otel(self):
        """Test get_metrics without OTEL."""
        llmops = LLMOps()
        llmops.otel_tracer = None
        llmops.otel_metrics = None
        
        result = llmops.get_metrics()
        
        assert result is not None
        assert "total_operations" in result

    def test_get_metrics_with_tenant_id_otel(self):
        """Test get_metrics with tenant_id and OTEL."""
        tracer = OTELTracer(service_name="test-llmops")
        metrics = OTELMetrics(service_name="test-llmops")
        
        llmops = LLMOps(
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        result = llmops.get_metrics(tenant_id="tenant_123")
        
        assert result is not None
        assert "total_operations" in result
        assert llmops.otel_tracer is not None

    def test_get_cost_summary_with_otel(self):
        """Test get_cost_summary with OTEL tracing."""
        tracer = OTELTracer(service_name="test-llmops")
        metrics = OTELMetrics(service_name="test-llmops")
        
        llmops = LLMOps(
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        # Execute get_cost_summary - should not raise exception
        result = llmops.get_cost_summary()
        
        assert result is not None
        assert "total_cost_usd" in result
        assert "total_tokens" in result
        assert "cost_per_1k_tokens" in result
        assert llmops.otel_tracer is not None

