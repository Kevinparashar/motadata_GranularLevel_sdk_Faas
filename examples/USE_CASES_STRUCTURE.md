# Motadata Use Cases Folder Structure and Management

## Overview

This document defines the folder structure, naming conventions, and management guidelines for use case examples in the SDK.

## 📁 Folder Structure

```
examples/
├── README.md                          # Main examples documentation
├── USE_CASES_STRUCTURE.md            # This file
│
├── basic_usage/                      # Basic component examples
│   ├── 01_observability_basic.py
│   ├── 02_pool_implementation_basic.py
│   ├── 03_postgresql_database_basic.py
│   ├── 04_connectivity_basic.py
│   ├── 05_litellm_gateway_basic.py
│   ├── 06_cache_basic.py
│   ├── 07_agent_basic.py
│   ├── 08_prompt_context_basic.py
│   ├── 09_rag_basic.py
│   └── 10_api_backend_basic.py
│
├── integration/                      # Multi-component integration examples
│   ├── agent_with_rag.py
│   └── api_with_agent.py
│
├── end_to_end/                      # Complete workflow examples
│   └── complete_qa_system.py
│
└── use_cases/                       # Real-world use case implementations
    ├── README.md                    # Use cases index
    │
    ├── customer_support_chatbot/    # Use case: Customer Support Chatbot
    │   ├── README.md               # Use case documentation
    │   ├── main.py                 # Main implementation
    │   ├── config.py               # Configuration
    │   ├── models.py               # Data models
    │   ├── api.py                  # API endpoints (if applicable)
    │   ├── requirements.txt        # Use case specific dependencies
    │   ├── .env.example            # Environment variables template
    │   ├── tests/                  # Use case tests
    │   │   ├── __init__.py
    │   │   ├── test_main.py        # Unit tests
    │   │   ├── test_integration.py # Integration tests
    │   │   └── fixtures.py         # Test fixtures
    │   └── docs/                   # Additional documentation
    │       └── architecture.md     # Architecture diagram/docs
    │
    ├── document_qa_system/          # Use case: Document Q&A System
    │   ├── README.md
    │   ├── main.py
    │   ├── config.py
    │   ├── models.py
    │   ├── requirements.txt
    │   ├── .env.example
    │   ├── tests/
    │   └── docs/
    │
    ├── intelligent_agent_workflow/ # Use case: Intelligent Agent Workflow
    │   ├── README.md
    │   ├── main.py
    │   ├── config.py
    │   ├── models.py
    │   ├── requirements.txt
    │   ├── .env.example
    │   ├── tests/
    │   └── docs/
    │
    └── template/                    # Template for new use cases
        ├── README.md.template
        ├── main.py.template
        ├── config.py.template
        ├── models.py.template
        ├── requirements.txt.template
        ├── .env.example.template
        ├── tests/
        │   ├── __init__.py.template
        │   ├── test_main.py.template
        │   └── test_integration.py.template
        └── docs/
            └── architecture.md.template
```

## 📝 Naming Conventions

### Use Case Folder Names

**Format**: `snake_case` (lowercase with underscores)

**Rules**:
- Use descriptive, clear names
- Keep it concise (2-4 words)
- Use underscores, not hyphens
- Avoid abbreviations unless widely known
- Match the use case purpose

**Examples**:
- ✅ `customer_support_chatbot`
- ✅ `document_qa_system`
- ✅ `intelligent_agent_workflow`
- ✅ `multi_agent_coordination`
- ✅ `rag_based_knowledge_base`
- ❌ `customer-support-chatbot` (hyphens)
- ❌ `CSBot` (abbreviation)
- ❌ `chatbot` (too generic)

### File Names

**Standard Files** (required):
- `README.md` - Use case documentation
- `main.py` - Main implementation
- `config.py` - Configuration management
- `models.py` - Data models
- `requirements.txt` - Dependencies
- `.env.example` - Environment variables template

**Optional Files**:
- `api.py` - API endpoints (if REST API needed)
- `utils.py` - Utility functions
- `constants.py` - Constants
- `exceptions.py` - Custom exceptions

**Test Files**:
- `tests/test_main.py` - Unit tests
- `tests/test_integration.py` - Integration tests
- `tests/fixtures.py` - Test fixtures
- `tests/conftest.py` - Pytest configuration

## 🆕 Creating a New Use Case

### Step 1: Create Folder Structure

```bash
# Navigate to examples directory
cd examples/use_cases

# Create use case folder (use snake_case)
mkdir customer_support_chatbot
cd customer_support_chatbot

# Create standard structure
mkdir tests docs
touch README.md main.py config.py models.py requirements.txt .env.example
touch tests/__init__.py tests/test_main.py tests/test_integration.py
touch docs/architecture.md
```

### Step 2: Use Template

Copy from template folder:

```bash
# Copy template files
cp ../template/README.md.template README.md
cp ../template/main.py.template main.py
cp ../template/config.py.template config.py
# ... etc
```

### Step 3: Update Files

1. **README.md**: Update with use case description
2. **main.py**: Implement use case logic
3. **config.py**: Add configuration
4. **models.py**: Define data models
5. **requirements.txt**: Add dependencies
6. **.env.example**: Add environment variables

### Step 4: Register Use Case

Add to `examples/use_cases/README.md`:

```markdown
## customer_support_chatbot

**Description**: Customer support chatbot using RAG and Agent Framework

**Components Used**: RAG System, Agent Framework, LiteLLM Gateway, API Backend

**See**: [README.md](customer_support_chatbot/README.md)
```

## 📋 Use Case Template Structure

### README.md Template

```markdown
# [Use Case Name]

## Overview
Brief description of the use case.

## Components Used
- Component 1: Purpose
- Component 2: Purpose

## Prerequisites
- Requirement 1
- Requirement 2

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Configure environment: Copy `.env.example` to `.env`
3. Run: `python main.py`

## Usage
```python
# Example usage
```

## Testing
```bash
pytest tests/
```

## Architecture
See [docs/architecture.md](docs/architecture.md)
```

### main.py Template

```python
"""
[Use Case Name]

Description of what this use case does.
"""

import os
from dotenv import load_dotenv
from src.core.litellm_gateway import LiteLLMGateway
# ... other imports

# Load configuration
load_dotenv()

# Initialize SDK components
# ... initialization code

class UseCaseClass:
    """Main use case implementation."""
    
    def __init__(self, ...):
        """Initialize use case."""
        pass
    
    async def execute(self, ...):
        """Execute use case logic."""
        pass

if __name__ == "__main__":
    # Run use case
    pass
```

## 🔄 Management Guidelines

### Adding a New Use Case

1. **Create Folder**: Use snake_case naming
2. **Copy Template**: Use template folder structure
3. **Implement**: Follow SDK patterns
4. **Test**: Add comprehensive tests
5. **Document**: Complete README and docs
6. **Register**: Add to use_cases/README.md
7. **Review**: Code review before merging

### Updating an Existing Use Case

1. **Update Code**: Make changes to implementation
2. **Update Tests**: Ensure tests cover changes
3. **Update Docs**: Update README if needed
4. **Test**: Run all tests
5. **Review**: Code review

### Removing a Use Case

1. **Deprecate**: Mark as deprecated in README
2. **Archive**: Move to archive folder (if needed)
3. **Remove**: Delete folder after deprecation period
4. **Update Index**: Remove from use_cases/README.md

### Version Control

- Each use case is self-contained
- Use git submodules if use case becomes large
- Tag releases for stable use cases
- Document breaking changes

## 📊 Use Case Index

The `examples/use_cases/README.md` serves as the index:

```markdown
# Use Cases Index

## Active Use Cases

### customer_support_chatbot
- **Status**: ✅ Active
- **Components**: RAG, Agent, Gateway
- **Last Updated**: 2024-01-15
- [Documentation](customer_support_chatbot/README.md)

### document_qa_system
- **Status**: ✅ Active
- **Components**: RAG, Gateway
- **Last Updated**: 2024-01-10
- [Documentation](document_qa_system/README.md)

## Template

See [template/](template/) for creating new use cases.
```

## ✅ Quality Checklist

Before adding a use case:

- [ ] Folder name follows snake_case convention
- [ ] All standard files present (README, main.py, etc.)
- [ ] README.md is complete and clear
- [ ] Code follows SDK patterns
- [ ] Tests are comprehensive (>80% coverage)
- [ ] .env.example includes all required variables
- [ ] requirements.txt is up to date
- [ ] Use case is registered in index
- [ ] Code review completed

## 🎯 Best Practices

1. **Self-Contained**: Each use case should be independent
2. **Well-Documented**: Clear README and code comments
3. **Tested**: Comprehensive test coverage
4. **Maintainable**: Follow SDK patterns and conventions
5. **Reusable**: Can be used as reference for similar use cases

## 📚 Related Documentation

- [Building New Use Cases Guide](../BUILDING_NEW_USECASE_GUIDE.md)
- [Examples README](README.md)
- [Developer Guide](../../PYTHON_SDK_DEVELOPMENT_ENVIRONMENT_SETUP_GUIDE.md)

