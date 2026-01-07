"""
Agent Framework Exception Hierarchy

Exceptions specific to the Agent Framework, including agents, tools, memory, and orchestration.
"""

from typing import Optional, Dict, Any
from ..exceptions import SDKError


class AgentError(SDKError):
    """Base exception for agent-related errors."""
    pass


class AgentExecutionError(AgentError):
    """
    Raised when an agent fails at any point during planning, execution, or completion.
    
    Attributes:
        agent_id: ID of the agent that failed
        task_type: Type of task that was being executed
        execution_stage: Stage where execution failed (planning, execution, completion)
    """
    
    def __init__(
        self,
        message: str,
        agent_id: Optional[str] = None,
        task_type: Optional[str] = None,
        execution_stage: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message, original_error)
        self.agent_id = agent_id
        self.task_type = task_type
        self.execution_stage = execution_stage


class AgentConfigurationError(AgentError):
    """
    Raised when agent configuration is invalid.
    
    Attributes:
        agent_id: ID of the agent with invalid configuration
        config_key: Configuration key that is invalid
    """
    
    def __init__(
        self,
        message: str,
        agent_id: Optional[str] = None,
        config_key: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message, original_error)
        self.agent_id = agent_id
        self.config_key = config_key


class AgentStateError(AgentError):
    """
    Raised when agent state operations fail (save/load).
    
    Attributes:
        agent_id: ID of the agent
        operation: Operation that failed (save, load)
        file_path: Path to state file (if applicable)
    """
    
    def __init__(
        self,
        message: str,
        agent_id: Optional[str] = None,
        operation: Optional[str] = None,
        file_path: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message, original_error)
        self.agent_id = agent_id
        self.operation = operation
        self.file_path = file_path


class ToolError(SDKError):
    """Base exception for tool-related errors."""
    pass


class ToolInvocationError(ToolError):
    """
    Raised when a tool fails due to invalid input, runtime error, timeout, or bad output.
    
    Attributes:
        tool_name: Name of the tool that failed
        arguments: Arguments passed to the tool
        error_type: Type of error (validation, runtime, timeout, output)
    """
    
    def __init__(
        self,
        message: str,
        tool_name: Optional[str] = None,
        arguments: Optional[Dict[str, Any]] = None,
        error_type: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message, original_error)
        self.tool_name = tool_name
        self.arguments = arguments
        self.error_type = error_type


class ToolNotFoundError(ToolError):
    """
    Raised when a requested tool is not found in the registry.
    
    Attributes:
        tool_name: Name of the tool that was not found
    """
    
    def __init__(
        self,
        tool_name: str,
        original_error: Optional[Exception] = None
    ):
        message = f"Tool '{tool_name}' not found"
        super().__init__(message, original_error)
        self.tool_name = tool_name


class ToolNotImplementedError(ToolError):
    """
    Raised when a tool has no function implementation.
    
    Attributes:
        tool_name: Name of the tool that is not implemented
    """
    
    def __init__(
        self,
        tool_name: str,
        original_error: Optional[Exception] = None
    ):
        message = f"Tool '{tool_name}' is not implemented"
        super().__init__(message, original_error)
        self.tool_name = tool_name


class ToolValidationError(ToolError):
    """
    Raised when tool parameter validation fails.
    
    Attributes:
        tool_name: Name of the tool
        missing_parameters: List of missing required parameters
    """
    
    def __init__(
        self,
        message: str,
        tool_name: Optional[str] = None,
        missing_parameters: Optional[list] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message, original_error)
        self.tool_name = tool_name
        self.missing_parameters = missing_parameters or []


class MemoryError(SDKError):
    """Base exception for memory-related errors."""
    pass


class MemoryReadError(MemoryError):
    """
    Raised when reading from memory/storage fails.
    
    Attributes:
        agent_id: ID of the agent whose memory failed
        memory_id: ID of the memory item (if applicable)
        operation: Operation that failed
    """
    
    def __init__(
        self,
        message: str,
        agent_id: Optional[str] = None,
        memory_id: Optional[str] = None,
        operation: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message, original_error)
        self.agent_id = agent_id
        self.memory_id = memory_id
        self.operation = operation


class MemoryWriteError(MemoryError):
    """
    Raised when writing or persisting memory fails.
    
    Attributes:
        agent_id: ID of the agent whose memory failed
        memory_id: ID of the memory item (if applicable)
        memory_type: Type of memory (short_term, long_term, etc.)
        operation: Operation that failed (store, persist, etc.)
    """
    
    def __init__(
        self,
        message: str,
        agent_id: Optional[str] = None,
        memory_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        operation: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message, original_error)
        self.agent_id = agent_id
        self.memory_id = memory_id
        self.memory_type = memory_type
        self.operation = operation


class MemoryPersistenceError(MemoryError):
    """
    Raised when memory persistence operations fail.
    
    Attributes:
        agent_id: ID of the agent
        file_path: Path to persistence file
        operation: Operation that failed (save, load)
    """
    
    def __init__(
        self,
        message: str,
        agent_id: Optional[str] = None,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message, original_error)
        self.agent_id = agent_id
        self.file_path = file_path
        self.operation = operation


class OrchestrationError(SDKError):
    """
    Raised when agent execution coordination or scheduling fails.
    
    Attributes:
        workflow_id: ID of the workflow (if applicable)
        agent_id: ID of the agent (if applicable)
        operation: Operation that failed
    """
    
    def __init__(
        self,
        message: str,
        workflow_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        operation: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message, original_error)
        self.workflow_id = workflow_id
        self.agent_id = agent_id
        self.operation = operation


class WorkflowNotFoundError(OrchestrationError):
    """
    Raised when a requested workflow is not found.
    
    Attributes:
        workflow_id: ID of the workflow that was not found
    """
    
    def __init__(
        self,
        workflow_id: str,
        original_error: Optional[Exception] = None
    ):
        message = f"Workflow '{workflow_id}' not found"
        super().__init__(message, workflow_id=workflow_id, original_error=original_error)
        self.workflow_id = workflow_id


class AgentNotFoundError(OrchestrationError):
    """
    Raised when a requested agent is not found in the orchestrator.
    
    Attributes:
        agent_id: ID of the agent that was not found
    """
    
    def __init__(
        self,
        agent_id: str,
        original_error: Optional[Exception] = None
    ):
        message = f"Agent '{agent_id}' not found"
        super().__init__(message, agent_id=agent_id, original_error=original_error)
        self.agent_id = agent_id


