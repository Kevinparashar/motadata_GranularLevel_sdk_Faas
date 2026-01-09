# Getting Started with Prompt Context Management

## Overview

The Prompt Context Management component provides template-based prompts with versioning, context building, and token management. This guide explains the complete workflow from template creation to prompt rendering.

## Entry Point

The primary entry point for creating prompt managers is through factory functions:

```python
from src.core.prompt_context_management import (
    create_prompt_manager,
    render_prompt,
    build_context
)
```

## Input Requirements

### Required Inputs

1. **Prompt Manager Configuration**:
   - `max_tokens`: Maximum tokens for context window (default: 8000)

### Optional Inputs

- `token_estimation_model`: Model for token estimation
- `enable_truncation`: Enable automatic truncation
- `enable_redaction`: Enable sensitive data redaction

## Process Flow

### Step 1: Prompt Manager Creation

**What Happens:**
1. Prompt manager is initialized
2. Context window manager is created
3. Token estimator is configured
4. Template storage is initialized

**Code:**
```python
manager = create_prompt_manager(max_tokens=8000)
```

**Internal Process:**
```
create_prompt_manager()
  ├─> Initialize template storage
  ├─> Configure context window
  ├─> Set up token estimator
  └─> Return manager instance
```

### Step 2: Template Creation

**What Happens:**
1. Template is validated
2. Template is stored with version
3. Template metadata is recorded

**Code:**
```python
manager.add_template(
    template_id="greeting",
    template="Hello, {{name}}! How can I help you today?",
    version="1.0.0",
    description="Greeting template"
)
```

**Input:**
- `template_id`: Unique template identifier
- `template`: Template string with variables ({{variable}})
- `version`: Template version
- `description`: Optional description

**Internal Process:**
```
add_template()
  ├─> Validate template syntax
  ├─> Extract variables
  ├─> Store template with version
  └─> Record metadata
```

### Step 3: Prompt Rendering

**What Happens:**
1. Template is retrieved
2. Variables are substituted
3. Template is rendered
4. Result is returned

**Code:**
```python
prompt = render_prompt(
    manager,
    template_id="greeting",
    variables={"name": "Alice"}
)
# Result: "Hello, Alice! How can I help you today?"
```

**Input:**
- `manager`: Prompt manager instance
- `template_id`: Template to render
- `variables`: Dictionary of variables to substitute
- `version`: Optional template version (uses latest if not specified)

**Internal Process:**
```
render_prompt()
  ├─> Retrieve template
  ├─> Validate variables
  ├─> Substitute variables
  └─> Return rendered prompt
```

### Step 4: Context Building

**What Happens:**
1. Context is assembled from history
2. New message is added
3. Token count is estimated
4. Context is truncated if needed
5. Final context is returned

**Code:**
```python
context = build_context(
    manager,
    new_message="What is AI?",
    include_history=True,
    history=[
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi! How can I help?"}
    ],
    max_tokens=4000
)
```

**Input:**
- `manager`: Prompt manager instance
- `new_message`: New message to add
- `include_history`: Whether to include conversation history
- `history`: List of previous messages
- `max_tokens`: Maximum tokens for context

**Internal Process:**
```
build_context()
  ├─> Estimate tokens for history
  ├─> Estimate tokens for new message
  ├─> Truncate if exceeds max_tokens
  ├─> Assemble context
  └─> Return formatted context
```

## Output

### Template Rendering Output

```python
# Rendered prompt string
"Hello, Alice! How can I help you today?"
```

### Context Building Output

```python
{
    "context": "User: Hello\nAssistant: Hi! How can I help?\nUser: What is AI?",
    "token_count": 25,
    "truncated": False,
    "history_included": True
}
```

## Where Output is Used

### 1. Direct Usage

```python
# Render prompt for direct use
prompt = render_prompt(manager, "greeting", {"name": "Alice"})
print(prompt)
```

### 2. Integration with Agent Framework

```python
# Agents automatically use prompt management
agent = create_agent(agent_id="agent_001", gateway=gateway, ...)
agent.prompt_manager = manager

# Agent uses templates during task execution
# Templates are automatically applied to agent prompts
```

### 3. Integration with LiteLLM Gateway

```python
# Build context before sending to gateway
context = build_context(
    manager,
    new_message="What is AI?",
    include_history=True
)

response = gateway.generate(
    prompt=context["context"],
    model="gpt-4"
)
```

### 4. Integration with RAG System

```python
# Use templates for RAG queries
template = render_prompt(
    manager,
    template_id="rag_query",
    variables={
        "query": "What is AI?",
        "context": rag_context
    }
)

result = rag.query(template)
```

## Complete Example

```python
from src.core.prompt_context_management import (
    create_prompt_manager,
    render_prompt,
    build_context
)

# Step 1: Create Manager (Entry Point)
manager = create_prompt_manager(max_tokens=8000)

# Step 2: Add Templates (Input)
manager.add_template(
    template_id="greeting",
    template="Hello, {{name}}! How can I help you today?",
    version="1.0.0"
)

manager.add_template(
    template_id="rag_query",
    template="""Based on the following context:
{{context}}

Answer this question: {{query}}""",
    version="1.0.0"
)

# Step 3: Render Prompt (Process)
greeting = render_prompt(
    manager,
    template_id="greeting",
    variables={"name": "Alice"}
)
print(greeting)  # "Hello, Alice! How can I help you today?"

# Step 4: Build Context (Process)
context = build_context(
    manager,
    new_message="What is artificial intelligence?",
    include_history=True,
    history=[
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi! How can I help?"}
    ],
    max_tokens=4000
)

# Step 5: Use Output
# Use rendered prompt or context in your application
print(context["context"])
```

## Important Information

### Token Estimation

```python
from src.core.prompt_context_management import estimate_tokens

token_count = estimate_tokens(
    text="Hello, world!",
    model="gpt-4"
)
print(f"Estimated tokens: {token_count}")
```

### Truncation

```python
from src.core.prompt_context_management import truncate_to_fit

truncated = truncate_to_fit(
    manager,
    text="Very long text...",
    max_tokens=100
)
```

### Sensitive Data Redaction

```python
from src.core.prompt_context_management import redact_sensitive

redacted = redact_sensitive(
    text="User email: john@example.com",
    patterns=["email", "phone"]
)
# Result: "User email: [REDACTED]"
```

### Template Versioning

```python
# Add new version of template
manager.add_template(
    template_id="greeting",
    template="Hi, {{name}}! What can I do for you?",
    version="2.0.0"
)

# Render specific version
prompt = render_prompt(
    manager,
    template_id="greeting",
    variables={"name": "Alice"},
    version="1.0.0"  # Use old version
)
```

## Next Steps

- See [README.md](README.md) for detailed component documentation
- Check [component_explanation/prompt_context_management_explanation.md](../../../component_explanation/prompt_context_management_explanation.md) for comprehensive guide
- Review [troubleshooting guide](../../../docs/troubleshooting/prompt_context_management_troubleshooting.md) for common issues

