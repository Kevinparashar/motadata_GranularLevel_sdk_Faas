# MOTADATA - RAG SYSTEM CLASS DOCUMENTATION

**Complete class documentation for the RAGSystem class providing Retrieval-Augmented Generation capabilities.**

## Overview

The `rag_system.py` file contains the core `RAGSystem` class implementation, which provides a complete Retrieval-Augmented Generation (RAG) system. This class integrates document processing, vector retrieval, and LLM generation to enable context-aware AI applications that can answer questions based on a knowledge base of documents.

**Primary Functionality:**
- Document ingestion with multi-modal support (text, PDF, audio, video, images)
- Vector-based document retrieval
- Context-aware text generation using retrieved documents
- Conversation memory for multi-turn interactions
- Document management (update, delete, versioning)
- Incremental updates and real-time synchronization
- Relevance scoring and re-ranking
- Hallucination detection

## Code Explanation

### Class Structure

#### `RAGSystem` (Class)
Main RAG system class that integrates all components.

**Core Attributes:**
- `db`: Database connection for vector storage
- `gateway`: LiteLLM Gateway for embeddings and generation
- `embedding_model`: Model for generating embeddings
- `generation_model`: Model for text generation
- `cache`: Cache mechanism for performance optimization
- `memory`: AgentMemory for conversation context

**Component Instances:**
- `vector_ops`: VectorOperations for vector database operations
- `index_manager`: VectorIndexManager for index management
- `document_processor`: DocumentProcessor for document processing
- `retriever`: Retriever for document retrieval
- `generator`: RAGGenerator for response generation

### Key Methods

#### `ingest_document(title, content=None, file_path=None, **kwargs) -> str`
Ingests a document into the RAG system.

**Parameters:**
- `title`: Document title
- `content`: Document content (if provided directly)
- `file_path`: Path to file (for multi-modal loading)
- `tenant_id`: Optional tenant ID for multi-tenant SaaS
- `source`: Optional source URL/path
- `metadata`: Optional metadata dictionary

**Supported Formats:**
- **Text**: .txt, .md, .html, .json
- **Documents**: .pdf, .doc, .docx
- **Audio**: .mp3, .wav, .m4a, .ogg (with transcription)
- **Video**: .mp4, .avi, .mov, .mkv (with transcription and frame extraction)
- **Images**: .jpg, .png, .gif, .bmp (with OCR and description)

**Process:**
1. Loads document from file or uses provided content
2. Processes document (chunking, preprocessing)
3. Generates embeddings for chunks
4. Stores chunks and embeddings in vector database
5. Returns document ID

**Returns:** Document ID string

#### `async def ingest_document_async(title, content=None, file_path=None, **kwargs) -> str`
Asynchronous document ingestion (recommended for production).

**Parameters:** Same as `ingest_document()`

**Returns:** Document ID string

#### `query(query_text, top_k=5, **kwargs) -> Dict[str, Any]`
Queries the RAG system and generates a response.

**Parameters:**
- `query_text`: User query text
- `top_k`: Number of top documents to retrieve (default: 5)
- `tenant_id`: Optional tenant ID for filtering
- `rerank`: Enable re-ranking (default: True)
- `min_score`: Minimum relevance score (default: 0.0)
- `use_memory`: Use conversation memory (default: True)
- `**kwargs`: Additional query parameters

**Process:**
1. Converts query to embedding
2. Retrieves top-k relevant documents
3. Re-ranks documents (if enabled)
4. Builds context from retrieved documents
5. Generates response using context
6. Detects hallucinations (if enabled)
7. Updates conversation memory
8. Returns response with sources

**Returns:** Dictionary with:
- `answer`: Generated answer
- `sources`: List of source documents
- `relevance_scores`: Relevance scores for sources
- `metadata`: Additional metadata

#### `async def query_async(query_text, top_k=5, **kwargs) -> Dict[str, Any]`
Asynchronous query processing (recommended for production).

**Parameters:** Same as `query()`

**Returns:** Dictionary with query results

#### `update_document(document_id, title=None, content=None, **kwargs) -> bool`
Updates an existing document.

**Parameters:**
- `document_id`: Document ID to update
- `title`: Optional new title
- `content`: Optional new content
- `metadata`: Optional updated metadata
- `tenant_id`: Optional tenant ID for validation

**Process:**
1. Validates document exists
2. Updates document metadata
3. Re-processes content if provided
4. Updates embeddings if content changed
5. Returns success status

**Returns:** Boolean indicating success

#### `delete_document(document_id, tenant_id=None) -> bool`
Deletes a document from the RAG system.

**Parameters:**
- `document_id`: Document ID to delete
- `tenant_id`: Optional tenant ID for validation

**Returns:** Boolean indicating success

#### `get_document(document_id, tenant_id=None) -> Optional[Dict[str, Any]]`
Retrieves document information.

**Parameters:**
- `document_id`: Document ID
- `tenant_id`: Optional tenant ID for filtering

**Returns:** Dictionary with document information or None

#### `list_documents(tenant_id=None, limit=100, offset=0) -> List[Dict[str, Any]]`
Lists documents in the system.

**Parameters:**
- `tenant_id`: Optional tenant ID for filtering
- `limit`: Maximum number of documents (default: 100)
- `offset`: Offset for pagination (default: 0)

**Returns:** List of document dictionaries

## Usage Instructions

### Basic RAG System Creation

```python
from src.core.rag import RAGSystem
from src.core.litellm_gateway import create_gateway
from src.core.postgresql_database import create_database_connection

# Create dependencies
gateway = create_gateway(api_keys={'openai': 'your-api-key'}, default_model='gpt-4')
db = create_database_connection("postgresql://user:pass@localhost/db")

# Create RAG system
rag = RAGSystem(
    db=db,
    gateway=gateway,
    embedding_model="text-embedding-3-small",
    generation_model="gpt-4"
)
```

### Document Ingestion

```python
# Ingest text content directly
doc_id = rag.ingest_document(
    title="AI Guide",
    content="Artificial intelligence is...",
    tenant_id="tenant_123",
    metadata={"category": "technology"}
)

# Ingest from file (supports multiple formats)
doc_id = await rag.ingest_document_async(
    title="Product Manual",
    file_path="/path/to/manual.pdf",
    tenant_id="tenant_123"
)

# Ingest image with OCR
doc_id = await rag.ingest_document_async(
    title="Diagram",
    file_path="/path/to/diagram.png",
    tenant_id="tenant_123"
)
```

### Querying the RAG System

```python
# Basic query
result = await rag.query_async(
    query_text="What is artificial intelligence?",
    top_k=5,
    tenant_id="tenant_123"
)

print(f"Answer: {result['answer']}")
print(f"Sources: {result['sources']}")

# Query with re-ranking
result = await rag.query_async(
    query_text="Explain machine learning",
    top_k=10,
    rerank=True,
    min_score=0.7
)
```

### Document Management

```python
# Update document
success = rag.update_document(
    document_id=doc_id,
    title="Updated Title",
    content="Updated content...",
    tenant_id="tenant_123"
)

# Delete document
success = rag.delete_document(
    document_id=doc_id,
    tenant_id="tenant_123"
)

# Get document
doc = rag.get_document(document_id, tenant_id="tenant_123")
if doc:
    print(f"Title: {doc['title']}")
    print(f"Chunks: {doc['chunk_count']}")

# List documents
docs = rag.list_documents(
    tenant_id="tenant_123",
    limit=50,
    offset=0
)
```

### With Memory for Conversations

```python
# Create RAG system with memory
rag = RAGSystem(
    db=db,
    gateway=gateway,
    enable_memory=True,
    memory_config={
        "max_episodic": 100,
        "max_semantic": 200,
        "persistence_path": "/tmp/rag_memory.json"
    }
)

# First query
result1 = await rag.query_async(
    "What is AI?",
    session_id="session_001"
)

# Follow-up query (uses conversation context)
result2 = await rag.query_async(
    "Can you give me more details?",
    session_id="session_001"  # Same session
)
```

### Prerequisites

1. **Python 3.10+**: Required for type hints and async/await
2. **Dependencies**: Install via `pip install -r requirements.txt`
   - `litellm`: For LLM operations
   - `pgvector`: For vector operations in PostgreSQL
   - `pydantic`: For data validation
   - Optional: `Pillow`, `opencv-python`, `pydub` for multi-modal support
3. **Database**: PostgreSQL with pgvector extension
4. **API Keys**: LLM provider API keys for embeddings and generation
5. **Vector Index**: Create vector index for efficient similarity search

## Connection to Other Components

### Database Connection
Uses `DatabaseConnection` from `src/core/postgresql_database/connection.py`:
- Stores document metadata
- Stores vector embeddings
- Manages document versions

**Integration Point:** `rag.db` attribute

### Vector Operations
Uses `VectorOperations` from `src/core/postgresql_database/vector_operations.py`:
- Stores and retrieves embeddings
- Performs similarity search
- Manages vector indexes

**Integration Point:** `rag.vector_ops` attribute

### Vector Index Manager
Uses `VectorIndexManager` from `src/core/postgresql_database/vector_index_manager.py`:
- Creates and manages vector indexes
- Optimizes search performance
- Supports IVFFlat and HNSW indexes

**Integration Point:** `rag.index_manager` attribute

### LiteLLM Gateway
Uses `LiteLLMGateway` from `src/core/litellm_gateway/gateway.py`:
- Generates embeddings for documents and queries
- Generates responses using retrieved context
- Handles multi-modal processing (image descriptions)

**Integration Point:** `rag.gateway` attribute

### Document Processor
Uses `DocumentProcessor` from `src/core/rag/document_processor.py`:
- Processes documents (chunking, preprocessing)
- Extracts metadata
- Handles multi-modal formats

**Integration Point:** `rag.document_processor` attribute

### Retriever
Uses `Retriever` from `src/core/rag/retriever.py`:
- Converts queries to embeddings
- Performs vector similarity search
- Re-ranks results

**Integration Point:** `rag.retriever` attribute

### Generator
Uses `RAGGenerator` from `src/core/rag/generator.py`:
- Generates responses using retrieved context
- Handles prompt construction
- Manages response formatting

**Integration Point:** `rag.generator` attribute

### Cache Mechanism
Uses `CacheMechanism` from `src/core/cache_mechanism/`:
- Caches query results
- Caches embeddings
- Improves performance

**Integration Point:** `rag.cache` attribute

### Agent Memory
Uses `AgentMemory` from `src/core/agno_agent_framework/memory.py`:
- Stores conversation context
- Enables multi-turn interactions
- Maintains query history

**Integration Point:** `rag.memory` attribute

### Where Used
- **RAG Functions** (`src/core/rag/functions.py`): Factory functions create RAGSystem instances
- **FaaS RAG Service** (`src/faas/services/rag_service/`): REST API wrapper for RAG
- **API Backend Services** (`src/core/api_backend_services/`): HTTP endpoints for RAG
- **Examples**: All RAG examples use this class

## Best Practices

### 1. Use Async Methods
Always prefer async methods for production:
```python
# Good: Async for better performance
doc_id = await rag.ingest_document_async("Title", content="...")
result = await rag.query_async("query")

# Bad: Synchronous blocks event loop
doc_id = rag.ingest_document("Title", content="...")
result = rag.query("query")
```

### 2. Configure Chunking
Set appropriate chunking parameters:
```python
# Good: Configured chunking
rag = RAGSystem(
    db=db,
    gateway=gateway,
    chunk_size=1000,
    chunk_overlap=200,
    chunking_strategy="sentence"  # Better for semantic search
)

# Bad: Default chunking may not be optimal
rag = RAGSystem(db=db, gateway=gateway)
```

### 3. Use Tenant IDs
Always provide tenant_id for multi-tenant applications:
```python
# Good: Tenant-scoped operations
doc_id = await rag.ingest_document_async(
    "Title", content="...", tenant_id="tenant_123"
)
result = await rag.query_async("query", tenant_id="tenant_123")

# Bad: Missing tenant_id in multi-tenant system
doc_id = await rag.ingest_document_async("Title", content="...")
```

### 4. Enable Memory for Conversations
Enable memory for multi-turn interactions:
```python
# Good: Memory enabled
rag = RAGSystem(
    db=db,
    gateway=gateway,
    enable_memory=True,
    memory_config={"max_episodic": 100}
)

# Bad: No memory (loses conversation context)
rag = RAGSystem(db=db, gateway=gateway, enable_memory=False)
```

### 5. Use Re-ranking
Enable re-ranking for better results:
```python
# Good: Re-ranking enabled
result = await rag.query_async(
    "query",
    top_k=10,
    rerank=True,
    min_score=0.7
)

# Bad: No re-ranking (may return less relevant results)
result = await rag.query_async("query", top_k=5)
```

### 6. Handle Errors
Always handle errors appropriately:
```python
# Good: Error handling
try:
    result = await rag.query_async("query")
except Exception as e:
    logger.error(f"Query failed: {e}")
    # Handle error

# Bad: No error handling
result = await rag.query_async("query")  # May crash
```

### 7. Monitor Performance
Monitor query performance and adjust top_k:
```python
# Good: Appropriate top_k
result = await rag.query_async("query", top_k=5)  # Balance speed/quality

# Bad: Too many or too few
result = await rag.query_async("query", top_k=100)  # Too slow
result = await rag.query_async("query", top_k=1)  # May miss relevant docs
```

### 8. Use Caching
Enable caching for repeated queries:
```python
# Good: Caching enabled
rag = RAGSystem(
    db=db,
    gateway=gateway,
    cache=CacheMechanism(CacheConfig(backend="dragonfly"))
)

# Bad: No caching (higher costs, slower)
rag = RAGSystem(db=db, gateway=gateway)
```

### 9. Document Metadata
Always provide meaningful metadata:
```python
# Good: Rich metadata
doc_id = await rag.ingest_document_async(
    "Title",
    content="...",
    metadata={
        "category": "technology",
        "author": "John Doe",
        "date": "2024-01-01",
        "tags": ["AI", "ML"]
    }
)

# Bad: No metadata (harder to filter/manage)
doc_id = await rag.ingest_document_async("Title", content="...")
```

### 10. Incremental Updates
Use update instead of re-ingesting:
```python
# Good: Update existing document
rag.update_document(
    document_id=doc_id,
    content="Updated content..."
)

# Bad: Delete and re-ingest (loses history)
rag.delete_document(doc_id)
rag.ingest_document("Title", content="Updated content...")
```

## Additional Resources

### Documentation
- **[RAG README](README.md)** - Complete RAG system guide
- **[RAG Functions Documentation](functions.md)** - Factory and convenience functions
- **[RAG Troubleshooting](../../../docs/troubleshooting/rag_troubleshooting.md)** - Common issues

### Related Components
- **[Document Processor](document_processor.py)** - Document processing
- **[Retriever](retriever.py)** - Document retrieval
- **[Generator](generator.py)** - Response generation
- **[Vector Operations](../../postgresql_database/vector_operations.py)** - Vector database operations

### External Resources
- **[RAG Paper](https://arxiv.org/abs/2005.11401)** - Original RAG research paper
- **[Vector Similarity Search](https://www.pinecone.io/learn/vector-similarity-search/)** - Vector search guide
- **[PostgreSQL pgvector](https://github.com/pgvector/pgvector)** - pgvector documentation

### Examples
- **[Basic RAG Example](../../../../examples/basic_usage/07_rag_basic.py)** - Simple RAG usage
- **[RAG with Multi-Modal Example](../../../../examples/)** - Multi-modal document processing
- **[RAG with Memory Example](../../../../examples/)** - Conversation memory

