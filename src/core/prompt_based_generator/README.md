# Prompt-Based Generator

## Overview

The Prompt-Based Generator enables creation of AI agents and tools from natural language prompts. Users can describe what they want in plain English, and the system automatically generates fully configured agents and tools.

## Key Features

- **Natural Language Input**: Describe agents and tools in plain English
- **Automatic Configuration**: System extracts requirements and generates configurations
- **Code Generation**: Automatically generates tool code from descriptions
- **Access Control**: Built-in permission management for resources
- **Feedback Loop**: Collect and process user feedback for continuous improvement
- **Caching**: Efficient caching of interpretations and configurations

## Quick Start

### Creating an Agent from Prompt

```python
from src.core.prompt_based_generator import create_agent_from_prompt
from src.core.litellm_gateway import create_gateway

# Create gateway
gateway = create_gateway(
    api_key="your-api-key",
    provider="openai"
)

# Create agent from natural language
agent = await create_agent_from_prompt(
    prompt="""
    Create a customer support agent that:
    - Categorizes support tickets by type
    - Suggests solutions from knowledge base
    - Escalates complex issues to human agents
    - Tracks resolution time
    """,
    gateway=gateway,
    tenant_id="tenant_123",
    user_id="user_456"
)

# Use the agent
response = await agent.execute_task(task)
```

### Creating a Tool from Prompt

```python
from src.core.prompt_based_generator import create_tool_from_prompt

# Create tool from natural language
tool = await create_tool_from_prompt(
    prompt="""
    Create a tool that calculates ticket priority.
    Inputs: urgency (1-5), impact (1-5), customer_tier (bronze/silver/gold/platinum)
    Output: Priority score 1-5
    """,
    gateway=gateway,
    tenant_id="tenant_123"
)

# Use the tool
priority = tool.execute(urgency=4, impact=5, customer_tier="gold")
```

## Components

### PromptInterpreter

Interprets natural language prompts using LLM to extract structured requirements.

### AgentGenerator

Generates fully configured Agent instances from interpreted requirements.

### ToolGenerator

Generates Tool instances with executable code from interpreted requirements.

### AccessControl

Manages permissions for agents and tools with tenant isolation.

### FeedbackCollector

Collects and processes user feedback for agents and tools.

### GeneratorCache

Specialized caching for prompt interpretations and generated configurations.

## Access Control

```python
from src.core.prompt_based_generator import grant_permission, check_permission

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

## Feedback Collection

```python
from src.core.prompt_based_generator import rate_agent, rate_tool, get_agent_feedback_stats

# Rate an agent
rate_agent(
    agent_id="agent_123",
    rating=5,
    user_id="user_456",
    tenant_id="tenant_123",
    feedback_text="Very helpful!"
)

# Get feedback statistics
stats = get_agent_feedback_stats("agent_123", tenant_id="tenant_123")
print(f"Average rating: {stats['average_rating']}")
```

## Caching

The system automatically caches:
- Prompt interpretations (24 hours)
- Agent configurations (7 days)
- Tool schemas (7 days)
- Generated code (30 days)

## Best Practices

1. **Clear Prompts**: Be specific about requirements and capabilities
2. **Feedback**: Provide feedback to improve generation quality
3. **Permissions**: Set appropriate permissions for security
4. **Caching**: Leverage caching for repeated similar prompts
5. **Validation**: Review generated agents/tools before production use

## Error Handling

The component provides specific exceptions:
- `PromptInterpretationError`: Prompt interpretation failed
- `AgentGenerationError`: Agent generation failed
- `ToolGenerationError`: Tool generation failed
- `CodeValidationError`: Generated code is invalid
- `AccessControlError`: Permission denied

## See Also

- `getting-started.md` - Detailed getting started guide
- `docs/components/prompt_based_generator_explanation.md` - Comprehensive explanation
- `docs/guides/prompt_based_creation_guide.md` - User guide

