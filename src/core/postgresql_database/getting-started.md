# Getting Started with PostgreSQL Database

## Overview

The PostgreSQL Database component provides database connectivity and vector operations using pgvector for similarity search. This guide explains the complete workflow from connection setup to vector operations.

## Entry Point

The primary entry point for database operations:

```python
from src.core.postgresql_database import DatabaseConnection, DatabaseConfig
from src.core.postgresql_database.vector_operations import VectorOperations
```

## Input Requirements

### Required Inputs

1. **Database Configuration**:
   - `host`: Database host
   - `port`: Database port (default: 5432)
   - `database`: Database name
   - `user`: Database user
   - `password`: Database password

### Optional Inputs

- `pool_size`: Connection pool size
- `max_overflow`: Maximum overflow connections
- `pool_timeout`: Pool timeout in seconds

## Process Flow

### Step 1: Database Connection Creation

**What Happens:**
1. Configuration is validated
2. Connection pool is created
3. Database connection is tested
4. pgvector extension is verified

**Code:**
```python
config = DatabaseConfig(
    host="localhost",
    port=5432,
    database="mydb",
    user="postgres",
    password="password",
    pool_size=10
)

db = DatabaseConnection(config)
```

**Internal Process:**
```
DatabaseConnection.__init__()
  ├─> Validate configuration
  ├─> Create connection pool
  ├─> Test connection
  ├─> Verify pgvector extension
  └─> Return connection instance
```

### Step 2: Query Execution

**What Happens:**
1. Query is prepared
2. Connection is acquired from pool
3. Query is executed
4. Results are fetched
5. Connection is returned to pool

**Code:**
```python
# Execute query
result = db.execute_query(
    "SELECT * FROM documents WHERE tenant_id = %s",
    params=("tenant_123",),
    fetch_one=False
)

for row in result:
    print(row)
```

**Input:**
- `query`: SQL query string
- `params`: Query parameters (tuple or dict)
- `fetch_one`: Whether to fetch one row or all rows
- `tenant_id`: Optional tenant ID for multi-tenancy

**Internal Process:**
```
execute_query()
  ├─> Acquire connection from pool
  ├─> Prepare query
  ├─> Execute query
  ├─> Fetch results
  ├─> Return connection to pool
  └─> Return results
```

### Step 3: Vector Operations

**What Happens:**
1. Vector operations instance is created
2. Embeddings are stored in vector table
3. Similarity search is performed
4. Results are ranked by similarity

**Code:**
```python
vector_ops = VectorOperations(db)

# Store embedding
vector_ops.store_embedding(
    table_name="document_embeddings",
    document_id="doc_123",
    embedding=[0.1, 0.2, 0.3, ...],
    metadata={"title": "AI Guide"},
    tenant_id="tenant_123"
)

# Similarity search
results = vector_ops.similarity_search(
    query_vector=[0.1, 0.2, 0.3, ...],
    table_name="document_embeddings",
    limit=5,
    threshold=0.7,
    tenant_id="tenant_123"
)
```

**Input:**
- `table_name`: Vector table name
- `query_vector`: Query embedding vector
- `limit`: Maximum results to return
- `threshold`: Minimum similarity threshold
- `tenant_id`: Optional tenant ID

**Internal Process:**
```
similarity_search()
  ├─> Validate vector dimensions
  ├─> Build similarity query (cosine distance)
  ├─> Execute query with pgvector
  ├─> Filter by threshold
  ├─> Sort by similarity
  ├─> Limit results
  └─> Return ranked results
```

## Output

### Query Execution Output

```python
# Single row
row = db.execute_query(
    "SELECT * FROM documents WHERE id = %s",
    params=("doc_123",),
    fetch_one=True
)
# Result: {"id": "doc_123", "title": "AI Guide", "content": "..."}

# Multiple rows
rows = db.execute_query(
    "SELECT * FROM documents WHERE tenant_id = %s",
    params=("tenant_123",),
    fetch_one=False
)
# Result: [{"id": "doc_123", ...}, {"id": "doc_456", ...}]
```

### Vector Search Output

```python
[
    {
        "document_id": "doc_123",
        "similarity": 0.92,
        "metadata": {"title": "AI Guide"},
        "embedding": [0.1, 0.2, 0.3, ...]
    },
    {
        "document_id": "doc_456",
        "similarity": 0.85,
        "metadata": {"title": "ML Guide"},
        "embedding": [0.2, 0.3, 0.4, ...]
    }
]
```

## Where Output is Used

### 1. Direct Usage

```python
# Query documents
documents = db.execute_query(
    "SELECT * FROM documents WHERE tenant_id = %s",
    params=("tenant_123",)
)

for doc in documents:
    print(f"Title: {doc['title']}")
```

### 2. Integration with RAG System

```python
# RAG uses database for document storage and vector search
rag = create_rag_system(db=db, gateway=gateway, ...)

# RAG automatically uses vector operations for retrieval
result = rag.query("What is AI?")
# Internally uses vector_ops.similarity_search()
```

### 3. Integration with ML Components

```python
# ML components use database for model storage
from src.core.machine_learning.ml_framework import create_ml_system

ml_system = create_ml_system(db=db, ...)
# Models and metadata stored in database
```

### 4. Transaction Management

```python
# Use transactions for atomic operations
with db.transaction():
    db.execute_query("INSERT INTO documents ...")
    db.execute_query("INSERT INTO embeddings ...")
    # Both succeed or both fail
```

## Complete Example

```python
from src.core.postgresql_database import DatabaseConnection, DatabaseConfig
from src.core.postgresql_database.vector_operations import VectorOperations
import numpy as np

# Step 1: Create Database Connection (Entry Point)
config = DatabaseConfig(
    host="localhost",
    port=5432,
    database="mydb",
    user="postgres",
    password="password",
    pool_size=10
)

db = DatabaseConnection(config)

# Step 2: Execute Queries (Input)
# Create table (if not exists)
db.execute_query("""
    CREATE TABLE IF NOT EXISTS documents (
        id SERIAL PRIMARY KEY,
        title TEXT,
        content TEXT,
        tenant_id TEXT
    )
""")

# Insert document
db.execute_query(
    "INSERT INTO documents (title, content, tenant_id) VALUES (%s, %s, %s)",
    params=("AI Guide", "Content about AI...", "tenant_123")
)

# Step 3: Vector Operations (Process)
vector_ops = VectorOperations(db)

# Create vector table
vector_ops.create_vector_table(
    table_name="document_embeddings",
    dimension=1536  # OpenAI embedding dimension
)

# Generate embedding (example)
embedding = np.random.rand(1536).tolist()  # In practice, use gateway.embed()

# Store embedding
vector_ops.store_embedding(
    table_name="document_embeddings",
    document_id="doc_123",
    embedding=embedding,
    metadata={"title": "AI Guide"},
    tenant_id="tenant_123"
)

# Step 4: Similarity Search (Process)
query_embedding = np.random.rand(1536).tolist()  # In practice, use gateway.embed()

results = vector_ops.similarity_search(
    query_vector=query_embedding,
    table_name="document_embeddings",
    limit=5,
    threshold=0.7,
    tenant_id="tenant_123"
)

# Step 5: Use Output
for result in results:
    print(f"Document ID: {result['document_id']}")
    print(f"Similarity: {result['similarity']:.2f}")
    print(f"Metadata: {result['metadata']}")
```

## Important Information

### Connection Pooling

```python
# Configure connection pool
config = DatabaseConfig(
    pool_size=10,        # Base pool size
    max_overflow=5,      # Additional connections
    pool_timeout=30.0     # Timeout for getting connection
)

db = DatabaseConnection(config)
# Connections are automatically managed
```

### Multi-Tenancy

```python
# All queries support tenant isolation
# Use tenant_id parameter or filter in WHERE clause

# Option 1: Use tenant_id parameter
db.execute_query(
    "SELECT * FROM documents WHERE tenant_id = %s",
    params=("tenant_123",)
)

# Option 2: Filter in query
db.execute_query(
    "SELECT * FROM documents WHERE tenant_id = 'tenant_123'"
)
```

### Vector Table Setup

```python
# Create vector table with pgvector
vector_ops.create_vector_table(
    table_name="embeddings",
    dimension=1536,  # Must match embedding dimension
    index_type="ivfflat"  # or "hnsw"
)

# Table structure:
# - id: SERIAL PRIMARY KEY
# - document_id: TEXT
# - embedding: vector(dimension)
# - metadata: JSONB
# - tenant_id: TEXT
```

### Error Handling

```python
try:
    result = db.execute_query("SELECT * FROM documents")
except DatabaseError as e:
    print(f"Database error: {e.message}")
    print(f"Error code: {e.error_code}")
except ConnectionError as e:
    print(f"Connection error: {e.message}")
    # Retry or use fallback
```

### Health Check

```python
# Check database health
health = db.get_health()
print(f"Status: {health['status']}")
print(f"Pool size: {health['pool_size']}")
print(f"Active connections: {health['active_connections']}")
```

## Next Steps

- See [README.md](README.md) for detailed component documentation
- Check [docs/components/postgresql_database_explanation.md](../../../docs/components/postgresql_database_explanation.md) for comprehensive guide
- Review [troubleshooting guide](../../../docs/troubleshooting/postgresql_database_troubleshooting.md) for common issues

