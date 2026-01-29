# Motadata Prompt-Based Generator Functions Documentation

## Overview

The `functions.py` file provides high-level factory functions and convenience functions for the Prompt-Based Generator system. These functions enable creating agents and tools from natural language prompts, making it easy for users to generate AI components without manual configuration.

**Primary Functionality:**
- Create agents from natural language prompts
- Create tools from natural language prompts
- Feedback collection for generated components
- Permission management for generated resources
- Feedback statistics retrieval

## Code Explanation

### Function Categories

#### 1. Agent Generation Functions
- **`create_agent_from_prompt()`**: Create agent from natural language prompt
- **`create_agent_from_prompt_async()`**: Async version

#### 2. Tool Generation Functions
- **`create_tool_from_prompt()`**: Create tool from natural language prompt
- **`create_tool_from_prompt_async()`**: Async version

#### 3. Feedback Functions
- **`rate_agent()`**: Rate a generated agent
- **`rate_tool()`**: Rate a generated tool
- **`get_agent_feedback_stats()`**: Get agent feedback statistics
- **`get_tool_feedback_stats()`**: Get tool feedback statistics

#### 4. Permission Functions
- **`grant_permission()`**: Grant permission for a resource
- **`check_permission()`**: Check permission for a resource

### Key Functions

#### `async def create_agent_from_prompt(prompt, gateway, **kwargs) -> Agent`
Creates an agent from a natural language prompt.

**Parameters:**
- `prompt`: Natural language description of desired agent
- `gateway`: LiteLLM Gateway instance
- `agent_id`: Optional agent ID
- `tenant_id`: Optional tenant ID
- `user_id`: Optional user ID
- `cache`: Optional GeneratorCache instance
- `**kwargs`: Additional agent configuration

**Returns:** Configured `Agent` instance

**Example:**
```python
from src.core.prompt_based_generator import create_agent_from_prompt
from src.core.litellm_gateway import create_gateway

gateway = create_gateway(api_keys={'openai': 'key'}, default_model='gpt-4')

agent = await create_agent_from_prompt(
    prompt="Create a customer support agent that categorizes tickets",
    gateway=gateway,
    tenant_id="tenant_123"
)
```

#### `async def create_tool_from_prompt(prompt, gateway, **kwargs) -> Tool`
Creates a tool from a natural language prompt.

**Parameters:**
- `prompt`: Natural language description of desired tool
- `gateway`: LiteLLM Gateway instance
- `tool_id`: Optional tool ID
- `tenant_id`: Optional tenant ID
- `user_id`: Optional user ID
- `cache`: Optional GeneratorCache instance
- `**kwargs`: Additional tool configuration

**Returns:** Configured `Tool` instance

**Example:**
```python
from src.core.prompt_based_generator import create_tool_from_prompt

tool = await create_tool_from_prompt(
    prompt="Create a tool that calculates priority based on urgency and impact",
    gateway=gateway,
    tenant_id="tenant_123"
)
```

#### `rate_agent(agent_id, rating, feedback=None, **kwargs) -> None`
Rates a generated agent.

**Parameters:**
- `agent_id`: Agent ID
- `rating`: Rating (1-5)
- `feedback`: Optional feedback text
- `tenant_id`: Optional tenant ID
- `user_id`: Optional user ID

#### `get_agent_feedback_stats(agent_id, tenant_id=None) -> Dict[str, Any]`
Gets feedback statistics for an agent.

**Parameters:**
- `agent_id`: Agent ID
- `tenant_id`: Optional tenant ID

**Returns:** Dictionary with feedback statistics

#### `grant_permission(resource_type, resource_id, user_id, permission, **kwargs) -> None`
Grants permission for a resource.

**Parameters:**
- `resource_type`: Resource type ("agent" or "tool")
- `resource_id`: Resource ID
- `user_id`: User ID
- `permission`: Permission type ("read", "write", "execute")
- `tenant_id`: Optional tenant ID

## Usage Instructions

### Creating Agent from Prompt

```python
from src.core.prompt_based_generator import create_agent_from_prompt
from src.core.litellm_gateway import create_gateway

gateway = create_gateway(api_keys={'openai': 'key'}, default_model='gpt-4')

agent = await create_agent_from_prompt(
    prompt="""
    Create a customer support agent that:
    - Categorizes support tickets by type
    - Suggests solutions from knowledge base
    - Escalates complex issues to human agents
    """,
    gateway=gateway,
    tenant_id="tenant_123",
    user_id="user_456"
)
```

### Creating Tool from Prompt

```python
from src.core.prompt_based_generator import create_tool_from_prompt

tool = await create_tool_from_prompt(
    prompt="Create a tool that calculates priority based on urgency and impact",
    gateway=gateway,
    tenant_id="tenant_123"
)
```

### Feedback Collection

```python
from src.core.prompt_based_generator import rate_agent, get_agent_feedback_stats

# Rate agent
rate_agent(
    agent_id="agent_123",
    rating=5,
    feedback="Great agent!",
    tenant_id="tenant_123",
    user_id="user_456"
)

# Get feedback statistics
stats = get_agent_feedback_stats("agent_123", tenant_id="tenant_123")
print(f"Average rating: {stats['average_rating']}")
```

### Permission Management

```python
from src.core.prompt_based_generator import grant_permission

grant_permission(
    resource_type="agent",
    resource_id="agent_123",
    user_id="user_456",
    permission="read",
    tenant_id="tenant_123"
)
```

### Prerequisites

1. **Python 3.10+**: Required for type hints and async/await
2. **Dependencies**: Install via `pip install -r requirements.txt`
   - `litellm`: For LLM operations
   - `pydantic`: For data validation
3. **API Keys**: LLM provider API keys

## Connection to Other Components

### Agent Generator
Uses `AgentGenerator` from `src/core/prompt_based_generator/agent_generator.py`:
- Interprets prompts
- Generates agent configurations
- Creates agent instances

**Integration Point:** `create_agent_from_prompt()` uses AgentGenerator

### Tool Generator
Uses `ToolGenerator` from `src/core/prompt_based_generator/tool_generator.py`:
- Interprets prompts
- Generates tool code
- Creates tool instances

**Integration Point:** `create_tool_from_prompt()` uses ToolGenerator

### Prompt Interpreter
Uses `PromptInterpreter` from `src/core/prompt_based_generator/prompt_interpreter.py`:
- Interprets natural language prompts
- Extracts requirements
- Generates configurations

**Integration Point:** Both generators use PromptInterpreter

### LiteLLM Gateway
Uses `LiteLLMGateway` from `src/core/litellm_gateway/gateway.py`:
- Required for LLM operations
- Generates interpretations and code

**Integration Point:** `gateway` parameter in all functions

### Access Control
Uses `AccessControl` from `src/core/prompt_based_generator/access_control.py`:
- Manages permissions
- Controls resource access

**Integration Point:** Permission functions use AccessControl

### Feedback System
Uses `FeedbackCollector` from `src/core/prompt_based_generator/feedback_integration.py`:
- Collects user feedback
- Tracks ratings
- Provides statistics

**Integration Point:** Feedback functions use FeedbackCollector

### Where Used
- **FaaS Prompt Generator Service**: REST API wrapper uses these functions
- **Examples**: All prompt-based examples use these functions
- **User Applications**: Primary interface for prompt-based generation

## Best Practices

### 1. Use Async Functions
Always prefer async functions:
```python
# Good: Async
agent = await create_agent_from_prompt(prompt, gateway)

# Bad: Synchronous (if available)
agent = create_agent_from_prompt(prompt, gateway)
```

### 2. Provide Clear Prompts
Write clear, detailed prompts:
```python
# Good: Clear and detailed
prompt = """
Create a customer support agent that:
- Categorizes tickets by type (technical, billing, general)
- Suggests solutions from knowledge base
- Escalates complex issues
- Tracks resolution time
"""

# Bad: Vague
prompt = "Create a support agent"
```

### 3. Provide Tenant IDs
Always provide tenant_id for multi-tenant applications:
```python
# Good: Tenant-scoped
agent = await create_agent_from_prompt(
    prompt="...",
    gateway=gateway,
    tenant_id="tenant_123"
)

# Bad: Missing tenant_id
agent = await create_agent_from_prompt(prompt="...", gateway=gateway)
```

### 4. Collect Feedback
Collect feedback to improve generation:
```python
# Good: Collect feedback
rate_agent(
    agent_id="agent_123",
    rating=5,
    feedback="Works well!",
    tenant_id="tenant_123"
)

# Bad: No feedback (can't improve)
```

### 5. Manage Permissions
Grant appropriate permissions:
```python
# Good: Grant permissions
grant_permission(
    resource_type="agent",
    resource_id="agent_123",
    user_id="user_456",
    permission="read",
    tenant_id="tenant_123"
)

# Bad: No permission management
```

## Additional Resources

### Documentation
- **[Prompt-Based Generator README](README.md)** - Complete guide
- **[Agent Generator Documentation](agent_generator.md)** - Agent generation
- **[Tool Generator Documentation](tool_generator.md)** - Tool generation

### Related Components
- **[Agent Generator](agent_generator.py)** - Agent generation implementation
- **[Tool Generator](tool_generator.py)** - Tool generation implementation
- **[Prompt Interpreter](prompt_interpreter.py)** - Prompt interpretation

### External Resources
- **[Natural Language Processing](https://en.wikipedia.org/wiki/Natural_language_processing)** - NLP concepts
- **[Code Generation](https://en.wikipedia.org/wiki/Automatic_programming)** - Code generation

### Examples
- **[Prompt-Based Agent Example](../../../../examples/prompt_based/)** - Agent creation
- **[Prompt-Based Tool Example](../../../../examples/prompt_based/)** - Tool creation

