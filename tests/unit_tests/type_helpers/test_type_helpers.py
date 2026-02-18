"""
Unit Tests for Type Helper Utilities

Tests type aliases, protocols, and type helper functions.
"""

import asyncio

import pytest

from src.core.utils.type_helpers import (
    ConfigDict,
    MetadataDict,
    ParametersDict,
    ResultDict,
    ensure_type,
    optional_type,
)


class TestTypeAliases:
    """Test type aliases."""

    def test_config_dict_type_alias(self):
        """Test ConfigDict type alias."""
        config: ConfigDict = {"key": "value"}
        assert isinstance(config, dict)
        assert config["key"] == "value"

    def test_metadata_dict_type_alias(self):
        """Test MetadataDict type alias."""
        metadata: MetadataDict = {"meta_key": "meta_value"}
        assert isinstance(metadata, dict)
        assert metadata["meta_key"] == "meta_value"

    def test_parameters_dict_type_alias(self):
        """Test ParametersDict type alias."""
        params: ParametersDict = {"param1": "value1"}
        assert isinstance(params, dict)
        assert params["param1"] == "value1"

    def test_result_dict_type_alias(self):
        """Test ResultDict type alias."""
        result: ResultDict = {"result_key": "result_value"}
        assert isinstance(result, dict)
        assert result["result_key"] == "result_value"


class TestGatewayProtocol:
    """Test GatewayProtocol protocol."""

    def test_gateway_protocol_implementation(self):
        """Test GatewayProtocol can be implemented."""
        class MockGateway:
            async def generate_async(self, prompt: str, **kwargs):
                await asyncio.sleep(0)
                return f"Response to: {prompt}"

            def generate(self, prompt: str, **kwargs):
                return f"Response to: {prompt}"

        gateway = MockGateway()
        # Type check: should satisfy GatewayProtocol
        assert hasattr(gateway, "generate_async")
        assert hasattr(gateway, "generate")


class TestAgentProtocol:
    """Test AgentProtocol protocol."""

    def test_agent_protocol_implementation(self):
        """Test AgentProtocol can be implemented."""
        class MockAgent:
            agent_id: str = "agent_001"
            tenant_id: str | None = "tenant_123"
            name: str = "Test Agent"
            description: str = "Test description"

        agent = MockAgent()
        # Type check: should satisfy AgentProtocol
        assert hasattr(agent, "agent_id")
        assert hasattr(agent, "tenant_id")
        assert hasattr(agent, "name")
        assert hasattr(agent, "description")
        # Verify values
        assert agent.agent_id == "agent_001"
        assert agent.name == "Test Agent"


class TestToolProtocol:
    """Test ToolProtocol protocol."""

    def test_tool_protocol_implementation(self):
        """Test ToolProtocol can be implemented."""
        class MockTool:
            tool_id: str = "tool_001"
            name: str = "Test Tool"
            description: str = "Test description"

            async def execute(self, **kwargs):
                await asyncio.sleep(0)
                return "executed"

        tool = MockTool()
        # Type check: should satisfy ToolProtocol
        assert hasattr(tool, "tool_id")
        assert hasattr(tool, "name")
        assert hasattr(tool, "description")
        assert hasattr(tool, "execute")


class TestCacheProtocol:
    """Test CacheProtocol protocol."""

    def test_cache_protocol_implementation(self):
        """Test CacheProtocol can be implemented."""
        class MockCache:
            async def get(self, key: str, tenant_id: str | None = None):
                await asyncio.sleep(0)
                return None

            async def set(self, key: str, value, tenant_id: str | None = None, ttl: int | None = None):
                await asyncio.sleep(0)
                # Mock implementation - no-op

            async def delete(self, key: str, tenant_id: str | None = None):
                await asyncio.sleep(0)
                # Mock implementation - no-op

            async def invalidate_pattern(self, pattern: str, tenant_id: str | None = None):
                await asyncio.sleep(0)
                # Mock implementation - no-op

        cache = MockCache()
        # Type check: should satisfy CacheProtocol
        assert hasattr(cache, "get")
        assert hasattr(cache, "set")
        assert hasattr(cache, "delete")
        assert hasattr(cache, "invalidate_pattern")


class TestEnsureType:
    """Test ensure_type function."""

    def test_ensure_type_correct_type(self):
        """Test ensure_type with correct type."""
        value = "test_string"
        result = ensure_type(value, str)
        assert result == "test_string"
        assert isinstance(result, str)

    def test_ensure_type_int(self):
        """Test ensure_type with int."""
        value = 123
        result = ensure_type(value, int)
        assert result == 123
        assert isinstance(result, int)

    def test_ensure_type_list(self):
        """Test ensure_type with list."""
        value = [1, 2, 3]
        result = ensure_type(value, list)
        assert result == [1, 2, 3]
        assert isinstance(result, list)

    def test_ensure_type_dict(self):
        """Test ensure_type with dict."""
        value = {"key": "value"}
        result = ensure_type(value, dict)
        assert result == {"key": "value"}
        assert isinstance(result, dict)

    def test_ensure_type_wrong_type(self):
        """Test ensure_type with wrong type raises TypeError."""
        value = "not_an_int"
        with pytest.raises(TypeError) as exc_info:
            ensure_type(value, int)

        assert "Type mismatch" in str(exc_info.value)
        assert "expected int" in str(exc_info.value)
        assert "got str" in str(exc_info.value)

    def test_ensure_type_custom_error_message(self):
        """Test ensure_type with custom error message."""
        value = "not_an_int"
        with pytest.raises(TypeError) as exc_info:
            ensure_type(value, int, error_message="Custom error")

        assert "Custom error" in str(exc_info.value)
        assert "expected int" in str(exc_info.value)


class TestOptionalType:
    """Test optional_type function."""

    def test_optional_type_none(self):
        """Test optional_type with None returns default."""
        result = optional_type(None, str, "default_value")
        assert result == "default_value"

    def test_optional_type_correct_type(self):
        """Test optional_type with correct type returns value."""
        result = optional_type("actual_value", str, "default_value")
        assert result == "actual_value"

    def test_optional_type_wrong_type(self):
        """Test optional_type with wrong type returns default."""
        result = optional_type(123, str, "default_value")
        assert result == "default_value"

    def test_optional_type_int(self):
        """Test optional_type with int."""
        result = optional_type(42, int, 0)
        assert result == 42

    def test_optional_type_int_none(self):
        """Test optional_type with None and int default."""
        result = optional_type(None, int, 0)
        assert result == 0

    def test_optional_type_int_wrong_type(self):
        """Test optional_type with wrong type and int default."""
        result = optional_type("not_an_int", int, 0)
        assert result == 0

    def test_optional_type_list(self):
        """Test optional_type with list."""
        result = optional_type([1, 2, 3], list, [])
        assert result == [1, 2, 3]

    def test_optional_type_list_none(self):
        """Test optional_type with None and list default."""
        result = optional_type(None, list, [])
        assert result == []

    def test_optional_type_list_wrong_type(self):
        """Test optional_type with wrong type and list default."""
        result = optional_type("not_a_list", list, [])
        assert result == []

