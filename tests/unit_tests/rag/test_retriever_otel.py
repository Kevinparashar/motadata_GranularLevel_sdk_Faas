"""
Unit Tests for Retriever OTEL Integration

Tests for OpenTelemetry integration within the Retriever component.
"""

from unittest.mock import AsyncMock, MagicMock

from src.core.rag.retriever import Retriever
from src.core.otel_integration import OTELMetrics, OTELTracer


class TestRetrieverOTELIntegration:
    """Tests for Retriever OTEL integration."""

    def test_retriever_with_otel_tracer(self):
        """Test retriever initialization with OTEL tracer."""
        tracer = OTELTracer(service_name="test-retriever")
        vector_ops = MagicMock()
        gateway = MagicMock()
        
        retriever = Retriever(
            vector_ops=vector_ops,
            gateway=gateway,
            otel_tracer=tracer,
        )
        
        assert retriever.otel_tracer is not None
        assert retriever.otel_tracer.service_name == "test-retriever"

    def test_retriever_with_otel_metrics(self):
        """Test retriever initialization with OTEL metrics."""
        metrics = OTELMetrics(service_name="test-retriever")
        vector_ops = MagicMock()
        gateway = MagicMock()
        
        retriever = Retriever(
            vector_ops=vector_ops,
            gateway=gateway,
            otel_metrics=metrics,
        )
        
        assert retriever.otel_metrics is not None
        assert retriever.otel_metrics.service_name == "test-retriever"

    def test_retriever_without_otel(self):
        """Test retriever works without OTEL configured."""
        vector_ops = MagicMock()
        gateway = MagicMock()
        
        retriever = Retriever(
            vector_ops=vector_ops,
            gateway=gateway,
        )
        
        # OTEL should be auto-initialized if available
        # But it may be None if OTEL SDK is not installed
        assert retriever is not None

    def test_retrieve_with_otel(self):
        """Test retrieve operation with OTEL tracing."""
        tracer = OTELTracer(service_name="test-retriever")
        metrics = OTELMetrics(service_name="test-retriever")
        
        vector_ops = MagicMock()
        gateway = MagicMock()
        gateway.embed = MagicMock(return_value=MagicMock(embeddings=[[0.1, 0.2, 0.3]]))
        
        vector_ops.similarity_search = AsyncMock(return_value=[
            {"id": "1", "content": "test", "similarity": 0.9}
        ])
        
        retriever = Retriever(
            vector_ops=vector_ops,
            gateway=gateway,
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        # Execute retrieve - should not raise exception
        results = retriever.retrieve("test query", top_k=5)
        
        assert results is not None
        assert retriever.otel_tracer is not None
        assert retriever.otel_metrics is not None

    def test_retrieve_without_otel(self):
        """Test retrieve operation without OTEL."""
        vector_ops = MagicMock()
        gateway = MagicMock()
        gateway.embed = MagicMock(return_value=MagicMock(embeddings=[[0.1, 0.2, 0.3]]))
        
        vector_ops.similarity_search = AsyncMock(return_value=[
            {"id": "1", "content": "test", "similarity": 0.9}
        ])
        
        retriever = Retriever(
            vector_ops=vector_ops,
            gateway=gateway,
        )
        retriever.otel_tracer = None
        retriever.otel_metrics = None
        
        results = retriever.retrieve("test query", top_k=5)
        
        assert results is not None

    def test_retrieve_with_filters_otel(self):
        """Test retrieve operation with filters and OTEL."""
        tracer = OTELTracer(service_name="test-retriever")
        metrics = OTELMetrics(service_name="test-retriever")
        
        vector_ops = MagicMock()
        gateway = MagicMock()
        gateway.embed = MagicMock(return_value=MagicMock(embeddings=[[0.1, 0.2, 0.3]]))
        
        vector_ops.similarity_search = AsyncMock(return_value=[
            {"id": "1", "content": "test", "similarity": 0.9, "metadata": {"tenant_id": "tenant_123"}}
        ])
        
        retriever = Retriever(
            vector_ops=vector_ops,
            gateway=gateway,
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        results = retriever.retrieve("test query", top_k=5, tenant_id="tenant_123", filters={"tenant_id": "tenant_123"})
        
        assert results is not None
        assert retriever.otel_tracer is not None

    def test_retrieve_hybrid_with_otel(self):
        """Test retrieve_hybrid operation with OTEL tracing."""
        tracer = OTELTracer(service_name="test-retriever")
        metrics = OTELMetrics(service_name="test-retriever")
        
        vector_ops = MagicMock()
        gateway = MagicMock()
        gateway.embed = MagicMock(return_value=MagicMock(embeddings=[[0.1, 0.2, 0.3]]))
        
        vector_ops.similarity_search = AsyncMock(return_value=[
            {"id": "1", "content": "test", "similarity": 0.9}
        ])
        vector_ops.db = MagicMock()
        vector_ops.db.execute_query = MagicMock(return_value=[])
        
        retriever = Retriever(
            vector_ops=vector_ops,
            gateway=gateway,
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        # Execute retrieve_hybrid - should not raise exception
        results = retriever.retrieve_hybrid("test query", top_k=5)
        
        assert results is not None
        assert retriever.otel_tracer is not None

