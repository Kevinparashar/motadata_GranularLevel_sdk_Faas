"""
Unit Tests for Agent DAL

Tests database operations for agent persistence.
Follows @cursorrules.md: Success ≥2, Edge ≥2, Failure ≥2
"""


import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.faas.shared.dal.agent_dal import AgentDAL


class TestAgentDAL:
    """Test AgentDAL class."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database connection."""
        db = MagicMock()
        db.execute_query = AsyncMock()
        return db

    @pytest.fixture
    def agent_dal(self, mock_db):
        """Create an AgentDAL instance."""
        return AgentDAL(mock_db)

    # Success Cases (≥2)
    @pytest.mark.asyncio
    async def test_save_agent_success(self, agent_dal, mock_db):
        """Test successfully saving an agent."""
        await agent_dal.save_agent(
            agent_id="agent_123",
            tenant_id="tenant_456",
            name="Test Agent",
            description="Test description",
            llm_model="gpt-4",
            llm_provider="openai",
            system_prompt="You are helpful",
            capabilities=["search", "code"],
            config={"temperature": 0.7},
        )

        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        assert "INSERT INTO agents" in call_args[0][0]
        assert call_args[1]["params"][0] == "agent_123"
        assert call_args[1]["params"][1] == "tenant_456"
        assert call_args[1]["params"][2] == "Test Agent"

    @pytest.mark.asyncio
    async def test_load_agent_success(self, agent_dal, mock_db):
        """Test successfully loading an agent."""
        mock_db.execute_query.return_value = {
            "agent_id": "agent_123",
            "name": "Test Agent",
            "description": "Test description",
            "llm_model": "gpt-4",
            "llm_provider": "openai",
            "system_prompt": "You are helpful",
            "capabilities": json.dumps(["search", "code"]),
            "config": json.dumps({"temperature": 0.7}),
        }

        result = await agent_dal.load_agent("agent_123", "tenant_456")

        assert result is not None
        assert result["agent_id"] == "agent_123"
        assert result["name"] == "Test Agent"
        assert isinstance(result["capabilities"], list)
        assert isinstance(result["config"], dict)

    @pytest.mark.asyncio
    async def test_list_agents_success(self, agent_dal, mock_db):
        """Test successfully listing agents."""
        mock_db.execute_query.return_value = [
            {"agent_id": "agent_1", "name": "Agent 1"},
            {"agent_id": "agent_2", "name": "Agent 2"},
        ]

        result = await agent_dal.list_agents("tenant_456", limit=10, offset=0)

        assert len(result) == 2
        assert result[0]["agent_id"] == "agent_1"

    @pytest.mark.asyncio
    async def test_delete_agent_success(self, agent_dal, mock_db):
        """Test successfully deleting an agent."""
        mock_db.execute_query.return_value = 1  # 1 row deleted

        result = await agent_dal.delete_agent("agent_123", "tenant_456")

        assert result is True
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        assert "DELETE FROM agents" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_agent_exists_success(self, agent_dal, mock_db):
        """Test successfully checking agent existence."""
        mock_db.execute_query.return_value = {"1": 1}

        result = await agent_dal.agent_exists("agent_123", "tenant_456")

        assert result is True

    # Edge Cases (≥2)
    @pytest.mark.asyncio
    async def test_load_agent_with_string_json(self, agent_dal, mock_db):
        """Test loading agent with string JSON fields."""
        mock_db.execute_query.return_value = {
            "agent_id": "agent_123",
            "name": "Test Agent",
            "description": None,
            "llm_model": None,
            "llm_provider": None,
            "system_prompt": None,
            "capabilities": '["search"]',  # String JSON
            "config": '{"key": "value"}',  # String JSON
        }

        result = await agent_dal.load_agent("agent_123", "tenant_456")

        assert result is not None
        assert isinstance(result["capabilities"], list)
        assert isinstance(result["config"], dict)

    @pytest.mark.asyncio
    async def test_list_agents_empty_result(self, agent_dal, mock_db):
        """Test listing agents with empty result."""
        mock_db.execute_query.return_value = None

        result = await agent_dal.list_agents("tenant_456")

        assert result == []

    @pytest.mark.asyncio
    async def test_save_agent_with_none_values(self, agent_dal, mock_db):
        """Test saving agent with None values."""
        await agent_dal.save_agent(
            agent_id="agent_123",
            tenant_id="tenant_456",
            name="Test Agent",
            description=None,
            llm_model=None,
            llm_provider=None,
            system_prompt=None,
            capabilities=[],
            config={},
        )

        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_agent_not_found(self, agent_dal, mock_db):
        """Test deleting non-existent agent."""
        mock_db.execute_query.return_value = 0  # 0 rows deleted

        result = await agent_dal.delete_agent("nonexistent", "tenant_456")

        assert result is False

    @pytest.mark.asyncio
    async def test_agent_exists_not_found(self, agent_dal, mock_db):
        """Test checking existence of non-existent agent."""
        mock_db.execute_query.return_value = None

        result = await agent_dal.agent_exists("nonexistent", "tenant_456")

        assert result is False

    # Failure Cases (≥2)
    @pytest.mark.asyncio
    async def test_load_agent_not_found(self, agent_dal, mock_db):
        """Test loading non-existent agent."""
        mock_db.execute_query.return_value = None

        result = await agent_dal.load_agent("nonexistent", "tenant_456")

        assert result is None

    @pytest.mark.asyncio
    async def test_save_agent_database_error(self, agent_dal, mock_db):
        """Test saving agent with database error."""
        mock_db.execute_query.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            await agent_dal.save_agent(
                agent_id="agent_123",
                tenant_id="tenant_456",
                name="Test Agent",
                description="Test",
                llm_model="gpt-4",
                llm_provider="openai",
                system_prompt="Test",
                capabilities=[],
                config={},
            )

