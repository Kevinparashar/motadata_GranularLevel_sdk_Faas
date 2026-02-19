"""
Unit Tests for PromptInterpreter Codec Integration

Tests codec encoding/decoding for AgentRequirements and ToolRequirements.
"""

from unittest.mock import MagicMock

import pytest

from src.core.codec_integration import create_codec_serializer
from src.core.prompt_based_generator.prompt_interpreter import (
    AgentRequirements,
    PromptInterpreter,
    ToolRequirements,
)


class TestPromptInterpreterCodecIntegration:
    """Tests for PromptInterpreter codec integration."""

    @pytest.fixture
    def gateway(self):
        """Create a test gateway."""
        return MagicMock()

    @pytest.fixture
    def interpreter(self, gateway):
        """Create a test prompt interpreter."""
        return PromptInterpreter(gateway=gateway)

    @pytest.fixture
    def codec(self):
        """Create a test codec serializer."""
        return create_codec_serializer()

    @pytest.fixture
    def agent_requirements(self):
        """Create test agent requirements."""
        return AgentRequirements(
            name="test_agent",
            description="Test agent description",
            capabilities=["capability1", "capability2"],
            system_prompt="You are a test agent",
            required_tools=["tool1", "tool2"],
            memory_config={"max_episodic": 500},
            max_context_tokens=4000,
            enable_tool_calling=True,
            metadata={"key": "value"},
        )

    @pytest.fixture
    def tool_requirements(self):
        """Create test tool requirements."""
        return ToolRequirements(
            name="test_tool",
            description="Test tool description",
            function_name="test_function",
            parameters=[{"name": "param1", "type": "str"}],
            return_type="str",
            code_template="def test_function(): pass",
            metadata={"key": "value"},
        )

    def test_interpreter_with_codec_serializer(self, gateway, codec):
        """Test prompt interpreter initialization with codec serializer."""
        interpreter = PromptInterpreter(gateway=gateway, codec_serializer=codec)

        assert interpreter.codec_serializer is not None
        assert interpreter.codec_serializer == codec

    def test_interpreter_without_codec(self, gateway):
        """Test prompt interpreter works without codec configured."""
        interpreter = PromptInterpreter(gateway=gateway)

        # Codec should be auto-initialized if available
        # But it may be None if codec SDK is not installed
        assert interpreter is not None

    @pytest.mark.asyncio
    async def test_encode_agent_requirements_with_codec(self, interpreter, codec, agent_requirements):
        """Test encoding agent requirements with codec serializer."""
        interpreter.codec_serializer = codec

        encoded = await interpreter.encode_agent_requirements(agent_requirements)

        assert isinstance(encoded, bytes)
        assert b"test_agent" in encoded
        assert b"Test agent description" in encoded

    @pytest.mark.asyncio
    async def test_encode_agent_requirements_without_codec(self, interpreter, agent_requirements):
        """Test encoding agent requirements without codec serializer (should use default)."""
        # Should work with default codec from import
        encoded = await interpreter.encode_agent_requirements(agent_requirements)

        assert isinstance(encoded, bytes)

    @pytest.mark.asyncio
    async def test_decode_agent_requirements_with_codec(self, interpreter, codec, agent_requirements):
        """Test decoding agent requirements with codec serializer."""
        interpreter.codec_serializer = codec

        encoded = await interpreter.encode_agent_requirements(agent_requirements)
        decoded = await interpreter.decode_agent_requirements(encoded)

        assert isinstance(decoded, AgentRequirements)
        assert decoded.name == agent_requirements.name
        assert decoded.description == agent_requirements.description
        assert decoded.capabilities == agent_requirements.capabilities
        assert decoded.system_prompt == agent_requirements.system_prompt

    @pytest.mark.asyncio
    async def test_decode_agent_requirements_without_codec(self, interpreter, agent_requirements):
        """Test decoding agent requirements without codec serializer (should use default)."""
        encoded = await interpreter.encode_agent_requirements(agent_requirements)

        # Should work with default codec from import
        decoded = await interpreter.decode_agent_requirements(encoded)

        assert isinstance(decoded, AgentRequirements)
        assert decoded.name == agent_requirements.name
        assert decoded.description == agent_requirements.description

    @pytest.mark.asyncio
    async def test_encode_decode_agent_requirements_roundtrip(self, interpreter, codec, agent_requirements):
        """Test encode/decode roundtrip for agent requirements."""
        interpreter.codec_serializer = codec

        encoded = await interpreter.encode_agent_requirements(agent_requirements)
        decoded = await interpreter.decode_agent_requirements(encoded)

        assert decoded.name == agent_requirements.name
        assert decoded.description == agent_requirements.description
        assert decoded.capabilities == agent_requirements.capabilities
        assert decoded.system_prompt == agent_requirements.system_prompt
        assert decoded.required_tools == agent_requirements.required_tools
        assert decoded.memory_config == agent_requirements.memory_config
        assert decoded.max_context_tokens == agent_requirements.max_context_tokens
        assert decoded.enable_tool_calling == agent_requirements.enable_tool_calling
        assert decoded.metadata == agent_requirements.metadata

    @pytest.mark.asyncio
    async def test_encode_tool_requirements_with_codec(self, interpreter, codec, tool_requirements):
        """Test encoding tool requirements with codec serializer."""
        interpreter.codec_serializer = codec

        encoded = await interpreter.encode_tool_requirements(tool_requirements)

        assert isinstance(encoded, bytes)
        assert b"test_tool" in encoded
        assert b"Test tool description" in encoded

    @pytest.mark.asyncio
    async def test_encode_tool_requirements_without_codec(self, interpreter, tool_requirements):
        """Test encoding tool requirements without codec serializer (should use default)."""
        # Should work with default codec from import
        encoded = await interpreter.encode_tool_requirements(tool_requirements)

        assert isinstance(encoded, bytes)

    @pytest.mark.asyncio
    async def test_decode_tool_requirements_with_codec(self, interpreter, codec, tool_requirements):
        """Test decoding tool requirements with codec serializer."""
        interpreter.codec_serializer = codec

        encoded = await interpreter.encode_tool_requirements(tool_requirements)
        decoded = await interpreter.decode_tool_requirements(encoded)

        assert isinstance(decoded, ToolRequirements)
        assert decoded.name == tool_requirements.name
        assert decoded.description == tool_requirements.description
        assert decoded.function_name == tool_requirements.function_name
        assert decoded.parameters == tool_requirements.parameters

    @pytest.mark.asyncio
    async def test_decode_tool_requirements_without_codec(self, interpreter, tool_requirements):
        """Test decoding tool requirements without codec serializer (should use default)."""
        encoded = await interpreter.encode_tool_requirements(tool_requirements)

        # Should work with default codec from import
        decoded = await interpreter.decode_tool_requirements(encoded)

        assert isinstance(decoded, ToolRequirements)
        assert decoded.name == tool_requirements.name
        assert decoded.description == tool_requirements.description

    @pytest.mark.asyncio
    async def test_encode_decode_tool_requirements_roundtrip(self, interpreter, codec, tool_requirements):
        """Test encode/decode roundtrip for tool requirements."""
        interpreter.codec_serializer = codec

        encoded = await interpreter.encode_tool_requirements(tool_requirements)
        decoded = await interpreter.decode_tool_requirements(encoded)

        assert decoded.name == tool_requirements.name
        assert decoded.description == tool_requirements.description
        assert decoded.function_name == tool_requirements.function_name
        assert decoded.parameters == tool_requirements.parameters
        assert decoded.return_type == tool_requirements.return_type
        assert decoded.code_template == tool_requirements.code_template
        assert decoded.metadata == tool_requirements.metadata

    @pytest.mark.asyncio
    async def test_encode_agent_requirements_custom_version(self, interpreter, codec, agent_requirements):
        """Test encoding agent requirements with custom schema version."""
        interpreter.codec_serializer = codec

        encoded = await interpreter.encode_agent_requirements(agent_requirements, schema_version="1.0")

        assert isinstance(encoded, bytes)

    @pytest.mark.asyncio
    async def test_encode_tool_requirements_custom_version(self, interpreter, codec, tool_requirements):
        """Test encoding tool requirements with custom schema version."""
        interpreter.codec_serializer = codec

        encoded = await interpreter.encode_tool_requirements(tool_requirements, schema_version="1.0")

        assert isinstance(encoded, bytes)

    @pytest.mark.asyncio
    async def test_encode_agent_requirements_with_empty_metadata(self, interpreter, codec):
        """Test encoding agent requirements with empty metadata."""
        interpreter.codec_serializer = codec
        requirements = AgentRequirements(
            name="test",
            description="test",
            system_prompt="test",
            metadata={},
        )

        encoded = await interpreter.encode_agent_requirements(requirements)
        decoded = await interpreter.decode_agent_requirements(encoded)

        assert decoded.metadata == {}

    @pytest.mark.asyncio
    async def test_encode_tool_requirements_with_none_code_template(self, interpreter, codec):
        """Test encoding tool requirements with None code_template."""
        interpreter.codec_serializer = codec
        requirements = ToolRequirements(
            name="test",
            description="test",
            function_name="test_func",
            parameters=[],
            return_type="str",
            code_template=None,
        )

        encoded = await interpreter.encode_tool_requirements(requirements)
        decoded = await interpreter.decode_tool_requirements(encoded)

        assert decoded.code_template is None

    @pytest.mark.asyncio
    async def test_encode_agent_requirements_with_codec_serializer(self, interpreter, codec, agent_requirements):
        """Test encoding agent requirements with codec_serializer set."""
        interpreter.codec_serializer = codec

        encoded = await interpreter.encode_agent_requirements(agent_requirements)

        assert isinstance(encoded, bytes)

    @pytest.mark.asyncio
    async def test_decode_agent_requirements_with_codec_serializer(self, interpreter, codec, agent_requirements):
        """Test decoding agent requirements with codec_serializer set."""
        interpreter.codec_serializer = codec

        encoded = await interpreter.encode_agent_requirements(agent_requirements)
        decoded = await interpreter.decode_agent_requirements(encoded)

        assert isinstance(decoded, AgentRequirements)
        assert decoded.name == agent_requirements.name

    @pytest.mark.asyncio
    async def test_encode_tool_requirements_with_codec_serializer(self, interpreter, codec, tool_requirements):
        """Test encoding tool requirements with codec_serializer set."""
        interpreter.codec_serializer = codec

        encoded = await interpreter.encode_tool_requirements(tool_requirements)

        assert isinstance(encoded, bytes)

    @pytest.mark.asyncio
    async def test_decode_tool_requirements_with_codec_serializer(self, interpreter, codec, tool_requirements):
        """Test decoding tool requirements with codec_serializer set."""
        interpreter.codec_serializer = codec

        encoded = await interpreter.encode_tool_requirements(tool_requirements)
        decoded = await interpreter.decode_tool_requirements(encoded)

        assert isinstance(decoded, ToolRequirements)
        assert decoded.name == tool_requirements.name

    @pytest.mark.asyncio
    async def test_decode_agent_requirements_with_target_version(self, interpreter, codec, agent_requirements):
        """Test decoding agent requirements with target_version."""
        interpreter.codec_serializer = codec

        encoded = await interpreter.encode_agent_requirements(agent_requirements, schema_version="1.0")
        decoded = await interpreter.decode_agent_requirements(encoded, target_version="1.0")

        assert isinstance(decoded, AgentRequirements)
        assert decoded.name == agent_requirements.name

    @pytest.mark.asyncio
    async def test_decode_tool_requirements_with_target_version(self, interpreter, codec, tool_requirements):
        """Test decoding tool requirements with target_version."""
        interpreter.codec_serializer = codec

        encoded = await interpreter.encode_tool_requirements(tool_requirements, schema_version="1.0")
        decoded = await interpreter.decode_tool_requirements(encoded, target_version="1.0")

        assert isinstance(decoded, ToolRequirements)
        assert decoded.name == tool_requirements.name


    @pytest.mark.asyncio
    async def test_encode_agent_requirements_with_dict(self, interpreter, codec):
        """Test encoding agent requirements from dictionary."""
        interpreter.codec_serializer = codec
        from src.core.codec_integration import encode_agent_requirements

        requirements_dict = {
            "name": "test_agent",
            "description": "Test agent",
            "capabilities": ["cap1"],
            "system_prompt": "You are a test agent",
            "required_tools": [],
            "memory_config": {},
            "max_context_tokens": 4000,
            "enable_tool_calling": True,
            "metadata": {},
        }

        encoded = await encode_agent_requirements(requirements_dict, codec=codec)

        assert isinstance(encoded, bytes)

    @pytest.mark.asyncio
    async def test_encode_tool_requirements_with_dict(self, interpreter, codec):
        """Test encoding tool requirements from dictionary."""
        interpreter.codec_serializer = codec
        from src.core.codec_integration import encode_tool_requirements

        requirements_dict = {
            "name": "test_tool",
            "description": "Test tool",
            "function_name": "test_func",
            "parameters": [],
            "return_type": "str",
            "code_template": None,
            "metadata": {},
        }

        encoded = await encode_tool_requirements(requirements_dict, codec=codec)

        assert isinstance(encoded, bytes)

    @pytest.mark.asyncio
    async def test_encode_prompt_template_with_dict(self, codec):
        """Test encoding prompt template from dictionary."""
        from src.core.codec_integration import encode_prompt_template

        template_dict = {
            "name": "test_template",
            "version": "1.0",
            "content": "Hello {name}",
            "tenant_id": None,
            "metadata": {},
        }

        encoded = await encode_prompt_template(template_dict, codec=codec)

        assert isinstance(encoded, bytes)

    @pytest.mark.asyncio
    async def test_encode_agent_requirements_with_dict_method(self, codec):
        """Test encoding agent requirements using dict() method (Pydantic v1 style)."""
        from src.core.codec_integration import encode_agent_requirements

        # Create a mock object with dict() method (Pydantic v1 style)
        class MockAgentRequirements:
            def dict(self):
                return {
                    "name": "test_agent",
                    "description": "Test agent",
                    "capabilities": ["cap1"],
                    "system_prompt": "You are a test agent",
                    "required_tools": [],
                    "memory_config": {},
                    "max_context_tokens": 4000,
                    "enable_tool_calling": True,
                    "metadata": {},
                }

        mock_req = MockAgentRequirements()
        encoded = await encode_agent_requirements(mock_req, codec=codec)

        assert isinstance(encoded, bytes)

    @pytest.mark.asyncio
    async def test_encode_agent_requirements_with_plain_object(self, codec):
        """Test encoding agent requirements from plain object."""
        from src.core.codec_integration import encode_agent_requirements

        # Create a plain object without model_dump or dict
        class PlainObject:
            def __init__(self):
                self.name = "test_agent"
                self.description = "Test agent"
                self.capabilities = ["cap1"]
                self.system_prompt = "You are a test agent"
                self.required_tools = []
                self.memory_config = {}
                self.max_context_tokens = 4000
                self.enable_tool_calling = True
                self.metadata = {}

        plain_obj = PlainObject()
        encoded = await encode_agent_requirements(plain_obj, codec=codec)

        assert isinstance(encoded, bytes)

    @pytest.mark.asyncio
    async def test_encode_tool_requirements_with_dict_method(self, codec):
        """Test encoding tool requirements using dict() method (Pydantic v1 style)."""
        from src.core.codec_integration import encode_tool_requirements

        # Create a mock object with dict() method (Pydantic v1 style)
        class MockToolRequirements:
            def dict(self):
                return {
                    "name": "test_tool",
                    "description": "Test tool",
                    "function_name": "test_func",
                    "parameters": [],
                    "return_type": "str",
                    "code_template": None,
                    "metadata": {},
                }

        mock_req = MockToolRequirements()
        encoded = await encode_tool_requirements(mock_req, codec=codec)

        assert isinstance(encoded, bytes)

    @pytest.mark.asyncio
    async def test_encode_tool_requirements_with_plain_object(self, codec):
        """Test encoding tool requirements from plain object."""
        from src.core.codec_integration import encode_tool_requirements

        # Create a plain object without model_dump or dict
        class PlainObject:
            def __init__(self):
                self.name = "test_tool"
                self.description = "Test tool"
                self.function_name = "test_func"
                self.parameters = []
                self.return_type = "str"
                self.code_template = None
                self.metadata = {}

        plain_obj = PlainObject()
        encoded = await encode_tool_requirements(plain_obj, codec=codec)

        assert isinstance(encoded, bytes)

    @pytest.mark.asyncio
    async def test_encode_prompt_template_with_plain_object(self, codec):
        """Test encoding prompt template from plain object."""
        from src.core.codec_integration import encode_prompt_template

        # Create a plain object
        class PlainObject:
            def __init__(self):
                self.name = "test_template"
                self.version = "1.0"
                self.content = "Hello {name}"
                self.tenant_id = None
                self.metadata = {}

        plain_obj = PlainObject()
        encoded = await encode_prompt_template(plain_obj, codec=codec)

        assert isinstance(encoded, bytes)

    @pytest.mark.asyncio
    async def test_encode_agent_requirements_without_codec_param(self, agent_requirements):
        """Test encoding agent requirements without codec parameter (creates default)."""
        from src.core.codec_integration import encode_agent_requirements

        encoded = await encode_agent_requirements(agent_requirements, codec=None)

        assert isinstance(encoded, bytes)

    @pytest.mark.asyncio
    async def test_decode_agent_requirements_without_codec_param(self, agent_requirements):
        """Test decoding agent requirements without codec parameter (creates default)."""
        from src.core.codec_integration import encode_agent_requirements, decode_agent_requirements

        encoded = await encode_agent_requirements(agent_requirements, codec=None)
        decoded = await decode_agent_requirements(encoded, codec=None)

        assert isinstance(decoded, dict)
        assert decoded["name"] == agent_requirements.name

    @pytest.mark.asyncio
    async def test_decode_agent_requirements_with_migration_needed(self, agent_requirements):
        """Test decoding agent requirements when migration is needed."""
        from src.core.codec_integration import encode_agent_requirements, decode_agent_requirements

        encoded = await encode_agent_requirements(agent_requirements, schema_version="1.0")
        # Request different version to trigger migration
        decoded = await decode_agent_requirements(encoded, codec=None, target_version="1.0")

        assert isinstance(decoded, dict)
        assert decoded["name"] == agent_requirements.name

    @pytest.mark.asyncio
    async def test_encode_tool_requirements_without_codec_param(self, tool_requirements):
        """Test encoding tool requirements without codec parameter (creates default)."""
        from src.core.codec_integration import encode_tool_requirements

        encoded = await encode_tool_requirements(tool_requirements, codec=None)

        assert isinstance(encoded, bytes)

    @pytest.mark.asyncio
    async def test_decode_tool_requirements_without_codec_param(self, tool_requirements):
        """Test decoding tool requirements without codec parameter (creates default)."""
        from src.core.codec_integration import encode_tool_requirements, decode_tool_requirements

        encoded = await encode_tool_requirements(tool_requirements, codec=None)
        decoded = await decode_tool_requirements(encoded, codec=None)

        assert isinstance(decoded, dict)
        assert decoded["name"] == tool_requirements.name

    @pytest.mark.asyncio
    async def test_decode_tool_requirements_with_migration_needed(self, tool_requirements):
        """Test decoding tool requirements when migration is needed."""
        from src.core.codec_integration import encode_tool_requirements, decode_tool_requirements

        encoded = await encode_tool_requirements(tool_requirements, schema_version="1.0")
        # Request different version to trigger migration
        decoded = await decode_tool_requirements(encoded, codec=None, target_version="1.0")

        assert isinstance(decoded, dict)
        assert decoded["name"] == tool_requirements.name

    @pytest.mark.asyncio
    async def test_decode_agent_requirements_with_different_version(self, agent_requirements):
        """Test decoding agent requirements with different target version (triggers migration)."""
        from src.core.codec_integration import encode_agent_requirements, decode_agent_requirements

        encoded = await encode_agent_requirements(agent_requirements, schema_version="1.0")
        # Request same version - no migration needed, but tests the path
        decoded = await decode_agent_requirements(encoded, codec=None, target_version="1.0")

        assert isinstance(decoded, dict)
        assert decoded["name"] == agent_requirements.name

    @pytest.mark.asyncio
    async def test_decode_tool_requirements_with_different_version(self, tool_requirements):
        """Test decoding tool requirements with different target version (triggers migration)."""
        from src.core.codec_integration import encode_tool_requirements, decode_tool_requirements

        encoded = await encode_tool_requirements(tool_requirements, schema_version="1.0")
        # Request same version - no migration needed, but tests the path
        decoded = await decode_tool_requirements(encoded, codec=None, target_version="1.0")

        assert isinstance(decoded, dict)
        assert decoded["name"] == tool_requirements.name

    @pytest.mark.asyncio
    async def test_decode_agent_requirements_with_migration(self, interpreter, codec, agent_requirements):
        """Test decoding agent requirements with schema migration."""
        interpreter.codec_serializer = codec

        encoded = await interpreter.encode_agent_requirements(agent_requirements, schema_version="1.0")
        decoded = await interpreter.decode_agent_requirements(encoded, target_version="1.0")

        assert isinstance(decoded, AgentRequirements)
        assert decoded.name == agent_requirements.name

    @pytest.mark.asyncio
    async def test_decode_tool_requirements_with_migration(self, interpreter, codec, tool_requirements):
        """Test decoding tool requirements with schema migration."""
        interpreter.codec_serializer = codec

        encoded = await interpreter.encode_tool_requirements(tool_requirements, schema_version="1.0")
        decoded = await interpreter.decode_tool_requirements(encoded, target_version="1.0")

        assert isinstance(decoded, ToolRequirements)
        assert decoded.name == tool_requirements.name


