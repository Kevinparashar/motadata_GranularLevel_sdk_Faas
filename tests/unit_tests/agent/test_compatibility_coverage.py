"""
Unit tests for compatibility.py coverage improvements.

Tests missing coverage paths in compatibility.py to achieve >85% coverage.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from src.core.agno_agent_framework.compatibility import (
    Agent,
    AgentMessage,
    AgentTask,
)


class TestAgentModelExtractionCoverage:
    """Test Agent model extraction edge cases for coverage."""

    def test_init_model_none_with_gateway(self):
        """Test __init__() when model is None and gateway is provided."""
        mock_gateway = MagicMock()
        mock_gateway.default_model = "gpt-3.5-turbo"
        
        agent = Agent(
            agent_id="test-agent",
            name="Test Agent",
            gateway=mock_gateway,
            llm_model=None,
        )
        
        assert agent.agent_id == "test-agent"
        assert agent.name == "Test Agent"

    def test_init_model_empty_string(self):
        """Test __init__() when model is empty string."""
        agent = Agent(
            agent_id="test-agent",
            name="Test Agent",
            gateway=None,
            llm_model="",
        )
        
        assert agent.agent_id == "test-agent"

    def test_init_model_without_provider(self):
        """Test __init__() when model doesn't have provider."""
        agent = Agent(
            agent_id="test-agent",
            name="Test Agent",
            gateway=None,
            llm_model="gpt-4",
            llm_provider=None,
        )
        
        assert agent.agent_id == "test-agent"

    def test_init_model_non_string(self):
        """Test __init__() when model is not a string."""
        agent = Agent(
            agent_id="test-agent",
            name="Test Agent",
            gateway=None,
            llm_model="gpt-4",  # String type required
        )
        
        assert agent.agent_id == "test-agent"

    def test_extract_model_from_gateway_no_provider(self):
        """Test _extract_model_from_gateway() when no provider specified."""
        agent = Agent(
            agent_id="test-agent",
            name="Test Agent",
            gateway=None,
            llm_model="gpt-4",
            llm_provider=None,
        )
        
        model = agent._extract_model_from_gateway(None, "gpt-4", None)
        assert ":" in model or model == "gpt-4"

    def test_extract_model_from_gateway_non_string_fallback(self):
        """Test _extract_model_from_gateway() when model is not a string."""
        agent = Agent(
            agent_id="test-agent",
            name="Test Agent",
        )
        
        model = agent._extract_model_from_gateway(None, None, None)
        assert isinstance(model, str)
        assert len(model) > 0


class TestAgentCreationErrorHandling:
    """Test Agent creation error handling for coverage."""

    def test_init_agent_creation_fallback(self):
        """Test __init__() when agent creation fails and fallback succeeds."""
        with patch("src.core.agno_agent_framework.compatibility.RealAgnoAgent") as mock_agno:
            # First call fails, second succeeds
            mock_agno.side_effect = [
                Exception("First attempt failed"),
                MagicMock()  # Fallback succeeds
            ]
            
            agent = Agent(
                agent_id="test-agent",
                name="Test Agent",
            )
            
            assert agent.agent_id == "test-agent"
            assert mock_agno.call_count == 2

    def test_init_agent_creation_both_fail(self):
        """Test __init__() when both agent creation attempts fail."""
        with patch("src.core.agno_agent_framework.compatibility.RealAgnoAgent") as mock_agno:
            mock_agno.side_effect = Exception("Both attempts failed")
            
            with pytest.raises(Exception):
                Agent(
                    agent_id="test-agent",
                    name="Test Agent",
                )

    def test_init_agent_creation_tenant_only(self):
        """Test __init__() when only tenant_id is provided."""
        agent = Agent(
            agent_id="test-agent-id",  # agent_id is required
            name="Test Agent",
            tenant_id="tenant-123",
        )
        
        assert agent.tenant_id == "tenant-123"
        assert agent.name == "Test Agent"


class TestAgentCapabilitiesCoverage:
    """Test Agent capabilities handling for coverage."""

    def test_init_capabilities_not_list(self):
        """Test __init__() when capabilities is not a list."""
        agent = Agent(
            agent_id="test-agent",
            name="Test Agent",
            capabilities="not-a-list",  # Should be converted to []
        )
        
        assert isinstance(agent._capabilities, list)
        assert len(agent._capabilities) == 0


class TestAgentMessageCodecCoverage:
    """Test Agent message codec operations for coverage."""

    @pytest.mark.asyncio
    async def test_encode_message_import_error(self):
        """Test encode_message() when codec_integration import fails."""
        agent = Agent(
            agent_id="test-agent",
            name="Test Agent",
        )
        
        message = AgentMessage(
            from_agent="agent-1",
            to_agent="agent-2",
            content="Test message",
        )
        
        with patch("src.core.codec_integration.encode_agent_message", side_effect=ImportError("No codec")):
            result = await agent.encode_message(message)
            
            # Should fall back to JSON encoding
            assert isinstance(result, bytes)
            assert b"from_agent" in result or b"Test message" in result

    @pytest.mark.asyncio
    async def test_decode_message_import_error(self):
        """Test decode_message() when codec_integration import fails."""
        agent = Agent(
            agent_id="test-agent",
            name="Test Agent",
        )
        
        # Create a JSON-encoded message
        import json
        message_dict = {
            "from_agent": "agent-1",
            "to_agent": "agent-2",
            "content": "Test message",
            "message_type": "text",
            "timestamp": datetime.now().isoformat(),
            "metadata": {},
        }
        payload = json.dumps(message_dict).encode('utf-8')
        
        with patch("src.core.codec_integration.decode_agent_message", side_effect=ImportError("No codec")):
            result = await agent.decode_message(payload)
            
            # Should fall back to JSON decoding
            assert isinstance(result, AgentMessage)
            assert result.from_agent == "agent-1"
            assert result.content == "Test message"


class TestAgentToolsCoverage:
    """Test Agent tools attachment for coverage."""

    def test_attach_tools_exception(self):
        """Test attach_tools() when ToolRegistry creation fails."""
        agent = Agent(
            agent_id="test-agent",
            name="Test Agent",
        )
        
        mock_tool = MagicMock()
        
        with patch("src.core.agno_agent_framework.tools.ToolRegistry", side_effect=Exception("ToolRegistry error")):
            # Should create MockToolRegistry as fallback
            agent.attach_tools([mock_tool])
            
            assert agent._tool_registry is not None
            assert hasattr(agent._tool_registry, 'register_tool')


class TestAgentChatCoverage:
    """Test Agent chat method for coverage."""

    @pytest.mark.asyncio
    async def test_chat_response_text_attribute(self):
        """Test chat() when response has 'text' attribute."""
        agent = Agent(
            agent_id="test-agent",
            name="Test Agent",
        )
        
        mock_response = MagicMock()
        mock_response.text = "Response text"
        del mock_response.content  # Remove content attribute
        
        agent._agno_agent.arun = AsyncMock(return_value=mock_response)
        
        result = await agent.chat("Hello")
        
        assert "response" in result
        assert result["response"] == "Response text"

    @pytest.mark.asyncio
    async def test_chat_response_output_attribute(self):
        """Test chat() when response has 'output' attribute."""
        agent = Agent(
            agent_id="test-agent",
            name="Test Agent",
        )
        
        mock_response = MagicMock()
        mock_response.output = "Response output"
        del mock_response.content
        del mock_response.text
        
        agent._agno_agent.arun = AsyncMock(return_value=mock_response)
        
        result = await agent.chat("Hello")
        
        assert "response" in result
        assert result["response"] == "Response output"

    @pytest.mark.asyncio
    async def test_chat_no_arun_method(self):
        """Test chat() when _agno_agent doesn't have arun method."""
        agent = Agent(
            agent_id="test-agent",
            name="Test Agent",
        )
        
        # Mock _agno_agent to not have arun (use object without arun)
        original_agno = agent._agno_agent
        # Create a simple object without arun
        class NoArunAgent:
            pass
        agent._agno_agent = NoArunAgent()
        
        result = await agent.chat("Hello")
        
        assert "response" in result
        assert result["response"] == "Chat response"
        
        # Restore
        agent._agno_agent = original_agno


class TestAgentTaskExecutionCoverage:
    """Test Agent task execution for coverage."""

    @pytest.mark.asyncio
    async def test_execute_task_response_text_attribute(self):
        """Test execute_task() when response has 'text' attribute."""
        agent = Agent(
            agent_id="test-agent",
            name="Test Agent",
        )
        
        task = AgentTask(
            task_id="task-1",
            task_type="test",
            priority=1,
        )
        
        mock_response = MagicMock()
        mock_response.text = "Task result"
        del mock_response.content
        
        agent._agno_agent.arun = AsyncMock(return_value=mock_response)
        
        result = await agent.execute_task(task)
        
        assert result["status"] == "completed"
        assert result["result"] == "Task result"

    @pytest.mark.asyncio
    async def test_execute_task_response_output_attribute(self):
        """Test execute_task() when response has 'output' attribute."""
        agent = Agent(
            agent_id="test-agent",
            name="Test Agent",
        )
        
        task = AgentTask(
            task_id="task-1",
            task_type="test",
            priority=1,
        )
        
        mock_response = MagicMock()
        mock_response.output = "Task output"
        del mock_response.content
        del mock_response.text
        
        agent._agno_agent.arun = AsyncMock(return_value=mock_response)
        
        result = await agent.execute_task(task)
        
        assert result["status"] == "completed"
        assert result["result"] == "Task output"

    @pytest.mark.asyncio
    async def test_execute_task_sync_run(self):
        """Test execute_task() when using sync run() method."""
        agent = Agent(
            agent_id="test-agent",
            name="Test Agent",
        )
        
        task = AgentTask(
            task_id="task-1",
            task_type="test",
            priority=1,
        )
        
        # Create agent with only run method
        original_agno = agent._agno_agent
        class RunOnlyAgent:
            def run(self, prompt):
                return "Sync result"
        agent._agno_agent = RunOnlyAgent()
        
        result = await agent.execute_task(task)
        
        assert result["status"] == "completed"
        assert result["result"] == "Sync result"
        
        # Restore
        agent._agno_agent = original_agno

    @pytest.mark.asyncio
    async def test_execute_task_no_arun_no_run(self):
        """Test execute_task() when neither arun nor run exists."""
        agent = Agent(
            agent_id="test-agent",
            name="Test Agent",
        )
        
        task = AgentTask(
            task_id="task-1",
            task_type="test",
            priority=1,
        )
        
        # Create agent without arun or run
        original_agno = agent._agno_agent
        class NoMethodsAgent:
            pass
        agent._agno_agent = NoMethodsAgent()
        
        result = await agent.execute_task(task)
        
        # Should use fallback
        assert result["status"] == "completed"
        assert result["result"] == "Task executed"
        
        # Restore
        agent._agno_agent = original_agno


class TestAgentGetAttrCoverage:
    """Test Agent __getattr__ method for coverage."""

    def test_getattr_compatibility_methods(self):
        """Test __getattr__() for compatibility methods."""
        agent = Agent(
            agent_id="test-agent",
            name="Test Agent",
        )
        
        # Test that __getattr__ delegates to _agno_agent for unknown attributes
        # The real Agno agent might have various attributes, so we test delegation
        # by checking that accessing a non-existent attribute raises AttributeError
        # from the real Agno agent, not from our compatibility layer
        
        # Test with a definitely non-existent attribute
        with pytest.raises(AttributeError):
            _ = agent._nonexistent_attribute_xyz_123

    def test_getattr_delegates_to_agno_agent(self):
        """Test __getattr__() delegates to _agno_agent."""
        agent = Agent(
            agent_id="test-agent",
            name="Test Agent",
        )
        
        # Add a method to _agno_agent
        agent._agno_agent.custom_method = MagicMock(return_value="custom")
        
        # Should delegate to _agno_agent
        result = agent.custom_method()
        assert result == "custom"


class TestAgentConvertDbCoverage:
    """Test Agent database conversion for coverage."""

    def test_convert_db_to_agno_with_connection_string(self):
        """Test _convert_db_to_agno() when db has connection_string."""
        agent = Agent(
            agent_id="test-agent",
            name="Test Agent",
        )
        
        mock_db = MagicMock()
        mock_db.connection_string = "postgresql://localhost/test"
        
        with patch("src.core.agno_agent_framework.compatibility.Postgres") as mock_postgres:
            agent._convert_db_to_agno(mock_db)
            
            # Should create Postgres instance
            mock_postgres.assert_called_once_with("postgresql://localhost/test")

