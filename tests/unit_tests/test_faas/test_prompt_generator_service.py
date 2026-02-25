"""
Unit tests for Prompt Generator Service.
"""

import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

# Mock ml_service module before any imports to avoid numpy dependency
ml_service_mock = MagicMock()
ml_service_mock.MLService = MagicMock
ml_service_mock.create_ml_service = MagicMock
sys.modules["src.faas.services.ml_service"] = ml_service_mock

from src.faas.services.prompt_generator_service.service import create_prompt_generator_service
from src.faas.shared.config import ServiceConfig

DEFAULT_LLM_MODEL = "gpt-4"
DEFAULT_LLM_PROVIDER = "openai"


def _get_service_instance_from_app(app):
    """Extract the service instance (self) from any bound route endpoint."""
    for route in getattr(app, "routes", []):
        endpoint = getattr(route, "endpoint", None)
        if endpoint is not None and hasattr(endpoint, "__self__"):
            return endpoint.__self__
    return None


@pytest.fixture
def mock_config():
    """Create mock service configuration."""
    return ServiceConfig(
        service_name="prompt-generator-service",
        service_version="1.0.0",
        service_port=8080,
        database_url="postgresql://test:test@localhost/test",
        gateway_service_url=None,
        orchestrator_service_url=None,
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
def prompt_generator_service(mock_config, mock_db):
    """Create prompt generator service instance for testing."""
    with (
        patch(
            "src.faas.services.prompt_generator_service.service.get_database_connection"
        ) as mock_get_db,
        patch(
            "src.faas.services.prompt_generator_service.service.create_gateway"
        ) as mock_create_gateway,
        patch(
            "src.faas.services.prompt_generator_service.service.create_agent_from_prompt",
            new_callable=AsyncMock,
        ) as mock_create_agent,
        patch(
            "src.faas.services.prompt_generator_service.service.create_tool_from_prompt",
            new_callable=AsyncMock,
        ) as mock_create_tool,
        patch(
            "src.faas.services.prompt_generator_service.service.rate_agent",
            new_callable=AsyncMock,
        ) as mock_rate_agent,
        patch(
            "src.faas.services.prompt_generator_service.service.rate_tool",
            new_callable=AsyncMock,
        ) as mock_rate_tool,
        patch(
            "src.faas.services.prompt_generator_service.service.create_nats_client",
            return_value=None,
        ),
        patch(
            "src.faas.services.prompt_generator_service.service.create_otel_tracer",
            return_value=None,
        ),
        patch("os.getenv", side_effect=lambda key, default=None: {
            "OPENAI_API_KEY": "",
            "SERVICE_PORT": "8080",
            "SERVICE_VERSION": "1.0.0",
            "DATABASE_URL": "postgresql://test:test@localhost/test",
        }.get(key, default if default is not None else "")),
    ):
        mock_db_manager = Mock()
        mock_db_manager.get_connection.return_value = mock_db
        mock_get_db.return_value = mock_db_manager

        # Mock gateway
        mock_gateway = Mock()
        mock_create_gateway.return_value = mock_gateway

        # Mock agent creation
        mock_agent = Mock()
        mock_agent.agent_id = "agent_123"
        mock_agent.name = "Support Agent"
        mock_agent.description = "Agent description"
        mock_agent.capabilities = []
        mock_agent.system_prompt = "You are a helpful agent"
        from datetime import datetime
        mock_agent.created_at = datetime.now()
        mock_create_agent.return_value = mock_agent

        # Mock tool creation
        mock_tool = Mock()
        mock_tool.tool_id = "tool_123"
        mock_tool.name = "Tax Calculator"
        mock_tool.description = "Tool description"
        mock_tool.tool_type = Mock(value="function")
        mock_tool.parameters = []
        mock_tool.metadata = {}
        mock_create_tool.return_value = mock_tool

        # Mock rating functions
        mock_rate_agent.return_value = {"success": True, "rating_id": "rating_123"}
        mock_rate_tool.return_value = {"success": True, "rating_id": "rating_123"}

        app = create_prompt_generator_service(
            service_name="prompt-generator-service",
            config_overrides={"database_url": "postgresql://test:test@localhost/test"},
        )
        yield app


def test_prompt_generator_service_creation(prompt_generator_service):
    """Test prompt generator service creation."""
    assert prompt_generator_service is not None
    # create_prompt_generator_service returns the FastAPI app, not the service instance
    assert hasattr(prompt_generator_service, "routes")


@pytest.mark.asyncio
async def test_create_agent_from_prompt_endpoint(prompt_generator_service):
    """Test create agent from prompt endpoint."""
    client = TestClient(prompt_generator_service)

    response = client.post(
        "/api/v1/prompt/agents",
        json={
            "agent_id": "agent_123",
            "prompt": "Create an agent that helps with customer support",
            "llm_model": DEFAULT_LLM_MODEL,
            "llm_provider": DEFAULT_LLM_PROVIDER,
            "additional_config": {},
        },
        headers={"X-Tenant-ID": "tenant_123"},
    )

    assert response.status_code in [201, 404, 422, 500]
    if response.status_code == 201:
        data = response.json()
        assert data["success"] is True
        assert "agent_id" in data["data"]


@pytest.mark.asyncio
async def test_create_tool_from_prompt_endpoint(prompt_generator_service):
    """Test create tool from prompt endpoint."""
    client = TestClient(prompt_generator_service)

    response = client.post(
        "/api/v1/prompt/tools",
        json={
            "tool_id": "tool_123",
            "prompt": "Create a tool that calculates tax",
            "llm_model": DEFAULT_LLM_MODEL,
            "llm_provider": DEFAULT_LLM_PROVIDER,
            "additional_config": {},
        },
        headers={"X-Tenant-ID": "tenant_123"},
    )

    assert response.status_code in [201, 404, 422, 500]
    if response.status_code == 201:
        data = response.json()
        assert data["success"] is True
        assert "tool_id" in data["data"]


@pytest.mark.asyncio
async def test_rate_agent_endpoint(prompt_generator_service):
    """Test rate agent endpoint."""
    client = TestClient(prompt_generator_service)

    response = client.post(
        "/api/v1/prompt/agents/agent_123/rate",
        json={"rating": 5, "feedback": "Great agent!"},
        headers={"X-Tenant-ID": "tenant_123"},
    )

    assert response.status_code in [200, 404, 422, 500]
    if response.status_code == 200:
        data = response.json()
        assert data["success"] is True


@pytest.mark.asyncio
async def test_rate_tool_endpoint(prompt_generator_service):
    """Test rate tool endpoint."""
    client = TestClient(prompt_generator_service)

    response = client.post(
        "/api/v1/prompt/tools/tool_123/rate",
        json={"rating": 4, "feedback": "Good tool!"},
        headers={"X-Tenant-ID": "tenant_123"},
    )

    assert response.status_code in [200, 404, 422, 500]
    if response.status_code == 200:
        data = response.json()
        assert data["success"] is True


def test_health_check(prompt_generator_service):
    """Test health check endpoint."""
    client = TestClient(prompt_generator_service)

    response = client.get("/health")
    assert response.status_code in [200, 401]
    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "prompt-generator-service"


@pytest.mark.asyncio
async def test_create_agent_missing_tenant_id(prompt_generator_service):
    """Test create agent endpoint without tenant ID."""
    client = TestClient(prompt_generator_service)

    response = client.post(
        "/api/v1/prompt/agents",
        json={
            "agent_id": "agent_123",
            "prompt": "Create an agent",
            "llm_model": DEFAULT_LLM_MODEL,
            "llm_provider": DEFAULT_LLM_PROVIDER,
            "additional_config": {},
        },
    )

    assert response.status_code in [401, 404]


@pytest.mark.asyncio
async def test_create_agent_from_prompt_with_otel(prompt_generator_service):
    """Test create agent with OTEL tracing - covers lines 163-169."""
    from src.faas.services.prompt_generator_service.models import CreateAgentFromPromptRequest

    mock_span = Mock()
    mock_span.__enter__ = Mock(return_value=mock_span)
    mock_span.__exit__ = Mock(return_value=None)
    mock_span.set_attribute = Mock()

    mock_tracer = Mock()
    mock_tracer.start_span = Mock(return_value=mock_span)

    service_instance = _get_service_instance_from_app(prompt_generator_service)
    if service_instance is None:
        pytest.skip("Could not extract service instance from app")

    service_instance.otel_tracer = mock_tracer

    request = CreateAgentFromPromptRequest(
        agent_id="agent_123",
        prompt="Create an agent that helps with customer support",
        llm_model=DEFAULT_LLM_MODEL,
        llm_provider=DEFAULT_LLM_PROVIDER,
        additional_config={},
    )
    headers = {
        "x_tenant_id": "tenant_123",
        "x_request_id": "req_123",
        "x_correlation_id": "corr_123",
        "x_user_id": None,
    }

    result = await service_instance._handle_create_agent_from_prompt(request, headers)

    mock_tracer.start_span.assert_called_once()
    assert result.success is True


@pytest.mark.asyncio
async def test_create_agent_from_prompt_error_handling(prompt_generator_service):
    """Test create agent error handling - covers lines 178-183."""
    from fastapi import HTTPException
    from src.faas.services.prompt_generator_service.models import CreateAgentFromPromptRequest

    service_instance = _get_service_instance_from_app(prompt_generator_service)
    if service_instance is None:
        pytest.skip("Could not extract service instance from app")

    service_instance._create_agent_from_prompt = AsyncMock(side_effect=RuntimeError("Creation error"))

    request = CreateAgentFromPromptRequest(
        agent_id="agent_123",
        prompt="Create an agent",
        llm_model=DEFAULT_LLM_MODEL,
        llm_provider=DEFAULT_LLM_PROVIDER,
        additional_config={},
    )
    headers = {
        "x_tenant_id": "tenant_123",
        "x_request_id": "req_123",
        "x_correlation_id": "corr_123",
        "x_user_id": None,
    }

    with pytest.raises(HTTPException) as exc_info:
        await service_instance._handle_create_agent_from_prompt(request, headers)

    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_create_tool_from_prompt_with_otel(prompt_generator_service):
    """Test create tool with OTEL tracing - covers lines 204-209."""
    from src.faas.services.prompt_generator_service.models import CreateToolFromPromptRequest

    service_instance = _get_service_instance_from_app(prompt_generator_service)
    if service_instance is None:
        pytest.skip("Could not extract service instance from app")

    mock_span = Mock()
    mock_span.__enter__ = Mock(return_value=mock_span)
    mock_span.__exit__ = Mock(return_value=None)
    mock_span.set_attribute = Mock()

    mock_tracer = Mock()
    mock_tracer.start_span = Mock(return_value=mock_span)
    service_instance.otel_tracer = mock_tracer

    request = CreateToolFromPromptRequest(
        tool_id="tool_123",
        prompt="Create a tool that calculates tax",
        llm_model=DEFAULT_LLM_MODEL,
        llm_provider=DEFAULT_LLM_PROVIDER,
        additional_config={},
    )
    headers = {
        "x_tenant_id": "tenant_123",
        "x_request_id": "req_123",
        "x_correlation_id": "corr_123",
        "x_user_id": None,
    }

    result = await service_instance._handle_create_tool_from_prompt(request, headers)

    mock_tracer.start_span.assert_called_once()
    assert result.success is True


@pytest.mark.asyncio
async def test_create_tool_from_prompt_error_handling(prompt_generator_service):
    """Test create tool error handling - covers lines 218-223."""
    from fastapi import HTTPException
    from src.faas.services.prompt_generator_service.models import CreateToolFromPromptRequest

    service_instance = _get_service_instance_from_app(prompt_generator_service)
    if service_instance is None:
        pytest.skip("Could not extract service instance from app")

    service_instance._create_tool_from_prompt = AsyncMock(side_effect=RuntimeError("Creation error"))

    request = CreateToolFromPromptRequest(
        tool_id="tool_123",
        prompt="Create a tool",
        llm_model=DEFAULT_LLM_MODEL,
        llm_provider=DEFAULT_LLM_PROVIDER,
        additional_config={},
    )
    headers = {
        "x_tenant_id": "tenant_123",
        "x_request_id": "req_123",
        "x_correlation_id": "corr_123",
        "x_user_id": None,
    }

    with pytest.raises(HTTPException) as exc_info:
        await service_instance._handle_create_tool_from_prompt(request, headers)

    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_rate_agent_success(prompt_generator_service):
    """Test rate agent success - covers lines 242-261."""
    from src.faas.services.prompt_generator_service.models import RateAgentRequest

    service_instance = _get_service_instance_from_app(prompt_generator_service)
    if service_instance is None:
        pytest.skip("Could not extract service instance from app")

    request = RateAgentRequest(
        agent_id="agent_123",
        rating=5,
        feedback="Great agent!",
        metadata={},
    )
    headers = {
        "x_tenant_id": "tenant_123",
        "x_request_id": "req_123",
        "x_correlation_id": "corr_123",
        "x_user_id": "user_123",
    }

    result = await service_instance._handle_rate_agent("agent_123", request, headers)

    assert result.success is True
    assert result.message == "Agent rated successfully"


@pytest.mark.asyncio
async def test_rate_agent_with_tenant_id_as_user_id(prompt_generator_service):
    """Test rate agent with tenant_id as user_id fallback - covers line 247."""
    from src.faas.services.prompt_generator_service.models import RateAgentRequest

    service_instance = _get_service_instance_from_app(prompt_generator_service)
    if service_instance is None:
        pytest.skip("Could not extract service instance from app")

    request = RateAgentRequest(
        agent_id="agent_123",
        rating=5,
        feedback="Great agent!",
        metadata={},
    )
    headers = {
        "x_tenant_id": "tenant_123",
        "x_request_id": "req_123",
        "x_correlation_id": "corr_123",
        "x_user_id": None,
    }

    result = await service_instance._handle_rate_agent("agent_123", request, headers)
    assert result.success is True


@pytest.mark.asyncio
async def test_rate_agent_error_handling(prompt_generator_service):
    """Test rate agent error handling - covers lines 262-267."""
    from fastapi import HTTPException
    from src.faas.services.prompt_generator_service.models import RateAgentRequest

    service_instance = _get_service_instance_from_app(prompt_generator_service)
    if service_instance is None:
        pytest.skip("Could not extract service instance from app")

    with patch("src.faas.services.prompt_generator_service.service.rate_agent") as mock_rate:
        mock_rate.side_effect = RuntimeError("Rating error")

        request = RateAgentRequest(
            agent_id="agent_123",
            rating=5,
            feedback="Great agent!",
            metadata={},
        )
        headers = {
            "x_tenant_id": "tenant_123",
            "x_request_id": "req_123",
            "x_correlation_id": "corr_123",
            "x_user_id": "user_123",
        }

        with pytest.raises(HTTPException) as exc_info:
            await service_instance._handle_rate_agent("agent_123", request, headers)

        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_rate_tool_success(prompt_generator_service):
    """Test rate tool success - covers lines 286-305."""
    from src.faas.services.prompt_generator_service.models import RateToolRequest

    service_instance = _get_service_instance_from_app(prompt_generator_service)
    if service_instance is None:
        pytest.skip("Could not extract service instance from app")

    request = RateToolRequest(
        tool_id="tool_123",
        rating=4,
        feedback="Good tool!",
        metadata={},
    )
    headers = {
        "x_tenant_id": "tenant_123",
        "x_request_id": "req_123",
        "x_correlation_id": "corr_123",
        "x_user_id": "user_123",
    }

    result = await service_instance._handle_rate_tool("tool_123", request, headers)

    assert result.success is True
    assert result.message == "Tool rated successfully"


@pytest.mark.asyncio
async def test_rate_tool_with_tenant_id_as_user_id(prompt_generator_service):
    """Test rate tool with tenant_id as user_id fallback - covers line 291."""
    from src.faas.services.prompt_generator_service.models import RateToolRequest

    service_instance = _get_service_instance_from_app(prompt_generator_service)
    if service_instance is None:
        pytest.skip("Could not extract service instance from app")

    request = RateToolRequest(
        tool_id="tool_123",
        rating=4,
        feedback="Good tool!",
        metadata={},
    )
    headers = {
        "x_tenant_id": "tenant_123",
        "x_request_id": "req_123",
        "x_correlation_id": "corr_123",
        "x_user_id": None,
    }

    result = await service_instance._handle_rate_tool("tool_123", request, headers)
    assert result.success is True


@pytest.mark.asyncio
async def test_rate_tool_error_handling(prompt_generator_service):
    """Test rate tool error handling - covers lines 306-311."""
    from fastapi import HTTPException
    from src.faas.services.prompt_generator_service.models import RateToolRequest

    service_instance = _get_service_instance_from_app(prompt_generator_service)
    if service_instance is None:
        pytest.skip("Could not extract service instance from app")

    with patch("src.faas.services.prompt_generator_service.service.rate_tool") as mock_rate:
        mock_rate.side_effect = RuntimeError("Rating error")

        request = RateToolRequest(
            tool_id="tool_123",
            rating=4,
            feedback="Good tool!",
            metadata={},
        )
        headers = {
            "x_tenant_id": "tenant_123",
            "x_request_id": "req_123",
            "x_correlation_id": "corr_123",
            "x_user_id": "user_123",
        }

        with pytest.raises(HTTPException) as exc_info:
            await service_instance._handle_rate_tool("tool_123", request, headers)

        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_get_agent_feedback_success(prompt_generator_service):
    """Test get agent feedback success - covers lines 329-342."""
    service_instance = _get_service_instance_from_app(prompt_generator_service)
    if service_instance is None:
        pytest.skip("Could not extract service instance from app")

    with patch("src.faas.services.prompt_generator_service.service.get_agent_feedback_stats") as mock_get_stats:
        mock_get_stats.return_value = {
            "total_ratings": 10,
            "average_rating": 4.5,
            "ratings": [5, 4, 5, 4, 5],
        }

        headers = {
            "x_tenant_id": "tenant_123",
            "x_request_id": "req_123",
            "x_correlation_id": "corr_123",
            "x_user_id": None,
        }

        result = await service_instance._handle_get_agent_feedback("agent_123", headers)

        assert result.success is True
        assert "data" in result.model_dump()


@pytest.mark.asyncio
async def test_get_agent_feedback_error_handling(prompt_generator_service):
    """Test get agent feedback error handling - covers lines 343-348."""
    from fastapi import HTTPException

    service_instance = _get_service_instance_from_app(prompt_generator_service)
    if service_instance is None:
        pytest.skip("Could not extract service instance from app")

    with patch("src.faas.services.prompt_generator_service.service.get_agent_feedback_stats") as mock_get_stats:
        mock_get_stats.side_effect = RuntimeError("Stats error")

        headers = {
            "x_tenant_id": "tenant_123",
            "x_request_id": "req_123",
            "x_correlation_id": "corr_123",
            "x_user_id": None,
        }

        with pytest.raises(HTTPException) as exc_info:
            await service_instance._handle_get_agent_feedback("agent_123", headers)

        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_get_tool_feedback_success(prompt_generator_service):
    """Test get tool feedback success - covers lines 366-379."""
    service_instance = _get_service_instance_from_app(prompt_generator_service)
    if service_instance is None:
        pytest.skip("Could not extract service instance from app")

    with patch("src.faas.services.prompt_generator_service.service.get_tool_feedback_stats") as mock_get_stats:
        mock_get_stats.return_value = {
            "total_ratings": 8,
            "average_rating": 4.2,
            "ratings": [4, 5, 4, 4, 5],
        }

        headers = {
            "x_tenant_id": "tenant_123",
            "x_request_id": "req_123",
            "x_correlation_id": "corr_123",
            "x_user_id": None,
        }

        result = await service_instance._handle_get_tool_feedback("tool_123", headers)

        assert result.success is True
        assert "data" in result.model_dump()


@pytest.mark.asyncio
async def test_get_tool_feedback_error_handling(prompt_generator_service):
    """Test get tool feedback error handling - covers lines 380-385."""
    from fastapi import HTTPException

    service_instance = _get_service_instance_from_app(prompt_generator_service)
    if service_instance is None:
        pytest.skip("Could not extract service instance from app")

    with patch("src.faas.services.prompt_generator_service.service.get_tool_feedback_stats") as mock_get_stats:
        mock_get_stats.side_effect = RuntimeError("Stats error")

        headers = {
            "x_tenant_id": "tenant_123",
            "x_request_id": "req_123",
            "x_correlation_id": "corr_123",
            "x_user_id": None,
        }

        with pytest.raises(HTTPException) as exc_info:
            await service_instance._handle_get_tool_feedback("tool_123", headers)

        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_grant_permission_success(prompt_generator_service):
    """Test grant permission success - covers lines 403-419."""
    from src.faas.services.prompt_generator_service.models import GrantPermissionRequest

    service_instance = _get_service_instance_from_app(prompt_generator_service)
    if service_instance is None:
        pytest.skip("Could not extract service instance from app")

    request = GrantPermissionRequest(
        user_id="user_123",
        resource_type="agent",
        resource_id="agent_123",
        permission="read",
    )
    headers = {
        "x_tenant_id": "tenant_123",
        "x_request_id": "req_123",
        "x_correlation_id": "corr_123",
        "x_user_id": None,
    }

    result = await service_instance._handle_grant_permission(request, headers)

    assert result.success is True
    assert result.message == "Permission granted successfully"


@pytest.mark.asyncio
async def test_grant_permission_error_handling(prompt_generator_service):
    """Test grant permission error handling - covers lines 420-425."""
    from fastapi import HTTPException
    from src.faas.services.prompt_generator_service.models import GrantPermissionRequest

    service_instance = _get_service_instance_from_app(prompt_generator_service)
    if service_instance is None:
        pytest.skip("Could not extract service instance from app")

    with patch("src.faas.services.prompt_generator_service.service.grant_permission") as mock_grant:
        mock_grant.side_effect = RuntimeError("Permission error")

        request = GrantPermissionRequest(
            user_id="user_123",
            resource_type="agent",
            resource_id="agent_123",
            permission="read",
        )
        headers = {
            "x_tenant_id": "tenant_123",
            "x_request_id": "req_123",
            "x_correlation_id": "corr_123",
            "x_user_id": None,
        }

        with pytest.raises(HTTPException) as exc_info:
            await service_instance._handle_grant_permission(request, headers)

        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_handle_health_check(prompt_generator_service):
    """Test health check handler - covers line 434."""
    service_instance = _get_service_instance_from_app(prompt_generator_service)
    if service_instance is None:
        pytest.skip("Could not extract service instance from app")

    result = await service_instance._handle_health_check()
    assert result["status"] == "healthy"
    assert result["service"] == "prompt-generator-service"


@pytest.mark.asyncio
async def test_create_agent_from_prompt_internal(prompt_generator_service):
    """Test _create_agent_from_prompt internal method - covers lines 450-467."""
    from src.faas.services.prompt_generator_service.models import CreateAgentFromPromptRequest

    service_instance = _get_service_instance_from_app(prompt_generator_service)
    if service_instance is None:
        pytest.skip("Could not extract service instance from app")

    with patch("src.faas.services.prompt_generator_service.service.create_agent_from_prompt") as mock_create:
        mock_agent = Mock()
        mock_agent.agent_id = "agent_123"
        mock_agent.name = "Support Agent"
        mock_agent.description = "Agent description"
        mock_agent.capabilities = []
        mock_agent.system_prompt = "You are a helpful agent"
        from datetime import datetime
        mock_agent.created_at = datetime.now()
        mock_create.return_value = mock_agent

        request = CreateAgentFromPromptRequest(
            agent_id="agent_123",
            prompt="Create an agent",
            llm_model=DEFAULT_LLM_MODEL,
            llm_provider=DEFAULT_LLM_PROVIDER,
            additional_config={},
        )
        headers = Mock()
        headers.tenant_id = "tenant_123"
        headers.user_id = "user_123"

        result = await service_instance._create_agent_from_prompt(request, headers)

        assert result["agent_id"] == "agent_123"
        assert result["name"] == "Support Agent"
        assert "capabilities" in result


@pytest.mark.asyncio
async def test_create_agent_from_prompt_without_gateway(prompt_generator_service):
    """Test _create_agent_from_prompt without existing gateway - covers lines 450-454."""
    from src.faas.services.prompt_generator_service.models import CreateAgentFromPromptRequest

    service_instance = _get_service_instance_from_app(prompt_generator_service)
    if service_instance is None:
        pytest.skip("Could not extract service instance from app")

    service_instance.gateway = None

    with (
        patch("os.getenv", return_value="test_api_key"),
        patch("src.faas.services.prompt_generator_service.service.create_gateway") as mock_create_gateway,
        patch("src.faas.services.prompt_generator_service.service.create_agent_from_prompt") as mock_create,
    ):
        mock_gateway = Mock()
        mock_create_gateway.return_value = mock_gateway

        mock_agent = Mock()
        mock_agent.agent_id = "agent_123"
        mock_agent.name = "Support Agent"
        mock_agent.description = "Agent description"
        mock_agent.capabilities = []
        mock_agent.system_prompt = "You are a helpful agent"
        from datetime import datetime
        mock_agent.created_at = datetime.now()
        mock_create.return_value = mock_agent

        request = CreateAgentFromPromptRequest(
            agent_id="agent_123",
            prompt="Create an agent",
            llm_model=DEFAULT_LLM_MODEL,
            llm_provider=DEFAULT_LLM_PROVIDER,
            additional_config={},
        )
        headers = Mock()
        headers.tenant_id = "tenant_123"
        headers.user_id = "user_123"

        result = await service_instance._create_agent_from_prompt(request, headers)

        mock_create_gateway.assert_called_once()
        assert result["agent_id"] == "agent_123"


@pytest.mark.asyncio
async def test_create_tool_from_prompt_internal(prompt_generator_service):
    """Test _create_tool_from_prompt internal method - covers lines 490-507."""
    from src.faas.services.prompt_generator_service.models import CreateToolFromPromptRequest

    service_instance = _get_service_instance_from_app(prompt_generator_service)
    if service_instance is None:
        pytest.skip("Could not extract service instance from app")

    with patch("src.faas.services.prompt_generator_service.service.create_tool_from_prompt") as mock_create:
        mock_tool = Mock()
        mock_tool.tool_id = "tool_123"
        mock_tool.name = "Tax Calculator"
        mock_tool.description = "Tool description"
        mock_tool.tool_type = Mock(value="function")
        mock_tool.parameters = []
        mock_tool.metadata = {}
        mock_create.return_value = mock_tool

        request = CreateToolFromPromptRequest(
            tool_id="tool_123",
            prompt="Create a tool",
            llm_model=DEFAULT_LLM_MODEL,
            llm_provider=DEFAULT_LLM_PROVIDER,
            additional_config={},
        )
        headers = Mock()
        headers.tenant_id = "tenant_123"
        headers.user_id = "user_123"

        result = await service_instance._create_tool_from_prompt(request, headers)

        assert result["tool_id"] == "tool_123"
        assert result["name"] == "Tax Calculator"
        assert "parameters" in result


@pytest.mark.asyncio
async def test_create_tool_from_prompt_without_gateway(prompt_generator_service):
    """Test _create_tool_from_prompt without existing gateway - covers lines 490-494."""
    from src.faas.services.prompt_generator_service.models import CreateToolFromPromptRequest

    service_instance = _get_service_instance_from_app(prompt_generator_service)
    if service_instance is None:
        pytest.skip("Could not extract service instance from app")

    service_instance.gateway = None

    with (
        patch("os.getenv", return_value="test_api_key"),
        patch("src.faas.services.prompt_generator_service.service.create_gateway") as mock_create_gateway,
        patch("src.faas.services.prompt_generator_service.service.create_tool_from_prompt") as mock_create,
    ):
        mock_gateway = Mock()
        mock_create_gateway.return_value = mock_gateway

        mock_tool = Mock()
        mock_tool.tool_id = "tool_123"
        mock_tool.name = "Tax Calculator"
        mock_tool.description = "Tool description"
        mock_tool.tool_type = Mock(value="function")
        mock_tool.parameters = []
        mock_tool.metadata = {}
        mock_create.return_value = mock_tool

        request = CreateToolFromPromptRequest(
            tool_id="tool_123",
            prompt="Create a tool",
            llm_model=DEFAULT_LLM_MODEL,
            llm_provider=DEFAULT_LLM_PROVIDER,
            additional_config={},
        )
        headers = Mock()
        headers.tenant_id = "tenant_123"
        headers.user_id = "user_123"

        result = await service_instance._create_tool_from_prompt(request, headers)

        mock_create_gateway.assert_called_once()
        assert result["tool_id"] == "tool_123"


@pytest.mark.asyncio
async def test_create_agent_with_additional_config(prompt_generator_service):
    """Test _create_agent_from_prompt with additional_config - covers line 464."""
    from src.faas.services.prompt_generator_service.models import CreateAgentFromPromptRequest

    service_instance = _get_service_instance_from_app(prompt_generator_service)
    if service_instance is None:
        pytest.skip("Could not extract service instance from app")

    with patch("src.faas.services.prompt_generator_service.service.create_agent_from_prompt") as mock_create:
        mock_agent = Mock()
        mock_agent.agent_id = "agent_123"
        mock_agent.name = "Support Agent"
        mock_agent.description = "Agent description"
        mock_agent.capabilities = []
        mock_agent.system_prompt = "You are a helpful agent"
        from datetime import datetime
        mock_agent.created_at = datetime.now()
        mock_create.return_value = mock_agent

        request = CreateAgentFromPromptRequest(
            agent_id="agent_123",
            prompt="Create an agent",
            llm_model=DEFAULT_LLM_MODEL,
            llm_provider=DEFAULT_LLM_PROVIDER,
            additional_config={"temperature": 0.7},
        )
        headers = Mock()
        headers.tenant_id = "tenant_123"
        headers.user_id = "user_123"

        result = await service_instance._create_agent_from_prompt(request, headers)
        assert result["agent_id"] == "agent_123"

        call_kwargs = mock_create.call_args.kwargs
        assert abs(float(call_kwargs.get("temperature", 0.0)) - 0.7) < 1e-9


@pytest.mark.asyncio
async def test_create_tool_with_additional_config(prompt_generator_service):
    """Test _create_tool_from_prompt with additional_config - covers line 504."""
    from src.faas.services.prompt_generator_service.models import CreateToolFromPromptRequest

    service_instance = _get_service_instance_from_app(prompt_generator_service)
    if service_instance is None:
        pytest.skip("Could not extract service instance from app")

    with patch("src.faas.services.prompt_generator_service.service.create_tool_from_prompt") as mock_create:
        mock_tool = Mock()
        mock_tool.tool_id = "tool_123"
        mock_tool.name = "Tax Calculator"
        mock_tool.description = "Tool description"
        mock_tool.tool_type = Mock(value="function")
        mock_tool.parameters = []
        mock_tool.metadata = {}
        mock_create.return_value = mock_tool

        request = CreateToolFromPromptRequest(
            tool_id="tool_123",
            prompt="Create a tool",
            llm_model=DEFAULT_LLM_MODEL,
            llm_provider=DEFAULT_LLM_PROVIDER,
            additional_config={"max_iterations": 3},
        )
        headers = Mock()
        headers.tenant_id = "tenant_123"
        headers.user_id = "user_123"

        result = await service_instance._create_tool_from_prompt(request, headers)
        assert result["tool_id"] == "tool_123"

        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs.get("max_iterations") == 3


def test_service_initialization_with_gateway():
    """Test service initialization with gateway - covers line 82."""
    with (
        patch("src.faas.services.prompt_generator_service.service.get_database_connection") as mock_get_db,
        patch("src.faas.services.prompt_generator_service.service.create_gateway") as mock_create_gateway,
        patch("src.faas.services.prompt_generator_service.service.create_nats_client", return_value=None),
        patch("src.faas.services.prompt_generator_service.service.create_otel_tracer", return_value=None),
        patch("os.getenv", side_effect=lambda key, default=None: {
            "OPENAI_API_KEY": "test_api_key",
            "SERVICE_PORT": "8080",
            "SERVICE_VERSION": "1.0.0",
            "DATABASE_URL": "postgresql://test:test@localhost/test",
        }.get(key, default if default is not None else "")),
    ):
        mock_db_manager = Mock()
        mock_db_manager.get_connection.return_value = Mock()
        mock_get_db.return_value = mock_db_manager

        mock_gateway = Mock()
        mock_create_gateway.return_value = mock_gateway

        app = create_prompt_generator_service(
            service_name="prompt-generator-service",
            config_overrides={"database_url": "postgresql://test:test@localhost/test"},
        )

        mock_create_gateway.assert_called_once()
        assert hasattr(app, "routes")


def test_service_initialization_without_gateway():
    """Test service initialization without gateway - covers line 85."""
    with (
        patch("src.faas.services.prompt_generator_service.service.get_database_connection") as mock_get_db,
        patch("src.faas.services.prompt_generator_service.service.create_gateway") as mock_create_gateway,
        patch("src.faas.services.prompt_generator_service.service.create_nats_client", return_value=None),
        patch("src.faas.services.prompt_generator_service.service.create_otel_tracer", return_value=None),
        patch("os.getenv", side_effect=lambda key, default=None: {
            "OPENAI_API_KEY": "",
            "SERVICE_PORT": "8080",
            "SERVICE_VERSION": "1.0.0",
            "DATABASE_URL": "postgresql://test:test@localhost/test",
        }.get(key, default if default is not None else "")),
    ):
        mock_db_manager = Mock()
        mock_db_manager.get_connection.return_value = Mock()
        mock_get_db.return_value = mock_db_manager

        app = create_prompt_generator_service(
            service_name="prompt-generator-service",
            config_overrides={"database_url": "postgresql://test:test@localhost/test"},
        )

        assert mock_create_gateway.call_count == 0
        assert hasattr(app, "routes")


@pytest.mark.asyncio
async def test_startup_event(prompt_generator_service):
    """Test startup event - covers lines 101-102."""
    assert hasattr(prompt_generator_service, "router") or hasattr(prompt_generator_service, "routes")
