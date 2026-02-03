"""
Shared Utilities

Common utilities used across SDK components.
"""


from .config_builders import (
    AgentConfigBuilder,
    GatewayConfigBuilder,
    ToolConfigBuilder,
    create_agent_config,
    create_gateway_config,
    create_tool_config,
)
from .config_discovery import (
    discover_config,
    get_agent_config_options,
    get_gateway_config_options,
    get_rag_config_options,
    print_config_options,
)
from .config_validator import ConfigHelper, ConfigurationError, ConfigValidator
from .error_handler import ErrorHandler, create_error_with_suggestion
from .type_helpers import (
    AgentProtocol,
    CacheProtocol,
    ConfigDict,
    GatewayProtocol,
    MetadataDict,
    ParametersDict,
    ResultDict,
    ToolProtocol,
    ensure_type,
    optional_type,
)

__all__ = [
    # Error handling
    "ErrorHandler",
    "create_error_with_suggestion",
    # Type helpers
    "GatewayProtocol",
    "AgentProtocol",
    "ToolProtocol",
    "CacheProtocol",
    "ConfigDict",
    "MetadataDict",
    "ParametersDict",
    "ResultDict",
    "ensure_type",
    "optional_type",
    # Configuration builders
    "AgentConfigBuilder",
    "ToolConfigBuilder",
    "GatewayConfigBuilder",
    "create_agent_config",
    "create_tool_config",
    "create_gateway_config",
    # Configuration validation
    "ConfigurationError",
    "ConfigValidator",
    "ConfigHelper",
    # Configuration discovery
    "get_agent_config_options",
    "get_gateway_config_options",
    "get_rag_config_options",
    "print_config_options",
    "discover_config",
]
