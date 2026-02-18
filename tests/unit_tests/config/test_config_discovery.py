"""
Unit Tests for Configuration Discovery Utilities

Tests configuration discovery functions for SDK components.
"""

from io import StringIO
from typing import Optional
from unittest.mock import patch

from src.core.utils.config_discovery import (
    discover_config,
    get_agent_config_options,
    get_gateway_config_options,
    get_rag_config_options,
    print_config_options,
)


class TestGetConfigOptions:
    """Test functions that get configuration options."""

    def test_get_agent_config_options(self):
        """Test get_agent_config_options function."""
        options = get_agent_config_options()

        assert "required" in options
        assert "optional" in options
        assert "example" in options

        # Check required fields
        assert "agent_id" in options["required"]
        assert "name" in options["required"]
        assert "gateway" in options["required"]

        # Check optional fields
        assert "tenant_id" in options["optional"]
        assert "description" in options["optional"]
        assert "llm_model" in options["optional"]
        assert "llm_provider" in options["optional"]
        assert "system_prompt" in options["optional"]
        assert "enable_tool_calling" in options["optional"]
        assert "max_tool_iterations" in options["optional"]
        assert "memory_config" in options["optional"]

        # Check structure of a required field
        agent_id_info = options["required"]["agent_id"]
        assert agent_id_info["type"] == "str"
        assert "description" in agent_id_info
        assert "example" in agent_id_info

        # Check structure of an optional field
        tenant_id_info = options["optional"]["tenant_id"]
        assert tenant_id_info["type"] == "str"
        assert "description" in tenant_id_info
        assert "example" in tenant_id_info
        assert "default" in tenant_id_info

        # Check range for max_tool_iterations
        max_iter_info = options["optional"]["max_tool_iterations"]
        assert "range" in max_iter_info
        assert max_iter_info["range"] == [1, 50]

    def test_get_gateway_config_options(self):
        """Test get_gateway_config_options function."""
        options = get_gateway_config_options()

        assert "required" in options
        assert "optional" in options
        assert "example" in options

        # Check required fields
        assert "api_keys" in options["required"]

        # Check optional fields
        assert "providers" in options["optional"]
        assert "default_model" in options["optional"]
        assert "timeout" in options["optional"]
        assert "max_retries" in options["optional"]
        assert "retry_delay" in options["optional"]
        assert "fallbacks" in options["optional"]

        # Check valid_options for default_model
        default_model_info = options["optional"]["default_model"]
        assert "valid_options" in default_model_info
        assert "gpt-4" in default_model_info["valid_options"]
        assert "gpt-3.5-turbo" in default_model_info["valid_options"]

        # Check ranges
        timeout_info = options["optional"]["timeout"]
        assert "range" in timeout_info
        assert timeout_info["range"] == [1.0, 300.0]

        max_retries_info = options["optional"]["max_retries"]
        assert "range" in max_retries_info
        assert max_retries_info["range"] == [0, 10]

    def test_get_rag_config_options(self):
        """Test get_rag_config_options function."""
        options = get_rag_config_options()

        assert "required" in options
        assert "optional" in options
        assert "example" in options

        # Check required fields
        assert "db" in options["required"]
        assert "gateway" in options["required"]

        # Check optional fields
        assert "tenant_id" in options["optional"]
        assert "embedding_model" in options["optional"]
        assert "chunk_size" in options["optional"]
        assert "chunk_overlap" in options["optional"]
        assert "top_k" in options["optional"]

        # Check ranges
        chunk_size_info = options["optional"]["chunk_size"]
        assert "range" in chunk_size_info
        assert chunk_size_info["range"] == [100, 10000]

        chunk_overlap_info = options["optional"]["chunk_overlap"]
        assert "range" in chunk_overlap_info
        assert chunk_overlap_info["range"] == [0, 1000]

        top_k_info = options["optional"]["top_k"]
        assert "range" in top_k_info
        assert top_k_info["range"] == [1, 50]


class TestPrintConfigOptions:
    """Test print_config_options function."""

    @patch("sys.stdout", new_callable=StringIO)
    @patch("src.core.utils.config_discovery.ConfigHelper")
    def test_print_config_options_agent(self, mock_config_helper, mock_stdout):
        """Test print_config_options for agent component."""
        mock_config_helper.get_config_example.return_value = {"agent_id": "test", "name": "Test"}
        print_config_options("agent")

        output = mock_stdout.getvalue()
        assert "Configuration Options for: AGENT" in output
        assert "REQUIRED OPTIONS:" in output
        assert "OPTIONAL OPTIONS:" in output
        assert "EXAMPLE CONFIGURATION:" in output
        assert "agent_id" in output

    @patch("sys.stdout", new_callable=StringIO)
    @patch("src.core.utils.config_discovery.ConfigHelper")
    def test_print_config_options_gateway(self, mock_config_helper, mock_stdout):
        """Test print_config_options for gateway component."""
        mock_config_helper.get_config_example.return_value = {"api_keys": {}}
        print_config_options("gateway")

        output = mock_stdout.getvalue()
        assert "Configuration Options for: GATEWAY" in output
        assert "REQUIRED OPTIONS:" in output
        assert "api_keys" in output

    @patch("sys.stdout", new_callable=StringIO)
    @patch("src.core.utils.config_discovery.ConfigHelper")
    def test_print_config_options_rag(self, mock_config_helper, mock_stdout):
        """Test print_config_options for RAG component."""
        mock_config_helper.get_config_example.return_value = {"db": None, "gateway": None}
        print_config_options("rag")

        output = mock_stdout.getvalue()
        assert "Configuration Options for: RAG" in output
        assert "REQUIRED OPTIONS:" in output
        assert "db" in output
        assert "gateway" in output

    @patch("sys.stdout", new_callable=StringIO)
    @patch("src.core.utils.config_discovery.ConfigHelper")
    def test_print_config_options_tool(self, mock_config_helper, mock_stdout):
        """Test print_config_options for tool component."""
        mock_config_helper.get_config_example.return_value = {"tool_id": "test"}
        print_config_options("tool")

        output = mock_stdout.getvalue()
        assert "Configuration Options for: TOOL" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_print_config_options_unknown(self, mock_stdout):
        """Test print_config_options for unknown component."""
        print_config_options("unknown_component")

        output = mock_stdout.getvalue()
        assert "Unknown component: unknown_component" in output
        assert "Available components:" in output
        assert "agent" in output
        assert "gateway" in output
        assert "rag" in output

    @patch("sys.stdout", new_callable=StringIO)
    @patch("src.core.utils.config_discovery.ConfigHelper")
    def test_print_config_options_case_insensitive(self, mock_config_helper, mock_stdout):
        """Test print_config_options is case insensitive."""
        mock_config_helper.get_config_example.return_value = {"agent_id": "test"}
        print_config_options("AGENT")

        output = mock_stdout.getvalue()
        assert "Configuration Options for: AGENT" in output


class TestDiscoverConfig:
    """Test discover_config function."""

    def test_discover_config_agent_no_partial(self):
        """Test discover_config for agent without partial config."""
        result = discover_config("agent")

        assert result["component"] == "agent"
        assert "options" in result
        assert result["validation"] is None
        assert "required" in result["options"]
        assert "optional" in result["options"]

    def test_discover_config_gateway_no_partial(self):
        """Test discover_config for gateway without partial config."""
        result = discover_config("gateway")

        assert result["component"] == "gateway"
        assert "options" in result
        assert result["validation"] is None

    def test_discover_config_rag_no_partial(self):
        """Test discover_config for RAG without partial config."""
        result = discover_config("rag")

        assert result["component"] == "rag"
        assert "options" in result
        assert result["validation"] is None

    @patch("src.core.utils.config_validator.ConfigHelper")
    def test_discover_config_with_valid_partial(self, mock_config_helper):
        """Test discover_config with valid partial configuration."""
        mock_config_helper.validate_and_suggest.return_value = {
            "agent_id": "agent1",
            "name": "Test Agent",
        }

        partial_config = {"agent_id": "agent1", "name": "Test Agent"}
        result = discover_config("agent", partial_config=partial_config)

        # Component name is preserved as passed
        assert result["component"] == "agent"
        assert "options" in result
        assert result["validation"] is not None
        assert result["validation"]["valid"] is True
        assert "config" in result["validation"]

        mock_config_helper.validate_and_suggest.assert_called_once()

    @patch("src.core.utils.config_validator.ConfigHelper")
    def test_discover_config_with_invalid_partial(self, mock_config_helper):
        """Test discover_config with invalid partial configuration."""
        # Create a custom exception class with suggestion attribute
        class ConfigError(ValueError):
            def __init__(self, message: str, suggestion: Optional[str] = None):
                super().__init__(message)
                self.suggestion = suggestion

        error = ConfigError("Invalid configuration", "Fix the configuration")
        mock_config_helper.validate_and_suggest.side_effect = error

        partial_config = {"invalid": "config"}
        result = discover_config("agent", partial_config=partial_config)

        assert result["component"] == "agent"
        assert "options" in result
        assert result["validation"] is not None
        assert result["validation"]["valid"] is False
        assert "error" in result["validation"]
        assert "suggestions" in result["validation"]

    def test_discover_config_unknown_component(self):
        """Test discover_config with unknown component."""
        result = discover_config("unknown_component")

        assert "error" in result
        assert "Unknown component" in result["error"]
        assert "available_components" in result
        assert "agent" in result["available_components"]
        assert "gateway" in result["available_components"]
        assert "rag" in result["available_components"]

    def test_discover_config_case_insensitive(self):
        """Test discover_config is case insensitive for lookup but preserves original case."""
        result = discover_config("AGENT")

        # Component name is preserved as-is (not normalized)
        assert result["component"] == "AGENT"
        assert "options" in result

    @patch("src.core.utils.config_validator.ConfigHelper")
    def test_discover_config_exception_without_suggestion(self, mock_config_helper):
        """Test discover_config when exception has no suggestion attribute."""
        error = ValueError("Invalid configuration")
        # No suggestion attribute
        mock_config_helper.validate_and_suggest.side_effect = error

        partial_config = {"invalid": "config"}
        result = discover_config("agent", partial_config=partial_config)

        assert result["validation"]["valid"] is False
        assert result["validation"]["suggestions"] is None

