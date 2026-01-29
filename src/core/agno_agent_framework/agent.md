# Motadata Agent Class Documentation

## Overview

The `agent.py` file contains the core `Agent` class implementation for the Agno Agent Framework. This class provides the foundation for creating autonomous AI agents that can execute tasks, manage memory, communicate with other agents, and coordinate complex workflows. The Agent class is designed to be flexible, extensible, and production-ready with built-in error handling, health monitoring, and circuit breaker patterns.

**Primary Functionality:**
- Agent lifecycle management (creation, execution, state management)
- Task execution and orchestration
- Memory management (short-term and long-term)
- Inter-agent communication
- Tool integration and execution
- Health monitoring and circuit breaking
- Session management for conversational interactions

## Code Explanation

### Class Structure

#### `AgentStatus` (Enum)
Defines the possible states an agent can be in:
- `IDLE`: Agent is ready but not executing
- `RUNNING`: Agent is actively executing a task
- `PAUSED`: Agent execution is paused
- `STOPPED`: Agent has been stopped
- `ERROR`: Agent encountered an error

#### `AgentCapability` (BaseModel)
Represents a capability that an agent can perform:
- `name`: Capability identifier
- `description`: Human-readable description
- `parameters`: Configuration parameters for the capability

#### `AgentMessage` (BaseModel)
Represents messages between agents for inter-agent communication:
- `from_agent`: Source agent ID
- `to_agent`: Destination agent ID
- `content`: Message payload
- `message_type`: Type of message (task, response, etc.)
- `timestamp`: When the message was created
- `metadata`: Additional message metadata

#### `AgentTask` (BaseModel)
Represents a task that can be executed by an agent:
- `task_id`: Unique task identifier
- `task_type`: Type of task
- `parameters`: Task-specific parameters
- `priority`: Task priority (higher = more important)
- `created_at`: Task creation timestamp
- `status`: Current task status

#### `Agent` (BaseModel)
The main agent class with the following key components:

**Core Attributes:**
- `agent_id`: Unique identifier for the agent
- `tenant_id`: Multi-tenant support for SaaS environments
- `name`: Human-readable agent name
- `description`: Agent description
- `capabilities`: List of agent capabilities
- `status`: Current agent status

**LLM Configuration:**
- `llm_model`: LLM model to use (e.g., "gpt-4")
- `llm_provider`: LLM provider (e.g., "openai")
- `gateway`: LiteLLM Gateway instance for LLM calls

**Memory Management:**
- `memory`: AgentMemory instance for storing context
- `memory_persistence_path`: Path for persisting memory to disk

**Communication:**
- `message_queue`: Queue for inter-agent messages
- `communication_enabled`: Whether agent can communicate with others

**Tools and Plugins:**
- `tools`: List of tools available to the agent
- `tool_registry`: ToolRegistry for managing tools
- `plugins`: List of plugins extending agent functionality

**Monitoring and Resilience:**
- `circuit_breaker`: CircuitBreaker for fault tolerance
- `health_check`: HealthCheck for monitoring agent health

### Key Methods

#### `execute_task(task: AgentTask) -> Dict[str, Any]`
Executes a task assigned to the agent. This is the primary method for agent task execution.

**Process:**
1. Validates task and agent state
2. Updates agent status to RUNNING
3. Processes task based on task_type
4. Uses LLM gateway for AI operations
5. Updates memory with execution context
6. Returns execution results
7. Handles errors with circuit breaker

**Returns:** Dictionary with execution results, status, and metadata

#### `chat(message: str, session_id: Optional[str] = None) -> Dict[str, Any]`
Handles conversational interactions with the agent.

**Process:**
1. Creates or retrieves session
2. Loads conversation history from memory
3. Generates response using LLM
4. Updates memory with new conversation
5. Returns response and session information

**Returns:** Dictionary with agent response, session_id, and metadata

#### `add_tool(tool: Tool) -> None`
Adds a tool to the agent's tool registry.

**Process:**
1. Validates tool
2. Registers tool in tool_registry
3. Updates agent capabilities

#### `send_message(to_agent: str, content: Any, message_type: str = "task") -> None`
Sends a message to another agent.

**Process:**
1. Creates AgentMessage
2. Validates communication is enabled
3. Adds message to target agent's message queue

#### `check_health() -> HealthCheckResult`
Performs health check on the agent.

**Checks:**
- Agent status
- Gateway connectivity
- Memory availability
- Circuit breaker state

**Returns:** HealthCheckResult with status and details

## Usage Instructions

### Basic Agent Creation

```python
from src.core.agno_agent_framework.agent import Agent, AgentStatus
from src.core.litellm_gateway import create_gateway

# Create gateway
gateway = create_gateway(api_keys={"openai": "your-api-key"})

# Create agent
agent = Agent(
    agent_id="agent_001",
    name="Customer Support Agent",
    description="Handles customer support inquiries",
    gateway=gateway,
    llm_model="gpt-4",
    llm_provider="openai"
)

# Agent is ready to use
print(f"Agent status: {agent.status}")
```

### Executing a Task

```python
from src.core.agno_agent_framework.agent import AgentTask

# Create a task
task = AgentTask(
    task_id="task_001",
    task_type="analyze",
    parameters={"query": "Analyze customer feedback"},
    priority=5
)

# Execute task
result = await agent.execute_task(task)
print(f"Task result: {result['result']}")
```

### Chat Interaction

```python
# Start a conversation
response = await agent.chat(
    message="Hello, I need help with my account",
    session_id="session_001"
)

print(f"Agent: {response['response']}")
print(f"Session ID: {response['session_id']}")

# Continue conversation
response = await agent.chat(
    message="Can you check my order status?",
    session_id="session_001"  # Same session for context
)
```

### Adding Tools

```python
from src.core.agno_agent_framework.tools import Tool

# Create a tool
def calculate_priority(urgency: int, impact: int) -> int:
    return urgency * impact

tool = Tool(
    tool_id="calc_priority",
    name="Calculate Priority",
    description="Calculates priority based on urgency and impact",
    function=calculate_priority
)

# Add tool to agent
agent.add_tool(tool)

# Agent can now use this tool in task execution
```

### Health Monitoring

```python
# Check agent health
health = agent.check_health()

if health.status == "healthy":
    print("Agent is healthy")
else:
    print(f"Health issues: {health.details}")
```

### Prerequisites

1. **Python 3.10+**: Required for type hints and async/await
2. **Dependencies**: Install via `pip install -r requirements.txt`
   - `pydantic`: For data validation
   - `litellm`: For LLM gateway (via gateway module)
3. **API Keys**: Configure LLM provider API keys
4. **Memory Backend** (optional): For persistent memory storage

## Connection to Other Components

### LiteLLM Gateway
The Agent uses the LiteLLM Gateway (`src/core/litellm_gateway/`) for all LLM operations:
- Text generation for task execution
- Chat completions for conversational interactions
- Embeddings for memory operations (if needed)

**Integration Point:** `agent.gateway` attribute

### Agent Memory
The Agent uses `AgentMemory` (`src/core/agno_agent_framework/memory.py`) for:
- Storing conversation history
- Maintaining context across tasks
- Long-term memory persistence

**Integration Point:** `agent.memory` attribute

### Tools System
The Agent integrates with the Tools system (`src/core/agno_agent_framework/tools.py`):
- Tool registration via `ToolRegistry`
- Tool execution via `ToolExecutor`
- Dynamic tool discovery

**Integration Point:** `agent.tool_registry` and `agent.tools`

### Prompt Context Management
Optional integration with Prompt Context Management (`src/core/prompt_context_management/`):
- Dynamic prompt building
- Context-aware prompt generation
- Template management

**Integration Point:** `agent.prompt_manager` (optional)

### Circuit Breaker
Uses Circuit Breaker pattern (`src/core/utils/circuit_breaker.py`) for:
- Fault tolerance
- Automatic recovery
- Failure detection

**Integration Point:** `agent.circuit_breaker`

### Health Check
Uses Health Check system (`src/core/utils/health_check.py`) for:
- Service health monitoring
- Dependency checking
- Status reporting

**Integration Point:** `agent.health_check`

### Where Used
- **Agent Framework Functions** (`src/core/agno_agent_framework/functions.py`): Factory functions create Agent instances
- **FaaS Agent Service** (`src/faas/services/agent_service/`): REST API wrapper for Agent
- **API Backend Services** (`src/core/api_backend_services/`): HTTP endpoints for agent operations
- **Examples**: All agent examples use this class

## Best Practices

### 1. Agent Initialization
- Always provide a unique `agent_id`
- Set appropriate `tenant_id` for multi-tenant environments
- Configure `gateway` before executing tasks
- Initialize memory if persistent context is needed

```python
# Good: Complete initialization
agent = Agent(
    agent_id="unique_id",
    tenant_id="tenant_123",
    name="My Agent",
    gateway=gateway,
    memory=AgentMemory(memory_type=MemoryType.BOUNDED)
)

# Bad: Missing required components
agent = Agent(agent_id="id", name="Agent")  # No gateway!
```

### 2. Error Handling
- Always check agent status before execution
- Handle `AgentExecutionError` exceptions
- Use circuit breaker for resilience
- Monitor health regularly

```python
# Good: Proper error handling
try:
    if agent.status == AgentStatus.IDLE:
        result = await agent.execute_task(task)
    else:
        print(f"Agent not ready: {agent.status}")
except AgentExecutionError as e:
    print(f"Execution failed: {e}")
    # Handle error appropriately
```

### 3. Memory Management
- Use bounded memory for production
- Persist memory for long-running agents
- Clear memory when appropriate
- Monitor memory usage

```python
# Good: Memory management
agent.memory = AgentMemory(
    memory_type=MemoryType.BOUNDED,
    max_entries=1000
)
agent.memory_persistence_path = "/path/to/memory.json"
```

### 4. Task Design
- Use descriptive task types
- Include all necessary parameters
- Set appropriate priorities
- Track task status

```python
# Good: Well-structured task
task = AgentTask(
    task_id=f"task_{uuid4()}",
    task_type="customer_support_analysis",
    parameters={
        "ticket_id": "12345",
        "category": "billing",
        "priority": "high"
    },
    priority=8
)
```

### 5. Tool Integration
- Validate tools before adding
- Document tool parameters
- Handle tool execution errors
- Use tool registry for management

```python
# Good: Tool validation
if tool.validate():
    agent.add_tool(tool)
else:
    raise ValueError("Invalid tool")
```

### 6. Health Monitoring
- Check health before critical operations
- Monitor health in production
- Handle unhealthy states gracefully
- Log health check results

```python
# Good: Health monitoring
health = agent.check_health()
if health.status != "healthy":
    # Alert or handle unhealthy state
    logger.warning(f"Agent unhealthy: {health.details}")
```

### 7. Code Style
- Follow PEP 8 style guide
- Use type hints for all methods
- Document complex logic
- Use async/await properly for async operations

## Additional Resources

### Documentation
- **[Agent Framework README](../agno_agent_framework/README.md)** - Complete agent framework guide
- **[Agent Functions Documentation](functions.md)** - Factory and convenience functions
- **[Agent Troubleshooting](../../../docs/troubleshooting/agent_troubleshooting.md)** - Common issues and solutions

### Related Components
- **[Memory System](memory.py)** - Agent memory implementation
- **[Tools System](tools.py)** - Tool integration
- **[Orchestration](orchestration.py)** - Multi-agent coordination
- **[LiteLLM Gateway](../../litellm_gateway/README.md)** - LLM operations

### External Resources
- **[Pydantic Documentation](https://docs.pydantic.dev/)** - Data validation framework
- **[Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)** - Fault tolerance pattern
- **[Async/Await in Python](https://docs.python.org/3/library/asyncio.html)** - Asynchronous programming

### Examples
- **[Basic Agent Example](../../../../examples/basic_usage/05_agent_basic.py)** - Simple agent usage
- **[Agent with Tools Example](../../../../examples/)** - Tool integration examples
- **[Multi-Agent Example](../../../../examples/)** - Inter-agent communication

### Best Practices References
- **[Python Type Hints](https://docs.python.org/3/library/typing.html)** - Type annotation guide
- **[PEP 8 Style Guide](https://pep8.org/)** - Python code style
- **[Async Best Practices](https://docs.python.org/3/library/asyncio-dev.html)** - Async programming guidelines

