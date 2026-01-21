# Prompt Context Management Functions Documentation

## Overview

The `functions.py` file provides high-level factory functions, convenience functions, and utilities for the Prompt Context Management system. These functions simplify prompt manager creation, template management, and common operations.

**Primary Functionality:**
- Factory functions for creating prompt managers
- Convenience functions for template operations
- Quick template rendering functions
- Context building helpers

## Code Explanation

### Function Categories

#### 1. Factory Functions
- **`create_prompt_manager()`**: Create prompt manager with configuration

#### 2. Convenience Functions
- **`add_template()`**: Add template convenience function
- **`get_template()`**: Get template convenience function
- **`render_template()`**: Render template convenience function
- **`build_context()`**: Build context convenience function

### Key Functions

#### `create_prompt_manager(max_tokens=4000, **kwargs) -> PromptContextManager`
Creates a prompt context manager instance.

**Parameters:**
- `max_tokens`: Maximum tokens for context window (default: 4000)
- `safety_margin`: Safety margin for token estimation (default: 200)
- `**kwargs`: Additional configuration

**Returns:** Configured `PromptContextManager` instance

#### `add_template(manager, name, content, **kwargs) -> str`
Adds a template to the manager.

**Parameters:**
- `manager`: PromptContextManager instance
- `name`: Template name
- `content`: Template content
- `version`: Optional version
- `metadata`: Optional metadata

**Returns:** Template ID

#### `render_template(manager, name, context=None, **kwargs) -> str`
Renders a template with context.

**Parameters:**
- `manager`: PromptContextManager instance
- `name`: Template name
- `context`: Optional context dictionary
- `version`: Optional template version
- `**kwargs`: Additional template variables

**Returns:** Rendered prompt string

## Usage Instructions

### Basic Usage

```python
from src.core.prompt_context_management import create_prompt_manager, add_template, render_template

# Create manager
manager = create_prompt_manager(max_tokens=4000)

# Add template
template_id = add_template(
    manager,
    name="system_prompt",
    content="You are a helpful assistant. Query: {query}"
)

# Render template
prompt = render_template(
    manager,
    "system_prompt",
    context={"query": "What is AI?"}
)
```

### Prerequisites

1. **Python 3.10+**: Required for type hints
2. **Dependencies**: Install via `pip install -r requirements.txt`

## Connection to Other Components

### Prompt Context Manager
These functions create and use `PromptContextManager` instances from `prompt_manager.py`.

**Integration Point:** Functions wrap `PromptContextManager` class

### Where Used
- **Agent Framework**: For prompt management
- **RAG System**: For query prompts
- **Examples**: All prompt examples

## Best Practices

### 1. Use Factory Functions
Always use factory functions:
```python
# Good: Use factory function
manager = create_prompt_manager(max_tokens=4000)

# Bad: Direct instantiation
from src.core.prompt_context_management.prompt_manager import PromptContextManager
manager = PromptContextManager(max_tokens=4000)
```

### 2. Version Templates
Always version templates:
```python
# Good: Versioned
add_template(manager, "prompt", "Content", version="1.0")

# Bad: No versioning
add_template(manager, "prompt", "Content")
```

## Additional Resources

### Documentation
- **[Prompt Manager Documentation](prompt_manager.md)** - Core manager class
- **[Prompt Context README](README.md)** - Complete guide

### Related Components
- **[Prompt Manager](prompt_manager.py)** - Core implementation

### Examples
- **[Basic Prompt Example](../../../../examples/basic_usage/06_prompt_context_basic.py)** - Simple usage

