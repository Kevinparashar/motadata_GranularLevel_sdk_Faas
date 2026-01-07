# Developer Guide

## Guidelines for Developers

This guide provides guidelines for developers on adding new components, folder structures, and relevant files.

## Adding New Components

### Component Structure

When adding a new component, follow this structure:

```
src/core/your_component/
├── __init__.py          # Component exports
├── README.md            # Component documentation
├── your_component.py    # Main implementation
├── functions.py         # Factory and convenience functions (if applicable)
└── interfaces.py        # Interfaces for swappability (if applicable)
```

**Note**: For components with complex functionality (like RAG), consider:
- Separate classes for different responsibilities (e.g., DocumentProcessor, Retriever, Generator)
- Pipeline patterns for multi-step processing (e.g., preprocessing, chunking, validation)
- Metadata handling with schema validation
- Multiple processing strategies (e.g., chunking strategies: fixed, sentence, paragraph, semantic)

### Component Template

```python
# src/core/your_component/__init__.py
"""
Your Component

Brief description of component.
"""

from .your_component import YourComponent

__all__ = ["YourComponent"]
```

### README Template

Each component must have a README.md with:
- Overview
- Purpose
- Libraries used
- Key methods
- Error handling
- Integration points
- Usage examples

## Folder Structures

### Standard Structure

```
motadata-python-ai-sdk/
├── src/
│   ├── core/
│   │   ├── litellm_gateway/
│   │   ├── your_component/
│   │   └── interfaces.py
│   └── tests/
├── connectivity_clients/    # Outside src
├── pool_implementation/     # Outside src
└── governance_framework/   # Outside src
```

### Naming Conventions

- **Folders**: Use lowercase with underscores (`your_component`)
- **Files**: Use lowercase with underscores (`your_file.py`)
- **Classes**: Use PascalCase (`YourComponent`)
- **Functions**: Use snake_case (`your_function`)

## Relevant Files

### Required Files

1. **`__init__.py`**: Package initialization with exports
2. **`README.md`**: Component documentation
3. **Implementation files**: Core functionality

### Optional Files

1. **`interfaces.py`**: Interfaces for swappability
2. **`exceptions.py`**: Custom exceptions
3. **`config.py`**: Configuration management
4. **`utils.py`**: Utility functions

## Making Components Swappable

### Interface Definition

```python
# interfaces.py
from abc import ABC, abstractmethod

class ComponentInterface(ABC):
    """Interface for swappable components."""

    @abstractmethod
    def execute(self, *args, **kwargs):
        """Execute component operation."""
        pass
```

### Implementation

```python
# your_component.py
from .interfaces import ComponentInterface

class YourComponent(ComponentInterface):
    """Your component implementation."""

    def execute(self, *args, **kwargs):
        """Implementation."""
        pass
```

### Configuration-Based Swapping

```python
# config.py
import os

COMPONENT_TYPE = os.getenv("COMPONENT_TYPE", "default")

if COMPONENT_TYPE == "alternative":
    from .alternative_component import AlternativeComponent
    Component = AlternativeComponent
else:
    from .your_component import YourComponent
    Component = YourComponent
```

## Testing Requirements

### Unit Tests

- Create unit tests for each component
- Test individual methods and functions
- Use mocks for external dependencies

### Integration Tests

- Test component interactions
- Test end-to-end workflows
- Use test containers for external services

### Test Structure

```
src/tests/
├── unit_tests/
│   └── test_your_component.py
└── integration_tests/
    └── test_your_component_integration.py
```

## Documentation Requirements

### Component README

Must include:
1. Overview and purpose
2. Libraries used
3. Key methods with examples
4. Error handling
5. Integration points
6. Usage examples
7. Enhanced features (if applicable):
   - Pipeline processing steps
   - Multiple strategies/approaches
   - Metadata handling and validation
   - Preprocessing and validation steps

### Code Documentation

- Docstrings for all public classes and methods
- Type hints for all function parameters
- Inline comments for complex logic

## Code Standards

### Formatting

- Use `black` for code formatting
- Use `isort` for import sorting
- Line length: 100 characters

### Type Hints

```python
from typing import List, Dict, Optional

def your_function(
    param1: str,
    param2: Optional[int] = None
) -> Dict[str, Any]:
    """Function with type hints."""
    pass
```

### Error Handling

The SDK uses a hybrid exception hierarchy approach:
- **Base Exception**: `src/core/exceptions.py` - Contains `SDKError` base class
- **Component Exceptions**: Each component has its own exceptions file (e.g., `src/core/agno_agent_framework/exceptions.py`, `src/core/rag/exceptions.py`)

**Example:**
```python
from src.core.exceptions import SDKError
from src.core.agno_agent_framework.exceptions import AgentExecutionError
from src.core.rag.exceptions import RetrievalError

try:
    result = await agent.execute_task(task)
except AgentExecutionError as e:
    logger.error(f"Agent {e.agent_id} failed: {e.message}")
    # Handle agent-specific error
except SDKError as e:
    logger.error(f"SDK error: {e.message}")
    # Handle any SDK error
```

**Component Exception Files:**
- Agent Framework: `src/core/agno_agent_framework/exceptions.py`
- RAG System: `src/core/rag/exceptions.py`
- Base: `src/core/exceptions.py`

## Best Practices

1. **Modularity**: Design components to be independent
2. **Swappability**: Use interfaces for swappable components
3. **Error Handling**: Comprehensive error handling
4. **Logging**: Use structured logging
5. **Testing**: Maintain high test coverage (>80%)
6. **Documentation**: Keep documentation up to date
7. **Pipeline Design**: For multi-step processing, use pipeline patterns with validation at each step
8. **Metadata Management**: Implement schema-based metadata validation and enrichment
9. **Strategy Pattern**: Support multiple strategies/approaches (e.g., chunking strategies, retrieval strategies)
10. **Preprocessing**: Include preprocessing steps for data normalization and cleaning

## Contribution Process

1. Create feature branch
2. Implement component following guidelines
3. Write tests (unit and integration)
4. Update documentation
5. Submit pull request

## Examples and Tests

### Working Examples

See `examples/` directory for working code examples:
- **Basic Usage**: `examples/basic_usage/` - Examples for each component
- **Integration**: `examples/integration/` - Multi-component examples
- **End-to-End**: `examples/end_to_end/` - Complete workflows

### Test Suites

See `src/tests/` directory for comprehensive tests:
- **Unit Tests**: `src/tests/unit_tests/` - Component-specific tests
- **Integration Tests**: `src/tests/integration_tests/` - Integration tests

### Running Examples

```bash
# Run a basic example
python examples/basic_usage/01_observability_basic.py

# Run an integration example
python examples/integration/agent_with_rag.py
```

### Running Tests

```bash
# Run all unit tests
pytest src/tests/unit_tests/

# Run integration tests
pytest src/tests/integration_tests/ -m integration
```

## Questions?

Refer to existing components for examples or contact the development team.

