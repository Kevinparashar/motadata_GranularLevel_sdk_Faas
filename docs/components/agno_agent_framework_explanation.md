# MOTADATA - AGNO AGENT FRAMEWORK

**Comprehensive explanation of the Agno Agent Framework for creating, managing, and orchestrating autonomous AI agents with task execution, memory management, and tool integration.**

## Overview

The Agno Agent Framework is a comprehensive system for creating, managing, and orchestrating autonomous AI agents. It provides a complete infrastructure for building multi-agent systems with capabilities including task execution, memory management, tool integration, session handling, and complex workflow orchestration.

**Agent Framework Architecture Diagram:**

```
┌─────────────────────────────────────────────────────────────────┐
│                      AGENT FRAMEWORK                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Agent Instance                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            │                                     │
│        ┌───────────────────┼───────────────────┐               │
│        │                   │                   │               │
│        ▼                   ▼                   ▼               │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐              │
│  │ Memory   │      │  Tools  │      │ Session │              │
│  │ System   │      │Registry │      │ Manager │              │
│  │          │      │         │      │         │              │
│  │- Short   │      │         │      │         │              │
│  │- Long    │      │         │      │         │              │
│  │- Episodic│      │         │      │         │              │
│  │- Semantic│      │         │      │         │              │
│  └──────────┘      └──────────┘      └──────────┘              │
│        │                   │                   │               │
│        └───────────────────┼───────────────────┘               │
│                            │                                     │
│                            ▼                                     │
│                  ┌──────────────────┐                            │
│                  │   Orchestrator   │                            │
│                  └──────────────────┘                            │
│                            │                                     │
│        ┌───────────────────┼───────────────────┐               │
│        │                   │                   │               │
│        ▼                   ▼                   ▼               │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐              │
│  │ Agent 1  │◄────►│ Agent 2  │◄────►│ Agent N  │              │
│  │          │      │          │      │          │              │
│  │ Messages │      │ Messages │      │ Messages │              │
│  └──────────┘      └──────────┘      └──────────┘              │
└─────────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Gateway    │    │  RAG System │    │  Database    │
│  (LiteLLM)   │    │             │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│    Cache     │    │     NATS     │    │              │
│              │    │   Messaging  │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
```

## Table of Contents

1. [Agents](#agents)
2. [Memory Management](#memory-management)
3. [Exception Handling](#exception-handling)
4. [Functions](#functions)
5. [Orchestration](#orchestration)
6. [Workflow](#workflow)
7. [Customization](#customization)

---

## Agents

### Functionality

Agents are autonomous entities within the framework that can:
- Execute tasks based on their capabilities
- Communicate with other agents through message passing
- Maintain state and context across task executions
- Use tools to extend their capabilities
- Store and retrieve information from memory
- Coordinate with other agents to accomplish complex goals

### Roles and Interactions

#### Agent Roles

1. **Task Executor**: Agents execute tasks based on their defined capabilities
2. **Communicator**: Agents send and receive messages from other agents
3. **Memory Manager**: Agents store and retrieve information from their memory systems
4. **Tool User**: Agents can use tools to extend their capabilities
5. **Workflow Participant**: Agents participate in multi-agent workflows

#### Agent Interactions

- **Agent-to-Agent Communication**: Agents communicate through the `AgentManager` using `AgentMessage` objects
- **Task Delegation**: Agents can delegate tasks to other agents
- **Workflow Coordination**: Agents coordinate through the `AgentOrchestrator` for complex workflows
- **Resource Sharing**: Agents can share information through memory and message passing

### Code Examples

#### Creating a Basic Agent

```python
from src.core.agno_agent_framework import create_agent
from src.core.litellm_gateway import LiteLLMGateway

# Initialize gateway
gateway = LiteLLMGateway(
    api_key="your-api-key",
    provider="openai"
)

# Create a basic agent
agent = create_agent(
    agent_id="agent_001",
    name="Assistant Agent",
    gateway=gateway,
    tenant_id="tenant_123",
    description="A helpful assistant agent"
)

# Add capabilities
from src.core.agno_agent_framework.agent import AgentCapability

agent.capabilities.append(
    AgentCapability(
        name="text_analysis",
        description="Analyze and process text content",
        parameters={"max_length": 1000}
    )
)
```

#### Agent Task Execution

```python
from src.core.agno_agent_framework.agent import AgentTask

# Create a task
task = AgentTask(
    task_id="task_001",
    task_type="llm_query",
    parameters={
        "prompt": "Explain quantum computing",
        "model": "gpt-4"
    },
    priority=1
)

# Add task to agent
agent.add_task(task)

# Execute task
result = await agent.execute_task(task, tenant_id="tenant_123")
print(f"Task result: {result}")
```

#### Agent Communication

```python
from src.core.agno_agent_framework.agent import AgentManager, AgentMessage

# Create agent manager
manager = AgentManager()

# Register agents
manager.register_agent(agent1)
manager.register_agent(agent2)

# Send message between agents
message = AgentMessage(
    from_agent="agent_001",
    to_agent="agent_002",
    content="Please analyze this data",
    message_type="task_request"
)

manager.send_message(message)

# Receive messages
messages = agent2.get_messages()
for msg in messages:
    print(f"From {msg.from_agent}: {msg.content}")
```

#### Agent with Tools

```python
from src.core.agno_agent_framework.tools import Tool, ToolType

# Define a tool function
def calculate_sum(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

# Create tool
calculator_tool = Tool(
    tool_id="calc_sum",
    name="calculate_sum",
    description="Adds two numbers together",
    tool_type=ToolType.FUNCTION,
    function=calculate_sum
)

# Attach tool to agent
agent.attach_tools([calculator_tool], enable_tool_calling=True)

# Execute task with tool calling
task = AgentTask(
    task_id="task_002",
    task_type="llm_query",
    parameters={
        "prompt": "What is 5 + 3? Use the calculator tool.",
        "model": "gpt-4"
    }
)

result = await agent.execute_task(task)
# Agent will automatically call the calculator tool when needed
```

---

## Memory Management

### Functionality

The memory management system handles memory allocation and management for optimal performance. It provides:

- **Bounded Memory**: Limits on episodic and semantic memory to prevent memory leaks
- **Automatic Cleanup**: Time-based expiration and automatic trimming
- **Memory Types**: Short-term, long-term, episodic, and semantic memory
- **Persistence**: Optional persistence to disk for long-term storage
- **Memory Pressure Handling**: Proactive management when memory usage is high

### Memory Types

1. **Short-Term Memory**: Working memory for current task context (default: 50 items)
2. **Long-Term Memory**: Persistent memory for important information (default: 1000 items)
3. **Episodic Memory**: Event-based memory for specific experiences (default: 500 items, bounded)
4. **Semantic Memory**: Knowledge-based memory for general facts (default: 2000 items, bounded)

### Code Examples

#### Creating Agent with Memory

```python
from src.core.agno_agent_framework import create_agent_with_memory

# Create agent with memory configuration
agent = create_agent_with_memory(
    agent_id="agent_001",
    name="Memory Agent",
    gateway=gateway,
    tenant_id="tenant_123",
    memory_config={
        "persistence_path": "/tmp/agent_memory.json",
        "max_short_term": 50,
        "max_long_term": 1000,
        "max_episodic": 500,  # Bounded for ITSM ticket history
        "max_semantic": 2000,  # Bounded for knowledge patterns
        "max_age_days": 30  # Auto-cleanup after 30 days
    }
)
```

#### Storing Memories

```python
from src.core.agno_agent_framework.memory import MemoryType

# Store short-term memory
memory_item = agent.memory.store(
    content="User asked about password reset",
    memory_type=MemoryType.SHORT_TERM,
    importance=0.7,
    metadata={"user_id": "user_123", "timestamp": "2024-01-01"}
)

# Store episodic memory (ticket history)
episodic_memory = agent.memory.store(
    content="Resolved ticket #12345: Password reset issue",
    memory_type=MemoryType.EPISODIC,
    importance=0.9,
    tags=["ticket", "resolved", "password"]
)

# Store semantic memory (knowledge pattern)
semantic_memory = agent.memory.store(
    content="Password reset process: 1. Verify identity 2. Send reset link 3. Confirm reset",
    memory_type=MemoryType.SEMANTIC,
    importance=0.8,
    tags=["knowledge", "process", "password"]
)
```

#### Retrieving Memories

```python
# Retrieve relevant memories
memories = agent.memory.retrieve(
    query="password reset process",
    memory_type=MemoryType.SEMANTIC,
    limit=5
)

for memory in memories:
    print(f"Memory: {memory.content}")
    print(f"Importance: {memory.importance}")
    print(f"Tags: {memory.tags}")
```

#### Memory Cleanup

```python
# Automatic cleanup of expired memories
removed_count = agent.memory.cleanup_expired(max_age_days=7)
print(f"Removed {removed_count} expired memories")

# Check memory pressure
pressure = agent.memory.check_memory_pressure()
if pressure["under_pressure"]:
    print(f"Memory pressure detected: {pressure['usage_percent']}%")
    # Handle memory pressure
    agent.memory.handle_memory_pressure()
```

#### Memory Persistence

```python
# Save memory to disk
agent.memory.save()

# Load memory from disk (automatic on initialization)
# Memory is automatically loaded if persistence_path exists
```

---

## Exception Handling

### Exception Hierarchy

The framework uses a structured exception hierarchy for granular error handling:

```
SDKError (Base)
├── AgentError
│   ├── AgentExecutionError
│   ├── AgentConfigurationError
│   └── AgentStateError
├── ToolError
│   ├── ToolInvocationError
│   ├── ToolNotFoundError
│   ├── ToolNotImplementedError
│   └── ToolValidationError
├── MemoryError
│   ├── MemoryReadError
│   ├── MemoryWriteError
│   └── MemoryPersistenceError
└── OrchestrationError
    ├── WorkflowNotFoundError
    └── AgentNotFoundError
```

### Exception Types and Usage

#### Agent Execution Errors

```python
from src.core.agno_agent_framework.exceptions import (
    AgentExecutionError,
    AgentConfigurationError,
    AgentStateError
)

try:
    result = await agent.execute_task(task)
except AgentExecutionError as e:
    print(f"Agent {e.agent_id} failed during {e.execution_stage}")
    print(f"Task type: {e.task_type}")
    print(f"Error: {e.message}")
    if e.original_error:
        print(f"Original error: {e.original_error}")
except AgentConfigurationError as e:
    print(f"Configuration error for agent {e.agent_id}")
    print(f"Invalid config key: {e.config_key}")
except AgentStateError as e:
    print(f"State operation failed for agent {e.agent_id}")
    print(f"Operation: {e.operation}")
    print(f"File path: {e.file_path}")
```

#### Tool Errors

```python
from src.core.agno_agent_framework.exceptions import (
    ToolInvocationError,
    ToolNotFoundError,
    ToolNotImplementedError,
    ToolValidationError
)

try:
    result = tool.execute(a=5, b=3)
except ToolNotFoundError as e:
    print(f"Tool '{e.tool_name}' not found")
except ToolNotImplementedError as e:
    print(f"Tool '{e.tool_name}' is not implemented")
except ToolValidationError as e:
    print(f"Tool '{e.tool_name}' validation failed")
    print(f"Missing parameters: {e.missing_parameters}")
except ToolInvocationError as e:
    print(f"Tool '{e.tool_name}' execution failed")
    print(f"Error type: {e.error_type}")
    print(f"Arguments: {e.arguments}")
```

#### Memory Errors

```python
from src.core.agno_agent_framework.exceptions import (
    MemoryReadError,
    MemoryWriteError,
    MemoryPersistenceError
)

try:
    memory_item = agent.memory.store(content="Test")
except MemoryWriteError as e:
    print(f"Memory write failed for agent {e.agent_id}")
    print(f"Memory type: {e.memory_type}")
    print(f"Operation: {e.operation}")

try:
    memories = agent.memory.retrieve(query="test")
except MemoryReadError as e:
    print(f"Memory read failed for agent {e.agent_id}")
    print(f"Memory ID: {e.memory_id}")
    print(f"Operation: {e.operation}")

try:
    agent.memory.save()
except MemoryPersistenceError as e:
    print(f"Memory persistence failed for agent {e.agent_id}")
    print(f"File path: {e.file_path}")
    print(f"Operation: {e.operation}")
```

#### Orchestration Errors

```python
from src.core.agno_agent_framework.exceptions import (
    OrchestrationError,
    WorkflowNotFoundError,
    AgentNotFoundError
)

try:
    result = await orchestrator.execute_workflow("workflow_001")
except WorkflowNotFoundError as e:
    print(f"Workflow '{e.workflow_id}' not found")
except AgentNotFoundError as e:
    print(f"Agent '{e.agent_id}' not found in orchestrator")
except OrchestrationError as e:
    print(f"Orchestration failed for workflow {e.workflow_id}")
    print(f"Agent: {e.agent_id}")
    print(f"Operation: {e.operation}")
```

### Best Practices

1. **Catch Specific Exceptions**: Catch specific exception types for better error handling
2. **Log Original Errors**: Always log `original_error` for debugging
3. **Handle Gracefully**: Provide fallback behavior when exceptions occur
4. **Validate Input**: Validate inputs before operations to prevent exceptions
5. **Use Context**: Include context information (agent_id, task_type, etc.) in error messages

---

## Functions

### Factory Functions

Factory functions simplify agent creation and configuration:

#### `create_agent()`

Creates a basic agent with default settings.

```python
from src.core.agno_agent_framework import create_agent

agent = create_agent(
    agent_id="agent_001",
    name="Assistant",
    gateway=gateway,
    tenant_id="tenant_123",
    description="A helpful assistant",
    llm_model="gpt-4",
    llm_provider="openai"
)
```

#### `create_agent_with_memory()`

Creates an agent with memory pre-configured.

```python
from src.core.agno_agent_framework import create_agent_with_memory

agent = create_agent_with_memory(
    agent_id="agent_001",
    name="Memory Agent",
    gateway=gateway,
    tenant_id="tenant_123",
    memory_config={
        "persistence_path": "/tmp/memory.json",
        "max_episodic": 500,
        "max_semantic": 2000,
        "max_age_days": 30
    }
)
```

#### `create_agent_with_prompt_management()`

Creates an agent with prompt context management pre-configured.

```python
from src.core.agno_agent_framework import create_agent_with_prompt_management

agent = create_agent_with_prompt_management(
    agent_id="agent_001",
    name="Prompt Agent",
    gateway=gateway,
    tenant_id="tenant_123",
    system_prompt="You are a helpful AI assistant.",
    role_template="assistant_role",
    max_context_tokens=8000
)
```

#### `create_agent_with_tools()`

Creates an agent with tools pre-configured.

```python
from src.core.agno_agent_framework import create_agent_with_tools
from src.core.agno_agent_framework.tools import Tool, ToolType

def get_weather(location: str) -> str:
    return f"Weather in {location}: Sunny, 25°C"

weather_tool = Tool(
    tool_id="weather",
    name="get_weather",
    description="Get weather information",
    tool_type=ToolType.FUNCTION,
    function=get_weather
)

agent = create_agent_with_tools(
    agent_id="agent_001",
    name="Tool Agent",
    gateway=gateway,
    tenant_id="tenant_123",
    tools=[weather_tool],
    enable_tool_calling=True,
    max_tool_iterations=10
)
```

#### `create_agent_manager()`

Creates an AgentManager for managing multiple agents.

```python
from src.core.agno_agent_framework import create_agent_manager

manager = create_agent_manager()
manager.register_agent(agent1)
manager.register_agent(agent2)
```

#### `create_orchestrator()`

Creates an AgentOrchestrator for workflow orchestration.

```python
from src.core.agno_agent_framework import create_orchestrator

orchestrator = create_orchestrator(manager)
```

### High-Level Convenience Functions

#### `chat_with_agent()`

Chat with an agent (handles session management automatically).

```python
from src.core.agno_agent_framework import chat_with_agent

response = await chat_with_agent(
    agent,
    "What is AI?",
    context={"user_id": "user_123"},
    tenant_id="tenant_123"
)

print(response["answer"])
print(response["session_id"])
```

#### `execute_task()`

Execute a task on an agent easily.

```python
from src.core.agno_agent_framework import execute_task

result = await execute_task(
    agent,
    "analyze",
    {
        "text": "Analyze this document",
        "model": "gpt-4"
    },
    tenant_id="tenant_123"
)

print(result)
```

#### `delegate_task()`

Delegate a task between agents.

```python
from src.core.agno_agent_framework import delegate_task

result = await delegate_task(
    orchestrator,
    "agent_001",
    "agent_002",
    "analyze",
    {"data": "..."},
    tenant_id="tenant_123"
)
```

#### `find_agents_by_capability()`

Find agents by their capabilities.

```python
from src.core.agno_agent_framework import find_agents_by_capability

agents = find_agents_by_capability(manager, "data_analysis")
for agent in agents:
    print(f"Found agent: {agent.agent_id}")
```

### Utility Functions

#### `batch_process_agents()`

Process tasks on multiple agents concurrently.

```python
from src.core.agno_agent_framework import batch_process_agents

results = await batch_process_agents(
    [agent1, agent2, agent3],
    "analyze",
    {"text": "..."},
    tenant_id="tenant_123"
)

for agent_id, result in results.items():
    print(f"Agent {agent_id}: {result}")
```

#### `retry_on_failure()`

Decorator for retry logic.

```python
from src.core.agno_agent_framework import retry_on_failure

@retry_on_failure(max_retries=3, retry_delay=1.0)
async def my_function():
    # Will retry up to 3 times on failure
    result = await agent.execute_task(task)
    return result
```

#### `save_agent_state()` and `load_agent_state()`

Save and load agent state for persistence.

```python
from src.core.agno_agent_framework import save_agent_state, load_agent_state

# Save agent state
save_agent_state(agent, "/tmp/agent_state.json", tenant_id="tenant_123")

# Load agent state
restored_agent = load_agent_state(
    "/tmp/agent_state.json",
    gateway,
    tenant_id="tenant_123"
)
```

---

## Orchestration

### Functionality

Orchestration manages complex multi-agent workflows with:
- **Workflow Pipelines**: Sequential, parallel, and conditional execution
- **Coordination Patterns**: Leader-follower, peer-to-peer, hierarchical, pipeline, broadcast
- **Task Delegation**: Delegate tasks between agents
- **Task Chaining**: Chain tasks across multiple agents
- **Dependency Management**: Handle step dependencies
- **Error Handling**: Retry logic and timeout support per step

### Coordination Patterns

1. **Leader-Follower**: Leader executes first, then followers execute in parallel
2. **Peer-to-Peer**: All agents execute simultaneously and coordinate results
3. **Hierarchical**: Tree structure with parent-child relationships
4. **Pipeline**: Sequential processing through a chain of agents
5. **Broadcast**: One-to-many communication pattern

### Code Examples

#### Creating a Workflow

```python
from src.core.agno_agent_framework.orchestration import (
    AgentOrchestrator,
    WorkflowPipeline
)

# Create orchestrator
orchestrator = AgentOrchestrator(manager)

# Create workflow
workflow = orchestrator.create_workflow(
    name="Data Analysis Workflow",
    description="Analyze data and generate report"
)

# Add workflow steps
workflow.add_step(
    agent_id="agent_001",
    task_type="data_collection",
    parameters={"source": "database"},
    step_id="step1"
)

workflow.add_step(
    agent_id="agent_002",
    task_type="data_analysis",
    parameters={"method": "statistical"},
    step_id="step2",
    depends_on=["step1"]  # Depends on step1
)

workflow.add_step(
    agent_id="agent_003",
    task_type="report_generation",
    parameters={"format": "pdf"},
    step_id="step3",
    depends_on=["step2"]  # Depends on step2
)
```

#### Executing a Workflow

```python
# Execute workflow
result = await orchestrator.execute_workflow(
    workflow.pipeline_id,
    tenant_id="tenant_123"
)

print(f"Workflow status: {result['status']}")
print(f"Completed steps: {result['completed_steps']}")
print(f"Step results: {result['step_results']}")
```

#### Coordination Patterns

```python
# Leader-Follower Pattern
result = await orchestrator.coordinate_agents(
    pattern="leader_follower",
    leader_id="agent_001",
    follower_ids=["agent_002", "agent_003"],
    task_type="analysis",
    parameters={"data": "..."},
    tenant_id="tenant_123"
)

# Peer-to-Peer Pattern
result = await orchestrator.coordinate_agents(
    pattern="peer_to_peer",
    agent_ids=["agent_001", "agent_002", "agent_003"],
    task_type="analysis",
    parameters={"data": "..."},
    tenant_id="tenant_123"
)

# Pipeline Pattern
result = await orchestrator.coordinate_agents(
    pattern="pipeline",
    agent_ids=["agent_001", "agent_002", "agent_003"],
    task_type="processing",
    parameters={"data": "..."},
    tenant_id="tenant_123"
)
```

#### Task Delegation

```python
# Delegate task from one agent to another
result = await orchestrator.delegate_task(
    from_agent_id="agent_001",
    to_agent_id="agent_002",
    task_type="analysis",
    parameters={"data": "..."},
    tenant_id="tenant_123"
)
```

#### Task Chaining

```python
# Chain tasks across multiple agents
result = await orchestrator.chain_tasks(
    agent_ids=["agent_001", "agent_002", "agent_003"],
    task_type="processing",
    initial_parameters={"data": "..."},
    transform_func=lambda result, agent_id: {
        "data": result,
        "processed_by": agent_id
    },
    tenant_id="tenant_123"
)
```

---

## Workflow

### Component Placement in SDK Architecture

The Agno Agent Framework is positioned in the **Core Layer** of the SDK architecture and interacts with multiple components:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SDK ARCHITECTURE OVERVIEW                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ API Backend  │  │   RAG System  │  │   Workflows  │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
┌─────────┼──────────────────┼──────────────────┼─────────────────┐
│         │                  │                  │                  │
│  ┌──────▼──────────────────▼──────────────────▼──────┐          │
│  │         AGNO AGENT FRAMEWORK (Core Layer)          │          │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐        │          │
│  │  │  Agent   │  │ Manager  │  │Orchestrator│       │          │
│  │  └────┬─────┘  └────┬─────┘  └─────┬─────┘        │          │
│  └───────┼─────────────┼──────────────┼──────────────┘          │
│          │             │              │                         │
└──────────┼─────────────┼──────────────┼─────────────────────────┘
           │             │              │
           │             │              │
┌──────────┼─────────────┼──────────────┼─────────────────────────┐
│          │             │              │                         │
│  ┌───────▼──────┐  ┌───▼──────┐  ┌───▼──────────┐              │
│  │LiteLLM Gateway│  │  Cache   │  │  PostgreSQL  │              │
│  └──────────────┘  └──────────┘  └──────────────┘              │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Prompt     │  │ Observability │  │  Connectivity│         │
│  │  Management  │  │               │  │   Clients    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│                    INFRASTRUCTURE LAYER                          │
└──────────────────────────────────────────────────────────────────┘
```

### Detailed Agent Task Execution Workflow

The following diagram shows the complete flow of a task execution with all components and their interactions:

```
┌─────────────────────────────────────────────────────────────────┐
│                    TASK EXECUTION WORKFLOW                       │
└─────────────────────────────────────────────────────────────────┘

    [User/API Request]
           │
           ▼
    ┌──────────────┐
    │  AgentTask   │  Parameters:
    │  Created     │  - task_id: str
    │              │  - task_type: str
    │              │  - parameters: Dict[str, Any]
    │              │  - priority: int
    └──────┬───────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 1: Task Submission                                │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ agent.add_task(task)                             │  │
    │  │                                                   │  │
    │  │ Code Flow:                                       │  │
    │  │ 1. Validate task parameters                      │  │
    │  │ 2. Check agent status (must be IDLE/RUNNING)     │  │
    │  │ 3. Add task to agent.task_queue                  │  │
    │  │ 4. Sort queue by priority (highest first)        │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 2: Task Selection                                 │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ agent.execute_task(task)                          │  │
    │  │                                                   │  │
    │  │ Code Flow:                                       │  │
    │  │ 1. Select highest priority task from queue       │  │
    │  │ 2. Update agent.status = AgentStatus.RUNNING     │  │
    │  │ 3. Validate tenant_id matches agent.tenant_id    │  │
    │  │ 4. Check circuit breaker state                    │  │
    │  │ 5. Check health check status                      │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 3: Prompt Building                                │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ _build_prompt_with_context(task)                  │  │
    │  │                                                   │  │
    │  │ Parameters Used:                                  │  │
    │  │ - task.parameters["prompt"]: Base prompt         │  │
    │  │ - agent.system_prompt: System instructions       │  │
    │  │ - agent.prompt_manager: Template rendering       │  │
    │  │                                                   │  │
    │  │ Code Flow:                                       │  │
    │  │ 1. Start with system_prompt (if set)            │  │
    │  │ 2. Render role_template via prompt_manager       │  │
    │  │ 3. Retrieve relevant memories:                  │  │
    │  │    memories = agent.memory.retrieve(             │  │
    │  │        query=task.parameters["prompt"],           │  │
    │  │        limit=5                                   │  │
    │  │    )                                             │  │
    │  │ 4. Build context from memories                   │  │
    │  │ 5. Include conversation history (if available)  │  │
    │  │ 6. Enforce token budget via ContextWindowManager│  │
    │  │ 7. Assemble final prompt                         │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 4: Tool Preparation (if tools enabled)            │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ agent.tool_registry.prepare_tool_schemas()       │  │
    │  │                                                   │  │
    │  │ Parameters Used:                                  │  │
    │  │ - agent.tools: List[Tool]                        │  │
    │  │ - enable_tool_calling: bool                      │  │
    │  │                                                   │  │
    │  │ Code Flow:                                       │  │
    │  │ 1. Check if tools are registered                 │  │
    │  │ 2. Check if tool_calling is enabled              │  │
    │  │ 3. Convert tools to LLM function schemas:        │  │
    │  │    schemas = [                                    │  │
    │  │        {                                          │  │
    │  │            "name": tool.name,                    │  │
    │  │            "description": tool.description,     │  │
    │  │            "parameters": tool.parameters         │  │
    │  │        }                                          │  │
    │  │        for tool in agent.tools                   │  │
    │  │    ]                                             │  │
    │  │ 4. Include schemas in LLM request               │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 5: LLM Call via LiteLLM Gateway                   │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ gateway.generate_async(                           │  │
    │  │     prompt=enhanced_prompt,                       │  │
    │  │     model=agent.llm_model,                        │  │
    │  │     tenant_id=agent.tenant_id,                    │  │
    │  │     functions=tool_schemas                         │  │
    │  │ )                                                 │  │
    │  │                                                   │  │
    │  │ Parameters Passed:                                │  │
    │  │ - prompt: str (enhanced with context)             │  │
    │  │ - model: str (e.g., "gpt-4")                     │  │
    │  │ - tenant_id: Optional[str]                       │  │
    │  │ - functions: Optional[List[Dict]]                │  │
    │  │                                                   │  │
    │  │ Gateway Processing:                               │  │
    │  │ 1. Rate limiting check (per tenant)              │  │
    │  │ 2. Request deduplication                          │  │
    │  │ 3. Circuit breaker check                         │  │
    │  │ 4. LLM API call                                   │  │
    │  │ 5. LLMOps logging                                │  │
    │  │ 6. Response validation                           │  │
    │  │ 7. Return GenerateResponse                       │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 6: Tool Execution Loop (if function calls)        │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ while function_calls and iterations < max:        │  │
    │  │    1. Extract function calls from LLM response   │  │
    │  │    2. For each function call:                    │  │
    │  │       - Find tool by name                        │  │
    │  │       - Validate arguments                       │  │
    │  │       - Execute tool:                             │  │
    │  │         result = tool.execute(**arguments)        │  │
    │  │       - Add result to tool_results                │  │
    │  │    3. Feed tool_results back to LLM              │  │
    │  │    4. Get new LLM response                        │  │
    │  │    5. Check for more function calls                │  │
    │  │                                                   │  │
    │  │ Parameters:                                       │  │
    │  │ - max_tool_iterations: int (default: 10)         │  │
    │  │ - tool_results: List[Dict]                        │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 7: Result Processing                              │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ Code Flow:                                       │  │
    │  │ 1. Extract final text from LLM response          │  │
    │  │ 2. Process any remaining function calls          │  │
    │  │ 3. Format result according to task_type          │  │
    │  │ 4. Update task.status = "completed"             │  │
    │  │ 5. Update agent.status = AgentStatus.IDLE        │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 8: Memory Storage                                  │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ if agent.memory:                                  │  │
    │  │     agent.memory.store(                           │  │
    │  │         content=result_text,                      │  │
    │  │         memory_type=MemoryType.EPISODIC,          │  │
    │  │         importance=0.7,                           │  │
    │  │         metadata={                                │  │
    │  │             "task_id": task.task_id,              │  │
    │  │             "task_type": task.task_type           │  │
    │  │         }                                          │  │
    │  │     )                                             │  │
    │  │                                                   │  │
    │  │ Memory Processing:                                │  │
    │  │ 1. Check memory bounds (max_episodic, etc.)      │  │
    │  │ 2. Trim if exceeds limits                        │  │
    │  │ 3. Cleanup expired memories                      │  │
    │  │ 4. Persist to disk (if enabled)                 │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    [Return Result to Caller]
```

### Multi-Agent Workflow Orchestration

```
┌─────────────────────────────────────────────────────────────────┐
│              MULTI-AGENT WORKFLOW ORCHESTRATION                  │
└─────────────────────────────────────────────────────────────────┘

    [Workflow Definition]
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  WorkflowPipeline Creation                              │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ workflow = orchestrator.create_workflow(         │  │
    │  │     name="Data Analysis",                        │  │
    │  │     description="..."                            │  │
    │  │ )                                                 │  │
    │  │                                                   │  │
    │  │ Parameters:                                       │  │
    │  │ - name: str                                       │  │
    │  │ - description: str                                │  │
    │  │ - pipeline_id: Optional[str] (auto-generated)    │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  Adding Workflow Steps                                  │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ workflow.add_step(                                │  │
    │  │     agent_id="agent_001",                         │  │
    │  │     task_type="data_collection",                   │  │
    │  │     parameters={"source": "database"},            │  │
    │  │     step_id="step1",                              │  │
    │  │     depends_on=[],                                 │  │
    │  │     retry_count=3,                                │  │
    │  │     timeout=300.0                                  │  │
    │  │ )                                                 │  │
    │  │                                                   │  │
    │  │ Parameters Explained:                            │  │
    │  │ - agent_id: str - Which agent executes this step  │  │
    │  │ - task_type: str - Type of task to execute       │  │
    │  │ - parameters: Dict - Task parameters             │  │
    │  │ - step_id: str - Unique step identifier          │  │
    │  │ - depends_on: List[str] - Step dependencies      │  │
    │  │ - retry_count: int - Retries on failure          │  │
    │  │ - timeout: float - Step timeout in seconds       │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  Workflow Execution                                     │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ result = await orchestrator.execute_workflow(    │  │
    │  │     workflow.pipeline_id,                        │  │
    │  │     tenant_id="tenant_123"                        │  │
    │  │ )                                                 │  │
    │  │                                                   │  │
    │  │ Execution Flow:                                  │  │
    │  │ 1. Build dependency graph from steps             │  │
    │  │ 2. Identify steps with no dependencies (ready)  │  │
    │  │ 3. Execute ready steps in parallel               │  │
    │  │ 4. As steps complete, mark dependencies met      │  │
    │  │ 5. Execute next batch of ready steps              │  │
    │  │ 6. Continue until all steps complete              │  │
    │  │ 7. Aggregate results from all steps              │  │
    │  │                                                   │  │
    │  │ For each step execution:                         │  │
    │  │   - Get agent from AgentManager                  │  │
    │  │   - Create AgentTask from step                   │  │
    │  │   - Execute task via agent.execute_task()        │  │
    │  │   - Handle retries on failure                    │  │
    │  │   - Apply timeout                                │  │
    │  │   - Store result in workflow state               │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    [Workflow Results]
```

### Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│              COMPONENT INTERACTION FLOW                          │
└─────────────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │   Agent      │
                    │  (Core)      │
                    └──────┬───────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│LiteLLM Gateway│  │ AgentMemory   │  │PromptManager  │
│               │  │               │  │               │
│ Functions:    │  │ Functions:    │  │ Functions:    │
│ - generate()  │  │ - store()     │  │ - render()    │
│ - embed()     │  │ - retrieve()  │  │ - add_template│
│ - stream()    │  │ - cleanup()   │  │ - build_context│
└───────┬───────┘  └───────┬───────┘  └───────┬───────┘
        │                  │                  │
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ ToolRegistry │
                    │              │
                    │ Functions:   │
                    │ - execute()  │
                    │ - register() │
                    └──────┬───────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│AgentManager   │  │Orchestrator    │  │HealthCheck    │
│               │  │                │  │               │
│ Functions:    │  │ Functions:     │  │ Functions:     │
│ - register()  │  │ - create_      │  │ - check()      │
│ - send_msg()  │  │   workflow()   │  │ - get_health() │
│ - get_agent() │  │ - execute_     │  │               │
│               │  │   workflow()   │  │               │
└───────────────┘  └───────────────┘  └───────────────┘
```

### Parameter Details

#### AgentTask Parameters

```python
class AgentTask(BaseModel):
    task_id: str              # Unique identifier for the task
                            # Format: "task_{uuid}" or custom

    task_type: str          # Type of task (e.g., "llm_query", "analysis")
                            # Used to determine processing logic

    parameters: Dict[str, Any]  # Task-specific parameters
                            # Common keys:
                            #   - "prompt": str (for LLM queries)
                            #   - "model": str (LLM model name)
                            #   - "temperature": float (0.0-2.0)
                            #   - "max_tokens": int

    priority: int = 0       # Task priority (higher = more important)
                            # Tasks sorted by priority in queue
                            # Range: -inf to +inf (default: 0)

    created_at: datetime    # Timestamp when task was created
                            # Used for queue ordering if priorities equal

    status: str = "pending" # Task status
                            # Values: "pending", "running", "completed", "failed"
```

#### Memory Store Parameters

```python
agent.memory.store(
    content: str,                    # Memory content to store
                                    # Can be text, structured data, etc.

    memory_type: MemoryType,         # Type of memory
                                    # Values:
                                    #   - MemoryType.SHORT_TERM (working memory)
                                    #   - MemoryType.LONG_TERM (persistent)
                                    #   - MemoryType.EPISODIC (events/tickets)
                                    #   - MemoryType.SEMANTIC (knowledge)

    importance: float = 0.5,        # Importance score (0.0-1.0)
                                    # Used for:
                                    #   - Retrieval ranking
                                    #   - Cleanup prioritization
                                    #   - Memory trimming decisions

    metadata: Optional[Dict] = None, # Additional metadata
                                    # Common keys:
                                    #   - "task_id": str
                                    #   - "user_id": str
                                    #   - "timestamp": str
                                    #   - "source": str

    tags: Optional[List[str]] = None # Tags for categorization
                                    # Used for:
                                    #   - Filtering during retrieval
                                    #   - Memory organization
                                    #   - Search optimization
) -> MemoryItem
```

#### Workflow Step Parameters

```python
workflow.add_step(
    agent_id: str,                  # Agent that executes this step
                                    # Must be registered in AgentManager

    task_type: str,                 # Type of task to execute
                                    # Must match agent capabilities

    parameters: Dict[str, Any],      # Task parameters
                                    # Passed to agent.execute_task()

    step_id: Optional[str] = None,  # Unique step identifier
                                    # Auto-generated if not provided
                                    # Format: "step_{index}"

    depends_on: Optional[List[str]] = None,  # Step dependencies
                                    # List of step_ids that must complete first
                                    # Empty list = no dependencies (runs immediately)

    condition: Optional[Callable] = None,    # Conditional execution
                                    # Function: (context: Dict) -> bool
                                    # Step only executes if condition returns True

    retry_count: int = 0,           # Number of retries on failure
                                    # 0 = no retries
                                    # Each retry uses exponential backoff

    timeout: Optional[float] = None # Step timeout in seconds
                                    # None = no timeout
                                    # Step fails if exceeds timeout
) -> str  # Returns step_id
```

---

## Customization

### Configuration Files

#### Agent Configuration

```python
# agent_config.py
AGENT_CONFIG = {
    "agent_id": "agent_001",
    "name": "Custom Agent",
    "description": "A customized agent",
    "capabilities": [
        {
            "name": "custom_capability",
            "description": "Custom capability",
            "parameters": {"param1": "value1"}
        }
    ],
    "memory_config": {
        "max_episodic": 1000,
        "max_semantic": 5000,
        "max_age_days": 60
    },
    "llm_config": {
        "model": "gpt-4",
        "provider": "openai",
        "temperature": 0.7
    }
}
```

#### Memory Configuration

```python
# memory_config.py
MEMORY_CONFIG = {
    "max_short_term": 100,
    "max_long_term": 2000,
    "max_episodic": 1000,
    "max_semantic": 5000,
    "max_age_days": 60,
    "persistence_path": "/custom/path/memory.json",
    "cleanup_interval_hours": 24
}
```

#### Workflow Configuration

```python
# workflow_config.py
WORKFLOW_CONFIG = {
    "default_retry_count": 3,
    "default_timeout": 300.0,
    "max_parallel_steps": 5,
    "coordination_pattern": "pipeline"
}
```

### Parameter Adjustments

#### Customizing Agent Behavior

```python
# Create agent with custom configuration
agent = create_agent(
    agent_id="custom_agent",
    name="Custom Agent",
    gateway=gateway,
    tenant_id="tenant_123",
    description="Customized agent",
    llm_model="gpt-4",
    llm_provider="openai"
)

# Customize capabilities
agent.capabilities = [
    AgentCapability(
        name="custom_analysis",
        description="Custom analysis capability",
        parameters={"method": "advanced"}
    )
]

# Customize memory
agent.attach_memory(
    persistence_path="/custom/memory.json",
    max_episodic=1000,
    max_semantic=5000,
    max_age_days=60
)

# Customize prompt management
agent.prompt_manager = create_prompt_manager(
    max_tokens=16000,
    system_prompt="You are a specialized custom agent."
)
```

#### Customizing Memory Management

```python
# Custom memory limits
memory_config = {
    "max_short_term": 100,  # Increase short-term memory
    "max_long_term": 2000,  # Increase long-term memory
    "max_episodic": 1000,  # Custom episodic limit
    "max_semantic": 5000,  # Custom semantic limit
    "max_age_days": 60,  # Longer retention period
    "persistence_path": "/custom/path/memory.json"
}

agent.attach_memory(**memory_config)
```

#### Customizing Workflow Execution

```python
# Custom workflow with specific configurations
workflow = orchestrator.create_workflow(
    name="Custom Workflow",
    description="Custom workflow with specific settings"
)

# Add step with custom retry and timeout
workflow.add_step(
    agent_id="agent_001",
    task_type="custom_task",
    parameters={"custom_param": "value"},
    step_id="custom_step",
    retry_count=5,  # Custom retry count
    timeout=600.0  # Custom timeout (10 minutes)
)
```

#### Customizing Exception Handling

```python
# Custom exception handler
async def custom_error_handler(error: Exception, context: dict):
    """Custom error handling logic."""
    if isinstance(error, AgentExecutionError):
        # Custom handling for execution errors
        logger.error(f"Execution failed: {error.message}")
        # Retry logic, fallback, etc.
    elif isinstance(error, ToolInvocationError):
        # Custom handling for tool errors
        logger.error(f"Tool failed: {error.tool_name}")
        # Alternative tool, fallback, etc.

# Attach custom error handler
agent.set_error_handler(custom_error_handler)
```

### Creating Custom Components

#### Custom Tool

```python
from src.core.agno_agent_framework.tools import Tool, ToolType

def custom_analysis_function(data: str, method: str = "default") -> dict:
    """Custom analysis function."""
    # Custom logic here
    return {"result": "analysis", "method": method}

custom_tool = Tool(
    tool_id="custom_analysis",
    name="custom_analysis",
    description="Custom analysis tool",
    tool_type=ToolType.FUNCTION,
    function=custom_analysis_function
)

agent.attach_tools([custom_tool])
```

#### Custom Memory Strategy

```python
from src.core.agno_agent_framework.memory import AgentMemory, MemoryType

class CustomMemory(AgentMemory):
    """Custom memory implementation."""

    def custom_retrieval_strategy(self, query: str, limit: int = 5):
        """Custom retrieval strategy."""
        # Custom logic for memory retrieval
        memories = self.retrieve(query, limit=limit)
        # Apply custom filtering, ranking, etc.
        return memories

# Use custom memory
custom_memory = CustomMemory(
    agent_id="agent_001",
    max_episodic=1000,
    max_semantic=5000
)
agent.memory = custom_memory
```

#### Custom Orchestration Pattern

```python
from src.core.agno_agent_framework.orchestration import AgentOrchestrator

class CustomOrchestrator(AgentOrchestrator):
    """Custom orchestrator with additional patterns."""

    async def custom_coordination_pattern(
        self,
        agent_ids: List[str],
        task_type: str,
        parameters: dict,
        tenant_id: Optional[str] = None
    ):
        """Custom coordination pattern."""
        # Custom coordination logic
        results = {}
        for agent_id in agent_ids:
            agent = self.manager.get_agent(agent_id)
            result = await agent.execute_task(
                AgentTask(
                    task_id=f"task_{agent_id}",
                    task_type=task_type,
                    parameters=parameters
                ),
                tenant_id=tenant_id
            )
            results[agent_id] = result
        return results

# Use custom orchestrator
custom_orchestrator = CustomOrchestrator(manager)
```

---

## Best Practices

1. **Agent Design**: Design agents with specific, well-defined capabilities
2. **Memory Management**: Set appropriate memory bounds for long-running agents
3. **Error Handling**: Implement comprehensive error handling with specific exception types
4. **Tool Design**: Design tools with clear interfaces and proper validation
5. **Workflow Design**: Design workflows with clear dependencies and error handling
6. **Resource Management**: Monitor resource usage, especially LLM API calls
7. **Observability**: Ensure all agent activities are logged and monitored
8. **Testing**: Write comprehensive tests for agents, tools, and workflows
9. **Documentation**: Document custom components and configurations
10. **Performance**: Optimize memory usage and workflow execution

---

## Additional Resources

- **Component README**: `src/core/agno_agent_framework/README.md`
- **Troubleshooting Guide**: `docs/troubleshooting/agent_troubleshooting.md`
- **Function Documentation**: `src/core/agno_agent_framework/functions.py`
- **Examples**: `examples/basic_usage/07_agent_basic.py`
- **Integration Examples**: `examples/integration/multi_agent_orchestration.py`

