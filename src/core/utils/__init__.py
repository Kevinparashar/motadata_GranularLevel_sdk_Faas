"""
Shared Utilities

Common utilities used across SDK components.
"""

from .error_handler import (
    ErrorHandler,
    create_error_with_suggestion
)
from .type_helpers import (
    GatewayProtocol,
    AgentProtocol,
    ToolProtocol,
    CacheProtocol,
    ConfigDict,
    MetadataDict,
    ParametersDict,
    ResultDict,
    ensure_type,
    optional_type
)
from .config_builders import (
    AgentConfigBuilder,
    ToolConfigBuilder,
    GatewayConfigBuilder,
    create_agent_config,
    create_tool_config,
    create_gateway_config
)
from .config_validator import (
    ConfigurationError,
    ConfigValidator,
    ConfigHelper
)
from .config_discovery import (
    get_agent_config_options,
    get_gateway_config_options,
    get_rag_config_options,
    print_config_options,
    discover_config
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
