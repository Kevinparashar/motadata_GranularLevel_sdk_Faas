"""
Unit Tests for Prompt-Based Generator

Tests for prompt interpretation, agent generation, and tool generation.
"""


import json
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.core.prompt_based_generator import (
    AccessControl,
    AgentGenerator,
    AgentRequirements,
    CodeValidationError,
    FeedbackCollector,
    GeneratorCache,
    Permission,
    PromptInterpreter,
    ResourceType,
    ToolGenerator,
    ToolRequirements,
)
from src.core.prompt_based_generator.exceptions import (
    AccessControlError,
    AgentGenerationError,
    PromptInterpretationError,
    ToolGenerationError,
)
from src.core.prompt_based_generator.functions import (
    check_permission,
    create_agent_from_prompt,
    create_tool_from_prompt,
    get_agent_feedback_stats,
    get_tool_feedback_stats,
    grant_permission,
    rate_agent,
    rate_tool,
)


class TestPromptInterpreter:
    """Test prompt interpretation."""

    @pytest.fixture
    def mock_gateway(self):
        """Create mock gateway."""
        gateway = Mock()
        gateway.generate_async = AsyncMock(
            return_value=MagicMock(
                text='{"name": "Test Agent", "description": "Test", "capabilities": [], "system_prompt": "Test", "required_tools": [], "memory_config": {}, "max_context_tokens": 4000, "enable_tool_calling": true}'
            )
        )
        return gateway

    @pytest.fixture
    def interpreter(self, mock_gateway):
        """Create prompt interpreter."""
        return PromptInterpreter(mock_gateway)

    @pytest.mark.asyncio
    async def test_interpret_agent_prompt(self, interpreter):
        """Test agent prompt interpretation."""
        requirements = await interpreter.interpret_agent_prompt(prompt="Create a helpful assistant")
        assert requirements.name == "Test Agent"
        assert requirements.description == "Test"

    @pytest.mark.asyncio
    async def test_interpret_agent_prompt_with_cache(self, interpreter):
        """Test agent prompt interpretation with cache."""
        mock_cache = AsyncMock()
        cached_data = {
            "name": "Cached Agent",
            "description": "Cached",
            "capabilities": [],
            "system_prompt": "Cached",
            "required_tools": [],
            "memory_config": {},
            "max_context_tokens": 4000,
            "enable_tool_calling": True,
        }
        mock_cache.get = AsyncMock(return_value=json.dumps(cached_data))

        requirements = await interpreter.interpret_agent_prompt(
            prompt="Create a helpful assistant", cache=mock_cache
        )
        assert requirements.name == "Cached Agent"
        mock_cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_interpret_agent_prompt_with_invalid_cache(self, interpreter):
        """Test agent prompt interpretation with invalid cache."""
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value="invalid json")
        interpreter.gateway.generate_async = AsyncMock(
            return_value=MagicMock(
                text='{"name": "Test Agent", "description": "Test", "capabilities": [], "system_prompt": "Test", "required_tools": [], "memory_config": {}, "max_context_tokens": 4000, "enable_tool_calling": true}'
            )
        )

        requirements = await interpreter.interpret_agent_prompt(
            prompt="Create a helpful assistant", cache=mock_cache
        )
        assert requirements.name == "Test Agent"

    @pytest.mark.asyncio
    async def test_interpret_agent_prompt_with_json_code_block(self, interpreter):
        """Test agent prompt interpretation with JSON code block."""
        interpreter.gateway.generate_async = AsyncMock(
            return_value=MagicMock(
                text='```json\n{"name": "Test Agent", "description": "Test", "capabilities": [], "system_prompt": "Test", "required_tools": [], "memory_config": {}, "max_context_tokens": 4000, "enable_tool_calling": true}\n```'
            )
        )

        requirements = await interpreter.interpret_agent_prompt(prompt="Create a helpful assistant")
        assert requirements.name == "Test Agent"

    @pytest.mark.asyncio
    async def test_interpret_agent_prompt_with_code_block(self, interpreter):
        """Test agent prompt interpretation with code block."""
        interpreter.gateway.generate_async = AsyncMock(
            return_value=MagicMock(
                text='```\n{"name": "Test Agent", "description": "Test", "capabilities": [], "system_prompt": "Test", "required_tools": [], "memory_config": {}, "max_context_tokens": 4000, "enable_tool_calling": true}\n```'
            )
        )

        requirements = await interpreter.interpret_agent_prompt(prompt="Create a helpful assistant")
        assert requirements.name == "Test Agent"

    @pytest.mark.asyncio
    async def test_interpret_agent_prompt_json_error(self, interpreter):
        """Test agent prompt interpretation with JSON error."""
        interpreter.gateway.generate_async = AsyncMock(return_value=MagicMock(text="invalid json"))

        with pytest.raises(PromptInterpretationError):
            await interpreter.interpret_agent_prompt(prompt="Create a helpful assistant")

    @pytest.mark.asyncio
    async def test_interpret_agent_prompt_general_error(self, interpreter):
        """Test agent prompt interpretation with general error."""
        interpreter.gateway.generate_async = AsyncMock(side_effect=Exception("Gateway error"))

        with pytest.raises(PromptInterpretationError):
            await interpreter.interpret_agent_prompt(prompt="Create a helpful assistant")

    @pytest.mark.asyncio
    async def test_interpret_tool_prompt(self, interpreter):
        """Test tool prompt interpretation."""
        interpreter.gateway.generate_async = AsyncMock(
            return_value=MagicMock(
                text='{"name": "Test Tool", "description": "Test", "function_name": "test_func", "parameters": [], "return_type": "Any", "code_template": "def test_func(): pass"}'
            )
        )

        requirements = await interpreter.interpret_tool_prompt(prompt="Create a tool that adds numbers")
        assert requirements.name == "Test Tool"

    @pytest.mark.asyncio
    async def test_interpret_tool_prompt_with_cache(self, interpreter):
        """Test tool prompt interpretation with cache."""
        mock_cache = AsyncMock()
        cached_data = {
            "name": "Cached Tool",
            "description": "Cached",
            "function_name": "cached_func",
            "parameters": [],
            "return_type": "Any",
            "code_template": "def cached_func(): pass",
        }
        mock_cache.get = AsyncMock(return_value=json.dumps(cached_data))

        requirements = await interpreter.interpret_tool_prompt(
            prompt="Create a tool", cache=mock_cache
        )
        assert requirements.name == "Cached Tool"

    @pytest.mark.asyncio
    async def test_hash_prompt(self, interpreter):
        """Test prompt hashing."""
        hash1 = interpreter._hash_prompt("test prompt")
        hash2 = interpreter._hash_prompt("test prompt")
        assert hash1 == hash2
        assert hash1 != interpreter._hash_prompt("different prompt")


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
            permission=Permission.EXECUTE,
        )

        assert access_control.check_permission(
            tenant_id="tenant_123",
            user_id="user_456",
            resource_type=ResourceType.AGENT,
            resource_id="agent_789",
            permission=Permission.EXECUTE,
        )

    def test_grant_permission_duplicate(self, access_control):
        """Test granting duplicate permission."""
        access_control.grant_permission(
            tenant_id="tenant_123",
            user_id="user_456",
            resource_type=ResourceType.AGENT,
            resource_id="agent_789",
            permission=Permission.EXECUTE,
        )
        # Grant again - should not duplicate
        access_control.grant_permission(
            tenant_id="tenant_123",
            user_id="user_456",
            resource_type=ResourceType.AGENT,
            resource_id="agent_789",
            permission=Permission.EXECUTE,
        )

        permissions = access_control.get_user_permissions(
            tenant_id="tenant_123", user_id="user_456", resource_type=ResourceType.AGENT
        )
        assert len(permissions.get("agent_789", [])) == 1

    def test_revoke_permission(self, access_control):
        """Test revoking permission."""
        access_control.grant_permission(
            tenant_id="tenant_123",
            user_id="user_456",
            resource_type=ResourceType.AGENT,
            resource_id="agent_789",
            permission=Permission.EXECUTE,
        )

        access_control.revoke_permission(
            tenant_id="tenant_123",
            user_id="user_456",
            resource_type=ResourceType.AGENT,
            resource_id="agent_789",
            permission=Permission.EXECUTE,
        )

        assert not access_control.check_permission(
            tenant_id="tenant_123",
            user_id="user_456",
            resource_type=ResourceType.AGENT,
            resource_id="agent_789",
            permission=Permission.EXECUTE,
        )

    def test_revoke_permission_nonexistent_tenant(self, access_control):
        """Test revoking permission for nonexistent tenant - covers line 123."""
        access_control.revoke_permission(
            tenant_id="nonexistent",
            user_id="user_456",
            resource_type=ResourceType.AGENT,
            resource_id="agent_789",
            permission=Permission.EXECUTE,
        )
        # Should not raise error

    def test_revoke_permission_nonexistent_user(self, access_control):
        """Test revoking permission for nonexistent user - covers line 126."""
        access_control.grant_permission(
            tenant_id="tenant_123",
            user_id="user_456",
            resource_type=ResourceType.AGENT,
            resource_id="agent_789",
            permission=Permission.EXECUTE,
        )
        access_control.revoke_permission(
            tenant_id="tenant_123",
            user_id="nonexistent",
            resource_type=ResourceType.AGENT,
            resource_id="agent_789",
            permission=Permission.EXECUTE,
        )

    def test_revoke_permission_nonexistent_resource_type(self, access_control):
        """Test revoking permission for nonexistent resource type - covers line 129."""
        access_control.grant_permission(
            tenant_id="tenant_123",
            user_id="user_456",
            resource_type=ResourceType.AGENT,
            resource_id="agent_789",
            permission=Permission.EXECUTE,
        )
        access_control.revoke_permission(
            tenant_id="tenant_123",
            user_id="user_456",
            resource_type=ResourceType.TOOL,
            resource_id="agent_789",
            permission=Permission.EXECUTE,
        )

    def test_revoke_permission_nonexistent_resource(self, access_control):
        """Test revoking permission for nonexistent resource - covers line 132."""
        access_control.grant_permission(
            tenant_id="tenant_123",
            user_id="user_456",
            resource_type=ResourceType.AGENT,
            resource_id="agent_789",
            permission=Permission.EXECUTE,
        )
        access_control.revoke_permission(
            tenant_id="tenant_123",
            user_id="user_456",
            resource_type=ResourceType.AGENT,
            resource_id="nonexistent",
            permission=Permission.EXECUTE,
        )

    def test_check_permission_nonexistent_tenant(self, access_control):
        """Test check permission for nonexistent tenant - covers line 162."""
        assert not access_control.check_permission(
            tenant_id="nonexistent",
            user_id="user_456",
            resource_type=ResourceType.AGENT,
            resource_id="agent_789",
            permission=Permission.EXECUTE,
        )

    def test_check_permission_nonexistent_user(self, access_control):
        """Test check permission for nonexistent user - covers line 165."""
        access_control.grant_permission(
            tenant_id="tenant_123",
            user_id="user_456",
            resource_type=ResourceType.AGENT,
            resource_id="agent_789",
            permission=Permission.EXECUTE,
        )
        assert not access_control.check_permission(
            tenant_id="tenant_123",
            user_id="nonexistent",
            resource_type=ResourceType.AGENT,
            resource_id="agent_789",
            permission=Permission.EXECUTE,
        )

    def test_check_permission_nonexistent_resource_type(self, access_control):
        """Test check permission for nonexistent resource type - covers line 168."""
        access_control.grant_permission(
            tenant_id="tenant_123",
            user_id="user_456",
            resource_type=ResourceType.AGENT,
            resource_id="agent_789",
            permission=Permission.EXECUTE,
        )
        assert not access_control.check_permission(
            tenant_id="tenant_123",
            user_id="user_456",
            resource_type=ResourceType.TOOL,
            resource_id="agent_789",
            permission=Permission.EXECUTE,
        )

    def test_check_permission_nonexistent_resource(self, access_control):
        """Test check permission for nonexistent resource - covers line 171."""
        access_control.grant_permission(
            tenant_id="tenant_123",
            user_id="user_456",
            resource_type=ResourceType.AGENT,
            resource_id="agent_789",
            permission=Permission.EXECUTE,
        )
        assert not access_control.check_permission(
            tenant_id="tenant_123",
            user_id="user_456",
            resource_type=ResourceType.AGENT,
            resource_id="nonexistent",
            permission=Permission.EXECUTE,
        )

    def test_check_permission_admin(self, access_control):
        """Test check permission with ADMIN permission - covers line 177."""
        access_control.grant_permission(
            tenant_id="tenant_123",
            user_id="user_456",
            resource_type=ResourceType.AGENT,
            resource_id="agent_789",
            permission=Permission.ADMIN,
        )

        # ADMIN should grant all permissions
        assert access_control.check_permission(
            tenant_id="tenant_123",
            user_id="user_456",
            resource_type=ResourceType.AGENT,
            resource_id="agent_789",
            permission=Permission.EXECUTE,
        )

    def test_require_permission(self, access_control):
        """Test require permission - covers lines 206-207."""
        access_control.grant_permission(
            tenant_id="tenant_123",
            user_id="user_456",
            resource_type=ResourceType.AGENT,
            resource_id="agent_789",
            permission=Permission.EXECUTE,
        )

        # Should not raise
        access_control.require_permission(
            tenant_id="tenant_123",
            user_id="user_456",
            resource_type=ResourceType.AGENT,
            resource_id="agent_789",
            permission=Permission.EXECUTE,
        )

    def test_require_permission_denied(self, access_control):
        """Test require permission when denied."""
        with pytest.raises(AccessControlError):
            access_control.require_permission(
                tenant_id="tenant_123",
                user_id="user_456",
                resource_type=ResourceType.AGENT,
                resource_id="agent_789",
                permission=Permission.EXECUTE,
            )

    def test_get_user_permissions_nonexistent_tenant(self, access_control):
        """Test get user permissions for nonexistent tenant - covers line 230."""
        perms = access_control.get_user_permissions(tenant_id="nonexistent", user_id="user_456")
        assert perms == {}

    def test_get_user_permissions_nonexistent_user(self, access_control):
        """Test get user permissions for nonexistent user - covers line 234."""
        perms = access_control.get_user_permissions(tenant_id="tenant_123", user_id="nonexistent")
        assert perms == {}

    def test_get_user_permissions_with_resource_type(self, access_control):
        """Test get user permissions with resource type - covers lines 238-241."""
        access_control.grant_permission(
            tenant_id="tenant_123",
            user_id="user_456",
            resource_type=ResourceType.AGENT,
            resource_id="agent_789",
            permission=Permission.EXECUTE,
        )

        perms = access_control.get_user_permissions(
            tenant_id="tenant_123", user_id="user_456", resource_type=ResourceType.AGENT
        )
        assert "agent_789" in perms

    def test_get_user_permissions_without_resource_type(self, access_control):
        """Test get user permissions without resource type - covers lines 244-247."""
        access_control.grant_permission(
            tenant_id="tenant_123",
            user_id="user_456",
            resource_type=ResourceType.AGENT,
            resource_id="agent_789",
            permission=Permission.EXECUTE,
        )
        access_control.grant_permission(
            tenant_id="tenant_123",
            user_id="user_456",
            resource_type=ResourceType.TOOL,
            resource_id="tool_789",
            permission=Permission.READ,
        )

        perms = access_control.get_user_permissions(tenant_id="tenant_123", user_id="user_456")
        assert "agent_789" in perms or "tool_789" in perms

    def test_set_default_permissions(self, access_control):
        """Test set default permissions - covers line 261."""
        access_control.set_default_permissions(
            tenant_id="tenant_123", permissions=[Permission.READ, Permission.EXECUTE]
        )
        perms = access_control.get_default_permissions("tenant_123")
        assert Permission.READ in perms
        assert Permission.EXECUTE in perms

    def test_get_default_permissions(self, access_control):
        """Test get default permissions - covers line 273."""
        perms = access_control.get_default_permissions("tenant_123")
        assert Permission.READ in perms
        assert Permission.EXECUTE in perms


class TestAgentGenerator:
    """Test agent generator."""

    @pytest.fixture
    def mock_gateway(self):
        """Create mock gateway."""
        gateway = Mock()
        gateway.generate_async = AsyncMock(
            return_value=MagicMock(
                text='{"name": "Test Agent", "description": "Test", "capabilities": ["cap1"], "system_prompt": "Test", "required_tools": [], "memory_config": {"max_episodic": 500}, "max_context_tokens": 4000, "enable_tool_calling": true}'
            )
        )
        return gateway

    @pytest.fixture
    def generator(self, mock_gateway):
        """Create agent generator."""
        return AgentGenerator(gateway=mock_gateway)

    @pytest.mark.asyncio
    async def test_generate_agent_from_prompt(self, generator):
        """Test generate agent from prompt."""
        with patch("src.core.prompt_based_generator.agent_generator.Agent") as mock_agent_class:
            mock_agent = Mock()
            mock_agent.agent_id = "agent_123"
            mock_agent.capabilities = []
            mock_agent_class.return_value = mock_agent

            agent = await generator.generate_agent_from_prompt(
                prompt="Create a helpful assistant", agent_id="agent_123"
            )
            assert agent.agent_id == "agent_123"

    @pytest.mark.asyncio
    async def test_generate_agent_from_prompt_with_memory(self, generator):
        """Test generate agent from prompt with memory config."""
        with patch("src.core.prompt_based_generator.agent_generator.Agent") as mock_agent_class:
            mock_agent = Mock()
            mock_agent.agent_id = "agent_123"
            mock_agent.capabilities = []
            mock_agent.attach_memory = Mock()
            mock_agent_class.return_value = mock_agent

            agent = await generator.generate_agent_from_prompt(
                prompt="Create a helpful assistant", agent_id="agent_123"
            )
            mock_agent.attach_memory.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_agent_from_prompt_error(self, generator):
        """Test generate agent from prompt with error."""
        generator.interpreter.interpret_agent_prompt = AsyncMock(side_effect=Exception("Error"))

        with pytest.raises(AgentGenerationError):
            await generator.generate_agent_from_prompt(prompt="Create a helpful assistant")

    @pytest.mark.asyncio
    async def test_generate_agent_from_cached_config(self, generator):
        """Test generate agent from cached config."""
        mock_config = {
            "name": "Cached Agent",
            "description": "Cached",
            "capabilities": ["cap1"],
            "system_prompt": "Cached",
            "max_context_tokens": 4000,
        }
        generator.cache.get_cached_agent_config = AsyncMock(return_value=mock_config)

        with patch("src.core.prompt_based_generator.agent_generator.Agent") as mock_agent_class:
            mock_agent = Mock()
            mock_agent.capabilities = []
            mock_agent_class.return_value = mock_agent

            agent = await generator.generate_agent_from_cached_config(
                agent_id="agent_123", tenant_id="tenant_123"
            )
            assert agent is not None

    @pytest.mark.asyncio
    async def test_generate_agent_from_cached_config_not_found(self, generator):
        """Test generate agent from cached config when not found."""
        generator.cache.get_cached_agent_config = AsyncMock(return_value=None)

        agent = await generator.generate_agent_from_cached_config(
            agent_id="agent_123", tenant_id="tenant_123"
        )
        assert agent is None

    @pytest.mark.asyncio
    async def test_generate_agent_from_cached_config_error(self, generator):
        """Test generate agent from cached config with error."""
        mock_config = {"name": "Cached Agent"}
        generator.cache.get_cached_agent_config = AsyncMock(return_value=mock_config)

        with patch("src.core.prompt_based_generator.agent_generator.Agent") as mock_agent_class:
            mock_agent_class.side_effect = Exception("Error")

            agent = await generator.generate_agent_from_cached_config(
                agent_id="agent_123", tenant_id="tenant_123"
            )
            assert agent is None


class TestToolGenerator:
    """Test tool generator."""

    @pytest.fixture
    def mock_gateway(self):
        """Create mock gateway."""
        gateway = Mock()
        gateway.generate_async = AsyncMock(
            return_value=MagicMock(
                text='{"name": "Test Tool", "description": "Test", "function_name": "test_func", "parameters": [], "return_type": "int", "code_template": "def test_func() -> int:\\n    return 42"}'
            )
        )
        return gateway

    @pytest.fixture
    def generator(self, mock_gateway):
        """Create tool generator."""
        return ToolGenerator(gateway=mock_gateway)

    def test_validate_code_valid(self, generator):
        """Test validate code with valid code."""
        code = "def test_func() -> int:\n    return 42"
        is_valid, errors = generator._validate_code(code)
        assert is_valid
        assert len(errors) == 0

    def test_validate_code_syntax_error(self, generator):
        """Test validate code with syntax error."""
        code = "def test_func() -> int:\n    if True\n        return 42"  # Missing colon - syntax error
        is_valid, errors = generator._validate_code(code)
        assert not is_valid
        assert len(errors) > 0

    def test_validate_code_dangerous_import(self, generator):
        """Test validate code with dangerous import."""
        code = "import os\ndef test_func():\n    pass"
        is_valid, errors = generator._validate_code(code)
        assert not is_valid
        assert any("Dangerous import" in err for err in errors)

    def test_create_function_from_code(self, generator):
        """Test create function from code."""
        code = "def test_func() -> int:\n    return 42"
        func = generator._create_function_from_code(code, "test_func")
        assert func is not None
        assert func() == 42

    def test_create_function_from_code_syntax_error(self, generator):
        """Test create function from code with syntax error."""
        code = "def test_func() -> int:\n    if True\n        return 42"  # Missing colon - syntax error
        with pytest.raises(CodeValidationError):
            generator._create_function_from_code(code, "test_func")

    def test_create_function_from_code_dangerous_import(self, generator):
        """Test create function from code with dangerous import."""
        code = "import os\ndef test_func():\n    pass"
        with pytest.raises(CodeValidationError):
            generator._create_function_from_code(code, "test_func")

    @pytest.mark.asyncio
    async def test_generate_tool_from_prompt(self, generator):
        """Test generate tool from prompt."""
        with patch("src.core.prompt_based_generator.tool_generator.Tool") as mock_tool_class:
            mock_tool = Mock()
            mock_tool.tool_id = "tool_123"
            mock_tool_class.return_value = mock_tool

            tool = await generator.generate_tool_from_prompt(
                prompt="Create a tool that returns 42", tool_id="tool_123"
            )
            assert tool.tool_id == "tool_123"

    @pytest.mark.asyncio
    async def test_generate_tool_from_prompt_invalid_code(self, generator):
        """Test generate tool from prompt with invalid code."""
        generator.interpreter.interpret_tool_prompt = AsyncMock(
            return_value=ToolRequirements(
                name="Test Tool",
                description="Test",
                function_name="test_func",
                parameters=[],
                return_type="int",
                code_template="invalid code syntax",
            )
        )

        with pytest.raises(CodeValidationError):
            await generator.generate_tool_from_prompt(prompt="Create a tool")

    @pytest.mark.asyncio
    async def test_generate_tool_from_prompt_no_function(self, generator):
        """Test generate tool from prompt when function extraction fails."""
        generator._create_function_from_code = Mock(return_value=None)

        generator.interpreter.interpret_tool_prompt = AsyncMock(
            return_value=ToolRequirements(
                name="Test Tool",
                description="Test",
                function_name="test_func",
                parameters=[],
                return_type="int",
                code_template="def other_func():\n    pass",
            )
        )

        with pytest.raises(ToolGenerationError):
            await generator.generate_tool_from_prompt(prompt="Create a tool")


class TestGeneratorCache:
    """Test generator cache."""

    @pytest.fixture
    def mock_cache(self):
        """Create mock cache."""
        cache = AsyncMock()
        return cache

    @pytest.fixture
    def generator_cache(self, mock_cache):
        """Create generator cache."""
        with patch("src.core.prompt_based_generator.generator_cache.CacheMechanism") as mock_cache_class:
            mock_cache_instance = Mock()
            mock_cache_instance.set = AsyncMock()
            mock_cache_instance.get = AsyncMock()
            mock_cache_instance.invalidate_pattern = AsyncMock()
            mock_cache_class.return_value = mock_cache_instance
            cache = GeneratorCache()
            cache.cache = mock_cache_instance
            return cache

    @pytest.mark.asyncio
    async def test_cache_prompt_interpretation(self, generator_cache):
        """Test cache prompt interpretation."""
        interpretation = {"name": "Test", "description": "Test"}
        await generator_cache.cache_prompt_interpretation(
            prompt_hash="hash123", interpretation=interpretation
        )
        generator_cache.cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cached_interpretation(self, generator_cache):
        """Test get cached interpretation."""
        interpretation = {"name": "Test", "description": "Test"}
        generator_cache.cache.get = AsyncMock(return_value=json.dumps(interpretation))

        result = await generator_cache.get_cached_interpretation(prompt_hash="hash123")
        assert result == interpretation

    @pytest.mark.asyncio
    async def test_get_cached_interpretation_not_found(self, generator_cache):
        """Test get cached interpretation when not found."""
        generator_cache.cache.get = AsyncMock(return_value=None)

        result = await generator_cache.get_cached_interpretation(prompt_hash="hash123")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_cached_interpretation_invalid_json(self, generator_cache):
        """Test get cached interpretation with invalid JSON."""
        generator_cache.cache.get = AsyncMock(return_value="invalid json")

        result = await generator_cache.get_cached_interpretation(prompt_hash="hash123")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_agent_config(self, generator_cache):
        """Test cache agent config."""
        config = {"name": "Test Agent", "description": "Test"}
        await generator_cache.cache_agent_config(agent_id="agent_123", config=config)
        generator_cache.cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cached_agent_config(self, generator_cache):
        """Test get cached agent config."""
        config = {"name": "Test Agent", "description": "Test"}
        generator_cache.cache.get = AsyncMock(return_value=json.dumps(config))

        result = await generator_cache.get_cached_agent_config(agent_id="agent_123")
        assert result == config

    @pytest.mark.asyncio
    async def test_cache_tool_schema(self, generator_cache):
        """Test cache tool schema."""
        schema = {"name": "Test Tool", "description": "Test"}
        await generator_cache.cache_tool_schema(tool_id="tool_123", schema=schema)
        generator_cache.cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cached_tool_schema(self, generator_cache):
        """Test get cached tool schema."""
        schema = {"name": "Test Tool", "description": "Test"}
        generator_cache.cache.get = AsyncMock(return_value=json.dumps(schema))

        result = await generator_cache.get_cached_tool_schema(tool_id="tool_123")
        assert result == schema

    @pytest.mark.asyncio
    async def test_cache_tool_code(self, generator_cache):
        """Test cache tool code."""
        code = "def test_func():\n    pass"
        await generator_cache.cache_tool_code(tool_id="tool_123", code=code)
        generator_cache.cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cached_tool_code(self, generator_cache):
        """Test get cached tool code."""
        code = "def test_func():\n    pass"
        generator_cache.cache.get = AsyncMock(return_value=code)

        result = await generator_cache.get_cached_tool_code(tool_id="tool_123")
        assert result == code

    @pytest.mark.asyncio
    async def test_invalidate_pattern(self, generator_cache):
        """Test invalidate pattern."""
        await generator_cache.invalidate_pattern(pattern="agent_*")
        generator_cache.cache.invalidate_pattern.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_all(self, generator_cache):
        """Test clear all."""
        await generator_cache.clear_all()
        generator_cache.cache.invalidate_pattern.assert_called_once()


class TestFeedbackCollector:
    """Test feedback collector."""

    @pytest.fixture
    def feedback_collector(self):
        """Create feedback collector."""
        return FeedbackCollector()

    @pytest.mark.asyncio
    async def test_collect_agent_feedback(self, feedback_collector):
        """Test collect agent feedback."""
        feedback_id = await feedback_collector.collect_agent_feedback(
            agent_id="agent_123",
            rating=5,
            user_id="user_456",
            tenant_id="tenant_123",
            feedback_text="Great!",
        )
        assert feedback_id == "agent_123"

    @pytest.mark.asyncio
    async def test_collect_agent_feedback_with_loop(self, feedback_collector):
        """Test collect agent feedback with feedback loop."""
        mock_loop = AsyncMock()
        feedback_collector.feedback_loop = mock_loop

        await feedback_collector.collect_agent_feedback(
            agent_id="agent_123",
            rating=5,
            user_id="user_456",
            tenant_id="tenant_123",
        )
        mock_loop.record_feedback.assert_called_once()

    @pytest.mark.asyncio
    async def test_collect_tool_feedback(self, feedback_collector):
        """Test collect tool feedback."""
        feedback_id = await feedback_collector.collect_tool_feedback(
            tool_id="tool_123",
            rating=4,
            user_id="user_456",
            tenant_id="tenant_123",
            feedback_text="Good!",
        )
        assert feedback_id == "tool_123"

    @pytest.mark.asyncio
    async def test_collect_tool_feedback_with_loop(self, feedback_collector):
        """Test collect tool feedback with feedback loop."""
        mock_loop = AsyncMock()
        feedback_collector.feedback_loop = mock_loop

        await feedback_collector.collect_tool_feedback(
            tool_id="tool_123",
            rating=4,
            user_id="user_456",
            tenant_id="tenant_123",
        )
        mock_loop.record_feedback.assert_called_once()

    def test_get_agent_feedback_stats(self, feedback_collector):
        """Test get agent feedback stats."""
        # No feedback yet
        stats = feedback_collector.get_agent_feedback_stats(agent_id="agent_123")
        assert stats["total_feedback"] == 0

    def test_get_agent_feedback_stats_with_feedback(self, feedback_collector):
        """Test get agent feedback stats with feedback."""
        import asyncio

        asyncio.run(
            feedback_collector.collect_agent_feedback(
                agent_id="agent_123",
                rating=5,
                user_id="user_456",
                tenant_id="tenant_123",
            )
        )

        stats = feedback_collector.get_agent_feedback_stats(agent_id="agent_123")
        assert stats["total_feedback"] == 1
        assert stats["average_rating"] == 5.0

    def test_get_agent_feedback_stats_with_tenant_filter(self, feedback_collector):
        """Test get agent feedback stats with tenant filter."""
        import asyncio

        asyncio.run(
            feedback_collector.collect_agent_feedback(
                agent_id="agent_123",
                rating=5,
                user_id="user_456",
                tenant_id="tenant_123",
            )
        )

        stats = feedback_collector.get_agent_feedback_stats(
            agent_id="agent_123", tenant_id="different_tenant"
        )
        assert stats["total_feedback"] == 0

    def test_get_tool_feedback_stats(self, feedback_collector):
        """Test get tool feedback stats."""
        stats = feedback_collector.get_tool_feedback_stats(tool_id="tool_123")
        assert stats["total_feedback"] == 0

    def test_get_tool_feedback_stats_with_feedback(self, feedback_collector):
        """Test get tool feedback stats with feedback."""
        import asyncio

        asyncio.run(
            feedback_collector.collect_tool_feedback(
                tool_id="tool_123",
                rating=4,
                user_id="user_456",
                tenant_id="tenant_123",
            )
        )

        stats = feedback_collector.get_tool_feedback_stats(tool_id="tool_123")
        assert stats["total_feedback"] == 1
        assert stats["average_rating"] == 4.0


class TestFunctions:
    """Test high-level functions."""

    @pytest.fixture
    def mock_gateway(self):
        """Create mock gateway."""
        gateway = Mock()
        gateway.generate_async = AsyncMock(
            return_value=MagicMock(
                text='{"name": "Test Agent", "description": "Test", "capabilities": [], "system_prompt": "Test", "required_tools": [], "memory_config": {}, "max_context_tokens": 4000, "enable_tool_calling": true}'
            )
        )
        return gateway

    @pytest.mark.asyncio
    async def test_create_agent_from_prompt(self, mock_gateway):
        """Test create agent from prompt."""
        with patch("src.core.prompt_based_generator.functions.AgentGenerator") as mock_gen_class:
            mock_generator = AsyncMock()
            mock_agent = Mock()
            mock_agent.agent_id = "agent_123"
            mock_generator.generate_agent_from_prompt = AsyncMock(return_value=mock_agent)
            mock_gen_class.return_value = mock_generator

            agent = await create_agent_from_prompt(
                prompt="Create a helpful assistant", gateway=mock_gateway, user_id="user_123", tenant_id="tenant_123"
            )
            assert agent.agent_id == "agent_123"

    @pytest.mark.asyncio
    async def test_create_agent_from_prompt_empty(self, mock_gateway):
        """Test create agent from prompt with empty prompt - covers line 63."""
        with pytest.raises(AgentGenerationError):
            await create_agent_from_prompt(prompt="", gateway=mock_gateway)

    @pytest.mark.asyncio
    async def test_create_agent_from_prompt_error(self, mock_gateway):
        """Test create agent from prompt with error - covers line 94."""
        with patch("src.core.prompt_based_generator.functions.AgentGenerator") as mock_gen_class:
            mock_generator = AsyncMock()
            mock_generator.generate_agent_from_prompt = AsyncMock(side_effect=Exception("Error"))
            mock_gen_class.return_value = mock_generator

            with pytest.raises(AgentGenerationError):
                await create_agent_from_prompt(prompt="Create agent", gateway=mock_gateway)

    @pytest.mark.asyncio
    async def test_create_tool_from_prompt(self, mock_gateway):
        """Test create tool from prompt."""
        mock_gateway.generate_async = AsyncMock(
            return_value=MagicMock(
                text='{"name": "Test Tool", "description": "Test", "function_name": "test_func", "parameters": [], "return_type": "int", "code_template": "def test_func() -> int:\\n    return 42"}'
            )
        )

        with patch("src.core.prompt_based_generator.functions.ToolGenerator") as mock_gen_class:
            mock_generator = AsyncMock()
            mock_tool = Mock()
            mock_tool.tool_id = "tool_123"
            mock_generator.generate_tool_from_prompt = AsyncMock(return_value=mock_tool)
            mock_gen_class.return_value = mock_generator

            tool = await create_tool_from_prompt(
                prompt="Create a tool", gateway=mock_gateway, user_id="user_123", tenant_id="tenant_123"
            )
            assert tool.tool_id == "tool_123"

    @pytest.mark.asyncio
    async def test_create_tool_from_prompt_empty(self, mock_gateway):
        """Test create tool from prompt with empty prompt - covers line 143."""
        with pytest.raises(ToolGenerationError):
            await create_tool_from_prompt(prompt="", gateway=mock_gateway)

    @pytest.mark.asyncio
    async def test_rate_agent(self):
        """Test rate agent."""
        mock_collector = AsyncMock()
        mock_collector.collect_agent_feedback = AsyncMock(return_value="feedback_123")

        feedback_id = await rate_agent(
            agent_id="agent_123",
            rating=5,
            user_id="user_456",
            tenant_id="tenant_123",
            feedback_collector=mock_collector,
        )
        assert feedback_id == "feedback_123"

    @pytest.mark.asyncio
    async def test_rate_tool(self):
        """Test rate tool."""
        mock_collector = AsyncMock()
        mock_collector.collect_tool_feedback = AsyncMock(return_value="feedback_123")

        feedback_id = await rate_tool(
            tool_id="tool_123",
            rating=4,
            user_id="user_456",
            tenant_id="tenant_123",
            feedback_collector=mock_collector,
        )
        assert feedback_id == "feedback_123"

    def test_grant_permission(self):
        """Test grant permission."""
        mock_ac = Mock()
        grant_permission(
            tenant_id="tenant_123",
            user_id="user_456",
            resource_type="agent",
            resource_id="agent_789",
            permission="execute",
            access_control=mock_ac,
        )
        mock_ac.grant_permission.assert_called_once()

    def test_check_permission(self):
        """Test check permission."""
        mock_ac = Mock()
        mock_ac.check_permission.return_value = True

        result = check_permission(
            tenant_id="tenant_123",
            user_id="user_456",
            resource_type="agent",
            resource_id="agent_789",
            permission="execute",
            access_control=mock_ac,
        )
        assert result is True

    def test_get_agent_feedback_stats(self):
        """Test get agent feedback stats."""
        mock_collector = Mock()
        mock_collector.get_agent_feedback_stats.return_value = {"total_feedback": 5}

        stats = get_agent_feedback_stats(
            agent_id="agent_123", feedback_collector=mock_collector
        )
        assert stats["total_feedback"] == 5

    def test_get_tool_feedback_stats(self):
        """Test get tool feedback stats."""
        mock_collector = Mock()
        mock_collector.get_tool_feedback_stats.return_value = {"total_feedback": 3}

        stats = get_tool_feedback_stats(tool_id="tool_123", feedback_collector=mock_collector)
        assert stats["total_feedback"] == 3


class TestExceptions:
    """Test exception classes."""

    def test_prompt_interpretation_error(self):
        """Test PromptInterpretationError initialization - covers lines 44-46."""
        error = PromptInterpretationError(
            message="Test error", prompt="test prompt", reason="test_reason"
        )
        assert error.prompt == "test prompt"
        assert error.reason == "test_reason"

    def test_agent_generation_error(self):
        """Test AgentGenerationError initialization - covers lines 77-80."""
        error = AgentGenerationError(
            message="Test error", prompt="test prompt", agent_id="agent_123", stage="test_stage"
        )
        assert error.prompt == "test prompt"
        assert error.agent_id == "agent_123"
        assert error.stage == "test_stage"

    def test_tool_generation_error(self):
        """Test ToolGenerationError initialization - covers lines 111-114."""
        error = ToolGenerationError(
            message="Test error", prompt="test prompt", tool_id="tool_123", stage="test_stage"
        )
        assert error.prompt == "test prompt"
        assert error.tool_id == "tool_123"
        assert error.stage == "test_stage"

    def test_code_validation_error(self):
        """Test CodeValidationError initialization - covers lines 142-144."""
        error = CodeValidationError(
            message="Test error", code="test code", validation_errors=["error1", "error2"]
        )
        assert error.code == "test code"
        assert len(error.validation_errors) == 2

    def test_access_control_error(self):
        """Test AccessControlError initialization - covers lines 181-186."""
        error = AccessControlError(
            message="Test error",
            tenant_id="tenant_123",
            user_id="user_456",
            resource_type="agent",
            resource_id="agent_789",
            permission="execute",
        )
        assert error.tenant_id == "tenant_123"
        assert error.user_id == "user_456"
        assert error.resource_type == "agent"
        assert error.resource_id == "agent_789"
        assert error.permission == "execute"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
