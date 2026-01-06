"""
Agno Agent Framework Integration

Interface for agent framework integration with LiteLLM Gateway.
Designed to be swappable with other agent frameworks (e.g., LangChain).
"""

from .agent import (
    Agent,
    AgentManager,
    AgentStatus,
    AgentCapability,
    AgentMessage,
    AgentTask
)
from .session import (
    AgentSession,
    SessionManager,
    SessionStatus,
    SessionMessage
)
from .memory import (
    AgentMemory,
    MemoryItem,
    MemoryType
)
from .tools import (
    Tool,
    ToolRegistry,
    ToolExecutor,
    ToolType,
    ToolParameter
)
from .plugins import (
    AgentPlugin,
    PluginManager,
    PluginStatus,
    PluginHook
)
from .orchestration import (
    WorkflowPipeline,
    WorkflowStep,
    WorkflowState,
    WorkflowStatus,
    CoordinationPattern,
    AgentOrchestrator
)
from .functions import (
    create_agent,
    create_agent_with_memory,
    create_agent_manager,
    create_orchestrator,
    execute_task,
    chat_with_agent,
    delegate_task,
    find_agents_by_capability,
    batch_process_agents,
    retry_on_failure,
)

__all__ = [
    # Core classes
    "Agent",
    "AgentManager",
    "AgentStatus",
    "AgentCapability",
    "AgentMessage",
    "AgentTask",
    "AgentSession",
    "SessionManager",
    "SessionStatus",
    "SessionMessage",
    "AgentMemory",
    "MemoryItem",
    "MemoryType",
    "Tool",
    "ToolRegistry",
    "ToolExecutor",
    "ToolType",
    "ToolParameter",
    "AgentPlugin",
    "PluginManager",
    "PluginStatus",
    "PluginHook",
    "WorkflowPipeline",
    "WorkflowStep",
    "WorkflowState",
    "WorkflowStatus",
    "CoordinationPattern",
    "AgentOrchestrator",
    # Factory functions
    "create_agent",
    "create_agent_with_memory",
    "create_agent_manager",
    "create_orchestrator",
    # High-level convenience functions
    "execute_task",
    "chat_with_agent",
    "delegate_task",
    "find_agents_by_capability",
    # Utility functions
    "batch_process_agents",
    "retry_on_failure",
]
