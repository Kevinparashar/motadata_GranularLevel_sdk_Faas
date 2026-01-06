# Function-Driven API Documentation

**Created:** 2026-01-06 15:42:21

## Overview

The Motadata Python AI SDK provides a **function-driven API** that makes it easy to create, configure, and use SDK components. This approach follows standard SDK design patterns where components are driven by functions that can be easily discovered and used.

## Design Principles

1. **Function-First**: Functions are the primary interface for component creation and operations
2. **Simplified Configuration**: Factory functions handle complex initialization
3. **High-Level Convenience**: Common operations have dedicated convenience functions
4. **Utility Functions**: Reusable utilities for common patterns (batch processing, retries, etc.)

## Component Functions

### 1. Agno Agent Framework ✅

**Location:** `src/core/agno_agent_framework/functions.py`

#### Factory Functions
- `create_agent()` - Create and configure an agent
- `create_agent_with_memory()` - Create agent with memory pre-configured
- `create_agent_manager()` - Create an AgentManager instance
- `create_orchestrator()` - Create an AgentOrchestrator for workflows

#### High-Level Convenience Functions
- `chat_with_agent()` - Chat with agent (handles session management automatically)
- `execute_task()` - Execute a task on an agent
- `delegate_task()` - Delegate task between agents
- `find_agents_by_capability()` - Find agents by capability

#### Utility Functions
- `batch_process_agents()` - Process tasks on multiple agents concurrently
- `retry_on_failure()` - Decorator for retry logic

**Example:**
```python
from src.core.agno_agent_framework import (
    create_agent,
    chat_with_agent,
    execute_task
)

gateway = LiteLLMGateway()
agent = create_agent("agent1", "Assistant", gateway)

response = await chat_with_agent(agent, "What is AI?")
result = await execute_task(agent, "analyze", {"text": "..."})
```

### 2. RAG System ✅

**Location:** `src/core/rag/functions.py`

#### Factory Functions
- `create_rag_system()` - Create and configure a RAG system
- `create_document_processor()` - Create a document processor

#### High-Level Convenience Functions
- `quick_rag_query()` - Quick RAG query without manual setup
- `quick_rag_query_async()` - Async quick RAG query
- `ingest_document_simple()` - Simple document ingestion
- `ingest_document_simple_async()` - Async simple document ingestion
- `batch_ingest_documents()` - Batch ingest multiple documents
- `batch_ingest_documents_async()` - Async batch ingest

#### Utility Functions
- `batch_process_documents()` - Process documents in batches

**Example:**
```python
from src.core.rag import (
    create_rag_system,
    quick_rag_query,
    ingest_document_simple
)

rag = create_rag_system(db, gateway)
result = quick_rag_query(rag, "What is AI?", top_k=5)
doc_id = ingest_document_simple(rag, "AI Guide", "Content...")
```

### 3. LiteLLM Gateway ✅

**Location:** `src/core/litellm_gateway/functions.py`

#### Factory Functions
- `create_gateway()` - Create and configure a LiteLLM Gateway
- `configure_gateway()` - Create a GatewayConfig

#### High-Level Convenience Functions
- `generate_text()` - Generate text with simplified interface
- `generate_text_async()` - Async text generation
- `stream_text()` - Stream text generation
- `generate_embeddings()` - Generate embeddings with simplified interface
- `generate_embeddings_async()` - Async embeddings generation

#### Utility Functions
- `batch_generate()` - Generate text for multiple prompts concurrently

**Example:**
```python
from src.core.litellm_gateway import (
    create_gateway,
    generate_text,
    generate_embeddings
)

gateway = create_gateway(
    providers=["openai"],
    default_model="gpt-4"
)
text = generate_text(gateway, "What is AI?")
embeddings = generate_embeddings(gateway, ["Hello", "World"])
```

### 4. Prompt Context Management ✅

**Location:** `src/core/prompt_context_management/functions.py`

#### Factory Functions
- `create_prompt_manager()` - Create and configure a PromptContextManager
- `create_context_window_manager()` - Create a ContextWindowManager

#### High-Level Convenience Functions
- `render_prompt()` - Render a prompt template with variables
- `add_template()` - Add a prompt template
- `build_context()` - Build context from history and new message
- `truncate_to_fit()` - Truncate prompt to fit within token limits
- `redact_sensitive()` - Redact sensitive information from text

#### Utility Functions
- `estimate_tokens()` - Estimate token count for text
- `validate_prompt_length()` - Validate if prompt fits within token limits

**Example:**
```python
from src.core.prompt_context_management import (
    create_prompt_manager,
    render_prompt,
    build_context
)

manager = create_prompt_manager(max_tokens=8000)
prompt = render_prompt(manager, "template", {"var": "value"})
context = build_context(manager, "What is AI?", include_history=True)
```

### 5. Cache Mechanism ✅

**Location:** `src/core/cache_mechanism/functions.py`

#### Factory Functions
- `create_cache()` - Create and configure a cache
- `create_memory_cache()` - Create an in-memory cache
- `create_redis_cache()` - Create a Redis cache
- `configure_cache()` - Create a CacheConfig

#### High-Level Convenience Functions
- `cache_get()` - Get a value from cache
- `cache_set()` - Set a value in cache
- `cache_delete()` - Delete a value from cache
- `cache_clear_pattern()` - Clear keys matching a pattern

#### Utility Functions
- `cache_or_compute()` - Get from cache or compute and cache
- `batch_cache_set()` - Set multiple values at once
- `batch_cache_get()` - Get multiple values at once

**Example:**
```python
from src.core.cache_mechanism import (
    create_memory_cache,
    cache_get,
    cache_set
)

cache = create_memory_cache(default_ttl=600)
cache_set(cache, "user:123", {"name": "John"}, ttl=600)
value = cache_get(cache, "user:123")
```

### 6. API Backend Services ✅

**Location:** `src/core/api_backend_services/functions.py`

#### Factory Functions
- `create_api_app()` - Create and configure a FastAPI application
- `create_api_router()` - Create an API router
- `configure_api_app()` - Configure an existing FastAPI app

#### High-Level Convenience Functions
- `register_router()` - Register a router with the app
- `add_endpoint()` - Add an endpoint to a router
- `create_rag_endpoints()` - Create RAG system endpoints
- `create_agent_endpoints()` - Create agent framework endpoints
- `create_gateway_endpoints()` - Create gateway endpoints

#### Utility Functions
- `add_health_check()` - Add a health check endpoint
- `add_api_versioning()` - Set up API versioning

**Example:**
```python
from src.core.api_backend_services import (
    create_api_app,
    create_rag_endpoints,
    create_agent_endpoints
)

app = create_api_app(title="AI SDK API")
router = create_api_router(prefix="/api/v1")
create_rag_endpoints(router, rag_system)
create_agent_endpoints(router, agent_manager)
register_router(app, router)
```

## Benefits

1. **Easier Discovery**: Functions are easy to find and understand
2. **Simplified Usage**: High-level functions hide complexity
3. **Consistent Patterns**: All components follow the same function-driven pattern
4. **Better Developer Experience**: Less boilerplate code required
5. **Standard SDK Pattern**: Follows industry-standard SDK design

## Migration Guide

### Before (Class-Based)
```python
from src.core.agno_agent_framework import Agent

agent = Agent(
    agent_id="agent1",
    name="Assistant",
    gateway=gateway,
    description="",
    llm_model=None,
    llm_provider=None
)
memory = AgentMemory(agent_id="agent1", persistence_path="/tmp/memory.json")
agent.attach_memory("/tmp/memory.json")
```

### After (Function-Driven)
```python
from src.core.agno_agent_framework import create_agent_with_memory

agent = create_agent_with_memory(
    "agent1",
    "Assistant",
    gateway,
    memory_config={"persistence_path": "/tmp/memory.json"}
)
```

## Complete Example

```python
from src.core.litellm_gateway import create_gateway, generate_text
from src.core.agno_agent_framework import create_agent, chat_with_agent
from src.core.rag import create_rag_system, quick_rag_query
from src.core.prompt_context_management import create_prompt_manager
from src.core.cache_mechanism import create_memory_cache, cache_set
from src.core.api_backend_services import create_api_app, create_rag_endpoints

# Create gateway
gateway = create_gateway(providers=["openai"], default_model="gpt-4")

# Create agent
agent = create_agent("assistant", "AI Assistant", gateway)

# Chat with agent
response = await chat_with_agent(agent, "What is AI?")
print(response["answer"])

# Create RAG system
rag = create_rag_system(db, gateway)

# Query RAG
result = quick_rag_query(rag, "What is machine learning?")
print(result["answer"])

# Create prompt manager
prompt_manager = create_prompt_manager(max_tokens=8000)

# Create cache
cache = create_memory_cache(default_ttl=600)
cache_set(cache, "key", "value", ttl=300)

# Create API app
app = create_api_app(title="AI SDK API")
router = create_api_router(prefix="/api/v1")
create_rag_endpoints(router, rag)
register_router(app, router)
```

## Testing

Comprehensive test coverage is provided for all function-driven API components:

### Test Files

- **`test_agent_functions.py`**: Tests for agent framework functions (factory, convenience, utilities)
- **`test_rag_functions.py`**: Tests for RAG system functions
- **`test_cache_functions.py`**: Tests for cache mechanism functions
- **`test_api_functions.py`**: Tests for API backend functions
- **`test_litellm_gateway_functions.py`**: Tests for LiteLLM Gateway functions
- **`test_prompt_context_functions.py`**: Tests for prompt context management functions

### Running Function Tests

```bash
# Run all function-driven API tests
pytest src/tests/unit_tests/ -k "functions" -v

# Run specific function test file
pytest src/tests/unit_tests/test_agent_functions.py -v

# Run with coverage
pytest src/tests/unit_tests/ -k "functions" --cov=src/core --cov-report=html
```

### Test Coverage

Each test file includes:
- ✅ Factory function tests (create_*, configure_*)
- ✅ Convenience function tests (high-level operations)
- ✅ Utility function tests (batch processing, retries)
- ✅ Edge case and error handling tests
- ✅ Async function tests (where applicable)
- ✅ Mocking of external dependencies

## Documentation

- **Component READMEs**: Each component README includes function-driven API documentation
- **Main README**: See `README.md` for function-driven API overview
- **Function Files**: See `src/core/{component}/functions.py` for complete function documentation
- **Test Files**: See `src/tests/unit_tests/test_*_functions.py` for test examples and validation

## Standards Compliance

This function-driven API follows standard SDK design patterns:
- ✅ Factory functions for component creation
- ✅ High-level convenience functions for common operations
- ✅ Utility functions for reusable patterns
- ✅ Consistent naming conventions
- ✅ Comprehensive documentation
- ✅ Type hints for better IDE support

