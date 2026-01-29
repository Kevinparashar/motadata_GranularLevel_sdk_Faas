# Motadata Prompt Context Manager Documentation

## Overview

The `prompt_manager.py` file contains the core `PromptContextManager` class implementation, which provides comprehensive prompt template management, versioning, and context building capabilities. This manager enables dynamic prompt construction, template versioning, and context-aware prompt generation for AI applications.

**Primary Functionality:**
- Prompt template management (CRUD operations)
- Template versioning and history
- Context building and management
- Dynamic prompt rendering
- Template validation
- Fallback template handling
- Automatic prompt optimization
- Context window management

## Code Explanation

### Class Structure

#### `PromptContextManager` (Class)
Main prompt context manager class.

**Core Attributes:**
- `templates`: Dictionary of prompt templates
- `versions`: Template version history
- `context_builder`: Context building utilities
- `max_tokens`: Maximum tokens for context window
- `safety_margin`: Safety margin for token estimation

### Key Methods

#### `add_template(name, content, version=None, metadata=None) -> str`
Adds a new prompt template.

**Parameters:**
- `name`: Template name
- `content`: Template content
- `version`: Optional version string
- `metadata`: Optional metadata dictionary

**Returns:** Template ID

#### `get_template(name, version=None) -> Optional[Dict[str, Any]]`
Retrieves a template.

**Parameters:**
- `name`: Template name
- `version`: Optional version (latest if not provided)

**Returns:** Template dictionary or None

#### `render_template(name, context=None, version=None, **kwargs) -> str`
Renders a template with context.

**Parameters:**
- `name`: Template name
- `context`: Optional context dictionary
- `version`: Optional template version
- `**kwargs`: Additional template variables

**Returns:** Rendered prompt string

#### `build_context(query, history=None, metadata=None) -> Dict[str, Any]`
Builds context for prompt rendering.

**Parameters:**
- `query`: User query
- `history`: Optional conversation history
- `metadata`: Optional metadata

**Returns:** Context dictionary

#### `get_versions(name) -> List[Dict[str, Any]]`
Gets version history for a template.

**Parameters:**
- `name`: Template name

**Returns:** List of version dictionaries

## Usage Instructions

### Basic Manager Creation

```python
from src.core.prompt_context_management import PromptContextManager

manager = PromptContextManager(
    max_tokens=4000,
    safety_margin=200
)
```

### Template Management

```python
# Add template
template_id = manager.add_template(
    name="system_prompt",
    content="You are a helpful AI assistant. User query: {query}",
    metadata={"category": "system"}
)

# Get template
template = manager.get_template("system_prompt")

# Render template
prompt = manager.render_template(
    "system_prompt",
    context={"query": "What is AI?"}
)
```

### Versioning

```python
# Add versioned template
v1 = manager.add_template("prompt", "Version 1", version="1.0")
v2 = manager.add_template("prompt", "Version 2", version="2.0")

# Get specific version
template = manager.get_template("prompt", version="1.0")

# Get version history
versions = manager.get_versions("prompt")
```

### Context Building

```python
# Build context
context = manager.build_context(
    query="What is AI?",
    history=[{"role": "user", "content": "Hello"}],
    metadata={"user_id": "user_123"}
)

# Render with context
prompt = manager.render_template("system_prompt", context=context)
```

### Prerequisites

1. **Python 3.10+**: Required for type hints
2. **Dependencies**: Install via `pip install -r requirements.txt`
   - `pydantic`: For data validation

## Connection to Other Components

### Agent Framework
Agents use prompt manager for:
- Dynamic prompt construction
- Context-aware prompts
- Template management

**Integration Point:** `agent.prompt_manager` attribute

### RAG System
RAG system uses prompt manager for:
- Query prompt construction
- Context building
- Template-based responses

**Integration Point:** RAG generator uses prompt manager

### Where Used
- **Agent Framework**: For agent prompts
- **RAG System**: For query prompts
- **Examples**: All prompt examples

## Best Practices

### 1. Use Versioning
Always version templates:
```python
# Good: Versioned templates
manager.add_template("prompt", "Content", version="1.0")

# Bad: No versioning (hard to track changes)
manager.add_template("prompt", "Content")
```

### 2. Provide Metadata
Always provide meaningful metadata:
```python
# Good: Rich metadata
manager.add_template(
    "prompt",
    "Content",
    metadata={"category": "system", "author": "John"}
)

# Bad: No metadata
manager.add_template("prompt", "Content")
```

### 3. Manage Context Window
Monitor context window usage:
```python
# Good: Appropriate max_tokens
manager = PromptContextManager(max_tokens=4000, safety_margin=200)

# Bad: Too large or too small
manager = PromptContextManager(max_tokens=100000)  # Too large
manager = PromptContextManager(max_tokens=100)    # Too small
```

## Additional Resources

### Documentation
- **[Prompt Context README](README.md)** - Complete guide
- **[Prompt Functions Documentation](functions.md)** - Factory functions

### Related Components
- **[Prompt Enhancements](prompt_enhancements.py)** - Advanced features

### Examples
- **[Basic Prompt Example](../../../../examples/basic_usage/06_prompt_context_basic.py)** - Simple usage

