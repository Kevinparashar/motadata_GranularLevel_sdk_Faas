"""
Unit Tests for Agent Tools

Tests tool system functionality for agents.
"""


import asyncio
import inspect

import pytest

from src.core.agno_agent_framework.exceptions import (
    ToolInvocationError,
    ToolNotFoundError,
    ToolNotImplementedError,
    ToolValidationError,
)
from src.core.agno_agent_framework.tools import (
    Tool,
    ToolExecutor,
    ToolParameter,
    ToolRegistry,
    ToolType,
)


class TestToolType:
    """Test ToolType enum."""

    def test_tool_type_values(self):
        """Test ToolType enum values."""
        assert ToolType.FUNCTION == "function"
        assert ToolType.API == "api"
        assert ToolType.DATABASE == "database"
        assert ToolType.FILE == "file"
        assert ToolType.CUSTOM == "custom"


class TestToolParameter:
    """Test ToolParameter class."""

    def test_tool_parameter_init(self):
        """Test ToolParameter initialization."""
        param = ToolParameter(
            name="test_param",
            type="string",
            description="Test parameter",
            required=True,
            default=None,
        )

        assert param.name == "test_param"
        assert param.type == "string"
        assert param.description == "Test parameter"
        assert param.required is True
        assert param.default is None

    def test_tool_parameter_with_default(self):
        """Test ToolParameter with default value."""
        param = ToolParameter(
            name="test_param",
            type="integer",
            description="Test parameter",
            required=False,
            default=10,
        )

        assert param.default == 10
        assert param.required is False


class TestTool:
    """Test Tool class."""

    def test_tool_init(self):
        """Test Tool initialization."""
        tool = Tool(
            tool_id="tool1",
            name="test_tool",
            description="Test tool",
            tool_type=ToolType.FUNCTION,
        )

        assert tool.tool_id == "tool1"
        assert tool.name == "test_tool"
        assert tool.description == "Test tool"
        assert tool.tool_type == ToolType.FUNCTION
        assert tool.function is None
        assert tool.parameters == []
        assert tool.metadata == {}
        assert tool.tags == []

    def test_tool_init_with_function(self):
        """Test Tool initialization with function."""
        def test_func(x: int) -> int:
            return x * 2

        tool = Tool(
            tool_id="tool1",
            name="test_tool",
            description="Test tool",
            function=test_func,
        )

        assert tool.function == test_func

    @pytest.mark.asyncio
    async def test_execute_without_function(self):
        """Test execute when function is None to cover line 84."""
        tool = Tool(tool_id="tool1", name="test_tool", description="Test")

        with pytest.raises(ToolNotImplementedError):
            await tool.execute()

    @pytest.mark.asyncio
    async def test_execute_async_function(self):
        """Test execute with async function to cover line 100."""
        async def async_func(x: int) -> int:  # noqa: ARG001
            await asyncio.sleep(0)  # Use async feature
            return x * 2

        tool = Tool(
            tool_id="tool1",
            name="test_tool",
            description="Test",
            function=async_func,
        )

        result = await tool.execute(x=5)

        assert result == 10

    @pytest.mark.asyncio
    async def test_execute_sync_function(self):
        """Test execute with sync function to cover lines 102-104."""
        def sync_func(x: int) -> int:
            return x * 3

        tool = Tool(
            tool_id="tool1",
            name="test_tool",
            description="Test",
            function=sync_func,
        )

        result = await tool.execute(x=5)

        assert result == 15

    @pytest.mark.asyncio
    async def test_execute_validation_error(self):
        """Test execute with validation error to cover lines 89-95."""
        def test_func(x: int) -> int:
            return x * 2

        param = ToolParameter(name="x", type="integer", description="X value", required=True)
        tool = Tool(
            tool_id="tool1",
            name="test_tool",
            description="Test",
            function=test_func,
            parameters=[param],
        )

        with pytest.raises(ToolValidationError):
            await tool.execute()  # Missing required parameter

    @pytest.mark.asyncio
    async def test_execute_invocation_error(self):
        """Test execute with invocation error to cover lines 108-114."""
        def failing_func(x: int) -> int:
            raise RuntimeError("Function failed")

        tool = Tool(
            tool_id="tool1",
            name="test_tool",
            description="Test",
            function=failing_func,
        )

        with pytest.raises(ToolInvocationError) as exc_info:
            await tool.execute(x=5)

        assert exc_info.value.tool_name == "test_tool"
        assert exc_info.value.error_type == "runtime"

    @pytest.mark.asyncio
    async def test_execute_tool_invocation_error_passthrough(self):
        """Test execute when ToolInvocationError is raised directly to cover line 106."""
        def func_raising_tool_error(x: int) -> int:
            raise ToolInvocationError("Tool error", tool_name="test_tool")

        tool = Tool(
            tool_id="tool1",
            name="test_tool",
            description="Test",
            function=func_raising_tool_error,
        )

        with pytest.raises(ToolInvocationError) as exc_info:
            await tool.execute(x=5)

        assert exc_info.value.tool_name == "test_tool"

    def test_validate_parameters_missing(self):
        """Test _validate_parameters with missing required parameters to cover lines 134-139."""
        param = ToolParameter(name="x", type="integer", description="X value", required=True)
        tool = Tool(
            tool_id="tool1",
            name="test_tool",
            description="Test",
            parameters=[param],
        )

        with pytest.raises(ToolValidationError) as exc_info:
            tool._validate_parameters({})

        assert "x" in exc_info.value.missing_parameters

    def test_validate_parameters_success(self):
        """Test _validate_parameters with valid parameters."""
        param = ToolParameter(name="x", type="integer", description="X value", required=True)
        tool = Tool(
            tool_id="tool1",
            name="test_tool",
            description="Test",
            parameters=[param],
        )

        # Should not raise
        tool._validate_parameters({"x": 5})

    def test_get_schema(self):
        """Test get_schema method."""
        param1 = ToolParameter(name="x", type="integer", description="X value", required=True)
        param2 = ToolParameter(name="y", type="string", description="Y value", required=False, default="default")
        tool = Tool(
            tool_id="tool1",
            name="test_tool",
            description="Test tool",
            parameters=[param1, param2],
        )

        schema = tool.get_schema()

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "test_tool"
        assert schema["function"]["description"] == "Test tool"
        assert "x" in schema["function"]["parameters"]["properties"]
        assert "y" in schema["function"]["parameters"]["properties"]
        assert "x" in schema["function"]["parameters"]["required"]
        assert "y" not in schema["function"]["parameters"]["required"]


class TestToolRegistry:
    """Test ToolRegistry class."""

    @pytest.fixture
    def registry(self):
        """Create a ToolRegistry instance."""
        return ToolRegistry()

    def test_init(self, registry):
        """Test ToolRegistry initialization."""
        assert len(registry._tools) == 0

    def test_detect_param_type_int(self, registry):
        """Test _detect_param_type for integer to cover line 190."""
        param = inspect.Parameter("x", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=int)
        param_type = registry._detect_param_type(param)

        assert param_type == "integer"

    def test_detect_param_type_float(self, registry):
        """Test _detect_param_type for float to cover line 192."""
        param = inspect.Parameter("x", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=float)
        param_type = registry._detect_param_type(param)

        assert param_type == "number"

    def test_detect_param_type_bool(self, registry):
        """Test _detect_param_type for bool to cover line 194."""
        param = inspect.Parameter("x", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=bool)
        param_type = registry._detect_param_type(param)

        assert param_type == "boolean"

    def test_detect_param_type_list(self, registry):
        """Test _detect_param_type for list to cover line 196."""
        param = inspect.Parameter("x", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=list)
        param_type = registry._detect_param_type(param)

        assert param_type == "array"

    def test_detect_param_type_empty(self, registry):
        """Test _detect_param_type for empty annotation to cover line 186."""
        param = inspect.Parameter("x", inspect.Parameter.POSITIONAL_OR_KEYWORD)
        param_type = registry._detect_param_type(param)

        assert param_type == "string"

    def test_detect_param_type_string(self, registry):
        """Test _detect_param_type for string."""
        param = inspect.Parameter("x", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=str)
        param_type = registry._detect_param_type(param)

        assert param_type == "string"

    def test_create_tool_parameter(self, registry):
        """Test _create_tool_parameter to cover lines 210-216."""
        param = inspect.Parameter("x", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=int, default=inspect.Parameter.empty)
        tool_param = registry._create_tool_parameter("x", param)

        assert tool_param.name == "x"
        assert tool_param.type == "integer"
        assert tool_param.required is True
        assert tool_param.default is None

    def test_create_tool_parameter_with_default(self, registry):
        """Test _create_tool_parameter with default value."""
        param = inspect.Parameter("x", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=int, default=10)
        tool_param = registry._create_tool_parameter("x", param)

        assert tool_param.required is False
        assert tool_param.default == 10

    def test_auto_detect_parameters(self, registry):
        """Test _auto_detect_parameters to cover lines 228-232."""
        def test_func(x: int, y: str = "default") -> int:
            return x

        params = registry._auto_detect_parameters(test_func)

        assert len(params) == 2
        assert params[0].name == "x"
        assert params[0].type == "integer"
        assert params[0].required is True
        assert params[1].name == "y"
        assert params[1].required is False

    def test_register_tool(self, registry):
        """Test register_tool method."""
        tool = Tool(tool_id="tool1", name="test_tool", description="Test")

        registry.register_tool(tool)

        assert "tool1" in registry._tools
        assert registry._tools["tool1"] == tool

    def test_register_tool_with_auto_detect(self, registry):
        """Test register_tool with auto_register_function to cover lines 245-246."""
        def test_func(x: int) -> int:
            return x * 2

        tool = Tool(
            tool_id="tool1",
            name="test_tool",
            description="Test",
            function=test_func,
        )

        registry.register_tool(tool, auto_register_function=True)

        assert len(tool.parameters) > 0
        assert tool.parameters[0].name == "x"

    def test_register_tool_without_auto_detect(self, registry):
        """Test register_tool without auto_register_function."""
        def test_func(x: int) -> int:
            return x * 2

        tool = Tool(
            tool_id="tool1",
            name="test_tool",
            description="Test",
            function=test_func,
        )

        registry.register_tool(tool, auto_register_function=False)

        assert len(tool.parameters) == 0

    def test_register_function(self, registry):
        """Test register_function method to cover lines 265-276."""
        def test_func(x: int) -> int:
            return x * 2

        tool = registry.register_function("test_tool", test_func, "Test tool description")

        assert tool.name == "test_tool"
        assert tool.description == "Test tool description"
        assert tool.function == test_func
        assert tool.tool_id in registry._tools

    def test_register_function_with_tool_id(self, registry):
        """Test register_function with custom tool_id."""
        def test_func(x: int) -> int:
            return x * 2

        tool = registry.register_function("test_tool", test_func, "Test", tool_id="custom_id")

        assert tool.tool_id == "custom_id"

    def test_get_tool(self, registry):
        """Test get_tool method."""
        tool = Tool(tool_id="tool1", name="test_tool", description="Test")
        registry.register_tool(tool)

        retrieved = registry.get_tool("tool1")
        assert retrieved == tool

        not_found = registry.get_tool("nonexistent")
        assert not_found is None

    def test_get_tool_by_name(self, registry):
        """Test get_tool_by_name method to cover lines 300-303."""
        tool = Tool(tool_id="tool1", name="test_tool", description="Test")
        registry.register_tool(tool)

        retrieved = registry.get_tool_by_name("test_tool")
        assert retrieved == tool

        not_found = registry.get_tool_by_name("nonexistent")
        assert not_found is None

    def test_list_tools(self, registry):
        """Test list_tools method."""
        tool1 = Tool(tool_id="tool1", name="tool1", description="Test", tags=["tag1"])
        tool2 = Tool(tool_id="tool2", name="tool2", description="Test", tags=["tag2"])
        registry.register_tool(tool1)
        registry.register_tool(tool2)

        tools = registry.list_tools()

        assert len(tools) == 2

    def test_list_tools_with_tags(self, registry):
        """Test list_tools with tags filter to cover lines 317-318."""
        tool1 = Tool(tool_id="tool1", name="tool1", description="Test", tags=["tag1", "common"])
        tool2 = Tool(tool_id="tool2", name="tool2", description="Test", tags=["tag2", "common"])
        registry.register_tool(tool1)
        registry.register_tool(tool2)

        tools = registry.list_tools(tags=["tag1"])

        assert len(tools) == 1
        assert tools[0].tool_id == "tool1"

    def test_get_tools_schema(self, registry):
        """Test get_tools_schema method."""
        tool = Tool(tool_id="tool1", name="test_tool", description="Test")
        registry.register_tool(tool)

        schemas = registry.get_tools_schema()

        assert len(schemas) == 1
        assert schemas[0]["function"]["name"] == "test_tool"


class TestToolExecutor:
    """Test ToolExecutor class."""

    @pytest.fixture
    def registry(self):
        """Create a ToolRegistry instance."""
        return ToolRegistry()

    @pytest.fixture
    def executor(self, registry):
        """Create a ToolExecutor instance."""
        return ToolExecutor(registry)

    def test_init(self, registry):
        """Test ToolExecutor initialization."""
        executor = ToolExecutor(registry)

        assert executor.registry == registry

    @pytest.mark.asyncio
    async def test_execute_tool_call_success(self, executor, registry):
        """Test execute_tool_call with successful execution."""
        async def test_func(x: int) -> int:  # noqa: ARG001
            await asyncio.sleep(0)  # Use async feature
            return x * 2

        tool = Tool(
            tool_id="tool1",
            name="test_tool",
            description="Test",
            function=test_func,
        )
        registry.register_tool(tool)

        result = await executor.execute_tool_call("test_tool", {"x": 5})

        assert result == 10

    @pytest.mark.asyncio
    async def test_execute_tool_call_not_found(self, executor):
        """Test execute_tool_call when tool not found to cover lines 360-361."""
        with pytest.raises(ToolNotFoundError):
            await executor.execute_tool_call("nonexistent_tool", {})

