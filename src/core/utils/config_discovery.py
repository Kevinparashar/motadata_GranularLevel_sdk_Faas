"""
Configuration Discovery Utilities

Helps users discover available configuration options for SDK components.
"""


from typing import Any, Dict, Optional

from .config_validator import ConfigHelper


def get_agent_config_options() -> Dict[str, Any]:
    """
    Get all available configuration options for agent creation.

    Returns:
        Dictionary with configuration options, descriptions, and examples
    """
    return {
        "required": {
            "agent_id": {
                "type": "str",
                "description": "Unique identifier for the agent",
                "example": "agent_001",
            },
            "name": {
                "type": "str",
                "description": "Human-readable name for the agent",
                "example": "Customer Support Agent",
            },
            "gateway": {
                "type": "LiteLLMGateway",
                "description": "LiteLLM Gateway instance for LLM operations",
                "example": "gateway = create_gateway(...)",
            },
        },
        "optional": {
            "tenant_id": {
                "type": "str",
                "description": "Tenant ID for multi-tenant isolation",
                "example": "tenant_123",
                "default": None,
            },
            "description": {
                "type": "str",
                "description": "Detailed description of agent capabilities",
                "example": "Handles customer support tickets",
                "default": "",
            },
            "llm_model": {
                "type": "str",
                "description": "LLM model to use (e.g., 'gpt-4', 'claude-3-opus')",
                "example": "gpt-4",
                "default": None,
            },
            "llm_provider": {
                "type": "str",
                "description": "LLM provider (e.g., 'openai', 'anthropic')",
                "example": "openai",
                "default": None,
            },
            "system_prompt": {
                "type": "str",
                "description": "System prompt defining agent behavior",
                "example": "You are a helpful customer support agent",
                "default": None,
            },
            "enable_tool_calling": {
                "type": "bool",
                "description": "Enable tool calling capabilities",
                "example": True,
                "default": True,
            },
            "max_tool_iterations": {
                "type": "int",
                "description": "Maximum tool calling iterations",
                "example": 10,
                "default": 10,
                "range": [1, 50],
            },
            "memory_config": {
                "type": "dict",
                "description": "Memory configuration",
                "example": {
                    "persistence_path": "/tmp/memory.json",
                    "max_short_term": 50,
                    "max_long_term": 1000,
                },
                "default": None,
            },
        },
        "example": ConfigHelper.get_config_example("agent"),
    }


def get_gateway_config_options() -> Dict[str, Any]:
    """
    Get all available configuration options for gateway creation.

    Returns:
        Dictionary with configuration options, descriptions, and examples
    """
    return {
        "required": {
            "api_keys": {
                "type": "dict",
                "description": "Dictionary mapping provider names to API keys",
                "example": {"openai": "sk-..."},
            }
        },
        "optional": {
            "providers": {
                "type": "list[str]",
                "description": "List of provider names to enable",
                "example": ["openai", "anthropic"],
                "default": None,
            },
            "default_model": {
                "type": "str",
                "description": "Default model to use",
                "example": "gpt-4",
                "default": "gpt-4",
                "valid_options": [
                    "gpt-4",
                    "gpt-3.5-turbo",
                    "claude-3-opus",
                    "claude-3-sonnet",
                    "gemini-pro",
                ],
            },
            "timeout": {
                "type": "float",
                "description": "Request timeout in seconds",
                "example": 60.0,
                "default": 60.0,
                "range": [1.0, 300.0],
            },
            "max_retries": {
                "type": "int",
                "description": "Maximum number of retries",
                "example": 3,
                "default": 3,
                "range": [0, 10],
            },
            "retry_delay": {
                "type": "float",
                "description": "Delay between retries in seconds",
                "example": 1.0,
                "default": 1.0,
                "range": [0.1, 60.0],
            },
            "fallbacks": {
                "type": "list[str]",
                "description": "Fallback models to try if primary fails",
                "example": ["gpt-3.5-turbo", "claude-3-haiku"],
                "default": None,
            },
        },
        "example": ConfigHelper.get_config_example("gateway"),
    }


def get_rag_config_options() -> Dict[str, Any]:
    """
    Get all available configuration options for RAG system.

    Returns:
        Dictionary with configuration options, descriptions, and examples
    """
    return {
        "required": {
            "db": {
                "type": "PostgreSQLDatabase",
                "description": "PostgreSQL database instance with pgvector",
                "example": "db = create_database(...)",
            },
            "gateway": {
                "type": "LiteLLMGateway",
                "description": "LiteLLM Gateway instance",
                "example": "gateway = create_gateway(...)",
            },
        },
        "optional": {
            "tenant_id": {
                "type": "str",
                "description": "Tenant ID for multi-tenant isolation",
                "example": "tenant_123",
                "default": None,
            },
            "embedding_model": {
                "type": "str",
                "description": "Embedding model name",
                "example": "text-embedding-3-small",
                "default": "text-embedding-3-small",
            },
            "chunk_size": {
                "type": "int",
                "description": "Document chunk size in characters",
                "example": 1000,
                "default": 1000,
                "range": [100, 10000],
            },
            "chunk_overlap": {
                "type": "int",
                "description": "Overlap between chunks",
                "example": 200,
                "default": 200,
                "range": [0, 1000],
            },
            "top_k": {
                "type": "int",
                "description": "Number of documents to retrieve",
                "example": 5,
                "default": 5,
                "range": [1, 50],
            },
        },
        "example": ConfigHelper.get_config_example("rag"),
    }


def _print_required_options(options: Dict[str, Any]) -> None:
    """
    Print required configuration options.
    
    Args:
        options (Dict[str, Any]): Input parameter for this operation.
    
    Returns:
        None: Result of the operation.
    """
    if "required" not in options:
        return
    
    print("REQUIRED OPTIONS:")
    print("-" * 60)
    for key, info in options["required"].items():
        print(f"  {key}:")
        print(f"    Type: {info['type']}")
        print(f"    Description: {info['description']}")
        print(f"    Example: {info['example']}")
        print()


def _print_optional_options(options: Dict[str, Any]) -> None:
    """
    Print optional configuration options.
    
    Args:
        options (Dict[str, Any]): Input parameter for this operation.
    
    Returns:
        None: Result of the operation.
    """
    if "optional" not in options:
        return
    
    print("OPTIONAL OPTIONS:")
    print("-" * 60)
    for key, info in options["optional"].items():
        print(f"  {key}:")
        print(f"    Type: {info['type']}")
        print(f"    Description: {info['description']}")
        if "default" in info:
            print(f"    Default: {info['default']}")
        if "range" in info:
            print(f"    Range: {info['range'][0]} - {info['range'][1]}")
        if "valid_options" in info:
            print(f"    Valid options: {', '.join(info['valid_options'])}")
        print(f"    Example: {info['example']}")
        print()


def _print_example_config(options: Dict[str, Any]) -> None:
    """
    Print example configuration.
    
    Args:
        options (Dict[str, Any]): Input parameter for this operation.
    
    Returns:
        None: Result of the operation.
    """
    if "example" not in options or not options["example"]:
        return
    
    print("EXAMPLE CONFIGURATION:")
    print("-" * 60)
    import json
    print(json.dumps(options["example"], indent=2))
    print()


def print_config_options(component_name: str) -> None:
    """
    Print available configuration options for a component.
    
    Args:
        component_name (str): Input parameter for this operation.
    
    Returns:
        None: Result of the operation.
    """
    options_map = {
        "agent": get_agent_config_options,
        "gateway": get_gateway_config_options,
        "rag": get_rag_config_options,
        "tool": lambda: {"example": ConfigHelper.get_config_example("tool")},
    }

    get_options = options_map.get(component_name.lower())
    if not get_options:
        print(f"Unknown component: {component_name}")
        print(f"Available components: {', '.join(options_map.keys())}")
        return

    options = get_options()

    print(f"\n{'='*60}")
    print(f"Configuration Options for: {component_name.upper()}")
    print(f"{'='*60}\n")

    _print_required_options(options)
    _print_optional_options(options)
    _print_example_config(options)


def discover_config(
    component_name: str, partial_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Discover configuration options and validate partial configuration.

    Args:
        component_name: Name of the component
        partial_config: Optional partial configuration to validate

    Returns:
        Dictionary with available options and validation results
    """
    from .config_validator import ConfigHelper

    options_map = {
        "agent": get_agent_config_options,
        "gateway": get_gateway_config_options,
        "rag": get_rag_config_options,
    }

    get_options = options_map.get(component_name.lower())
    if not get_options:
        return {
            "error": f"Unknown component: {component_name}",
            "available_components": list(options_map.keys()),
        }

    options = get_options()
    result = {"component": component_name, "options": options, "validation": None}

    if partial_config:
        required_keys = list(options.get("required", {}).keys())
        optional_keys = list(options.get("optional", {}).keys())

        try:
            validated = ConfigHelper.validate_and_suggest(
                partial_config, component_name, required_keys, optional_keys
            )
            result["validation"] = {"valid": True, "config": validated}
        except Exception as e:
            result["validation"] = {
                "valid": False,
                "error": str(e),
                "suggestions": getattr(e, "suggestion", None),
            }

    return result
