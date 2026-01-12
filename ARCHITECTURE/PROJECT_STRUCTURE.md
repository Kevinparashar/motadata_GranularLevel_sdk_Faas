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
│   │   ├── machine_learning/    # Machine Learning components
│   │   │   ├── ml_framework/    # ML framework (training, inference)
│   │   │   │   ├── models/      # Model wrappers and factories
│   │   │   │   └── utils/       # ML utilities
│   │   │   ├── mlops/           # MLOps pipeline
│   │   │   ├── ml_data_management/ # Data management
│   │   │   ├── model_serving/   # Model serving
│   │   │   └── use_cases/       # Use case templates
│   │   ├── prompt_context_management/ # Prompt management
│   │   ├── evaluation_observability/ # Observability
│   │   ├── api_backend_services/ # API services (includes unified query endpoint)
│   │   ├── cache_mechanism/     # Caching (used by Gateway and RAG)
│   │   ├── feedback_loop/        # Feedback loop mechanism
│   │   ├── llmops/              # LLMOps tracking and metrics
│   │   ├── validation/          # Validation and guardrails
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
├── examples/                     # Working code examples
│   ├── README.md
│   ├── USE_CASES_STRUCTURE.md   # Use cases structure guide
│   ├── basic_usage/              # Basic component examples
│   │   ├── 01_observability_basic.py
│   │   ├── 02_pool_implementation_basic.py
│   │   ├── 03_postgresql_database_basic.py
│   │   ├── 04_connectivity_basic.py
│   │   ├── 05_litellm_gateway_basic.py
│   │   ├── 06_cache_basic.py
│   │   ├── 07_agent_basic.py
│   │   ├── 08_prompt_context_basic.py
│   │   ├── 09_rag_basic.py
│   │   └── 10_api_backend_basic.py
│   ├── integration/              # Integration examples
│   │   ├── agent_with_rag.py
│   │   └── api_with_agent.py
│   ├── end_to_end/              # End-to-end workflows
│   │   └── complete_qa_system.py
│   └── use_cases/               # Real-world use cases
│       ├── README.md            # Use cases index
│       ├── template/            # Template for new use cases
│       │   ├── README.md.template
│       │   ├── main.py.template
│       │   ├── config.py.template
│       │   ├── models.py.template
│       │   ├── requirements.txt.template
│       │   ├── .env.example.template
│       │   ├── tests/
│       │   └── docs/
│       └── [use_case_name]/     # Individual use cases
│           ├── README.md
│           ├── main.py
│           ├── config.py
│           ├── models.py
│           ├── requirements.txt
│           ├── .env.example
│           ├── tests/
│           └── docs/
│
├── README.md                     # Main documentation
├── README_DEVELOPER.md          # Developer guide
├── PROJECT_STRUCTURE.md         # This file
├── EXAMPLES_AND_TESTS_SUMMARY.md # Examples and tests summary
└── SDK_DEVELOPMENT_STORY.md     # Development story
```

## Component Locations

### Core Components (src/core/)
All AI-related components are in `src/core/`:
- `litellm_gateway/` - LLM gateway
- `agno_agent_framework/` - Agent framework
- `machine_learning/` - Machine Learning components
  - `ml_framework/` - ML framework (training, inference, model management)
  - `mlops/` - MLOps pipeline (experiments, deployment, monitoring)
  - `ml_data_management/` - Data management and feature store
  - `model_serving/` - Model serving infrastructure
  - `use_cases/` - Use case templates for ITSM-specific models
- `postgresql_database/` - Database with pgvector
- `rag/` - RAG system
- `prompt_context_management/` - Prompt management
- `evaluation_observability/` - Observability
- `api_backend_services/` - API services (includes unified query endpoint)
- `cache_mechanism/` - Caching (used by Gateway and RAG)
- `feedback_loop/` - Feedback loop mechanism
- `llmops/` - LLMOps tracking and metrics
- `validation/` - Validation and guardrails framework

### Infrastructure Components (root level)
Infrastructure components are at the root level:
- `connectivity_clients/` - Client connectivity
- `pool_implementation/` - Resource pooling
- `governance_framework/` - Governance and policies

### Tests (src/tests/)
- `unit_tests/` - Unit tests for all components
  - `test_observability.py` - Observability tests
  - `test_pool_implementation.py` - Pool tests
  - `test_postgresql_database.py` - Database tests
  - `test_litellm_gateway.py` - Gateway tests
  - `test_cache.py` - Cache tests
  - `test_agent.py` - Agent tests
  - `test_rag.py` - RAG tests
- `integration_tests/` - Integration tests
  - `test_agent_rag_integration.py` - Agent-RAG integration
  - `test_api_agent_integration.py` - API-Agent integration
  - `test_end_to_end_workflows.py` - End-to-end workflows

### Examples (examples/)
- `basic_usage/` - Working examples for each component (10 examples)
- `integration/` - Multi-component integration examples (2 examples)
- `end_to_end/` - Complete workflow examples (1 example)
- `use_cases/` - Real-world use case implementations
  - `template/` - Template for creating new use cases
  - `[use_case_name]/` - Individual use cases (snake_case naming)
    - Standard structure: README.md, main.py, config.py, models.py, tests/, docs/

## Import Paths

### Core Components
```python
from src.core.litellm_gateway import LiteLLMGateway, create_gateway
from src.core.rag import RAGSystem, create_rag_system
from src.core.agno_agent_framework import Agent, create_agent
from src.core.api_backend_services import create_unified_query_endpoint
from src.core.cache_mechanism import CacheMechanism, CacheConfig
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

