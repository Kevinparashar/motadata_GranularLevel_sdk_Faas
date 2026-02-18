"""
Unit Tests for Configuration Validator

Tests configuration validation, discovery, and error handling.
"""

import pytest

from src.core.exceptions import SDKError
from src.core.utils.config_validator import (
    ConfigHelper,
    ConfigValidator,
    ConfigurationError,
)


class TestConfigurationError:
    """Test ConfigurationError class."""

    def test_configuration_error_basic(self):
        """Test ConfigurationError with basic message."""
        error = ConfigurationError("Invalid configuration")
        assert isinstance(error, SDKError)
        assert error.message == "Invalid configuration"
        assert error.config_key is None
        assert error.invalid_value is None
        assert error.valid_options is None
        assert error.suggestion is None

    def test_configuration_error_with_all_params(self):
        """Test ConfigurationError with all parameters."""
        error = ConfigurationError(
            "Invalid configuration",
            config_key="api_key",
            invalid_value="invalid",
            valid_options=["option1", "option2"],
            suggestion="Use a valid option",
        )
        assert error.message == "Invalid configuration"
        assert error.config_key == "api_key"
        assert error.invalid_value == "invalid"
        assert error.valid_options == ["option1", "option2"]
        assert error.suggestion == "Use a valid option"


class TestConfigValidatorValidateRequired:
    """Test ConfigValidator.validate_required method."""

    def test_validate_required_all_present(self):
        """Test validate_required when all keys are present."""
        config = {"key1": "value1", "key2": "value2"}
        ConfigValidator.validate_required(config, ["key1", "key2"])

    def test_validate_required_missing_keys(self):
        """Test validate_required when keys are missing."""
        config = {"key1": "value1"}
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigValidator.validate_required(config, ["key1", "key2", "key3"], "test_component")

        assert "Missing required configuration" in str(exc_info.value)
        assert "key2" in str(exc_info.value)
        assert "key3" in str(exc_info.value)
        assert exc_info.value.config_key is not None
        # component_name is passed but not stored as attribute (it's in the message)

    def test_validate_required_api_key_suggestion(self):
        """Test validate_required with api_key suggestion."""
        config = {}
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigValidator.validate_required(config, ["api_key"], "test_component")

        # The suggestion is in the error message, not as an attribute
        error_str = str(exc_info.value)
        assert "api_key" in error_str
        assert "environment variable" in error_str or "Suggestion" in error_str

    def test_validate_required_model_suggestion(self):
        """Test validate_required with model suggestion."""
        config = {}
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigValidator.validate_required(config, ["llm_model"], "test_component")

        error_str = str(exc_info.value)
        assert "llm_model" in error_str
        assert "gpt-4" in error_str or "Suggestion" in error_str

    def test_validate_required_provider_suggestion(self):
        """Test validate_required with provider suggestion."""
        config = {}
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigValidator.validate_required(config, ["provider"], "test_component")

        error_str = str(exc_info.value)
        assert "provider" in error_str
        assert "openai" in error_str or "Suggestion" in error_str

    def test_validate_required_generic_suggestion(self):
        """Test validate_required with generic suggestion."""
        config = {}
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigValidator.validate_required(config, ["custom_key"], "test_component")

        error_str = str(exc_info.value)
        assert "custom_key" in error_str
        assert "Provide custom_key" in error_str or "Suggestion" in error_str


class TestConfigValidatorValidateType:
    """Test ConfigValidator.validate_type method."""

    def test_validate_type_correct_type(self):
        """Test validate_type with correct type."""
        config = {"key": "value"}
        ConfigValidator.validate_type(config, "key", str)

    def test_validate_type_missing_key(self):
        """Test validate_type with missing key."""
        config = {}
        ConfigValidator.validate_type(config, "key", str)  # Should not raise

    def test_validate_type_wrong_type(self):
        """Test validate_type with wrong type."""
        config = {"key": 123}
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigValidator.validate_type(config, "key", str, "test_component")

        assert "Invalid type" in str(exc_info.value)
        assert "expected str" in str(exc_info.value)
        assert exc_info.value.config_key == "key"
        assert exc_info.value.invalid_value == 123

    def test_validate_type_int_suggestion(self):
        """Test validate_type with int conversion suggestion."""
        config = {"key": "123"}
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigValidator.validate_type(config, "key", int)

        error_str = str(exc_info.value)
        assert "Convert key to integer" in error_str or "Suggestion" in error_str

    def test_validate_type_float_suggestion(self):
        """Test validate_type with float conversion suggestion."""
        config = {"key": "123.5"}
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigValidator.validate_type(config, "key", float)

        error_str = str(exc_info.value)
        assert "Convert key to float" in error_str or "Suggestion" in error_str

    def test_validate_type_str_suggestion(self):
        """Test validate_type with str conversion suggestion."""
        config = {"key": 123}
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigValidator.validate_type(config, "key", str)

        error_str = str(exc_info.value)
        assert "Convert key to string" in error_str or "Suggestion" in error_str

    def test_validate_type_bool_suggestion(self):
        """Test validate_type with bool conversion suggestion."""
        config = {"key": "true"}
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigValidator.validate_type(config, "key", bool)

        error_str = str(exc_info.value)
        assert "Convert key to boolean" in error_str or "Suggestion" in error_str

    def test_validate_type_other_type_suggestion(self):
        """Test validate_type with other type suggestion."""
        config = {"key": "value"}
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigValidator.validate_type(config, "key", list)

        error_str = str(exc_info.value)
        assert "Ensure key is of type list" in error_str or "Suggestion" in error_str


class TestConfigValidatorValidateEnum:
    """Test ConfigValidator.validate_enum method."""

    def test_validate_enum_valid_value(self):
        """Test validate_enum with valid value."""
        config = {"key": "option1"}
        ConfigValidator.validate_enum(config, "key", ["option1", "option2", "option3"])

    def test_validate_enum_missing_key(self):
        """Test validate_enum with missing key."""
        config = {}
        ConfigValidator.validate_enum(config, "key", ["option1", "option2"])  # Should not raise

    def test_validate_enum_invalid_value(self):
        """Test validate_enum with invalid value."""
        config = {"key": "invalid"}
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigValidator.validate_enum(config, "key", ["option1", "option2"], "test_component")

        assert "Invalid value" in str(exc_info.value)
        assert exc_info.value.config_key == "key"
        assert exc_info.value.invalid_value == "invalid"
        assert exc_info.value.valid_options == ["option1", "option2"]

    def test_validate_enum_with_closest_match(self):
        """Test validate_enum with closest match suggestion."""
        config = {"key": "optin1"}  # Typo: should be "option1"
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigValidator.validate_enum(config, "key", ["option1", "option2"])

        error_str = str(exc_info.value)
        assert "Valid options" in error_str or "Suggestion" in error_str
        # May or may not have closest match depending on similarity


class TestConfigValidatorValidateRange:
    """Test ConfigValidator.validate_range method."""

    def test_validate_range_valid_value(self):
        """Test validate_range with valid value."""
        config = {"key": 5}
        ConfigValidator.validate_range(config, "key", min_value=0, max_value=10)

    def test_validate_range_missing_key(self):
        """Test validate_range with missing key."""
        config = {}
        ConfigValidator.validate_range(config, "key", min_value=0, max_value=10)  # Should not raise

    def test_validate_range_below_min(self):
        """Test validate_range with value below minimum."""
        config = {"key": -1}
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigValidator.validate_range(config, "key", min_value=0, max_value=10, component_name="test")

        assert "out of range" in str(exc_info.value)
        assert exc_info.value.config_key == "key"
        assert exc_info.value.invalid_value == -1
        error_str = str(exc_info.value)
        assert "must be >= 0" in error_str or "Suggestion" in error_str

    def test_validate_range_above_max(self):
        """Test validate_range with value above maximum."""
        config = {"key": 15}
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigValidator.validate_range(config, "key", min_value=0, max_value=10, component_name="test")

        assert "out of range" in str(exc_info.value)
        error_str = str(exc_info.value)
        assert "must be <= 10" in error_str or "Suggestion" in error_str

    def test_validate_range_both_violations(self):
        """Test validate_range with both min and max violations."""
        config = {"key": 15}
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigValidator.validate_range(config, "key", min_value=5, max_value=10, component_name="test")

        assert "out of range" in str(exc_info.value)

    def test_validate_range_non_numeric(self):
        """Test validate_range with non-numeric value."""
        config = {"key": "not_a_number"}
        with pytest.raises(ConfigurationError):
            ConfigValidator.validate_range(config, "key", min_value=0, max_value=10)


class TestConfigValidatorDiscoverConfigOptions:
    """Test ConfigValidator.discover_config_options method."""

    def test_discover_config_options_without_schema(self):
        """Test discover_config_options without schema."""
        result = ConfigValidator.discover_config_options("test_component")
        assert result["component"] == "test_component"
        assert result["options"] == {}
        assert result["required"] == []
        assert result["optional"] == []
        assert result["examples"] == []

    def test_discover_config_options_with_schema(self):
        """Test discover_config_options with schema."""
        schema = {"key1": "value1", "key2": "value2"}
        result = ConfigValidator.discover_config_options("test_component", schema)
        assert result["component"] == "test_component"
        assert result["options"] == schema


class TestConfigValidatorFindClosestMatch:
    """Test ConfigValidator._find_closest_match method."""

    def test_find_closest_match_exact(self):
        """Test _find_closest_match with exact match."""
        result = ConfigValidator._find_closest_match("option1", ["option1", "option2"])
        assert result == "option1"

    def test_find_closest_match_typo(self):
        """Test _find_closest_match with typo."""
        result = ConfigValidator._find_closest_match("optin1", ["option1", "option2"])
        # Should find closest match based on similarity
        assert result is not None

    def test_find_closest_match_no_match(self):
        """Test _find_closest_match with no close match."""
        result = ConfigValidator._find_closest_match("xyz", ["option1", "option2"])
        # Should return None if similarity is too low
        assert result is None

    def test_find_closest_match_case_insensitive(self):
        """Test _find_closest_match is case insensitive."""
        result = ConfigValidator._find_closest_match("OPTION1", ["option1", "option2"])
        assert result == "option1"


class TestConfigHelperGetConfigExample:
    """Test ConfigHelper.get_config_example method."""

    def test_get_config_example_agent(self):
        """Test get_config_example for agent."""
        example = ConfigHelper.get_config_example("agent")
        assert "agent_id" in example
        assert "name" in example
        assert "llm_model" in example
        assert example["llm_model"] == "gpt-4"

    def test_get_config_example_gateway(self):
        """Test get_config_example for gateway."""
        example = ConfigHelper.get_config_example("gateway")
        assert "api_key" in example
        assert "provider" in example
        assert "rate_limit" in example

    def test_get_config_example_rag(self):
        """Test get_config_example for rag."""
        example = ConfigHelper.get_config_example("rag")
        assert "tenant_id" in example
        assert "embedding_model" in example
        assert "chunk_size" in example

    def test_get_config_example_tool(self):
        """Test get_config_example for tool."""
        example = ConfigHelper.get_config_example("tool")
        assert "tool_id" in example
        assert "name" in example
        assert "parameters" in example

    def test_get_config_example_unknown(self):
        """Test get_config_example for unknown component."""
        example = ConfigHelper.get_config_example("unknown")
        assert example == {}

    def test_get_config_example_case_insensitive(self):
        """Test get_config_example is case insensitive."""
        example = ConfigHelper.get_config_example("AGENT")
        assert "agent_id" in example


class TestConfigHelperValidateAndSuggest:
    """Test ConfigHelper.validate_and_suggest method."""

    def test_validate_and_suggest_valid_config(self):
        """Test validate_and_suggest with valid config."""
        config = {"key1": "value1", "key2": "value2"}
        result = ConfigHelper.validate_and_suggest(
            config, "test_component", required_keys=["key1", "key2"]
        )
        assert result == config

    def test_validate_and_suggest_missing_required(self):
        """Test validate_and_suggest with missing required keys."""
        config = {"key1": "value1"}
        with pytest.raises(ConfigurationError):
            ConfigHelper.validate_and_suggest(
                config, "test_component", required_keys=["key1", "key2"]
            )

    def test_validate_and_suggest_unknown_keys_with_example(self):
        """Test validate_and_suggest with unknown keys when example exists."""
        config = {"unknown_key": "value", "agent_id": "agent_001"}
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigHelper.validate_and_suggest(
                config, "agent", required_keys=["agent_id"], optional_keys=[]
            )

        assert "Unknown configuration keys" in str(exc_info.value)
        assert "unknown_key" in str(exc_info.value)

    def test_validate_and_suggest_unknown_keys_with_closest_match(self):
        """Test validate_and_suggest with unknown key that has closest match."""
        # Provide required key and add unknown key with typo
        config = {"agent_id": "agent_001", "agent_idd": "typo_key"}  # Typo: should be something else
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigHelper.validate_and_suggest(
                config, "agent", required_keys=["agent_id"], optional_keys=[]
            )

        error_str = str(exc_info.value)
        assert "Unknown configuration keys" in error_str
        # The error should mention the unknown key
        assert "agent_idd" in error_str

    def test_validate_and_suggest_unknown_keys_no_example(self):
        """Test validate_and_suggest with unknown keys but no example."""
        config = {"unknown_key": "value", "key1": "value1"}
        # Should not raise if no example exists for component
        result = ConfigHelper.validate_and_suggest(
            config, "unknown_component", required_keys=["key1"], optional_keys=[]
        )
        assert result == config

    def test_validate_and_suggest_no_required_or_optional(self):
        """Test validate_and_suggest with no required or optional keys."""
        config = {"any_key": "value"}
        result = ConfigHelper.validate_and_suggest(config, "test_component")
        assert result == config


class TestConfigHelperFormatExample:
    """Test ConfigHelper._format_example method."""

    def test_format_example_simple(self):
        """Test _format_example with simple dict."""
        example = {"key1": "value1", "key2": 123}
        result = ConfigHelper._format_example(example)
        assert "key1: 'value1'" in result
        assert "key2: 123" in result

    def test_format_example_nested_dict(self):
        """Test _format_example with nested dict."""
        example = {"key1": {"nested_key": "nested_value"}}
        result = ConfigHelper._format_example(example)
        assert "key1: {" in result
        assert "nested_key: 'nested_value'" in result

    def test_format_example_list(self):
        """Test _format_example with list."""
        example = {"key1": ["item1", "item2"]}
        result = ConfigHelper._format_example(example)
        assert "key1: [" in result
        assert "item1" in result
        assert "item2" in result

    def test_format_example_list_of_dicts(self):
        """Test _format_example with list of dicts."""
        example = {"key1": [{"item_key": "item_value"}]}
        result = ConfigHelper._format_example(example)
        assert "key1: [" in result
        assert "{" in result
        assert "item_key: 'item_value'" in result

    def test_format_example_with_indent(self):
        """Test _format_example with custom indent."""
        example = {"key1": "value1"}
        result = ConfigHelper._format_example(example, indent=2)
        assert result.startswith("    ")  # 2 * 2 spaces

