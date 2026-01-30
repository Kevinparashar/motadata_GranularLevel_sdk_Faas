"""
Agent Tools

Tools that agents can use to extend their capabilities.
"""

import inspect
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

from .exceptions import (
    ToolInvocationError,
    ToolNotFoundError,
    ToolNotImplementedError,
    ToolValidationError,
)


class ToolType(str, Enum):
    """Tool type enumeration."""

    FUNCTION = "function"
    API = "api"
    DATABASE = "database"
    FILE = "file"
    CUSTOM = "custom"


class ToolParameter(BaseModel):
    """Tool parameter definition."""

    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None


class Tool(BaseModel):
    """
    Tool definition for agent use.

    Tools extend agent capabilities by providing functions
    that agents can call during task execution.
    """

    tool_id: str
    name: str
    description: str
    tool_type: ToolType = ToolType.FUNCTION

    # Function/implementation
    function: Optional[Callable] = None
    parameters: List[ToolParameter] = Field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True

    def execute(self, **kwargs: Any) -> Any:
        """
        Execute the tool.

        Args:
            **kwargs: Tool parameters

        Returns:
            Tool execution result

        Raises:
            ToolNotImplementedError: If tool has no function implementation
            ToolValidationError: If required parameters are missing
            ToolInvocationError: If tool execution fails
        """
        if self.function is None:
            raise ToolNotImplementedError(self.name)

        # Validate parameters
        try:
            self._validate_parameters(kwargs)
        except ValueError as e:
            raise ToolValidationError(
                message=f"Tool '{self.name}' validation failed: {str(e)}",
                tool_name=self.name,
                missing_parameters=[str(e)],
                original_error=e,
            )

        # Execute function
        try:
            return self.function(**kwargs)
        except ToolInvocationError:
            # Re-raise tool invocation errors as-is
            raise
        except Exception as e:
            raise ToolInvocationError(
                message=f"Tool {self.name} execution failed: {str(e)}",
                tool_name=self.name,
                arguments=kwargs,
                error_type="runtime",
                original_error=e,
            )

    def _validate_parameters(self, provided: Dict[str, Any]) -> None:
        """
        Validate provided parameters.

        Args:
            provided: Provided parameters

        Raises:
            ToolValidationError: If validation fails
        """
        missing_params = []
        for param in self.parameters:
            if param.required and param.name not in provided:
                missing_params.append(param.name)

        if missing_params:
            raise ToolValidationError(
                message=f"Required parameters missing: {', '.join(missing_params)}",
                tool_name=self.name,
                missing_parameters=missing_params,
            )

    def get_schema(self) -> Dict[str, Any]:
        """
        Get tool schema for LLM function calling.

        Returns:
            Tool schema dictionary
        """
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = {"type": param.type, "description": param.description}
            if param.default is not None:
                properties[param.name]["default"] = param.default
            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {"type": "object", "properties": properties, "required": required},
            },
        }


class ToolRegistry:
    """Registry for managing agent tools."""

    def __init__(self):
        """Initialize tool registry."""
        self._tools: Dict[str, Tool] = {}

    def _detect_param_type(self, param: inspect.Parameter) -> str:
        """Detect parameter type from annotation."""
        if param.annotation == inspect.Parameter.empty:
            return "string"
        
        type_str = str(param.annotation)
        if "int" in type_str:
            return "integer"
        elif "float" in type_str:
            return "number"
        elif "bool" in type_str:
            return "boolean"
        elif "list" in type_str or "List" in type_str:
            return "array"
        return "string"

    def _create_tool_parameter(self, param_name: str, param: inspect.Parameter) -> ToolParameter:
        """Create a ToolParameter from a function parameter."""
        return ToolParameter(
            name=param_name,
            type=self._detect_param_type(param),
            description=f"Parameter {param_name}",
            required=param.default == inspect.Parameter.empty,
            default=param.default if param.default != inspect.Parameter.empty else None,
        )

    def _auto_detect_parameters(self, function: Callable) -> List[ToolParameter]:
        """Auto-detect parameters from function signature."""
        sig = inspect.signature(function)
        return [
            self._create_tool_parameter(param_name, param)
            for param_name, param in sig.parameters.items()
        ]

    def register_tool(self, tool: Tool, auto_register_function: bool = True) -> None:
        """
        Register a tool.

        Args:
            tool: Tool to register
            auto_register_function: If True, auto-detect parameters from function
        """
        if auto_register_function and tool.function:
            tool.parameters = self._auto_detect_parameters(tool.function)

        self._tools[tool.tool_id] = tool

    def register_function(
        self, name: str, function: Callable, description: str, tool_id: Optional[str] = None
    ) -> Tool:
        """
        Register a function as a tool.

        Args:
            name: Tool name
            function: Function to register
            description: Tool description
            tool_id: Optional tool ID

        Returns:
            Created tool
        """
        import uuid

        tool = Tool(
            tool_id=tool_id or str(uuid.uuid4()),
            name=name,
            description=description,
            tool_type=ToolType.FUNCTION,
            function=function,
        )

        self.register_tool(tool, auto_register_function=True)
        return tool

    def get_tool(self, tool_id: str) -> Optional[Tool]:
        """
        Get a tool by ID.

        Args:
            tool_id: Tool identifier

        Returns:
            Tool or None
        """
        return self._tools.get(tool_id)

    def get_tool_by_name(self, name: str) -> Optional[Tool]:
        """
        Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool or None
        """
        for tool in self._tools.values():
            if tool.name == name:
                return tool
        return None

    def list_tools(self, tags: Optional[List[str]] = None) -> List[Tool]:
        """
        List all tools.

        Args:
            tags: Optional tag filter

        Returns:
            List of tools
        """
        tools = list(self._tools.values())

        if tags:
            tools = [tool for tool in tools if any(tag in tool.tags for tag in tags)]

        return tools

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """
        Get schemas for all tools (for LLM function calling).

        Returns:
            List of tool schemas
        """
        return [tool.get_schema() for tool in self._tools.values()]


class ToolExecutor:
    """Executor for agent tool calls."""

    def __init__(self, registry: ToolRegistry):
        """
        Initialize tool executor.

        Args:
            registry: Tool registry
        """
        self.registry = registry

    def execute_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a tool call.

        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        tool = self.registry.get_tool_by_name(tool_name)

        if tool is None:
            raise ToolNotFoundError(tool_name)

        return tool.execute(**arguments)
