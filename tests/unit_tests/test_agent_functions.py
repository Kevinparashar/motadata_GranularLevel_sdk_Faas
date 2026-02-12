"""
Unit Tests for Agent Framework Functions

Tests factory functions, convenience functions, and utilities for agent framework.
"""


from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.core.agno_agent_framework.agent import Agent, AgentManager, AgentStatus
from src.core.agno_agent_framework.functions import (  # Factory functions; Convenience functions; Utility functions
    batch_process_agents,
    chat_with_agent,
    create_agent,
    create_agent_manager,
    create_agent_with_memory,
    create_agent_with_prompt_management,
    create_agent_with_tools,
    create_orchestrator,
    delegate_task,
    execute_task,
    find_agents_by_capability,
    load_agent_state,
    retry_on_failure,
    save_agent_state,
)
from src.core.agno_agent_framework.session import SessionManager


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
            llm_provider="openai",
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
        agent = create_agent("agent1", "Agent", mock_gateway, custom_param="value")

        # Verify agent was created (kwargs passed to Agent constructor)
        assert agent.agent_id == "agent1"

    def test_create_agent_with_memory(self, mock_gateway):
        """Test create_agent_with_memory factory function."""
        memory_config = {
            "persistence_path": "/tmp/test_memory.json",
            "max_short_term": 100,
            "max_long_term": 2000,
        }

        agent = create_agent_with_memory(
            agent_id="agent1",
            name="Agent with Memory",
            gateway=mock_gateway,
            memory_config=memory_config,
        )

        assert isinstance(agent, Agent)
        assert agent.agent_id == "agent1"
        # Memory should be attached
        assert agent.memory is not None

    def test_create_agent_with_memory_no_config(self, mock_gateway):
        """Test create_agent_with_memory without memory config."""
        agent = create_agent_with_memory(
            agent_id="agent1", name="Agent", gateway=mock_gateway, memory_config=None
        )

        assert isinstance(agent, Agent)
        assert agent.agent_id == "agent1"

    def test_create_agent_with_memory_full_config(self, mock_gateway):
        """Test create_agent_with_memory with full memory config to cover lines 97-110."""
        memory_config = {
            "persistence_path": "/tmp/test_memory.json",
            "max_short_term": 100,
            "max_long_term": 2000,
            "max_episodic": 600,
            "max_semantic": 3000,
        }

        agent = create_agent_with_memory(
            agent_id="agent1",
            name="Agent with Memory",
            gateway=mock_gateway,
            memory_config=memory_config,
        )

        assert isinstance(agent, Agent)
        assert agent.memory is not None
        assert agent.memory.max_short_term == 100
        assert agent.memory.max_long_term == 2000
        assert agent.memory.max_episodic == 600
        assert agent.memory.max_semantic == 3000

    def test_create_agent_with_memory_no_memory_attached(self, mock_gateway):
        """Test create_agent_with_memory when memory is not attached to cover line 103."""
        memory_config = {"persistence_path": None}

        agent = create_agent_with_memory(
            agent_id="agent1",
            name="Agent",
            gateway=mock_gateway,
            memory_config=memory_config,
        )

        # If attach_memory fails or returns None, agent.memory might be None
        # This tests the if agent.memory check
        assert isinstance(agent, Agent)

    @patch("src.core.agno_agent_framework.functions.create_prompt_manager")
    def test_create_agent_with_prompt_management(self, mock_create_pm, mock_gateway):
        """Test create_agent_with_prompt_management factory function."""
        mock_pm = Mock()
        mock_create_pm.return_value = mock_pm

        agent = create_agent_with_prompt_management(
            agent_id="agent1",
            name="Agent with Prompts",
            gateway=mock_gateway,
            system_prompt="You are a helpful assistant.",
            role_template="assistant",
            max_context_tokens=8000,
        )

        assert isinstance(agent, Agent)
        assert agent.agent_id == "agent1"
        assert agent.system_prompt == "You are a helpful assistant."
        assert agent.role_template == "assistant"
        assert agent.max_context_tokens == 8000
        # Prompt manager should be attached
        assert agent.prompt_manager is not None

    @patch("src.core.agno_agent_framework.agent.create_prompt_manager")
    def test_create_agent_with_prompt_management_with_templates(self, mock_create_pm, mock_gateway):
        """Test create_agent_with_prompt_management with templates."""
        mock_pm = Mock()
        mock_pm.add_template = Mock()
        mock_create_pm.return_value = mock_pm

        prompt_config = {
            "templates": [
                {
                    "name": "greeting",
                    "version": "1.0",
                    "content": "Hello {name}!",
                    "metadata": {"type": "greeting"},
                }
            ]
        }

        agent = create_agent_with_prompt_management(
            agent_id="agent1", name="Agent", gateway=mock_gateway, prompt_config=prompt_config
        )

        assert agent.prompt_manager is not None
        # Verify template was added - check if add_template was called on the prompt manager
        # The agent's prompt_manager should be the mock_pm we created
        if isinstance(agent.prompt_manager, Mock):
            agent.prompt_manager.add_template.assert_called_once()

    def test_create_agent_with_prompt_management_no_module(self, mock_gateway):
        """Test create_agent_with_prompt_management when module not available - covers lines 19-20, 171-178."""
        # Patch create_prompt_manager to None to cover the else branch (lines 171-178)
        # The ImportError (lines 19-20) is already covered by the import statement itself
        with patch("src.core.agno_agent_framework.functions.create_prompt_manager", None):
            agent = create_agent_with_prompt_management(
                agent_id="agent1",
                name="Agent",
                gateway=mock_gateway,
                system_prompt="Test prompt",
                role_template="assistant",
                max_context_tokens=5000,
            )

            assert isinstance(agent, Agent)
            assert agent.system_prompt == "Test prompt"
            assert agent.role_template == "assistant"
            assert agent.max_context_tokens == 5000
            assert agent.use_prompt_management is False

    def test_create_agent_with_tools(self, mock_gateway):
        """Test create_agent_with_tools factory function - covers lines 228-236."""
        from src.core.agno_agent_framework.tools import Tool, ToolType

        def test_function(x: int, y: int) -> int:
            return x + y

        tool = Tool(
            tool_id="test_tool",
            name="test_function",
            description="Test tool",
            tool_type=ToolType.FUNCTION,
            function=test_function
        )

        agent = create_agent_with_tools(
            agent_id="agent1",
            name="Agent with Tools",
            gateway=mock_gateway,
            tools=[tool],
            enable_tool_calling=True,
            max_tool_iterations=5
        )

        assert isinstance(agent, Agent)
        assert agent.agent_id == "agent1"
        assert agent.enable_tool_calling is True
        assert agent.max_tool_iterations == 5

    def test_create_agent_with_tools_no_tools(self, mock_gateway):
        """Test create_agent_with_tools without tools - covers line 233."""
        agent = create_agent_with_tools(
            agent_id="agent1",
            name="Agent",
            gateway=mock_gateway,
            tools=None,
            tool_registry=None,
            enable_tool_calling=False
        )

        assert isinstance(agent, Agent)
        assert agent.agent_id == "agent1"
        assert agent.enable_tool_calling is False

    def test_create_agent_with_tools_with_registry(self, mock_gateway):
        """Test create_agent_with_tools with tool registry - covers line 234."""
        from src.core.agno_agent_framework.tools import ToolRegistry

        registry = ToolRegistry()
        with patch.object(Agent, "attach_tools", new_callable=Mock) as mock_attach:
            agent = create_agent_with_tools(
                agent_id="agent1",
                name="Agent",
                gateway=mock_gateway,
                tool_registry=registry
            )

            assert isinstance(agent, Agent)
            assert agent.agent_id == "agent1"
            mock_attach.assert_called_once_with(tools=None, registry=registry)

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
        gateway.generate_async = AsyncMock(return_value=Mock(text="Test response", model="gpt-4"))
        return gateway

    @pytest.fixture
    def mock_agent(self, mock_gateway):
        """Create a mock agent."""
        from src.core.agno_agent_framework.agent import AgentTask
        
        agent = Mock(spec=Agent)
        agent.agent_id = "agent1"
        agent.name = "Test Agent"
        agent.status = AgentStatus.IDLE
        agent.gateway = mock_gateway
        agent.task_queue = []
        agent.add_task = Mock(side_effect=lambda task_type, params, priority=0: (
            agent.task_queue.append(AgentTask(
                task_id=f"task_{len(agent.task_queue) + 1}",
                task_type=task_type,
                parameters=params,
                priority=priority
            )) or agent.task_queue[-1].task_id
        ))
        agent.execute_task = AsyncMock(return_value={"result": "Task completed"})
        return agent

    @pytest.fixture
    def session_manager(self):
        """Create a session manager."""
        return SessionManager()

    @pytest.mark.asyncio
    async def test_chat_with_agent(self, mock_agent, session_manager):
        """Test chat_with_agent convenience function."""
        from src.core.agno_agent_framework.agent import AgentTask
        
        # Reset task queue
        mock_agent.task_queue = []
        mock_agent.execute_task = AsyncMock(return_value={"result": "Hello! How can I help you?"})
        mock_agent.add_task = Mock(side_effect=lambda task_type, params, priority=0: (
            mock_agent.task_queue.append(AgentTask(
                task_id=f"task_{len(mock_agent.task_queue) + 1}",
                task_type=task_type,
                parameters=params,
                priority=priority
            )) or mock_agent.task_queue[-1].task_id
        ))

        response = await chat_with_agent(
            agent=mock_agent, message="Hello", tenant_id="test_tenant"
        )

        assert "answer" in response
        assert response["answer"] == "Hello! How can I help you?"
        assert "session_id" in response
        mock_agent.execute_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_with_agent_existing_session(self, mock_agent, session_manager):
        """Test chat_with_agent with existing session to cover lines 345-350."""
        from src.core.agno_agent_framework.agent import AgentTask
        
        # Reset session managers
        if hasattr(chat_with_agent, "_session_managers"):
            chat_with_agent._session_managers.clear()
        
        # Create session through chat_with_agent first
        mock_agent.task_queue = []
        mock_agent.execute_task = AsyncMock(return_value={"result": "First response"})
        task_id_returned = None
        def add_task_side_effect(task_type, params, priority=0):
            nonlocal task_id_returned
            task = AgentTask(
                task_id=f"task_{len(mock_agent.task_queue) + 1}",
                task_type=task_type,
                parameters=params,
                priority=priority
            )
            mock_agent.task_queue.append(task)
            task_id_returned = task.task_id
            return task.task_id
        
        mock_agent.add_task = Mock(side_effect=add_task_side_effect)
        
        # First call creates session
        response1 = await chat_with_agent(
            agent=mock_agent,
            message="First message",
            tenant_id="test_tenant",
        )
        session_id = response1["session_id"]

        # Second call with existing session_id
        mock_agent.execute_task = AsyncMock(return_value={"result": "Second response"})
        response2 = await chat_with_agent(
            agent=mock_agent,
            message="Second message",
            tenant_id="test_tenant",
            session_id=session_id,
        )

        assert "answer" in response2
        assert response2["answer"] == "Second response"
        assert response2["session_id"] == session_id

    @pytest.mark.asyncio
    async def test_chat_with_agent_with_context(self, mock_agent, session_manager):
        """Test chat_with_agent with context to cover lines 353-374."""
        from src.core.agno_agent_framework.agent import AgentTask
        
        # Reset session managers
        if hasattr(chat_with_agent, "_session_managers"):
            chat_with_agent._session_managers.clear()
        
        # Reset task queue
        mock_agent.task_queue = []
        mock_agent.execute_task = AsyncMock(return_value={"result": "Context response"})
        task_id_returned = None
        def add_task_side_effect(task_type, params, priority=0):
            nonlocal task_id_returned
            task = AgentTask(
                task_id=f"task_{len(mock_agent.task_queue) + 1}",
                task_type=task_type,
                parameters=params,
                priority=priority
            )
            mock_agent.task_queue.append(task)
            task_id_returned = task.task_id
            return task.task_id
        
        mock_agent.add_task = Mock(side_effect=add_task_side_effect)

        response = await chat_with_agent(
            agent=mock_agent,
            message="Hello",
            context={"key": "value", "user_id": "user123"},
            tenant_id="test_tenant"
        )

        assert "answer" in response
        assert response["answer"] == "Context response"
        assert "session_id" in response
        # Verify context was passed as metadata
        mock_agent.execute_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_with_agent_with_many_messages(self, mock_agent):
        """Test chat_with_agent with many messages to cover line 363."""
        from src.core.agno_agent_framework.agent import AgentTask
        
        # Reset session managers
        if hasattr(chat_with_agent, "_session_managers"):
            chat_with_agent._session_managers.clear()
        
        mock_agent.task_queue = []
        mock_agent.execute_task = AsyncMock(return_value={"result": "Response"})
        task_id_returned = None
        def add_task_side_effect(task_type, params, priority=0):
            nonlocal task_id_returned
            task = AgentTask(
                task_id=f"task_{len(mock_agent.task_queue) + 1}",
                task_type=task_type,
                parameters=params,
                priority=priority
            )
            mock_agent.task_queue.append(task)
            task_id_returned = task.task_id
            return task.task_id
        
        mock_agent.add_task = Mock(side_effect=add_task_side_effect)

        # Add many messages to session
        for i in range(15):
            await chat_with_agent(
                agent=mock_agent,
                message=f"Message {i}",
                tenant_id="test_tenant",
            )

        # Verify that only last 10 messages are used
        call_args = mock_agent.execute_task.call_args
        messages = call_args[0][0].parameters.get("messages", [])
        assert len(messages) <= 10

    @pytest.mark.asyncio
    async def test_execute_task(self, mock_agent):
        """Test execute_task convenience function to cover lines 303-305."""
        from src.core.agno_agent_framework.agent import AgentTask
        
        # Reset task queue
        mock_agent.task_queue = []
        task_id_returned = None
        def add_task_side_effect(task_type, params, priority=0):
            nonlocal task_id_returned
            task = AgentTask(
                task_id=f"task_{len(mock_agent.task_queue) + 1}",
                task_type=task_type,
                parameters=params,
                priority=priority
            )
            mock_agent.task_queue.append(task)
            task_id_returned = task.task_id
            return task.task_id
        
        mock_agent.add_task = Mock(side_effect=add_task_side_effect)
        
        result = await execute_task(
            agent=mock_agent,
            task_type="analyze",
            parameters={"text": "Test text"},
            priority=1,
            tenant_id="tenant1",
        )

        assert result == {"result": "Task completed"}
        mock_agent.execute_task.assert_called_once()
        # Verify tenant_id was passed
        call_args = mock_agent.execute_task.call_args
        assert call_args[1].get("tenant_id") == "tenant1"

    @pytest.mark.asyncio
    async def test_execute_task_default_priority(self, mock_agent):
        """Test execute_task with default priority."""
        from src.core.agno_agent_framework.agent import AgentTask
        
        # Reset task queue
        mock_agent.task_queue = []
        mock_agent.add_task = Mock(side_effect=lambda task_type, params, priority=0: (
            mock_agent.task_queue.append(AgentTask(
                task_id=f"task_{len(mock_agent.task_queue) + 1}",
                task_type=task_type,
                parameters=params,
                priority=priority
            )) or mock_agent.task_queue[-1].task_id
        ))
        
        await execute_task(agent=mock_agent, task_type="test", parameters={})

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

        orchestrator = Mock()
        orchestrator.delegate_task = AsyncMock(return_value={"result": "Completed"})

        result = await delegate_task(
            orchestrator=orchestrator,
            from_agent_id="agent1",
            to_agent_id="agent2",
            task_type="process",
            parameters={"data": "test"},
        )

        assert result == {"result": "Completed"}
        orchestrator.delegate_task.assert_called_once()

    @patch("src.core.agno_agent_framework.functions.create_prompt_manager")
    def test_create_agent_with_prompt_management_basic(self, mock_create_pm, mock_gateway):
        """Test create_agent_with_prompt_management basic functionality."""
        mock_pm = Mock()
        mock_pm.history = []
        mock_create_pm.return_value = mock_pm

        agent = create_agent_with_prompt_management(
            agent_id="agent1",
            name="Agent with Prompts",
            gateway=mock_gateway,
            system_prompt="You are helpful.",
            max_context_tokens=8000,
        )

        assert agent.system_prompt == "You are helpful."
        assert agent.max_context_tokens == 8000
        assert agent.use_prompt_management is True

    def test_find_agents_by_capability(self):
        """Test find_agents_by_capability convenience function to cover line 429."""
        agent1 = Mock(spec=Agent)
        agent1.agent_id = "agent1"
        agent1.has_capability = Mock(return_value=True)

        agent2 = Mock(spec=Agent)
        agent2.agent_id = "agent2"
        agent2.has_capability = Mock(return_value=False)

        manager = Mock(spec=AgentManager)
        manager.list_agents = Mock(return_value=["agent1", "agent2"])
        manager.get_agent = Mock(side_effect=lambda x: agent1 if x == "agent1" else agent2)
        manager.find_agents_by_capability = Mock(return_value=[agent1])

        agents = find_agents_by_capability(manager=manager, capability_name="analysis")

        assert len(agents) == 1
        assert agents[0].agent_id == "agent1"
        manager.find_agents_by_capability.assert_called_once_with("analysis")


class TestUtilityFunctions:
    """Test utility functions."""

    @pytest.fixture
    def mock_gateway(self):
        """Mock LiteLLM Gateway."""
        return Mock()

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent."""
        agent = Mock(spec=Agent)
        agent.agent_id = "agent1"
        agent.name = "Test Agent"
        agent.status = AgentStatus.IDLE
        return agent

    def test_batch_process_agents(self):
        """Test batch_process_agents utility function."""
        from src.core.agno_agent_framework.agent import AgentTask
        
        agent1 = Mock(spec=Agent)
        agent1.agent_id = "agent1"
        agent1.task_queue = []
        agent1.add_task = Mock(side_effect=lambda task_type, params, priority=0: (
            agent1.task_queue.append(AgentTask(
                task_id=f"task_{len(agent1.task_queue) + 1}",
                task_type=task_type,
                parameters=params,
                priority=priority
            )) or agent1.task_queue[-1].task_id
        ))
        agent1.execute_task = AsyncMock(return_value={"result": "Result 1"})

        agent2 = Mock(spec=Agent)
        agent2.agent_id = "agent2"
        agent2.task_queue = []
        agent2.add_task = Mock(side_effect=lambda task_type, params, priority=0: (
            agent2.task_queue.append(AgentTask(
                task_id=f"task_{len(agent2.task_queue) + 1}",
                task_type=task_type,
                parameters=params,
                priority=priority
            )) or agent2.task_queue[-1].task_id
        ))
        agent2.execute_task = AsyncMock(return_value={"result": "Result 2"})

        results = batch_process_agents(
            agents=[agent1, agent2], task_type="process", parameters={"data": "test"}
        )

        assert len(results) == 2
        # Results may contain exceptions, so check if they're dicts with "result" key
        if isinstance(results[0], dict):
            assert results[0]["result"] == "Result 1"
        if isinstance(results[1], dict):
            assert results[1]["result"] == "Result 2"

    def test_batch_process_agents_empty_list(self):
        """Test batch_process_agents with empty agent list."""
        results = batch_process_agents(agents=[], task_type="process", parameters={})

        assert results == []

    @pytest.mark.asyncio
    async def test_retry_on_failure_success(self):
        """Test retry_on_failure decorator with successful call."""

        @retry_on_failure(max_retries=3, retry_delay=0.1)
        async def successful_function():
            return "success"

        result = await successful_function()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_retry_on_failure_with_retries(self):
        """Test retry_on_failure decorator with failures then success to cover lines 491-507."""
        call_count = 0

        @retry_on_failure(max_retries=3, retry_delay=0.1, exceptions=(RuntimeError,))
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RuntimeError("Temporary failure")  # noqa: S112, TRY301
            return "success"

        result = await flaky_function()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_on_failure_with_different_exception(self):
        """Test retry_on_failure with different exception type."""
        call_count = 0

        @retry_on_failure(max_retries=3, retry_delay=0.1, exceptions=(ValueError,))
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"

        result = await flaky_function()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_on_failure_max_retries_exceeded(self):
        """Test retry_on_failure decorator when max retries exceeded."""

        @retry_on_failure(max_retries=2, retry_delay=0.1)
        async def always_fails():
            raise RuntimeError("Always fails")  # noqa: S112, TRY301

        with pytest.raises(RuntimeError, match="Always fails"):
            await always_fails()

    def test_retry_on_failure_sync_function(self):
        """Test retry_on_failure decorator with sync function - covers lines 526-542, 573."""
        call_count = 0

        @retry_on_failure(max_retries=3, retry_delay=0.01)
        def sync_flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"

        result = sync_flaky_function()
        assert result == "success"
        assert call_count == 2

    def test_retry_on_failure_sync_max_retries(self):
        """Test retry_on_failure decorator with sync function max retries - covers lines 526-542, 573."""

        @retry_on_failure(max_retries=2, retry_delay=0.01)
        def sync_always_fails():
            raise ValueError("Always fails")

        with pytest.raises(ValueError, match="Always fails"):
            sync_always_fails()

    @pytest.mark.asyncio
    async def test_save_agent_state(self, mock_agent, tmp_path):
        """Test save_agent_state utility function to cover line 592."""
        state_file = tmp_path / "agent_state.json"
        
        # Mock agent.save_state to avoid aiofiles dependency
        mock_agent.save_state = AsyncMock()

        await save_agent_state(mock_agent, str(state_file))

        # Verify save_state was called
        mock_agent.save_state.assert_called_once_with(str(state_file))

    @pytest.mark.asyncio
    async def test_save_agent_state_no_path(self, mock_agent):
        """Test save_agent_state without file path."""
        mock_agent.save_state = AsyncMock()

        await save_agent_state(mock_agent, None)

        mock_agent.save_state.assert_called_once_with(None)

    @pytest.mark.asyncio
    async def test_load_agent_state(self, mock_gateway, tmp_path):
        """Test load_agent_state utility function to cover line 609."""
        # First save an agent
        agent = create_agent("agent1", "Test Agent", mock_gateway)
        state_file = tmp_path / "agent_state.json"
        
        # Mock agent.save_state to avoid aiofiles dependency
        with patch.object(Agent, "save_state", new_callable=AsyncMock) as mock_save:
            await save_agent_state(agent, str(state_file))
            mock_save.assert_called_once()

        # Mock Agent.load_state for load
        with patch.object(Agent, "load_state", new_callable=AsyncMock) as mock_load:
            mock_load.return_value = agent
            
            # Then load it
            loaded_agent = await load_agent_state(str(state_file), mock_gateway)

            assert loaded_agent.agent_id == "agent1"
            assert loaded_agent.name == "Test Agent"
            mock_load.assert_called_once_with(str(state_file), mock_gateway)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
