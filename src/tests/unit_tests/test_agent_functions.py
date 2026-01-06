"""
Unit Tests for Agent Framework Functions

Tests factory functions, convenience functions, and utilities for agent framework.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from typing import Dict, Any
from src.core.agno_agent_framework.functions import (
    # Factory functions
    create_agent,
    create_agent_with_memory,
    create_agent_manager,
    create_orchestrator,
    # Convenience functions
    chat_with_agent,
    execute_task,
    delegate_task,
    find_agents_by_capability,
    # Utility functions
    batch_process_agents,
    retry_on_failure,
    save_agent_state,
    load_agent_state,
)
from src.core.agno_agent_framework.agent import Agent, AgentManager, AgentTask, AgentStatus
from src.core.agno_agent_framework.session import AgentSession, SessionManager
from src.core.agno_agent_framework.memory import AgentMemory


class TestFactoryFunctions:
    """Test factory functions for agent creation."""
    
    @pytest.fixture
    def mock_gateway(self):
        """Mock LiteLLM Gateway."""
        return Mock()
    
    def test_create_agent(self, mock_gateway):
        """Test create_agent factory function."""
        agent = create_agent(
            agent_id="agent1",
            name="Test Agent",
            gateway=mock_gateway,
            description="Test description",
            llm_model="gpt-4",
            llm_provider="openai"
        )
        
        assert isinstance(agent, Agent)
        assert agent.agent_id == "agent1"
        assert agent.name == "Test Agent"
        assert agent.description == "Test description"
        assert agent.llm_model == "gpt-4"
        assert agent.llm_provider == "openai"
    
    def test_create_agent_with_defaults(self, mock_gateway):
        """Test create_agent with default parameters."""
        agent = create_agent("agent1", "Agent", mock_gateway)
        
        assert agent.agent_id == "agent1"
        assert agent.name == "Agent"
        assert agent.description == ""
        assert agent.llm_model is None
        assert agent.llm_provider is None
    
    def test_create_agent_with_kwargs(self, mock_gateway):
        """Test create_agent with additional kwargs."""
        agent = create_agent(
            "agent1", "Agent", mock_gateway,
            custom_param="value"
        )
        
        # Verify agent was created (kwargs passed to Agent constructor)
        assert agent.agent_id == "agent1"
    
    def test_create_agent_with_memory(self, mock_gateway):
        """Test create_agent_with_memory factory function."""
        memory_config = {
            "persistence_path": "/tmp/test_memory.json",
            "max_short_term": 100,
            "max_long_term": 2000
        }
        
        agent = create_agent_with_memory(
            agent_id="agent1",
            name="Agent with Memory",
            gateway=mock_gateway,
            memory_config=memory_config
        )
        
        assert isinstance(agent, Agent)
        assert agent.agent_id == "agent1"
        # Memory should be attached
        assert agent.memory is not None
    
    def test_create_agent_with_memory_no_config(self, mock_gateway):
        """Test create_agent_with_memory without memory config."""
        agent = create_agent_with_memory(
            agent_id="agent1",
            name="Agent",
            gateway=mock_gateway,
            memory_config=None
        )
        
        assert isinstance(agent, Agent)
        assert agent.agent_id == "agent1"
    
    def test_create_agent_manager(self):
        """Test create_agent_manager factory function."""
        manager = create_agent_manager()
        
        assert isinstance(manager, AgentManager)
        assert len(manager.list_agents()) == 0
    
    def test_create_orchestrator(self):
        """Test create_orchestrator factory function."""
        manager = create_agent_manager()
        orchestrator = create_orchestrator(manager)
        
        assert orchestrator is not None
        assert orchestrator.agent_manager == manager


class TestConvenienceFunctions:
    """Test high-level convenience functions."""
    
    @pytest.fixture
    def mock_gateway(self):
        """Mock LiteLLM Gateway."""
        gateway = Mock()
        gateway.generate_async = AsyncMock(return_value=Mock(
            text="Test response",
            model="gpt-4"
        ))
        return gateway
    
    @pytest.fixture
    def mock_agent(self, mock_gateway):
        """Create a mock agent."""
        agent = Mock(spec=Agent)
        agent.agent_id = "agent1"
        agent.name = "Test Agent"
        agent.status = AgentStatus.IDLE
        agent.gateway = mock_gateway
        agent.execute_task = AsyncMock(return_value={"result": "Task completed"})
        return agent
    
    @pytest.fixture
    def session_manager(self):
        """Create a session manager."""
        return SessionManager()
    
    @pytest.mark.asyncio
    async def test_chat_with_agent(self, mock_agent, session_manager):
        """Test chat_with_agent convenience function."""
        mock_agent.execute_task = AsyncMock(return_value={
            "result": "Hello! How can I help you?"
        })
        
        response = await chat_with_agent(
            agent=mock_agent,
            message="Hello",
            session_manager=session_manager
        )
        
        assert response == "Hello! How can I help you?"
        mock_agent.execute_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_chat_with_agent_existing_session(self, mock_agent, session_manager):
        """Test chat_with_agent with existing session."""
        session = session_manager.create_session("agent1", max_history=10)
        session_id = session.session_id
        
        mock_agent.execute_task = AsyncMock(return_value={
            "result": "Response"
        })
        
        response = await chat_with_agent(
            agent=mock_agent,
            message="Hello",
            session_manager=session_manager,
            session_id=session_id
        )
        
        assert response == "Response"
    
    @pytest.mark.asyncio
    async def test_execute_task(self, mock_agent):
        """Test execute_task convenience function."""
        result = await execute_task(
            agent=mock_agent,
            task_type="analyze",
            parameters={"text": "Test text"},
            priority=1
        )
        
        assert result == {"result": "Task completed"}
        mock_agent.execute_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_task_default_priority(self, mock_agent):
        """Test execute_task with default priority."""
        await execute_task(
            agent=mock_agent,
            task_type="test",
            parameters={}
        )
        
        mock_agent.execute_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delegate_task(self):
        """Test delegate_task convenience function."""
        agent1 = Mock(spec=Agent)
        agent1.agent_id = "agent1"
        agent1.execute_task = AsyncMock(return_value={"result": "Delegated"})
        
        agent2 = Mock(spec=Agent)
        agent2.agent_id = "agent2"
        agent2.execute_task = AsyncMock(return_value={"result": "Completed"})
        
        manager = Mock()
        manager.get_agent = Mock(return_value=agent2)
        
        result = await delegate_task(
            from_agent=agent1,
            to_agent_id="agent2",
            agent_manager=manager,
            task_type="process",
            parameters={"data": "test"}
        )
        
        assert result == {"result": "Completed"}
        manager.get_agent.assert_called_once_with("agent2")
        agent2.execute_task.assert_called_once()
    
    def test_find_agents_by_capability(self):
        """Test find_agents_by_capability convenience function."""
        agent1 = Mock(spec=Agent)
        agent1.agent_id = "agent1"
        agent1.has_capability = Mock(return_value=True)
        
        agent2 = Mock(spec=Agent)
        agent2.agent_id = "agent2"
        agent2.has_capability = Mock(return_value=False)
        
        manager = Mock()
        manager.list_agents = Mock(return_value=["agent1", "agent2"])
        manager.get_agent = Mock(side_effect=lambda x: agent1 if x == "agent1" else agent2)
        
        agents = find_agents_by_capability(
            agent_manager=manager,
            capability_name="analysis"
        )
        
        assert len(agents) == 1
        assert agents[0].agent_id == "agent1"


class TestUtilityFunctions:
    """Test utility functions."""
    
    @pytest.mark.asyncio
    async def test_batch_process_agents(self):
        """Test batch_process_agents utility function."""
        agent1 = Mock(spec=Agent)
        agent1.agent_id = "agent1"
        agent1.execute_task = AsyncMock(return_value={"result": "Result 1"})
        
        agent2 = Mock(spec=Agent)
        agent2.agent_id = "agent2"
        agent2.execute_task = AsyncMock(return_value={"result": "Result 2"})
        
        results = await batch_process_agents(
            agents=[agent1, agent2],
            task_type="process",
            parameters={"data": "test"}
        )
        
        assert len(results) == 2
        assert results[0]["result"] == "Result 1"
        assert results[1]["result"] == "Result 2"
        agent1.execute_task.assert_called_once()
        agent2.execute_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_batch_process_agents_empty_list(self):
        """Test batch_process_agents with empty agent list."""
        results = await batch_process_agents(
            agents=[],
            task_type="process",
            parameters={}
        )
        
        assert results == []
    
    @pytest.mark.asyncio
    async def test_retry_on_failure_success(self):
        """Test retry_on_failure decorator with successful call."""
        @retry_on_failure(max_retries=3, delay=0.1)
        async def successful_function():
            return "success"
        
        result = await successful_function()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_retry_on_failure_with_retries(self):
        """Test retry_on_failure decorator with failures then success."""
        call_count = 0
        
        @retry_on_failure(max_retries=3, delay=0.1)
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary failure")
            return "success"
        
        result = await flaky_function()
        assert result == "success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_retry_on_failure_max_retries_exceeded(self):
        """Test retry_on_failure decorator when max retries exceeded."""
        @retry_on_failure(max_retries=2, delay=0.1)
        async def always_fails():
            raise Exception("Always fails")
        
        with pytest.raises(Exception, match="Always fails"):
            await always_fails()
    
    def test_save_agent_state(self, mock_agent, tmp_path):
        """Test save_agent_state utility function."""
        state_file = tmp_path / "agent_state.json"
        
        save_agent_state(mock_agent, str(state_file))
        
        assert state_file.exists()
        import json
        with state_file.open() as f:
            state = json.load(f)
            assert state["agent_id"] == "agent1"
    
    def test_load_agent_state(self, mock_gateway, tmp_path):
        """Test load_agent_state utility function."""
        # First save an agent
        agent = create_agent("agent1", "Test Agent", mock_gateway)
        state_file = tmp_path / "agent_state.json"
        save_agent_state(agent, str(state_file))
        
        # Then load it
        loaded_agent = load_agent_state(str(state_file), mock_gateway)
        
        assert loaded_agent.agent_id == "agent1"
        assert loaded_agent.name == "Test Agent"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

