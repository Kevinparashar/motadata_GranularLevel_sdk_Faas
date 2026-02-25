"""
Agent Tools

Tools that agents can use to extend their capabilities.
"""


import inspect
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from ...faas.shared.dal.tool_dal import ToolDAL
    from ...faas.shared.dal.tool_execution_dal import ToolExecutionDAL 

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

    async def execute(self, **kwargs: Any) -> Any:
        """
        Execute the tool asynchronously.
        
        Args:
            **kwargs (Any): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            ToolInvocationError: Raised when this function detects an invalid state or when an underlying call fails.
            ToolNotImplementedError: Raised when this function detects an invalid state or when an underlying call fails.
            ToolValidationError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        import asyncio
        
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
            ) from e

        # Execute function (async or sync)
        try:
            if asyncio.iscoroutinefunction(self.function):
                return await self.function(**kwargs)
            else:
                # Run sync function in executor to avoid blocking
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, lambda: self.function(**kwargs))
        except ToolInvocationError:
            raise
        except Exception as e:
            raise ToolInvocationError(
                message=f"Tool {self.name} execution failed: {str(e)}",
                tool_name=self.name,
                arguments=kwargs,
                error_type="runtime",
                original_error=e,
            ) from e

    def _validate_parameters(self, provided: Dict[str, Any]) -> None:
        """
        Validate provided parameters.
        
        Args:
            provided (Dict[str, Any]): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        
        Raises:
            ToolValidationError: Raised when this function detects an invalid state or when an underlying call fails.
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
            Dict[str, Any]: Dictionary result of the operation.
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
    """Registry for managing agent tools.
    
    Supports both in-memory storage (default) and database persistence via ToolDAL.
    """

    def __init__(self, tool_dal: Optional["ToolDAL"] = None, tenant_id: Optional[str] = None):
        """
        Initialize tool registry.
        
        Args:
            tool_dal: Optional ToolDAL instance for database persistence.
            tenant_id: Optional tenant ID for multi-tenant isolation.
        """
        self._tools: Dict[str, Tool] = {}
        self._tool_dal = tool_dal
        self._tenant_id = tenant_id

    def _detect_param_type(self, param: inspect.Parameter) -> str:
        """
        Detect parameter type from annotation.
        
        Args:
            param (inspect.Parameter): Input parameter for this operation.
        
        Returns:
            str: Returned text value.
        """
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
        """
        Create a ToolParameter from a function parameter.
        
        Args:
            param_name (str): Input parameter for this operation.
            param (inspect.Parameter): Input parameter for this operation.
        
        Returns:
            ToolParameter: Result of the operation.
        """
        return ToolParameter(
            name=param_name,
            type=self._detect_param_type(param),
            description=f"Parameter {param_name}",
            required=param.default == inspect.Parameter.empty,
            default=param.default if param.default != inspect.Parameter.empty else None,
        )

    def _auto_detect_parameters(self, function: Callable) -> List[ToolParameter]:
        """
        Auto-detect parameters from function signature.
        
        Args:
            function (Callable): Input parameter for this operation.
        
        Returns:
            List[ToolParameter]: List result of the operation.
        """
        sig = inspect.signature(function)
        return [
            self._create_tool_parameter(param_name, param)
            for param_name, param in sig.parameters.items()
        ]

    def register_tool(self, tool: Tool, auto_register_function: bool = True) -> None:
        """
        Register a tool.
        
        Args:
            tool (Tool): Input parameter for this operation.
            auto_register_function (bool): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        """
        if auto_register_function and tool.function:
            tool.parameters = self._auto_detect_parameters(tool.function)

        self._tools[tool.tool_id] = tool
        
        # Persist to database if DAL is available
        if self._tool_dal and self._tenant_id:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, create task
                    asyncio.create_task(
                        self._tool_dal.save_tool(
                            tool_id=tool.tool_id,
                            name=tool.name,
                            description=tool.description,
                            tool_type=tool.tool_type.value if hasattr(tool.tool_type, "value") else str(tool.tool_type),
                            parameters=[p.model_dump() if hasattr(p, "model_dump") else p.dict() if hasattr(p, "dict") else vars(p) for p in tool.parameters] if tool.parameters else [],
                            tenant_id=self._tenant_id,
                            metadata=tool.metadata,
                            tags=tool.tags,
                        )
                    )
                else:
                    loop.run_until_complete(
                        self._tool_dal.save_tool(
                            tool_id=tool.tool_id,
                            name=tool.name,
                            description=tool.description,
                            tool_type=tool.tool_type.value if hasattr(tool.tool_type, "value") else str(tool.tool_type),
                            parameters=[p.model_dump() if hasattr(p, "model_dump") else p.dict() if hasattr(p, "dict") else vars(p) for p in tool.parameters] if tool.parameters else [],
                            tenant_id=self._tenant_id,
                            metadata=tool.metadata,
                            tags=tool.tags,
                        )
                    )
            except RuntimeError:
                # No event loop, create new one
                asyncio.run(
                    self._tool_dal.save_tool(
                        tool_id=tool.tool_id,
                        name=tool.name,
                        description=tool.description,
                        tool_type=tool.tool_type.value if hasattr(tool.tool_type, "value") else str(tool.tool_type),
                        parameters=[p.model_dump() if hasattr(p, "model_dump") else p.dict() if hasattr(p, "dict") else vars(p) for p in tool.parameters] if tool.parameters else [],
                        tenant_id=self._tenant_id,
                        metadata=tool.metadata,
                        tags=tool.tags,
                    )
                )

    def register_function(
        self, name: str, function: Callable, description: str, tool_id: Optional[str] = None
    ) -> Tool:
        """
        Register a function as a tool.
        
        Args:
            name (str): Name value.
            function (Callable): Input parameter for this operation.
            description (str): Human-readable description text.
            tool_id (Optional[str]): Tool identifier.
        
        Returns:
            Tool: Result of the operation.
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
            tool_id (str): Tool identifier.
        
        Returns:
            Optional[Tool]: Result if available, else None.
        """
        # Try in-memory first
        tool = self._tools.get(tool_id)
        if tool:
            return tool
        
        # If not in memory and DAL is available, load from database
        if self._tool_dal and self._tenant_id:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, we can't use run_until_complete
                    # Return None and let caller handle async loading
                    return None
                else:
                    tool_data = loop.run_until_complete(
                        self._tool_dal.load_tool(tool_id, self._tenant_id)
                    )
                if tool_data:
                    # Reconstruct Tool from database data
                    # Note: function cannot be restored from database, must be provided separately
                    tool = Tool(
                        tool_id=tool_data["tool_id"],
                        name=tool_data["name"],
                        description=tool_data["description"],
                        tool_type=ToolType(tool_data["tool_type"]),
                        parameters=[ToolParameter(**p) for p in tool_data.get("parameters", [])],
                        metadata=tool_data.get("metadata", {}),
                        tags=tool_data.get("tags", []),
                        function=None,  # Function must be provided separately
                    )
                    # Cache in memory
                    self._tools[tool_id] = tool
                    return tool
            except RuntimeError:
                # No event loop, create new one
                tool_data = asyncio.run(
                    self._tool_dal.load_tool(tool_id, self._tenant_id)
                )
                if tool_data:
                    tool = Tool(
                        tool_id=tool_data["tool_id"],
                        name=tool_data["name"],
                        description=tool_data["description"],
                        tool_type=ToolType(tool_data["tool_type"]),
                        parameters=[ToolParameter(**p) for p in tool_data.get("parameters", [])],
                        metadata=tool_data.get("metadata", {}),
                        tags=tool_data.get("tags", []),
                        function=None,  # Function must be provided separately
                    )
                    # Cache in memory
                    self._tools[tool_id] = tool
                    return tool
        
        return None

    def get_tool_by_name(self, name: str) -> Optional[Tool]:
        """
        Get a tool by name.
        
        Args:
            name (str): Name value.
        
        Returns:
            Optional[Tool]: Result if available, else None.
        """
        for tool in self._tools.values():
            if tool.name == name:
                return tool
        return None

    def list_tools(self, tags: Optional[List[str]] = None) -> List[Tool]:
        """
        List all tools.
        
        Args:
            tags (Optional[List[str]]): Input parameter for this operation.
        
        Returns:
            List[Tool]: List result of the operation.
        """
        tools = list(self._tools.values())

        if tags:
            tools = [tool for tool in tools if any(tag in tool.tags for tag in tags)]

        return tools

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """
        Get schemas for all tools (for LLM function calling).
        
        Returns:
            List[Dict[str, Any]]: Dictionary result of the operation.
        """
        return [tool.get_schema() for tool in self._tools.values()]


class ToolExecutor:
    """Executor for agent tool calls.
    
    Supports execution history tracking via ToolExecutionDAL.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        execution_dal: Optional["ToolExecutionDAL"] = None,
        tenant_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ):
        """
        Initialize tool executor.
        
        Args:
            registry: Tool registry instance.
            execution_dal: Optional ToolExecutionDAL instance for execution history.
            tenant_id: Optional tenant ID for multi-tenant isolation.
            agent_id: Optional agent ID that owns this executor.
        """
        self.registry = registry
        self._execution_dal = execution_dal
        self._tenant_id = tenant_id
        self._agent_id = agent_id

    async def execute_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a tool call asynchronously.
        
        Args:
            tool_name (str): Input parameter for this operation.
            arguments (Dict[str, Any]): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            ToolNotFoundError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        import time
        
        tool = self.registry.get_tool_by_name(tool_name)

        if tool is None:
            raise ToolNotFoundError(tool_name)

        # Track execution start time
        start_time = time.time()
        status = "success"
        error = None
        result = None

        try:
            result = await tool.execute(**arguments)
        except Exception as e:
            status = "error"
            error = str(e)
            raise
        finally:
            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Save execution history if DAL is available
            if self._execution_dal and self._tenant_id:
                try:
                    await self._execution_dal.save_execution(
                        tool_id=tool.tool_id,
                        agent_id=self._agent_id,
                        arguments=arguments,
                        result=result,
                        status=status,
                        error=error,
                        tenant_id=self._tenant_id,
                        execution_time_ms=execution_time_ms,
                    )
                except Exception as e:
                    # Log but don't fail execution if history save fails
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Failed to save tool execution history: {e}", exc_info=True)

        return result
