# MOTADATA - AGENT FRAMEWORK FUNCTIONS

**Documentation of high-level factory functions, convenience functions, and utilities for the Agno Agent Framework.**

## Overview

The `functions.py` file provides high-level factory functions, convenience functions, and utilities for the Agno Agent Framework. These functions simplify agent creation, configuration, and common operations, making it easier for developers to work with agents without directly instantiating the `Agent` class or managing complex configurations.

**Primary Functionality:**
- Factory functions for creating agents with different configurations
- Convenience functions for common agent operations (chat, task execution)
- Agent management utilities (finding agents, batch processing)
- State persistence and recovery functions
- Error handling and retry utilities

## Code Explanation

### Function Categories

The file is organized into several categories:

#### 1. Factory Functions
Factory functions create and configure agents with specific features:

- **`create_agent()`**: Basic agent creation with minimal configuration
- **`create_agent_with_memory()`**: Creates agent with memory pre-configured
- **`create_agent_with_prompt_management()`**: Creates agent with prompt context management
- **`create_agent_with_tools()`**: Creates agent with tools pre-registered

#### 2. Management Functions
Functions for managing multiple agents:

- **`create_agent_manager()`**: Creates an AgentManager for managing multiple agents
- **`create_orchestrator()`**: Creates an AgentOrchestrator for coordinating agents

#### 3. Execution Functions
High-level functions for agent operations:

- **`execute_task()`**: Execute a task with an agent
- **`chat_with_agent()`**: Chat with an agent (conversational interface)
- **`delegate_task()`**: Delegate a task to another agent

#### 4. Utility Functions
Helper functions for common operations:

- **`find_agents_by_capability()`**: Find agents with specific capabilities
- **`batch_process_agents()`**: Process multiple agents in batch
- **`retry_on_failure()`**: Retry decorator for error handling
- **`save_agent_state()`**: Save agent state to disk
- **`load_agent_state()`**: Load agent state from disk

### Key Functions

#### `create_agent(agent_id, name, gateway, **kwargs) -> Agent`
Creates a basic agent with default settings.

**Parameters:**
- `agent_id`: Unique identifier for the agent
- `name`: Human-readable agent name
- `gateway`: LiteLLM Gateway instance (required)
- `tenant_id`: Optional tenant ID for multi-tenant SaaS
- `description`: Optional agent description
- `llm_model`: Optional LLM model name
- `llm_provider`: Optional LLM provider
- `**kwargs`: Additional agent configuration

**Returns:** Configured `Agent` instance

**Example:**
```python
gateway = create_gateway(api_keys={"openai": "key"})
agent = create_agent("agent1", "Assistant", gateway, tenant_id="tenant_123")
```

#### `create_agent_with_memory(agent_id, name, gateway, memory_config, **kwargs) -> Agent`
Creates an agent with memory pre-configured.

**Parameters:**
- `memory_config`: Dictionary with memory configuration:
  - `persistence_path`: Optional path for memory persistence
  - `max_short_term`: Max short-term memories (default: 50)
  - `max_long_term`: Max long-term memories (default: 1000)
  - `max_episodic`: Max episodic memories (default: 500)
  - `max_semantic`: Max semantic memories (default: 2000)

**Returns:** Agent instance with memory attached

**Example:**
```python
agent = create_agent_with_memory(
    "agent1", "Assistant", gateway,
    memory_config={"persistence_path": "/tmp/memory.json", "max_short_term": 100}
)
```

#### `create_agent_with_prompt_management(agent_id, name, gateway, **kwargs) -> Agent`
Creates an agent with prompt context management.

**Parameters:**
- `system_prompt`: Optional system prompt
- `role_template`: Optional role-based template name
- `max_context_tokens`: Maximum tokens for context window (default: 4000)
- `prompt_config`: Optional prompt configuration dict

**Returns:** Agent instance with prompt management attached

#### `create_agent_with_tools(agent_id, name, gateway, tools, **kwargs) -> Agent`
Creates an agent with tools pre-registered.

**Parameters:**
- `tools`: List of `Tool` instances or tool configurations

**Returns:** Agent instance with tools attached

#### `async def chat_with_agent(agent, message, session_id=None, **kwargs) -> Dict[str, Any]`
High-level function for chatting with an agent.

**Parameters:**
- `agent`: Agent instance
- `message`: User message
- `session_id`: Optional session ID (creates new if not provided)
- `**kwargs`: Additional chat parameters

**Returns:** Dictionary with:
- `answer`: Agent response
- `session_id`: Session ID
- `metadata`: Additional metadata

**Example:**
```python
response = await chat_with_agent(agent, "Hello!")
print(response["answer"])
```

#### `async def execute_task(agent, task_type, parameters, **kwargs) -> Dict[str, Any]`
High-level function for executing a task with an agent.

**Parameters:**
- `agent`: Agent instance
- `task_type`: Type of task
- `parameters`: Task parameters dictionary
- `**kwargs`: Additional task parameters

**Returns:** Dictionary with task execution results

#### `find_agents_by_capability(agent_manager, capability_name) -> List[Agent]`
Finds agents with a specific capability.

**Parameters:**
- `agent_manager`: AgentManager instance
- `capability_name`: Name of capability to search for

**Returns:** List of agents with the capability

#### `batch_process_agents(agents, func, *args, **kwargs) -> List[Any]`
Processes multiple agents in batch.

**Parameters:**
- `agents`: List of agent instances
- `func`: Function to apply to each agent
- `*args, **kwargs`: Arguments to pass to function

**Returns:** List of results from processing each agent

## Usage Instructions

### Basic Agent Creation

```python
from src.core.agno_agent_framework import create_agent
from src.core.litellm_gateway import create_gateway

# Create gateway
gateway = create_gateway(api_keys={"openai": "your-api-key"})

# Create basic agent
agent = create_agent(
    agent_id="agent_001",
    name="Customer Support Agent",
    gateway=gateway,
    tenant_id="tenant_123"
)
```

### Creating Agent with Memory

```python
from src.core.agno_agent_framework import create_agent_with_memory

agent = create_agent_with_memory(
    agent_id="agent_002",
    name="Assistant with Memory",
    gateway=gateway,
    memory_config={
        "persistence_path": "/tmp/agent_memory.json",
        "max_short_term": 100,
        "max_long_term": 2000
    }
)
```

### Chatting with Agent

```python
from src.core.agno_agent_framework import chat_with_agent

# Start conversation
response = await chat_with_agent(
    agent,
    "Hello, I need help with my account",
    session_id="session_001"
)

print(f"Agent: {response['answer']}")

# Continue conversation
response = await chat_with_agent(
    agent,
    "Can you check my order status?",
    session_id="session_001"  # Same session for context
)
```

### Executing Tasks

```python
from src.core.agno_agent_framework import execute_task

result = await execute_task(
    agent,
    task_type="analyze",
    parameters={"query": "Analyze customer feedback"}
)

print(f"Task result: {result['result']}")
```

### Finding Agents by Capability

```python
from src.core.agno_agent_framework import create_agent_manager, find_agents_by_capability

manager = create_agent_manager()
# ... add agents to manager ...

# Find agents with specific capability
support_agents = find_agents_by_capability(manager, "customer_support")
```

### Batch Processing

```python
from src.core.agno_agent_framework import batch_process_agents

agents = [agent1, agent2, agent3]

# Process all agents
results = batch_process_agents(
    agents,
    lambda agent: agent.check_health()
)
```

### Prerequisites

1. **Python 3.10+**: Required for type hints and async/await
2. **Dependencies**: Install via `pip install -r requirements.txt`
   - `pydantic`: For data validation
   - `litellm`: For LLM gateway
3. **API Keys**: Configure LLM provider API keys
4. **Gateway Instance**: Must create gateway before creating agents

## Connection to Other Components

### Agent Class
These functions create and configure `Agent` instances from `agent.py`:
- All factory functions return `Agent` instances
- Execution functions use `Agent` methods internally

**Integration Point:** Functions wrap `Agent` class instantiation and methods

### LiteLLM Gateway
All agent creation requires a gateway instance:
- Gateway is passed to factory functions
- Gateway handles all LLM operations

**Integration Point:** `gateway` parameter in all factory functions

### Agent Memory
Memory integration via `create_agent_with_memory()`:
- Uses `AgentMemory` from `memory.py`
- Configures memory persistence and limits

**Integration Point:** `memory_config` parameter

### Prompt Context Management
Prompt management integration via `create_agent_with_prompt_management()`:
- Uses `PromptContextManager` from `prompt_context_management/`
- Configures prompt templates and context windows

**Integration Point:** `prompt_config` parameter

### Tools System
Tool integration via `create_agent_with_tools()`:
- Uses `Tool` and `ToolRegistry` from `tools.py`
- Registers tools with agent

**Integration Point:** `tools` parameter

### Agent Manager
Management functions use `AgentManager` from `agent.py`:
- `create_agent_manager()` creates manager instance
- `find_agents_by_capability()` uses manager to search

**Integration Point:** `AgentManager` class

### Where Used
- **Examples**: All agent examples use these functions
- **API Backend Services**: HTTP endpoints use these functions
- **FaaS Agent Service**: REST API wrapper uses these functions
- **User Applications**: Primary interface for creating agents

## Best Practices

### 1. Use Factory Functions
Always use factory functions instead of directly instantiating `Agent`:
```python
# Good: Use factory function
agent = create_agent("id", "Name", gateway)

# Bad: Direct instantiation (unless you need full control)
agent = Agent(agent_id="id", name="Name", gateway=gateway)
```

### 2. Configure Based on Needs
Use specialized factory functions for specific features:
```python
# Good: Use specialized function if you need memory
agent = create_agent_with_memory("id", "Name", gateway, memory_config={...})

# Bad: Create basic agent then manually configure memory
agent = create_agent("id", "Name", gateway)
agent.attach_memory(...)  # More verbose
```

### 3. Error Handling
Always handle errors when using execution functions:
```python
# Good: Proper error handling
try:
    result = await execute_task(agent, "task_type", {"param": "value"})
except AgentExecutionError as e:
    print(f"Task failed: {e}")
```

### 4. Session Management
Use consistent session IDs for conversations:
```python
# Good: Consistent session ID
session_id = "user_123_session"
response1 = await chat_with_agent(agent, "Hello", session_id=session_id)
response2 = await chat_with_agent(agent, "How are you?", session_id=session_id)

# Bad: Different session IDs (loses context)
response1 = await chat_with_agent(agent, "Hello", session_id="session_1")
response2 = await chat_with_agent(agent, "How are you?", session_id="session_2")
```

### 5. Tenant Isolation
Always provide `tenant_id` for multi-tenant applications:
```python
# Good: Explicit tenant ID
agent = create_agent("id", "Name", gateway, tenant_id="tenant_123")

# Bad: Missing tenant ID in multi-tenant system
agent = create_agent("id", "Name", gateway)
```

### 6. Batch Processing
Use batch processing for multiple agents:
```python
# Good: Batch processing
results = batch_process_agents(agents, check_health)

# Bad: Sequential processing
results = [check_health(agent) for agent in agents]
```

### 7. State Persistence
Save agent state for long-running applications:
```python
# Good: Save state periodically
save_agent_state(agent, "/path/to/state.json")

# Load state on startup
agent = load_agent_state("/path/to/state.json", gateway)
```

## Additional Resources

### Documentation
- **[Agent Class Documentation](agent.md)** - Core Agent class implementation
- **[Agent Framework README](README.md)** - Complete agent framework guide
- **[Agent Troubleshooting](../../../docs/troubleshooting/agent_troubleshooting.md)** - Common issues

### Related Components
- **[Memory System](memory.py)** - Agent memory implementation
- **[Tools System](tools.py)** - Tool integration
- **[Orchestration](orchestration.py)** - Multi-agent coordination
- **[Session Management](session.py)** - Conversation sessions

### External Resources
- **[Python Async/Await](https://docs.python.org/3/library/asyncio.html)** - Asynchronous programming
- **[Factory Pattern](https://refactoring.guru/design-patterns/factory-method)** - Design pattern reference
- **[Pydantic Models](https://docs.pydantic.dev/)** - Data validation

### Examples
- **[Basic Agent Example](../../../../examples/basic_usage/05_agent_basic.py)** - Simple agent usage
- **[Agent with Memory Example](../../../../examples/)** - Memory usage examples
- **[Multi-Agent Example](../../../../examples/)** - Agent coordination

