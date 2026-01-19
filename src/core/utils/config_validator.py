"""
Configuration Validator and Discovery Utilities

Provides configuration validation, discovery, and helpful error messages.
"""

from typing import Dict, List, Optional, Any, Set, Type
from pydantic import BaseModel, ValidationError, Field
from ..exceptions import SDKError
from .error_handler import create_error_with_suggestion


class ConfigurationError(SDKError):
    """Raised when configuration is invalid."""
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        invalid_value: Optional[Any] = None,
        valid_options: Optional[List[str]] = None,
        suggestion: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, **kwargs)
        self.config_key = config_key
        self.invalid_value = invalid_value
        self.valid_options = valid_options
        self.suggestion = suggestion


class ConfigValidator:
    """
    Validates configuration and provides helpful error messages.
    """
    
    @staticmethod
    def validate_required(
        config: Dict[str, Any],
        required_keys: List[str],
        component_name: str = "component"
    ) -> None:
        """
        Validate that required configuration keys are present.
        
        Args:
            config: Configuration dictionary
            required_keys: List of required keys
            component_name: Name of component for error messages
            
        Raises:
            ConfigurationError: If required keys are missing
        """
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            suggestions = []
            for key in missing_keys:
                # Provide suggestions based on common patterns
                if "api_key" in key.lower():
                    suggestions.append(f"Set {key} using environment variable or config file")
                elif "model" in key.lower():
                    suggestions.append(f"Set {key} to a valid model name (e.g., 'gpt-4', 'claude-3-opus')")
                elif "provider" in key.lower():
                    suggestions.append(f"Set {key} to a valid provider (e.g., 'openai', 'anthropic', 'google')")
                else:
                    suggestions.append(f"Provide {key} in configuration")
            
            suggestion_text = "\n".join(f"  - {s}" for s in suggestions)
            raise create_error_with_suggestion(
                ConfigurationError,
                message=f"Missing required configuration for {component_name}: {', '.join(missing_keys)}",
                suggestion=f"Required configuration keys:\n{suggestion_text}",
                config_key=",".join(missing_keys),
                component_name=component_name
            )
    
    @staticmethod
    def validate_type(
        config: Dict[str, Any],
        key: str,
        expected_type: Type[Any],
        component_name: str = "component"
    ) -> None:
        """
        Validate that a configuration value has the correct type.
        
        Args:
            config: Configuration dictionary
            key: Configuration key to validate
            expected_type: Expected type
            component_name: Name of component for error messages
            
        Raises:
            ConfigurationError: If type is incorrect
        """
        if key not in config:
            return  # Skip if key is missing (use validate_required for that)
        
        value = config[key]
        if not isinstance(value, expected_type):
            type_name = expected_type.__name__
            actual_type = type(value).__name__
            
            # Provide type conversion suggestions
            suggestions = []
            if expected_type == int and isinstance(value, (str, float)):
                suggestions.append(f"Convert {key} to integer: {key} = int({key})")
            elif expected_type == float and isinstance(value, (str, int)):
                suggestions.append(f"Convert {key} to float: {key} = float({key})")
            elif expected_type == str and value is not None:
                suggestions.append(f"Convert {key} to string: {key} = str({key})")
            elif expected_type == bool and isinstance(value, (str, int)):
                suggestions.append(f"Convert {key} to boolean: {key} = bool({key})")
            else:
                suggestions.append(f"Ensure {key} is of type {type_name}, got {actual_type}")
            
            suggestion_text = "\n".join(f"  - {s}" for s in suggestions)
            raise create_error_with_suggestion(
                ConfigurationError,
                message=f"Invalid type for {key} in {component_name}: expected {type_name}, got {actual_type}",
                suggestion=f"Type conversion:\n{suggestion_text}",
                config_key=key,
                invalid_value=value,
                component_name=component_name
            )
    
    @staticmethod
    def validate_enum(
        config: Dict[str, Any],
        key: str,
        valid_values: List[str],
        component_name: str = "component"
    ) -> None:
        """
        Validate that a configuration value is one of the valid options.
        
        Args:
            config: Configuration dictionary
            key: Configuration key to validate
            valid_values: List of valid values
            component_name: Name of component for error messages
            
        Raises:
            ConfigurationError: If value is not in valid options
        """
        if key not in config:
            return
        
        value = config[key]
        if value not in valid_values:
            # Find closest match
            closest = ConfigValidator._find_closest_match(str(value), valid_values)
            
            suggestions = [f"Valid options for {key}: {', '.join(valid_values)}"]
            if closest:
                suggestions.append(f"Did you mean '{closest}'?")
            
            suggestion_text = "\n".join(f"  - {s}" for s in suggestions)
            raise create_error_with_suggestion(
                ConfigurationError,
                message=f"Invalid value for {key} in {component_name}: '{value}' is not valid",
                suggestion=suggestion_text,
                config_key=key,
                invalid_value=value,
                valid_options=valid_values,
                component_name=component_name
            )
    
    @staticmethod
    def validate_range(
        config: Dict[str, Any],
        key: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        component_name: str = "component"
    ) -> None:
        """
        Validate that a numeric configuration value is within range.
        
        Args:
            config: Configuration dictionary
            key: Configuration key to validate
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            component_name: Name of component for error messages
            
        Raises:
            ConfigurationError: If value is out of range
        """
        if key not in config:
            return
        
        value = config[key]
        if not isinstance(value, (int, float)):
            ConfigValidator.validate_type(config, key, (int, float), component_name)
            return
        
        suggestions = []
        if min_value is not None and value < min_value:
            suggestions.append(f"{key} must be >= {min_value}, got {value}")
            suggestions.append(f"Set {key} to at least {min_value}")
        if max_value is not None and value > max_value:
            suggestions.append(f"{key} must be <= {max_value}, got {value}")
            suggestions.append(f"Set {key} to at most {max_value}")
        
        if suggestions:
            suggestion_text = "\n".join(f"  - {s}" for s in suggestions)
            raise create_error_with_suggestion(
                ConfigurationError,
                message=f"Value for {key} in {component_name} is out of range",
                suggestion=suggestion_text,
                config_key=key,
                invalid_value=value,
                component_name=component_name
            )
    
    @staticmethod
    def discover_config_options(
        component_name: str,
        config_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Discover available configuration options for a component.
        
        Args:
            component_name: Name of the component
            config_schema: Optional schema definition
            
        Returns:
            Dictionary of available configuration options with descriptions
        """
        # This would be populated from component schemas
        # For now, return a structure that can be extended
        return {
            "component": component_name,
            "options": config_schema or {},
            "required": [],
            "optional": [],
            "examples": []
        }
    
    @staticmethod
    def _find_closest_match(value: str, options: List[str]) -> Optional[str]:
        """Find closest match using simple string similarity."""
        value_lower = value.lower()
        best_match = None
        best_score = 0
        
        for option in options:
            option_lower = option.lower()
            # Simple similarity: count common characters
            score = sum(1 for c in value_lower if c in option_lower)
            if score > best_score and score > len(value) * 0.5:
                best_score = score
                best_match = option
        
        return best_match


class ConfigHelper:
    """
    Helper class for configuration discovery and validation.
    """
    
    @staticmethod
    def get_config_example(component_name: str) -> Dict[str, Any]:
        """
        Get example configuration for a component.
        
        Args:
            component_name: Name of the component
            
        Returns:
            Example configuration dictionary
        """
        examples = {
            "agent": {
                "agent_id": "agent_001",
                "name": "My Agent",
                "description": "Agent description",
                "tenant_id": "tenant_123",
                "llm_model": "gpt-4",
                "llm_provider": "openai",
                "system_prompt": "You are a helpful assistant",
                "enable_tool_calling": True,
                "max_tool_iterations": 10
            },
            "gateway": {
                "api_key": "your-api-key",
                "provider": "openai",
                "default_model": "gpt-4",
                "rate_limit": {
                    "requests_per_minute": 60
                },
                "cache": {
                    "enabled": True,
                    "ttl": 3600
                }
            },
            "rag": {
                "tenant_id": "tenant_123",
                "embedding_model": "text-embedding-3-small",
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "top_k": 5
            },
            "tool": {
                "tool_id": "tool_001",
                "name": "My Tool",
                "description": "Tool description",
                "tool_type": "function",
                "parameters": [
                    {
                        "name": "param1",
                        "type": "string",
                        "description": "Parameter description",
                        "required": True
                    }
                ]
            }
        }
        
        return examples.get(component_name.lower(), {})
    
    @staticmethod
    def validate_and_suggest(
        config: Dict[str, Any],
        component_name: str,
        required_keys: Optional[List[str]] = None,
        optional_keys: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate configuration and provide suggestions for missing/invalid keys.
        
        Args:
            config: Configuration dictionary to validate
            component_name: Name of the component
            required_keys: List of required keys
            optional_keys: List of optional keys
            
        Returns:
            Validated and normalized configuration
            
        Raises:
            ConfigurationError: If validation fails
        """
        validator = ConfigValidator()
        
        # Validate required keys
        if required_keys:
            validator.validate_required(config, required_keys, component_name)
        
        # Get example for reference
        example = ConfigHelper.get_config_example(component_name)
        
        # Check for unknown keys
        all_valid_keys = set((required_keys or []) + (optional_keys or []))
        unknown_keys = set(config.keys()) - all_valid_keys
        
        if unknown_keys and example:
            # Suggest similar keys from example
            suggestions = []
            for unknown_key in unknown_keys:
                closest = ConfigValidator._find_closest_match(unknown_key, list(example.keys()))
                if closest:
                    suggestions.append(f"  - '{unknown_key}' is not recognized. Did you mean '{closest}'?")
                else:
                    suggestions.append(f"  - '{unknown_key}' is not a valid configuration key")
            
            if suggestions:
                suggestion_text = "\n".join(suggestions)
                suggestion_text += f"\n\nValid configuration keys: {', '.join(sorted(all_valid_keys))}"
                suggestion_text += f"\n\nExample configuration:\n{ConfigHelper._format_example(example)}"
                
                raise create_error_with_suggestion(
                    ConfigurationError,
                    message=f"Unknown configuration keys for {component_name}: {', '.join(unknown_keys)}",
                    suggestion=suggestion_text,
                    component_name=component_name
                )
        
        return config
    
    @staticmethod
    def _format_example(example: Dict[str, Any], indent: int = 0) -> str:
        """Format example configuration as readable string."""
        lines = []
        indent_str = "  " * indent
        
        for key, value in example.items():
            if isinstance(value, dict):
                lines.append(f"{indent_str}{key}: {{")
                lines.append(ConfigHelper._format_example(value, indent + 1))
                lines.append(f"{indent_str}}}")
            elif isinstance(value, list):
                lines.append(f"{indent_str}{key}: [")
                for item in value:
                    if isinstance(item, dict):
                        lines.append(f"{indent_str}  {{")
                        lines.append(ConfigHelper._format_example(item, indent + 2))
                        lines.append(f"{indent_str}  }}")
                    else:
                        lines.append(f"{indent_str}  {item}")
                lines.append(f"{indent_str}]")
            else:
                lines.append(f"{indent_str}{key}: {value!r}")
        
        return "\n".join(lines)

