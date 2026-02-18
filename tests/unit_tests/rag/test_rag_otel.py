"""
Unit Tests for RAG OTEL Integration

Tests for OpenTelemetry integration within the RAG System.
"""

from src.core.otel_integration import OTELMetrics, OTELTracer


class TestRAGOTELIntegration:
    """Tests for RAG OTEL integration."""

    def test_rag_with_otel_tracer(self):
        """Test RAG system initialization with OTEL tracer."""
        # Note: This test verifies OTEL fields can be set
        # Full RAG initialization requires database connection
        tracer = OTELTracer(service_name="test-rag")
        
        # Verify tracer is properly configured
        assert tracer is not None
        assert tracer.service_name == "test-rag"

    def test_rag_with_otel_metrics(self):
        """Test RAG system initialization with OTEL metrics."""
        metrics = OTELMetrics(service_name="test-rag")
        
        # Verify metrics is properly configured
        assert metrics is not None
        assert metrics.service_name == "test-rag"

    def test_otel_tracer_initialization(self):
        """Test OTEL tracer can be created for RAG."""
        tracer = OTELTracer(service_name="rag-system")
        
        assert tracer.service_name == "rag-system"
        assert tracer.environment == "development"

    def test_otel_metrics_initialization(self):
        """Test OTEL metrics can be created for RAG."""
        metrics = OTELMetrics(service_name="rag-system")
        
        assert metrics.service_name == "rag-system"
        assert metrics.environment == "development"

