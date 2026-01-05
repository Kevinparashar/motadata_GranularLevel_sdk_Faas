# Motadata Python AI SDK

## Overview

The Motadata Python AI SDK is a comprehensive, modular SDK for building AI-powered applications. It provides a unified interface for LLM operations, agent frameworks, RAG systems, and database operations, all designed with modularity and swappability in mind.

## Features

### Core AI Capabilities
- **Multi-Provider LLM Support**: Unified interface for OpenAI, Anthropic, Google Gemini, and other providers through LiteLLM Gateway
- **Autonomous AI Agents**: Create and manage intelligent agents with session management, memory systems, tools, and plugins
- **RAG System**: Complete Retrieval-Augmented Generation with document processing, vector search, and context-aware generation
- **Vector Database Integration**: PostgreSQL with pgvector for efficient similarity search and embedding storage

### Developer Experience
- **Type-Safe APIs**: Comprehensive type hints for better IDE support and fewer runtime errors
- **Modular Architecture**: Swappable components allow easy replacement of frameworks and backends
- **Production-Ready**: Built-in connection pooling, health monitoring, caching, and observability
- **Comprehensive Documentation**: Detailed README files for each component with clear integration guides

### Infrastructure & Operations
- **Connection Pooling**: Efficient resource management for databases and API connections
- **Caching Layer**: Multi-backend caching (Redis, memory, database) for improved performance
- **Observability**: Distributed tracing, structured logging, and metrics collection with OpenTelemetry
- **Health Monitoring**: Automatic failover, retry logic, and circuit breaker patterns

### Enterprise Features
- **Security**: Built-in authentication, authorization, and secure credential management
- **Governance**: Security policies, code review guidelines, and release processes
- **API Backend**: RESTful API endpoints with rate limiting and request validation
- **Prompt Management**: Template-based prompts with versioning and A/B testing support

## Architecture Overview

The SDK follows a layered architecture with clear separation of concerns:

### Foundation Layer
- **Evaluation & Observability**: Provides tracing, logging, and metrics for all components
- **Pool Implementation**: Manages connection and resource pooling

### Infrastructure Layer
- **LiteLLM Gateway**: Unified interface for multiple LLM providers
- **PostgreSQL Database**: Vector database with pgvector for embeddings
- **Connectivity Clients**: Service connection management with health monitoring

### Core Layer
- **Agent Framework**: Autonomous agents with session, memory, tools, and plugins
- **Cache Mechanism**: Multi-backend caching for responses and embeddings
- **Prompt Context Management**: Template system with versioning and context building

### Application Layer
- **RAG System**: Document processing, retrieval, and generation
- **API Backend Services**: RESTful API endpoints exposing SDK functionality

### Design Principles
- **Interface-Based Design**: Components implement interfaces defined in `src/core/interfaces.py` for easy swapping
- **Dependency Injection**: Components receive dependencies through constructor injection
- **Async-First**: Full asyncio support for high-performance operations
- **Type Safety**: Comprehensive type hints and Pydantic models throughout

### Component Communication
- Components communicate through well-defined interfaces
- Observability is integrated into all components for comprehensive monitoring
- Cache layer is available to all components for performance optimization
- Gateway provides LLM access to Agent, RAG, and API Backend components

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

## Requirements and Prerequisites

### Python Version
- **Python 3.8.1 or higher** (Python 3.9+ recommended)
- Tested on Python 3.8, 3.9, 3.10, 3.11, and 3.12

### System Requirements
- **Operating System**: Linux, macOS, or Windows
- **Memory**: Minimum 4GB RAM (8GB+ recommended for production)
- **Disk Space**: At least 500MB for dependencies and virtual environment

### External Dependencies
- **PostgreSQL 12+** with pgvector extension (for vector database functionality)
- **Redis** (optional, for caching - can use in-memory cache as alternative)
- **LLM API Keys**: OpenAI, Anthropic, or Google API keys (depending on provider)

### Python Dependencies
The SDK requires the following key libraries (automatically installed with requirements.txt):
- **pydantic**: Data validation and settings management
- **litellm**: Unified LLM gateway
- **psycopg2-binary**: PostgreSQL database adapter
- **fastapi/uvicorn**: API framework (for API Backend component)
- **opentelemetry**: Observability and tracing
- **httpx/aiohttp**: Async HTTP clients
- **redis**: Caching backend (optional)

See `requirements.txt` for complete dependency list.

## Getting Started

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd motadata-python-ai-sdk
```

### Step 2: Set Up Virtual Environment

**Option A: Using setup.sh (Recommended)**

```bash
chmod +x setup.sh
./setup.sh
source venv/bin/activate
```

**Option B: Manual Setup**

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# LLM Provider API Keys (choose your provider)
OPENAI_API_KEY=your-openai-api-key
# OR
ANTHROPIC_API_KEY=your-anthropic-api-key
# OR
GOOGLE_API_KEY=your-google-api-key

# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=motadata_sdk
POSTGRES_USER=your-username
POSTGRES_PASSWORD=your-password

# Redis Configuration (optional, for caching)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password

# Observability Configuration (optional)
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

### Step 4: Set Up PostgreSQL with pgvector

```bash
# Install pgvector extension in PostgreSQL
# Connect to your database and run:
CREATE EXTENSION IF NOT EXISTS vector;

# Or using psql:
psql -U your-username -d motadata_sdk -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Step 5: Verify Installation

```bash
# Activate virtual environment
source venv/bin/activate

# Run Python and test imports
python3 -c "from src.core.litellm_gateway import LiteLLMGateway; print('SDK installed successfully!')"
```

### Step 6: Basic Usage Example

```python
import os
from dotenv import load_dotenv
from src.core.litellm_gateway import LiteLLMGateway

# Load environment variables
load_dotenv()

# Initialize gateway
gateway = LiteLLMGateway(
    api_key=os.getenv("OPENAI_API_KEY"),
    provider="openai"
)

# Generate text
response = gateway.generate(
    prompt="Explain quantum computing in simple terms",
    model="gpt-4"
)

print(response.text)
```

### Step 7: Run Tests (Optional)

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest src/tests/

# Run with coverage
pytest src/tests/ --cov=src --cov-report=html
```

## Examples and Tutorials

The SDK includes comprehensive working examples and tutorials:

### Basic Usage Examples
- **Component Examples**: See `examples/basic_usage/` for working examples of each component
  - `01_observability_basic.py` - Observability and tracing
  - `02_pool_implementation_basic.py` - Connection and thread pooling
  - `03_postgresql_database_basic.py` - Database operations
  - `04_connectivity_basic.py` - HTTP and WebSocket clients
  - `05_litellm_gateway_basic.py` - LLM operations
  - `06_cache_basic.py` - Caching strategies
  - `07_agent_basic.py` - Agent framework
  - `08_prompt_context_basic.py` - Prompt management
  - `09_rag_basic.py` - RAG system
  - `10_api_backend_basic.py` - REST API endpoints

### Integration Examples
- **Component Integration**: See `examples/integration/` for multi-component examples
  - `agent_with_rag.py` - Agent using RAG for context
  - `api_with_agent.py` - API exposing agent functionality

### End-to-End Examples
- **Complete Workflows**: See `examples/end_to_end/` for full system examples
  - `complete_qa_system.py` - Complete Q&A system with all components

### Use Cases
- **Real-World Implementations**: See `examples/use_cases/` for complete use case implementations
  - Each use case is self-contained with full implementation, tests, and documentation
  - **Template**: `examples/use_cases/template/` - Template for creating new use cases
  - **Structure Guide**: `examples/USE_CASES_STRUCTURE.md` - Detailed structure and naming guidelines

### Running Examples
```bash
# Run a basic example
python examples/basic_usage/01_observability_basic.py

# Run an integration example
python examples/integration/agent_with_rag.py

# Run end-to-end example
python examples/end_to_end/complete_qa_system.py
```

See `examples/README.md` for detailed instructions.

## Testing

The SDK includes comprehensive test suites:

### Unit Tests
- **Component Tests**: See `src/tests/unit_tests/` for component-specific tests
  - `test_observability.py` - Observability tests
  - `test_pool_implementation.py` - Pool tests
  - `test_postgresql_database.py` - Database tests
  - `test_litellm_gateway.py` - Gateway tests
  - `test_cache.py` - Cache tests
  - `test_agent.py` - Agent framework tests
  - `test_rag.py` - RAG system tests

### Integration Tests
- **Component Integration**: See `src/tests/integration_tests/` for integration tests
  - `test_agent_rag_integration.py` - Agent-RAG integration
  - `test_api_agent_integration.py` - API-Agent integration
  - `test_end_to_end_workflows.py` - Complete workflow tests

### Running Tests
```bash
# Run all unit tests
pytest src/tests/unit_tests/

# Run all integration tests
pytest src/tests/integration_tests/ -m integration

# Run with coverage
pytest src/tests/ --cov=src --cov-report=html

# Run specific test file
pytest src/tests/unit_tests/test_rag.py -v
```

See `src/tests/unit_tests/README.md` and `src/tests/integration_tests/README.md` for detailed testing instructions.

## Documentation

- **Component Documentation**: See individual README files in each component folder
- **Examples**: See `examples/README.md` for working code examples
- **Tests**: See `src/tests/` for test suites and validation examples
- **Workflows**: See `src/workflows.md` for detailed workflow diagrams
- **Libraries**: See `src/libraries.md` for complete library list
- **Developer Guide**: See `README_DEVELOPER.md` for development guidelines
- **Ground Truth Analysis**: See `GROUND_TRUTH_ANALYSIS.md` for SDK as reference implementation guide

## Modularity and Swappability

The SDK is designed with modularity in mind:

- **Agent Frameworks**: Swap Agno with LangChain or other frameworks
- **Database Backends**: Swap PostgreSQL with other databases
- **Cache Backends**: Swap Redis with memory or database caching
- **LLM Providers**: Switch between providers via LiteLLM

See component README files for swapping instructions.

## License

MIT License - see LICENSE file for details.

