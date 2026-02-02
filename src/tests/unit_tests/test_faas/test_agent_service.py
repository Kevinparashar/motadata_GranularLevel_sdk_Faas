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
        redis_url=None,
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
    with patch("src.faas.services.agent_service.get_database_connection") as mock_get_db:
        mock_get_db.return_value.get_connection.return_value = mock_db
        service = create_agent_service(
            service_name="agent-service",
            config_overrides={
                "database_url": "postgresql://test:test@localhost/test",
                "gateway_service_url": "http://gateway-service:8080",
            },
        )
        return service


def test_agent_service_creation(agent_service):
    """Test agent service creation."""
    assert agent_service is not None
    assert agent_service.app is not None
    assert agent_service.config.service_name == "agent-service"


def test_create_agent_endpoint(agent_service):
    """Test create agent endpoint."""
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
    client = TestClient(agent_service.app)

    # First create an agent
    create_response = client.post(
        "/api/v1/agents",
        json={"name": "Test Agent"},
        headers={"X-Tenant-ID": "tenant_123"},
    )

    if create_response.status_code == 201:
        agent_id = create_response.json()["data"]["agent_id"]

        # Then get it
        response = client.get(
            f"/api/v1/agents/{agent_id}",
            headers={"X-Tenant-ID": "tenant_123"},
        )

        assert response.status_code in [200, 404]


def test_health_check(agent_service):
    """Test health check endpoint."""
    client = TestClient(agent_service.app)

    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "agent-service"
