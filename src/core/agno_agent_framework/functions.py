"""
Agno Agent Framework - High-Level Functions

Factory functions, convenience functions, and utilities for agent framework.
"""

from typing import Any, Dict, List, Optional, TypeVar, Callable, cast
from .agent import Agent, AgentManager, AgentTask, AgentStatus
from .memory import AgentMemory, MemoryType
from .session import AgentSession, SessionManager
from .tools import Tool, ToolRegistry, ToolExecutor
from .plugins import PluginManager
from .orchestration import AgentOrchestrator, WorkflowPipeline
from ..utils.type_helpers import GatewayProtocol, ConfigDict, MetadataDict

# Import Prompt Context Management
try:
    from ..prompt_context_management import create_prompt_manager
except ImportError:
    create_prompt_manager = None

# Import Prompt-Based Generator (optional)
try:
    from ..prompt_based_generator import create_agent_from_prompt, create_tool_from_prompt
except ImportError:
    create_agent_from_prompt = None
    create_tool_from_prompt = None


# ============================================================================
# Factory Functions
# ============================================================================

def create_agent(
    agent_id: str,
    name: str,
    gateway: GatewayProtocol,
    tenant_id: Optional[str] = None,
    description: str = "",
    llm_model: Optional[str] = None,
    llm_provider: Optional[str] = None,
    **kwargs: Any
) -> Agent:
    """
    Create and configure an agent with default settings.

    Args:
        agent_id: Unique agent identifier
        name: Agent name
        gateway: LiteLLM Gateway instance
        tenant_id: Optional tenant ID for multi-tenant SaaS
        description: Agent description
        llm_model: Optional LLM model name
        llm_provider: Optional LLM provider
        **kwargs: Additional agent configuration

    Returns:
        Configured Agent instance

    Example:
        >>> gateway = LiteLLMGateway()
        >>> agent = create_agent("agent1", "Assistant", gateway, tenant_id="tenant_123")
    """
    return Agent(
        agent_id=agent_id,
        tenant_id=tenant_id,
        name=name,
        description=description,
        gateway=gateway,
        llm_model=llm_model,
        llm_provider=llm_provider,
        **kwargs
    )


def create_agent_with_memory(
    agent_id: str,
    name: str,
    gateway: GatewayProtocol,
    tenant_id: Optional[str] = None,
    memory_config: Optional[ConfigDict] = None,
    **kwargs: Any
) -> Agent:
    """
    Create an agent with memory pre-configured.

    Args:
        agent_id: Unique agent identifier
        name: Agent name
        gateway: LiteLLM Gateway instance
        memory_config: Memory configuration dict with keys:
            - persistence_path: Optional path for memory persistence
            - max_short_term: Max short-term memories (default: 50)
            - max_long_term: Max long-term memories (default: 1000)
        **kwargs: Additional agent configuration

    Returns:
        Agent instance with memory attached

    Example:
        >>> agent = create_agent_with_memory(
        ...     "agent1", "Assistant", gateway,
        ...     memory_config={"persistence_path": "/tmp/memory.json"}
        ... )
    """
    agent = create_agent(agent_id, name, gateway, **kwargs)

    if memory_config:
        persistence_path = memory_config.get("persistence_path")
        max_short_term = memory_config.get("max_short_term", 50)
        max_long_term = memory_config.get("max_long_term", 1000)

        agent.attach_memory(persistence_path)
        if agent.memory:
            agent.memory.max_short_term = max_short_term
            agent.memory.max_long_term = max_long_term
            # Set episodic and semantic limits for ITSM
            agent.memory.max_episodic = memory_config.get("max_episodic", 500)
            agent.memory.max_semantic = memory_config.get("max_semantic", 2000)

    return agent


def create_agent_with_prompt_management(
    agent_id: str,
    name: str,
    gateway: Any,
    tenant_id: Optional[str] = None,
    system_prompt: Optional[str] = None,
    role_template: Optional[str] = None,
    max_context_tokens: int = 4000,
    prompt_config: Optional[Dict[str, Any]] = None,
    **kwargs: Any
) -> Agent:
    """
    Create an agent with prompt context management pre-configured.

    Args:
        agent_id: Unique agent identifier
        name: Agent name
        gateway: LiteLLM Gateway instance
        system_prompt: Optional system prompt for the agent
        role_template: Optional role-based template name
        max_context_tokens: Maximum tokens for context window (default: 4000)
        prompt_config: Optional prompt configuration dict with keys:
            - max_tokens: Max tokens (overrides max_context_tokens)
            - safety_margin: Safety margin for token estimation
            - templates: List of template dicts with name, version, content, metadata
        **kwargs: Additional agent configuration

    Returns:
        Agent instance with prompt management attached

    Example:
        >>> agent = create_agent_with_prompt_management(
        ...     "agent1", "Assistant", gateway,
        ...     system_prompt="You are a helpful AI assistant.",
        ...     role_template="assistant_role",
        ...     max_context_tokens=8000
        ... )
    """
    agent = create_agent(agent_id, name, gateway, tenant_id=tenant_id, **kwargs)

    if create_prompt_manager:
        prompt_max_tokens = max_context_tokens
        safety_margin = 200

        if prompt_config:
            prompt_max_tokens = prompt_config.get("max_tokens", max_context_tokens)
            safety_margin = prompt_config.get("safety_margin", 200)

        agent.attach_prompt_manager(
            max_tokens=prompt_max_tokens,
            system_prompt=system_prompt,
            role_template=role_template
        )

        # Add templates if provided
        if prompt_config and "templates" in prompt_config:
            for template in prompt_config["templates"]:
                agent.add_prompt_template(
                    name=template["name"],
                    version=template.get("version", "1.0"),
                    content=template["content"],
                    metadata=template.get("metadata")
                )
    else:
        # If prompt manager not available, set basic config
        agent.system_prompt = system_prompt
        agent.role_template = role_template
        agent.max_context_tokens = max_context_tokens
        agent.use_prompt_management = False

    return agent


def create_agent_with_tools(
    agent_id: str,
    name: str,
    gateway: GatewayProtocol,
    tenant_id: Optional[str] = None,
    tools: Optional[List[Tool]] = None,
    tool_registry: Optional[ToolRegistry] = None,
    enable_tool_calling: bool = True,
    max_tool_iterations: int = 10,
    **kwargs: Any
) -> Agent:
    """
    Create an agent with tools pre-configured.

    Args:
        agent_id: Unique agent identifier
        name: Agent name
        gateway: LiteLLM Gateway instance
        tools: Optional list of Tool instances to register
        tool_registry: Optional pre-configured ToolRegistry
        enable_tool_calling: Enable/disable tool calling (default: True)
        max_tool_iterations: Maximum iterations for tool calling loop (default: 10)
        **kwargs: Additional agent configuration

    Returns:
        Agent instance with tools attached

    Example:
        >>> from src.core.agno_agent_framework.tools import Tool, ToolType
        >>>
        >>> def calculate_sum(a: int, b: int) -> int:
        ...     return a + b
        >>>
        >>> tool = Tool(
        ...     tool_id="calc_sum",
        ...     name="calculate_sum",
        ...     description="Adds two numbers",
        ...     tool_type=ToolType.FUNCTION,
        ...     function=calculate_sum
        ... )
        >>>
        >>> agent = create_agent_with_tools(
        ...     "agent1", "Calculator", gateway,
        ...     tools=[tool],
        ...     enable_tool_calling=True
        ... )
    """
    agent = create_agent(agent_id, name, gateway, tenant_id=tenant_id, **kwargs)

    agent.enable_tool_calling = enable_tool_calling
    agent.max_tool_iterations = max_tool_iterations

    if tools or tool_registry:
        agent.attach_tools(tools=tools, registry=tool_registry)

    return agent


def create_agent_manager() -> AgentManager:
    """
    Create a new AgentManager instance.

    Returns:
        AgentManager instance

    Example:
        >>> manager = create_agent_manager()
        >>> agent = create_agent("agent1", "Assistant", gateway)
        >>> manager.register_agent(agent)
    """
    return AgentManager()


def create_orchestrator(agent_manager: AgentManager) -> AgentOrchestrator:
    """
    Create an AgentOrchestrator for multi-agent workflows.

    Args:
        agent_manager: AgentManager instance

    Returns:
        AgentOrchestrator instance

    Example:
        >>> manager = create_agent_manager()
        >>> orchestrator = create_orchestrator(manager)
        >>> workflow = orchestrator.create_workflow("data_analysis")
    """
    return AgentOrchestrator(agent_manager)


# ============================================================================
# High-Level Convenience Functions
# ============================================================================

async def execute_task(
    agent: Agent,
    task_type: str,
    parameters: Dict[str, Any],
    tenant_id: Optional[str] = None,
    priority: int = 0
) -> Dict[str, Any]:  # Task result is typically a dict
    """
    Execute a task on an agent (high-level convenience function).

    Args:
        agent: Agent instance
        task_type: Type of task to execute
        parameters: Task parameters
        priority: Task priority (higher = more important)

    Returns:
        Task execution result

    Example:
        >>> result = await execute_task(
        ...     agent,
        ...     "analyze",
        ...     {"text": "Analyze this document", "model": "gpt-4"}
        ... )
    """
    task_id = agent.add_task(task_type, parameters, priority)
    task = next(t for t in agent.task_queue if t.task_id == task_id)
    return await agent.execute_task(task, tenant_id=tenant_id)


async def chat_with_agent(
    agent: Agent,
    message: str,
    tenant_id: Optional[str] = None,
    session_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Chat with an agent using session management (high-level convenience).

    Args:
        agent: Agent instance
        message: User message
        session_id: Optional session ID (creates new if not provided)
        context: Optional context variables

    Returns:
        Dictionary with response and session info

    Example:
        >>> response = await chat_with_agent(
        ...     agent,
        ...     "What is AI?",
        ...     context={"user_id": "user123"}
        ... )
        >>> print(response["answer"])
    """
    # Create or get session manager
    # Use a module-level session manager or create one per agent
    if not hasattr(chat_with_agent, '_session_managers'):
        chat_with_agent._session_managers = {}

    if agent.agent_id not in chat_with_agent._session_managers:
        chat_with_agent._session_managers[agent.agent_id] = SessionManager()

    session_manager = chat_with_agent._session_managers[agent.agent_id]

    if session_id:
        session = session_manager.get_session(session_id)
        if not session:
            session = session_manager.create_session(agent.agent_id)
    else:
        session = session_manager.create_session(agent.agent_id)

    # Add user message to session
    session.add_message("user", message, metadata=context or {})

    # Execute task
    result = await execute_task(
        agent,
        "llm_query",
        {
            "prompt": message,
            "messages": [
                {"role": msg.role, "content": msg.content}
                for msg in session.messages[-10:]  # Last 10 messages
            ]
        }
    )

    # Extract answer
    answer = result.get("result", "") if isinstance(result, dict) else str(result)

    # Add assistant response to session
    session.add_message("assistant", answer)

    return {
        "answer": answer,
        "session_id": session.session_id,
        "result": result
    }


async def delegate_task(
    orchestrator: AgentOrchestrator,
    from_agent_id: str,
    to_agent_id: str,
    task_type: str,
    parameters: Dict[str, Any],
    priority: int = 5
) -> Dict[str, Any]:  # Task result is typically a dict
    """
    Delegate a task from one agent to another (high-level convenience).

    Args:
        orchestrator: AgentOrchestrator instance
        from_agent_id: Source agent ID
        to_agent_id: Target agent ID
        task_type: Type of task
        parameters: Task parameters
        priority: Task priority

    Returns:
        Task execution result

    Example:
        >>> result = await delegate_task(
        ...     orchestrator,
        ...     "agent1",
        ...     "agent2",
        ...     "analyze",
        ...     {"data": "..."}
        ... )
    """
    return await orchestrator.delegate_task(
        from_agent_id,
        to_agent_id,
        task_type,
        parameters,
        priority
    )


def find_agents_by_capability(
    manager: AgentManager,
    capability_name: str
) -> List[Agent]:
    """
    Find agents with a specific capability (high-level convenience).

    Args:
        manager: AgentManager instance
        capability_name: Capability name to search for

    Returns:
        List of agents with the capability

    Example:
        >>> agents = find_agents_by_capability(manager, "data_analysis")
        >>> for agent in agents:
        ...     print(agent.name)
    """
    return manager.find_agents_by_capability(capability_name)


# ============================================================================
# Utility Functions
# ============================================================================

def batch_process_agents(
    agents: List[Agent],
    task_type: str,
    parameters: Dict[str, Any],
    max_concurrent: int = 5
) -> List[Any]:
    """
    Process tasks on multiple agents concurrently.

    Args:
        agents: List of agent instances
        task_type: Type of task to execute
        parameters: Task parameters
        max_concurrent: Maximum concurrent executions

    Returns:
        List of results from each agent

    Example:
        >>> results = batch_process_agents(
        ...     [agent1, agent2, agent3],
        ...     "analyze",
        ...     {"text": "..."}
        ... )
    """
    import asyncio

    async def _process():
        tasks = [
            execute_task(agent, task_type, parameters)
            for agent in agents
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)

    return asyncio.run(_process())


def retry_on_failure(
    max_retries: int = 3,
    retry_delay: float = 1.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator to retry function on failure.

    Args:
        max_retries: Maximum number of retries
        retry_delay: Delay between retries in seconds
        exceptions: Tuple of exceptions to catch

    Returns:
        Decorator function

    Example:
        >>> @retry_on_failure(max_retries=3)
        ... async def my_function():
        ...     # May fail, will retry up to 3 times
        ...     pass
    """
    import asyncio
    from functools import wraps

    from typing import TypeVar, Callable, cast
    F = TypeVar('F', bound=Callable[..., Any])
    
    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (attempt + 1))
                    else:
                        raise last_error

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            import time
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (attempt + 1))
                    else:
                        raise last_error

        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        return cast(F, sync_wrapper)

    return decorator


def save_agent_state(
    agent: Agent,
    file_path: Optional[str] = None
) -> None:
    """
    Save agent state to disk for persistence (utility function).

    Args:
        agent: Agent instance to save
        file_path: Optional path to save state

    Example:
        >>> save_agent_state(agent, "/tmp/agent_state.json")
    """
    agent.save_state(file_path)


def load_agent_state(
    file_path: str,
    gateway: GatewayProtocol
) -> Agent:
    """
    Load agent state from disk (utility function).

    Args:
        file_path: Path to saved state file
        gateway: LiteLLM Gateway instance

    Returns:
        Restored Agent instance

    Example:
        >>> agent = load_agent_state("/tmp/agent_state.json", gateway)
    """
    return Agent.load_state(file_path, gateway)


__all__ = [
    # Factory functions
    "create_agent",
    "create_agent_with_memory",
    "create_agent_with_prompt_management",
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
]

