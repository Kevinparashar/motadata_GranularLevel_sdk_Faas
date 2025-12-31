# Project Structure

## Complete Directory Structure

```
motadata-python-ai-sdk/
│
├── src/                          # Source code
│   ├── core/                     # Core AI components
│   │   ├── litellm_gateway/     # LiteLLM Gateway
│   │   ├── agno_agent_framework/ # Agent framework
│   │   │   └── agents/          # Agent implementations
│   │   ├── postgresql_database/ # PostgreSQL with pgvector
│   │   │   └── vector_database/ # Vector operations
│   │   ├── rag/                 # RAG system
│   │   ├── prompt_context_management/ # Prompt management
│   │   ├── evaluation_observability/ # Observability
│   │   ├── api_backend_services/ # API services
│   │   ├── cache_mechanism/     # Caching
│   │   └── interfaces.py        # Swappable interfaces
│   │
│   ├── tests/                    # Tests
│   │   ├── unit_tests/          # Unit tests
│   │   └── integration_tests/   # Integration tests
│   │
│   ├── workflows.md             # Workflow diagrams
│   └── libraries.md              # Library list
│
├── connectivity_clients/         # Outside src (root level)
│   ├── __init__.py
│   └── README.md
│
├── pool_implementation/          # Outside src (root level)
│   ├── __init__.py
│   └── README.md
│
├── governance_framework/         # Outside src (root level)
│   ├── __init__.py
│   └── README.md
│
├── README.md                     # Main documentation
├── README_DEVELOPER.md          # Developer guide
└── PROJECT_STRUCTURE.md         # This file
```

## Component Locations

### Core Components (src/core/)
All AI-related components are in `src/core/`:
- `litellm_gateway/` - LLM gateway
- `agno_agent_framework/` - Agent framework
- `postgresql_database/` - Database with pgvector
- `rag/` - RAG system
- `prompt_context_management/` - Prompt management
- `evaluation_observability/` - Observability
- `api_backend_services/` - API services
- `cache_mechanism/` - Caching

### Infrastructure Components (root level)
Infrastructure components are at the root level:
- `connectivity_clients/` - Client connectivity
- `pool_implementation/` - Resource pooling
- `governance_framework/` - Governance and policies

### Tests (src/tests/)
- `unit_tests/` - Unit tests
- `integration_tests/` - Integration tests

## Import Paths

### Core Components
```python
from src.core.litellm_gateway import LiteLLMGateway
from src.core.rag import RAGSystem
from src.core.agno_agent_framework import Agent
```

### Infrastructure Components
```python
from connectivity_clients import ClientManager
from pool_implementation import ConnectionPool
from governance_framework import SecurityPolicy
```

## Rationale

- **Core components in src/core/**: All AI/LLM related functionality
- **Infrastructure outside src/**: Shared infrastructure used by all components
- **Modular design**: Easy to swap components via interfaces
- **Clear separation**: Infrastructure vs. business logic

