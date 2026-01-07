# Exception Architecture Documentation

## Overview

The SDK uses a **Hybrid Exception Approach (Option 3)** where exceptions are organized by component while maintaining a unified base class. This provides both modularity and consistency.

## Exception File Locations

### 1. Base Exception (`src/core/exceptions.py`)

**Location**: `src/core/exceptions.py`

**Purpose**:
- Contains the **base `SDKError` class** that all SDK exceptions inherit from
- Provides platform-wide error catching capability
- Enables uniform error handling across the entire SDK

**Why Here?**
- **Central Location**: Placed at the `src/core/` level because it's the foundation for all SDK components
- **Shared Dependency**: All components need access to `SDKError`, so it's at the common root
- **Import Path**: Easy to import from anywhere: `from src.core.exceptions import SDKError`

**Contents:**
```python
class SDKError(Exception):
    """Base exception class for all SDK errors."""
    # Provides message and original_error attributes
```

---

### 2. Agent Framework Exceptions (`src/core/agno_agent_framework/exceptions.py`)

**Location**: `src/core/agno_agent_framework/exceptions.py`

**Purpose**:
- Contains all exceptions related to the Agent Framework
- Includes: Agent, Tool, Memory, and Orchestration exceptions

**Why Here?**
- **Component Co-location**: Exceptions are placed **within the component** they belong to
- **Logical Grouping**: All agent-related errors (agent execution, tools, memory, orchestration) are grouped together
- **Encapsulation**: The Agent Framework is self-contained with its own exception hierarchy
- **Import Path**: `from src.core.agno_agent_framework.exceptions import AgentExecutionError`

**Contents:**
- `AgentError` → `AgentExecutionError`, `AgentConfigurationError`, `AgentStateError`
- `ToolError` → `ToolInvocationError`, `ToolNotFoundError`, `ToolNotImplementedError`, `ToolValidationError`
- `MemoryError` → `MemoryReadError`, `MemoryWriteError`, `MemoryPersistenceError`
- `OrchestrationError` → `WorkflowNotFoundError`, `AgentNotFoundError`

**Why Not Separate Files?**
- **Cohesion**: Agent, Tool, Memory, and Orchestration are tightly coupled within the Agent Framework
- **Simplicity**: One file is easier to maintain than multiple files for related exceptions
- **Usage Pattern**: These exceptions are often used together in agent workflows

---

### 3. RAG System Exceptions (`src/core/rag/exceptions.py`)

**Location**: `src/core/rag/exceptions.py`

**Purpose**:
- Contains all exceptions related to the RAG (Retrieval-Augmented Generation) system
- Includes: Retrieval, Generation, Embedding, Document Processing, Chunking, and Validation exceptions

**Why Here?**
- **Component Co-location**: Exceptions are placed **within the RAG component**
- **Logical Grouping**: All RAG-related errors are grouped together
- **Encapsulation**: The RAG system is self-contained with its own exception hierarchy
- **Import Path**: `from src.core.rag.exceptions import RetrievalError`

**Contents:**
- `RAGError` → `RetrievalError`, `GenerationError`, `EmbeddingError`, `DocumentProcessingError`, `ChunkingError`, `ValidationError`

**Why Separate from Agent Framework?**
- **Independence**: RAG is a standalone component that can be used independently
- **Different Domain**: RAG errors are specific to document processing, retrieval, and generation
- **Clear Separation**: Keeps RAG concerns separate from agent concerns

---

## Architecture Rationale

### Why Hybrid Approach (Option 3)?

The hybrid approach provides the **best of both worlds**:

1. **Modularity**: Each component has its own exceptions, making it self-contained
2. **Consistency**: All exceptions inherit from `SDKError`, enabling platform-wide catching
3. **Maintainability**: Exceptions are co-located with the code that uses them
4. **Scalability**: New components can add their own exception files without cluttering a central file

### Comparison with Other Approaches

**Option 1: Single Central File** (`src/core/exceptions.py` with all exceptions)
- ❌ **Problem**: One massive file with hundreds of exceptions
- ❌ **Problem**: Hard to maintain and navigate
- ❌ **Problem**: All components depend on one file

**Option 2: No Custom Exceptions** (Use standard Python exceptions)
- ❌ **Problem**: No structured error handling
- ❌ **Problem**: Can't catch SDK-specific errors uniformly
- ❌ **Problem**: No context-rich error information

**Option 3: Hybrid Approach** (Base + Component-specific) ✅
- ✅ **Solution**: Base class for consistency, component files for modularity
- ✅ **Solution**: Easy to find exceptions (they're with their components)
- ✅ **Solution**: Components are self-contained and swappable
- ✅ **Solution**: Platform-wide catching still possible via `SDKError`

---

## Import Patterns

### Catching All SDK Errors
```python
from src.core.exceptions import SDKError

try:
    # Any SDK operation
    result = await agent.execute_task(task)
except SDKError as e:
    # Catches ALL SDK errors (Agent, RAG, etc.)
    logger.error(f"SDK error: {e.message}")
```

### Catching Component-Specific Errors
```python
from src.core.agno_agent_framework.exceptions import AgentExecutionError
from src.core.rag.exceptions import RetrievalError

try:
    result = await agent.execute_task(task)
except AgentExecutionError as e:
    # Only catches agent execution errors
    logger.error(f"Agent {e.agent_id} failed: {e.message}")
except RetrievalError as e:
    # Only catches RAG retrieval errors
    logger.error(f"Retrieval failed: {e.message}")
```

### Catching Component Base Errors
```python
from src.core.agno_agent_framework.exceptions import AgentError
from src.core.rag.exceptions import RAGError

try:
    result = await agent.execute_task(task)
except AgentError as e:
    # Catches all agent-related errors (Agent, Tool, Memory, Orchestration)
    logger.error(f"Agent framework error: {e.message}")
except RAGError as e:
    # Catches all RAG-related errors
    logger.error(f"RAG error: {e.message}")
```

---

## Component Exception Mapping

| Component | Exception File | Base Exception | Specific Exceptions |
|-----------|---------------|----------------|---------------------|
| **Core SDK** | `src/core/exceptions.py` | `SDKError` | Base class only |
| **Agent Framework** | `src/core/agno_agent_framework/exceptions.py` | `AgentError` | AgentExecutionError, AgentConfigurationError, AgentStateError |
| **Tools** | `src/core/agno_agent_framework/exceptions.py` | `ToolError` | ToolInvocationError, ToolNotFoundError, ToolNotImplementedError, ToolValidationError |
| **Memory** | `src/core/agno_agent_framework/exceptions.py` | `MemoryError` | MemoryReadError, MemoryWriteError, MemoryPersistenceError |
| **Orchestration** | `src/core/agno_agent_framework/exceptions.py` | `OrchestrationError` | WorkflowNotFoundError, AgentNotFoundError |
| **RAG System** | `src/core/rag/exceptions.py` | `RAGError` | RetrievalError, GenerationError, EmbeddingError, DocumentProcessingError, ChunkingError, ValidationError |

---

## Design Principles

1. **Co-location**: Exceptions live with the components that raise them
2. **Inheritance**: All exceptions inherit from `SDKError` for consistency
3. **Rich Context**: Exceptions include structured attributes (agent_id, tool_name, etc.) for debugging
4. **Modularity**: Each component is self-contained with its own exception hierarchy
5. **Consistency**: All exceptions follow the same pattern (message, original_error, component-specific attributes)

---

## Future Components

When adding new components, follow this pattern:

1. **Create exception file**: `src/core/<component_name>/exceptions.py`
2. **Define base exception**: Inherit from `SDKError`
3. **Define specific exceptions**: Inherit from component base exception
4. **Import in component code**: Use component-specific exceptions
5. **Document**: Update this file and component README

**Example for a new "Cache" component:**
```python
# src/core/cache_mechanism/exceptions.py
from ..exceptions import SDKError

class CacheError(SDKError):
    """Base exception for cache-related errors."""
    pass

class CacheReadError(CacheError):
    """Raised when cache read fails."""
    pass

class CacheWriteError(CacheError):
    """Raised when cache write fails."""
    pass
```

---

## Summary

- **Base Exception**: `src/core/exceptions.py` - Foundation for all SDK errors
- **Agent Framework Exceptions**: `src/core/agno_agent_framework/exceptions.py` - All agent, tool, memory, orchestration errors
- **RAG Exceptions**: `src/core/rag/exceptions.py` - All RAG system errors
- **Rationale**: Hybrid approach provides modularity, consistency, and maintainability
- **Pattern**: Co-locate exceptions with components, inherit from `SDKError`, include rich context

