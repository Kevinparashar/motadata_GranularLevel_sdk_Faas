# MOTADATA - PROMPT CONTEXT MANAGEMENT

**Comprehensive explanation of the Prompt Context Management component providing unified system for managing prompts, templates, context building, and optimization.**

## Overview

The Prompt Context Management component provides a unified system for managing prompts, templates, and context throughout the SDK. It handles prompt template creation, versioning, context building, prompt optimization, and dynamic prompting capabilities.

## Table of Contents

1. [Template Management](#template-management)
2. [Context Building](#context-building)
3. [Dynamic Prompting](#dynamic-prompting)
4. [Prompt Optimization](#prompt-optimization)
5. [Fallback Templates](#fallback-templates)
6. [Exception Handling](#exception-handling)
7. [Functions](#functions)
8. [Workflow](#workflow)
9. [Customization](#customization)

---

## Template Management

### Functionality

Template management handles prompt templates:
- **Template Storage**: Stores templates with versioning and tenant isolation
- **Template Rendering**: Renders templates with variable substitution
- **Version Management**: Tracks template versions and changes
- **Tenant Isolation**: Ensures templates are isolated per tenant

### Code Examples

#### Creating and Using Templates

```python
from src.core.prompt_context_management import create_prompt_manager

# Create prompt manager
manager = create_prompt_manager(max_tokens=8000)

# Add template
manager.add_template(
    name="analysis_template",
    version="1.0",
    content="Analyze the following: {input}\nConsider: {context}",
    tenant_id="tenant_123",
    metadata={"author": "AI Team", "category": "analysis"}
)

# Render template
prompt = manager.render(
    template_name="analysis_template",
    variables={
        "input": "Sales data shows 20% growth",
        "context": "Q4 2023 results"
    },
    tenant_id="tenant_123"
)
```

#### Template Versioning

```python
# Add multiple versions
manager.add_template(
    name="greeting",
    version="1.0",
    content="Hello {name}!",
    tenant_id="tenant_123"
)

manager.add_template(
    name="greeting",
    version="2.0",
    content="Hello {name}! Welcome to our service.",
    tenant_id="tenant_123"
)

# Get latest version (default)
prompt = manager.render("greeting", {"name": "John"}, tenant_id="tenant_123")
# Uses version 2.0

# Get specific version
prompt = manager.render("greeting", {"name": "John"}, tenant_id="tenant_123", version="1.0")
# Uses version 1.0
```

---

## Context Building

### Functionality

Context building assembles context from multiple sources:
- **History Management**: Maintains conversation history
- **Context Prioritization**: Prioritizes important context
- **Token Management**: Enforces token limits
- **Context Truncation**: Intelligently truncates context

### Code Examples

#### Building Context with History

```python
# Record history
manager.record_history("User: What is AI?")
manager.record_history("Assistant: AI is...")

# Build context with new message
context = manager.build_context_with_history("User: Tell me more")

# Context includes history and new message, respecting token limits
```

#### Token Management

```python
# Estimate tokens
tokens = manager.window.estimate_tokens("Hello world")
print(f"Estimated tokens: {tokens}")

# Truncate prompt to fit token limit
truncated = manager.truncate_prompt(
    long_prompt,
    max_tokens=2000
)
```

---

## Dynamic Prompting

### Functionality

Dynamic prompting adjusts prompts based on context:
- **Context-Aware Prompts**: Automatically adjusts based on available context
- **Adaptive Templates**: Templates adapt to different scenarios
- **Dynamic Variable Injection**: Variables injected dynamically
- **Context-Based Selection**: Selects appropriate prompts based on context

### Code Examples

```python
from src.core.prompt_context_management.prompt_enhancements import DynamicPromptBuilder

# Create dynamic prompt builder
builder = DynamicPromptBuilder(manager.store)

# Build dynamic prompt
prompt = builder.build_dynamic_prompt(
    template_name="analysis_template",
    variables={"input": "Analyze this"},
    context={
        "user_role": "admin",
        "document_type": "incident",
        "urgency": "high"
    },
    tenant_id="tenant_123"
)

# Prompt automatically adjusts based on context
```

---

## Prompt Optimization

### Functionality

Prompt optimization improves prompt effectiveness:
- **Effectiveness Analysis**: Analyzes prompt effectiveness
- **Automatic Tuning**: Automatically tunes prompts
- **Optimization Strategies**: Multiple optimization strategies
- **Performance Tracking**: Tracks prompt performance

### Code Examples

```python
from src.core.prompt_context_management.prompt_enhancements import PromptOptimizer

# Create optimizer
optimizer = PromptOptimizer()

# Optimize prompt
optimized_prompt = optimizer.optimize(
    prompt="Analyze this data",
    context={"domain": "technical"}
)

# Get optimization suggestions
suggestions = optimizer.get_suggestions("analysis_template")
```

---

## Fallback Templates

### Functionality

Fallback templates ensure continuity:
- **Automatic Fallback**: Falls back to default templates
- **Fallback Chain**: Configurable fallback chain
- **Template Availability**: Checks template availability
- **Graceful Degradation**: Gracefully degrades when templates unavailable

### Code Examples

```python
from src.core.prompt_context_management.prompt_enhancements import FallbackTemplateManager

# Create fallback manager
fallback_manager = FallbackTemplateManager(
    manager.store,
    fallback_chain=["analysis_template", "default_template", "basic_template"]
)

# Render with fallback
prompt = fallback_manager.render_with_fallback(
    template_name="custom_template",  # Falls back if not found
    variables={"input": "Analyze this"},
    tenant_id="tenant_123"
)
```

---

## Exception Handling

The component handles errors gracefully:
- **Template Errors**: Validates templates and reports errors
- **Context Errors**: Handles errors when gathering context
- **Token Limit Exceeded**: Handles cases where context exceeds limits
- **Validation Failures**: Reports validation failures

### Code Examples

```python
try:
    prompt = manager.render("nonexistent_template", {}, tenant_id="tenant_123")
except ValueError as e:
    print(f"Template error: {e}")
    # Handle error - use fallback template
```

---

## Functions

### Factory Functions

```python
from src.core.prompt_context_management import (
    create_prompt_manager,
    create_context_window_manager
)

# Create prompt manager
manager = create_prompt_manager(max_tokens=8000)

# Create context window manager
window = create_context_window_manager(max_tokens=8000)
```

### Convenience Functions

```python
from src.core.prompt_context_management import (
    render_prompt,
    add_template,
    build_context,
    truncate_to_fit
)

# Render prompt
prompt = render_prompt(
    manager,
    "analysis_template",
    {"text": "Analyze this", "model": "gpt-4"}
)

# Add template
add_template(
    manager,
    "greeting",
    "1.0",
    "Hello {name}, welcome to {service}!"
)

# Build context
context = build_context(manager, "What is AI?", include_history=True)

# Truncate prompt
truncated = truncate_to_fit(manager, long_prompt, max_tokens=2000)
```

---

## Workflow

### Component Placement in SDK Architecture

The Prompt Context Management is positioned in the **Core Layer** and integrates with multiple components:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SDK ARCHITECTURE OVERVIEW                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ API Backend  │  │   RAG System  │  │   Agents     │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
┌─────────┼──────────────────┼──────────────────┼─────────────────┐
│         │                  │                  │                  │
│  ┌──────▼──────────────────▼──────────────────▼──────┐          │
│  │  PROMPT CONTEXT MANAGEMENT (Core Layer)           │          │
│  │  ┌──────────────┐  ┌──────────────┐             │          │
│  │  │  Template    │  │   Context     │             │          │
│  │  │  Management  │  │   Building    │             │          │
│  │  └──────┬───────┘  └──────┬───────┘             │          │
│  │         │                 │                      │          │
│  │  ┌──────▼─────────────────▼──────┐              │          │
│  │  │  PromptContextManager          │              │          │
│  │  │  (Orchestrator)                │              │          │
│  │  └──────┬─────────────────────────┘              │          │
│  │         │                                         │          │
│  │  ┌──────▼─────────────────────────┐              │          │
│  │  │  Advanced Features:             │              │          │
│  │  │  - Dynamic Prompting            │              │          │
│  │  │  - Prompt Optimization          │              │          │
│  │  │  - Fallback Templates           │              │          │
│  │  └─────────────────────────────────┘              │          │
│  └───────────────────────────────────────────────────┘          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │LiteLLM       │  │  Agent       │  │  RAG          │         │
│  │Gateway       │  │  Memory      │  │  Generator    │         │
│  │              │  │              │  │              │         │
│  │ - Receives   │  │ - Provides   │  │ - Uses        │         │
│  │   prompts    │  │   context    │  │   templates   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│                    CORE LAYER                                    │
└──────────────────────────────────────────────────────────────────┘
```

### Template Rendering Workflow

The following diagram shows the complete flow of template rendering:

```
┌─────────────────────────────────────────────────────────────────┐
│              TEMPLATE RENDERING WORKFLOW                          │
└─────────────────────────────────────────────────────────────────┘

    [Render Request]
           │
           │ Parameters:
           │ - template_name: str
           │ - variables: Dict[str, Any]
           │ - tenant_id: Optional[str]
           │ - version: Optional[str]
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 1: Template Retrieval                             │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ manager.render(template_name, variables, tenant_id)│  │
    │  │                                                   │  │
    │  │ Code Flow:                                       │  │
    │  │ 1. Get tenant-specific templates:                │  │
    │  │    tenant_templates = store._templates.get(tenant_id)│
    │  │ 2. Get template versions:                        │  │
    │  │    versions = tenant_templates.get(template_name)│
    │  │ 3. Select version:                               │  │
    │  │    if version:                                   │  │
    │  │        template = versions.get(version)          │  │
    │  │    else:                                         │  │
    │  │        # Get latest version                     │  │
    │  │        latest = sorted(versions.keys())[-1]     │  │
    │  │        template = versions[latest]              │  │
    │  │                                                   │  │
    │  │ Template Structure:                              │  │
    │  │ {                                                │  │
    │  │   tenant_id: {                                   │  │
    │  │     template_name: {                             │  │
    │  │       version: PromptTemplate                    │  │
    │  │     }                                            │  │
    │  │   }                                              │  │
    │  │ }                                                │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 2: Template Validation                            │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ if not template:                                   │  │
    │  │     raise ValueError(f"Template '{name}' not found")│
    │  │                                                   │  │
    │  │ Validation Checks:                                 │  │
    │  │ - Template exists                                  │  │
    │  │ - Template is accessible for tenant               │  │
    │  │ - Version exists (if specified)                   │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 3: Variable Substitution                          │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ prompt = template.content.format(**variables)     │  │
    │  │                                                   │  │
    │  │ Template Format:                                  │  │
    │  │ "Analyze the following: {input}\nConsider: {context}"│
    │  │                                                   │  │
    │  │ Variables Provided:                                │  │
    │  │ {                                                  │  │
    │  │   "input": "Sales data shows 20% growth",         │  │
    │  │   "context": "Q4 2023 results"                    │  │
    │  │ }                                                  │  │
    │  │                                                   │  │
    │  │ Result:                                            │  │
    │  │ "Analyze the following: Sales data shows 20% growth│
    │  │ Consider: Q4 2023 results"                        │  │
    │  │                                                   │  │
    │  │ Error Handling:                                   │  │
    │  │ - Missing variables: KeyError                     │  │
    │  │ - Invalid format: ValueError                     │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 4: Dynamic Prompting (if enabled)                  │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ if dynamic_prompting_enabled:                      │  │
    │  │     prompt = builder.build_dynamic_prompt(        │  │
    │  │         template_name,                             │  │
    │  │         variables,                                 │  │
    │  │         context                                    │  │
    │  │     )                                             │  │
    │  │                                                   │  │
    │  │ Dynamic Adjustments:                               │  │
    │  │ 1. Apply context adapters                         │  │
    │  │ 2. Adjust based on user_role                      │  │
    │  │ 3. Adjust based on urgency                        │  │
    │  │ 4. Adjust based on domain                         │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 5: Prompt Optimization (if enabled)               │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ if optimization_enabled:                          │  │
    │  │     prompt = optimizer.optimize(prompt, context)  │  │
    │  │                                                   │  │
    │  │ Optimization Steps:                               │  │
    │  │ 1. Apply optimization rules                       │  │
    │  │ 2. Improve clarity and structure                  │  │
    │  │ 3. Enhance effectiveness                          │  │
    │  │ 4. Track optimization history                     │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 6: Token Management                                │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ tokens = window.estimate_tokens(prompt)           │  │
    │  │                                                   │  │
    │  │ if tokens > max_tokens:                           │  │
    │  │     prompt = window.truncate(prompt, max_tokens) │  │
    │  │                                                   │  │
    │  │ Token Estimation:                                 │  │
    │  │ - Simple heuristic: tokens ≈ words               │  │
    │  │ - Used for context window management              │  │
    │  │                                                   │  │
    │  │ Truncation:                                       │  │
    │  │ - Preserves word boundaries                       │  │
    │  │ - Respects safety_margin                          │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 7: History Recording                               │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ manager.record_history(prompt)                     │  │
    │  │                                                   │  │
    │  │ History Management:                                │  │
    │  │ - Stores prompts for context building              │  │
    │  │ - Maintains conversation history                  │  │
    │  │ - Used for context-aware prompts                  │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    [Return Rendered Prompt]
```

### Context Building Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│              CONTEXT BUILDING WORKFLOW                          │
└─────────────────────────────────────────────────────────────────┘

    [Build Context Request]
           │
           │ Parameters:
           │ - new_message: str
           │ - include_history: bool
           │ - max_tokens: Optional[int]
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 1: Gather Context Sources                          │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ messages = []                                     │  │
    │  │                                                   │  │
    │  │ if include_history:                               │  │
    │  │     messages.extend(manager.history)             │  │
    │  │                                                   │  │
    │  │ messages.append(new_message)                      │  │
    │  │                                                   │  │
    │  │ Context Sources:                                  │  │
    │  │ - Conversation history                            │  │
    │  │ - New message                                     │  │
    │  │ - System context (if available)                    │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 2: Token Limit Calculation                         │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ limit = (max_tokens or window.max_tokens) - safety_margin│
    │  │                                                   │  │
    │  │ Safety Margin:                                    │  │
    │  │ - Prevents token overflow                         │  │
    │  │ - Default: 200 tokens                             │  │
    │  │ - Configurable per instance                       │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 3: Context Selection                               │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ selected = []                                    │  │
    │  │ context_tokens = 0                                │  │
    │  │                                                   │  │
    │  │ # Process messages in reverse (newest first)     │  │
    │  │ for msg in reversed(messages):                   │  │
    │  │     msg_tokens = window.estimate_tokens(msg)     │  │
    │  │     if context_tokens + msg_tokens > limit:     │  │
    │  │         break  # Stop if exceeds limit           │  │
    │  │     selected.append(msg)                         │  │
    │  │     context_tokens += msg_tokens                 │  │
    │  │                                                   │  │
    │  │ # Reverse to preserve chronological order        │  │
    │  │ selected = reversed(selected)                    │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 4: Context Assembly                                 │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ context = "\n".join(selected)                      │  │
    │  │                                                   │  │
    │  │ Context Format:                                    │  │
    │  │ "Message 1\nMessage 2\nMessage 3"                 │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    [Return Context String]
```

### Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│              COMPONENT INTERACTION FLOW                          │
└─────────────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │PromptContext │
                    │  Manager     │
                    │  (Core)      │
                    └──────┬───────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ PromptStore   │  │ContextWindow  │  │  Enhancements│
│               │  │   Manager     │  │               │
│ Functions:    │  │               │  │ - Dynamic     │
│ - add()       │  │ Functions:    │  │   Builder    │
│ - get()       │  │ - estimate_   │  │ - Optimizer  │
│               │  │   tokens()    │  │ - Fallback   │
│               │  │ - truncate()  │  │   Manager    │
│               │  │ - build_      │  │               │
│               │  │   context()   │  │               │
└───────────────┘  └───────────────┘  └───────────────┘
```

### Parameter Details

#### add_template() Parameters

```python
def add_template(
    self,
    name: str,                    # Template name
                               # Required, unique identifier
                               # Used for template retrieval
                               # Examples: "analysis_template", "greeting"

    version: str,                 # Template version
                               # Required, string identifier
                               # Examples: "1.0", "2.0", "latest"
                               # Used for versioning and A/B testing

    content: str,                 # Template content
                               # Required, non-empty string
                               # Supports Python format-style variables
                               # Example: "Hello {name}, welcome to {service}!"

    tenant_id: Optional[str] = None,  # Tenant identifier
                               # Used for tenant isolation
                               # Templates are scoped per tenant
                               # None = global template

    metadata: Optional[Dict[str, Any]] = None  # Template metadata
                               # Optional, additional information
                               # Common keys:
                               #   - "author": str
                               #   - "category": str
                               #   - "description": str
                               #   - "created_at": str
                               #   - Custom fields allowed
) -> None
```

#### render() Parameters

```python
def render(
    self,
    template_name: str,            # Template name to render
                               # Must match name used in add_template()
                               # Required, non-empty string

    variables: Dict[str, Any],     # Variables for substitution
                               # Required, dictionary
                               # Keys must match template variables
                               # Example: {"name": "John", "service": "AI SDK"}

    tenant_id: Optional[str] = None,  # Tenant identifier
                               # Must match tenant_id used in add_template()
                               # Ensures tenant isolation
                               # None = global templates

    version: Optional[str] = None  # Template version
                               # If None, uses latest version
                               # If specified, uses that version
                               # Example: "1.0", "2.0"
) -> str  # Returns rendered prompt string
         # Raises ValueError if template not found
```

#### build_context_with_history() Parameters

```python
def build_context_with_history(
    self,
    new_message: str,              # New message to add
                               # Required, non-empty string
                               # Added to context

    max_tokens: Optional[int] = None  # Maximum tokens
                               # Overrides manager.max_tokens if provided
                               # Range: 100 - 32000
                               # None = use manager.max_tokens
) -> str  # Returns context string
         # Includes history and new message
         # Respects token limits
```

---

## Customization

### Configuration

```python
# Custom prompt manager configuration
manager = create_prompt_manager(
    max_tokens=16000,  # Larger context window
    safety_margin=400  # Larger safety margin
)
```

### Custom Dynamic Prompting

```python
# Custom context adapter
def custom_adapter(prompt: str, context: Dict, variables: Dict) -> str:
    """Custom context adapter."""
    if context.get("language") == "spanish":
        prompt = f"[Spanish Mode]\n{prompt}"
    return prompt

builder = DynamicPromptBuilder(manager.store)
builder.add_context_adapter(custom_adapter)
```

### Custom Optimization Rules

```python
# Custom optimization rule
def clarity_rule(prompt: str) -> str:
    """Improve prompt clarity."""
    # Add clarity improvements
    if "analyze" in prompt.lower():
        prompt = prompt.replace("analyze", "thoroughly analyze")
    return prompt

optimizer = PromptOptimizer()
optimizer.add_optimization_rule(clarity_rule)
```

---

## Best Practices

1. **Template Naming**: Use descriptive, consistent template names
2. **Versioning**: Use semantic versioning for templates
3. **Variable Names**: Use clear, descriptive variable names
4. **Token Management**: Monitor and manage token usage
5. **Context Relevance**: Ensure context is relevant and useful
6. **Template Reusability**: Create reusable templates for common patterns
7. **Tenant Isolation**: Always use tenant_id for multi-tenant deployments
8. **Fallback Templates**: Provide fallback templates for continuity
9. **Optimization**: Enable prompt optimization for better results
10. **Testing**: Test templates thoroughly before deployment

---

## Additional Resources

- **Component README**: `src/core/prompt_context_management/README.md`
- **Function Documentation**: `src/core/prompt_context_management/functions.py`
- **Examples**: `examples/basic_usage/08_prompt_context_basic.py`

