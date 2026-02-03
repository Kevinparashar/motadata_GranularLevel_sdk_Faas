# MOTADATA - GETTING STARTED WITH PROMPT-BASED GENERATOR

**Complete guide for getting started with creating AI agents and tools using natural language descriptions.**

## Introduction

The Prompt-Based Generator allows you to create AI agents and tools using natural language descriptions. This guide will walk you through the basics.

## Prerequisites

- LiteLLM Gateway instance
- API key for LLM provider (OpenAI, Anthropic, etc.)
- Python 3.8+

## Installation

The component is part of the SDK. No additional installation needed.

## Basic Usage

### Step 1: Create a Gateway

```python
from src.core.litellm_gateway import create_gateway

gateway = create_gateway(
    api_key="your-api-key",
    provider="openai",
    default_model="gpt-4"
)
```

### Step 2: Create an Agent from Prompt

```python
from src.core.prompt_based_generator import create_agent_from_prompt

agent = await create_agent_from_prompt(
    prompt="Create a helpful assistant that answers questions about products",
    gateway=gateway,
    tenant_id="tenant_123"
)
```

### Step 3: Use the Agent

```python
from src.core.agno_agent_framework import AgentTask

task = AgentTask(
    task_id="task_1",
    task_type="answer_question",
    parameters={"question": "What is your return policy?"}
)

response = await agent.execute_task(task)
```

## Advanced Examples

### Creating a Specialized Agent

```python
agent = await create_agent_from_prompt(
    prompt="""
    Create a technical support agent with these capabilities:
    1. Diagnose technical issues from descriptions
    2. Provide step-by-step troubleshooting guides
    3. Escalate to human support when needed
    4. Track issue resolution time
    5. Learn from resolved tickets
    """,
    gateway=gateway,
    tenant_id="tenant_123",
    agent_id="tech_support_001"
)
```

### Creating a Custom Tool

```python
tool = await create_tool_from_prompt(
    prompt="""
    Create a tool that calculates SLA compliance.
    Inputs:
    - resolution_time: hours to resolve
    - sla_target: target hours
    - priority: low/medium/high/critical
    
    Output: compliance percentage (0-100)
    """,
    gateway=gateway,
    tenant_id="tenant_123"
)
```

## Next Steps

- Read the full [README.md](README.md)
- Explore [examples](../../../examples/prompt_based/)
- Check [troubleshooting guide](../../../docs/troubleshooting/prompt_generator_troubleshooting.md)

