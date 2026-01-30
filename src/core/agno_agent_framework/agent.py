"""
Agno Agent Framework - Core Agent Implementation

Provides the base agent class and agent management functionality.
"""

# Standard library imports
import asyncio
import json
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

# Third-party imports
from pydantic import BaseModel, Field

# Local application/library specific imports
from ..utils.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from ..utils.health_check import HealthCheck, HealthCheckResult, HealthStatus
from .exceptions import (
    AgentConfigurationError,
    AgentExecutionError,
    AgentStateError,
)
from .memory import AgentMemory, MemoryType
from .tools import Tool, ToolExecutor, ToolRegistry

# Import Prompt Context Management (optional dependency)
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
    tenant_id: Optional[str] = None  # Tenant context for multi-tenant SaaS
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

    # Circuit Breaker for external service calls
    circuit_breaker: Optional[CircuitBreaker] = None
    circuit_breaker_config: Optional[CircuitBreakerConfig] = None

    # Health Check
    health_check: Optional[HealthCheck] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    last_active: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    def add_capability(
        self, name: str, description: str, parameters: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a capability to the agent.

        Args:
            name: Capability name
            description: Capability description
            parameters: Optional parameters
        """
        capability = AgentCapability(
            name=name, description=description, parameters=parameters or {}
        )
        self.capabilities.append(capability)

    def add_task(self, task_type: str, parameters: Dict[str, Any], priority: int = 0) -> str:
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
            task_id=task_id, task_type=task_type, parameters=parameters, priority=priority
        )
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda t: t.priority, reverse=True)
        return task_id

    def _validate_tenant_id(self, tenant_id: Optional[str]) -> None:
        """Validate tenant_id matches agent's tenant_id."""
        if tenant_id is not None and self.tenant_id is not None:
            if tenant_id != self.tenant_id:
                from ..utils.error_handler import create_error_with_suggestion

                raise create_error_with_suggestion(
                    AgentConfigurationError,
                    message=f"Tenant ID mismatch: task tenant_id ({tenant_id}) does not match agent tenant_id ({self.tenant_id})",
                    suggestion="Ensure tenant_id matches:\n  - Use the same tenant_id when creating agent and executing tasks\n  - Or omit tenant_id from task to use agent's tenant_id\n  - For multi-tenant systems, verify tenant isolation",
                    agent_id=self.agent_id,
                )

    def _store_task_result_in_memory(self, task: AgentTask, result: Any) -> None:
        """Store task result in memory if auto-persist is enabled."""
        if self.memory and self.auto_persist_memory:
            self.memory.store(
                content=f"Task {task.task_id} result: {result}",
                memory_type=MemoryType.SHORT_TERM,
                importance=0.6,
                metadata={"task_type": task.task_type},
            )

    def _build_error_suggestion(self, error_msg: str) -> str:
        """Build error suggestion based on error message."""
        suggestion = "Common fixes:\n"
        if "timeout" in error_msg.lower():
            suggestion += "  - Increase timeout in gateway configuration\n"
            suggestion += "  - Check network connectivity\n"
        elif "rate limit" in error_msg.lower() or "429" in error_msg:
            suggestion += "  - Implement rate limiting\n"
            suggestion += "  - Reduce request frequency\n"
            suggestion += "  - Use request batching\n"
        elif "api key" in error_msg.lower() or "authentication" in error_msg.lower():
            suggestion += "  - Verify API key is correct\n"
            suggestion += "  - Check API key has required permissions\n"
            suggestion += "  - Ensure API key is not expired\n"
        else:
            suggestion += "  - Check agent configuration\n"
            suggestion += "  - Verify gateway is properly initialized\n"
            suggestion += "  - Review task parameters\n"
        return suggestion

    async def _execute_with_retry(self, task: AgentTask) -> Any:
        """Execute task with retry logic."""
        attempt = 0
        max_attempts = max(1, self.max_retries)

        while attempt < max_attempts:
            try:
                result = await self._execute_task_internal(task)
                self.last_active = datetime.now()
                self._store_task_result_in_memory(task, result)
                return result
            except AgentExecutionError:
                self.status = AgentStatus.ERROR
                raise
            except Exception as e:
                self.status = AgentStatus.ERROR
                attempt += 1
                if attempt < max_attempts:
                    await asyncio.sleep(self.retry_delay)
                    continue

                from ..utils.error_handler import create_error_with_suggestion

                error_msg = str(e)
                suggestion = self._build_error_suggestion(error_msg)
                raise create_error_with_suggestion(
                    AgentExecutionError,
                    message=f"Agent execution failed: {error_msg}",
                    suggestion=suggestion,
                    agent_id=self.agent_id,
                    task_type=task.task_type if task else None,
                    execution_stage="execution",
                    original_error=e,
                )

    async def execute_task(self, task: AgentTask, tenant_id: Optional[str] = None) -> Any:
        """
        Execute a task.

        Args:
            task: Task to execute
            tenant_id: Optional tenant ID for validation (must match agent's tenant_id)

        Returns:
            Task result

        Raises:
            AgentConfigurationError: If tenant_id doesn't match agent's tenant_id
        """
        self._validate_tenant_id(tenant_id)

        if tenant_id is None:
            tenant_id = self.tenant_id

        self.status = AgentStatus.RUNNING
        self.current_task = task

        try:
            return await self._execute_with_retry(task)
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
            return await self._execute_llm_task(task)

        # Default task execution
        return {
            "status": "completed",
            "task_id": task.task_id,
            "result": f"Task {task.task_type} executed",
        }

    async def _execute_llm_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute LLM-based task with tool calling support."""
        base_prompt = task.parameters.get("prompt", "")
        model = task.parameters.get("model", self.llm_model or "gpt-4")

        # Build and record prompt
        final_prompt = self._build_prompt_with_context(
            base_prompt=base_prompt, task=task, task_type=task.task_type
        )
        if self.prompt_manager:
            self.prompt_manager.record_history(final_prompt)

        # Prepare conversation and tools
        messages = [{"role": "user", "content": final_prompt}]
        tools_schema = self._get_tools_schema()

        # Execute tool calling loop
        return await self._tool_calling_loop(task, model, messages, tools_schema, final_prompt)

    def _get_tools_schema(self) -> Optional[List[Dict[str, Any]]]:
        """Get tool schemas if tools are enabled."""
        if self.enable_tool_calling and self.tool_registry:
            return self.tool_registry.get_tools_schema()
        return None

    async def _tool_calling_loop(
        self,
        task: AgentTask,
        model: str,
        messages: List[Dict[str, Any]],
        tools_schema: Optional[List[Dict[str, Any]]],
        final_prompt: str,
    ) -> Dict[str, Any]:
        """Execute the tool calling loop."""
        iteration = 0
        tool_calls_made = []

        while iteration < self.max_tool_iterations:
            response = await self._call_llm(task, model, messages, tools_schema, final_prompt)
            response_text = response.text
            finish_reason = getattr(response, "finish_reason", None)

            function_calls = self._extract_function_calls(response)

            # Return if no function calls
            if not function_calls or finish_reason != "tool_calls":
                messages.append({"role": "assistant", "content": response_text})
                return self._build_task_result(task, response_text, model, response, tool_calls_made, iteration + 1)

            # Execute function calls
            messages.append({"role": "assistant", "content": response_text})
            self._execute_function_calls(task, function_calls, messages, tool_calls_made, iteration)
            iteration += 1

        # Max iterations reached
        return self._build_task_result(
            task, response_text, model, response, tool_calls_made, iteration, "Max tool iterations reached"
        )

    async def _call_llm(
        self,
        task: AgentTask,
        model: str,
        messages: List[Dict[str, Any]],
        tools_schema: Optional[List[Dict[str, Any]]],
        final_prompt: str,
    ) -> Any:
        """Make LLM call with optional tools."""
        llm_kwargs = task.parameters.get("llm_kwargs", {})
        if tools_schema:
            llm_kwargs["tools"] = tools_schema
            llm_kwargs["tool_choice"] = "auto"

        return await self.gateway.generate_async(
            prompt=messages[-1]["content"] if messages else final_prompt,
            model=model,
            messages=messages,
            **llm_kwargs,
        )

    def _execute_function_calls(
        self,
        task: AgentTask,
        function_calls: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
        tool_calls_made: List[Dict[str, Any]],
        iteration: int,
    ) -> None:
        """Execute all function calls from LLM response."""
        for func_call in function_calls:
            tool_name = func_call.get("name", "")
            arguments = func_call.get("arguments", {})

            try:
                self._execute_single_tool(
                    task, tool_name, arguments, messages, tool_calls_made, func_call, iteration
                )
            except Exception as e:
                tool_calls_made.append(
                    {
                        "tool": tool_name,
                        "arguments": arguments,
                        "result": f"Tool execution failed: {str(e)}",
                        "success": False,
                        "error": str(e),
                    }
                )
                raise

    def _execute_single_tool(
        self,
        task: AgentTask,
        tool_name: str,
        arguments: Dict[str, Any],
        messages: List[Dict[str, Any]],
        tool_calls_made: List[Dict[str, Any]],
        func_call: Dict[str, Any],
        iteration: int,
    ) -> None:
        """Execute a single tool call."""
        if not self.tool_executor:
            tool_calls_made.append(
                {
                    "tool": tool_name,
                    "arguments": arguments,
                    "result": "Tool executor not available",
                    "success": False,
                }
            )
            return

        tool_result = self.tool_executor.execute_tool_call(tool_name=tool_name, arguments=arguments)

        # Store tool call info
        tool_calls_made.append(
            {
                "tool": tool_name,
                "arguments": arguments,
                "result": str(tool_result) if not isinstance(tool_result, (dict, list)) else tool_result,
                "success": True,
            }
        )

        # Add tool result to messages
        messages.append(
            {
                "role": "tool",
                "content": json.dumps(tool_result) if isinstance(tool_result, (dict, list)) else str(tool_result),
                "tool_call_id": func_call.get("id", f"call_{iteration}_{len(tool_calls_made)}"),
            }
        )

        # Store in memory
        if self.memory:
            self.memory.store(
                content=f"Tool {tool_name} executed with result: {tool_result}",
                memory_type=MemoryType.SHORT_TERM,
                importance=0.7,
                metadata={"tool_name": tool_name, "task_id": task.task_id},
            )

    def _build_task_result(
        self,
        task: AgentTask,
        result_text: str,
        model: str,
        response: Any,
        tool_calls: List[Dict[str, Any]],
        iterations: int,
        warning: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build the final task result dictionary."""
        result = {
            "status": "completed",
            "task_id": task.task_id,
            "result": result_text,
            "model": response.model if hasattr(response, "model") else model,
            "tool_calls": tool_calls,
            "iterations": iterations,
        }
        if warning:
            result["warning"] = warning
        return result

    def _extract_function_calls(self, response: Any) -> List[Dict[str, Any]]:
        """
        Extract function calls from LLM response.

        Args:
            response: LLM response object

        Returns:
            List of function call dictionaries
        """
        if not hasattr(response, "raw_response"):
            return []

        raw = response.raw_response

        if isinstance(raw, dict):
            return self._extract_from_dict_response(raw)
        elif hasattr(raw, "choices"):
            return self._extract_from_litellm_response(raw)

        return []

    def _extract_from_dict_response(self, raw: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract function calls from dictionary response."""
        function_calls = []
        choices = raw.get("choices", [])

        if not choices:
            return function_calls

        message = choices[0].get("message", {})
        tool_calls = message.get("tool_calls", [])

        for tool_call in tool_calls:
            func_call = {
                "id": tool_call.get("id", ""),
                "name": tool_call.get("function", {}).get("name", ""),
                "arguments": json.loads(tool_call.get("function", {}).get("arguments", "{}")),
            }
            function_calls.append(func_call)

        return function_calls

    def _extract_from_litellm_response(self, raw: Any) -> List[Dict[str, Any]]:
        """Extract function calls from LiteLLM response object."""
        function_calls = []

        if not raw.choices:
            return function_calls

        message = raw.choices[0].message

        if not (hasattr(message, "tool_calls") and message.tool_calls):
            return function_calls

        for tool_call in message.tool_calls:
            func_call = {
                "id": tool_call.id if hasattr(tool_call, "id") else "",
                "name": self._get_tool_name(tool_call),
                "arguments": self._get_tool_arguments(tool_call),
            }
            function_calls.append(func_call)

        return function_calls

    def _get_tool_name(self, tool_call: Any) -> str:
        """Extract tool name from tool call."""
        if hasattr(tool_call, "function") and hasattr(tool_call.function, "name"):
            return tool_call.function.name
        return ""

    def _get_tool_arguments(self, tool_call: Any) -> Dict[str, Any]:
        """Extract tool arguments from tool call."""
        if hasattr(tool_call, "function") and hasattr(tool_call.function, "arguments"):
            return json.loads(tool_call.function.arguments)
        return {}

    def _initialize_prompt_manager(self) -> None:
        """Initialize prompt manager if needed."""
        if not self.use_prompt_management or self.prompt_manager:
            return
        
        if PromptContextManager and create_prompt_manager:
            self.prompt_manager = create_prompt_manager(max_tokens=self.max_context_tokens)
            if self.prompt_manager and self.role_template and self.description:
                self.prompt_manager.add_template(
                    name=self.role_template, version="1.0", content=self.description
                )

    def _build_system_prompt_parts(self) -> List[str]:
        """Build system prompt parts."""
        prompt_parts = []
        if self.system_prompt:
            prompt_parts.append(f"System: {self.system_prompt}")
        return prompt_parts

    def _build_role_prompt_part(self) -> Optional[str]:
        """Build role prompt part from template."""
        if not self.role_template or not self.prompt_manager:
            return None
        
        try:
            role_prompt = self.prompt_manager.render(
                template_name=self.role_template,
                variables={
                    "agent_name": self.name,
                    "agent_id": self.agent_id,
                    "capabilities": ", ".join([cap.name for cap in self.capabilities]),
                    "description": self.description,
                },
            )
            return f"Role: {role_prompt}"
        except (ValueError, KeyError):
            if self.description:
                return f"Role: {self.description}"
            return None

    def _retrieve_memory_context(self, base_prompt: str) -> str:
        """Retrieve relevant context from memory."""
        if not self.memory:
            return ""
        
        relevant_memories = self.memory.retrieve(query=base_prompt, limit=5)
        if not relevant_memories:
            return ""
        
        memory_contents = [mem.content for mem in relevant_memories]
        return "\n".join(memory_contents)

    def _build_context(self, base_prompt: str, task: AgentTask) -> str:
        """Build context from history, memory, and task parameters."""
        if self.prompt_manager and self.prompt_manager.history:
            context = self.prompt_manager.build_context_with_history(base_prompt)
        else:
            context = base_prompt

        context_from_memory = self._retrieve_memory_context(base_prompt)
        if context_from_memory:
            context = f"{context}\n\nRelevant Context:\n{context_from_memory}"

        if task.parameters.get("context"):
            context = f"{context}\n\nAdditional Context:\n{task.parameters.get('context')}"

        return context

    def _enforce_token_budget(self, full_prompt: str) -> str:
        """Enforce token budget by truncating if necessary."""
        if not self.prompt_manager:
            return full_prompt
        
        validation = self.prompt_manager.window.estimate_tokens(full_prompt)
        if validation > (self.max_context_tokens - self.prompt_manager.window.safety_margin):
            return self.prompt_manager.truncate_prompt(
                full_prompt, max_tokens=self.max_context_tokens
            )
        return full_prompt

    def _build_prompt_with_context(self, base_prompt: str, task: AgentTask, task_type: str) -> str:
        """
        Build prompt with context management, system prompts, and memory integration.

        Args:
            base_prompt: Base prompt from task
            task: Task instance
            task_type: Type of task

        Returns:
            Final prompt with context
        """
        self._initialize_prompt_manager()

        if not self.use_prompt_management or not self.prompt_manager:
            return base_prompt

        prompt_parts = self._build_system_prompt_parts()

        role_part = self._build_role_prompt_part()
        if role_part:
            prompt_parts.append(role_part)

        context = self._build_context(base_prompt, task)
        prompt_parts.append(f"Task: {base_prompt}")

        full_prompt = "\n\n".join(prompt_parts)
        if context and context != base_prompt:
            full_prompt = f"{full_prompt}\n\nContext:\n{context}"

        return self._enforce_token_budget(full_prompt)

    def attach_memory(
        self,
        persistence_path: Optional[str] = None,
        tenant_id: Optional[str] = None,
        max_episodic: int = 500,
        max_semantic: int = 2000,
        max_age_days: Optional[int] = 30,
    ) -> None:
        """
        Attach an AgentMemory instance with optional persistence.

        Args:
            persistence_path: Optional path for memory persistence
            tenant_id: Optional tenant ID
            max_episodic: Maximum episodic memory items (default: 500 for ITSM)
            max_semantic: Maximum semantic memory items (default: 2000 for ITSM)
            max_age_days: Optional maximum age in days for automatic cleanup
        """
        self.memory = AgentMemory(
            agent_id=self.agent_id,
            persistence_path=persistence_path or self.memory_persistence_path,
            max_episodic=max_episodic,
            max_semantic=max_semantic,
            max_age_days=max_age_days,
        )

    def attach_tools(
        self, tools: Optional[List[Tool]] = None, registry: Optional[ToolRegistry] = None
    ) -> None:
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
        role_template: Optional[str] = None,
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
            from ..utils.error_handler import create_error_with_suggestion

            raise create_error_with_suggestion(
                AgentConfigurationError,
                message="PromptContextManager is not available",
                suggestion="Install prompt_context_management component:\n  - Ensure it's included in dependencies\n  - Import: from src.core.prompt_context_management import create_prompt_manager\n  - Or pass prompt_manager parameter when creating agent",
                agent_id=self.agent_id,
                config_key="prompt_manager",
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

    def attach_circuit_breaker(self, config: Optional[CircuitBreakerConfig] = None) -> None:
        """
        Attach a circuit breaker to the agent for external service calls.

        Args:
            config: Optional circuit breaker configuration
        """
        self.circuit_breaker_config = config or CircuitBreakerConfig()
        self.circuit_breaker = CircuitBreaker(
            name=f"agent_{self.agent_id}", config=self.circuit_breaker_config
        )

    def attach_health_check(self) -> None:
        """Attach health check to the agent."""
        self.health_check = HealthCheck(name=f"agent_{self.agent_id}")

        # Add default health checks
        def check_gateway_health() -> HealthCheckResult:
            """Check if gateway is available."""
            if not self.gateway:
                return HealthCheckResult(
                    status=HealthStatus.UNHEALTHY, message="Gateway not configured"
                )
            return HealthCheckResult(status=HealthStatus.HEALTHY, message="Gateway available")

        def check_memory_health() -> HealthCheckResult:
            """Check if memory is functioning."""
            if not self.memory:
                return HealthCheckResult(
                    status=HealthStatus.DEGRADED, message="Memory not configured"
                )
            return HealthCheckResult(status=HealthStatus.HEALTHY, message="Memory available")

        def check_status_health() -> HealthCheckResult:
            """Check agent status."""
            if self.status == AgentStatus.ERROR:
                return HealthCheckResult(
                    status=HealthStatus.UNHEALTHY, message="Agent in error state"
                )
            elif self.status == AgentStatus.STOPPED:
                return HealthCheckResult(status=HealthStatus.DEGRADED, message="Agent stopped")
            return HealthCheckResult(
                status=HealthStatus.HEALTHY, message=f"Agent status: {self.status.value}"
            )

        self.health_check.add_check(check_gateway_health)
        self.health_check.add_check(check_memory_health)
        self.health_check.add_check(check_status_health)

    async def get_health(self) -> Dict[str, Any]:
        """
        Get agent health status.

        Returns:
            Dictionary with health information
        """
        if not self.health_check:
            self.attach_health_check()

        if not self.health_check:
            return {
                "name": f"agent_{self.agent_id}",
                "status": "unknown",
                "message": "Health check not available",
            }

        await self.health_check.check()
        health_info = self.health_check.get_health()

        # Add agent-specific metrics
        health_info.update(
            {
                "agent_id": self.agent_id,
                "status": self.status.value,
                "task_queue_size": len(self.task_queue),
                "current_task": self.current_task.task_id if self.current_task else None,
                "last_active": self.last_active.isoformat(),
                "circuit_breaker": (
                    self.circuit_breaker.get_stats() if self.circuit_breaker else None
                ),
            }
        )

        return health_info

    def add_prompt_template(
        self, name: str, version: str, content: str, metadata: Optional[Dict[str, Any]] = None
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
            from ..utils.error_handler import create_error_with_suggestion

            raise create_error_with_suggestion(
                AgentConfigurationError,
                message="Prompt manager is not available",
                suggestion="Initialize prompt manager:\n  - Call agent.attach_prompt_management() first\n  - Or pass prompt_manager when creating agent\n  - Or install prompt_context_management component",
                agent_id=self.agent_id,
                config_key="prompt_manager",
            )

        self.prompt_manager.add_template(
            name=name, version=version, content=content, metadata=metadata
        )

    def send_message(self, to_agent: str, content: Any, message_type: str = "task") -> None:
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
            from_agent=self.agent_id, to_agent=to_agent, content=content, message_type=message_type
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

        # Serialize components
        tools_state = self._serialize_tools()
        prompt_manager_state = self._serialize_prompt_manager()

        # Prepare complete state
        state = self._build_state_dict(tools_state, prompt_manager_state)

        # Write state to file
        with state_path.open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, default=str)

        # Save additional components
        self._save_prompt_history(state_path)

    def _serialize_tools(self) -> Optional[List[Dict[str, Any]]]:
        """Serialize tool registry."""
        if not self.tool_registry:
            return None

        tools_state = []
        for tool in self.tool_registry._tools.values():
            tool_dict = {
                "tool_id": tool.tool_id,
                "name": tool.name,
                "description": tool.description,
                "tool_type": (
                    tool.tool_type.value if hasattr(tool.tool_type, "value") else str(tool.tool_type)
                ),
                "parameters": [param.model_dump() for param in tool.parameters],
                "metadata": tool.metadata,
                "tags": tool.tags,
            }
            tools_state.append(tool_dict)

        return tools_state

    def _serialize_prompt_manager(self) -> Optional[Dict[str, Any]]:
        """Serialize prompt manager state."""
        if not self.prompt_manager:
            return None

        prompt_manager_state = {
            "max_tokens": self.max_context_tokens,
            "templates": [],
            "history_count": (
                len(self.prompt_manager.history) if hasattr(self.prompt_manager, "history") else 0
            ),
        }

        if hasattr(self.prompt_manager, "templates"):
            prompt_manager_state["templates"] = self._serialize_templates()

        return prompt_manager_state

    def _serialize_templates(self) -> List[Dict[str, Any]]:
        """Serialize prompt templates."""
        templates = []
        for template_name, template in self.prompt_manager.templates.items():
            template_dict = {
                "name": template_name,
                "version": template.version if hasattr(template, "version") else "1.0",
                "content": template.content if hasattr(template, "content") else str(template),
                "metadata": template.metadata if hasattr(template, "metadata") else {},
            }
            templates.append(template_dict)
        return templates

    def _build_state_dict(
        self, tools_state: Optional[List[Dict[str, Any]]], prompt_manager_state: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build the complete state dictionary."""
        return {
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
            "memory_persistence_path": (
                str(self.memory_persistence_path) if self.memory_persistence_path else None
            ),
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

    def _save_prompt_history(self, state_path: Any) -> None:
        """Save prompt manager history if available."""
        if self.prompt_manager and hasattr(self.prompt_manager, "save_history"):
            prompt_history_path = state_path.parent / f"{self.agent_id}_prompt_history.json"
            self.prompt_manager.save_history(str(prompt_history_path))

    @classmethod
    def _load_state_file(cls, file_path: str) -> Dict[str, Any]:
        """Load state from file."""
        from pathlib import Path

        state_path = Path(file_path)
        if not state_path.exists():
            raise AgentStateError(
                message=f"Agent state file not found: {file_path}",
                operation="load",
                file_path=file_path,
            )

        with state_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def _create_agent_from_state(
        cls, state: Dict[str, Any], gateway: Optional[Any]
    ) -> "Agent":
        """Create agent instance from state."""
        return cls(
            agent_id=state["agent_id"],
            name=state["name"],
            description=state.get("description", ""),
            gateway=gateway,
            llm_model=state.get("llm_model"),
            llm_provider=state.get("llm_provider"),
        )

    @classmethod
    def _restore_basic_state(cls, agent: "Agent", state: Dict[str, Any]) -> None:
        """Restore basic agent state."""
        agent.capabilities = [AgentCapability(**cap) for cap in state.get("capabilities", [])]
        agent.status = AgentStatus(state.get("status", "idle"))
        agent.task_queue = [AgentTask(**task) for task in state.get("task_queue", [])]
        if state.get("current_task"):
            agent.current_task = AgentTask(**state["current_task"])

    @classmethod
    def _restore_configuration(cls, agent: "Agent", state: Dict[str, Any]) -> None:
        """Restore agent configuration."""
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

    @classmethod
    def _restore_prompt_manager(
        cls, agent: "Agent", state: Dict[str, Any], state_path: Any
    ) -> None:
        """Restore prompt manager and templates."""
        if not agent.use_prompt_management or not PromptContextManager:
            return

        agent.attach_prompt_manager(
            max_tokens=agent.max_context_tokens,
            system_prompt=agent.system_prompt,
            role_template=agent.role_template,
        )

        prompt_manager_state = state.get("prompt_manager")
        if not prompt_manager_state or not agent.prompt_manager:
            return

        for template_dict in prompt_manager_state.get("templates", []):
            agent.prompt_manager.add_template(
                name=template_dict["name"],
                version=template_dict.get("version", "1.0"),
                content=template_dict["content"],
                metadata=template_dict.get("metadata", {}),
            )

        prompt_history_path = state_path.parent / f"{agent.agent_id}_prompt_history.json"
        if prompt_history_path.exists() and hasattr(agent.prompt_manager, "load_history"):
            agent.prompt_manager.load_history(str(prompt_history_path))

    @classmethod
    def _restore_tools(
        cls, agent: "Agent", state: Dict[str, Any], restore_tools: Optional[Dict[str, Callable]]
    ) -> None:
        """Restore tools if available."""
        tools_state = state.get("tools")
        if not tools_state or not restore_tools:
            return

        from .tools import Tool, ToolParameter, ToolType

        restored_tools = []
        for tool_dict in tools_state:
            tool_name = tool_dict["name"]
            if tool_name in restore_tools:
                tool = Tool(
                    tool_id=tool_dict["tool_id"],
                    name=tool_dict["name"],
                    description=tool_dict["description"],
                    tool_type=ToolType(tool_dict["tool_type"]),
                    function=restore_tools[tool_name],
                    parameters=[
                        ToolParameter(**param) for param in tool_dict.get("parameters", [])
                    ],
                    metadata=tool_dict.get("metadata", {}),
                    tags=tool_dict.get("tags", []),
                )
                restored_tools.append(tool)

        if restored_tools:
            agent.attach_tools(tools=restored_tools)

    @classmethod
    def _restore_memory(cls, agent: "Agent", state: Dict[str, Any]) -> None:
        """Restore memory if persistence path is set."""
        memory_path = state.get("memory_persistence_path")
        if memory_path:
            agent.memory_persistence_path = memory_path
            agent.attach_memory(memory_path)

    @classmethod
    def _restore_timestamps(cls, agent: "Agent", state: Dict[str, Any]) -> None:
        """Restore timestamps."""
        from datetime import datetime

        if state.get("created_at"):
            agent.created_at = datetime.fromisoformat(state["created_at"])
        if state.get("last_active"):
            agent.last_active = datetime.fromisoformat(state["last_active"])

    @classmethod
    def load_state(
        cls,
        file_path: str,
        gateway: Optional[Any] = None,
        restore_tools: Optional[Dict[str, Callable]] = None,
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

        state = cls._load_state_file(file_path)
        agent = cls._create_agent_from_state(state, gateway)
        state_path = Path(file_path)

        cls._restore_basic_state(agent, state)
        cls._restore_configuration(agent, state)
        cls._restore_prompt_manager(agent, state, state_path)
        cls._restore_tools(agent, state, restore_tools)
        cls._restore_memory(agent, state)
        cls._restore_timestamps(agent, state)

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
            agent
            for agent in self._agents.values()
            if any(cap.name == capability_name for cap in agent.capabilities)
        ]

    def broadcast_message(
        self, from_agent: str, content: Any, message_type: str = "broadcast"
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

    def send_message_to_agent(
        self, from_agent: str, to_agent: str, content: Any, message_type: str = "message"
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
        return {agent_id: agent.get_status() for agent_id, agent in self._agents.items()}

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
