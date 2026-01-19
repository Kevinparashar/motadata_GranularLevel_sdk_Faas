"""
Configuration Builders

Provides builder pattern for complex configurations to improve developer experience.
"""

from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field
from ..utils.type_helpers import ConfigDict, MetadataDict


class AgentConfigBuilder:
    """Builder for agent configuration."""
    
    def __init__(self) -> None:
        self._config: ConfigDict = {}
        self._capabilities: List[str] = []
        self._tools: List[str] = []
        self._metadata: MetadataDict = {}
    
    def with_name(self, name: str) -> "AgentConfigBuilder":
        """Set agent name."""
        self._config["name"] = name
        return self
    
    def with_description(self, description: str) -> "AgentConfigBuilder":
        """Set agent description."""
        self._config["description"] = description
        return self
    
    def with_system_prompt(self, system_prompt: str) -> "AgentConfigBuilder":
        """Set system prompt."""
        self._config["system_prompt"] = system_prompt
        return self
    
    def with_capability(self, capability: str) -> "AgentConfigBuilder":
        """Add a capability."""
        self._capabilities.append(capability)
        return self
    
    def with_capabilities(self, capabilities: List[str]) -> "AgentConfigBuilder":
        """Add multiple capabilities."""
        self._capabilities.extend(capabilities)
        return self
    
    def with_tool(self, tool_id: str) -> "AgentConfigBuilder":
        """Add a tool."""
        self._tools.append(tool_id)
        return self
    
    def with_tools(self, tool_ids: List[str]) -> "AgentConfigBuilder":
        """Add multiple tools."""
        self._tools.extend(tool_ids)
        return self
    
    def with_memory(self, memory_type: str = "episodic", max_size: int = 1000) -> "AgentConfigBuilder":
        """Configure memory."""
        self._config["memory_config"] = {
            "memory_type": memory_type,
            "max_size": max_size
        }
        return self
    
    def with_metadata(self, key: str, value: Any) -> "AgentConfigBuilder":
        """Add metadata."""
        self._metadata[key] = value
        return self
    
    def with_metadata_dict(self, metadata: MetadataDict) -> "AgentConfigBuilder":
        """Add metadata dictionary."""
        self._metadata.update(metadata)
        return self
    
    def build(self) -> ConfigDict:
        """Build the configuration dictionary."""
        config = self._config.copy()
        if self._capabilities:
            config["capabilities"] = self._capabilities
        if self._tools:
            config["tools"] = self._tools
        if self._metadata:
            config["metadata"] = self._metadata
        return config


class ToolConfigBuilder:
    """Builder for tool configuration."""
    
    def __init__(self) -> None:
        self._config: ConfigDict = {}
        self._parameters: List[Dict[str, Any]] = []
        self._metadata: MetadataDict = {}
        self._tags: List[str] = []
    
    def with_name(self, name: str) -> "ToolConfigBuilder":
        """Set tool name."""
        self._config["name"] = name
        return self
    
    def with_description(self, description: str) -> "ToolConfigBuilder":
        """Set tool description."""
        self._config["description"] = description
        return self
    
    def with_tool_type(self, tool_type: str) -> "ToolConfigBuilder":
        """Set tool type."""
        self._config["tool_type"] = tool_type
        return self
    
    def with_parameter(
        self,
        name: str,
        param_type: str,
        description: str,
        required: bool = True,
        default: Optional[Any] = None
    ) -> "ToolConfigBuilder":
        """Add a parameter."""
        param = {
            "name": name,
            "type": param_type,
            "description": description,
            "required": required
        }
        if default is not None:
            param["default"] = default
        self._parameters.append(param)
        return self
    
    def with_tag(self, tag: str) -> "ToolConfigBuilder":
        """Add a tag."""
        self._tags.append(tag)
        return self
    
    def with_tags(self, tags: List[str]) -> "ToolConfigBuilder":
        """Add multiple tags."""
        self._tags.extend(tags)
        return self
    
    def with_metadata(self, key: str, value: Any) -> "ToolConfigBuilder":
        """Add metadata."""
        self._metadata[key] = value
        return self
    
    def build(self) -> ConfigDict:
        """Build the configuration dictionary."""
        config = self._config.copy()
        if self._parameters:
            config["parameters"] = self._parameters
        if self._tags:
            config["tags"] = self._tags
        if self._metadata:
            config["metadata"] = self._metadata
        return config


class GatewayConfigBuilder:
    """Builder for gateway configuration."""
    
    def __init__(self) -> None:
        self._config: ConfigDict = {}
    
    def with_provider(self, provider: str) -> "GatewayConfigBuilder":
        """Set LLM provider."""
        self._config["provider"] = provider
        return self
    
    def with_api_key(self, api_key: str) -> "GatewayConfigBuilder":
        """Set API key."""
        self._config["api_key"] = api_key
        return self
    
    def with_default_model(self, model: str) -> "GatewayConfigBuilder":
        """Set default model."""
        self._config["default_model"] = model
        return self
    
    def with_rate_limit(self, requests_per_minute: int) -> "GatewayConfigBuilder":
        """Set rate limit."""
        self._config["rate_limit"] = {"requests_per_minute": requests_per_minute}
        return self
    
    def with_cache(self, enabled: bool = True, ttl: int = 3600) -> "GatewayConfigBuilder":
        """Configure caching."""
        self._config["cache"] = {"enabled": enabled, "ttl": ttl}
        return self
    
    def build(self) -> ConfigDict:
        """Build the configuration dictionary."""
        return self._config.copy()


def create_agent_config() -> AgentConfigBuilder:
    """Create a new agent configuration builder."""
    return AgentConfigBuilder()


def create_tool_config() -> ToolConfigBuilder:
    """Create a new tool configuration builder."""
    return ToolConfigBuilder()


def create_gateway_config() -> GatewayConfigBuilder:
    """Create a new gateway configuration builder."""
    return GatewayConfigBuilder()

