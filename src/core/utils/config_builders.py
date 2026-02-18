"""
Configuration Builders

Provides builder pattern for complex configurations to improve developer experience.
"""


from typing import Any, Dict, List, Optional

from ..utils.type_helpers import ConfigDict, MetadataDict


class AgentConfigBuilder:
    """Builder for agent configuration."""

    def __init__(self) -> None:
        """
        Initialize AgentConfigBuilder.
        """
        self._config: ConfigDict = {}
        self._capabilities: List[str] = []
        self._tools: List[str] = []
        self._metadata: MetadataDict = {}

    def with_name(self, name: str) -> "AgentConfigBuilder":
        """
        Set agent name.
        
        Args:
            name (str): Value to set for name.
        
        Returns:
            'AgentConfigBuilder': Builder instance (returned for call chaining).
        """
        self._config["name"] = name
        return self

    def with_description(self, description: str) -> "AgentConfigBuilder":
        """
        Set agent description.
        
        Args:
            description (str): Value to set for description.
        
        Returns:
            'AgentConfigBuilder': Builder instance (returned for call chaining).
        """
        self._config["description"] = description
        return self

    def with_system_prompt(self, system_prompt: str) -> "AgentConfigBuilder":
        """
        Set system prompt.
        
        Args:
            system_prompt (str): Value to set for system prompt.
        
        Returns:
            'AgentConfigBuilder': Builder instance (returned for call chaining).
        """
        self._config["system_prompt"] = system_prompt
        return self

    def with_capability(self, capability: str) -> "AgentConfigBuilder":
        """
        Add a capability.
        
        Args:
            capability (str): Value to set for capability.
        
        Returns:
            'AgentConfigBuilder': Builder instance (returned for call chaining).
        """
        self._capabilities.append(capability)
        return self

    def with_capabilities(self, capabilities: List[str]) -> "AgentConfigBuilder":
        """
        Add multiple capabilities.
        
        Args:
            capabilities (List[str]): Value to set for capabilities.
        
        Returns:
            'AgentConfigBuilder': Builder instance (returned for call chaining).
        """
        self._capabilities.extend(capabilities)
        return self

    def with_tool(self, tool_id: str) -> "AgentConfigBuilder":
        """
        Add a tool.
        
        Args:
            tool_id (str): Value to set for tool.
        
        Returns:
            'AgentConfigBuilder': Builder instance (returned for call chaining).
        """
        self._tools.append(tool_id)
        return self

    def with_tools(self, tool_ids: List[str]) -> "AgentConfigBuilder":
        """
        Add multiple tools.
        
        Args:
            tool_ids (List[str]): Value to set for tools.
        
        Returns:
            'AgentConfigBuilder': Builder instance (returned for call chaining).
        """
        self._tools.extend(tool_ids)
        return self

    def with_memory(
        self, memory_type: str = "episodic", max_size: int = 1000
    ) -> "AgentConfigBuilder":
        """
        Configure memory.
        
        Args:
            memory_type (str): Value to set for memory.
            max_size (int): Value to set for memory.
        
        Returns:
            'AgentConfigBuilder': Builder instance (returned for call chaining).
        """
        self._config["memory_config"] = {"memory_type": memory_type, "max_size": max_size}
        return self

    def with_metadata(self, key: str, value: Any) -> "AgentConfigBuilder":
        """
        Add metadata.
        
        Args:
            key (str): Value to set for metadata.
            value (Any): Value to set for metadata.
        
        Returns:
            'AgentConfigBuilder': Builder instance (returned for call chaining).
        """
        self._metadata[key] = value
        return self

    def with_metadata_dict(self, metadata: MetadataDict) -> "AgentConfigBuilder":
        """
        Add metadata dictionary.
        
        Args:
            metadata (MetadataDict): Value to set for metadata dict.
        
        Returns:
            'AgentConfigBuilder': Builder instance (returned for call chaining).
        """
        self._metadata.update(metadata)
        return self

    def build(self) -> ConfigDict:
        """
        Build the configuration dictionary.
        
        Returns:
            ConfigDict: Result of the operation.
        """
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
        """
        Initialize ToolConfigBuilder.
        """
        self._config: ConfigDict = {}
        self._parameters: List[Dict[str, Any]] = []
        self._metadata: MetadataDict = {}
        self._tags: List[str] = []

    def with_name(self, name: str) -> "ToolConfigBuilder":
        """
        Set tool name.
        
        Args:
            name (str): Value to set for name.
        
        Returns:
            'ToolConfigBuilder': Builder instance (returned for call chaining).
        """
        self._config["name"] = name
        return self

    def with_description(self, description: str) -> "ToolConfigBuilder":
        """
        Set tool description.
        
        Args:
            description (str): Value to set for description.
        
        Returns:
            'ToolConfigBuilder': Builder instance (returned for call chaining).
        """
        self._config["description"] = description
        return self

    def with_tool_type(self, tool_type: str) -> "ToolConfigBuilder":
        """
        Set tool type.
        
        Args:
            tool_type (str): Value to set for tool type.
        
        Returns:
            'ToolConfigBuilder': Builder instance (returned for call chaining).
        """
        self._config["tool_type"] = tool_type
        return self

    def with_parameter(
        self,
        name: str,
        param_type: str,
        description: str,
        required: bool = True,
        default: Optional[Any] = None,
    ) -> "ToolConfigBuilder":
        """
        Add a parameter.
        
        Args:
            name (str): Value to set for parameter.
            param_type (str): Value to set for parameter.
            description (str): Value to set for parameter.
            required (bool): Value to set for parameter.
            default (Optional[Any]): Value to set for parameter.
        
        Returns:
            'ToolConfigBuilder': Builder instance (returned for call chaining).
        """
        param = {"name": name, "type": param_type, "description": description, "required": required}
        if default is not None:
            param["default"] = default
        self._parameters.append(param)
        return self

    def with_tag(self, tag: str) -> "ToolConfigBuilder":
        """
        Add a tag.
        
        Args:
            tag (str): Value to set for tag.
        
        Returns:
            'ToolConfigBuilder': Builder instance (returned for call chaining).
        """
        self._tags.append(tag)
        return self

    def with_tags(self, tags: List[str]) -> "ToolConfigBuilder":
        """
        Add multiple tags.
        
        Args:
            tags (List[str]): Value to set for tags.
        
        Returns:
            'ToolConfigBuilder': Builder instance (returned for call chaining).
        """
        self._tags.extend(tags)
        return self

    def with_metadata(self, key: str, value: Any) -> "ToolConfigBuilder":
        """
        Add metadata.
        
        Args:
            key (str): Value to set for metadata.
            value (Any): Value to set for metadata.
        
        Returns:
            'ToolConfigBuilder': Builder instance (returned for call chaining).
        """
        self._metadata[key] = value
        return self

    def build(self) -> ConfigDict:
        """
        Build the configuration dictionary.
        
        Returns:
            ConfigDict: Result of the operation.
        """
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
        """
        Initialize GatewayConfigBuilder.
        """
        self._config: ConfigDict = {}

    def with_provider(self, provider: str) -> "GatewayConfigBuilder":
        """
        Set LLM provider.
        
        Args:
            provider (str): Value to set for provider.
        
        Returns:
            'GatewayConfigBuilder': Builder instance (returned for call chaining).
        """
        self._config["provider"] = provider
        return self

    def with_api_key(self, api_key: str) -> "GatewayConfigBuilder":
        """
        Set API key.
        
        Args:
            api_key (str): Value to set for api key.
        
        Returns:
            'GatewayConfigBuilder': Builder instance (returned for call chaining).
        """
        self._config["api_key"] = api_key
        return self

    def with_default_model(self, model: str) -> "GatewayConfigBuilder":
        """
        Set default model.
        
        Args:
            model (str): Value to set for default model.
        
        Returns:
            'GatewayConfigBuilder': Builder instance (returned for call chaining).
        """
        self._config["default_model"] = model
        return self

    def with_rate_limit(self, requests_per_minute: int) -> "GatewayConfigBuilder":
        """
        Set rate limit.
        
        Args:
            requests_per_minute (int): Value to set for rate limit.
        
        Returns:
            'GatewayConfigBuilder': Builder instance (returned for call chaining).
        """
        self._config["rate_limit"] = {"requests_per_minute": requests_per_minute}
        return self

    def with_cache(self, enabled: bool = True, ttl: int = 3600) -> "GatewayConfigBuilder":
        """
        Configure caching.
        
        Args:
            enabled (bool): Value to set for cache.
            ttl (int): Value to set for cache.
        
        Returns:
            'GatewayConfigBuilder': Builder instance (returned for call chaining).
        """
        self._config["cache"] = {"enabled": enabled, "ttl": ttl}
        return self

    def build(self) -> ConfigDict:
        """
        Build the configuration dictionary.
        
        Returns:
            ConfigDict: Result of the operation.
        """
        return self._config.copy()


def create_agent_config() -> AgentConfigBuilder:
    """
    Create a new agent configuration builder.
    
    Returns:
        AgentConfigBuilder: Result of the operation.
    """
    return AgentConfigBuilder()


def create_tool_config() -> ToolConfigBuilder:
    """
    Create a new tool configuration builder.
    
    Returns:
        ToolConfigBuilder: Result of the operation.
    """
    return ToolConfigBuilder()


def create_gateway_config() -> GatewayConfigBuilder:
    """
    Create a new gateway configuration builder.
    
    Returns:
        GatewayConfigBuilder: Result of the operation.
    """
    return GatewayConfigBuilder()
