"""
Agno Agent Framework Integration

Interface for agent framework integration with LiteLLM Gateway.
Designed to be swappable with other agent frameworks (e.g., LangChain).
"""

from .agent import Agent, AgentCapability, AgentManager, AgentMessage, AgentStatus, AgentTask
from .functions import (
    batch_process_agents,
    chat_with_agent,
    create_agent,
    create_agent_manager,
    create_agent_with_memory,
    create_agent_with_prompt_management,
    create_agent_with_tools,
    create_orchestrator,
    delegate_task,
    execute_task,
    find_agents_by_capability,
    load_agent_state,
    retry_on_failure,
    save_agent_state,
)
from .memory import AgentMemory, MemoryItem, MemoryType
from .orchestration import (
    AgentOrchestrator,
    CoordinationPattern,
    WorkflowPipeline,
    WorkflowState,
    WorkflowStatus,
    WorkflowStep,
)
from .plugins import AgentPlugin, PluginHook, PluginManager, PluginStatus
from .session import AgentSession, SessionManager, SessionMessage, SessionStatus
from .tools import Tool, ToolExecutor, ToolParameter, ToolRegistry, ToolType

# Import Prompt-Based Generator functions (optional)
try:
    from ..prompt_based_generator import (
        create_agent_from_prompt,
        create_tool_from_prompt,
        rate_agent,
        rate_tool,
    )
except ImportError:
    create_agent_from_prompt = None
    create_tool_from_prompt = None
    rate_agent = None
    rate_tool = None

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
    "create_agent_with_prompt_management",
    "create_agent_with_tools",
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
    "save_agent_state",
    "load_agent_state",
    # Prompt-based creation functions (optional)
    "create_agent_from_prompt",
    "create_tool_from_prompt",
    "rate_agent",
    "rate_tool",
]
