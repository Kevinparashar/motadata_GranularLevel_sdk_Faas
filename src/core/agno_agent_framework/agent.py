"""
Agno Agent Framework - Core Agent Implementation

Provides the base agent class and agent management functionality.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum
import asyncio
from datetime import datetime


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
    
    # Task management
    task_queue: List[AgentTask] = Field(default_factory=list)
    current_task: Optional[AgentTask] = None
    
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
        
        try:
            # Execute task based on type
            result = await self._execute_task_internal(task)
            self.last_active = datetime.now()
            return result
        except Exception as e:
            self.status = AgentStatus.ERROR
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


class AgentManager:
    """Manager for multiple agents."""
    
    def __init__(self):
        """Initialize agent manager."""
        self._agents: Dict[str, Agent] = {}
    
    def register_agent(self, agent: Agent) -> None:
        """
        Register an agent.
        
        Args:
            agent: Agent instance
        """
        self._agents[agent.agent_id] = agent
    
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

