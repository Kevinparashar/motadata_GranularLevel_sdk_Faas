# Agno Agent Framework

## Overview

The Agno Agent Framework provides autonomous AI agent capabilities within the SDK. It enables the creation, management, and coordination of multiple AI agents that can execute tasks, communicate with each other, and work together to solve complex problems.

## Purpose and Functionality

The framework implements a multi-agent system where each agent is an autonomous entity capable of:
- Executing specific tasks based on its capabilities
- Communicating with other agents through message passing
- Coordinating with other agents to accomplish complex goals
- Maintaining state and context across task executions

Agents are designed to be specialized, with each agent having specific capabilities and expertise. This allows for modular problem-solving where different agents handle different aspects of a task.

## Connection to Other Components

### Integration with LiteLLM Gateway

The **LiteLLM Gateway** (`src/core/litellm_gateway/`) is a critical dependency for the agent framework. Every agent requires a gateway instance to perform LLM operations. When an agent needs to reason, generate text, or analyze information, it calls the gateway's methods. The gateway is injected into agents during creation, establishing a clear dependency relationship. The framework uses the gateway's `generate_async()` method for agent reasoning and decision-making.

### Integration with Prompt Context Management

The **Prompt Context Management** (`src/core/prompt_context_management/`) is fully integrated into the Agent Framework. Agents automatically use prompt management for:
- **System Prompts**: Define agent behavior and role through system prompts
- **Role-Based Templates**: Use role-based prompt templates for consistent agent behavior
- **Context Assembly**: Automatically assemble context from conversation history and memory
- **Token Budget Enforcement**: Enforce token limits to prevent context window overflow
- **Context Prioritization**: Prioritize relevant context from memory based on task requirements
- **Prompt History**: Maintain prompt history for context-aware conversations

When agents execute tasks, prompts are automatically enhanced with system prompts, role templates, relevant memories, and conversation history, ensuring optimal LLM interactions.

### Integration with RAG System

The **RAG System** (`src/core/rag/`) can be used by agents when they need to retrieve information from the knowledge base. Agents can query the RAG system to get context-aware information before making decisions or generating responses. This integration enables agents to have access to up-to-date information stored in the document database.

### Integration with PostgreSQL Database

The **PostgreSQL Database** (`src/core/postgresql_database/`) stores agent state, task history, and communication logs. When agents execute tasks, the results can be persisted to the database. Agent-to-agent messages can also be logged for debugging and audit purposes. The database provides persistence that allows agents to maintain context across sessions.

### Integration with Evaluation & Observability

The **Evaluation & Observability** component (`src/core/evaluation_observability/`) tracks agent activities, task execution times, success rates, and communication patterns. This monitoring is essential for understanding agent behavior, optimizing agent configurations, and debugging multi-agent interactions.

### Integration with API Backend Services

The **API Backend Services** (`src/core/api_backend_services/`) expose agent functionality through REST endpoints. External systems can create agents, submit tasks, and retrieve results through these APIs. The backend services route agent-related requests to the appropriate agent manager methods.

### Integration with Connectivity Clients

The **Connectivity Clients** (root level) are used by agents when they need to interact with external services. For example, an agent might use HTTP clients to fetch data from external APIs or WebSocket clients for real-time communication.

## Libraries Utilized

- **pydantic**: Used for data validation and model definitions. All agent configurations, messages, and tasks are defined using Pydantic models, ensuring type safety and validation.
- **asyncio**: Provides asynchronous execution capabilities, allowing agents to handle multiple tasks concurrently and communicate asynchronously.

## Key Components

### Agent Class

The `Agent` class represents an individual agent. Each agent has:
- A unique identifier and name
- A set of capabilities defining what tasks it can perform
- A status indicating its current state (idle, running, paused, etc.)
- A task queue for managing pending tasks
- A message queue for receiving communications from other agents
- A reference to the LiteLLM Gateway for LLM operations
- **Integrated Prompt Context Management** for system prompts, role templates, and context assembly
- **Memory integration** for context-aware prompt building

### AgentManager Class

The `AgentManager` class manages multiple agents. It provides:
- Agent registration and lookup
- Message routing between agents
- Broadcast messaging capabilities
- Status monitoring for all agents
- Agent discovery by capability
- Orchestrator integration

### Agent Communication

Agents communicate through the `AgentMessage` system. Messages are routed through the AgentManager, which ensures reliable delivery. This communication mechanism enables agents to coordinate, share information, and work together on complex tasks.

## Function-Driven API

The Agent Framework provides a **function-driven API** with factory functions, high-level convenience functions, and utilities for easy agent creation and management.

### Factory Functions

Create agents and managers with simplified configuration:

```python
from src.core.agno_agent_framework import (
    create_agent,
    create_agent_with_memory,
    create_agent_with_prompt_management,
    create_agent_with_tools,
    create_agent_manager,
    create_orchestrator
)

# Create a basic agent
gateway = LiteLLMGateway()
agent = create_agent("agent1", "Assistant", gateway)

# Create agent with memory pre-configured
agent = create_agent_with_memory(
    "agent2", "Analyst", gateway,
    memory_config={"persistence_path": "/tmp/memory.json"}
)

# Create agent with prompt management pre-configured
agent = create_agent_with_prompt_management(
    "agent3", "Helper", gateway,
    system_prompt="You are a helpful AI assistant.",
    role_template="assistant_role",
    max_context_tokens=8000
)

# Create agent with tools pre-configured
from src.core.agno_agent_framework.tools import Tool, ToolType

def calculate_sum(a: int, b: int) -> int:
    return a + b

tool = Tool(
    tool_id="calc_sum",
    name="calculate_sum",
    description="Adds two numbers together",
    tool_type=ToolType.FUNCTION,
    function=calculate_sum
)

agent = create_agent_with_tools(
    "agent4", "Calculator", gateway,
    tools=[tool],
    enable_tool_calling=True,
    max_tool_iterations=10
)

# Create agent manager
manager = create_agent_manager()
manager.register_agent(agent)

# Create orchestrator
orchestrator = create_orchestrator(manager)
```

### High-Level Convenience Functions

Use simplified functions for common operations:

```python
from src.core.agno_agent_framework import (
    chat_with_agent,
    execute_task,
    delegate_task,
    find_agents_by_capability
)

# Chat with agent (handles session management automatically)
response = await chat_with_agent(
    agent,
    "What is AI?",
    context={"user_id": "user123"}
)
print(response["answer"])

# Execute task easily
result = await execute_task(
    agent,
    "analyze",
    {"text": "Analyze this document", "model": "gpt-4"}
)

# Delegate task between agents
result = await delegate_task(
    orchestrator,
    "agent1",
    "agent2",
    "analyze",
    {"data": "..."}
)

# Find agents by capability
agents = find_agents_by_capability(manager, "data_analysis")
```

### Utility Functions

Use utility functions for common patterns:

```python
from src.core.agno_agent_framework import (
    batch_process_agents,
    retry_on_failure
)

# Process multiple agents concurrently
results = batch_process_agents(
    [agent1, agent2, agent3],
    "analyze",
    {"text": "..."}
)

# Retry decorator
@retry_on_failure(max_retries=3, retry_delay=1.0)
async def my_function():
    # Will retry up to 3 times on failure
    pass

# Save agent state for persistence
save_agent_state(agent, "/tmp/agent_state.json")

# Load agent state
agent = load_agent_state("/tmp/agent_state.json", gateway)
```

### Tool Calling Integration

Agents now support **integrated tool calling** with automatic function execution during task execution:

- **Tool Registration**: Register tools with agents using `attach_tools()` or `add_tool()`
- **Automatic Tool Execution**: When LLM requests function calls, tools are automatically executed
- **Iterative Tool Calling**: Agents can make multiple tool calls in a loop until task completion
- **Tool Results Integration**: Tool execution results are fed back to the LLM for continued reasoning
- **Error Handling**: Tool execution errors are caught and reported to the LLM

**Example:**
```python
from src.core.agno_agent_framework import create_agent_with_tools
from src.core.agno_agent_framework.tools import Tool, ToolType

# Define a tool function
def get_weather(location: str) -> str:
    return f"Weather in {location}: Sunny, 25°C"

# Create tool
weather_tool = Tool(
    tool_id="weather",
    name="get_weather",
    description="Get weather information for a location",
    tool_type=ToolType.FUNCTION,
    function=get_weather
)

# Create agent with tools
agent = create_agent_with_tools(
    "weather_agent", "Weather Assistant", gateway,
    tools=[weather_tool],
    enable_tool_calling=True,
    max_tool_iterations=10
)

# Execute task - agent will automatically use tools when needed
result = await agent.execute_task(
    AgentTask(
        task_id="task1",
        task_type="llm_query",
        parameters={
            "prompt": "What's the weather in New York?",
            "model": "gpt-4"
        }
    )
)
# Agent will call get_weather tool and use the result in its response
```

### Agent State Persistence

Agents now support **complete state persistence**, allowing you to save and restore full agent state:

- **Save State**: Persists agent configuration, capabilities, task queue, current task, tools, memory paths, prompt manager state, and metadata
- **Load State**: Restores agent from saved state file with all configuration intact, including tools (requires tool functions to be provided)
- **Memory Persistence**: Agent memory is persisted separately via memory.save() if attached
- **Tool Persistence**: Tool definitions are saved (tool functions must be re-registered on load)

**Example:**
```python
from src.core.agno_agent_framework import save_agent_state, load_agent_state

# Save agent state (includes tools, memory paths, prompt manager state)
save_agent_state(agent, "/tmp/agent_state.json")

# Later, restore agent with tool functions
tool_functions = {
    "get_weather": get_weather,
    "calculate_sum": calculate_sum
}
restored_agent = load_agent_state(
    "/tmp/agent_state.json",
    gateway,
    restore_tools=tool_functions
)
# Agent is fully restored with all capabilities, tasks, tools, and configuration
```

See `src/core/agno_agent_framework/functions.py` for complete function documentation.

### Prompt Context Management Integration

Agents now have **full integration with Prompt Context Management**, providing:

- **System Prompt Support**: Define agent behavior through system prompts
- **Role-Based Templates**: Use role-based prompt templates for consistent behavior
- **Context Assembly**: Automatically assemble context from memory and conversation history
- **Token Budget Enforcement**: Enforce token limits to prevent context overflow
- **Context Prioritization**: Prioritize relevant memories based on task requirements
- **Prompt History**: Maintain conversation history for context-aware interactions

**Example:**
```python
from src.core.agno_agent_framework import create_agent_with_prompt_management

# Create agent with prompt management
agent = create_agent_with_prompt_management(
    agent_id="agent1",
    name="Assistant",
    gateway=gateway,
    system_prompt="You are a helpful AI assistant specialized in technical questions.",
    role_template="technical_assistant",
    max_context_tokens=8000
)

# Add custom prompt templates
agent.add_prompt_template(
    name="analysis_template",
    version="1.0",
    content="Analyze the following: {input}\nConsider: {context}"
)

# Set system prompt dynamically
agent.set_system_prompt("You are now a data analyst.")

# Execute task - prompt is automatically enhanced with context
result = await execute_task(
    agent,
    "analyze",
    {
        "prompt": "What are the key insights?",
        "context": "Sales data shows 20% growth"
    }
)
```

**How It Works:**
1. When an agent executes a task, the prompt is automatically enhanced:
   - System prompt is prepended (if set)
   - Role template is rendered and added (if configured)
   - Relevant memories are retrieved and added as context
   - Conversation history is included (if available)
   - Token budget is enforced to prevent overflow
2. The enhanced prompt is sent to the LLM Gateway
3. Prompt history is recorded for future context building

## Task Execution Flow

1. **Task Submission**: A task is submitted to an agent through the `add_task()` method, which adds it to the agent's task queue.
2. **Task Selection**: The agent selects the highest priority task from its queue.
3. **Prompt Building**: If prompt management is enabled:
   - System prompt is added (if configured)
   - Role template is rendered (if configured)
   - Relevant memories are retrieved and added as context
   - Conversation history is included
4. **Tool Preparation**: If tools are registered and tool calling is enabled:
   - Tool schemas are prepared for LLM function calling
   - Tools are included in the LLM request
5. **LLM Call**: The enhanced prompt (and tools) is sent to the LiteLLM Gateway
6. **Tool Execution Loop** (if tool calling enabled):
   - LLM response is checked for function calls
   - If function calls are present:
     - Tools are executed with provided arguments
     - Tool results are fed back to the LLM
     - Process repeats until no more function calls or max iterations reached
7. **Result Processing**: Final LLM response is processed and returned
8. **Memory Storage**: Task result is stored in agent memory (if memory is attached)
   - Token budget is enforced
4. **LLM Reasoning**: The agent uses the LiteLLM Gateway with the enhanced prompt to generate responses or make decisions.
5. **Task Execution**: The agent executes the task based on its capabilities and the LLM's guidance.
6. **Result Storage**: Task results can be stored in memory and database for persistence.
7. **Status Update**: The agent updates its status and notifies the observability system.

## Error Handling

The Agent Framework uses a structured exception hierarchy for granular error handling. See the [Error Handling](#error-handling) section above for detailed information about exception types and usage examples.

## Swappability

The framework is designed to be swappable with other agent frameworks (e.g., LangChain) through the `AgentFrameworkInterface` defined in `src/core/interfaces.py`. This allows the SDK to support multiple agent frameworks while maintaining a consistent interface.

## Multi-Agent Orchestration

The framework includes advanced orchestration capabilities through the `AgentOrchestrator` class:

### Workflow Pipelines

Create complex multi-step workflows with dependencies:
- **Sequential Execution**: Steps execute in order based on dependencies
- **Parallel Execution**: Independent steps run concurrently
- **Conditional Execution**: Steps can have conditions for execution
- **Error Handling**: Retry logic and timeout support per step
- **State Management**: Workflow context is maintained across steps

### Coordination Patterns

Multiple coordination patterns are supported:

1. **Leader-Follower**: Leader executes first, then followers execute in parallel
2. **Peer-to-Peer**: All agents execute simultaneously and coordinate results
3. **Pipeline**: Sequential processing through a chain of agents
4. **Broadcast**: One-to-many communication pattern

### Task Delegation and Chaining

- **Task Delegation**: Agents can delegate tasks to other agents
- **Task Chaining**: Chain tasks across multiple agents sequentially
- **Result Transformation**: Transform results between chained tasks

### Example Usage

```python
from src.core.agno_agent_framework import (
    Agent, AgentManager, AgentOrchestrator
)

# Create agents and manager
manager = AgentManager()
agent1 = Agent(agent_id="agent1", name="Agent 1")
agent2 = Agent(agent_id="agent2", name="Agent 2")
manager.register_agent(agent1)
manager.register_agent(agent2)

# Create orchestrator
orchestrator = AgentOrchestrator(manager)

# Create workflow
workflow = orchestrator.create_workflow(name="My Workflow")
workflow.add_step(
    agent_id="agent1",
    task_type="task1",
    parameters={"param": "value"},
    step_id="step1"
)
workflow.add_step(
    agent_id="agent2",
    task_type="task2",
    parameters={"param": "value"},
    step_id="step2",
    depends_on=["step1"]  # Depends on step1
)

# Execute workflow
result = await orchestrator.execute_workflow(workflow.pipeline_id)
```

See `examples/integration/multi_agent_orchestration.py` for complete examples.

## Best Practices

1. **Agent Specialization**: Design agents with specific, well-defined capabilities rather than general-purpose agents.
2. **Clear Communication Protocols**: Establish clear message formats and communication protocols between agents.
3. **Error Recovery**: Implement robust error handling and recovery mechanisms for agent failures.
4. **Resource Management**: Monitor agent resource usage, especially LLM API calls, to manage costs.
5. **Observability**: Ensure all agent activities are logged and monitored for debugging and optimization.
6. **Workflow Design**: Design workflows with clear dependencies and error handling for production use.

## Examples and Tests

### Working Examples

See the following examples for Agent Framework usage:

- **Basic Agent Example**: `examples/basic_usage/07_agent_basic.py` - Basic agent operations including creation, session management, memory, and tools
- **Agent with RAG**: `examples/integration/agent_with_rag.py` - Integration example showing agent using RAG for context
- **API with Agent**: `examples/integration/api_with_agent.py` - REST API exposing agent functionality
- **Complete Q&A System**: `examples/end_to_end/complete_qa_system.py` - End-to-end example with agent framework

### Tests

- **Unit Tests**: `src/tests/unit_tests/test_agent.py` - Comprehensive unit tests for agent components
- **Integration Tests**: `src/tests/integration_tests/test_agent_rag_integration.py` - Agent-RAG integration tests
- **Integration Tests**: `src/tests/integration_tests/test_api_agent_integration.py` - API-Agent integration tests

For more examples and test documentation, see:
- `examples/README.md` - Complete examples documentation
- `src/tests/unit_tests/README.md` - Unit tests documentation
