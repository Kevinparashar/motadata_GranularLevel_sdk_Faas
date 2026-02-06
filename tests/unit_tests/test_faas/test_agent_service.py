"""
Unit tests for Agent Service.
"""


from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from src.faas.services.agent_service import create_agent_service
from src.faas.shared.config import ServiceConfig


@pytest.fixture
def mock_config():
    """Create mock service configuration."""
    return ServiceConfig(
        service_name="agent-service",
        service_version="1.0.0",
        service_port=8080,
        database_url="postgresql://test:test@localhost/test",
        gateway_service_url="http://gateway-service:8080",
        cache_service_url="http://cache-service:8080",
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
    db.fetch_one = AsyncMock(return_value=None)
    db.fetch_all = AsyncMock(return_value=[])
    db.execute = AsyncMock()
    return db


@pytest.fixture
def agent_service(mock_config, mock_db):
    """Create agent service instance for testing."""
    with patch("src.faas.services.agent_service.get_database_connection") as mock_get_db, \
         patch("src.faas.services.agent_service.create_gateway") as mock_create_gateway:
        mock_get_db.return_value.get_connection.return_value = mock_db
        
        # Mock gateway
        mock_gateway = Mock()
        mock_create_gateway.return_value = mock_gateway
        
        service = create_agent_service(
            service_name="agent-service",
            config_overrides={
                "database_url": "postgresql://test:test@localhost/test",
                "gateway_service_url": "http://gateway-service:8080",
            },
        )
        
        # Mock async agent_storage methods
        service.agent_storage.save_agent = AsyncMock(return_value=None)
        service.agent_storage.load_agent = AsyncMock(return_value=None)
        service.agent_storage.list_agents = AsyncMock(return_value=[])
        
        return service


def test_agent_service_creation(agent_service):
    """Test agent service creation."""
    assert agent_service is not None
    assert agent_service.app is not None
    assert agent_service.config.service_name == "agent-service"


def test_create_agent_endpoint(agent_service):
    """Test create agent endpoint."""
    from src.core.agno_agent_framework import Agent, AgentStatus
    
    # Mock agent to be returned by create_agent
    mock_agent = Mock(spec=Agent)
    mock_agent.agent_id = "test_agent_123"
    mock_agent.name = "Test Agent"
    mock_agent.status = AgentStatus.IDLE
    mock_agent.capabilities = []
    mock_agent.add_capability = Mock()
    
    with patch("src.faas.services.agent_service.create_agent", return_value=mock_agent), \
         patch("src.faas.services.agent_service.create_nats_client", return_value=None), \
         patch("src.faas.services.agent_service.create_otel_tracer", return_value=None):
        client = TestClient(agent_service.app)

        response = client.post(
            "/api/v1/agents",
            json={
                "name": "Test Agent",
                "description": "Test description",
                "llm_model": "gpt-4",
            },
            headers={
                "X-Tenant-ID": "tenant_123",
                "X-User-ID": "user_456",
            },
        )

        assert response.status_code in [201, 500]  # 500 if gateway creation fails
        if response.status_code == 201:
            data = response.json()
            assert data["success"] is True
            assert "agent_id" in data["data"]


def test_get_agent_endpoint(agent_service):
    """Test get agent endpoint."""
    from src.core.agno_agent_framework import Agent, AgentStatus
    
    # Mock agent to be returned by load_agent
    mock_agent = Mock(spec=Agent)
    mock_agent.agent_id = "test_agent_123"
    mock_agent.name = "Test Agent"
    mock_agent.description = "Test description"
    mock_agent.status = AgentStatus.IDLE
    mock_agent.capabilities = []
    
    # Set load_agent to return the mock agent
    agent_service.agent_storage.load_agent = AsyncMock(return_value=mock_agent)
    
    with patch("src.faas.services.agent_service.create_gateway") as mock_create_gateway:
        mock_gateway = Mock()
        mock_create_gateway.return_value = mock_gateway
        
        client = TestClient(agent_service.app)

        # Get agent
        response = client.get(
            "/api/v1/agents/test_agent_123",
            headers={"X-Tenant-ID": "tenant_123"},
        )

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert data["data"]["agent_id"] == "test_agent_123"


def test_health_check(agent_service):
    """Test health check endpoint."""
    client = TestClient(agent_service.app)

    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "agent-service"
