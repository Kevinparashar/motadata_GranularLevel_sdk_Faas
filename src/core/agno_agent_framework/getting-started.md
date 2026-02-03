# MOTADATA - GETTING STARTED WITH AGNO AGENT FRAMEWORK

**Complete guide for getting started with the Agno Agent Framework, from agent creation to task execution.**

## Overview

The Agno Agent Framework enables you to create autonomous AI agents that can execute tasks, communicate with other agents, and coordinate complex workflows. This guide provides a detailed walkthrough of the agent lifecycle from creation to task execution.

## Entry Point

The primary entry point for creating agents is through factory functions:

```python
from src.core.agno_agent_framework import create_agent, create_agent_with_memory
from src.core.litellm_gateway import create_gateway
```

## Input Requirements

### Required Inputs

1. **Gateway Instance**: A LiteLLM Gateway instance for LLM operations
   ```python
   gateway = create_gateway(
       api_key="your-api-key",
       provider="openai",
       default_model="gpt-4"
   )
   ```

2. **Agent Configuration**:
   - `agent_id`: Unique identifier for the agent
   - `name`: Human-readable name
   - `gateway`: LiteLLM Gateway instance
   - `tenant_id`: Optional tenant ID for multi-tenancy

### Optional Inputs

- `description`: Agent description
- `llm_model`: Specific LLM model to use
- `llm_provider`: Specific provider
- `memory_config`: Memory configuration (if using memory)
- `capabilities`: List of agent capabilities

## Process Flow

### Step 1: Agent Creation

**What Happens:**
1. Agent object is instantiated with provided configuration
2. Gateway is attached to the agent
3. Agent capabilities are initialized
4. Task queue is created
5. Session manager is initialized (if needed)

**Code:**
```python
agent = create_agent(
    agent_id="assistant_001",
    name="AI Assistant",
    gateway=gateway,
    tenant_id="tenant_123",
    description="A helpful assistant for answering questions"
)
```

**Internal Process:**
- Agent validates gateway connection
- Initializes empty task queue
- Sets up internal state management
- Registers with agent manager (if provided)

### Step 2: Task Creation

**What Happens:**
1. Task object is created with task type and parameters
2. Task is validated against agent capabilities
3. Task is added to agent's task queue
4. Task priority is assigned

**Code:**
```python
task_id = agent.add_task(
    task_type="llm_query",
    parameters={
        "prompt": "Explain artificial intelligence in detail.",
        "model": "gpt-4",
        "max_tokens": 500
    },
    priority=1
)
```

**Input:**
- `task_type`: Type of task (e.g., "llm_query", "analysis", "data_processing")
- `parameters`: Task-specific parameters (prompt, model, etc.)
- `priority`: Task priority (1 = highest)

**Internal Process:**
- Task validation against agent capabilities
- Task ID generation
- Queue insertion based on priority
- Task state set to "pending"

### Step 3: Task Execution

**What Happens:**
1. Agent retrieves task from queue
2. Agent prepares context (memory, history, etc.)
3. Agent calls gateway with prepared prompt
4. Gateway processes request through LLM
5. Response is received and processed
6. Task result is stored
7. Task state is updated

**Code:**
```python
import asyncio

async def execute_agent_task():
    if agent.task_queue:
        task = agent.task_queue[0]
        result = await agent.execute_task(task, tenant_id="tenant_123")
        return result

result = asyncio.run(execute_agent_task())
```

**Internal Process:**
```
Agent.execute_task()
  ├─> Validate task state
  ├─> Retrieve relevant memories (if memory enabled)
  ├─> Build prompt context
  ├─> Call gateway.generate_async()
  │   ├─> Gateway validates request
  │   ├─> Gateway applies rate limiting
  │   ├─> Gateway calls LLM provider
  │   ├─> LLM processes request
  │   └─> Response returned to gateway
  ├─> Process response
  ├─> Store result
  └─> Update task state to "completed"
```

## Output

### Task Execution Result

The `execute_task()` method returns a dictionary containing:

```python
{
    "task_id": "task_001",
    "status": "completed",
    "result": {
        "text": "Artificial Intelligence (AI) is...",
        "model": "gpt-4",
        "usage": {
            "prompt_tokens": 15,
            "completion_tokens": 150,
            "total_tokens": 165
        }
    },
    "execution_time": 2.5,  # seconds
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### Output Structure

- **`task_id`**: Identifier of the executed task
- **`status`**: Task execution status ("completed", "failed", "pending")
- **`result`**: The actual response from the LLM
  - `text`: Generated text response
  - `model`: Model used for generation
  - `usage`: Token usage information
- **`execution_time`**: Time taken to execute the task
- **`timestamp`**: When the task was completed

## Where Output is Used

### 1. Direct Usage

The output can be used directly in your application:

```python
result = await agent.execute_task(task)
response_text = result['result']['text']
print(f"Agent response: {response_text}")
```

### 2. Integration with Other Components

**With RAG System:**
```python
# Agent can use RAG output as context
rag_result = rag_system.query("What is AI?")
agent_task = agent.add_task(
    task_type="llm_query",
    parameters={
        "prompt": f"Based on this context: {rag_result['answer']}, explain further..."
    }
)
```

**With API Backend:**
```python
# API endpoint returns agent result
@app.post("/api/agent/execute")
async def execute_agent_api(request: Request):
    task_id = agent.add_task(...)
    result = await agent.execute_task(agent.task_queue[0])
    return {"response": result['result']['text']}
```

**With Memory System:**
```python
# Store result in agent memory
if result['status'] == 'completed':
    agent.memory.store(
        content=result['result']['text'],
        memory_type=MemoryType.EPISODIC,
        importance=0.8
    )
```

### 3. Multi-Agent Communication

```python
# Agent can send result to another agent
from src.core.agno_agent_framework.agent import AgentMessage

message = AgentMessage(
    from_agent="assistant_001",
    to_agent="analyst_002",
    content=result['result']['text'],
    message_type="task_result"
)
agent_manager.send_message(message)
```

## Complete Example

```python
import os
import asyncio
from src.core.agno_agent_framework import create_agent
from src.core.litellm_gateway import create_gateway

async def main():
    # Step 1: Create Gateway (Entry Point)
    gateway = create_gateway(
        api_key=os.getenv("OPENAI_API_KEY"),
        provider="openai",
        default_model="gpt-4"
    )

    # Step 2: Create Agent (Entry Point)
    agent = create_agent(
        agent_id="assistant_001",
        name="AI Assistant",
        gateway=gateway,
        tenant_id="tenant_123"
    )

    # Step 3: Add Task (Input)
    task_id = agent.add_task(
        task_type="llm_query",
        parameters={
            "prompt": "Explain quantum computing in simple terms.",
            "model": "gpt-4",
            "max_tokens": 300
        },
        priority=1
    )

    # Step 4: Execute Task (Process)
    if agent.task_queue:
        task = agent.task_queue[0]
        result = await agent.execute_task(task, tenant_id="tenant_123")

        # Step 5: Use Output
        if result['status'] == 'completed':
            response_text = result['result']['text']
            print(f"Agent Response: {response_text}")
            print(f"Tokens Used: {result['result']['usage']['total_tokens']}")
            print(f"Execution Time: {result['execution_time']}s")

            # Use output in your application
            return response_text

# Run the example
response = asyncio.run(main())
```

## Important Information

### Error Handling

```python
try:
    result = await agent.execute_task(task)
except AgentError as e:
    print(f"Agent error: {e.message}")
    print(f"Task ID: {e.task_id}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Memory Integration

```python
# Create agent with memory
agent = create_agent_with_memory(
    agent_id="assistant_002",
    name="Assistant with Memory",
    gateway=gateway,
    memory_config={
        "max_episodic": 100,
        "max_semantic": 50,
        "max_age_days": 30
    },
    tenant_id="tenant_123"
)

# Memory is automatically used during task execution
# Agent retrieves relevant memories before executing tasks
```

### Session Management

```python
from src.core.agno_agent_framework.session import SessionManager

session_manager = SessionManager()
session = session_manager.create_session(
    agent_id=agent.agent_id,
    user_id="user_123"
)

# Agent uses session context during execution
result = await agent.execute_task(task, session_id=session.session_id)
```

### Tool Integration

```python
from src.core.agno_agent_framework.tools import Tool, ToolRegistry

# Define tool
def calculate(operation: str, a: float, b: float) -> float:
    if operation == "add":
        return a + b
    elif operation == "multiply":
        return a * b

tool = Tool(
    name="calculator",
    description="Perform calculations",
    function=calculate
)

# Register tool with agent
tool_registry = ToolRegistry()
tool_registry.register(tool)
agent.tool_registry = tool_registry

# Agent can use tools during task execution
```

### Multi-Agent Coordination

```python
from src.core.agno_agent_framework import AgentManager

# Create agent manager
manager = AgentManager()

# Register multiple agents
manager.register_agent(agent1)
manager.register_agent(agent2)

# Agents can communicate and coordinate
result1 = await agent1.execute_task(task1)
# Agent1 can delegate to Agent2 based on result
```

## Next Steps

- See [README.md](README.md) for detailed component documentation
- Check [docs/components/agno_agent_framework_explanation.md](../../../docs/components/agno_agent_framework_explanation.md) for comprehensive guide
- Review [troubleshooting guide](../../../docs/troubleshooting/agent_troubleshooting.md) for common issues
- Explore [examples/basic_usage/05_agent_basic.py](../../../examples/basic_usage/05_agent_basic.py) for more examples

