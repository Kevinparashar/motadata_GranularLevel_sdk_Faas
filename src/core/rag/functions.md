# RAG System Functions Documentation

## Overview

The `functions.py` file provides high-level factory functions, convenience functions, and utilities for the RAG System. These functions simplify RAG system creation, configuration, and common operations, making it easier for developers to work with RAG without directly instantiating the `RAGSystem` class or managing complex configurations.

**Primary Functionality:**
- Factory functions for creating RAG systems with different configurations
- Convenience functions for common RAG operations (ingestion, querying)
- Quick query functions for simple use cases
- Batch processing utilities for handling multiple documents
- Configuration helpers for setting up RAG systems

## Code Explanation

### Function Categories

The file is organized into several categories:

#### 1. Factory Functions
Factory functions create and configure RAG systems:

- **`create_rag_system()`**: Create RAG system with simplified configuration
- **`create_rag_system_with_memory()`**: Create RAG system with memory pre-configured
- **`create_rag_system_with_cache()`**: Create RAG system with caching pre-configured

#### 2. Convenience Functions
High-level functions for common operations:

- **`quick_rag_query()`**: Quick query function for simple use cases
- **`quick_rag_query_async()`**: Async version of quick query
- **`ingest_document()`**: Simplified document ingestion
- **`ingest_document_async()`**: Async document ingestion
- **`query_rag()`**: Simplified query function
- **`query_rag_async()`**: Async query function

#### 3. Batch Processing Functions
Utilities for batch operations:

- **`ingest_documents_batch()`**: Batch document ingestion
- **`ingest_documents_batch_async()`**: Async batch ingestion

### Key Functions

#### `create_rag_system(db, gateway, **kwargs) -> RAGSystem`
Creates a RAG system instance with validation and helpful error messages.

**Parameters:**
- `db`: Database connection instance
- `gateway`: LiteLLM Gateway instance
- `embedding_model`: Model for embeddings (default: "text-embedding-3-small")
- `generation_model`: Model for generation (default: "gpt-4")
- `cache`: Optional cache mechanism
- `cache_config`: Optional cache configuration
- `enable_memory`: Enable memory for conversation context (default: True)
- `memory_config`: Optional memory configuration
- `**kwargs`: Additional RAG configuration:
  - `chunk_size`: Document chunk size (default: 1000)
  - `chunk_overlap`: Chunk overlap size (default: 200)
  - `chunking_strategy`: Chunking strategy (default: "fixed")

**Returns:** Configured `RAGSystem` instance

**Example:**
```python
from src.core.rag import create_rag_system
from src.core.litellm_gateway import create_gateway
from src.core.postgresql_database import create_database_connection

gateway = create_gateway(api_keys={'openai': 'key'}, default_model='gpt-4')
db = create_database_connection("postgresql://user:pass@localhost/db")

rag = create_rag_system(
    db=db,
    gateway=gateway,
    embedding_model="text-embedding-3-small",
    generation_model="gpt-4"
)
```

#### `async def quick_rag_query(rag, query, top_k=5, **kwargs) -> Dict[str, Any]`
Quick query function for simple use cases.

**Parameters:**
- `rag`: RAGSystem instance
- `query`: Query text
- `top_k`: Number of documents to retrieve (default: 5)
- `tenant_id`: Optional tenant ID
- `**kwargs`: Additional query parameters

**Returns:** Dictionary with answer and sources

**Example:**
```python
result = await quick_rag_query(rag, "What is AI?", top_k=5)
print(result["answer"])
```

#### `async def ingest_document(rag, title, content=None, file_path=None, **kwargs) -> str`
Simplified document ingestion function.

**Parameters:**
- `rag`: RAGSystem instance
- `title`: Document title
- `content`: Document content (if provided directly)
- `file_path`: Path to file (for multi-modal loading)
- `tenant_id`: Optional tenant ID
- `metadata`: Optional metadata

**Returns:** Document ID

**Example:**
```python
doc_id = await ingest_document(
    rag,
    title="AI Guide",
    content="Artificial intelligence is...",
    tenant_id="tenant_123"
)
```

#### `async def query_rag(rag, query, top_k=5, **kwargs) -> Dict[str, Any]`
Simplified query function.

**Parameters:** Same as `quick_rag_query()`

**Returns:** Dictionary with query results

#### `async def ingest_documents_batch(rag, documents, **kwargs) -> List[str]`
Batch document ingestion.

**Parameters:**
- `rag`: RAGSystem instance
- `documents`: List of document dictionaries with keys:
  - `title`: Document title
  - `content`: Document content (optional)
  - `file_path`: Path to file (optional)
  - `metadata`: Optional metadata
- `tenant_id`: Optional tenant ID for all documents
- `**kwargs`: Additional parameters

**Returns:** List of document IDs

**Example:**
```python
documents = [
    {"title": "Doc 1", "content": "Content 1"},
    {"title": "Doc 2", "content": "Content 2"},
    {"title": "Doc 3", "file_path": "/path/to/doc.pdf"}
]
doc_ids = await ingest_documents_batch(rag, documents, tenant_id="tenant_123")
```

## Usage Instructions

### Basic RAG System Creation

```python
from src.core.rag import create_rag_system
from src.core.litellm_gateway import create_gateway
from src.core.postgresql_database import create_database_connection

# Create dependencies
gateway = create_gateway(api_keys={'openai': 'key'}, default_model='gpt-4')
db = create_database_connection("postgresql://user:pass@localhost/db")

# Create RAG system
rag = create_rag_system(
    db=db,
    gateway=gateway,
    embedding_model="text-embedding-3-small",
    generation_model="gpt-4"
)
```

### Quick Query

```python
from src.core.rag import create_rag_system, quick_rag_query_async

# Create RAG system (as above)
rag = create_rag_system(db=db, gateway=gateway)

# Quick query
result = await quick_rag_query_async(
    rag,
    query="What is artificial intelligence?",
    top_k=5,
    tenant_id="tenant_123"
)

print(f"Answer: {result['answer']}")
print(f"Sources: {len(result['sources'])} documents")
```

### Document Ingestion

```python
from src.core.rag import create_rag_system, ingest_document_async

rag = create_rag_system(db=db, gateway=gateway)

# Ingest text content
doc_id = await ingest_document_async(
    rag,
    title="AI Guide",
    content="Artificial intelligence is the simulation of human intelligence...",
    tenant_id="tenant_123",
    metadata={"category": "technology"}
)

# Ingest from file
doc_id = await ingest_document_async(
    rag,
    title="Product Manual",
    file_path="/path/to/manual.pdf",
    tenant_id="tenant_123"
)
```

### Batch Ingestion

```python
from src.core.rag import create_rag_system, ingest_documents_batch_async

rag = create_rag_system(db=db, gateway=gateway)

documents = [
    {"title": "Introduction to AI", "content": "AI is..."},
    {"title": "Machine Learning Basics", "content": "ML is..."},
    {"title": "Deep Learning Guide", "file_path": "/path/to/deep_learning.pdf"}
]

doc_ids = await ingest_documents_batch_async(
    rag,
    documents,
    tenant_id="tenant_123"
)

print(f"Ingested {len(doc_ids)} documents")
```

### With Memory

```python
from src.core.rag import create_rag_system_with_memory

rag = create_rag_system_with_memory(
    db=db,
    gateway=gateway,
    memory_config={
        "max_episodic": 100,
        "max_semantic": 200,
        "persistence_path": "/tmp/rag_memory.json"
    }
)

# First query
result1 = await quick_rag_query_async(
    rag,
    "What is AI?",
    session_id="session_001"
)

# Follow-up query (uses conversation context)
result2 = await quick_rag_query_async(
    rag,
    "Can you give me more details?",
    session_id="session_001"  # Same session
)
```

### With Caching

```python
from src.core.rag import create_rag_system_with_cache
from src.core.cache_mechanism import CacheConfig

rag = create_rag_system_with_cache(
    db=db,
    gateway=gateway,
    cache_config=CacheConfig(
        backend="redis",
        redis_url="redis://localhost:6379",
        ttl=3600
    )
)

# First query - hits LLM
result1 = await quick_rag_query_async(rag, "What is AI?")

# Second query - returns cached result
result2 = await quick_rag_query_async(rag, "What is AI?")  # Faster!
```

### Prerequisites

1. **Python 3.10+**: Required for type hints and async/await
2. **Dependencies**: Install via `pip install -r requirements.txt`
   - `litellm`: For LLM operations
   - `pgvector`: For vector operations
   - `pydantic`: For data validation
3. **Database**: PostgreSQL with pgvector extension
4. **API Keys**: LLM provider API keys
5. **Vector Index**: Create vector index for efficient search

## Connection to Other Components

### RAG System Class
These functions create and use `RAGSystem` instances from `rag_system.py`:
- All factory functions return `RAGSystem` instances
- Convenience functions use RAG system methods internally

**Integration Point:** Functions wrap `RAGSystem` class instantiation and methods

### Database Connection
Uses `DatabaseConnection` from `src/core/postgresql_database/connection.py`:
- Required parameter for RAG system creation
- Stores documents and embeddings

**Integration Point:** `db` parameter in factory functions

### LiteLLM Gateway
Uses `LiteLLMGateway` from `src/core/litellm_gateway/gateway.py`:
- Required parameter for RAG system creation
- Generates embeddings and responses

**Integration Point:** `gateway` parameter in factory functions

### Cache Mechanism
Uses `CacheMechanism` from `src/core/cache_mechanism/`:
- Optional caching for query results
- Improves performance and reduces costs

**Integration Point:** `cache` or `cache_config` parameters

### Agent Memory
Uses `AgentMemory` from `src/core/agno_agent_framework/memory.py`:
- Optional memory for conversation context
- Enables multi-turn interactions

**Integration Point:** `memory_config` parameter

### Where Used
- **Examples**: All RAG examples use these functions
- **API Backend Services**: HTTP endpoints use these functions
- **FaaS RAG Service**: REST API wrapper uses these functions
- **User Applications**: Primary interface for creating RAG systems

## Best Practices

### 1. Use Factory Functions
Always use factory functions instead of directly instantiating `RAGSystem`:
```python
# Good: Use factory function
rag = create_rag_system(db=db, gateway=gateway)

# Bad: Direct instantiation (unless you need full control)
from src.core.rag.rag_system import RAGSystem
rag = RAGSystem(db=db, gateway=gateway, ...)
```

### 2. Use Async Functions
Always prefer async functions for production:
```python
# Good: Async for better performance
result = await quick_rag_query_async(rag, "query")
doc_id = await ingest_document_async(rag, "Title", content="...")

# Bad: Synchronous blocks event loop
result = quick_rag_query(rag, "query")
doc_id = ingest_document(rag, "Title", content="...")
```

### 3. Provide Tenant IDs
Always provide tenant_id for multi-tenant applications:
```python
# Good: Tenant-scoped operations
result = await quick_rag_query_async(rag, "query", tenant_id="tenant_123")
doc_id = await ingest_document_async(rag, "Title", content="...", tenant_id="tenant_123")

# Bad: Missing tenant_id in multi-tenant system
result = await quick_rag_query_async(rag, "query")
```

### 4. Use Batch Processing
Use batch processing for multiple documents:
```python
# Good: Batch processing
doc_ids = await ingest_documents_batch_async(rag, documents)

# Bad: Sequential processing
doc_ids = []
for doc in documents:
    doc_id = await ingest_document_async(rag, doc["title"], content=doc["content"])
    doc_ids.append(doc_id)
```

### 5. Enable Caching
Enable caching for repeated queries:
```python
# Good: Caching enabled
rag = create_rag_system_with_cache(db=db, gateway=gateway, cache_config=...)

# Bad: No caching (higher costs, slower)
rag = create_rag_system(db=db, gateway=gateway)
```

### 6. Configure Chunking
Set appropriate chunking parameters:
```python
# Good: Configured chunking
rag = create_rag_system(
    db=db,
    gateway=gateway,
    chunk_size=1000,
    chunk_overlap=200,
    chunking_strategy="sentence"
)

# Bad: Default chunking may not be optimal
rag = create_rag_system(db=db, gateway=gateway)
```

### 7. Handle Errors
Always handle errors appropriately:
```python
# Good: Error handling
try:
    result = await quick_rag_query_async(rag, "query")
except Exception as e:
    logger.error(f"Query failed: {e}")
    # Handle error

# Bad: No error handling
result = await quick_rag_query_async(rag, "query")  # May crash
```

### 8. Use Memory for Conversations
Enable memory for multi-turn interactions:
```python
# Good: Memory enabled
rag = create_rag_system_with_memory(
    db=db,
    gateway=gateway,
    memory_config={"max_episodic": 100}
)

# Bad: No memory (loses conversation context)
rag = create_rag_system(db=db, gateway=gateway, enable_memory=False)
```

## Additional Resources

### Documentation
- **[RAG System Class Documentation](rag_system.md)** - Core RAGSystem class
- **[RAG README](README.md)** - Complete RAG system guide
- **[RAG Troubleshooting](../../../docs/troubleshooting/rag_troubleshooting.md)** - Common issues

### Related Components
- **[RAG System Class](rag_system.py)** - Core RAG implementation
- **[Document Processor](document_processor.py)** - Document processing
- **[Retriever](retriever.py)** - Document retrieval
- **[Generator](generator.py)** - Response generation

### External Resources
- **[RAG Paper](https://arxiv.org/abs/2005.11401)** - Original RAG research
- **[Vector Similarity Search](https://www.pinecone.io/learn/vector-similarity-search/)** - Vector search guide
- **[PostgreSQL pgvector](https://github.com/pgvector/pgvector)** - pgvector docs

### Examples
- **[Basic RAG Example](../../../../examples/basic_usage/07_rag_basic.py)** - Simple RAG usage
- **[RAG with Multi-Modal Example](../../../../examples/)** - Multi-modal processing
- **[RAG with Memory Example](../../../../examples/)** - Conversation memory

