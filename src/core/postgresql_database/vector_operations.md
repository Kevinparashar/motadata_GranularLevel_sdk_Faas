# Vector Operations Documentation

## Overview

The `vector_operations.py` file contains the core `VectorOperations` class implementation, which provides vector database operations for storing, retrieving, and searching vector embeddings using PostgreSQL with the pgvector extension. This class enables efficient similarity search for RAG systems and other vector-based applications.

**Primary Functionality:**
- Vector embedding storage
- Similarity search (cosine, L2, inner product)
- Batch vector operations
- Vector index management
- Metadata storage and retrieval
- Tenant-scoped vector operations

## Code Explanation

### Class Structure

#### `VectorOperations` (Class)
Main vector operations class.

**Core Attributes:**
- `db`: Database connection instance
- `table_name`: Table name for embeddings (default: "embeddings")
- `dimension`: Vector dimension

### Key Methods

#### `insert_embedding(document_id, embedding, model, metadata=None, tenant_id=None) -> None`
Inserts a single embedding.

**Parameters:**
- `document_id`: Document ID
- `embedding`: Embedding vector
- `model`: Model used for embedding
- `metadata`: Optional metadata
- `tenant_id`: Optional tenant ID

#### `batch_insert_embeddings(embeddings_data) -> None`
Batch inserts multiple embeddings.

**Parameters:**
- `embeddings_data`: List of tuples (document_id, embedding, model, metadata)

**Returns:** None

#### `search_similar(query_embedding, top_k=5, threshold=0.0, tenant_id=None) -> List[Dict[str, Any]]`
Searches for similar vectors.

**Parameters:**
- `query_embedding`: Query embedding vector
- `top_k`: Number of results to return
- `threshold`: Similarity threshold
- `tenant_id`: Optional tenant ID

**Returns:** List of similar documents with scores

#### `get_embedding(document_id, tenant_id=None) -> Optional[List[float]]`
Retrieves embedding for a document.

**Parameters:**
- `document_id`: Document ID
- `tenant_id`: Optional tenant ID

**Returns:** Embedding vector or None

#### `delete_embedding(document_id, tenant_id=None) -> bool`
Deletes embedding for a document.

**Parameters:**
- `document_id`: Document ID
- `tenant_id`: Optional tenant ID

**Returns:** Boolean indicating success

## Usage Instructions

### Basic Vector Operations

```python
from src.core.postgresql_database import DatabaseConnection, VectorOperations

# Create database connection
db = DatabaseConnection("postgresql://user:pass@localhost/db")
db.connect()

# Create vector operations
vector_ops = VectorOperations(db)

# Insert embedding
vector_ops.insert_embedding(
    document_id="doc_123",
    embedding=[0.1, 0.2, 0.3, ...],  # 1536-dimensional vector
    model="text-embedding-3-small",
    tenant_id="tenant_123"
)

# Search similar
results = vector_ops.search_similar(
    query_embedding=[0.1, 0.2, 0.3, ...],
    top_k=5,
    tenant_id="tenant_123"
)
```

### Batch Operations

```python
# Batch insert
embeddings_data = [
    ("doc_1", [0.1, 0.2, ...], "model1"),
    ("doc_2", [0.3, 0.4, ...], "model1"),
    ("doc_3", [0.5, 0.6, ...], "model1")
]
vector_ops.batch_insert_embeddings(embeddings_data)
```

### Similarity Search

```python
# Search with threshold
results = vector_ops.search_similar(
    query_embedding=query_vector,
    top_k=10,
    threshold=0.7,  # Minimum similarity score
    tenant_id="tenant_123"
)

for result in results:
    print(f"Document: {result['document_id']}, Score: {result['score']}")
```

### Prerequisites

1. **Python 3.10+**: Required for type hints
2. **Dependencies**: Install via `pip install -r requirements.txt`
   - `psycopg2`: PostgreSQL adapter
   - `pgvector`: Vector extension
3. **PostgreSQL**: With pgvector extension installed
4. **Vector Index**: Create vector index for performance

## Connection to Other Components

### Database Connection
Uses `DatabaseConnection` from `src/core/postgresql_database/connection.py`:
- Provides database connection
- Enables SQL operations

**Integration Point:** `vector_ops.db` attribute

### RAG System
Used by `RAGSystem` from `src/core/rag/rag_system.py`:
- Stores document embeddings
- Performs similarity search
- Enables document retrieval

**Integration Point:** `rag.vector_ops` attribute

### Vector Index Manager
Works with `VectorIndexManager` from `src/core/postgresql_database/vector_index_manager.py`:
- Creates indexes for performance
- Manages index lifecycle

**Integration Point:** RAG system uses both together

### Where Used
- **RAG System**: For document retrieval
- **Examples**: All vector search examples

## Best Practices

### 1. Use Batch Operations
Always use batch operations for multiple embeddings:
```python
# Good: Batch insert
vector_ops.batch_insert_embeddings(embeddings_data)

# Bad: Sequential insert
for embedding in embeddings:
    vector_ops.insert_embedding(...)
```

### 2. Create Indexes
Always create vector indexes for performance:
```python
# Good: Index created
from src.core.postgresql_database import create_vector_index_manager
index_manager = create_vector_index_manager(db)
index_manager.create_index("embeddings", "embedding", index_type="ivfflat")

# Bad: No index (slow searches)
```

### 3. Use Tenant IDs
Always provide tenant_id for multi-tenant applications:
```python
# Good: Tenant-scoped
vector_ops.search_similar(query_vector, tenant_id="tenant_123")

# Bad: Missing tenant_id
vector_ops.search_similar(query_vector)
```

### 4. Set Appropriate Thresholds
Set similarity thresholds based on use case:
```python
# Good: Appropriate threshold
results = vector_ops.search_similar(
    query_vector,
    threshold=0.7  # Filter low-quality matches
)

# Bad: Too low or too high
results = vector_ops.search_similar(query_vector, threshold=0.0)  # Too low
results = vector_ops.search_similar(query_vector, threshold=0.99)  # Too high
```

## Additional Resources

### Documentation
- **[PostgreSQL Database README](README.md)** - Complete database guide
- **[Vector Index Manager Documentation](vector_index_manager.md)** - Index management
- **[RAG System Documentation](../../rag/README.md)** - RAG usage

### Related Components
- **[Database Connection](connection.py)** - Database connection
- **[Vector Index Manager](vector_index_manager.py)** - Index management

### External Resources
- **[pgvector Documentation](https://github.com/pgvector/pgvector)** - Vector extension
- **[Vector Similarity Search](https://www.pinecone.io/learn/vector-similarity-search/)** - Search guide

### Examples
- **[Vector Operations Example](../../../../examples/)** - Vector search examples

