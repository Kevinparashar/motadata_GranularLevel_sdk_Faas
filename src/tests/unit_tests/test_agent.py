"""
Unit Tests for Agent Framework Component

Tests agent creation, task execution, and communication.
"""

# Standard library imports
from unittest.mock import Mock, patch

# Third-party imports
import pytest

# Local application/library specific imports
from src.core.agno_agent_framework import (
    Agent,
    AgentManager,
    AgentStatus,
    AgentTask,
)
from src.core.agno_agent_framework.memory import AgentMemory, MemoryType
from src.core.agno_agent_framework.session import AgentSession
from src.core.agno_agent_framework.tools import Tool, ToolExecutor, ToolRegistry


class TestAgent:
    """Test Agent class."""

    @pytest.fixture
    def agent(self):
        """Create a test agent."""
        return Agent(agent_id="test-agent-001", name="Test Agent", description="A test agent")

    def test_agent_initialization(self, agent):
        """Test agent initialization."""
        assert agent.agent_id == "test-agent-001"
        assert agent.name == "Test Agent"
        assert agent.status == AgentStatus.IDLE

    def test_add_capability(self, agent):
        """Test adding capability."""
        agent.add_capability(
            name="test_capability", description="Test capability", parameters={"param1": "value1"}
        )

        assert len(agent.capabilities) == 1
        assert agent.capabilities[0].name == "test_capability"

    def test_add_task(self, agent):
        """Test adding task."""
        task_id = agent.add_task(task_type="test_task", parameters={"key": "value"}, priority=1)

        assert task_id is not None
        assert len(agent.task_queue) == 1
        assert agent.task_queue[0].task_type == "test_task"

    def test_send_message(self, agent):
        """Test sending message."""
        agent.send_message(to_agent="agent-002", content="Hello", message_type="message")

        assert len(agent.message_queue) == 1
        assert agent.message_queue[0].to_agent == "agent-002"

    def test_receive_message(self, agent):
        """Test receiving message."""
        agent.send_message("agent-002", "Hello")
        message = agent.receive_message()

        assert message is not None
        assert message.content == "Hello"

    def test_get_status(self, agent):
        """Test getting agent status."""
        status = agent.get_status()

        assert status["agent_id"] == "test-agent-001"
        assert status["status"] == "idle"
        assert "capabilities" in status


class TestAgentManager:
    """Test AgentManager."""

    def test_register_agent(self):
        """Test agent registration."""
        manager = AgentManager()
        agent = Agent(agent_id="agent-001", name="Test Agent")

        manager.register_agent(agent)
        assert manager.get_agent("agent-001") == agent

    def test_get_agent(self):
        """Test getting agent."""
        manager = AgentManager()
        agent = Agent(agent_id="agent-001", name="Test Agent")
        manager.register_agent(agent)

        retrieved = manager.get_agent("agent-001")
        assert retrieved == agent

    def test_list_agents(self):
        """Test listing agents."""
        manager = AgentManager()
        agent1 = Agent(agent_id="agent-001", name="Agent 1")
        agent2 = Agent(agent_id="agent-002", name="Agent 2")

        manager.register_agent(agent1)
        manager.register_agent(agent2)

        agent_ids = manager.list_agents()
        assert len(agent_ids) == 2
        assert "agent-001" in agent_ids


class TestAgentSession:
    """Test AgentSession."""

    def test_create_session(self):
        """Test session creation."""
        session = AgentSession(session_id="session-001", agent_id="agent-001")

        assert session.session_id == "session-001"
        assert session.agent_id == "agent-001"

    def test_add_message(self):
        """Test adding message to session."""
        session = AgentSession(session_id="session-001", agent_id="agent-001")
        session.add_message("user", "Hello")
        session.add_message("assistant", "Hi!")

        messages = session.get_conversation_history()
        assert len(messages) == 2


class TestAgentMemory:
    """Test AgentMemory."""

    def test_store_memory(self):
        """Test storing memory."""
        memory = AgentMemory(agent_id="agent-001")
        memory.store(content="User likes Python", memory_type=MemoryType.SHORT_TERM, importance=0.7)

        memories = memory.retrieve(query="Python", limit=5)
        assert len(memories) >= 1

    def test_retrieve_memory(self):
        """Test retrieving memory."""
        memory = AgentMemory(agent_id="agent-001")
        memory.store("Test memory", MemoryType.LONG_TERM, 0.9)

        memories = memory.retrieve(query="Test", limit=5)
        assert len(memories) >= 1


class TestToolRegistry:
    """Test ToolRegistry."""

    def test_register_tool(self):
        """Test tool registration."""

        def test_function(x: int) -> int:
            return x * 2

        tool = Tool(
            tool_id="test_tool",
            name="test_tool",
            description="Test tool",
            function=test_function,
        )

        registry = ToolRegistry()
        registry.register_tool(tool)

        assert registry.get_tool("test_tool") == tool

    def test_execute_tool(self):
        """Test tool execution."""

        def add(a: int, b: int) -> int:
            """Add two integers together."""
            return a + b

        tool = Tool(
            tool_id="add",
            name="add",
            description="Add two numbers",
            function=add,
        )

        registry = ToolRegistry()
        registry.register_tool(tool)

        executor = ToolExecutor(registry)
        result = executor.execute_tool_call("add", {"a": 5, "b": 3})
        assert result == 8

    @patch("src.core.agno_agent_framework.agent.create_prompt_manager")
    def test_attach_prompt_manager(self, mock_create_pm, agent):
        """Test attaching prompt manager to agent."""
        mock_pm = Mock()
        mock_pm.history = []
        mock_create_pm.return_value = mock_pm

        agent.attach_prompt_manager(
            max_tokens=8000, system_prompt="You are helpful.", role_template="assistant"
        )

        assert agent.prompt_manager is not None
        assert agent.system_prompt == "You are helpful."
        assert agent.role_template == "assistant"
        assert agent.max_context_tokens == 8000

    @patch("src.core.agno_agent_framework.agent.create_prompt_manager")
    def test_set_system_prompt(self, mock_create_pm, agent):
        """Test setting system prompt."""
        agent.set_system_prompt("You are a data analyst.")
        assert agent.system_prompt == "You are a data analyst."

    @patch("src.core.agno_agent_framework.agent.create_prompt_manager")
    def test_add_prompt_template(self, mock_create_pm, agent):
        """Test adding prompt template."""
        mock_pm = Mock()
        mock_pm.add_template = Mock()
        mock_create_pm.return_value = mock_pm

        agent.attach_prompt_manager()
        agent.add_prompt_template(
            name="analysis",
            version="1.0",
            content="Analyze: {input}",
            metadata={"type": "analysis"},
        )

        mock_pm.add_template.assert_called_once()

    @patch("src.core.agno_agent_framework.agent.create_prompt_manager")
    def test_build_prompt_with_context(self, mock_create_pm, agent):
        """Test building prompt with context management."""
        mock_pm = Mock()
        mock_pm.history = []
        mock_pm.build_context_with_history = Mock(return_value="Context with history")
        mock_pm.window = Mock()
        mock_pm.window.estimate_tokens = Mock(return_value=100)
        mock_pm.window.safety_margin = 200
        mock_pm.truncate_prompt = Mock(return_value="Truncated prompt")
        mock_create_pm.return_value = mock_pm

        agent.attach_prompt_manager()
        agent.system_prompt = "You are helpful."

        task = AgentTask(
            task_id="task1", task_type="llm_query", parameters={"prompt": "What is AI?"}
        )

        prompt = agent._build_prompt_with_context(
            base_prompt="What is AI?", task=task, task_type="llm_query"
        )

        assert "System: You are helpful." in prompt
        assert "What is AI?" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
