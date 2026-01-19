"""
Unit Tests for Prompt-Based Generator

Tests for prompt interpretation, agent generation, and tool generation.
"""

import pytest  # pyright: ignore[reportMissingImports]
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from src.core.prompt_based_generator import (
    PromptInterpreter,
    AgentGenerator,
    ToolGenerator,
    AccessControl,
    Permission,
    ResourceType
)
from src.core.prompt_based_generator.exceptions import (
    PromptInterpretationError,
    AgentGenerationError,
    ToolGenerationError
)


class TestPromptInterpreter:
    """Test prompt interpretation."""
    
    @pytest.fixture
    def mock_gateway(self):
        """Create mock gateway."""
        gateway = Mock()
        gateway.generate_async = AsyncMock(return_value=MagicMock(
            text='{"name": "Test Agent", "description": "Test", "capabilities": [], "system_prompt": "Test", "required_tools": [], "memory_config": {}, "max_context_tokens": 4000, "enable_tool_calling": true}'
        ))
        return gateway
    
    @pytest.fixture
    def interpreter(self, mock_gateway):
        """Create prompt interpreter."""
        return PromptInterpreter(mock_gateway)
    
    @pytest.mark.asyncio
    async def test_interpret_agent_prompt(self, interpreter):
        """Test agent prompt interpretation."""
        requirements = await interpreter.interpret_agent_prompt(
            prompt="Create a helpful assistant"
        )
        assert requirements.name == "Test Agent"
        assert requirements.description == "Test"
    
    @pytest.mark.asyncio
    async def test_interpret_tool_prompt(self, interpreter):
        """Test tool prompt interpretation."""
        interpreter._tool_prompt_template = interpreter._tool_prompt_template.replace(
            "{prompt}", "Create a tool"
        )
        interpreter.gateway.generate_async = AsyncMock(return_value=MagicMock(
            text='{"name": "Test Tool", "description": "Test", "function_name": "test_func", "parameters": [], "return_type": "Any", "code_template": "def test_func(): pass"}'
        ))
        
        requirements = await interpreter.interpret_tool_prompt(
            prompt="Create a tool that adds numbers"
        )
        assert requirements.name == "Test Tool"


class TestAccessControl:
    """Test access control."""
    
    @pytest.fixture
    def access_control(self):
        """Create access control instance."""
        return AccessControl()
    
    def test_grant_permission(self, access_control):
        """Test granting permission."""
        access_control.grant_permission(
            tenant_id="tenant_123",
            user_id="user_456",
            resource_type=ResourceType.AGENT,
            resource_id="agent_789",
            permission=Permission.EXECUTE
        )
        
        assert access_control.check_permission(
            tenant_id="tenant_123",
            user_id="user_456",
            resource_type=ResourceType.AGENT,
            resource_id="agent_789",
            permission=Permission.EXECUTE
        )
    
    def test_revoke_permission(self, access_control):
        """Test revoking permission."""
        access_control.grant_permission(
            tenant_id="tenant_123",
            user_id="user_456",
            resource_type=ResourceType.AGENT,
            resource_id="agent_789",
            permission=Permission.EXECUTE
        )
        
        access_control.revoke_permission(
            tenant_id="tenant_123",
            user_id="user_456",
            resource_type=ResourceType.AGENT,
            resource_id="agent_789",
            permission=Permission.EXECUTE
        )
        
        assert not access_control.check_permission(
            tenant_id="tenant_123",
            user_id="user_456",
            resource_type=ResourceType.AGENT,
            resource_id="agent_789",
            permission=Permission.EXECUTE
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

