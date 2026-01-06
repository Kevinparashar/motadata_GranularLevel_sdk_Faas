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

## Task Execution Flow

1. **Task Submission**: A task is submitted to an agent through the `add_task()` method, which adds it to the agent's task queue.
2. **Task Selection**: The agent selects the highest priority task from its queue.
3. **LLM Reasoning**: If the task requires reasoning, the agent uses the LiteLLM Gateway to generate responses or make decisions.
4. **Task Execution**: The agent executes the task based on its capabilities and the LLM's guidance.
5. **Result Storage**: Task results can be stored in the database for persistence.
6. **Status Update**: The agent updates its status and notifies the observability system.

## Error Handling

The framework implements error handling at multiple levels:
- **Task-Level Errors**: If a task fails, the agent updates its status to ERROR and can optionally retry the task.
- **Communication Errors**: Failed message deliveries are logged and can be retried.
- **LLM Errors**: Errors from the gateway are caught and handled gracefully, with fallback behaviors when possible.

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
