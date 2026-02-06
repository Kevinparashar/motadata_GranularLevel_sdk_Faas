"""
Unit tests for AgentStorage.
"""


import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.core.agno_agent_framework import Agent
from src.core.litellm_gateway import LiteLLMGateway
from src.faas.shared.agent_storage import AgentStorage


@pytest.fixture
def mock_db():
    """Create mock database connection."""
    db = Mock()
    db.execute_query = AsyncMock(return_value=None)
    return db


@pytest.fixture
def agent_storage(mock_db):
    """Create AgentStorage instance for testing."""
    return AgentStorage(db_connection=mock_db)


@pytest.fixture
def mock_agent():
    """Create mock agent."""
    agent = Mock(spec=Agent)
    agent.agent_id = "test_agent_123"
    agent.name = "Test Agent"
    agent.description = "Test description"
    agent.llm_model = "gpt-4"
    agent.llm_provider = "openai"
    agent.system_prompt = "You are a helpful assistant"
    agent.capabilities = []
    agent.metadata = {}
    return agent


@pytest.fixture
def mock_gateway():
    """Create mock gateway."""
    return Mock(spec=LiteLLMGateway)


@pytest.mark.asyncio
async def test_ensure_table(agent_storage, mock_db):
    """Test _ensure_table creates table."""
    await agent_storage._ensure_table()
    
    # Verify execute_query was called
    assert mock_db.execute_query.called


@pytest.mark.asyncio
async def test_save_agent(agent_storage, mock_agent, mock_db):
    """Test save_agent."""
    await agent_storage.save_agent(agent=mock_agent, tenant_id="tenant_123")
    
    # Verify execute_query was called
    assert mock_db.execute_query.called
    
    # Verify INSERT query was executed
    call_args = mock_db.execute_query.call_args
    assert "INSERT INTO agents" in call_args[0][0] or "INSERT" in str(call_args)


@pytest.mark.asyncio
async def test_load_agent_exists(agent_storage, mock_gateway, mock_db):
    """Test load_agent when agent exists."""
    # Mock database row
    mock_row = {
        "agent_id": "test_agent_123",
        "name": "Test Agent",
        "description": "Test description",
        "llm_model": "gpt-4",
        "llm_provider": "openai",
        "system_prompt": "You are a helpful assistant",
        "capabilities": json.dumps(["capability1"]),
        "config": json.dumps({"key": "value"}),
    }
    
    mock_db.execute_query = AsyncMock(return_value=mock_row)
    
    with patch("src.faas.shared.agent_storage.create_agent") as mock_create_agent:
        mock_created_agent = Mock(spec=Agent)
        mock_created_agent.add_capability = Mock()
        mock_created_agent.metadata = {}
        mock_create_agent.return_value = mock_created_agent
        
        agent = await agent_storage.load_agent(
            agent_id="test_agent_123",
            tenant_id="tenant_123",
            gateway=mock_gateway,
        )
        
        assert agent is not None
        assert mock_create_agent.called


@pytest.mark.asyncio
async def test_load_agent_not_exists(agent_storage, mock_gateway, mock_db):
    """Test load_agent when agent does not exist."""
    mock_db.execute_query = AsyncMock(return_value=None)
    
    agent = await agent_storage.load_agent(
        agent_id="nonexistent_agent",
        tenant_id="tenant_123",
        gateway=mock_gateway,
    )
    
    assert agent is None


@pytest.mark.asyncio
async def test_list_agents(agent_storage, mock_db):
    """Test list_agents."""
    mock_results = [
        {
            "agent_id": "agent_1",
            "name": "Agent 1",
            "description": "Description 1",
            "llm_model": "gpt-4",
            "llm_provider": "openai",
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01",
        },
        {
            "agent_id": "agent_2",
            "name": "Agent 2",
            "description": "Description 2",
            "llm_model": "gpt-3.5",
            "llm_provider": "openai",
            "created_at": "2024-01-02",
            "updated_at": "2024-01-02",
        },
    ]
    
    mock_db.execute_query = AsyncMock(return_value=mock_results)
    
    agents = await agent_storage.list_agents(
        tenant_id="tenant_123",
        limit=10,
        offset=0,
    )
    
    assert len(agents) == 2
    assert agents[0]["agent_id"] == "agent_1"
    assert agents[1]["agent_id"] == "agent_2"


@pytest.mark.asyncio
async def test_list_agents_empty(agent_storage, mock_db):
    """Test list_agents when no agents exist."""
    mock_db.execute_query = AsyncMock(return_value=[])
    
    agents = await agent_storage.list_agents(
        tenant_id="tenant_123",
        limit=10,
        offset=0,
    )
    
    assert agents == []


@pytest.mark.asyncio
async def test_delete_agent_exists(agent_storage, mock_db):
    """Test delete_agent when agent exists."""
    mock_db.execute_query = AsyncMock(return_value=1)  # 1 row deleted
    
    result = await agent_storage.delete_agent(
        agent_id="test_agent_123",
        tenant_id="tenant_123",
    )
    
    assert result is True
    assert mock_db.execute_query.called


@pytest.mark.asyncio
async def test_delete_agent_not_exists(agent_storage, mock_db):
    """Test delete_agent when agent does not exist."""
    mock_db.execute_query = AsyncMock(return_value=0)  # 0 rows deleted
    
    result = await agent_storage.delete_agent(
        agent_id="nonexistent_agent",
        tenant_id="tenant_123",
    )
    
    assert result is False


@pytest.mark.asyncio
async def test_agent_exists_true(agent_storage, mock_db):
    """Test agent_exists when agent exists."""
    mock_db.execute_query = AsyncMock(return_value={"agent_id": "test_agent_123"})
    
    result = await agent_storage.agent_exists(
        agent_id="test_agent_123",
        tenant_id="tenant_123",
    )
    
    assert result is True


@pytest.mark.asyncio
async def test_agent_exists_false(agent_storage, mock_db):
    """Test agent_exists when agent does not exist."""
    mock_db.execute_query = AsyncMock(return_value=None)
    
    result = await agent_storage.agent_exists(
        agent_id="nonexistent_agent",
        tenant_id="tenant_123",
    )
    
    assert result is False


@pytest.mark.asyncio
async def test_save_agent_with_capabilities(agent_storage, mock_agent, mock_db):
    """Test save_agent with capabilities."""
    mock_capability = Mock()
    mock_capability.name = "test_capability"
    mock_agent.capabilities = [mock_capability]
    
    await agent_storage.save_agent(agent=mock_agent, tenant_id="tenant_123")
    
    assert mock_db.execute_query.called


@pytest.mark.asyncio
async def test_save_agent_with_metadata(agent_storage, mock_agent, mock_db):
    """Test save_agent with metadata."""
    mock_agent.metadata = {"key": "value", "nested": {"inner": "data"}}
    
    await agent_storage.save_agent(agent=mock_agent, tenant_id="tenant_123")
    
    assert mock_db.execute_query.called

