"""
Agno Agent Framework - Core Agent Implementation

Provides the base agent class and agent management functionality.
"""

from typing import Any, Dict, List, Optional, Callable
from pydantic import BaseModel, Field
from enum import Enum
import asyncio
import json
from datetime import datetime
from .memory import AgentMemory, MemoryType
from .tools import ToolRegistry, ToolExecutor, Tool
from .exceptions import (
    AgentExecutionError,
    AgentConfigurationError,
    AgentStateError,
    MemoryWriteError
)

# Import Prompt Context Management
try:
    from ..prompt_context_management import PromptContextManager, create_prompt_manager
except ImportError:
    # Fallback if not available
    PromptContextManager = None
    create_prompt_manager = None


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
    
    # Prompt Context Management
    prompt_manager: Optional[Any] = None  # PromptContextManager instance
    system_prompt: Optional[str] = None
    role_template: Optional[str] = None  # Role-based template name
    use_prompt_management: bool = True  # Enable/disable prompt management
    max_context_tokens: int = 4000  # Max tokens for context window
    
    # Tool Management
    tool_registry: Optional[ToolRegistry] = None
    tool_executor: Optional[ToolExecutor] = None
    enable_tool_calling: bool = True  # Enable/disable tool calling
    max_tool_iterations: int = 10  # Max iterations for tool calling loop
    
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
            except AgentExecutionError:
                # Re-raise agent execution errors as-is
                self.status = AgentStatus.ERROR
                raise
            except Exception as e:  # pragma: no cover - runtime errors
                # Wrap other exceptions in AgentExecutionError
                last_error = e
                self.status = AgentStatus.ERROR
                attempt += 1
                if attempt < max(1, self.max_retries):
                    await asyncio.sleep(self.retry_delay)
                    continue
                raise AgentExecutionError(
                    message=f"Agent execution failed: {str(e)}",
                    agent_id=self.agent_id,
                    task_type=task.task_type if task else None,
                    execution_stage="execution",
                    original_error=e
                )
            finally:
                self.status = AgentStatus.IDLE
                self.current_task = None
    
    async def _execute_task_internal(self, task: AgentTask) -> Any:
        """
        Internal task execution logic with integrated prompt management and tool calling.
        
        Args:
            task: Task to execute
        
        Returns:
            Task result
        """
        # Use gateway for LLM operations if available
        if self.gateway and task.task_type in ["llm_query", "generate", "analyze"]:
            # Get base prompt from task parameters
            base_prompt = task.parameters.get("prompt", "")
            model = task.parameters.get("model", self.llm_model or "gpt-4")
            
            # Build prompt using prompt management if enabled
            final_prompt = self._build_prompt_with_context(
                base_prompt=base_prompt,
                task=task,
                task_type=task.task_type
            )
            
            # Record prompt in history if prompt manager is available
            if self.prompt_manager:
                self.prompt_manager.record_history(final_prompt)
            
            # Prepare messages for conversation
            messages = [{"role": "user", "content": final_prompt}]
            
            # Get tool schemas if tools are enabled
            tools_schema = None
            if self.enable_tool_calling and self.tool_registry:
                tools_schema = self.tool_registry.get_tools_schema()
            
            # Tool calling loop
            iteration = 0
            tool_calls_made = []
            
            while iteration < self.max_tool_iterations:
                # Prepare kwargs for LLM call
                llm_kwargs = task.parameters.get("llm_kwargs", {})
                
                # Add tools if available
                if tools_schema:
                    llm_kwargs["tools"] = tools_schema
                    llm_kwargs["tool_choice"] = "auto"
                
                # Make LLM call
                response = await self.gateway.generate_async(
                    prompt=messages[-1]["content"] if messages else final_prompt,
                    model=model,
                    messages=messages,
                    **llm_kwargs
                )
                
                # Extract response content
                response_text = response.text
                finish_reason = getattr(response, 'finish_reason', None)
                
                # Check for function calls in raw response
                function_calls = self._extract_function_calls(response)
                
                # If no function calls, return the final response
                if not function_calls or finish_reason != "tool_calls":
                    # Add assistant response to messages
                    messages.append({"role": "assistant", "content": response_text})
                    
                    return {
                        "status": "completed",
                        "task_id": task.task_id,
                        "result": response_text,
                        "model": response.model if hasattr(response, 'model') else model,
                        "tool_calls": tool_calls_made,
                        "iterations": iteration + 1
                    }
                
                # Execute function calls
                messages.append({"role": "assistant", "content": response_text})
                
                for func_call in function_calls:
                    tool_name = func_call.get("name", "")
                    arguments = func_call.get("arguments", {})
                    
                    try:
                        # Execute tool
                        if self.tool_executor:
                            tool_result = self.tool_executor.execute_tool_call(
                                tool_name=tool_name,
                                arguments=arguments
                            )
                            
                            # Store tool call info
                            tool_calls_made.append({
                                "tool": tool_name,
                                "arguments": arguments,
                                "result": str(tool_result) if not isinstance(tool_result, (dict, list)) else tool_result,
                                "success": True
                            })
                            
                            # Add tool result to messages for next LLM call
                            messages.append({
                                "role": "tool",
                                "content": json.dumps(tool_result) if isinstance(tool_result, (dict, list)) else str(tool_result),
                                "tool_call_id": func_call.get("id", f"call_{iteration}_{len(tool_calls_made)}")
                            })
                            
                            # Store tool execution in memory
                            if self.memory:
                                self.memory.store(
                                    content=f"Tool {tool_name} executed with result: {tool_result}",
                                    memory_type=MemoryType.SHORT_TERM,
                                    importance=0.7,
                                    metadata={"tool_name": tool_name, "task_id": task.task_id}
                                )
                        else:
                            tool_calls_made.append({
                                "tool": tool_name,
                                "arguments": arguments,
                                "result": "Tool executor not available",
                                "success": False
                            })
                    except Exception as e:
                        # Handle tool execution errors
                        tool_calls_made.append({
                            "tool": tool_name,
                            "arguments": arguments,
                            "result": f"Tool execution failed: {str(e)}",
                            "success": False,
                            "error": str(e)
                        })
                        raise
                
                iteration += 1
            
            # Max iterations reached, return last response
            return {
                "status": "completed",
                "task_id": task.task_id,
                "result": response_text,
                "model": response.model if hasattr(response, 'model') else model,
                "tool_calls": tool_calls_made,
                "iterations": iteration,
                "warning": "Max tool iterations reached"
            }
        
        # Default task execution
        return {
            "status": "completed",
            "task_id": task.task_id,
            "result": f"Task {task.task_type} executed"
        }
    
    def _extract_function_calls(self, response: Any) -> List[Dict[str, Any]]:
        """
        Extract function calls from LLM response.
        
        Args:
            response: LLM response object
        
        Returns:
            List of function call dictionaries
        """
        function_calls = []
        
        # Check raw_response for function calls
        if hasattr(response, 'raw_response'):
            raw = response.raw_response
            if isinstance(raw, dict):
                choices = raw.get("choices", [])
                if choices:
                    message = choices[0].get("message", {})
                    tool_calls = message.get("tool_calls", [])
                    if tool_calls:
                        for tool_call in tool_calls:
                            func_call = {
                                "id": tool_call.get("id", ""),
                                "name": tool_call.get("function", {}).get("name", ""),
                                "arguments": json.loads(tool_call.get("function", {}).get("arguments", "{}"))
                            }
                            function_calls.append(func_call)
            elif hasattr(raw, 'choices'):
                # Handle LiteLLM response object
                if raw.choices:
                    message = raw.choices[0].message
                    if hasattr(message, 'tool_calls') and message.tool_calls:
                        for tool_call in message.tool_calls:
                            func_call = {
                                "id": tool_call.id if hasattr(tool_call, 'id') else "",
                                "name": tool_call.function.name if hasattr(tool_call, 'function') and hasattr(tool_call.function, 'name') else "",
                                "arguments": json.loads(tool_call.function.arguments) if hasattr(tool_call, 'function') and hasattr(tool_call.function, 'arguments') else {}
                            }
                            function_calls.append(func_call)
        
        return function_calls
    
    def _build_prompt_with_context(
        self,
        base_prompt: str,
        task: AgentTask,
        task_type: str
    ) -> str:
        """
        Build prompt with context management, system prompts, and memory integration.
        
        Args:
            base_prompt: Base prompt from task
            task: Task instance
            task_type: Type of task
        
        Returns:
            Final prompt with context
        """
        # Initialize prompt manager if not present and enabled
        if self.use_prompt_management and not self.prompt_manager:
            if PromptContextManager and create_prompt_manager:
                self.prompt_manager = create_prompt_manager(
                    max_tokens=self.max_context_tokens
                )
                # Add default role template if role_template is set
                if self.prompt_manager and self.role_template and self.description:
                    self.prompt_manager.add_template(
                        name=self.role_template,
                        version="1.0",
                        content=self.description
                    )
        
        # If prompt management is disabled, return base prompt
        if not self.use_prompt_management or not self.prompt_manager:
            return base_prompt
        
        # Start with system prompt if available
        prompt_parts = []
        
        # Add system prompt
        if self.system_prompt:
            prompt_parts.append(f"System: {self.system_prompt}")
        
        # Add role-based template if available
        if self.role_template:
            try:
                role_prompt = self.prompt_manager.render(
                    template_name=self.role_template,
                    variables={
                        "agent_name": self.name,
                        "agent_id": self.agent_id,
                        "capabilities": ", ".join([cap.name for cap in self.capabilities]),
                        "description": self.description
                    }
                )
                prompt_parts.append(f"Role: {role_prompt}")
            except (ValueError, KeyError):
                # Template not found or render failed, use description
                if self.description:
                    prompt_parts.append(f"Role: {self.description}")
        
        # Retrieve relevant context from memory
        context_from_memory = ""
        if self.memory:
            # Retrieve relevant memories based on task
            relevant_memories = self.memory.retrieve(
                query=base_prompt,
                limit=5  # Get top 5 relevant memories
            )
            if relevant_memories:
                memory_contents = [mem.content for mem in relevant_memories]
                context_from_memory = "\n".join(memory_contents)
        
        # Build context with history if available
        if self.prompt_manager.history:
            context = self.prompt_manager.build_context_with_history(base_prompt)
        else:
            context = base_prompt
        
        # Add context from memory
        if context_from_memory:
            context = f"{context}\n\nRelevant Context:\n{context_from_memory}"
        
        # Add task-specific context
        if task.parameters.get("context"):
            context = f"{context}\n\nAdditional Context:\n{task.parameters.get('context')}"
        
        # Add the main prompt
        prompt_parts.append(f"Task: {base_prompt}")
        
        # Combine all parts
        full_prompt = "\n\n".join(prompt_parts)
        
        # Add context if available
        if context and context != base_prompt:
            full_prompt = f"{full_prompt}\n\nContext:\n{context}"
        
        # Enforce token budget
        validation = self.prompt_manager.window.estimate_tokens(full_prompt)
        if validation > (self.max_context_tokens - self.prompt_manager.window.safety_margin):
            # Truncate to fit
            full_prompt = self.prompt_manager.truncate_prompt(
                full_prompt,
                max_tokens=self.max_context_tokens
            )
        
        return full_prompt

    def attach_memory(self, persistence_path: Optional[str] = None) -> None:
        """Attach an AgentMemory instance with optional persistence."""
        self.memory = AgentMemory(
            agent_id=self.agent_id,
            persistence_path=persistence_path or self.memory_persistence_path,
        )
    
    def attach_tools(self, tools: Optional[List[Tool]] = None, registry: Optional[ToolRegistry] = None) -> None:
        """
        Attach tools to the agent.
        
        Args:
            tools: Optional list of Tool instances to register
            registry: Optional pre-configured ToolRegistry
        """
        if registry:
            self.tool_registry = registry
        else:
            self.tool_registry = ToolRegistry()
            if tools:
                for tool in tools:
                    self.tool_registry.register_tool(tool)
        
        self.tool_executor = ToolExecutor(self.tool_registry)
    
    def add_tool(self, tool: Tool) -> None:
        """
        Add a single tool to the agent's tool registry.
        
        Args:
            tool: Tool instance to add
        """
        if not self.tool_registry:
            self.tool_registry = ToolRegistry()
            self.tool_executor = ToolExecutor(self.tool_registry)
        
        self.tool_registry.register_tool(tool)
    
    def attach_prompt_manager(
        self,
        prompt_manager: Optional[Any] = None,
        max_tokens: int = 4000,
        system_prompt: Optional[str] = None,
        role_template: Optional[str] = None
    ) -> None:
        """
        Attach a PromptContextManager instance to the agent.
        
        Args:
            prompt_manager: Optional PromptContextManager instance (creates new if None)
            max_tokens: Maximum tokens for context window
            system_prompt: Optional system prompt for the agent
            role_template: Optional role-based template name
        """
        if prompt_manager:
            self.prompt_manager = prompt_manager
        elif PromptContextManager and create_prompt_manager:
            self.prompt_manager = create_prompt_manager(max_tokens=max_tokens)
        else:
            raise AgentConfigurationError(
                message="PromptContextManager is not available",
                agent_id=self.agent_id,
                config_key="prompt_manager"
            )
        
        self.max_context_tokens = max_tokens
        if system_prompt:
            self.system_prompt = system_prompt
        if role_template:
            self.role_template = role_template
    
    def set_system_prompt(self, system_prompt: str) -> None:
        """
        Set the system prompt for the agent.
        
        Args:
            system_prompt: System prompt text
        """
        self.system_prompt = system_prompt
    
    def add_prompt_template(
        self,
        name: str,
        version: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a prompt template to the agent's prompt manager.
        
        Args:
            name: Template name
            version: Template version
            content: Template content
            metadata: Optional metadata
        """
        if not self.prompt_manager:
            self.attach_prompt_manager()
        
        if not self.prompt_manager:
            raise AgentConfigurationError(
                message="Prompt manager is not available",
                agent_id=self.agent_id,
                config_key="prompt_manager"
            )
        
        self.prompt_manager.add_template(
            name=name,
            version=version,
            content=content,
            metadata=metadata
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
        Save complete agent state to disk for persistence.
        
        Saves agent configuration, capabilities, task queue, tools, memory,
        prompt manager state, and metadata.
        
        Args:
            file_path: Optional path to save state. If None, uses agent_id.json
        """
        from pathlib import Path
        
        if not file_path:
            file_path = f"{self.agent_id}_state.json"
        
        state_path = Path(file_path)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Serialize tool registry if available
        tools_state = None
        if self.tool_registry:
            tools_state = []
            for tool_id, tool in self.tool_registry._tools.items():
                # Serialize tool (exclude function, as it's not serializable)
                tool_dict = {
                    "tool_id": tool.tool_id,
                    "name": tool.name,
                    "description": tool.description,
                    "tool_type": tool.tool_type.value if hasattr(tool.tool_type, 'value') else str(tool.tool_type),
                    "parameters": [param.model_dump() for param in tool.parameters],
                    "metadata": tool.metadata,
                    "tags": tool.tags,
                    # Note: function is not serialized - must be re-registered on load
                }
                tools_state.append(tool_dict)
        
        # Serialize prompt manager state if available
        prompt_manager_state = None
        if self.prompt_manager:
            prompt_manager_state = {
                "max_tokens": self.max_context_tokens,
                "templates": [],
                "history_count": len(self.prompt_manager.history) if hasattr(self.prompt_manager, 'history') else 0
            }
            # Save templates if available
            if hasattr(self.prompt_manager, 'templates'):
                for template_name, template in self.prompt_manager.templates.items():
                    template_dict = {
                        "name": template_name,
                        "version": template.version if hasattr(template, 'version') else "1.0",
                        "content": template.content if hasattr(template, 'content') else str(template),
                        "metadata": template.metadata if hasattr(template, 'metadata') else {}
                    }
                    prompt_manager_state["templates"].append(template_dict)
        
        # Prepare complete state
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
            "system_prompt": self.system_prompt,
            "role_template": self.role_template,
            "use_prompt_management": self.use_prompt_management,
            "max_context_tokens": self.max_context_tokens,
            "enable_tool_calling": self.enable_tool_calling,
            "max_tool_iterations": self.max_tool_iterations,
            "tools": tools_state,
            "prompt_manager": prompt_manager_state,
        }
        
        with state_path.open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, default=str)
        
        # Persist memory if attached (memory persists automatically via _persist())
        if self.memory and self.auto_persist_memory:
            # Memory persistence is handled automatically by the memory system
            # when operations are performed (store, consolidate, etc.)
            pass
        
        # Save prompt manager history if available
        if self.prompt_manager and hasattr(self.prompt_manager, 'save_history'):
            prompt_history_path = state_path.parent / f"{self.agent_id}_prompt_history.json"
            self.prompt_manager.save_history(str(prompt_history_path))
    
    @classmethod
    def load_state(
        cls,
        file_path: str,
        gateway: Optional[Any] = None,
        restore_tools: Optional[Dict[str, Callable]] = None
    ) -> "Agent":
        """
        Load complete agent state from disk.
        
        Args:
            file_path: Path to saved state file
            gateway: LiteLLM Gateway instance (required for agent functionality)
            restore_tools: Optional dictionary mapping tool names to their functions.
                          Required to restore tools with their implementations.
        
        Returns:
            Restored Agent instance with complete state
        """
        from pathlib import Path
        
        state_path = Path(file_path)
        if not state_path.exists():
            raise AgentStateError(
                message=f"Agent state file not found: {file_path}",
                operation="load",
                file_path=file_path
            )
        
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
        agent.system_prompt = state.get("system_prompt")
        agent.role_template = state.get("role_template")
        agent.use_prompt_management = state.get("use_prompt_management", True)
        agent.max_context_tokens = state.get("max_context_tokens", 4000)
        agent.enable_tool_calling = state.get("enable_tool_calling", True)
        agent.max_tool_iterations = state.get("max_tool_iterations", 10)
        
        # Restore prompt manager if enabled
        if agent.use_prompt_management and PromptContextManager:
            agent.attach_prompt_manager(
                max_tokens=agent.max_context_tokens,
                system_prompt=agent.system_prompt,
                role_template=agent.role_template
            )
            
            # Restore prompt manager templates
            prompt_manager_state = state.get("prompt_manager")
            if prompt_manager_state and agent.prompt_manager:
                for template_dict in prompt_manager_state.get("templates", []):
                    agent.prompt_manager.add_template(
                        name=template_dict["name"],
                        version=template_dict.get("version", "1.0"),
                        content=template_dict["content"],
                        metadata=template_dict.get("metadata", {})
                    )
                
                # Restore prompt history if available
                prompt_history_path = state_path.parent / f"{agent.agent_id}_prompt_history.json"
                if prompt_history_path.exists() and hasattr(agent.prompt_manager, 'load_history'):
                    agent.prompt_manager.load_history(str(prompt_history_path))
        
        # Restore tools if available
        tools_state = state.get("tools")
        if tools_state and restore_tools:
            from .tools import Tool, ToolParameter, ToolType
            restored_tools = []
            for tool_dict in tools_state:
                tool_name = tool_dict["name"]
                # Get function from restore_tools dict
                if tool_name in restore_tools:
                    tool = Tool(
                        tool_id=tool_dict["tool_id"],
                        name=tool_dict["name"],
                        description=tool_dict["description"],
                        tool_type=ToolType(tool_dict["tool_type"]),
                        function=restore_tools[tool_name],
                        parameters=[ToolParameter(**param) for param in tool_dict.get("parameters", [])],
                        metadata=tool_dict.get("metadata", {}),
                        tags=tool_dict.get("tags", [])
                    )
                    restored_tools.append(tool)
            
            if restored_tools:
                agent.attach_tools(tools=restored_tools)
        
        # Restore memory if persistence path is set
        memory_path = state.get("memory_persistence_path")
        if memory_path:
            agent.memory_persistence_path = memory_path
            agent.attach_memory(memory_path)
            # Memory will auto-load from file if it exists
        
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

