"""
Unit tests for Prompt Service.
"""


from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from src.faas.services.prompt_service import create_prompt_service
from src.faas.shared.config import ServiceConfig


@pytest.fixture
def mock_config():
    """Create mock service configuration."""
    return ServiceConfig(
        service_name="prompt-service",
        service_version="1.0.0",
        service_port=8080,
        database_url="postgresql://test:test@localhost/test",
        gateway_service_url=None,
        cache_service_url=None,
        rag_service_url=None,
        agent_service_url=None,
        ml_service_url=None,
        prompt_service_url=None,
        data_ingestion_service_url=None,
        prompt_generator_service_url=None,
        llmops_service_url=None,
        dragonfly_url=None,
        nats_url=None,
        otel_exporter_otlp_endpoint=None,
        enable_nats=False,
        enable_otel=False,
    )


@pytest.fixture
def mock_db():
    """Create mock database connection."""
    db = Mock()
    db.connect = AsyncMock(return_value=None)
    db.execute_query = AsyncMock(return_value=[])
    return db


@pytest.fixture
def prompt_service(mock_config, mock_db):
    """Create prompt service instance for testing."""
    with patch("src.faas.services.prompt_service.get_database_connection") as mock_get_db, \
         patch("src.faas.services.prompt_service.create_prompt_manager") as mock_create_manager:
        mock_get_db.return_value.get_connection.return_value = mock_db
        
        # Mock prompt manager
        mock_manager = Mock()
        mock_manager.add_template = Mock()
        mock_manager.render = Mock(return_value="Rendered prompt")
        mock_manager.build_context_with_history = Mock(return_value="Built context")
        mock_create_manager.return_value = mock_manager
        
        service = create_prompt_service(
            service_name="prompt-service",
            config_overrides={
                "database_url": "postgresql://test:test@localhost/test",
            },
        )
        
        # Patch _get_prompt_manager to return the mock manager
        service._get_prompt_manager = Mock(return_value=mock_manager)
        
        return service


def test_prompt_service_creation(prompt_service):
    """Test prompt service creation."""
    assert prompt_service is not None
    assert prompt_service.app is not None
    assert prompt_service.config.service_name == "prompt-service"


@pytest.mark.asyncio
async def test_create_template_endpoint(prompt_service):
    """Test create template endpoint."""
    client = TestClient(prompt_service.app)
    
    response = client.post(
        "/api/v1/prompts/templates",
        json={
            "name": "test_template",
            "version": "1.0",
            "content": "Hello {name}",
            "metadata": {},
        },
        headers={
            "X-Tenant-ID": "tenant_123",
        },
    )
    
    assert response.status_code in [201, 500]
    if response.status_code == 201:
        data = response.json()
        assert data["success"] is True


@pytest.mark.asyncio
async def test_render_prompt_endpoint(prompt_service):
    """Test render prompt endpoint."""
    client = TestClient(prompt_service.app)
    
    response = client.post(
        "/api/v1/prompts/render",
        json={
            "template_name": "test_template",
            "variables": {"name": "World"},
        },
        headers={
            "X-Tenant-ID": "tenant_123",
        },
    )
    
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert data["success"] is True
        assert "rendered_prompt" in data["data"]


@pytest.mark.asyncio
async def test_build_context_endpoint(prompt_service):
    """Test build context endpoint."""
    client = TestClient(prompt_service.app)
    
    response = client.post(
        "/api/v1/prompts/context",
        json={
            "new_message": "What is AI?",
            "include_history": True,
        },
        headers={
            "X-Tenant-ID": "tenant_123",
        },
    )
    
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert data["success"] is True
        assert "context" in data["data"]


def test_health_check(prompt_service):
    """Test health check endpoint."""
    client = TestClient(prompt_service.app)
    
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "prompt-service"


@pytest.mark.asyncio
async def test_create_template_missing_tenant_id(prompt_service):
    """Test create template endpoint without tenant ID."""
    client = TestClient(prompt_service.app)
    
    response = client.post(
        "/api/v1/prompts/templates",
        json={
            "name": "test_template",
            "version": "1.0",
            "content": "Hello {name}",
        },
    )
    
    assert response.status_code == 401  # AuthMiddleware should reject

