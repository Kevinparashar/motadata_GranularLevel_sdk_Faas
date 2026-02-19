"""
Unit Tests for PromptInterpreter OTEL Integration

Tests for OpenTelemetry integration within the PromptInterpreter component.
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.prompt_based_generator.prompt_interpreter import PromptInterpreter
from src.core.otel_integration import OTELMetrics, OTELTracer


class TestPromptInterpreterOTELIntegration:
    """Tests for PromptInterpreter OTEL integration."""

    def test_prompt_interpreter_with_otel_tracer(self):
        """Test prompt interpreter initialization with OTEL tracer."""
        tracer = OTELTracer(service_name="test-prompt-interpreter")
        gateway = MagicMock()
        
        interpreter = PromptInterpreter(
            gateway=gateway,
            otel_tracer=tracer,
        )
        
        assert interpreter.otel_tracer is not None
        assert interpreter.otel_tracer.service_name == "test-prompt-interpreter"

    def test_prompt_interpreter_with_otel_metrics(self):
        """Test prompt interpreter initialization with OTEL metrics."""
        metrics = OTELMetrics(service_name="test-prompt-interpreter")
        gateway = MagicMock()
        
        interpreter = PromptInterpreter(
            gateway=gateway,
            otel_metrics=metrics,
        )
        
        assert interpreter.otel_metrics is not None
        assert interpreter.otel_metrics.service_name == "test-prompt-interpreter"

    def test_prompt_interpreter_without_otel(self):
        """Test prompt interpreter works without OTEL configured."""
        gateway = MagicMock()
        
        interpreter = PromptInterpreter(gateway=gateway)
        
        # OTEL should be auto-initialized if available
        # But it may be None if OTEL SDK is not installed
        assert interpreter is not None

    @pytest.mark.asyncio
    async def test_interpret_agent_prompt_with_otel(self):
        """Test interpret_agent_prompt operation with OTEL tracing."""
        tracer = OTELTracer(service_name="test-prompt-interpreter")
        metrics = OTELMetrics(service_name="test-prompt-interpreter")
        
        gateway = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "name": "test_agent",
            "description": "Test agent description",
            "capabilities": ["capability1"],
            "system_prompt": "You are a test agent",
            "required_tools": [],
            "memory_config": {},
            "max_context_tokens": 4000,
            "enable_tool_calling": True,
            "metadata": {}
        })
        gateway.generate_async = AsyncMock(return_value=mock_response)
        
        interpreter = PromptInterpreter(
            gateway=gateway,
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        # Execute interpret_agent_prompt - should not raise exception
        result = await interpreter.interpret_agent_prompt("Create an agent that tests things")
        
        assert result is not None
        assert result.name == "test_agent"
        assert interpreter.otel_tracer is not None
        assert interpreter.otel_metrics is not None

    @pytest.mark.asyncio
    async def test_interpret_agent_prompt_without_otel(self):
        """Test interpret_agent_prompt operation without OTEL."""
        gateway = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "name": "test_agent",
            "description": "Test agent description",
            "capabilities": ["capability1"],
            "system_prompt": "You are a test agent",
            "required_tools": [],
            "memory_config": {},
            "max_context_tokens": 4000,
            "enable_tool_calling": True,
            "metadata": {}
        })
        gateway.generate_async = AsyncMock(return_value=mock_response)
        
        interpreter = PromptInterpreter(gateway=gateway)
        interpreter.otel_tracer = None
        interpreter.otel_metrics = None
        
        result = await interpreter.interpret_agent_prompt("Create an agent that tests things")
        
        assert result is not None
        assert result.name == "test_agent"

    @pytest.mark.asyncio
    async def test_interpret_agent_prompt_with_cache_otel(self):
        """Test interpret_agent_prompt with cache and OTEL."""
        tracer = OTELTracer(service_name="test-prompt-interpreter")
        metrics = OTELMetrics(service_name="test-prompt-interpreter")
        
        gateway = MagicMock()
        cache = MagicMock()
        cached_data = json.dumps({
            "name": "cached_agent",
            "description": "Cached agent description",
            "capabilities": ["capability1"],
            "system_prompt": "You are a cached agent",
            "required_tools": [],
            "memory_config": {},
            "max_context_tokens": 4000,
            "enable_tool_calling": True,
            "metadata": {}
        })
        cache.get = AsyncMock(return_value=cached_data)
        
        interpreter = PromptInterpreter(
            gateway=gateway,
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        result = await interpreter.interpret_agent_prompt(
            "Create an agent",
            cache=cache,
            tenant_id="tenant_123"
        )
        
        assert result is not None
        assert result.name == "cached_agent"
        assert interpreter.otel_tracer is not None

    @pytest.mark.asyncio
    async def test_interpret_agent_prompt_error_with_otel(self):
        """Test interpret_agent_prompt error handling with OTEL."""
        tracer = OTELTracer(service_name="test-prompt-interpreter")
        metrics = OTELMetrics(service_name="test-prompt-interpreter")
        
        gateway = MagicMock()
        gateway.generate_async = AsyncMock(side_effect=Exception("Gateway error"))
        
        interpreter = PromptInterpreter(
            gateway=gateway,
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        with pytest.raises(Exception):
            await interpreter.interpret_agent_prompt("Create an agent")
        
        assert interpreter.otel_tracer is not None
        assert interpreter.otel_metrics is not None

    @pytest.mark.asyncio
    async def test_interpret_tool_prompt_with_otel(self):
        """Test interpret_tool_prompt operation with OTEL tracing."""
        tracer = OTELTracer(service_name="test-prompt-interpreter")
        metrics = OTELMetrics(service_name="test-prompt-interpreter")
        
        gateway = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "name": "test_tool",
            "description": "Test tool description",
            "function_name": "test_function",
            "parameters": [],
            "return_type": "str",
            "code_template": "def test_function(): pass",
            "metadata": {}
        })
        gateway.generate_async = AsyncMock(return_value=mock_response)
        
        interpreter = PromptInterpreter(
            gateway=gateway,
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        # Execute interpret_tool_prompt - should not raise exception
        result = await interpreter.interpret_tool_prompt("Create a tool that tests things")
        
        assert result is not None
        assert result.name == "test_tool"
        assert interpreter.otel_tracer is not None
        assert interpreter.otel_metrics is not None

    @pytest.mark.asyncio
    async def test_interpret_tool_prompt_without_otel(self):
        """Test interpret_tool_prompt operation without OTEL."""
        gateway = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "name": "test_tool",
            "description": "Test tool description",
            "function_name": "test_function",
            "parameters": [],
            "return_type": "str",
            "code_template": "def test_function(): pass",
            "metadata": {}
        })
        gateway.generate_async = AsyncMock(return_value=mock_response)
        
        interpreter = PromptInterpreter(gateway=gateway)
        interpreter.otel_tracer = None
        interpreter.otel_metrics = None
        
        result = await interpreter.interpret_tool_prompt("Create a tool that tests things")
        
        assert result is not None
        assert result.name == "test_tool"

    @pytest.mark.asyncio
    async def test_interpret_tool_prompt_with_cache_otel(self):
        """Test interpret_tool_prompt with cache and OTEL."""
        tracer = OTELTracer(service_name="test-prompt-interpreter")
        metrics = OTELMetrics(service_name="test-prompt-interpreter")
        
        gateway = MagicMock()
        cache = MagicMock()
        cached_data = json.dumps({
            "name": "cached_tool",
            "description": "Cached tool description",
            "function_name": "cached_function",
            "parameters": [],
            "return_type": "str",
            "code_template": "def cached_function(): pass",
            "metadata": {}
        })
        cache.get = AsyncMock(return_value=cached_data)
        
        interpreter = PromptInterpreter(
            gateway=gateway,
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        result = await interpreter.interpret_tool_prompt(
            "Create a tool",
            cache=cache,
            tenant_id="tenant_123"
        )
        
        assert result is not None
        assert result.name == "cached_tool"
        assert interpreter.otel_tracer is not None

    @pytest.mark.asyncio
    async def test_interpret_tool_prompt_error_with_otel(self):
        """Test interpret_tool_prompt error handling with OTEL."""
        tracer = OTELTracer(service_name="test-prompt-interpreter")
        metrics = OTELMetrics(service_name="test-prompt-interpreter")
        
        gateway = MagicMock()
        gateway.generate_async = AsyncMock(side_effect=Exception("Gateway error"))
        
        interpreter = PromptInterpreter(
            gateway=gateway,
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        with pytest.raises(Exception):
            await interpreter.interpret_tool_prompt("Create a tool")
        
        assert interpreter.otel_tracer is not None
        assert interpreter.otel_metrics is not None

    @pytest.mark.asyncio
    async def test_interpret_agent_prompt_json_error_with_otel(self):
        """Test interpret_agent_prompt JSON parse error with OTEL."""
        tracer = OTELTracer(service_name="test-prompt-interpreter")
        metrics = OTELMetrics(service_name="test-prompt-interpreter")
        
        gateway = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Invalid JSON response"
        gateway.generate_async = AsyncMock(return_value=mock_response)
        
        interpreter = PromptInterpreter(
            gateway=gateway,
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        with pytest.raises(Exception):
            await interpreter.interpret_agent_prompt("Create an agent")
        
        assert interpreter.otel_tracer is not None
        assert interpreter.otel_metrics is not None

    @pytest.mark.asyncio
    async def test_interpret_agent_prompt_with_invalid_cache_otel(self):
        """Test interpret_agent_prompt with invalid cached JSON and OTEL."""
        tracer = OTELTracer(service_name="test-prompt-interpreter")
        metrics = OTELMetrics(service_name="test-prompt-interpreter")
        
        gateway = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "name": "test_agent",
            "description": "Test agent description",
            "capabilities": ["capability1"],
            "system_prompt": "You are a test agent",
            "required_tools": [],
            "memory_config": {},
            "max_context_tokens": 4000,
            "enable_tool_calling": True,
            "metadata": {}
        })
        gateway.generate_async = AsyncMock(return_value=mock_response)
        
        cache = MagicMock()
        cache.get = AsyncMock(return_value="invalid json")
        cache.set = AsyncMock()
        
        interpreter = PromptInterpreter(
            gateway=gateway,
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        result = await interpreter.interpret_agent_prompt(
            "Create an agent",
            cache=cache,
            tenant_id="tenant_123"
        )
        
        assert result is not None
        assert result.name == "test_agent"
        # Verify cache.set was called
        cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_interpret_agent_prompt_with_code_block_marker_otel(self):
        """Test interpret_agent_prompt with JSON code block marker and OTEL."""
        tracer = OTELTracer(service_name="test-prompt-interpreter")
        metrics = OTELMetrics(service_name="test-prompt-interpreter")
        
        gateway = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "```json\n" + json.dumps({
            "name": "test_agent",
            "description": "Test agent description",
            "capabilities": ["capability1"],
            "system_prompt": "You are a test agent",
            "required_tools": [],
            "memory_config": {},
            "max_context_tokens": 4000,
            "enable_tool_calling": True,
            "metadata": {}
        }) + "\n```"
        gateway.generate_async = AsyncMock(return_value=mock_response)
        
        interpreter = PromptInterpreter(
            gateway=gateway,
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        result = await interpreter.interpret_agent_prompt("Create an agent")
        
        assert result is not None
        assert result.name == "test_agent"

    @pytest.mark.asyncio
    async def test_interpret_agent_prompt_without_otel_cache_set(self):
        """Test interpret_agent_prompt without OTEL but with cache set."""
        gateway = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "name": "test_agent",
            "description": "Test agent description",
            "capabilities": ["capability1"],
            "system_prompt": "You are a test agent",
            "required_tools": [],
            "memory_config": {},
            "max_context_tokens": 4000,
            "enable_tool_calling": True,
            "metadata": {}
        })
        gateway.generate_async = AsyncMock(return_value=mock_response)
        
        cache = MagicMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        
        interpreter = PromptInterpreter(gateway=gateway)
        interpreter.otel_tracer = None
        interpreter.otel_metrics = None
        
        result = await interpreter.interpret_agent_prompt(
            "Create an agent",
            cache=cache,
            tenant_id="tenant_123"
        )
        
        assert result is not None
        cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_interpret_tool_prompt_with_invalid_cache_otel(self):
        """Test interpret_tool_prompt with invalid cached JSON and OTEL."""
        tracer = OTELTracer(service_name="test-prompt-interpreter")
        metrics = OTELMetrics(service_name="test-prompt-interpreter")
        
        gateway = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "name": "test_tool",
            "description": "Test tool description",
            "function_name": "test_function",
            "parameters": [],
            "return_type": "str",
            "code_template": "def test_function(): pass",
            "metadata": {}
        })
        gateway.generate_async = AsyncMock(return_value=mock_response)
        
        cache = MagicMock()
        cache.get = AsyncMock(return_value="invalid json")
        cache.set = AsyncMock()
        
        interpreter = PromptInterpreter(
            gateway=gateway,
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        result = await interpreter.interpret_tool_prompt(
            "Create a tool",
            cache=cache,
            tenant_id="tenant_123"
        )
        
        assert result is not None
        assert result.name == "test_tool"
        cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_interpret_tool_prompt_with_code_block_otel(self):
        """Test interpret_tool_prompt with code block and OTEL."""
        tracer = OTELTracer(service_name="test-prompt-interpreter")
        metrics = OTELMetrics(service_name="test-prompt-interpreter")
        
        gateway = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "```\n" + json.dumps({
            "name": "test_tool",
            "description": "Test tool description",
            "function_name": "test_function",
            "parameters": [],
            "return_type": "str",
            "code_template": "def test_function(): pass",
            "metadata": {}
        }) + "\n```"
        gateway.generate_async = AsyncMock(return_value=mock_response)
        
        interpreter = PromptInterpreter(
            gateway=gateway,
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        result = await interpreter.interpret_tool_prompt("Create a tool")
        
        assert result is not None
        assert result.name == "test_tool"

    @pytest.mark.asyncio
    async def test_interpret_tool_prompt_without_otel_cache_set(self):
        """Test interpret_tool_prompt without OTEL but with cache set."""
        gateway = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "name": "test_tool",
            "description": "Test tool description",
            "function_name": "test_function",
            "parameters": [],
            "return_type": "str",
            "code_template": "def test_function(): pass",
            "metadata": {}
        })
        gateway.generate_async = AsyncMock(return_value=mock_response)
        
        cache = MagicMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        
        interpreter = PromptInterpreter(gateway=gateway)
        interpreter.otel_tracer = None
        interpreter.otel_metrics = None
        
        result = await interpreter.interpret_tool_prompt(
            "Create a tool",
            cache=cache,
            tenant_id="tenant_123"
        )
        
        assert result is not None
        cache.set.assert_called_once()

