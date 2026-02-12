"""
Unit Tests for Agent Framework Exceptions

Tests exception classes for the agent framework.
"""


from src.core.agno_agent_framework.exceptions import (
    AgentConfigurationError,
    AgentError,
    AgentExecutionError,
    AgentNotFoundError,
    AgentStateError,
    MemoryError,
    MemoryPersistenceError,
    MemoryReadError,
    MemoryWriteError,
    OrchestrationError,
    ToolError,
    ToolInvocationError,
    ToolNotFoundError,
    ToolNotImplementedError,
    ToolValidationError,
    WorkflowNotFoundError,
)


class TestAgentError:
    """Test AgentError base class."""

    def test_agent_error_basic(self):
        """Test AgentError basic initialization."""
        error = AgentError("Test error")

        assert error.message == "Test error"
        assert str(error) == "Test error"

    def test_agent_error_with_original_error(self):
        """Test AgentError with original error."""
        original = ValueError("Original error")
        error = AgentError("Test error", original_error=original)

        assert error.message == "Test error"
        assert error.original_error == original


class TestAgentExecutionError:
    """Test AgentExecutionError class."""

    def test_agent_execution_error_basic(self):
        """Test AgentExecutionError basic initialization."""
        error = AgentExecutionError("Execution failed")

        assert error.message == "Execution failed"
        assert error.agent_id is None
        assert error.task_type is None
        assert error.execution_stage is None

    def test_agent_execution_error_with_all_params(self):
        """Test AgentExecutionError with all parameters."""
        original = RuntimeError("Original error")
        error = AgentExecutionError(
            "Execution failed",
            agent_id="agent1",
            task_type="test_task",
            execution_stage="execution",
            original_error=original,
        )

        assert error.message == "Execution failed"
        assert error.agent_id == "agent1"
        assert error.task_type == "test_task"
        assert error.execution_stage == "execution"
        assert error.original_error == original


class TestAgentConfigurationError:
    """Test AgentConfigurationError class."""

    def test_agent_configuration_error_basic(self):
        """Test AgentConfigurationError basic initialization."""
        error = AgentConfigurationError("Configuration invalid")

        assert error.message == "Configuration invalid"
        assert error.agent_id is None
        assert error.config_key is None

    def test_agent_configuration_error_with_all_params(self):
        """Test AgentConfigurationError with all parameters."""
        original = ValueError("Original error")
        error = AgentConfigurationError(
            "Configuration invalid",
            agent_id="agent1",
            config_key="max_tasks",
            original_error=original,
        )

        assert error.message == "Configuration invalid"
        assert error.agent_id == "agent1"
        assert error.config_key == "max_tasks"
        assert error.original_error == original


class TestAgentStateError:
    """Test AgentStateError class."""

    def test_agent_state_error_basic(self):
        """Test AgentStateError basic initialization."""
        error = AgentStateError("State operation failed")

        assert error.message == "State operation failed"
        assert error.agent_id is None
        assert error.operation is None
        assert error.file_path is None

    def test_agent_state_error_with_all_params(self):
        """Test AgentStateError with all parameters to cover lines 111-114."""
        original = IOError("Original error")
        error = AgentStateError(
            "State operation failed",
            agent_id="agent1",
            operation="save",
            file_path="/path/to/state.json",
            original_error=original,
        )

        assert error.message == "State operation failed"
        assert error.agent_id == "agent1"
        assert error.operation == "save"
        assert error.file_path == "/path/to/state.json"
        assert error.original_error == original


class TestToolError:
    """Test ToolError base class."""

    def test_tool_error_basic(self):
        """Test ToolError basic initialization."""
        error = ToolError("Tool error")

        assert error.message == "Tool error"

    def test_tool_error_with_original_error(self):
        """Test ToolError with original error."""
        original = ValueError("Original error")
        error = ToolError("Tool error", original_error=original)

        assert error.original_error == original


class TestToolInvocationError:
    """Test ToolInvocationError class."""

    def test_tool_invocation_error_basic(self):
        """Test ToolInvocationError basic initialization."""
        error = ToolInvocationError("Tool invocation failed")

        assert error.message == "Tool invocation failed"
        assert error.tool_name is None
        assert error.arguments is None
        assert error.error_type is None

    def test_tool_invocation_error_with_all_params(self):
        """Test ToolInvocationError with all parameters."""
        original = RuntimeError("Original error")
        error = ToolInvocationError(
            "Tool invocation failed",
            tool_name="test_tool",
            arguments={"param": "value"},
            error_type="runtime",
            original_error=original,
        )

        assert error.message == "Tool invocation failed"
        assert error.tool_name == "test_tool"
        assert error.arguments == {"param": "value"}
        assert error.error_type == "runtime"
        assert error.original_error == original


class TestToolNotFoundError:
    """Test ToolNotFoundError class."""

    def test_tool_not_found_error_basic(self):
        """Test ToolNotFoundError basic initialization to cover lines 173-175."""
        error = ToolNotFoundError("nonexistent_tool")

        assert error.message == "Tool 'nonexistent_tool' not found"
        assert error.tool_name == "nonexistent_tool"
        assert error.original_error is None

    def test_tool_not_found_error_with_original_error(self):
        """Test ToolNotFoundError with original error."""
        original = KeyError("Original error")
        error = ToolNotFoundError("nonexistent_tool", original_error=original)

        assert error.tool_name == "nonexistent_tool"
        assert error.original_error == original


class TestToolNotImplementedError:
    """Test ToolNotImplementedError class."""

    def test_tool_not_implemented_error_basic(self):
        """Test ToolNotImplementedError basic initialization to cover lines 194-196."""
        error = ToolNotImplementedError("unimplemented_tool")

        assert error.message == "Tool 'unimplemented_tool' is not implemented"
        assert error.tool_name == "unimplemented_tool"
        assert error.original_error is None

    def test_tool_not_implemented_error_with_original_error(self):
        """Test ToolNotImplementedError with original error."""
        original = NotImplementedError("Original error")
        error = ToolNotImplementedError("unimplemented_tool", original_error=original)

        assert error.tool_name == "unimplemented_tool"
        assert error.original_error == original


class TestToolValidationError:
    """Test ToolValidationError class."""

    def test_tool_validation_error_basic(self):
        """Test ToolValidationError basic initialization."""
        error = ToolValidationError("Validation failed")

        assert error.message == "Validation failed"
        assert error.tool_name is None
        assert error.missing_parameters == []

    def test_tool_validation_error_with_all_params(self):
        """Test ToolValidationError with all parameters to cover lines 224-226."""
        original = ValueError("Original error")
        error = ToolValidationError(
            "Validation failed",
            tool_name="test_tool",
            missing_parameters=["param1", "param2"],
            original_error=original,
        )

        assert error.message == "Validation failed"
        assert error.tool_name == "test_tool"
        assert error.missing_parameters == ["param1", "param2"]
        assert error.original_error == original


class TestMemoryError:
    """Test MemoryError base class."""

    def test_memory_error_basic(self):
        """Test MemoryError basic initialization."""
        error = MemoryError("Memory error")

        assert error.message == "Memory error"

    def test_memory_error_with_original_error(self):
        """Test MemoryError with original error."""
        original = IOError("Original error")
        error = MemoryError("Memory error", original_error=original)

        assert error.original_error == original


class TestMemoryReadError:
    """Test MemoryReadError class."""

    def test_memory_read_error_basic(self):
        """Test MemoryReadError basic initialization."""
        error = MemoryReadError("Read failed")

        assert error.message == "Read failed"
        assert error.agent_id is None
        assert error.memory_id is None
        assert error.operation is None

    def test_memory_read_error_with_all_params(self):
        """Test MemoryReadError with all parameters to cover lines 263-266."""
        original = IOError("Original error")
        error = MemoryReadError(
            "Read failed",
            agent_id="agent1",
            memory_id="mem1",
            operation="retrieve",
            original_error=original,
        )

        assert error.message == "Read failed"
        assert error.agent_id == "agent1"
        assert error.memory_id == "mem1"
        assert error.operation == "retrieve"
        assert error.original_error == original


class TestMemoryWriteError:
    """Test MemoryWriteError class."""

    def test_memory_write_error_basic(self):
        """Test MemoryWriteError basic initialization."""
        error = MemoryWriteError("Write failed")

        assert error.message == "Write failed"
        assert error.agent_id is None
        assert error.memory_id is None
        assert error.memory_type is None
        assert error.operation is None

    def test_memory_write_error_with_all_params(self):
        """Test MemoryWriteError with all parameters."""
        original = IOError("Original error")
        error = MemoryWriteError(
            "Write failed",
            agent_id="agent1",
            memory_id="mem1",
            memory_type="short_term",
            operation="store",
            original_error=original,
        )

        assert error.message == "Write failed"
        assert error.agent_id == "agent1"
        assert error.memory_id == "mem1"
        assert error.memory_type == "short_term"
        assert error.operation == "store"
        assert error.original_error == original


class TestMemoryPersistenceError:
    """Test MemoryPersistenceError class."""

    def test_memory_persistence_error_basic(self):
        """Test MemoryPersistenceError basic initialization."""
        error = MemoryPersistenceError("Persistence failed")

        assert error.message == "Persistence failed"
        assert error.agent_id is None
        assert error.file_path is None
        assert error.operation is None

    def test_memory_persistence_error_with_all_params(self):
        """Test MemoryPersistenceError with all parameters."""
        original = IOError("Original error")
        error = MemoryPersistenceError(
            "Persistence failed",
            agent_id="agent1",
            file_path="/path/to/memory.json",
            operation="save",
            original_error=original,
        )

        assert error.message == "Persistence failed"
        assert error.agent_id == "agent1"
        assert error.file_path == "/path/to/memory.json"
        assert error.operation == "save"
        assert error.original_error == original


class TestOrchestrationError:
    """Test OrchestrationError class."""

    def test_orchestration_error_basic(self):
        """Test OrchestrationError basic initialization."""
        error = OrchestrationError("Orchestration failed")

        assert error.message == "Orchestration failed"
        assert error.workflow_id is None
        assert error.agent_id is None
        assert error.operation is None

    def test_orchestration_error_with_all_params(self):
        """Test OrchestrationError with all parameters."""
        original = RuntimeError("Original error")
        error = OrchestrationError(
            "Orchestration failed",
            workflow_id="workflow1",
            agent_id="agent1",
            operation="execute",
            original_error=original,
        )

        assert error.message == "Orchestration failed"
        assert error.workflow_id == "workflow1"
        assert error.agent_id == "agent1"
        assert error.operation == "execute"
        assert error.original_error == original


class TestWorkflowNotFoundError:
    """Test WorkflowNotFoundError class."""

    def test_workflow_not_found_error_basic(self):
        """Test WorkflowNotFoundError basic initialization."""
        error = WorkflowNotFoundError("workflow1")

        assert error.message == "Workflow 'workflow1' not found"
        assert error.workflow_id == "workflow1"
        assert error.original_error is None

    def test_workflow_not_found_error_with_original_error(self):
        """Test WorkflowNotFoundError with original error."""
        original = KeyError("Original error")
        error = WorkflowNotFoundError("workflow1", original_error=original)

        assert error.workflow_id == "workflow1"
        assert error.original_error == original


class TestAgentNotFoundError:
    """Test AgentNotFoundError class."""

    def test_agent_not_found_error_basic(self):
        """Test AgentNotFoundError basic initialization."""
        error = AgentNotFoundError("agent1")

        assert error.message == "Agent 'agent1' not found"
        assert error.agent_id == "agent1"
        assert error.original_error is None

    def test_agent_not_found_error_with_original_error(self):
        """Test AgentNotFoundError with original error."""
        original = KeyError("Original error")
        error = AgentNotFoundError("agent1", original_error=original)

        assert error.agent_id == "agent1"
        assert error.original_error == original

