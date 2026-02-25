"""
Additional tests for agno_agent_framework/functions.py to improve coverage.

Tests missing paths to achieve >85% coverage.
"""

from unittest.mock import MagicMock, patch

from src.core.agno_agent_framework.functions import create_agent


class TestFunctionsCoverage:
    """Test missing coverage paths in functions.py."""

    def test_create_agent_with_prompt_management_none(self):
        """Test create_agent_with_prompt_management when modules are None."""
        with patch("src.core.agno_agent_framework.functions._AgentOrchestrator", None), \
             patch("src.core.agno_agent_framework.functions.create_prompt_manager", None):
            from src.core.litellm_gateway import LiteLLMGateway
            
            gateway = LiteLLMGateway()
            agent = create_agent(
                agent_id="test-agent",
                name="Test Agent",
                gateway=gateway,
            )
            
            assert agent is not None

    def test_create_agent_with_session_manager_none(self):
        """Test create_agent when SessionManager is None."""
        with patch("src.core.agno_agent_framework.functions._SessionManager", None), \
             patch("src.core.agno_agent_framework.functions.create_prompt_manager", None):
            from src.core.litellm_gateway import LiteLLMGateway
            
            gateway = LiteLLMGateway()
            agent = create_agent(
                agent_id="test-agent",
                name="Test Agent",
                gateway=gateway,
            )
            
            assert agent is not None

    def test_create_agent_with_tools_none(self):
        """Test create_agent when Tool/ToolRegistry are None."""
        with patch("src.core.agno_agent_framework.functions._Tool", None), \
             patch("src.core.agno_agent_framework.functions._ToolRegistry", None), \
             patch("src.core.agno_agent_framework.functions.create_prompt_manager", None):
            from src.core.litellm_gateway import LiteLLMGateway
            
            gateway = LiteLLMGateway()
            agent = create_agent(
                agent_id="test-agent",
                name="Test Agent",
                gateway=gateway
            )
            
            assert agent is not None

    def test_create_agent_basic(self):
        """Test basic create_agent call."""
        with patch("src.core.agno_agent_framework.functions.create_prompt_manager", None):
            from src.core.litellm_gateway import LiteLLMGateway
            
            gateway = LiteLLMGateway()
            agent = create_agent(
                agent_id="test-agent",
                name="Test Agent",
                gateway=gateway,
            )
            
            assert agent is not None
