# Getting Started with RAG System

## Overview

The RAG (Retrieval-Augmented Generation) System enables context-aware AI responses by combining document retrieval with LLM generation. This guide explains the complete workflow from document ingestion to query processing.

## Entry Point

The primary entry point for creating RAG systems is through factory functions:

```python
from src.core.rag import create_rag_system, quick_rag_query, ingest_document_simple
from src.core.postgresql_database import DatabaseConnection
from src.core.litellm_gateway import create_gateway
```

## Input Requirements

### Required Inputs

1. **Database Connection**: PostgreSQL database with pgvector extension
   ```python
   from src.core.postgresql_database import DatabaseConnection, DatabaseConfig

   config = DatabaseConfig(
       host="localhost",
       port=5432,
       database="mydb",
       user="postgres",
       password="password"
   )
   db = DatabaseConnection(config)
   ```

2. **Gateway Instance**: LiteLLM Gateway for embeddings and generation
   ```python
   gateway = create_gateway(
       api_key="your-api-key",
       provider="openai"
   )
   ```

### Optional Inputs

- `embedding_model`: Model for generating embeddings (default: "text-embedding-3-small")
- `generation_model`: Model for text generation (default: "gpt-4")
- `cache`: Cache mechanism instance for caching results
- `chunk_size`: Document chunk size (default: 1000)
- `chunk_overlap`: Overlap between chunks (default: 200)
- `enable_memory`: Enable conversation memory integration (default: True)
- `memory_config`: Configuration for AgentMemory (episodic, semantic, long-term memory)

## Process Flow

### Step 1: RAG System Creation

**What Happens:**
1. RAG system validates database connection
2. Initializes vector operations for similarity search
3. Sets up document processor for chunking
4. Configures retriever for document retrieval
5. Initializes generator for response generation
6. Sets up cache mechanism (if provided)

**Code:**
```python
rag = create_rag_system(
    db=db,
    gateway=gateway,
    embedding_model="text-embedding-3-small",
    generation_model="gpt-4",
    enable_memory=True,  # Enable conversation context
    memory_config={
        "max_episodic": 100,  # Store last 100 queries
        "max_semantic": 200,  # Store 200 semantic patterns
        "max_age_days": 30    # Auto-cleanup after 30 days
    }
)
```

**Internal Process:**
```
create_rag_system()
  ├─> Validate database connection
  ├─> Initialize VectorOperations
  ├─> Initialize DocumentProcessor
  ├─> Initialize Retriever
  ├─> Initialize RAGGenerator
  ├─> Set up cache (if provided)
  ├─> Initialize AgentMemory (if enable_memory=True)
  └─> Return RAGSystem instance
```

### Step 2: Document Ingestion

**What Happens:**
1. Document is inserted into database
2. Document is processed and chunked
3. Embeddings are generated for each chunk
4. Chunks and embeddings are stored in database
5. Metadata is extracted and stored

**Code:**
```python
doc_id = ingest_document_simple(
    rag,
    title="AI Guide",
    content="Artificial Intelligence (AI) is the simulation of human intelligence...",
    source="https://example.com/ai-guide",
    metadata={"category": "technology", "author": "John Doe"},
    tenant_id="tenant_123"
)
```

**Input:**
- `rag`: RAG system instance
- `title`: Document title
- `content`: Document content (text)
- `source`: Optional source URL/path
- `metadata`: Optional metadata dictionary
- `tenant_id`: Optional tenant ID for multi-tenancy

**Internal Process:**
```
ingest_document()
  ├─> Insert document into database
  │   └─> Store title, content, metadata, tenant_id
  ├─> Process document
  │   ├─> Preprocess text (normalize, clean)
  │   ├─> Chunk document (fixed/sentence/paragraph/semantic)
  │   └─> Extract metadata
  ├─> Generate embeddings
  │   ├─> For each chunk:
  │   │   ├─> Call gateway.embed_async()
  │   │   └─> Get embedding vector
  ├─> Store chunks and embeddings
  │   ├─> Insert chunks into database
  │   └─> Store embeddings in vector table
  └─> Return document ID
```

### Step 3: Query Processing

**What Happens:**
1. Query is received
2. Query embedding is generated
3. Similar documents are retrieved using vector search
4. Retrieved chunks are ranked and filtered
5. Context is assembled from top chunks
6. Final response is generated using LLM
7. Response is returned with sources

**Code:**
```python
result = quick_rag_query(
    rag,
    query="What is artificial intelligence?",
    top_k=5,
    threshold=0.7,
    tenant_id="tenant_123",
    user_id="user_456",  # For memory context
    conversation_id="conv_789"  # For conversation history
)
```

**Input:**
- `rag`: RAG system instance
- `query`: User query/question
- `top_k`: Number of top chunks to retrieve (default: 5)
- `threshold`: Minimum similarity threshold (default: 0.7)
- `tenant_id`: Optional tenant ID for multi-tenancy
- `user_id`: Optional user ID for memory context (if memory enabled)
- `conversation_id`: Optional conversation ID for conversation history (if memory enabled)

**Internal Process:**
```
query()
  ├─> Retrieve conversation memory (if enable_memory=True)
  │   ├─> Get relevant episodic memories
  │   ├─> Get relevant semantic memories
  │   └─> Build conversation context
  ├─> Generate query embedding
  │   └─> Call gateway.embed_async(query)
  ├─> Vector similarity search
  │   ├─> Query vector database
  │   ├─> Find similar chunks (cosine similarity)
  │   └─> Filter by threshold
  ├─> Re-rank results (if enabled)
  │   ├─> Calculate relevance scores
  │   └─> Sort by relevance
  ├─> Assemble context
  │   ├─> Combine top chunks
  │   ├─> Add conversation context (from memory)
  │   ├─> Add metadata
  │   └─> Format for LLM
  ├─> Generate response
  │   ├─> Build prompt with context + memory
  │   ├─> Call gateway.generate_async()
  │   └─> Get generated text
  ├─> Store query-answer pair in memory (if enable_memory=True)
  │   └─> Store in episodic memory
  └─> Return result with sources
```

## Output

### Document Ingestion Output

```python
{
    "document_id": "doc_123",
    "status": "success",
    "chunks_created": 5,
    "embeddings_generated": 5
}
```

### Query Output Structure

```python
{
    "answer": "Artificial Intelligence (AI) is the simulation of human intelligence...",
    "sources": [
        {
            "document_id": "doc_123",
            "chunk_id": "chunk_456",
            "title": "AI Guide",
            "content": "Artificial Intelligence (AI) is...",
            "similarity": 0.92,
            "metadata": {"category": "technology"}
        },
        ...
    ],
    "metadata": {
        "query": "What is artificial intelligence?",
        "top_k": 5,
        "chunks_retrieved": 5,
        "generation_model": "gpt-4",
        "tokens_used": 250
    }
}
```

### Output Fields

- **`answer`**: Generated response text from LLM
- **`sources`**: List of source chunks used
  - `document_id`: Source document ID
  - `chunk_id`: Chunk ID
  - `title`: Document title
  - `content`: Chunk content
  - `similarity`: Similarity score (0-1)
  - `metadata`: Chunk metadata
- **`metadata`**: Query metadata
  - `query`: Original query
  - `top_k`: Number of chunks retrieved
  - `chunks_retrieved`: Actual number of chunks
  - `generation_model`: Model used for generation
  - `tokens_used`: Total tokens used

## Where Output is Used

### 1. Direct Usage

```python
result = quick_rag_query(rag, "What is AI?")
print(result["answer"])
for source in result["sources"]:
    print(f"Source: {source['title']} (similarity: {source['similarity']})")
```

### 2. Integration with Agent Framework

```python
# Agent uses RAG for context-aware responses
agent = create_agent(agent_id="agent_001", gateway=gateway, ...)

# Agent can query RAG before responding
rag_result = rag.query("What is AI?", tenant_id="tenant_123")
agent_task = agent.add_task(
    task_type="llm_query",
    parameters={
        "prompt": f"Based on this context: {rag_result['answer']}, provide more details..."
    }
)
```

### 3. Integration with API Backend

```python
# API exposes RAG functionality
@app.post("/api/rag/query")
async def rag_query_api(request: RAGQueryRequest):
    result = quick_rag_query(
        rag,
        query=request.query,
        top_k=request.top_k,
        tenant_id=request.tenant_id
    )
    return {
        "answer": result["answer"],
        "sources": result["sources"]
    }
```

### 4. Integration with Cache

```python
# RAG automatically caches query results
# Identical queries return cached results
result1 = quick_rag_query(rag, "What is AI?")  # Generates response
result2 = quick_rag_query(rag, "What is AI?")  # Returns cached result
```

### 5. Document Management

```python
# Update document
rag.update_document(
    document_id="doc_123",
    content="Updated content...",
    tenant_id="tenant_123"
)

# Delete document
rag.delete_document(
    document_id="doc_123",
    tenant_id="tenant_123"
)
```

## Complete Example

```python
import os
from src.core.rag import create_rag_system, quick_rag_query, ingest_document_simple
from src.core.postgresql_database import DatabaseConnection, DatabaseConfig
from src.core.litellm_gateway import create_gateway

# Step 1: Initialize Dependencies (Entry Point)
db_config = DatabaseConfig(
    host="localhost",
    port=5432,
    database="mydb",
    user="postgres",
    password="password"
)
db = DatabaseConnection(db_config)

gateway = create_gateway(
    api_key=os.getenv("OPENAI_API_KEY"),
    provider="openai"
)

# Step 2: Create RAG System (Entry Point)
rag = create_rag_system(
    db=db,
    gateway=gateway,
    embedding_model="text-embedding-3-small",
    generation_model="gpt-4"
)

# Step 3: Ingest Documents (Input)
doc_id = ingest_document_simple(
    rag,
    title="Artificial Intelligence Guide",
    content="""
    Artificial Intelligence (AI) is the simulation of human intelligence
    by machines. It includes learning, reasoning, and self-correction.
    Machine Learning is a subset of AI that enables systems to learn
    from data without explicit programming.
    """,
    source="https://example.com/ai-guide",
    metadata={"category": "technology", "author": "John Doe"},
    tenant_id="tenant_123"
)

print(f"Document ingested: {doc_id}")

# Step 4: Query RAG System (Process)
result = quick_rag_query(
    rag,
    query="What is artificial intelligence?",
    top_k=5,
    threshold=0.7,
    tenant_id="tenant_123"
)

# Step 5: Process Output
answer = result["answer"]
sources = result["sources"]

print(f"Answer: {answer}")
print(f"\nSources ({len(sources)}):")
for source in sources:
    print(f"  - {source['title']} (similarity: {source['similarity']:.2f})")

# Step 6: Use Output
# Use answer and sources in your application
return {
    "response": answer,
    "source_count": len(sources),
    "sources": sources
}
```

## Important Information

### Document Chunking Strategies

```python
from src.core.rag import create_document_processor

# Fixed chunking (default)
processor = create_document_processor(
    chunk_size=1000,
    chunk_overlap=200,
    chunking_strategy="fixed"
)

# Sentence-based chunking
processor = create_document_processor(
    chunking_strategy="sentence",
    min_chunk_size=50
)

# Paragraph-based chunking
processor = create_document_processor(
    chunking_strategy="paragraph"
)

# Semantic chunking (requires additional processing)
processor = create_document_processor(
    chunking_strategy="semantic"
)
```

### Advanced Retrieval

```python
# Custom retrieval with re-ranking
from src.core.rag.retriever import Retriever

retriever = Retriever(
    vector_ops=rag.vector_ops,
    gateway=rag.gateway,
    embedding_model="text-embedding-3-small"
)

# Retrieve with custom parameters
chunks = retriever.retrieve(
    query="What is AI?",
    top_k=10,
    threshold=0.6,
    enable_reranking=True,
    tenant_id="tenant_123"
)
```

### Incremental Updates

```python
# Update document incrementally
rag.update_document(
    document_id="doc_123",
    content="Updated content...",
    tenant_id="tenant_123"
)

# Only changed chunks are re-embedded
# Existing chunks are preserved
```

### Real-time Synchronization

```python
# Enable real-time document sync
rag.enable_realtime_sync()

# Documents are automatically synced when updated
# Queries always use latest content
```

### Error Handling

```python
try:
    result = quick_rag_query(rag, "What is AI?")
except RAGError as e:
    print(f"RAG error: {e.message}")
    print(f"Error type: {e.error_type}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Multi-Tenancy

```python
# All operations support tenant isolation
# Documents are automatically filtered by tenant_id

# Ingest document for specific tenant
doc_id = ingest_document_simple(
    rag,
    title="Tenant-specific document",
    content="...",
    tenant_id="tenant_123"
)

# Query only returns documents for that tenant
result = quick_rag_query(
    rag,
    query="What is AI?",
    tenant_id="tenant_123"  # Only searches tenant_123 documents
)
```

## Next Steps

- See [README.md](README.md) for detailed component documentation
- Check [component_explanation/rag_system_explanation.md](../../../component_explanation/rag_system_explanation.md) for comprehensive guide
- Review [troubleshooting guide](../../../docs/troubleshooting/rag_system_troubleshooting.md) for common issues
- Explore [examples/basic_usage/06_rag_basic.py](../../../examples/basic_usage/06_rag_basic.py) for more examples

