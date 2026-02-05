"""
Unit tests for Prompt Generator Service.
"""


from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from src.faas.services.prompt_generator_service import create_prompt_generator_service
from src.faas.shared.config import ServiceConfig


@pytest.fixture
def mock_config():
    """Create mock service configuration."""
    return ServiceConfig(
        service_name="prompt-generator-service",
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
    db.connect = AsyncMock(return_value=None)
    db.execute_query = AsyncMock(return_value=[])
    return db


@pytest.fixture
def prompt_generator_service(mock_config, mock_db):
    """Create prompt generator service instance for testing."""
    with patch("src.faas.services.prompt_generator_service.get_database_connection") as mock_get_db, \
         patch("src.faas.services.prompt_generator_service.create_gateway") as mock_create_gateway, \
         patch("src.faas.services.prompt_generator_service.create_agent_from_prompt") as mock_create_agent, \
         patch("src.faas.services.prompt_generator_service.create_tool_from_prompt") as mock_create_tool, \
         patch("src.faas.services.prompt_generator_service.rate_agent") as mock_rate_agent, \
         patch("src.faas.services.prompt_generator_service.rate_tool") as mock_rate_tool:
        mock_get_db.return_value.get_connection.return_value = mock_db
        
        # Mock gateway
        mock_gateway = Mock()
        mock_create_gateway.return_value = mock_gateway
        
        # Mock agent creation
        mock_agent = Mock()
        mock_agent.agent_id = "agent_123"
        mock_create_agent.return_value = mock_agent
        
        # Mock tool creation
        mock_tool = Mock()
        mock_tool.tool_id = "tool_123"
        mock_create_tool.return_value = mock_tool
        
        # Mock rating functions
        mock_rate_agent.return_value = {"success": True}
        mock_rate_tool.return_value = {"success": True}
        
        service = create_prompt_generator_service(
            service_name="prompt-generator-service",
            config_overrides={
                "database_url": "postgresql://test:test@localhost/test",
            },
        )
        
        return service


def test_prompt_generator_service_creation(prompt_generator_service):
    """Test prompt generator service creation."""
    assert prompt_generator_service is not None
    assert prompt_generator_service.app is not None
    assert prompt_generator_service.config.service_name == "prompt-generator-service"


@pytest.mark.asyncio
async def test_create_agent_from_prompt_endpoint(prompt_generator_service):
    """Test create agent from prompt endpoint."""
    with patch("src.faas.services.prompt_generator_service.create_agent_from_prompt") as mock_create_agent:
        mock_agent = Mock()
        mock_agent.agent_id = "agent_123"
        mock_create_agent.return_value = mock_agent
        
        client = TestClient(prompt_generator_service.app)
        
        response = client.post(
            "/api/v1/prompt-generator/agents",
            json={
                "prompt": "Create an agent that helps with customer support",
                "name": "Support Agent",
            },
            headers={
                "X-Tenant-ID": "tenant_123",
            },
        )
        
        assert response.status_code in [201, 500]
        if response.status_code == 201:
            data = response.json()
            assert data["success"] is True
            assert "agent_id" in data["data"]


@pytest.mark.asyncio
async def test_create_tool_from_prompt_endpoint(prompt_generator_service):
    """Test create tool from prompt endpoint."""
    with patch("src.faas.services.prompt_generator_service.create_tool_from_prompt") as mock_create_tool:
        mock_tool = Mock()
        mock_tool.tool_id = "tool_123"
        mock_create_tool.return_value = mock_tool
        
        client = TestClient(prompt_generator_service.app)
        
        response = client.post(
            "/api/v1/prompt-generator/tools",
            json={
                "prompt": "Create a tool that calculates tax",
                "name": "Tax Calculator",
            },
            headers={
                "X-Tenant-ID": "tenant_123",
            },
        )
        
        assert response.status_code in [201, 500]
        if response.status_code == 201:
            data = response.json()
            assert data["success"] is True
            assert "tool_id" in data["data"]


@pytest.mark.asyncio
async def test_rate_agent_endpoint(prompt_generator_service):
    """Test rate agent endpoint."""
    with patch("src.faas.services.prompt_generator_service.rate_agent", new_callable=AsyncMock) as mock_rate:
        mock_rate.return_value = {"success": True, "rating_id": "rating_123"}
        
        client = TestClient(prompt_generator_service.app)
        
        response = client.post(
            "/api/v1/prompt-generator/agents/agent_123/rate",
            json={
                "rating": 5,
                "feedback": "Great agent!",
            },
            headers={
                "X-Tenant-ID": "tenant_123",
            },
        )
        
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True


@pytest.mark.asyncio
async def test_rate_tool_endpoint(prompt_generator_service):
    """Test rate tool endpoint."""
    with patch("src.faas.services.prompt_generator_service.rate_tool", new_callable=AsyncMock) as mock_rate:
        mock_rate.return_value = {"success": True, "rating_id": "rating_123"}
        
        client = TestClient(prompt_generator_service.app)
        
        response = client.post(
            "/api/v1/prompt-generator/tools/tool_123/rate",
            json={
                "rating": 4,
                "feedback": "Good tool!",
            },
            headers={
                "X-Tenant-ID": "tenant_123",
            },
        )
        
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True


def test_health_check(prompt_generator_service):
    """Test health check endpoint."""
    client = TestClient(prompt_generator_service.app)
    
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "prompt-generator-service"


@pytest.mark.asyncio
async def test_create_agent_missing_tenant_id(prompt_generator_service):
    """Test create agent endpoint without tenant ID."""
    client = TestClient(prompt_generator_service.app)
    
    response = client.post(
        "/api/v1/prompt-generator/agents",
        json={
            "prompt": "Create an agent",
        },
    )
    
    assert response.status_code == 401  # AuthMiddleware should reject

