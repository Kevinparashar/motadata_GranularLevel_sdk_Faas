# Agents

## Overview

This directory contains agent implementations and agent type definitions within the Agno Agent Framework. Agents are the core execution units that perform specific tasks, communicate with each other, and coordinate to accomplish complex goals. Agents are enhanced with session management, memory systems, tools, and plugins to provide comprehensive autonomous capabilities.

## Purpose and Functionality

Agents are autonomous entities within the framework that:
- **Execute Tasks**: Perform specific tasks based on their capabilities
- **Reason with LLMs**: Use LLM reasoning to make decisions and generate responses
- **Communicate**: Exchange messages with other agents for coordination
- **Maintain State**: Track their current state and task progress
- **Manage Sessions**: Maintain conversation sessions with context and history
- **Store Memories**: Remember important information across interactions
- **Use Tools**: Extend capabilities through tool usage
- **Load Plugins**: Extend functionality through plugin system
- **Handle Errors**: Implement error recovery and handling mechanisms

Each agent is specialized for specific types of tasks, enabling modular problem-solving where different agents handle different aspects of complex problems.

## Connection to Other Components

### Integration with Agent Framework

Agents are managed by the **Agno Agent Framework** (`src/core/agno_agent_framework/`). The framework's `AgentManager` class registers agents, routes messages between them, and provides coordination capabilities. Agents are created through the framework and communicate through the framework's messaging system.

### Integration with LiteLLM Gateway

The **LiteLLM Gateway** (`src/core/litellm_gateway/`) is a critical dependency for agents. Every agent requires a gateway instance to perform LLM operations. When agents need to reason, analyze, or generate responses, they use the gateway's `generate_async()` method. The gateway is injected into agents during creation, establishing a clear dependency relationship.

### Integration with Session Management

The **Session Management** system (internal component) provides conversation context and history for agents. Sessions maintain:
- **Conversation History**: Messages exchanged in a session
- **Session Context**: Context variables that persist across interactions
- **Session State**: Current state of the session (active, paused, completed)

Agents use sessions to maintain context across multiple interactions, enabling coherent multi-turn conversations.

### Integration with Memory System

The **Memory System** (internal component) provides both short-term and long-term memory for agents. Memory stores:
- **Short-term Memory**: Recent information and working memory
- **Long-term Memory**: Important information that persists
- **Episodic Memory**: Event-based memories
- **Semantic Memory**: Fact-based knowledge

Agents use memory to remember important information, learn from past interactions, and maintain knowledge across sessions.

### Integration with Tools System

The **Tools System** (internal component) provides capabilities that agents can use. Tools extend agent functionality by providing:
- **Function Tools**: Python functions that agents can call
- **API Tools**: External API integrations
- **Database Tools**: Database query capabilities
- **Custom Tools**: Domain-specific tools

Agents use tools through the tool registry and executor, enabling them to perform actions beyond LLM reasoning.

### Integration with Plugins System

The **Plugins System** (internal component) provides extensibility for agents. Plugins can:
- **Register Hooks**: Intercept agent lifecycle events
- **Provide Tools**: Add new tools to the agent's toolkit
- **Modify Behavior**: Change agent behavior through hooks
- **Extend Capabilities**: Add new capabilities to agents

Plugins enable third-party extensions and custom agent behaviors without modifying core agent code.

### Integration with PostgreSQL Database

The **PostgreSQL Database** (`src/core/postgresql_database/`) can store:
- **Agent State**: Persistent agent state and configuration
- **Session Data**: Session history and context
- **Memory Storage**: Long-term memories can be persisted
- **Task History**: Historical task execution records

This persistence enables agents to maintain context across application restarts and provides audit trails.

### Integration with RAG System

The **RAG System** (`src/core/rag/`) can be used by agents when they need to retrieve information from the knowledge base. Agents can query the RAG system to get context-aware information before making decisions or generating responses. This integration enables agents to have access to up-to-date information stored in the document database.

### Integration with Evaluation & Observability

The **Evaluation & Observability** component (`src/core/evaluation_observability/`) tracks:
- **Agent Activities**: All agent operations and interactions
- **Task Execution Times**: Monitors how long tasks take to execute
- **Success Rates**: Tracks task success and failure rates
- **Memory Usage**: Monitors memory storage and retrieval patterns
- **Tool Usage**: Tracks which tools are used and how often
- **Plugin Performance**: Monitors plugin execution and performance
- **Communication Patterns**: Monitors agent-to-agent communication
- **Resource Usage**: Tracks LLM API usage and costs per agent

This monitoring is essential for understanding agent behavior, optimizing configurations, and debugging issues.

## Agent Structure

### Base Agent Class

All agents inherit from a base `Agent` class that provides:
- **Task Execution Interface**: Standard interface for executing tasks
- **Communication Capabilities**: Methods for sending and receiving messages
- **LLM Integration**: Integration with the LiteLLM Gateway for reasoning
- **State Management**: Tracks agent state (idle, running, paused, error)
- **Session Management**: Maintains conversation sessions
- **Memory Management**: Stores and retrieves memories
- **Tool Access**: Access to registered tools
- **Plugin Support**: Support for plugin hooks and extensions
- **Error Handling**: Implements error handling and recovery

### Agent Types

#### Task Agent

Task agents execute specific tasks using LLM reasoning. They receive tasks, use the gateway to reason about the task, access relevant memories, use appropriate tools, and execute the task based on their capabilities.

#### Coordination Agent

Coordination agents manage multi-agent workflows. They decompose complex tasks into subtasks, assign them to appropriate agents, coordinate execution, and aggregate results. They use sessions to maintain workflow context.

#### Specialized Agent

Specialized agents are domain-specific agents with expertise in particular areas:
- **Data Analyst Agent**: Specialized in data analysis and visualization, uses data analysis tools
- **Code Reviewer Agent**: Specialized in code review and analysis, uses code analysis tools
- **Research Agent**: Specialized in research and information gathering, uses RAG system and research tools

## Session Management

Sessions provide conversation context and history:
- **Session Creation**: Sessions are created for agent interactions
- **Message History**: Sessions maintain conversation message history
- **Context Variables**: Sessions store context variables that persist across messages
- **Session State**: Sessions track their state (active, paused, completed, expired)
- **Session Expiration**: Sessions can expire after inactivity or time limits

Agents use sessions to maintain coherent conversations and context across multiple interactions.

## Memory System

Memory provides both short-term and long-term storage:
- **Short-term Memory**: Stores recent information and working memory, limited capacity
- **Long-term Memory**: Stores important information that persists, larger capacity
- **Episodic Memory**: Stores event-based memories of specific occurrences
- **Semantic Memory**: Stores fact-based knowledge and concepts
- **Memory Consolidation**: Important short-term memories can be consolidated to long-term
- **Memory Retrieval**: Memories can be retrieved by query, tags, or type

Agents use memory to remember important information, learn from interactions, and maintain knowledge.

## Tools System

Tools extend agent capabilities:
- **Tool Registration**: Tools are registered in a tool registry
- **Tool Execution**: Agents can execute tools during task processing
- **Function Calling**: Tools can be exposed to LLMs through function calling
- **Tool Schemas**: Tools provide schemas for LLM function calling integration
- **Tool Types**: Supports function, API, database, file, and custom tool types

Agents use tools to perform actions beyond LLM reasoning, such as database queries, API calls, or file operations.

## Plugins System

Plugins provide extensibility:
- **Plugin Registration**: Plugins are registered with a plugin manager
- **Hook System**: Plugins can register hooks to intercept agent lifecycle events
- **Tool Provision**: Plugins can provide tools to agents
- **Behavior Modification**: Plugins can modify agent behavior through hooks
- **Dependency Management**: Plugins can depend on other plugins

Plugins enable third-party extensions and custom behaviors without modifying core agent code.

## Agent Lifecycle

### States

Agents transition through different states:
- **IDLE**: Agent is ready to receive tasks
- **RUNNING**: Agent is currently executing a task
- **PAUSED**: Agent is paused and not accepting new tasks
- **ERROR**: Agent encountered an error and needs recovery

### State Transitions

Agents transition between states based on events:
- **IDLE → RUNNING**: When a task is received and execution begins
- **RUNNING → IDLE**: When task execution completes successfully
- **RUNNING → ERROR**: When an error occurs during execution
- **ERROR → IDLE**: After error recovery
- **IDLE → PAUSED**: When agent is paused
- **PAUSED → IDLE**: When agent is resumed

## Task Execution Flow

1. **Task Reception**: Agent receives a task from the manager or another agent
2. **Session Context**: Agent retrieves or creates a session for the task
3. **Memory Retrieval**: Agent retrieves relevant memories for context
4. **Capability Verification**: Agent verifies it has the capabilities to handle the task
5. **LLM Reasoning**: Agent uses the LiteLLM Gateway to reason about the task
6. **Tool Selection**: Agent selects and uses appropriate tools if needed
7. **Plugin Hooks**: Plugin hooks are executed at various stages
8. **Task Execution**: Agent executes the task using its capabilities, tools, and LLM guidance
9. **Memory Storage**: Important information is stored in memory
10. **Result Generation**: Agent generates results based on task execution
11. **Result Return**: Agent returns results to the caller or stores them

## Communication Flow

1. **Message Creation**: Agent creates a message for another agent
2. **Session Context**: Message is associated with a session if applicable
3. **Memory Context**: Relevant memories are included in message context
4. **Message Routing**: Message is routed through the AgentManager's communication layer
5. **Plugin Hooks**: Plugin hooks can modify messages
6. **Message Delivery**: Message is delivered to the target agent's message queue
7. **Message Processing**: Target agent processes the message
8. **Response Generation**: Optional response is generated and sent back

## Multi-Agent Coordination

When multiple agents work together:
1. **Task Decomposition**: Complex task is broken into subtasks
2. **Agent Selection**: Appropriate agents are selected for each subtask
3. **Session Management**: Sessions are created or reused for coordination
4. **Task Distribution**: Subtasks are distributed to selected agents
5. **Parallel Execution**: Agents execute subtasks in parallel when possible
6. **Memory Sharing**: Agents can share relevant memories
7. **Result Aggregation**: Results from all agents are collected
8. **Final Assembly**: Results are combined into final output

## Error Handling

Agents implement error handling at multiple levels:
- **Task-Level Errors**: If a task fails, agent updates status to ERROR and can retry
- **LLM Errors**: Errors from the gateway are caught and handled gracefully
- **Tool Errors**: Tool execution errors are caught and reported
- **Plugin Errors**: Plugin errors are isolated to prevent affecting core functionality
- **Communication Errors**: Failed message deliveries are logged and can be retried
- **Memory Errors**: Memory storage/retrieval errors are handled gracefully
- **Recovery Mechanisms**: Agents can recover from errors and return to IDLE state

## Best Practices

1. **Single Responsibility**: Each agent should have a focused, well-defined purpose
2. **Clear Capabilities**: Define clear capabilities that agents can handle
3. **Session Management**: Use sessions to maintain conversation context
4. **Memory Optimization**: Store important information in long-term memory
5. **Tool Selection**: Use appropriate tools for specific tasks
6. **Plugin Design**: Design plugins to be modular and independent
7. **Error Recovery**: Implement robust error recovery mechanisms
8. **State Management**: Properly manage state transitions
9. **Resource Cleanup**: Clean up resources when tasks complete
10. **Monitoring**: Ensure agent activities are properly monitored
11. **Documentation**: Document agent capabilities, tools, and expected behaviors
