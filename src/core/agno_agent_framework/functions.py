"""
Agno Agent Framework - High-Level Functions

Factory functions, convenience functions, and utilities for agent framework.
"""

from typing import Any, Dict, List, Optional
from .agent import Agent, AgentManager, AgentTask, AgentStatus
from .memory import AgentMemory, MemoryType
from .session import AgentSession, SessionManager
from .tools import ToolRegistry, ToolExecutor
from .plugins import PluginManager
from .orchestration import AgentOrchestrator, WorkflowPipeline


# ============================================================================
# Factory Functions
# ============================================================================

def create_agent(
    agent_id: str,
    name: str,
    gateway: Any,
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
        description: Agent description
        llm_model: Optional LLM model name
        llm_provider: Optional LLM provider
        **kwargs: Additional agent configuration
    
    Returns:
        Configured Agent instance
    
    Example:
        >>> gateway = LiteLLMGateway()
        >>> agent = create_agent("agent1", "Assistant", gateway)
    """
    return Agent(
        agent_id=agent_id,
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
    gateway: Any,
    memory_config: Optional[Dict[str, Any]] = None,
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
    priority: int = 0
) -> Any:
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
    return await agent.execute_task(task)


async def chat_with_agent(
    agent: Agent,
    message: str,
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
) -> Any:
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
    
    def decorator(func: Any) -> Any:
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
            return async_wrapper
        return sync_wrapper
    
    return decorator


__all__ = [
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

