"""
Unit Tests for Configuration Builders

Tests builder pattern for complex configurations.
"""

import pytest

from src.core.utils.config_builders import (
    AgentConfigBuilder,
    GatewayConfigBuilder,
    ToolConfigBuilder,
    create_agent_config,
    create_gateway_config,
    create_tool_config,
)


class TestAgentConfigBuilder:
    """Test AgentConfigBuilder class."""

    def test_init(self):
        """Test AgentConfigBuilder initialization."""
        builder = AgentConfigBuilder()
        assert builder._config == {}
        assert builder._capabilities == []
        assert builder._tools == []
        assert builder._metadata == {}

    def test_with_name(self):
        """Test with_name method."""
        builder = AgentConfigBuilder()
        result = builder.with_name("Test Agent")
        assert result is builder  # Method chaining
        assert builder._config["name"] == "Test Agent"

    def test_with_description(self):
        """Test with_description method."""
        builder = AgentConfigBuilder()
        result = builder.with_description("Test description")
        assert result is builder
        assert builder._config["description"] == "Test description"

    def test_with_system_prompt(self):
        """Test with_system_prompt method."""
        builder = AgentConfigBuilder()
        result = builder.with_system_prompt("You are a helpful assistant")
        assert result is builder
        assert builder._config["system_prompt"] == "You are a helpful assistant"

    def test_with_capability(self):
        """Test with_capability method."""
        builder = AgentConfigBuilder()
        result = builder.with_capability("capability1")
        assert result is builder
        assert builder._capabilities == ["capability1"]

    def test_with_capability_multiple(self):
        """Test with_capability method with multiple calls."""
        builder = AgentConfigBuilder()
        builder.with_capability("cap1").with_capability("cap2")
        assert builder._capabilities == ["cap1", "cap2"]

    def test_with_capabilities(self):
        """Test with_capabilities method."""
        builder = AgentConfigBuilder()
        result = builder.with_capabilities(["cap1", "cap2", "cap3"])
        assert result is builder
        assert builder._capabilities == ["cap1", "cap2", "cap3"]

    def test_with_capabilities_extends(self):
        """Test with_capabilities extends existing capabilities."""
        builder = AgentConfigBuilder()
        builder.with_capability("cap1").with_capabilities(["cap2", "cap3"])
        assert builder._capabilities == ["cap1", "cap2", "cap3"]

    def test_with_tool(self):
        """Test with_tool method."""
        builder = AgentConfigBuilder()
        result = builder.with_tool("tool1")
        assert result is builder
        assert builder._tools == ["tool1"]

    def test_with_tool_multiple(self):
        """Test with_tool method with multiple calls."""
        builder = AgentConfigBuilder()
        builder.with_tool("tool1").with_tool("tool2")
        assert builder._tools == ["tool1", "tool2"]

    def test_with_tools(self):
        """Test with_tools method."""
        builder = AgentConfigBuilder()
        result = builder.with_tools(["tool1", "tool2", "tool3"])
        assert result is builder
        assert builder._tools == ["tool1", "tool2", "tool3"]

    def test_with_tools_extends(self):
        """Test with_tools extends existing tools."""
        builder = AgentConfigBuilder()
        builder.with_tool("tool1").with_tools(["tool2", "tool3"])
        assert builder._tools == ["tool1", "tool2", "tool3"]

    def test_with_memory_default(self):
        """Test with_memory method with defaults."""
        builder = AgentConfigBuilder()
        result = builder.with_memory()
        assert result is builder
        assert builder._config["memory_config"] == {"memory_type": "episodic", "max_size": 1000}

    def test_with_memory_custom(self):
        """Test with_memory method with custom values."""
        builder = AgentConfigBuilder()
        result = builder.with_memory(memory_type="semantic", max_size=2000)
        assert result is builder
        assert builder._config["memory_config"] == {"memory_type": "semantic", "max_size": 2000}

    def test_with_metadata(self):
        """Test with_metadata method."""
        builder = AgentConfigBuilder()
        result = builder.with_metadata("key1", "value1")
        assert result is builder
        assert builder._metadata == {"key1": "value1"}

    def test_with_metadata_multiple(self):
        """Test with_metadata method with multiple calls."""
        builder = AgentConfigBuilder()
        builder.with_metadata("key1", "value1").with_metadata("key2", "value2")
        assert builder._metadata == {"key1": "value1", "key2": "value2"}

    def test_with_metadata_dict(self):
        """Test with_metadata_dict method."""
        builder = AgentConfigBuilder()
        metadata = {"key1": "value1", "key2": "value2"}
        result = builder.with_metadata_dict(metadata)
        assert result is builder
        assert builder._metadata == metadata

    def test_with_metadata_dict_extends(self):
        """Test with_metadata_dict extends existing metadata."""
        builder = AgentConfigBuilder()
        builder.with_metadata("key1", "value1").with_metadata_dict({"key2": "value2"})
        assert builder._metadata == {"key1": "value1", "key2": "value2"}

    def test_build_empty(self):
        """Test build method with empty configuration."""
        builder = AgentConfigBuilder()
        config = builder.build()
        assert config == {}

    def test_build_with_all_fields(self):
        """Test build method with all fields."""
        builder = (
            AgentConfigBuilder()
            .with_name("Test Agent")
            .with_description("Test description")
            .with_system_prompt("You are helpful")
            .with_capability("cap1")
            .with_tool("tool1")
            .with_memory(memory_type="episodic", max_size=1000)
            .with_metadata("key1", "value1")
        )
        config = builder.build()
        assert config["name"] == "Test Agent"
        assert config["description"] == "Test description"
        assert config["system_prompt"] == "You are helpful"
        assert config["capabilities"] == ["cap1"]
        assert config["tools"] == ["tool1"]
        assert config["memory_config"] == {"memory_type": "episodic", "max_size": 1000}
        assert config["metadata"] == {"key1": "value1"}

    def test_build_without_capabilities(self):
        """Test build method without capabilities."""
        builder = AgentConfigBuilder().with_name("Test Agent")
        config = builder.build()
        assert "capabilities" not in config

    def test_build_without_tools(self):
        """Test build method without tools."""
        builder = AgentConfigBuilder().with_name("Test Agent")
        config = builder.build()
        assert "tools" not in config

    def test_build_without_metadata(self):
        """Test build method without metadata."""
        builder = AgentConfigBuilder().with_name("Test Agent")
        config = builder.build()
        assert "metadata" not in config


class TestToolConfigBuilder:
    """Test ToolConfigBuilder class."""

    def test_init(self):
        """Test ToolConfigBuilder initialization."""
        builder = ToolConfigBuilder()
        assert builder._config == {}
        assert builder._parameters == []
        assert builder._metadata == {}
        assert builder._tags == []

    def test_with_name(self):
        """Test with_name method."""
        builder = ToolConfigBuilder()
        result = builder.with_name("Test Tool")
        assert result is builder
        assert builder._config["name"] == "Test Tool"

    def test_with_description(self):
        """Test with_description method."""
        builder = ToolConfigBuilder()
        result = builder.with_description("Test description")
        assert result is builder
        assert builder._config["description"] == "Test description"

    def test_with_tool_type(self):
        """Test with_tool_type method."""
        builder = ToolConfigBuilder()
        result = builder.with_tool_type("function")
        assert result is builder
        assert builder._config["tool_type"] == "function"

    def test_with_parameter_required(self):
        """Test with_parameter method with required parameter."""
        builder = ToolConfigBuilder()
        result = builder.with_parameter("param1", "string", "Parameter description", required=True)
        assert result is builder
        assert len(builder._parameters) == 1
        param = builder._parameters[0]
        assert param["name"] == "param1"
        assert param["type"] == "string"
        assert param["description"] == "Parameter description"
        assert param["required"] is True
        assert "default" not in param

    def test_with_parameter_optional(self):
        """Test with_parameter method with optional parameter."""
        builder = ToolConfigBuilder()
        result = builder.with_parameter("param1", "string", "Description", required=False, default="default_value")
        assert result is builder
        param = builder._parameters[0]
        assert param["required"] is False
        assert param["default"] == "default_value"

    def test_with_parameter_multiple(self):
        """Test with_parameter method with multiple parameters."""
        builder = ToolConfigBuilder()
        builder.with_parameter("param1", "string", "Desc1").with_parameter("param2", "int", "Desc2")
        assert len(builder._parameters) == 2
        assert builder._parameters[0]["name"] == "param1"
        assert builder._parameters[1]["name"] == "param2"

    def test_with_tag(self):
        """Test with_tag method."""
        builder = ToolConfigBuilder()
        result = builder.with_tag("tag1")
        assert result is builder
        assert builder._tags == ["tag1"]

    def test_with_tag_multiple(self):
        """Test with_tag method with multiple calls."""
        builder = ToolConfigBuilder()
        builder.with_tag("tag1").with_tag("tag2")
        assert builder._tags == ["tag1", "tag2"]

    def test_with_tags(self):
        """Test with_tags method."""
        builder = ToolConfigBuilder()
        result = builder.with_tags(["tag1", "tag2", "tag3"])
        assert result is builder
        assert builder._tags == ["tag1", "tag2", "tag3"]

    def test_with_tags_extends(self):
        """Test with_tags extends existing tags."""
        builder = ToolConfigBuilder()
        builder.with_tag("tag1").with_tags(["tag2", "tag3"])
        assert builder._tags == ["tag1", "tag2", "tag3"]

    def test_with_metadata(self):
        """Test with_metadata method."""
        builder = ToolConfigBuilder()
        result = builder.with_metadata("key1", "value1")
        assert result is builder
        assert builder._metadata == {"key1": "value1"}

    def test_build_empty(self):
        """Test build method with empty configuration."""
        builder = ToolConfigBuilder()
        config = builder.build()
        assert config == {}

    def test_build_with_all_fields(self):
        """Test build method with all fields."""
        builder = (
            ToolConfigBuilder()
            .with_name("Test Tool")
            .with_description("Test description")
            .with_tool_type("function")
            .with_parameter("param1", "string", "Description", required=True)
            .with_tag("tag1")
            .with_metadata("key1", "value1")
        )
        config = builder.build()
        assert config["name"] == "Test Tool"
        assert config["description"] == "Test description"
        assert config["tool_type"] == "function"
        assert len(config["parameters"]) == 1
        assert config["tags"] == ["tag1"]
        assert config["metadata"] == {"key1": "value1"}

    def test_build_without_parameters(self):
        """Test build method without parameters."""
        builder = ToolConfigBuilder().with_name("Test Tool")
        config = builder.build()
        assert "parameters" not in config

    def test_build_without_tags(self):
        """Test build method without tags."""
        builder = ToolConfigBuilder().with_name("Test Tool")
        config = builder.build()
        assert "tags" not in config

    def test_build_without_metadata(self):
        """Test build method without metadata."""
        builder = ToolConfigBuilder().with_name("Test Tool")
        config = builder.build()
        assert "metadata" not in config


class TestGatewayConfigBuilder:
    """Test GatewayConfigBuilder class."""

    def test_init(self):
        """Test GatewayConfigBuilder initialization."""
        builder = GatewayConfigBuilder()
        assert builder._config == {}

    def test_with_provider(self):
        """Test with_provider method."""
        builder = GatewayConfigBuilder()
        result = builder.with_provider("openai")
        assert result is builder
        assert builder._config["provider"] == "openai"

    def test_with_api_key(self):
        """Test with_api_key method."""
        builder = GatewayConfigBuilder()
        result = builder.with_api_key("test-api-key")
        assert result is builder
        assert builder._config["api_key"] == "test-api-key"

    def test_with_default_model(self):
        """Test with_default_model method."""
        builder = GatewayConfigBuilder()
        result = builder.with_default_model("gpt-4")
        assert result is builder
        assert builder._config["default_model"] == "gpt-4"

    def test_with_rate_limit(self):
        """Test with_rate_limit method."""
        builder = GatewayConfigBuilder()
        result = builder.with_rate_limit(60)
        assert result is builder
        assert builder._config["rate_limit"] == {"requests_per_minute": 60}

    def test_with_cache_default(self):
        """Test with_cache method with defaults."""
        builder = GatewayConfigBuilder()
        result = builder.with_cache()
        assert result is builder
        assert builder._config["cache"] == {"enabled": True, "ttl": 3600}

    def test_with_cache_custom(self):
        """Test with_cache method with custom values."""
        builder = GatewayConfigBuilder()
        result = builder.with_cache(enabled=False, ttl=7200)
        assert result is builder
        assert builder._config["cache"] == {"enabled": False, "ttl": 7200}

    def test_build_empty(self):
        """Test build method with empty configuration."""
        builder = GatewayConfigBuilder()
        config = builder.build()
        assert config == {}

    def test_build_with_all_fields(self):
        """Test build method with all fields."""
        builder = (
            GatewayConfigBuilder()
            .with_provider("openai")
            .with_api_key("test-key")
            .with_default_model("gpt-4")
            .with_rate_limit(60)
            .with_cache(enabled=True, ttl=3600)
        )
        config = builder.build()
        assert config["provider"] == "openai"
        assert config["api_key"] == "test-key"
        assert config["default_model"] == "gpt-4"
        assert config["rate_limit"] == {"requests_per_minute": 60}
        assert config["cache"] == {"enabled": True, "ttl": 3600}

    def test_build_returns_copy(self):
        """Test build method returns a copy of config."""
        builder = GatewayConfigBuilder().with_provider("openai")
        config1 = builder.build()
        config2 = builder.build()
        assert config1 == config2
        assert config1 is not config2  # Different objects
        config1["new_key"] = "new_value"
        assert "new_key" not in config2


class TestFactoryFunctions:
    """Test factory functions."""

    def test_create_agent_config(self):
        """Test create_agent_config function."""
        builder = create_agent_config()
        assert isinstance(builder, AgentConfigBuilder)

    def test_create_tool_config(self):
        """Test create_tool_config function."""
        builder = create_tool_config()
        assert isinstance(builder, ToolConfigBuilder)

    def test_create_gateway_config(self):
        """Test create_gateway_config function."""
        builder = create_gateway_config()
        assert isinstance(builder, GatewayConfigBuilder)

