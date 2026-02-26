# MOTADATA - POSTGRESQL DATABASE

**Database connectivity and management with pgvector support for efficient vector similarity search operations.**

## Overview

The PostgreSQL Database component provides robust database connectivity and management for the entire SDK. It includes comprehensive support for the pgvector extension, enabling efficient vector similarity search operations that are essential for RAG (Retrieval-Augmented Generation) systems and embedding-based applications.

## Purpose and Functionality

This component serves as the primary data persistence layer for the SDK. It manages:
- **Document Storage**: Stores documents, metadata, and associated information
- **Vector Embeddings**: Stores and manages vector embeddings using pgvector
- **Connection Pooling**: Efficiently manages database connections through connection pooling
- **Query Execution**: Provides safe and efficient query execution with transaction support

The component abstracts database operations, providing a clean interface that other components can use without dealing with low-level database details.

## Connection to Other Components

### Integration with RAG System

The **RAG System** (`src/core/rag/`) is the primary consumer of this database component. The RAG system uses the database to:
1. **Store Documents**: When documents are ingested, they are stored in the database with their metadata
2. **Store Embeddings**: Vector embeddings generated for documents are stored using the pgvector extension
3. **Retrieve Documents**: The RAG retriever performs similarity searches using the database's vector operations
4. **Query Context**: Retrieved documents are fetched from the database to provide context for LLM generation

The database's `VectorOperations` class provides the similarity search functionality that the RAG system depends on.

### Integration with Pool Implementation

The **Pool Implementation** (root level) is used by the database component for connection management. The database connection manager uses connection pooling to efficiently reuse database connections, reducing overhead and improving performance. This integration ensures that database connections are properly managed and don't exhaust system resources.

### Integration with LiteLLM Gateway

The **LiteLLM Gateway** (`src/core/litellm_gateway/`) is used indirectly through the RAG system. When the RAG system needs to generate embeddings for documents, it uses the gateway, and those embeddings are then stored in this database. The gateway doesn't directly interact with the database, but the data flow connects them.

### Integration with Agno Agent Framework

The **Agno Agent Framework** (`src/core/agno_agent_framework/`) can use the database to:
- Store agent state and task history
- Persist agent communication logs
- Store task results and outcomes

This persistence enables agents to maintain context across sessions and provides audit trails for agent activities.

### Integration with Evaluation & Observability

The **Evaluation & Observability** component (`src/core/evaluation_observability/`) can store metrics, logs, and traces in the database. This enables long-term storage of observability data for analysis and reporting.

## Libraries Utilized

- **psycopg2-binary**: The PostgreSQL adapter for Python. It provides the low-level database connectivity and connection pooling capabilities. The binary version includes all necessary dependencies for easy deployment.
- **pgvector**: PostgreSQL extension for vector similarity search. It provides the `vector` data type and operators for efficient similarity calculations using cosine distance, L2 distance, or inner product.

## Key Components

### DatabaseConnection Class

The `DatabaseConnection` class manages database connectivity and provides:
- **Connection Pooling**: Creates and manages a pool of database connections
- **Query Execution**: Provides safe methods for executing queries with proper error handling
- **Transaction Management**: Supports transactions for atomic operations
- **Connection Health Checks**: Validates database connectivity
- **pgvector Extension Management**: Automatically verifies and optionally creates pgvector extension on connection

### VectorOperations Class

The `VectorOperations` class provides vector-specific operations:
- **Embedding Storage**: Stores vector embeddings in the database
- **Similarity Search**: Performs efficient similarity searches using pgvector operators
- **Batch Operations**: Supports batch insertion of embeddings for performance

## Vector Database Operations

The component leverages pgvector's capabilities for efficient vector operations:

- **Cosine Similarity**: Uses the `<=>` operator for cosine distance calculations
- **L2 Distance**: Supports Euclidean distance calculations
- **Indexing**: Can create indexes on vector columns for faster searches

The similarity search operations are optimized to return the most relevant documents based on embedding similarity, which is crucial for RAG system performance.

## Error Handling

The component implements comprehensive error handling:
- **Connection Errors**: Handles database connection failures with appropriate retry logic
- **Query Errors**: Catches and reports SQL errors with detailed information
- **Transaction Rollback**: Automatically rolls back transactions on errors
- **Connection Pool Exhaustion**: Handles cases where all connections are in use

## Configuration

The database is configured through the `DatabaseConfig` class, which supports:
- Database connection parameters (host, port, database name, credentials)
- Connection pool sizing (minimum and maximum connections)
- Connection timeout settings
- **pgvector Extension Management**: `auto_create_extension` option to automatically create pgvector extension on connection

**Example:**
```python
config = DatabaseConfig(
    host="localhost",
    port=5432,
    database="mydb",
    user="postgres",
    password="password",
    auto_create_extension=True  # Automatically create pgvector extension if missing
)
```

Configuration can be loaded from environment variables, enabling flexible deployment across different environments.

## Best Practices

1. **Connection Pooling**: Always use connection pooling to manage database connections efficiently
2. **Index Management**: Create appropriate indexes on vector columns for optimal search performance
3. **Transaction Boundaries**: Use transactions for operations that must be atomic
4. **Error Handling**: Implement proper error handling for all database operations
5. **Resource Cleanup**: Ensure database connections are properly closed to prevent resource leaks
6. **Vector Dimension Consistency**: Maintain consistent embedding dimensions across all stored vectors

---

## Database Initialization

### Quick Setup

For first-time setup, use the `setup_database()` function to initialize everything:

```python
from src.core.postgresql_database import DatabaseConnection, DatabaseConfig, setup_database

# Create database connection
config = DatabaseConfig(
    host="localhost",
    port=5432,
    database="mydb",
    user="postgres",
    password="password",
)
db = DatabaseConnection(config)
await db.connect()

# Initialize database with pgvector
results = await setup_database(db, config={
    "dimension": 1536,  # Embedding dimension
    "index_type": "ivfflat",  # or "hnsw"
    "create_extension": True,  # Create pgvector extension
    "create_tables": True,  # Create embeddings and documents tables
    "create_indexes": True,  # Create vector indexes
})

# Check results
if results.get("error"):
    print(f"Setup failed: {results.get('message')}")
else:
    print(f"Extension: {results['pgvector_extension']}")
    print(f"Tables: {results['embeddings_table']}, {results['documents_table']}")
    print(f"Indexes: {results['vector_indexes']}")
```

### Manual Setup

You can also set up components individually:

```python
from src.core.postgresql_database import (
    create_pgvector_extension,
    create_embeddings_table,
    create_documents_table,
    setup_vector_indexes,
    verify_setup,
)

# Step 1: Create pgvector extension
await create_pgvector_extension(db)

# Step 2: Create tables
await create_embeddings_table(db, dimension=1536)
await create_documents_table(db)

# Step 3: Create indexes (optional but recommended)
await setup_vector_indexes(db, index_type="ivfflat")

# Step 4: Verify setup
status = await verify_setup(db)
print(status)
```

### Verification

Check if your database is properly set up:

```python
from src.core.postgresql_database import verify_setup

status = await verify_setup(db)
# Returns:
# {
#     "connection": True,
#     "pgvector_extension": True,
#     "tables": {"embeddings": True, "documents": True},
#     "indexes": {"embeddings_embedding": True, "indexes_list": [...]}
# }
```

---

## Getting Started Guide

This section provides a complete step-by-step guide for getting started with the PostgreSQL Database, from connection setup to vector operations.

### Entry Point

The primary entry point for database operations:

```python
from src.core.postgresql_database import DatabaseConnection, DatabaseConfig
from src.core.postgresql_database.vector_operations import VectorOperations
```

### Input Requirements

#### Required Inputs

1. **Database Configuration**:
   - `host`: Database host
   - `port`: Database port (default: 5432)
   - `database`: Database name
   - `user`: Database user
   - `password`: Database password

#### Optional Inputs

- `pool_size`: Connection pool size
- `max_overflow`: Maximum overflow connections
- `pool_timeout`: Pool timeout in seconds

### Process Flow

#### Step 1: Database Connection Creation

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
db.connect()
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

#### Step 2: Query Execution

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
    parameters=("tenant_123",),
    tenant_id="tenant_123"
)

for row in result:
    print(row)
```

**Input:**
- `query`: SQL query string
- `parameters`: Query parameters (tuple or dict)
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

#### Step 3: Vector Operations

**What Happens:**
1. Vector operations instance is created
2. Embeddings are stored in vector table
3. Similarity search is performed
4. Results are ranked by similarity

**Code:**
```python
vector_ops = VectorOperations(db)

# Store embedding
vector_ops.insert_embedding(
    document_id="doc_123",
    embedding=[0.1, 0.2, 0.3, ...],
    model="text-embedding-ada-002",
    metadata={"title": "AI Guide"},
    tenant_id="tenant_123"
)

# Similarity search
results = vector_ops.search_similar(
    query_embedding=[0.1, 0.2, 0.3, ...],
    top_k=5,
    threshold=0.7,
    tenant_id="tenant_123"
)
```

**Input:**
- `document_id`: Document identifier
- `embedding`: Embedding vector
- `query_embedding`: Query embedding vector
- `top_k`: Maximum results to return
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

### Output

#### Query Execution Output

```python
# Single row
row = db.execute_query(
    "SELECT * FROM documents WHERE id = %s",
    parameters=("doc_123",),
    fetch_one=True
)
# Result: {"id": "doc_123", "title": "AI Guide", "content": "..."}

# Multiple rows
rows = db.execute_query(
    "SELECT * FROM documents WHERE tenant_id = %s",
    parameters=("tenant_123",),
    fetch_one=False
)
# Result: [{"id": "doc_123", ...}, {"id": "doc_456", ...}]
```

#### Vector Search Output

```python
[
    {
        "document_id": "doc_123",
        "score": 0.92,
        "metadata": {"title": "AI Guide"},
        "embedding": [0.1, 0.2, 0.3, ...]
    },
    {
        "document_id": "doc_456",
        "score": 0.85,
        "metadata": {"title": "ML Guide"},
        "embedding": [0.2, 0.3, 0.4, ...]
    }
]
```

### Complete Example

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
db.connect()

# Step 2: Execute Queries (Input)
# Create table (if not exists)
db.execute_update("""
    CREATE TABLE IF NOT EXISTS documents (
        id SERIAL PRIMARY KEY,
        title TEXT,
        content TEXT,
        tenant_id TEXT
    )
""")

# Insert document
db.execute_update(
    "INSERT INTO documents (title, content, tenant_id) VALUES (%s, %s, %s)",
    parameters=("AI Guide", "Content about AI...", "tenant_123")
)

# Step 3: Vector Operations (Process)
vector_ops = VectorOperations(db)

# Generate embedding (example - in practice, use gateway.embed())
embedding = np.random.rand(1536).tolist()

# Store embedding
vector_ops.insert_embedding(
    document_id="doc_123",
    embedding=embedding,
    model="text-embedding-ada-002",
    metadata={"title": "AI Guide"},
    tenant_id="tenant_123"
)

# Step 4: Similarity Search (Process)
query_embedding = np.random.rand(1536).tolist()  # In practice, use gateway.embed()

results = vector_ops.search_similar(
    query_embedding=query_embedding,
    top_k=5,
    threshold=0.7,
    tenant_id="tenant_123"
)

# Step 5: Use Output
for result in results:
    print(f"Document ID: {result['document_id']}")
    print(f"Score: {result['score']:.2f}")
    print(f"Metadata: {result.get('metadata', {})}")
```

### Important Information

#### Connection Pooling

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

#### Multi-Tenancy

```python
# All queries support tenant isolation
# Use tenant_id parameter or filter in WHERE clause

# Option 1: Use tenant_id parameter
db.execute_query(
    "SELECT * FROM documents WHERE tenant_id = %s",
    parameters=("tenant_123",),
    tenant_id="tenant_123"
)

# Option 2: Filter in query
db.execute_query(
    "SELECT * FROM documents WHERE tenant_id = 'tenant_123'"
)
```

#### Vector Table Setup

```python
# Vector operations automatically handle table creation
# Ensure pgvector extension is installed:
# CREATE EXTENSION IF NOT EXISTS vector;

# Vector operations use the embeddings table by default
# Table structure:
# - id: SERIAL PRIMARY KEY
# - document_id: TEXT
# - embedding: vector(dimension)
# - model: TEXT
# - metadata: JSONB
# - tenant_id: TEXT
```

#### Error Handling

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

#### Health Check

```python
# Check database health
health = db.check_health()
print(f"Status: {health['status']}")
print(f"Pool size: {health.get('pool_size', 'N/A')}")
print(f"Active connections: {health.get('active_connections', 'N/A')}")
```

---

## Detailed Class Documentation

This section provides comprehensive documentation for the database classes and related components.

### DatabaseConnection Class

The `DatabaseConnection` class provides robust PostgreSQL connectivity with connection pooling and health monitoring.

#### Core Attributes

- `connection_string`: PostgreSQL connection string
- `pool`: Connection pool instance
- `max_connections`: Maximum pool connections
- `min_connections`: Minimum pool connections
- `health_check`: Health monitoring instance

#### Key Methods

##### `async def connect() -> None`

Establishes database connection and creates connection pool.

**Process:**
1. Creates async connection pool
2. Validates connection
3. Verifies pgvector extension
4. Optionally creates pgvector extension if `auto_create_extension=True`
5. Sets up health monitoring

**Note:** The `connect()` method automatically verifies the pgvector extension. If the extension is missing and `auto_create_extension=True` in the config, it will attempt to create it automatically.

##### `execute_query(query, parameters=None, tenant_id=None) -> List[Dict[str, Any]]`

Executes a SELECT query.

**Parameters:**
- `query`: SQL query string
- `parameters`: Query parameters (for parameterized queries)
- `tenant_id`: Optional tenant ID for tenant-scoped queries

**Returns:** List of result dictionaries

**Example:**
```python
results = db.execute_query(
    "SELECT * FROM documents WHERE tenant_id = %s",
    parameters=(tenant_id,),
    tenant_id=tenant_id
)
```

##### `execute_update(query, parameters=None, tenant_id=None) -> int`

Executes an UPDATE, INSERT, or DELETE query.

**Parameters:**
- `query`: SQL query string
- `parameters`: Query parameters
- `tenant_id`: Optional tenant ID

**Returns:** Number of affected rows

##### `begin_transaction() -> None`

Begins a database transaction.

##### `commit_transaction() -> None`

Commits the current transaction.

##### `rollback_transaction() -> None`

Rolls back the current transaction.

##### `async def check_health() -> Dict[str, Any]`

Checks database connection health, including pgvector extension status.

**Returns:** Dictionary with health status including:
- `connection`: Boolean indicating connection status
- `database`: Database name
- `pgvector_extension`: Boolean indicating if pgvector extension is installed
- `error`: Optional error message if health check fails

**Example:**
```python
health = await db.health_check()
# Returns:
# {
#     "connection": True,
#     "database": "mydb",
#     "pgvector_extension": True
# }
```

##### `async def verify_pgvector_extension() -> bool`

Verifies if the pgvector extension is installed in the database.

**Returns:** `True` if extension exists, `False` otherwise

**Example:**
```python
if await db.verify_pgvector_extension():
    print("pgvector extension is installed")
else:
    print("pgvector extension not found")
```

##### `async def create_pgvector_extension() -> bool`

Creates the pgvector extension in the database.

**Returns:** `True` if extension was created successfully, `False` otherwise

**Raises:**
- `PostgresError`: If extension creation fails (e.g., insufficient permissions)

**Example:**
```python
if await db.create_pgvector_extension():
    print("pgvector extension created successfully")
else:
    print("Failed to create pgvector extension")
```

##### `close() -> None`

Closes database connections and pool.

#### Usage Examples

##### Basic Connection

```python
from src.core.postgresql_database import DatabaseConnection

# Create connection
db = DatabaseConnection(
    connection_string="postgresql://user:pass@localhost/dbname",
    max_connections=10,
    min_connections=2
)

# Connect
db.connect()

# Execute query
results = db.execute_query("SELECT * FROM users LIMIT 10")

# Close
db.close()
```

##### With Transactions

```python
# Begin transaction
db.begin_transaction()

try:
    # Execute updates
    db.execute_update("INSERT INTO users (name) VALUES (%s)", ("John",))
    db.execute_update("INSERT INTO users (name) VALUES (%s)", ("Jane",))
    
    # Commit
    db.commit_transaction()
except Exception as e:
    # Rollback on error
    db.rollback_transaction()
    raise
```

##### Tenant-Scoped Queries

```python
# Tenant-scoped query
results = db.execute_query(
    "SELECT * FROM documents WHERE tenant_id = %s",
    parameters=(tenant_id,),
    tenant_id=tenant_id
)
```

##### Health Monitoring

```python
# Check health (includes pgvector status)
health = await db.health_check()
if health.get("connection") and health.get("pgvector_extension"):
    print("Database is operational with pgvector support")
elif health.get("connection"):
    print("Database is operational but pgvector extension is missing")
else:
    print("Database connection failed")

# Verify pgvector extension
if await db.verify_pgvector_extension():
    print("pgvector extension is available")
else:
    # Create extension if needed
    if await db.create_pgvector_extension():
        print("pgvector extension created")
```

### VectorOperations Class

The `VectorOperations` class provides vector database operations for storing, retrieving, and searching embeddings.

#### Core Attributes

- `db`: Database connection instance
- `embedding_dal`: EmbeddingDAL instance for database operations (DAL-first architecture)
- `default_dimension`: Default embedding dimension for validation (default: 1536)
- `_verify_on_first_operation`: Flag to verify pgvector extension on first operation

**Note:** VectorOperations automatically verifies the pgvector extension on first use if `verify_extension=True` (default). It also validates embedding dimensions to ensure consistency.

#### Key Methods

##### `insert_embedding(document_id, embedding, model, metadata=None, tenant_id=None) -> None`

Inserts a single embedding.

**Parameters:**
- `document_id`: Document ID
- `embedding`: Embedding vector
- `model`: Model used for embedding
- `metadata`: Optional metadata
- `tenant_id`: Optional tenant ID

##### `batch_insert_embeddings(embeddings_data) -> None`

Batch inserts multiple embeddings.

**Parameters:**
- `embeddings_data`: List of tuples (document_id, embedding, model, metadata)

**Returns:** None

##### `search_similar(query_embedding, top_k=5, threshold=0.0, tenant_id=None) -> List[Dict[str, Any]]`

Searches for similar vectors.

**Parameters:**
- `query_embedding`: Query embedding vector
- `top_k`: Number of results to return
- `threshold`: Similarity threshold
- `tenant_id`: Optional tenant ID

**Returns:** List of similar documents with scores

##### `get_embedding(document_id, tenant_id=None) -> Optional[List[float]]`

Retrieves embedding for a document.

**Parameters:**
- `document_id`: Document ID
- `tenant_id`: Optional tenant ID

**Returns:** Embedding vector or None

##### `delete_embedding(document_id, tenant_id=None) -> bool`

Deletes embedding for a document.

**Parameters:**
- `document_id`: Document ID
- `tenant_id`: Optional tenant ID

**Returns:** Boolean indicating success

##### `async def health_check() -> Dict[str, Any]`

Performs health check for vector operations, including connection, pgvector extension, and EmbeddingDAL status.

**Returns:** Dictionary with health status:
- `connection`: Boolean indicating database connection status
- `pgvector_extension`: Boolean indicating if pgvector extension is available
- `embedding_dal`: Boolean indicating if EmbeddingDAL is initialized
- `error`: Optional error message if health check fails

**Example:**
```python
health = await vector_ops.health_check()
# Returns:
# {
#     "connection": True,
#     "pgvector_extension": True,
#     "embedding_dal": True
# }
```

#### Usage Examples

##### Basic Vector Operations

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

##### Batch Operations

```python
# Batch insert
embeddings_data = [
    ("doc_1", [0.1, 0.2, ...], "model1", {"title": "Doc 1"}),
    ("doc_2", [0.3, 0.4, ...], "model1", {"title": "Doc 2"}),
    ("doc_3", [0.5, 0.6, ...], "model1", {"title": "Doc 3"})
]
vector_ops.batch_insert_embeddings(embeddings_data)
```

##### Similarity Search

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

### VectorIndexManager

The Vector Index Manager helps you:

- Create vector indexes (for faster similarity search)
- Choose an index type (example: IVFFlat, HNSW)
- Reindex when needed
- Manage index configuration in a consistent way

**When you need this:**
- Similarity search becomes slow as data grows
- You change embedding dimension or model behaviour
- You want better latency in production

**Implementation:** `src/core/postgresql_database/vector_index_manager.py`

**Used by:** `src/core/rag/rag_system.py` and `src/core/postgresql_database/vector_operations.py`

---

## Best Practices

### 1. Use Connection Pooling

Always use connection pooling:
```python
# Good: Connection pooling
db = DatabaseConnection(
    connection_string="...",
    max_connections=10,
    min_connections=2
)

# Bad: Single connection (not scalable)
```

### 2. Use Transactions

Always use transactions for multiple operations:
```python
# Good: Transaction management
db.begin_transaction()
try:
    db.execute_update("INSERT ...")
    db.execute_update("UPDATE ...")
    db.commit_transaction()
except:
    db.rollback_transaction()

# Bad: No transaction (data inconsistency risk)
db.execute_update("INSERT ...")
db.execute_update("UPDATE ...")
```

### 3. Use Parameterized Queries

Always use parameterized queries to prevent SQL injection:
```python
# Good: Parameterized query
db.execute_query(
    "SELECT * FROM users WHERE id = %s",
    parameters=(user_id,)
)

# Bad: String formatting (SQL injection risk)
db.execute_query(f"SELECT * FROM users WHERE id = {user_id}")
```

### 4. Provide Tenant IDs

Always provide tenant_id for multi-tenant applications:
```python
# Good: Tenant-scoped
db.execute_query(
    "SELECT * FROM documents WHERE tenant_id = %s",
    parameters=(tenant_id,),
    tenant_id=tenant_id
)

# Bad: Missing tenant_id (no tenant isolation)
db.execute_query("SELECT * FROM documents")
```

### 5. Monitor Health

Regularly check database health:
```python
# Good: Health monitoring
health = db.check_health()
if health["status"] != "healthy":
    # Alert or handle unhealthy state
    logger.warning("Database unhealthy")

# Bad: No health monitoring
```

### 6. Close Connections

Always close connections when done:
```python
# Good: Proper cleanup
try:
    db.connect()
    # Use database
finally:
    db.close()

# Bad: Leaked connections
db.connect()
# No close() call
```

### 7. Use Batch Operations

Always use batch operations for multiple embeddings:
```python
# Good: Batch insert
vector_ops.batch_insert_embeddings(embeddings_data)

# Bad: Sequential insert
for embedding in embeddings:
    vector_ops.insert_embedding(...)
```

### 8. Create Indexes

Always create vector indexes for performance:
```python
# Good: Index created
from src.core.postgresql_database import create_vector_index_manager
index_manager = create_vector_index_manager(db)
index_manager.create_index("embeddings", "embedding", index_type="ivfflat")

# Bad: No index (slow searches)
```

### 9. Set Appropriate Thresholds

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

---

## Additional Resources

### Documentation
- **[PostgreSQL Database Troubleshooting](../../../docs/troubleshooting/postgresql_database_troubleshooting.md)** - Common issues and solutions

### Related Components
- **[RAG System](../rag/README.md)** - Uses database for document storage and retrieval
- **[Vector Operations](vector_operations.py)** - Vector database operations
- **[Vector Index Manager](vector_index_manager.py)** - Index management

### External Resources
- **[PostgreSQL Documentation](https://www.postgresql.org/docs/)** - PostgreSQL reference
- **[psycopg2 Documentation](https://www.psycopg.org/docs/)** - Python PostgreSQL adapter
- **[pgvector Documentation](https://github.com/pgvector/pgvector)** - Vector extension
- **[Vector Similarity Search](https://www.pinecone.io/learn/vector-similarity-search/)** - Search guide

### Examples
- **[Basic Database Example](../../../../examples/basic_usage/02_postgresql_database_basic.py)** - Simple usage
- **[Vector Operations Example](../../../../examples/)** - Vector search examples
