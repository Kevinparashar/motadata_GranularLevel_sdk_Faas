"""
Agno Agent Framework Integration

✅ USES REAL AGNO AGENT FRAMEWORK from https://www.agno.com/
This module provides compatibility wrappers to maintain existing API while using real Agno.

The real Agno framework is imported from the 'agno' package (pip install agno>=2.5.3).
All Agent instances are created using the real AgnoAgent from agno.com.
"""

# Import real Agno framework (REQUIRED - this is the real framework from agno.com)
# Note: Import errors are expected until 'pip install agno>=2.5.3' is run
try:
    from agno import AgentOS, Team, Workflow, Knowledge 
    from agno.agent import Agent as RealAgnoAgent  
    import logging
    logging.getLogger(__name__).info("✅ Real Agno Agent Framework loaded from agno.com")
except ImportError as e:
    # Set to None when agno is not installed (expected until pip install)
    AgentOS = None
    Team = None
    Workflow = None
    Knowledge = None
    RealAgnoAgent = None
    import logging
    logging.getLogger(__name__).error(
        f"❌ Real Agno framework not installed. Install with: pip install agno>=2.5.3\n"
        f"   Error: {e}"
    )

# Import compatibility wrappers (uses real Agno underneath)
from .compatibility import (
    Agent,
    AgentCapability,
    AgentManager,
    AgentMessage,
    AgentStatus,
    AgentTask,
    AgentOS,
    Team,
    Workflow,
    Knowledge,
    RealAgnoAgent,
)
# Import functions (will use compatibility layer)
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

# Import memory, orchestration, etc. (may need migration later)
try:
    from .memory import AgentMemory, MemoryItem, MemoryType
except ImportError:
    AgentMemory = None
    MemoryItem = None
    MemoryType = None

try:
    from .orchestration import (
        AgentOrchestrator,
        CoordinationPattern,
        WorkflowPipeline,
        WorkflowState,
        WorkflowStatus,
        WorkflowStep,
    )
except ImportError:
    AgentOrchestrator = None
    CoordinationPattern = None
    WorkflowPipeline = None
    WorkflowState = None
    WorkflowStatus = None
    WorkflowStep = None

try:
    from .plugins import AgentPlugin, PluginHook, PluginManager, PluginStatus
except ImportError:
    AgentPlugin = None
    PluginHook = None
    PluginManager = None
    PluginStatus = None

try:
    from .session import AgentSession, SessionManager, SessionMessage, SessionStatus
except ImportError:
    AgentSession = None
    SessionManager = None
    SessionMessage = None
    SessionStatus = None

try:
    from .tools import Tool, ToolExecutor, ToolParameter, ToolRegistry, ToolType
except ImportError:
    Tool = None
    ToolExecutor = None
    ToolParameter = None
    ToolRegistry = None
    ToolType = None

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
    # Core classes (from compatibility layer - uses real Agno)
    "Agent",
    "AgentManager",
    "AgentStatus",
    "AgentCapability",
    "AgentMessage",
    "AgentTask",
    # Real Agno classes (direct access)
    "AgentOS",
    "Team",
    "Workflow",
    "Knowledge",
    "RealAgnoAgent",
    # Legacy classes (may need migration)
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
