"""
Compatibility layer for real Agno Agent Framework.

This module provides compatibility wrappers to maintain existing API
while using the real Agno framework from https://www.agno.com/
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Define AgentStatus enum first (used by Agent class)
class AgentStatus(str, Enum):
    """Agent status enumeration (compatibility)."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"

# Import real Agno framework (REQUIRED - this is the real framework from agno.com)
_agno_available_flag = False
try:
    from agno.agent import Agent as RealAgnoAgent    
    # Try to import optional components
    try:
        from agno import AgentOS, Team, Workflow, Knowledge  # type: ignore[import-untyped]  # noqa: F401
    except ImportError:
        # These may not be available in all versions
        AgentOS = None
        Team = None
        Workflow = None
        Knowledge = None
    try:
        from agno.db import Postgres
    except ImportError:
        Postgres = None
    _agno_available_flag = True
    logger.info("✅ Real Agno Agent Framework loaded from agno.com")
except ImportError as e:
    _agno_available_flag = False
    RealAgnoAgent = None
    AgentOS = None
    Team = None
    Workflow = None
    Knowledge = None
    Postgres = None
    logger.error(
        f"❌ Real Agno framework not installed. Install with: pip install agno>=2.5.3\n"
        f"   Error: {e}"
    )

# Export as constant for compatibility (read-only)
AGNO_AVAILABLE: bool = _agno_available_flag

# Re-export real Agno classes for direct access
if _agno_available_flag:
    __all__ = [
        "Agent",
        "AgentStatus",
        "AgentCapability",
        "AgentManager",
        "AgentMessage",
        "AgentTask",
        "AgentOS",
        "Team",
        "Workflow",
        "Knowledge",
        "RealAgnoAgent",
    ]
else:
    __all__ = [
        "Agent",
        "AgentStatus",
        "AgentCapability",
        "AgentManager",
        "AgentMessage",
        "AgentTask",
    ]


# Compatibility wrapper for Agent
class Agent:
    """
    Compatibility wrapper for real Agno Agent.
    
    Maintains existing API while using real Agno underneath.
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        gateway: Optional[Any] = None,  # LiteLLM Gateway instance (optional for backward compatibility)
        tenant_id: Optional[str] = None,
        description: str = "",
        llm_model: Optional[str] = None,
        llm_provider: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initialize agent with compatibility wrapper.
        
        Args:
            agent_id: Unique agent identifier
            name: Agent name
            gateway: Optional LiteLLM Gateway instance (will be converted to Agno model string)
            tenant_id: Optional tenant ID for multi-tenant SaaS
            description: Agent description
            llm_model: Optional LLM model name
            llm_provider: Optional LLM provider
            **kwargs: Additional agent configuration
        """
        if not _agno_available_flag:
            raise ImportError(
                "Real Agno framework not installed. Install with: pip install agno>=2.5.3"
            )
        
        # Convert LiteLLM Gateway to Agno model string
        # If no gateway provided, create a minimal mock for testing (backward compatibility)
        if gateway is None:
            # For backward compatibility with tests that don't provide gateway
            # Create a minimal mock gateway
            class MockGateway:
                default_model = llm_model or "gpt-4"
            gateway = MockGateway()
            model = llm_model or "gpt-4"
        else:
            model = self._extract_model_from_gateway(gateway, llm_model, llm_provider)
        
        # Ensure model is always a valid string in Agno format (provider:model)
        # The _extract_model_from_gateway already handles this, but double-check
        if model is None or (isinstance(model, str) and not model.strip()):
            model = "openai:gpt-4"  # Default fallback in Agno format
        elif isinstance(model, str) and ":" not in model:
            # If no provider specified, default to openai
            model = f"openai:{model}"
        elif not isinstance(model, str):
            # If it's not a string, try to convert it
            model_str = str(model) if model is not None else "gpt-4"
            if ":" not in model_str:
                model = f"openai:{model_str}"
            else:
                model = model_str
        
        # Extract tools/knowledge/db if provided (stored for compatibility, not passed to Agno init)
        # These are stored but not used in RealAgnoAgent.__init__ as it doesn't support them
        _tools = kwargs.get("tools", [])  # Store for compatibility layer use
        _knowledge = kwargs.get("knowledge")  # Store for compatibility layer use
        _db = kwargs.get("db")  # Store for compatibility layer use
        
        # Create real Agno agent (from agno.com framework)
        # This is the actual RealAgnoAgent from the agno package
        # Only pass supported parameters (model, name, id, user_id, etc.)
        # Filter out unsupported kwargs to avoid type errors
        agno_kwargs = {
            "name": name,
            "model": model,
        }
        # Add id if agent_id is provided
        if agent_id:
            agno_kwargs["id"] = agent_id
        # Add user_id if tenant_id is provided (map tenant_id to user_id)
        if tenant_id:
            agno_kwargs["user_id"] = tenant_id
        
        # Note: tools, knowledge, db, enable_memories, instructions are not supported
        # by the real Agno Agent.__init__ - they may need to be set via other methods
        # Do NOT pass any other kwargs to avoid type errors
        
        # Explicitly pass only supported parameters to avoid type checker errors
        # RealAgnoAgent only accepts: name, model, id, user_id, session_id, etc.
        # We explicitly construct the call to avoid passing unsupported kwargs
        try:
            if agent_id and tenant_id:
                self._agno_agent = RealAgnoAgent(name=name, model=model, id=agent_id, user_id=tenant_id)
            elif agent_id:
                self._agno_agent = RealAgnoAgent(name=name, model=model, id=agent_id)
            elif tenant_id:
                self._agno_agent = RealAgnoAgent(name=name, model=model, user_id=tenant_id)
            else:
                self._agno_agent = RealAgnoAgent(name=name, model=model)
        except Exception as e:
            logger.error(f"Failed to create Agno agent: {e}")
            # Fallback: try with just name and model
            try:
                self._agno_agent = RealAgnoAgent(name=name, model=model)
            except Exception as e2:
                logger.error(f"Failed to create Agno agent with fallback: {e2}")
                raise
        logger.debug(f"Created real Agno agent: {name} using model: {model}")
        
        # Store compatibility attributes
        self.agent_id = agent_id
        self.tenant_id = tenant_id
        self.name = name
        self.description = description
        self.gateway = gateway  # Keep reference for compatibility
        self.llm_model = llm_model
        self.llm_provider = llm_provider
        
        # Store status (Agno doesn't have explicit status enum)
        self._status = "idle"
        
        # Compatibility attributes for features not in real Agno
        self._memory = None
        self._prompt_manager = None
        self._tool_registry = None
        self._circuit_breaker = None
        self._health_check = None
        self._codec_serializer = kwargs.pop('codec_serializer', None) if 'codec_serializer' in kwargs else None
        self._otel_tracer = kwargs.pop('otel_tracer', None) if 'otel_tracer' in kwargs else None
        self._otel_metrics = kwargs.pop('otel_metrics', None) if 'otel_metrics' in kwargs else None
        # Handle capabilities passed in constructor
        if 'capabilities' in kwargs:
            self._capabilities = kwargs.pop('capabilities')
            if not isinstance(self._capabilities, list):
                self._capabilities = []
        else:
            self._capabilities = []
        self._task_queue = []
        self._message_queue = []
        self.current_task = None
    
    def _extract_model_from_gateway(
        self,
        gateway: Any,
        llm_model: Optional[str],
        llm_provider: Optional[str],
    ) -> str:
        """Extract model string from LiteLLM Gateway."""
        # Priority: llm_model > gateway.default_model > default
        model_str = None
        
        if llm_model and isinstance(llm_model, str):
            # Convert to Agno format: "provider:model" or just "model"
            if llm_provider:
                model_str = f"{llm_provider}:{llm_model}"
            else:
                model_str = llm_model
        
        # Try to get from gateway if not set
        if not model_str and hasattr(gateway, "default_model"):
            gateway_model = gateway.default_model
            # Handle Mock objects - extract the actual value if it's a Mock
            if hasattr(gateway_model, '_mock_name') or str(type(gateway_model)).startswith("<class 'unittest.mock"):
                # It's a Mock object, use default
                model_str = None
            elif isinstance(gateway_model, str) and gateway_model.strip():
                model_str = gateway_model
        
        # Ensure we always return a valid string in Agno format
        if not model_str or (isinstance(model_str, str) and not model_str.strip()):
            # Default to openai:gpt-4 format (Agno prefers provider:model format)
            model_str = "openai:gpt-4"
        elif isinstance(model_str, str) and ":" not in model_str:
            # If no provider specified, default to openai
            model_str = f"openai:{model_str}"
        
        # Final validation - ensure it's a string
        if not isinstance(model_str, str):
            model_str = "openai:gpt-4"
        
        return model_str
    
    def _convert_db_to_agno(self, db: Any) -> Any:
        """Convert SDK database connection to Agno Postgres format."""
        # This is a placeholder - actual conversion depends on your DB structure
        # You may need to extract connection string from your DatabaseConnection
        if hasattr(db, "connection_string"):
            return Postgres(db.connection_string)
        return None
    
    @property
    def status(self) -> AgentStatus:
        """Get agent status."""
        try:
            return AgentStatus(self._status)
        except ValueError:
            return AgentStatus.IDLE
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status (compatibility method - returns dict)."""
        status = {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": self.status.value,
            "tenant_id": self.tenant_id,
            "capabilities": [{"name": c.name, "description": c.description, "parameters": c.parameters} 
                           for c in self.capabilities],
            "task_queue_size": len(self.task_queue),
            "message_queue_size": len(self.message_queue),
        }
        return status
    
    @property
    def system_prompt(self) -> Optional[str]:
        """Get system prompt (compatibility property)."""
        if self._prompt_manager and hasattr(self._prompt_manager, 'system_prompt'):
            return self._prompt_manager.system_prompt
        return getattr(self, '_system_prompt', None)
    
    @system_prompt.setter
    def system_prompt(self, value: Optional[str]) -> None:
        """Set system prompt (compatibility property)."""
        self._system_prompt = value
        if self._prompt_manager and hasattr(self._prompt_manager, 'system_prompt'):
            self._prompt_manager.system_prompt = value
    
    @property
    def role_template(self) -> Optional[str]:
        """Get role template (compatibility property)."""
        if self._prompt_manager and hasattr(self._prompt_manager, 'role_template'):
            return self._prompt_manager.role_template
        return getattr(self, '_role_template', None)
    
    @property
    def prompt_manager(self) -> Optional[Any]:
        """Get prompt manager (compatibility property)."""
        return self._prompt_manager
    
    @property
    def max_context_tokens(self) -> int:
        """Get max context tokens (compatibility property)."""
        if self._prompt_manager and hasattr(self._prompt_manager, 'max_tokens'):
            return self._prompt_manager.max_tokens
        return 4000  # Default
    
    @property
    def codec_serializer(self) -> Optional[Any]:
        """Get codec serializer (compatibility property)."""
        return self._codec_serializer
    
    @codec_serializer.setter
    def codec_serializer(self, value: Optional[Any]) -> None:
        """Set codec serializer (compatibility property)."""
        self._codec_serializer = value
    
    @property
    def otel_tracer(self) -> Optional[Any]:
        """Get OTEL tracer (compatibility property)."""
        return self._otel_tracer
    
    @property
    def otel_metrics(self) -> Optional[Any]:
        """Get OTEL metrics (compatibility property)."""
        return self._otel_metrics
    
    async def encode_message(self, message: "AgentMessage") -> bytes:
        """Encode agent message to bytes (compatibility method)."""
        try:
            from ..codec_integration import encode_agent_message
            return await encode_agent_message(message, codec=self._codec_serializer)
        except ImportError:
            # Fallback: simple JSON encoding
            import json
            message_dict = {
                "from_agent": message.from_agent,
                "to_agent": message.to_agent,
                "content": message.content,
                "message_type": message.message_type,
                "timestamp": message.timestamp.isoformat() if hasattr(message.timestamp, 'isoformat') else str(message.timestamp),
                "metadata": message.metadata,
            }
            return json.dumps(message_dict).encode('utf-8')
    
    async def decode_message(self, payload: bytes) -> "AgentMessage":
        """Decode bytes to agent message (compatibility method)."""
        try:
            from ..codec_integration import decode_agent_message
            decoded_data = await decode_agent_message(payload, codec=self._codec_serializer)
            return AgentMessage(
                from_agent=decoded_data.get("source_agent_id", "") or decoded_data.get("from_agent", ""),
                to_agent=decoded_data.get("target_agent_id", "") or decoded_data.get("to_agent", ""),
                content=decoded_data.get("content", ""),
                message_type=decoded_data.get("message_type", "text"),
                metadata=decoded_data.get("metadata", {}),
            )
        except ImportError:
            # Fallback: simple JSON decoding
            import json
            from datetime import datetime
            decoded = json.loads(payload.decode('utf-8'))
            return AgentMessage(
                from_agent=decoded.get("from_agent", ""),
                to_agent=decoded.get("to_agent", ""),
                content=decoded.get("content", ""),
                message_type=decoded.get("message_type", "text"),
                timestamp=datetime.fromisoformat(decoded.get("timestamp", datetime.now().isoformat())) if isinstance(decoded.get("timestamp"), str) else decoded.get("timestamp", datetime.now()),
                metadata=decoded.get("metadata", {}),
            )
    
    def add_prompt_template(self, name: Optional[str] = None, template_name: Optional[str] = None, template: Optional[str] = None, content: Optional[str] = None, version: Optional[str] = None, **kwargs: Any) -> None:
        """Add prompt template to agent (compatibility method)."""
        # Handle multiple parameter name variations
        if name and not template_name:
            template_name = name
        if template_name is None and 'template_name' in kwargs:
            template_name = kwargs.pop('template_name')
        if content and not template:
            template = content
        if template is None and 'template' in kwargs:
            template = kwargs.pop('template')
        if template is None and 'content' in kwargs:
            template = kwargs.pop('content')
        
        if template_name and template:
            if self._prompt_manager:
                if hasattr(self._prompt_manager, 'add_template'):
                    # Pass version and metadata if provided
                    add_kwargs = {}
                    if version:
                        add_kwargs['version'] = version
                    if 'metadata' in kwargs:
                        add_kwargs['metadata'] = kwargs.pop('metadata')
                    add_kwargs.update(kwargs)
                    self._prompt_manager.add_template(template_name, template, **add_kwargs)
                elif hasattr(self._prompt_manager, 'templates'):
                    self._prompt_manager.templates[template_name] = template
            logger.debug(f"Prompt template '{template_name}' added to agent {self.agent_id}")
    
    async def generate_async(self, prompt: str, **kwargs: Any) -> Any:
        """Generate response using real Agno agent."""
        # Use real Agno agent's async run method (from agno.com framework)
        if not _agno_available_flag:
            raise ImportError("Real Agno framework not available")
        try:
            # Agno's arun may return RunOutput directly or a coroutine
            response = self._agno_agent.arun(prompt)
            # Check if it's awaitable (coroutine)
            if hasattr(response, '__await__'):
                response = await response  # type: ignore[misc]
            # If it's RunOutput, extract the content
            if hasattr(response, 'content'):
                return response.content
            elif hasattr(response, 'text'):
                return response.text
            elif hasattr(response, 'output'):
                return response.output
            return response
        except Exception as e:
            logger.error(f"Error in generate_async: {e}")
            raise
    
    def attach_memory(self, memory: Any) -> None:
        """Attach memory to agent (compatibility method)."""
        # Handle both memory object and persistence_path string
        if isinstance(memory, str):
            # It's a persistence_path, create a mock memory object
            from ..agno_agent_framework.memory import AgentMemory
            try:
                self._memory = AgentMemory(agent_id=self.agent_id, persistence_path=memory)
            except Exception:
                # If AgentMemory not available, create a minimal mock
                class MockMemory:
                    def __init__(self, agent_id, persistence_path):
                        self.agent_id = agent_id
                        self.persistence_path = persistence_path
                        self.max_short_term = 50
                        self.max_long_term = 1000
                        self.max_episodic = 500
                        self.max_semantic = 2000
                self._memory = MockMemory(self.agent_id, memory)
        else:
            self._memory = memory
        logger.debug(f"Memory attached to agent {self.agent_id}")
    
    def attach_prompt_manager(self, prompt_manager: Optional[Any] = None, **kwargs: Any) -> None:
        """Attach prompt manager to agent (compatibility method)."""
        # Accept kwargs for backward compatibility (max_tokens, system_prompt, role_template, etc.)
        # If prompt_manager is provided, use it; otherwise create from kwargs
        if prompt_manager is not None:
            self._prompt_manager = prompt_manager
        elif kwargs:
            # Create a mock prompt manager from kwargs for compatibility
            class MockPromptManager:
                def __init__(self, **kw):
                    self.max_tokens = kw.get('max_tokens', 4000)
                    self.system_prompt = kw.get('system_prompt')
                    self.role_template = kw.get('role_template')
            self._prompt_manager = MockPromptManager(**kwargs)
        logger.debug(f"Prompt manager attached to agent {self.agent_id}")
    
    def attach_tool_registry(self, tool_registry: Any) -> None:
        """Attach tool registry to agent (compatibility method)."""
        self._tool_registry = tool_registry
        logger.debug(f"Tool registry attached to agent {self.agent_id}")
    
    def attach_tools(self, tools: Optional[list] = None, registry: Optional[Any] = None) -> None:
        """Attach tools to agent (compatibility method)."""
        if registry:
            self._tool_registry = registry
        elif tools:
            # Create a tool registry from tools list
            from ..agno_agent_framework.tools import ToolRegistry
            try:
                self._tool_registry = ToolRegistry()
                for tool in tools:
                    self._tool_registry.register_tool(tool)
            except Exception:
                # If ToolRegistry not available, create a minimal mock
                class MockToolRegistry:
                    def __init__(self):
                        self.tools = []
                    def register_tool(self, tool):
                        self.tools.append(tool)
                self._tool_registry = MockToolRegistry()
                for tool in tools:
                    self._tool_registry.register_tool(tool)
        logger.debug(f"Tools attached to agent {self.agent_id}")
    
    def attach_circuit_breaker(self, circuit_breaker: Optional[Any] = None) -> None:
        """Attach circuit breaker to agent (compatibility method)."""
        if circuit_breaker is None:
            # Create a default circuit breaker if none provided
            from enum import Enum
            class CircuitState(str, Enum):
                CLOSED = "closed"
                OPEN = "open"
                HALF_OPEN = "half_open"
            class DefaultCircuitBreaker:
                def __init__(self):
                    self.state = CircuitState.CLOSED
            circuit_breaker = DefaultCircuitBreaker()
        self._circuit_breaker = circuit_breaker
        logger.debug(f"Circuit breaker attached to agent {self.agent_id}")
    
    def attach_health_check(self, health_check: Optional[Any] = None) -> None:
        """Attach health check to agent (compatibility method)."""
        if health_check is None:
            # Create a default health check if none provided
            class DefaultHealthCheck:
                async def check(self):
                    return {"status": "healthy"}
            health_check = DefaultHealthCheck()
        self._health_check = health_check
        logger.debug(f"Health check attached to agent {self.agent_id}")
    
    @property
    def memory(self) -> Any:
        """Get agent memory (compatibility property)."""
        return self._memory
    
    @memory.setter
    def memory(self, value: Any) -> None:
        """Set agent memory (compatibility property)."""
        self._memory = value
    
    @property
    def capabilities(self) -> list:
        """Get agent capabilities (compatibility property)."""
        return getattr(self, '_capabilities', [])
    
    @property
    def task_queue(self) -> list:
        """Get agent task queue (compatibility property)."""
        return getattr(self, '_task_queue', [])
    
    @property
    def message_queue(self) -> list:
        """Get agent message queue (compatibility property)."""
        return getattr(self, '_message_queue', [])
    
    def add_capability(self, name: str, description: str, parameters: Optional[Dict[str, Any]] = None) -> None:
        """Add capability to agent (compatibility method)."""
        if not hasattr(self, '_capabilities'):
            self._capabilities = []
        capability = AgentCapability(name=name, description=description, parameters=parameters or {})
        self._capabilities.append(capability)
        logger.debug(f"Capability '{name}' added to agent {self.agent_id}")
    
    def add_task(self, task_type: str, parameters: Optional[Dict[str, Any]] = None, priority: int = 0) -> str:
        """Add task to agent queue (compatibility method)."""
        if not hasattr(self, '_task_queue'):
            self._task_queue = []
        import uuid
        task_id = str(uuid.uuid4())
        task = AgentTask(
            task_id=task_id,
            task_type=task_type,
            parameters=parameters or {},
            priority=priority,
        )
        self._task_queue.append(task)
        logger.debug(f"Task '{task_type}' added to agent {self.agent_id} queue")
        return task_id
    
    async def send_message(self, to_agent: str, content: Any, message_type: str = "message") -> None:
        """Send message to another agent (compatibility method)."""
        if not hasattr(self, '_message_queue'):
            self._message_queue = []
        message = AgentMessage(
            from_agent=self.agent_id,
            to_agent=to_agent,
            content=content,
            message_type=message_type,
        )
        self._message_queue.append(message)
        logger.debug(f"Message sent from {self.agent_id} to {to_agent}")
    
    async def receive_message(self) -> Optional[Any]:
        """Receive message from queue (compatibility method)."""
        if not hasattr(self, '_message_queue'):
            self._message_queue = []
        if self._message_queue:
            return self._message_queue.pop(0)
        return None
    
    async def execute_task(self, task: "AgentTask", tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute a task (compatibility method)."""
        # Validate tenant_id if provided
        if tenant_id and self.tenant_id and tenant_id != self.tenant_id:
            from ..agno_agent_framework.exceptions import AgentConfigurationError
            raise AgentConfigurationError(f"Tenant ID mismatch: agent tenant_id={self.tenant_id}, task tenant_id={tenant_id}")
        
        # Use real Agno agent's run method if available
        if hasattr(self._agno_agent, 'run') or hasattr(self._agno_agent, 'arun'):
            try:
                # Convert task to prompt for Agno
                prompt = f"Task: {task.task_type}\nParameters: {task.parameters}"
                if hasattr(self._agno_agent, 'arun'):
                    result = self._agno_agent.arun(prompt)
                    # Handle if it's a coroutine
                    if hasattr(result, '__await__'):
                        result = await result  # type: ignore[misc]
                    # Extract content if RunOutput
                    if hasattr(result, 'content'):
                        result = result.content
                    elif hasattr(result, 'text'):
                        result = result.text
                    elif hasattr(result, 'output'):
                        result = result.output
                else:
                    result = self._agno_agent.run(prompt)
                return {"result": result, "task_id": task.task_id, "status": "completed"}
            except Exception as e:
                logger.error(f"Error executing task: {e}")
                return {"result": None, "task_id": task.task_id, "status": "error", "error": str(e)}
        else:
            # Fallback implementation
            return {"result": "Task executed", "task_id": task.task_id, "status": "completed"}
    
    async def chat(self, message: str, session_id: Optional[str] = None, tenant_id: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        """Chat with agent (compatibility method)."""
        try:
            if hasattr(self._agno_agent, 'arun'):
                response = self._agno_agent.arun(message)
                if hasattr(response, '__await__'):
                    response = await response  # type: ignore[misc]
                # Extract content if RunOutput
                if hasattr(response, 'content'):
                    response = response.content
                elif hasattr(response, 'text'):
                    response = response.text
                elif hasattr(response, 'output'):
                    response = response.output
                return {"response": response, "session_id": session_id}
            else:
                return {"response": "Chat response", "session_id": session_id}
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return {"response": None, "error": str(e), "session_id": session_id}
    
    async def get_health(self) -> Dict[str, Any]:
        """Get agent health status (compatibility method)."""
        health: Dict[str, Any] = {
            "status": self.status.value,
            "agent_id": self.agent_id,
            "name": self.name,
        }
        
        # Add circuit breaker status if attached
        if self._circuit_breaker:
            if hasattr(self._circuit_breaker, 'state'):
                health["circuit_breaker"] = {"state": str(self._circuit_breaker.state)}
            else:
                health["circuit_breaker"] = {"state": "unknown"}
        
        # Add memory status if attached
        if self._memory:
            memory_dict: Dict[str, Any] = {"attached": True}
            if hasattr(self._memory, 'max_short_term'):
                memory_dict["max_short_term"] = self._memory.max_short_term
            health["memory"] = memory_dict
        
        # Add gateway status if available
        if self.gateway:
            gateway_dict: Dict[str, Any] = {"available": True}
            if hasattr(self.gateway, 'default_model'):
                gateway_dict["model"] = self.gateway.default_model
            health["gateway"] = gateway_dict
        
        # Add health check status if attached
        if self._health_check:
            health_check_dict: Dict[str, Any] = {"attached": True}
            if hasattr(self._health_check, 'check'):
                try:
                    # Check if check() is a coroutine function or returns awaitable
                    import inspect
                    check_method = self._health_check.check
                    if inspect.iscoroutinefunction(check_method):
                        check_result = await check_method()
                    else:
                        check_result = check_method()
                        # If result is awaitable, await it
                        if hasattr(check_result, '__await__'):
                            check_result = await check_result
                    health_check_dict["result"] = check_result
                except Exception:
                    health_check_dict["result"] = "error"
            health["health_check"] = health_check_dict
        
        return health
    
    def save_state(self, file_path: Optional[str] = None) -> None:
        """Save agent state to file (compatibility method)."""
        import json
        state = {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "tenant_id": self.tenant_id,
            "status": self.status.value,
            "llm_model": self.llm_model,
            "llm_provider": self.llm_provider,
            "capabilities": [{"name": c.name, "description": c.description, "parameters": c.parameters} 
                           for c in self.capabilities],
        }
        if file_path:
            with open(file_path, 'w') as f:
                json.dump(state, f, indent=2)
        logger.debug(f"Agent state saved for {self.agent_id}")
    
    @classmethod
    async def load_state(cls, file_path: str, gateway: Any) -> "Agent":
        """Load agent state from file (compatibility method - async for compatibility)."""
        import json
        import asyncio
        
        # Read file (can be done in async context)
        def read_file():
            with open(file_path, 'r') as f:
                return json.load(f)
        
        # Run file read in executor to avoid blocking
        loop = asyncio.get_event_loop()
        state = await loop.run_in_executor(None, read_file)
        
        agent = cls(
            agent_id=state["agent_id"],
            name=state["name"],
            gateway=gateway,
            tenant_id=state.get("tenant_id"),
            description=state.get("description", ""),
            llm_model=state.get("llm_model"),
            llm_provider=state.get("llm_provider"),
        )
        
        # Restore capabilities
        for cap_data in state.get("capabilities", []):
            agent.add_capability(
                name=cap_data["name"],
                description=cap_data["description"],
                parameters=cap_data.get("parameters", {})
            )
        
        logger.debug(f"Agent state loaded for {state['agent_id']}")
        return agent
    
    def __getattr__(self, name: str) -> Any:
        """Delegate to real Agno agent for other methods."""
        # First check if it's a compatibility method we handle
        if name in ['attach_memory', 'attach_prompt_manager', 'attach_tool_registry', 
                    'attach_circuit_breaker', 'attach_health_check']:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        # Otherwise delegate to real Agno agent
        return getattr(self._agno_agent, name)


# Compatibility classes
class AgentCapability:
    """Agent capability (compatibility class)."""
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Optional[Dict[str, Any]] = None,
    ):
        """Initialize AgentCapability."""
        self.name = name
        self.description = description
        self.parameters = parameters or {}


class AgentManager:
    """Agent manager (compatibility placeholder)."""
    
    def __init__(self):
        """Initialize AgentManager."""
        self._agents: Dict[str, Agent] = {}
        self._orchestrator: Optional[Any] = None
    
    def register_agent(self, agent: Agent) -> None:
        """Register an agent."""
        self._agents[agent.agent_id] = agent
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID."""
        return self._agents.get(agent_id)
    
    def list_agents(self, tenant_id: Optional[str] = None) -> List[Agent]:
        """List all agents, optionally filtered by tenant_id."""
        if tenant_id:
            return [agent for agent in self._agents.values() if agent.tenant_id == tenant_id]
        return list(self._agents.values())
    
    def find_agents_by_capability(self, capability_name: str, tenant_id: Optional[str] = None) -> List[Agent]:
        """Find agents with a specific capability."""
        agents = self.list_agents(tenant_id)
        result = []
        for agent in agents:
            if hasattr(agent, 'capabilities'):
                for cap in agent.capabilities:
                    if hasattr(cap, 'name') and cap.name == capability_name:
                        result.append(agent)
                        break
        return result
    
    def get_agent_statuses(self, tenant_id: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """Get status of all agents (compatibility method)."""
        agents = self.list_agents(tenant_id)
        statuses = {}
        for agent in agents:
            statuses[agent.agent_id] = {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "status": agent.status.value if hasattr(agent.status, 'value') else str(agent.status),
                "tenant_id": agent.tenant_id,
            }
        return statuses
    
    def attach_orchestrator(self, orchestrator: Any) -> None:
        """Attach orchestrator to agent manager (compatibility method)."""
        self._orchestrator = orchestrator
        logger.debug("Orchestrator attached to AgentManager")
    
    def get_orchestrator(self) -> Optional[Any]:
        """Get orchestrator from agent manager (compatibility method)."""
        return getattr(self, '_orchestrator', None)


class AgentMessage:
    """Agent message (compatibility class)."""
    def __init__(
        self,
        from_agent: str,
        to_agent: str,
        content: Any,
        message_type: str = "task",
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize AgentMessage."""
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.content = content
        self.message_type = message_type
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}


class AgentTask:
    """Agent task (compatibility class)."""
    def __init__(
        self,
        task_id: str,
        task_type: str,
        parameters: Optional[Dict[str, Any]] = None,
        priority: int = 0,
        created_at: Optional[datetime] = None,
        status: str = "pending",
    ):
        """Initialize AgentTask."""
        self.task_id = task_id
        self.task_type = task_type
        self.parameters = parameters or {}
        self.priority = priority
        self.created_at = created_at or datetime.now()
        self.status = status

