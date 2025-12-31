# Motadata Python AI SDK

## Overview

The Motadata Python AI SDK is a comprehensive, modular SDK for building AI-powered applications. It provides a unified interface for LLM operations, agent frameworks, RAG systems, and database operations, all designed with modularity and swappability in mind.

## Project Structure

```
motadata-python-ai-sdk/
├── src/
│   └── core/                    # Core AI components
│       ├── litellm_gateway/
│       ├── agno_agent_framework/
│       ├── postgresql_database/
│       ├── rag/
│       ├── prompt_context_management/
│       ├── evaluation_observability/
│       ├── api_backend_services/
│       └── cache_mechanism/
├── connectivity_clients/         # Outside src
├── pool_implementation/          # Outside src
├── governance_framework/        # Outside src
└── src/tests/                   # Tests
```

## Project Components

### Core Components (in src/core/)

1. **LiteLLM Gateway** (`src/core/litellm_gateway/`)
   - Unified interface for multiple LLM providers
   - Supports OpenAI, Anthropic, Google, and more
   - Streaming, embeddings, and function calling

2. **Agno Agent Framework** (`src/core/agno_agent_framework/`)
   - Autonomous AI agents
   - Multi-agent coordination
   - Task execution and communication

3. **PostgreSQL Database** (`src/core/postgresql_database/`)
   - PostgreSQL with pgvector extension
   - Vector similarity search
   - Document and embedding storage

4. **RAG System** (`src/core/rag/`)
   - Retrieval-Augmented Generation
   - Document ingestion and retrieval
   - Context-aware response generation

5. **Prompt Context Management** (`src/core/prompt_context_management/`)
   - Prompt templates and versioning
   - Context building and management

6. **Evaluation & Observability** (`src/core/evaluation_observability/`)
   - Distributed tracing
   - Structured logging
   - Metrics collection

7. **API Backend Services** (`src/core/api_backend_services/`)
   - RESTful API endpoints
   - Backend integration

8. **Cache Mechanism** (`src/core/cache_mechanism/`)
   - Response caching
   - Embedding caching
   - Query result caching

9. **Connectivity Clients** (`connectivity_clients/`)
   - Client connection management
   - Connection pooling
   - Health monitoring

10. **Pool Implementation** (`pool_implementation/`)
    - Resource pooling
    - Connection management
    - Thread pool management

11. **Governance Framework** (`governance_framework/`)
    - Security policies
    - Code review guidelines
    - Release processes
    - Documentation standards

## Flow and Interconnections

### Component Flow

```
User Request
    ↓
API Backend Services
    ↓
    ├─→ Agent Framework → LiteLLM Gateway → LLM Providers
    ├─→ RAG System → Vector Database → PostgreSQL
    └─→ Other Components
    ↓
Response with Observability
```

### Interconnections

- **Gateway ↔ All**: Gateway provides LLM access to all components
- **Database ↔ RAG**: RAG stores/retrieves documents and embeddings
- **Agents ↔ Gateway**: Agents use gateway for LLM operations
- **Cache ↔ All**: All components can use caching
- **Observability ↔ All**: All operations are traced and logged

## Quick Start

### Installation

```bash
# Clone repository
git clone <repository-url>
cd motadata-python-ai-sdk

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```python
from src.core.litellm_gateway import LiteLLMGateway
from connectivity_clients import ClientManager
from pool_implementation import ConnectionPool

# Initialize gateway
gateway = LiteLLMGateway()

# Initialize connectivity client
client_manager = ClientManager()

# Initialize connection pool
pool = ConnectionPool(config)

# Generate text
response = gateway.generate(
    prompt="Hello, world!",
    model="gpt-4"
)
print(response.text)
```

## Documentation

- **Component Documentation**: See individual README files in each component folder
- **Workflows**: See `src/workflows.md` for detailed workflow diagrams
- **Libraries**: See `src/libraries.md` for complete library list
- **Developer Guide**: See `README_DEVELOPER.md` for development guidelines

## Modularity and Swappability

The SDK is designed with modularity in mind:

- **Agent Frameworks**: Swap Agno with LangChain or other frameworks
- **Database Backends**: Swap PostgreSQL with other databases
- **Cache Backends**: Swap Redis with memory or database caching
- **LLM Providers**: Switch between providers via LiteLLM

See component README files for swapping instructions.

## License

MIT License - see LICENSE file for details.

