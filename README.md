# Motadata Python AI SDK

## 🚀 Quick Start (5 Minutes)

**Get started in 5 minutes!**

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your API key
export OPENAI_API_KEY='your-api-key-here'
# Or create .env file: echo "OPENAI_API_KEY=your-key" > .env

# 3. Run Hello World
python examples/hello_world.py
```

**Expected Output:**
```
🚀 Motadata AI SDK - Hello World Example
✅ API key found
📡 Creating gateway connection...
✅ Gateway created successfully
🤖 Sending request to AI...
============================================================
AI Response:
============================================================
Hello! I'm an AI assistant ready to help you.
============================================================
✅ Success! SDK is working correctly.
📊 Model used: gpt-3.5-turbo
💰 Tokens used: 15
```

**Next Steps:**
- Try [Basic Usage Examples](#examples-and-tutorials)
- Explore [Component Guides](#project-components)
- Check [When to Use What](#when-to-use-what) for component selection

---

## Overview

The Motadata Python AI SDK is a comprehensive, modular SDK for building AI-powered applications. It provides a unified interface for LLM operations, agent frameworks, RAG systems, machine learning capabilities, and database operations, all designed with modularity and swappability in mind.

## Features

### Core AI Capabilities
- **Prompt-Based Creation**: Create agents and tools from natural language prompts - describe what you want in plain English and the system generates fully configured agents and tools automatically
- **Multi-Provider LLM Support**: Unified interface for OpenAI, Anthropic, Google Gemini, and other providers through LiteLLM Gateway with advanced rate limiting, request queuing, batching, and deduplication
- **Autonomous AI Agents**: Create and manage intelligent agents with session management, bounded memory systems, tools, plugins, circuit breakers, and health checks
- **RAG System**: Complete Retrieval-Augmented Generation with document processing, vector search, re-ranking, versioning, relevance scoring, incremental updates, and real-time synchronization
- **Machine Learning Framework**: Comprehensive ML capabilities for training, inference, and model management with MLOps pipeline, data management, and model serving
- **Vector Database Integration**: PostgreSQL with pgvector for efficient similarity search and embedding storage

### Developer Experience
- **Type-Safe APIs**: Comprehensive type hints for better IDE support and fewer runtime errors
- **Modular Architecture**: Swappable components allow easy replacement of frameworks and backends
- **Production-Ready**: Built-in connection pooling, health monitoring, caching, and observability
- **Comprehensive Documentation**: Detailed README files for each component with clear integration guides

### Infrastructure & Operations
- **Connection Pooling**: Efficient resource management for databases and API connections
- **Advanced Caching**: Multi-backend caching (Redis, memory, database) with warming strategies, memory monitoring, automatic sharding, validation, and recovery mechanisms
- **Observability**: Distributed tracing, structured logging, metrics collection with OpenTelemetry, and comprehensive LLMOps capabilities
- **Health Monitoring**: Automatic failover, retry logic, circuit breaker patterns, and built-in health checks for all components
- **LLMOps**: Comprehensive logging, cost tracking, token usage monitoring, and performance metrics for LLM operations

### Enterprise Features
- **Security**: Built-in authentication, authorization, secure credential management, and validation/guardrails framework
- **Governance**: Security policies, code review guidelines, and release processes
- **API Backend**: RESTful API endpoints with rate limiting and request validation
- **Advanced Prompt Management**: Template-based prompts with versioning, A/B testing, dynamic prompting, automatic optimization, and fallback templates
- **Feedback Loop**: Continuous learning mechanism with user feedback collection and processing
- **Multi-Tenancy**: Full tenant isolation and context management across all components

## When to Use What

**Quick Decision Guide:**

- **Need AI text generation?** → Use [LiteLLM Gateway](src/core/litellm_gateway/README.md)
- **Building a chatbot or assistant?** → Use [Agent Framework](src/core/agno_agent_framework/README.md)
- **Want to create agents/tools from natural language?** → Use [Prompt-Based Generator](src/core/prompt_based_generator/README.md)
- **Answering questions from documents?** → Use [RAG System](src/core/rag/README.md)
- **Want to reduce API costs?** → Use [Cache Mechanism](src/core/cache_mechanism/README.md)
- **Need monitoring and debugging?** → Use [Observability](src/core/evaluation_observability/README.md)
- **Managing prompts and templates?** → Use [Prompt Context Management](src/core/prompt_context_management/README.md)
- **Building REST APIs?** → Use [API Backend Services](src/core/api_backend_services/README.md)

**For detailed guidance on each component, see their individual README files which include:**
- ✅ When to use this component
- ❌ When NOT to use this component
- Simple code examples
- Cost and performance notes

---

## Architecture Overview

For a simple, beginner-friendly explanation of how data flows through the SDK, see [Architecture Overview](docs/architecture_overview.md).

The SDK follows a layered architecture with clear separation of concerns:

### Foundation Layer
- **Evaluation & Observability**: Provides tracing, logging, and metrics for all components

### Infrastructure Layer
- **LiteLLM Gateway**: Unified interface for multiple LLM providers
- **PostgreSQL Database**: Vector database with pgvector for embeddings

### Core Layer
- **Agent Framework**: Autonomous agents with session, memory, tools, and plugins
- **Prompt-Based Generator**: Create agents and tools from natural language prompts
- **Machine Learning**: ML framework, MLOps pipeline, data management, and model serving
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
- **Structured Error Handling**: Custom exception hierarchy for granular error handling and debugging

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
│       ├── machine_learning/    # ML components
│       │   ├── ml_framework/
│       │   ├── mlops/
│       │   ├── ml_data_management/
│       │   ├── model_serving/
│       │   └── use_cases/
│       ├── postgresql_database/
│       ├── rag/
│       ├── prompt_context_management/
│       ├── prompt_based_generator/  # Prompt-based agent/tool creation
│       ├── evaluation_observability/
│       ├── api_backend_services/
│       └── cache_mechanism/
└── src/tests/                   # Tests
```

## Project Components

### Core Components (in src/core/)

1. **LiteLLM Gateway** (`src/core/litellm_gateway/`)
   - Unified interface for multiple LLM providers
   - Supports OpenAI, Anthropic, Google, and more
   - Streaming, embeddings, and function calling
   - **Advanced Rate Limiting** with request queuing and token bucket algorithm
   - **Request Batching** to improve efficiency for similar requests
   - **Request Deduplication** to avoid processing identical requests multiple times
   - **Circuit Breaker** mechanism for provider failures
   - **Health Monitoring** for providers to ensure service reliability
   - **LLMOps Integration** for comprehensive logging, cost tracking, and metrics
   - **Validation/Guardrails** framework for output quality and compliance
   - **Feedback Loop** mechanism for continuous learning and improvement

2. **Agno Agent Framework** (`src/core/agno_agent_framework/`)
   - Autonomous AI agents
   - Multi-agent coordination and orchestration
   - Workflow pipelines with dependencies
   - Coordination patterns (leader-follower, peer-to-peer)
   - Task delegation and chaining
   - Task execution and communication
   - Optional persistent memory with bounded episodic/semantic memory and automatic cleanup
   - Retry-aware task execution
   - **Circuit Breaker Pattern** for handling external service failures gracefully
   - **Built-in Health Checks** for monitoring agent performance and availability
   - **Integrated Prompt Context Management** with system prompts, role templates, and context assembly

3. **Prompt-Based Generator** (`src/core/prompt_based_generator/`)
   - Create agents from natural language prompts
   - Create tools from natural language prompts
   - Automatic configuration extraction and generation
   - Code generation and validation for tools
   - Access control framework for resources
   - Feedback collection and processing
   - Caching of interpretations and configurations
   - Memory management for generated resources

4. **PostgreSQL Database** (`src/core/postgresql_database/`)
   - PostgreSQL with pgvector extension
   - Vector similarity search
   - Document and embedding storage

5. **RAG System** (`src/core/rag/`)
   - Retrieval-Augmented Generation
   - Enhanced chunking pipeline with preprocessing, multiple strategies (fixed, sentence, paragraph, semantic)
   - Advanced metadata handling: automatic extraction, validation, enrichment, and schema support
   - Multiple file format support (text, HTML, JSON) with extensible architecture
   - Document ingestion and retrieval with batch processing
   - Context-aware response generation with query optimization
   - **Advanced Re-ranking** algorithms for improved document relevance
   - **Document Versioning** for better management and retrieval
   - **Explicit Relevance Scoring** for retrieved documents
   - **Incremental Updates** to avoid full re-embedding when documents are updated
   - **Document Validation** processes to ensure compliance with required formats
   - **Real-time Document Synchronization** for up-to-date information

5. **Machine Learning Framework** (`src/core/machine_learning/`)
   - **ML Framework** (`ml_framework/`): Core ML system for training, inference, and model management
     - Unified interface for ML operations (MLSystem)
     - Model lifecycle management (create, update, delete, archive, version)
     - Training orchestration with hyperparameter management and validation
     - Inference engine with preprocessing, postprocessing, and caching
     - Data preprocessing and feature engineering
     - Model versioning and registry
     - Memory management with configurable limits
     - Multi-tenant support with full tenant isolation
   - **MLOps Pipeline** (`mlops/`): End-to-end MLOps capabilities
     - Experiment tracking with MLflow integration
     - Model versioning and lineage tracking
     - Model deployment to different environments (dev, staging, prod)
     - Model monitoring with performance metrics and alerting
     - Drift detection (data drift, model drift, concept drift)
   - **Data Management** (`ml_data_management/`): Data lifecycle and feature store
     - Data ingestion, validation, transformation, and archival
     - Feature store for centralized feature storage and retrieval
     - Data quality checks and schema validation
     - ETL pipelines for data processing
   - **Model Serving** (`model_serving/`): Model serving infrastructure
     - REST API server (FastAPI) for model predictions
     - Batch prediction service for large-scale processing
     - Real-time prediction service with caching
   - **Use Cases** (`use_cases/`): Template structure for ITSM-specific ML models
     - Base class interface (BaseMLModel) for all use case models
     - Template for creating new ML models
     - Framework for ticket classification, priority prediction, SLA prediction, etc.

6. **Prompt Context Management** (`src/core/prompt_context_management/`)
   - Prompt templates and versioning
   - Context building and management
   - **Dynamic Prompting** capabilities that adjust based on context
   - **Automatic Prompt Optimization** techniques to maximize effectiveness
   - **Fallback Templates** to ensure continuity if a template is not found

7. **Evaluation & Observability** (`src/core/evaluation_observability/`)
   - Distributed tracing
   - Structured logging
   - Metrics collection

8. **API Backend Services** (`src/core/api_backend_services/`)
   - RESTful API endpoints
   - Backend integration

9. **Cache Mechanism** (`src/core/cache_mechanism/`)
   - Response, embedding, and query result caching
   - In-memory (LRU + TTL) and optional Redis backend
   - Pattern-based invalidation and max-size enforcement
   - **Cache Warming Strategies** to pre-load frequently accessed data
   - **Memory Usage Monitoring** for better resource management
   - **Automatic Cache Sharding** for improved performance and scalability
   - **Cache Validation Processes** to ensure the integrity of cached data
   - **Automatic Recovery Mechanisms** for cache failures

### Core Platform Integrations (src/integrations/)

10. **NATS Integration** (`src/integrations/nats_integration/`)
    - Asynchronous messaging for all AI components
    - Agent-to-agent communication via pub/sub
    - Gateway request queuing and response delivery
    - RAG document ingestion and query processing queues
    - Multi-tenant topic isolation
    - Error handling and reconnection logic

11. **OTEL Integration** (`src/integrations/otel_integration/`)
    - Distributed tracing across all components
    - Metrics collection for performance monitoring
    - Structured logging with trace context
    - Token usage and cost tracking
    - Trace propagation through NATS messages
    - Integration with OTEL collector

12. **CODEC Integration** (`src/integrations/codec_integration/`)
    - Message encoding/decoding for NATS communications
    - Schema versioning and migration
    - Message validation and error handling
    - Support for multiple encoding formats
    - Agent message, Gateway request/response, and RAG payload serialization


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
- **Agents ↔ Prompt Management**: Agents automatically use prompt management for context assembly
- **Agents ↔ Memory**: Agents use memory for context-aware prompt building
- **Cache ↔ All**: All components can use caching
- **Observability ↔ All**: All operations are traced and logged
- **NATS ↔ All**: Asynchronous messaging for all AI components
- **OTEL ↔ All**: Distributed tracing and metrics for all operations
- **CODEC ↔ NATS**: Message serialization for all NATS communications

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

## Function-Driven API

The SDK provides a **function-driven API** with factory functions, high-level convenience functions, and utilities for easy component creation and usage.

### Factory Functions

Create components with simplified configuration:

```python
# Agent Framework
from src.core.agno_agent_framework import create_agent, create_agent_with_memory, create_agent_manager

gateway = LiteLLMGateway()
agent = create_agent("agent1", "Assistant", gateway)
agent_with_memory = create_agent_with_memory(
    "agent2", "Analyst", gateway,
    memory_config={"persistence_path": "/tmp/memory.json"}
)
manager = create_agent_manager()

# RAG System with Enhanced Chunking and Metadata
from src.core.rag import create_rag_system, create_document_processor

# Create RAG system
rag = create_rag_system(db, gateway, embedding_model="text-embedding-3-small")

# Create document processor with enhanced features
processor = create_document_processor(
    chunk_size=1000,
    chunk_overlap=200,
    chunking_strategy="semantic",  # Use semantic chunking for structured docs
    min_chunk_size=100,  # Filter tiny chunks
    max_chunk_size=2000,  # Split oversized chunks
    enable_preprocessing=True,  # Enable text normalization
    enable_metadata_extraction=True  # Auto-extract metadata
)

# LiteLLM Gateway
from src.core.litellm_gateway import create_gateway

gateway = create_gateway(
    providers=["openai", "anthropic"],
    default_model="gpt-4",
    api_keys={"openai": "sk-...", "anthropic": "sk-..."}
)

# Prompt Management
from src.core.prompt_context_management import create_prompt_manager

prompt_manager = create_prompt_manager(max_tokens=8000)

# Cache Mechanism
from src.core.cache_mechanism import create_memory_cache, create_redis_cache

cache = create_memory_cache(default_ttl=600, max_size=2048)
redis_cache = create_redis_cache(redis_url="redis://localhost:6379/0")

# API Backend Services
from src.core.api_backend_services import create_api_app, create_api_router

app = create_api_app(title="AI SDK API", enable_cors=True)
router = create_api_router(prefix="/api/v1", tags=["agents"])
```

### High-Level Convenience Functions

Use simplified functions for common operations:

```python
# Agent Operations
from src.core.agno_agent_framework import chat_with_agent, execute_task

# Chat with agent (handles session management automatically)
response = await chat_with_agent(
    agent,
    "What is AI?",
    context={"user_id": "user123"}
)
print(response["answer"])

# Execute task easily
result = await execute_task(
    agent,
    "analyze",
    {"text": "Analyze this document", "model": "gpt-4"}
)

# RAG Operations with Enhanced Features
from src.core.rag import quick_rag_query, ingest_document_simple

# Quick RAG query with hybrid retrieval and query rewriting
result = quick_rag_query(
    rag, "What is machine learning?",
    top_k=5,
    retrieval_strategy="hybrid",
    use_query_rewriting=True
)
print(result["answer"])

# Simple document ingestion with automatic metadata extraction
# Metadata (title, dates, tags, language) is automatically extracted
doc_id = ingest_document_simple(
    rag,
    "AI Guide",
    "Artificial Intelligence is... #ai #ml",
    metadata={"category": "tutorial", "author": "AI Team"}
)

# Update document
from src.core.rag import update_document_simple, delete_document_simple
update_document_simple(rag, doc_id, title="Updated Guide", content="New content")

# Delete document
delete_document_simple(rag, doc_id)

# Gateway Operations
from src.core.litellm_gateway import generate_text, generate_embeddings

# Generate text easily
text = generate_text(gateway, "Explain quantum computing", model="gpt-4")

# Generate embeddings
embeddings = generate_embeddings(gateway, ["Hello", "World"])

# Prompt Management
from src.core.prompt_context_management import render_prompt, build_context

# Render prompt template
prompt = render_prompt(
    prompt_manager,
    "analysis_template",
    {"text": "Analyze this", "model": "gpt-4"}
)

# Build context from history
context = build_context(prompt_manager, "What is AI?", include_history=True)

# Cache Operations
from src.core.cache_mechanism import cache_get, cache_set, cache_delete

cache_set(cache, "user:123", {"name": "John"}, ttl=600)
value = cache_get(cache, "user:123")
cache_delete(cache, "user:123")

# API Operations
from src.core.api_backend_services import (
    register_router,
    create_rag_endpoints,
    create_agent_endpoints,
    add_health_check
)

create_rag_endpoints(router, rag, prefix="/api/rag")
create_agent_endpoints(router, agent_manager, prefix="/api/agents")
register_router(app, router)
add_health_check(app, path="/health")
```

### Utility Functions

Use utility functions for common patterns:

```python
# Batch Processing
from src.core.agno_agent_framework import batch_process_agents
from src.core.rag import batch_ingest_documents

# Process multiple agents concurrently
results = batch_process_agents(
    [agent1, agent2, agent3],
    "analyze",
    {"text": "..."}
)

# Batch ingest documents
doc_ids = batch_ingest_documents(rag, documents, batch_size=10)

# Retry Logic
from src.core.agno_agent_framework import retry_on_failure

@retry_on_failure(max_retries=3, retry_delay=1.0)
async def my_function():
    # Will retry up to 3 times on failure
    pass

# Cache Utilities
from src.core.cache_mechanism import cache_or_compute, batch_cache_set

# Cache or compute pattern
value = cache_or_compute(cache, "key", expensive_function, ttl=3600)

# Batch cache operations
items = {"key1": "value1", "key2": "value2"}
batch_cache_set(cache, items, ttl=600)
```

### Complete Example

```python
from src.core.litellm_gateway import create_gateway, generate_text
from src.core.agno_agent_framework import create_agent, chat_with_agent
from src.core.rag import create_rag_system, quick_rag_query

# Create gateway
gateway = create_gateway(providers=["openai"], default_model="gpt-4")

# Create agent
agent = create_agent("assistant", "AI Assistant", gateway)

# Chat with agent
response = await chat_with_agent(agent, "What is AI?")
print(response["answer"])

# Save agent state for persistence
from src.core.agno_agent_framework import save_agent_state, load_agent_state
save_agent_state(agent, "/tmp/agent_state.json")

# Load agent state later
restored_agent = load_agent_state("/tmp/agent_state.json", gateway)

# Create RAG system with enhanced chunking and metadata handling
rag = create_rag_system(db, gateway)

# Query RAG with hybrid retrieval and query optimization
result = quick_rag_query(
    rag, "What is machine learning?",
    retrieval_strategy="hybrid",
    use_query_rewriting=True  # Automatic query enhancement
)
print(result["answer"])

# Create cache
from src.core.cache_mechanism import create_memory_cache, cache_set
cache = create_memory_cache(default_ttl=600)
cache_set(cache, "result", result, ttl=300)

# Create API app
from src.core.api_backend_services import (
    create_api_app,
    create_api_router,
    create_rag_endpoints,
    register_router
)
app = create_api_app(title="AI SDK API")
router = create_api_router(prefix="/api/v1")
create_rag_endpoints(router, rag)
register_router(app, router)
```

See component-specific README files for detailed function documentation.

## Examples and Tutorials

The SDK includes comprehensive working examples and tutorials:

### Basic Usage Examples
- **Component Examples**: See `examples/basic_usage/` for working examples of each component
  - `01_observability_basic.py` - Observability and tracing
  - `02_postgresql_database_basic.py` - Database operations
  - `03_litellm_gateway_basic.py` - LLM operations
  - `04_cache_basic.py` - Caching strategies
  - `05_agent_basic.py` - Agent framework
  - `06_prompt_context_basic.py` - Prompt management
  - `07_rag_basic.py` - RAG system
  - `08_api_backend_basic.py` - REST API endpoints

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
  - `test_postgresql_database.py` - Database tests
  - `test_litellm_gateway.py` - Gateway tests
  - `test_cache.py` - Cache tests
  - `test_agent.py` - Agent framework tests
  - `test_rag.py` - RAG system tests

- **Function-Driven API Tests**: Comprehensive tests for function-driven API
  - `test_agent_functions.py` - Agent framework functions tests
  - `test_rag_functions.py` - RAG system functions tests
  - `test_cache_functions.py` - Cache mechanism functions tests
  - `test_api_functions.py` - API backend functions tests
  - `test_litellm_gateway_functions.py` - LiteLLM Gateway functions tests
  - `test_prompt_context_functions.py` - Prompt context functions tests

### Integration Tests
- **Component Integration**: See `src/tests/integration_tests/` for integration tests
  - `test_agent_rag_integration.py` - Agent-RAG integration
  - `test_api_agent_integration.py` - API-Agent integration
  - `test_end_to_end_workflows.py` - Complete workflow tests
  - `test_nats_integration.py` - NATS messaging integration
  - `test_otel_integration.py` - OpenTelemetry observability integration
  - `test_codec_integration.py` - CODEC serialization integration

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

# Run function-driven API tests
pytest src/tests/unit_tests/test_agent_functions.py -v
pytest src/tests/unit_tests/test_rag_functions.py -v

# Run all function-driven API tests
pytest src/tests/unit_tests/ -k "functions" -v
```

See `src/tests/unit_tests/README.md` and `src/tests/integration_tests/README.md` for detailed testing instructions.

## Documentation

- **Component Documentation**: See individual README files in each component folder
- **Examples**: See `examples/README.md` for working code examples
- **Tests**: See `src/tests/` for test suites and validation examples
- **Workflows**: See `docs/workflows.md` for detailed workflow diagrams
- **Libraries**: See `docs/libraries.md` for complete library list
- **Developer Guide**: See `README_DEVELOPER.md` for development guidelines
- **Ground Truth Analysis**: See `GROUND_TRUTH_ANALYSIS.md` for SDK as reference implementation guide
- **OpenTelemetry Guide**: See `OTEL_IMPLEMENTATION_GUIDE.md` for comprehensive OTEL integration and observability
- **Core Platform Integrations**: See `docs/integration_guides/` for NATS, OTEL, and CODEC integration guides
  - `nats_integration_guide.md` - NATS messaging integration
  - `otel_integration_guide.md` - OpenTelemetry observability integration
  - `codec_integration_guide.md` - CODEC serialization integration
- **Integration Story**: See `docs/components/CORE_COMPONENTS_INTEGRATION_STORY.md` for comprehensive integration architecture and workflow
- **End-to-End Flow**: See `docs/AI_SDK_END_TO_END_FLOW.md` for complete development to runtime execution flow
- **Architecture**: See `docs/architecture/` for detailed architecture documentation
- **Component Explanations**: See `docs/components/` for comprehensive component documentation

## Modularity and Swappability

The SDK is designed with modularity in mind:

- **Agent Frameworks**: Swap Agno with LangChain or other frameworks
- **Database Backends**: Swap PostgreSQL with other databases
- **Cache Backends**: Swap Redis with memory or database caching
- **LLM Providers**: Switch between providers via LiteLLM

See component README files for swapping instructions.

## Error Handling

The SDK uses a structured exception hierarchy for granular error handling and debugging. All SDK exceptions inherit from `SDKError`, enabling platform-wide catching and uniform error handling.

### Exception Hierarchy

```
SDKError (Base)
├── AgentError
│   ├── AgentExecutionError
│   ├── AgentConfigurationError
│   └── AgentStateError
├── ToolError
│   ├── ToolInvocationError
│   ├── ToolNotFoundError
│   ├── ToolNotImplementedError
│   └── ToolValidationError
├── MemoryError
│   ├── MemoryReadError
│   ├── MemoryWriteError
│   └── MemoryPersistenceError
├── OrchestrationError
│   ├── WorkflowNotFoundError
│   └── AgentNotFoundError
└── RAGError
    ├── RetrievalError
    ├── GenerationError
    ├── EmbeddingError
    ├── DocumentProcessingError
    ├── ChunkingError
    └── ValidationError
```

### Usage Examples

**Catching Specific Errors:**
```python
from src.core.agno_agent_framework.exceptions import (
    AgentExecutionError,
    ToolInvocationError
)
from src.core.rag.exceptions import RetrievalError

try:
    result = await agent.execute_task(task)
except AgentExecutionError as e:
    print(f"Agent {e.agent_id} failed: {e.message}")
    print(f"Task type: {e.task_type}, Stage: {e.execution_stage}")
except ToolInvocationError as e:
    print(f"Tool {e.tool_name} failed: {e.message}")
    print(f"Error type: {e.error_type}")
except RetrievalError as e:
    print(f"Retrieval failed for query: {e.query}")
```

**Catching All SDK Errors:**
```python
from src.core.exceptions import SDKError

try:
    # Any SDK operation
    result = await agent.execute_task(task)
except SDKError as e:
    print(f"SDK error: {e.message}")
    if e.original_error:
        print(f"Original error: {e.original_error}")
```

**Error Location:**
- Base exception: `src/core/exceptions.py`
- Agent Framework exceptions: `src/core/agno_agent_framework/exceptions.py`
- RAG exceptions: `src/core/rag/exceptions.py`

All exceptions include structured attributes (agent_id, tool_name, operation, etc.) for enhanced debugging and monitoring.

## License

MIT License - see LICENSE file for details.

