"""
Tests for cache backend auto-detection in OrchestratorService.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.faas.services.orchestrator_service.service import OrchestratorService
from src.faas.shared.config import ServiceConfig


@pytest.fixture
def mock_config_with_dragonfly():
    """Create mock service configuration with Dragonfly URL."""
    return ServiceConfig(
        service_name="orchestrator-service",
        service_version="1.0.0",
        service_port=8080,
        database_url="postgresql://test:test@localhost/test",
        gateway_service_url="http://gateway-service:8080",
        agent_service_url="http://agent-service:8080",
        rag_service_url="http://rag-service:8080",
        cache_service_url="http://cache-service:8080",
        ml_service_url=None,
        prompt_service_url=None,
        data_ingestion_service_url=None,
        prompt_generator_service_url=None,
        llmops_service_url=None,
        orchestrator_service_url=None,
        dragonfly_url="redis://localhost:6379",  # Dragonfly URL provided
        nats_url=None,
        otel_exporter_otlp_endpoint=None,
        enable_nats=False,
        enable_otel=False,
    )


@pytest.fixture
def mock_config_without_dragonfly():
    """Create mock service configuration without Dragonfly URL."""
    return ServiceConfig(
        service_name="orchestrator-service",
        service_version="1.0.0",
        service_port=8080,
        database_url="postgresql://test:test@localhost/test",
        gateway_service_url="http://gateway-service:8080",
        agent_service_url="http://agent-service:8080",
        rag_service_url="http://rag-service:8080",
        cache_service_url="http://cache-service:8080",
        ml_service_url=None,
        prompt_service_url=None,
        data_ingestion_service_url=None,
        prompt_generator_service_url=None,
        llmops_service_url=None,
        orchestrator_service_url=None,
        dragonfly_url=None,  # No Dragonfly URL
        nats_url=None,
        otel_exporter_otlp_endpoint=None,
        enable_nats=False,
        enable_otel=False,
    )


@pytest.fixture
def mock_db():
    """Create mock database connection."""
    db = MagicMock()
    db.fetch_one = AsyncMock(return_value=None)
    db.fetch_all = AsyncMock(return_value=[])
    db.execute = AsyncMock()
    return db


def test_orchestrator_service_uses_dragonfly_when_url_provided(mock_config_with_dragonfly, mock_db):
    """Test that OrchestratorService uses Dragonfly backend when URL is provided."""
    with patch("src.faas.services.orchestrator_service.service.create_gateway") as mock_create_gateway, \
         patch("src.core.litellm_gateway.create_gateway"), \
         patch("src.faas.integrations.codec.create_codec_manager", return_value=None), \
         patch("src.faas.integrations.otel.create_otel_tracer", return_value=None), \
         patch("src.faas.services.orchestrator_service.service.CacheMechanism") as mock_cache_class:
        
        # Mock gateway
        mock_gateway = MagicMock()
        mock_gateway.generate_async = AsyncMock()
        mock_create_gateway.return_value = mock_gateway
        
        # Mock cache mechanism
        mock_cache_instance = MagicMock()
        mock_cache_instance.get = AsyncMock(return_value=None)
        mock_cache_instance.set = AsyncMock()
        mock_cache_class.return_value = mock_cache_instance
        
        _ = OrchestratorService(
            config=mock_config_with_dragonfly,
            db_connection=mock_db,
        )
        
        # Verify CacheMechanism was called with Dragonfly backend
        call_args = mock_cache_class.call_args
        assert call_args is not None
        cache_config = call_args[1]["config"]  # Get config from kwargs
        assert cache_config.backend == "dragonfly"
        assert cache_config.dragonfly_url == "redis://localhost:6379"


def test_orchestrator_service_uses_memory_when_no_dragonfly_url(mock_config_without_dragonfly, mock_db):
    """Test that OrchestratorService uses memory backend when no Dragonfly URL is provided."""
    with patch("src.faas.services.orchestrator_service.service.create_gateway") as mock_create_gateway, \
         patch("src.core.litellm_gateway.create_gateway") as mock_core_gateway, \
         patch("src.faas.integrations.codec.create_codec_manager", return_value=None), \
         patch("src.faas.integrations.otel.create_otel_tracer", return_value=None), \
         patch("src.faas.services.orchestrator_service.service.CacheMechanism") as mock_cache_class:
        
        # Mock gateway
        mock_gateway = MagicMock()
        mock_gateway.generate_async = AsyncMock()
        mock_create_gateway.return_value = mock_gateway
        mock_core_gateway.return_value = mock_gateway
        
        # Mock cache mechanism
        mock_cache_instance = MagicMock()
        mock_cache_instance.get = AsyncMock(return_value=None)
        mock_cache_instance.set = AsyncMock()
        mock_cache_class.return_value = mock_cache_instance
        
        _ = OrchestratorService(
            config=mock_config_without_dragonfly,
            db_connection=mock_db,
        )
        
        # Verify CacheMechanism was called with memory backend
        call_args = mock_cache_class.call_args
        assert call_args is not None
        cache_config = call_args[1]["config"]  # Get config from kwargs
        assert cache_config.backend == "memory"
        assert cache_config.dragonfly_url is None

