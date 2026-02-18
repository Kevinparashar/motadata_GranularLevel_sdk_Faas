"""
Unit Tests for Data Ingestion OTEL Integration

Tests for OpenTelemetry integration within the Data Ingestion Service.
"""

import pytest
from pathlib import Path
import tempfile
from unittest.mock import AsyncMock, patch

from src.core.data_ingestion.ingestion_service import DataIngestionService
from src.core.otel_integration import OTELMetrics, OTELTracer


class TestIngestionOTELIntegration:
    """Tests for Data Ingestion OTEL integration."""

    def test_ingestion_with_otel_tracer(self):
        """Test ingestion service initialization with OTEL tracer."""
        tracer = OTELTracer(service_name="test-ingestion")
        service = DataIngestionService(
            otel_tracer=tracer,
        )
        
        assert service.otel_tracer is not None
        assert service.otel_tracer.service_name == "test-ingestion"

    def test_ingestion_with_otel_metrics(self):
        """Test ingestion service initialization with OTEL metrics."""
        metrics = OTELMetrics(service_name="test-ingestion")
        service = DataIngestionService(
            otel_metrics=metrics,
        )
        
        assert service.otel_metrics is not None
        assert service.otel_metrics.service_name == "test-ingestion"

    def test_ingestion_without_otel(self):
        """Test ingestion service works without OTEL configured."""
        service = DataIngestionService()
        
        # OTEL should be auto-initialized if available
        # But it may be None if OTEL SDK is not installed
        assert service is not None

    @pytest.mark.asyncio
    async def test_upload_and_process_with_otel(self):
        """Test upload_and_process with OTEL tracing."""
        tracer = OTELTracer(service_name="test-ingestion")
        metrics = OTELMetrics(service_name="test-ingestion")
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content")
            temp_path = f.name
        
        try:
            service = DataIngestionService(
                enable_validation=False,  # Disable validation for test
                enable_cleansing=False,  # Disable cleansing for test
                enable_auto_ingest=False,  # Disable auto-ingest for test
                otel_tracer=tracer,
                otel_metrics=metrics,
            )
            
            # Mock the multimodal loader
            with patch.object(service, 'multimodal_loader') as mock_loader:
                mock_loader.load = AsyncMock(return_value=("Test content", {}))
                
                # Execute upload_and_process - should not raise exception
                result = await service.upload_and_process(temp_path)
                
                assert result is not None
                assert "success" in result
                assert service.otel_tracer is not None
                assert service.otel_metrics is not None
        finally:
            # Clean up
            Path(temp_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_upload_and_process_without_otel(self):
        """Test upload_and_process without OTEL."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content")
            temp_path = f.name
        
        try:
            service = DataIngestionService(
                enable_validation=False,
                enable_cleansing=False,
                enable_auto_ingest=False,
            )
            service.otel_tracer = None
            service.otel_metrics = None
            
            # Mock the multimodal loader
            with patch.object(service, 'multimodal_loader') as mock_loader:
                mock_loader.load = AsyncMock(return_value=("Test content", {}))
                
                result = await service.upload_and_process(temp_path)
                
                assert result is not None
                assert "success" in result
        finally:
            Path(temp_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_batch_upload_and_process_with_otel(self):
        """Test batch_upload_and_process with OTEL tracing."""
        tracer = OTELTracer(service_name="test-ingestion")
        metrics = OTELMetrics(service_name="test-ingestion")
        
        # Create temporary files
        temp_paths = []
        for i in range(2):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(f"Test content {i}")
                temp_paths.append(f.name)
        
        try:
            service = DataIngestionService(
                enable_validation=False,
                enable_cleansing=False,
                enable_auto_ingest=False,
                otel_tracer=tracer,
                otel_metrics=metrics,
            )
            
            # Mock the multimodal loader
            with patch.object(service, 'multimodal_loader') as mock_loader:
                mock_loader.load = AsyncMock(return_value=("Test content", {}))
                
                results = await service.batch_upload_and_process(temp_paths)
                
                assert results is not None
                assert len(results) == 2
                assert service.otel_tracer is not None
        finally:
            for path in temp_paths:
                Path(path).unlink(missing_ok=True)

