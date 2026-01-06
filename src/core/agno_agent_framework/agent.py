"""
Agno Agent Framework - Core Agent Implementation

Provides the base agent class and agent management functionality.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum
import asyncio
from datetime import datetime
from .memory import AgentMemory, MemoryType


class AgentStatus(str, Enum):
    """Agent status enumeration."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class AgentCapability(BaseModel):
    """Agent capability definition."""
    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class AgentMessage(BaseModel):
    """Message between agents."""
    from_agent: str
    to_agent: str
    content: Any
    message_type: str = "task"
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentTask(BaseModel):
    """Task for an agent."""
    task_id: str
    task_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    status: str = "pending"


class Agent(BaseModel):
    """
    Base Agent class for autonomous AI agents.
    
    Agents can execute tasks, communicate with other agents,
    and coordinate complex workflows.
    """
    
    agent_id: str
    name: str
    description: str = ""
    capabilities: List[AgentCapability] = Field(default_factory=list)
    status: AgentStatus = AgentStatus.IDLE
    
    # LLM configuration
    llm_model: Optional[str] = None
    llm_provider: Optional[str] = None
    gateway: Optional[Any] = None  # LiteLLM Gateway instance
    
    # Communication
    message_queue: List[AgentMessage] = Field(default_factory=list)
    communication_enabled: bool = True

    # Memory
    memory: Optional[AgentMemory] = None
    memory_persistence_path: Optional[str] = None
    auto_persist_memory: bool = True
    
    # Task management
    task_queue: List[AgentTask] = Field(default_factory=list)
    current_task: Optional[AgentTask] = None

    # Reliability
    max_retries: int = 1
    retry_delay: float = 0.1
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    last_active: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True
    
    def add_capability(
        self,
        name: str,
        description: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a capability to the agent.
        
        Args:
            name: Capability name
            description: Capability description
            parameters: Optional parameters
        """
        capability = AgentCapability(
            name=name,
            description=description,
            parameters=parameters or {}
        )
        self.capabilities.append(capability)
    
    def add_task(
        self,
        task_type: str,
        parameters: Dict[str, Any],
        priority: int = 0
    ) -> str:
        """
        Add a task to the agent's task queue.
        
        Args:
            task_type: Type of task
            parameters: Task parameters
            priority: Task priority (higher = more important)
        
        Returns:
            Task ID
        """
        task_id = f"{self.agent_id}_{len(self.task_queue) + 1}"
        task = AgentTask(
            task_id=task_id,
            task_type=task_type,
            parameters=parameters,
            priority=priority
        )
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda t: t.priority, reverse=True)
        return task_id
    
    async def execute_task(self, task: AgentTask) -> Any:
        """
        Execute a task.
        
        Args:
            task: Task to execute
        
        Returns:
            Task result
        """
        self.status = AgentStatus.RUNNING
        self.current_task = task
        attempt = 0
        last_error: Optional[Exception] = None
        
        while attempt < max(1, self.max_retries):
            try:
                result = await self._execute_task_internal(task)
                self.last_active = datetime.now()
                if self.memory and self.auto_persist_memory:
                    self.memory.store(
                        content=f"Task {task.task_id} result: {result}",
                        memory_type=MemoryType.SHORT_TERM,
                        importance=0.6,
                        metadata={"task_type": task.task_type},
                    )
                return result
            except Exception as e:  # pragma: no cover - runtime errors
                last_error = e
                self.status = AgentStatus.ERROR
                attempt += 1
                if attempt < max(1, self.max_retries):
                    await asyncio.sleep(self.retry_delay)
                    continue
                raise
            finally:
                self.status = AgentStatus.IDLE
                self.current_task = None
    
    async def _execute_task_internal(self, task: AgentTask) -> Any:
        """
        Internal task execution logic.
        
        Args:
            task: Task to execute
        
        Returns:
            Task result
        """
        # Use gateway for LLM operations if available
        if self.gateway and task.task_type in ["llm_query", "generate", "analyze"]:
            prompt = task.parameters.get("prompt", "")
            model = task.parameters.get("model", self.llm_model or "gpt-4")
            
            response = await self.gateway.generate_async(
                prompt=prompt,
                model=model,
                **task.parameters.get("llm_kwargs", {})
            )
            
            return {
                "status": "completed",
                "task_id": task.task_id,
                "result": response.text,
                "model": response.model
            }
        
        # Default task execution
        return {
            "status": "completed",
            "task_id": task.task_id,
            "result": f"Task {task.task_type} executed"
        }

    def attach_memory(self, persistence_path: Optional[str] = None) -> None:
        """Attach an AgentMemory instance with optional persistence."""
        self.memory = AgentMemory(
            agent_id=self.agent_id,
            persistence_path=persistence_path or self.memory_persistence_path,
        )
    
    def send_message(
        self,
        to_agent: str,
        content: Any,
        message_type: str = "task"
    ) -> None:
        """
        Send a message to another agent.
        
        Args:
            to_agent: Target agent ID
            content: Message content
            message_type: Type of message
        """
        if not self.communication_enabled:
            return
        
        message = AgentMessage(
            from_agent=self.agent_id,
            to_agent=to_agent,
            content=content,
            message_type=message_type
        )
        self.message_queue.append(message)
    
    def receive_message(self) -> Optional[AgentMessage]:
        """
        Receive a message from the message queue.
        
        Returns:
            Message or None if queue is empty
        """
        if self.message_queue:
            return self.message_queue.pop(0)
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get agent status information.
        
        Returns:
            Status dictionary
        """
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": self.status.value,
            "capabilities": [cap.name for cap in self.capabilities],
            "task_queue_size": len(self.task_queue),
            "current_task": self.current_task.task_id if self.current_task else None,
            "last_active": self.last_active.isoformat(),
        }
    
    def save_state(self, file_path: Optional[str] = None) -> None:
        """
        Save agent state to disk for persistence.
        
        Saves agent configuration, capabilities, task queue, and metadata.
        Memory is persisted separately via memory.save() if memory is attached.
        
        Args:
            file_path: Optional path to save state. If None, uses agent_id.json
        """
        import json
        from pathlib import Path
        
        if not file_path:
            file_path = f"{self.agent_id}_state.json"
        
        state_path = Path(file_path)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare state (exclude non-serializable objects like gateway)
        state = {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "capabilities": [cap.model_dump() for cap in self.capabilities],
            "status": self.status.value,
            "llm_model": self.llm_model,
            "llm_provider": self.llm_provider,
            "task_queue": [task.model_dump() for task in self.task_queue],
            "current_task": self.current_task.model_dump() if self.current_task else None,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "metadata": self.metadata,
            "memory_persistence_path": str(self.memory_persistence_path) if self.memory_persistence_path else None,
            "auto_persist_memory": self.auto_persist_memory,
            "communication_enabled": self.communication_enabled,
        }
        
        with state_path.open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, default=str)
        
        # Persist memory if attached
        if self.memory and self.auto_persist_memory:
            self.memory.save()
    
    @classmethod
    def load_state(
        cls,
        file_path: str,
        gateway: Optional[Any] = None
    ) -> "Agent":
        """
        Load agent state from disk.
        
        Args:
            file_path: Path to saved state file
            gateway: LiteLLM Gateway instance (required for agent functionality)
        
        Returns:
            Restored Agent instance
        """
        import json
        from pathlib import Path
        
        state_path = Path(file_path)
        if not state_path.exists():
            raise FileNotFoundError(f"Agent state file not found: {file_path}")
        
        with state_path.open("r", encoding="utf-8") as f:
            state = json.load(f)
        
        # Recreate agent
        agent = cls(
            agent_id=state["agent_id"],
            name=state["name"],
            description=state.get("description", ""),
            gateway=gateway,
            llm_model=state.get("llm_model"),
            llm_provider=state.get("llm_provider"),
        )
        
        # Restore capabilities
        agent.capabilities = [
            AgentCapability(**cap) for cap in state.get("capabilities", [])
        ]
        
        # Restore status
        agent.status = AgentStatus(state.get("status", "idle"))
        
        # Restore task queue
        agent.task_queue = [
            AgentTask(**task) for task in state.get("task_queue", [])
        ]
        
        # Restore current task
        if state.get("current_task"):
            agent.current_task = AgentTask(**state["current_task"])
        
        # Restore configuration
        agent.max_retries = state.get("max_retries", 1)
        agent.retry_delay = state.get("retry_delay", 0.1)
        agent.metadata = state.get("metadata", {})
        agent.communication_enabled = state.get("communication_enabled", True)
        agent.auto_persist_memory = state.get("auto_persist_memory", True)
        
        # Restore timestamps
        from datetime import datetime
        if state.get("created_at"):
            agent.created_at = datetime.fromisoformat(state["created_at"])
        if state.get("last_active"):
            agent.last_active = datetime.fromisoformat(state["last_active"])
        
        # Restore memory if path exists
        memory_path = state.get("memory_persistence_path")
        if memory_path:
            agent.memory_persistence_path = memory_path
            agent.attach_memory(memory_path)
        
        return agent


class AgentManager:
    """
    Manager for multiple agents with orchestration support.
    
    Provides agent registration, discovery, and basic coordination.
    For advanced orchestration, use AgentOrchestrator.
    """
    
    def __init__(self):
        """Initialize agent manager."""
        self._agents: Dict[str, Agent] = {}
        self._orchestrator: Optional[Any] = None  # AgentOrchestrator instance
    
    def register_agent(self, agent: Agent) -> None:
        """
        Register an agent.
        
        Args:
            agent: Agent instance
        """
        self._agents[agent.agent_id] = agent
    
    def unregister_agent(self, agent_id: str) -> None:
        """
        Unregister an agent.
        
        Args:
            agent_id: Agent identifier
        """
        self._agents.pop(agent_id, None)
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """
        Get an agent by ID.
        
        Args:
            agent_id: Agent identifier
        
        Returns:
            Agent instance or None
        """
        return self._agents.get(agent_id)
    
    def list_agents(self) -> List[str]:
        """
        List all registered agent IDs.
        
        Returns:
            List of agent IDs
        """
        return list(self._agents.keys())
    
    def find_agents_by_capability(self, capability_name: str) -> List[Agent]:
        """
        Find agents with a specific capability.
        
        Args:
            capability_name: Capability name to search for
        
        Returns:
            List of agents with the capability
        """
        return [
            agent for agent in self._agents.values()
            if any(cap.name == capability_name for cap in agent.capabilities)
        ]
    
    async def broadcast_message(
        self,
        from_agent: str,
        content: Any,
        message_type: str = "broadcast"
    ) -> None:
        """
        Broadcast a message to all agents.
        
        Args:
            from_agent: Sender agent ID
            content: Message content
            message_type: Type of message
        """
        for agent in self._agents.values():
            if agent.agent_id != from_agent:
                agent.send_message(from_agent, content, message_type)
    
    async def send_message_to_agent(
        self,
        from_agent: str,
        to_agent: str,
        content: Any,
        message_type: str = "message"
    ) -> None:
        """
        Send a message from one agent to another.
        
        Args:
            from_agent: Sender agent ID
            to_agent: Target agent ID
            content: Message content
            message_type: Type of message
        """
        target = self.get_agent(to_agent)
        if target:
            target.send_message(from_agent, content, message_type)
    
    def get_agent_statuses(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all agents.
        
        Returns:
            Dictionary mapping agent IDs to their status
        """
        return {
            agent_id: agent.get_status()
            for agent_id, agent in self._agents.items()
        }
    
    def attach_orchestrator(self, orchestrator: Any) -> None:
        """
        Attach an orchestrator to this manager.
        
        Args:
            orchestrator: AgentOrchestrator instance
        """
        self._orchestrator = orchestrator
    
    def get_orchestrator(self) -> Optional[Any]:
        """Get the attached orchestrator."""
        return self._orchestrator

