"""
Agent Tools

Tools that agents can use to extend their capabilities.
"""

from typing import Dict, List, Optional, Any, Callable
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
from enum import Enum
import inspect


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
            ValueError: If required parameters are missing
            RuntimeError: If tool execution fails
        """
        if self.function is None:
            raise RuntimeError(f"Tool {self.name} has no function implementation")
        
        # Validate parameters
        self._validate_parameters(kwargs)
        
        # Execute function
        try:
            return self.function(**kwargs)
        except Exception as e:
            raise RuntimeError(f"Tool {self.name} execution failed: {e}")
    
    def _validate_parameters(self, provided: Dict[str, Any]) -> None:
        """
        Validate provided parameters.
        
        Args:
            provided: Provided parameters
        
        Raises:
            ValueError: If validation fails
        """
        for param in self.parameters:
            if param.required and param.name not in provided:
                raise ValueError(f"Required parameter '{param.name}' not provided")
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get tool schema for LLM function calling.
        
        Returns:
            Tool schema dictionary
        """
        properties = {}
        required = []
        
        for param in self.parameters:
            properties[param.name] = {
                "type": param.type,
                "description": param.description
            }
            if param.default is not None:
                properties[param.name]["default"] = param.default
            if param.required:
                required.append(param.name)
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }


class ToolRegistry:
    """Registry for managing agent tools."""
    
    def __init__(self):
        """Initialize tool registry."""
        self._tools: Dict[str, Tool] = {}
    
    def register_tool(
        self,
        tool: Tool,
        auto_register_function: bool = True
    ) -> None:
        """
        Register a tool.
        
        Args:
            tool: Tool to register
            auto_register_function: If True, auto-detect parameters from function
        """
        if auto_register_function and tool.function:
            # Auto-detect parameters from function signature
            sig = inspect.signature(tool.function)
            parameters = []
            
            for param_name, param in sig.parameters.items():
                param_type = "string"
                if param.annotation != inspect.Parameter.empty:
                    type_str = str(param.annotation)
                    if "int" in type_str:
                        param_type = "integer"
                    elif "float" in type_str:
                        param_type = "number"
                    elif "bool" in type_str:
                        param_type = "boolean"
                    elif "list" in type_str or "List" in type_str:
                        param_type = "array"
                
                parameters.append(ToolParameter(
                    name=param_name,
                    type=param_type,
                    description=f"Parameter {param_name}",
                    required=param.default == inspect.Parameter.empty,
                    default=param.default if param.default != inspect.Parameter.empty else None
                ))
            
            tool.parameters = parameters
        
        self._tools[tool.tool_id] = tool
    
    def register_function(
        self,
        name: str,
        function: Callable,
        description: str,
        tool_id: Optional[str] = None
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
            function=function
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
            tools = [
                tool for tool in tools
                if any(tag in tool.tags for tag in tags)
            ]
        
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
    
    def execute_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
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
            raise ValueError(f"Tool '{tool_name}' not found")
        
        return tool.execute(**arguments)

