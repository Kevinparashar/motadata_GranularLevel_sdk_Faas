# Prompt-Based Generator - Comprehensive Component Explanation

## Overview

The Prompt-Based Generator is an advanced SDK feature that enables clients to create custom AI agents and tools through natural language prompts. Instead of manually writing code and configurations, users can describe what they want in plain English, and the system automatically generates fully configured agents and tools.

## Table of Contents

1. [Introduction](#introduction)
2. [Architecture](#architecture)
3. [Core Components](#core-components)
4. [Usage Patterns](#usage-patterns)
5. [Access Control](#access-control)
6. [Feedback Loop](#feedback-loop)
7. [Caching Strategy](#caching-strategy)
8. [Memory Management](#memory-management)
9. [Best Practices](#best-practices)

---

## Introduction

### What is Prompt-Based Generation?

Prompt-based generation allows users to create AI agents and tools by describing their requirements in natural language. The system uses LLM to interpret the prompt, extract requirements, and automatically generate:

- **Agents**: Fully configured Agent instances with capabilities, system prompts, memory, and tools
- **Tools**: Executable Tool instances with generated Python code

### Key Benefits

- **Accessibility**: Non-technical users can create AI capabilities
- **Speed**: Create agents/tools in minutes instead of hours
- **Consistency**: Standardized generation process ensures quality
- **Learning**: System improves from user feedback

---

## Architecture

### Component Flow

```
User Prompt
    ↓
PromptInterpreter (LLM Analysis)
    ↓
Requirements Extraction
    ↓
Configuration Generation
    ↓
Agent/Tool Creation
    ↓
Caching & Registration
    ↓
Ready to Use
```

### Integration Points

- **LiteLLM Gateway**: For LLM calls to interpret prompts
- **Agent Framework**: For agent creation and management
- **Tool System**: For tool creation and registration
- **Cache Mechanism**: For caching interpretations
- **Feedback Loop**: For feedback collection
- **Access Control**: For permission management

---

## Core Components

### 1. PromptInterpreter

Interprets natural language prompts using LLM to extract structured requirements.

**Key Methods:**
- `interpret_agent_prompt()`: Extract agent requirements
- `interpret_tool_prompt()`: Extract tool requirements

### 2. AgentGenerator

Generates fully configured Agent instances from interpreted requirements.

**Key Methods:**
- `generate_agent_from_prompt()`: Create agent from prompt
- `generate_agent_from_cached_config()`: Recreate from cache

### 3. ToolGenerator

Generates Tool instances with executable code from interpreted requirements.

**Key Methods:**
- `generate_tool_from_prompt()`: Create tool from prompt
- `_validate_code()`: Validate generated code
- `_create_function_from_code()`: Create executable function

### 4. AccessControl

Manages permissions for agents and tools with tenant isolation.

**Key Methods:**
- `grant_permission()`: Grant access
- `revoke_permission()`: Revoke access
- `check_permission()`: Verify access
- `require_permission()`: Enforce access

### 5. FeedbackCollector

Collects and processes user feedback for continuous improvement.

**Key Methods:**
- `collect_agent_feedback()`: Collect agent ratings
- `collect_tool_feedback()`: Collect tool ratings
- `get_agent_feedback_stats()`: View statistics
- `get_tool_feedback_stats()`: View statistics

### 6. GeneratorCache

Specialized caching for prompt interpretations and configurations.

**Key Methods:**
- `cache_prompt_interpretation()`: Cache interpretation
- `cache_agent_config()`: Cache agent config
- `cache_tool_schema()`: Cache tool schema
- `cache_tool_code()`: Cache generated code

---

## Usage Patterns

### Pattern 1: Simple Agent Creation

```python
agent = await create_agent_from_prompt(
    prompt="Create a helpful assistant",
    gateway=gateway,
    tenant_id="tenant_123"
)
```

### Pattern 2: Specialized Agent with Requirements

```python
agent = await create_agent_from_prompt(
    prompt="""
    Create a technical support agent that:
    - Diagnoses technical issues
    - Provides troubleshooting steps
    - Escalates when needed
    """,
    gateway=gateway,
    tenant_id="tenant_123"
)
```

### Pattern 3: Tool Creation with Code Generation

```python
tool = await create_tool_from_prompt(
    prompt="""
    Create a tool that calculates priority.
    Inputs: urgency (1-5), impact (1-5)
    Output: Priority score (1-5)
    """,
    gateway=gateway,
    tenant_id="tenant_123"
)
```

---

## Access Control

### Permission Model

- **READ**: View agent/tool
- **EXECUTE**: Use agent/tool
- **CREATE**: Create new resources
- **DELETE**: Delete resources
- **ADMIN**: Full access

### Example

```python
# Grant permission
grant_permission(
    tenant_id="tenant_123",
    user_id="user_456",
    resource_type="agent",
    resource_id="agent_789",
    permission="execute"
)

# Check permission
has_access = check_permission(
    tenant_id="tenant_123",
    user_id="user_456",
    resource_type="agent",
    resource_id="agent_789",
    permission="execute"
)
```

---

## Feedback Loop

### Collecting Feedback

```python
# Rate agent
rate_agent(
    agent_id="agent_123",
    rating=5,
    user_id="user_456",
    tenant_id="tenant_123",
    feedback_text="Very helpful!"
)

# View statistics
stats = get_agent_feedback_stats("agent_123")
print(f"Average rating: {stats['average_rating']}")
```

### Continuous Improvement

The system uses feedback to:
- Improve prompt interpretation
- Refine generation algorithms
- Identify best practices
- Learn from high-rated examples

---

## Caching Strategy

### Cache Levels

1. **Prompt Interpretation** (24 hours TTL)
2. **Agent Configuration** (7 days TTL)
3. **Tool Schema** (7 days TTL)
4. **Generated Code** (30 days TTL)

### Cache Benefits

- **Cost Savings**: Avoid re-interpreting similar prompts
- **Performance**: Instant retrieval for cached items
- **Consistency**: Same prompt = same result

---

## Memory Management

### Agent Memory Limits

- Per-tenant agent limits
- Automatic cleanup of unused agents
- Memory pooling for frequently used agents

### Tool Memory Management

- Tool registry limits per tenant
- Tool lifecycle tracking
- Code caching for efficiency

---

## Best Practices

1. **Clear Prompts**: Be specific about requirements
2. **Test Thoroughly**: Always test generated agents/tools
3. **Provide Feedback**: Rate agents/tools to improve quality
4. **Set Permissions**: Configure appropriate access control
5. **Monitor Usage**: Track performance and effectiveness
6. **Review Code**: Check generated tool code for security

---

## Troubleshooting

See [Troubleshooting Guide](../troubleshooting/prompt_generator_troubleshooting.md) for common issues and solutions.

---

## Related Documentation

- [User Guide](../guides/prompt_based_creation_guide.md)
- [Implementation Plan](../architecture/PROMPT_BASED_GENERATOR_IMPLEMENTATION_PLAN.md)
- [Component README](../../src/core/prompt_based_generator/README.md)

