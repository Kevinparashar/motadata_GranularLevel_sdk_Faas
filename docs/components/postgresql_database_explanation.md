# PostgreSQL Database - Comprehensive Component Explanation

## Overview

The PostgreSQL Database component provides robust database connectivity and management for the entire SDK. It includes comprehensive support for the pgvector extension, enabling efficient vector similarity search operations essential for RAG systems and embedding-based applications.

## Table of Contents

1. [Database Connection](#database-connection)
2. [Vector Operations](#vector-operations)
3. [Query Execution](#query-execution)
4. [Exception Handling](#exception-handling)
5. [Functions](#functions)
6. [Workflow](#workflow)
7. [Customization](#customization)

---

## Database Connection

### Functionality

Database connection management provides:
- **Connection Pooling**: Efficiently manages database connections
- **Connection Health**: Validates database connectivity
- **Transaction Management**: Supports transactions for atomic operations
- **Query Execution**: Safe query execution with error handling

### Code Examples

#### Creating Database Connection

```python
from src.core.postgresql_database import DatabaseConnection, DatabaseConfig

# Create database configuration
config = DatabaseConfig(
    host="localhost",
    port=5432,
    database="ai_app",
    user="postgres",
    password="password",
    min_connections=1,
    max_connections=10,
    connection_timeout=30
)

# Create database connection
db = DatabaseConnection(config)
db.connect()
```

#### Using Connection Pool

```python
# Get connection from pool
with db.get_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM documents")
        results = cursor.fetchall()

# Get cursor directly
with db.get_cursor() as cursor:
    cursor.execute("SELECT * FROM documents")
    results = cursor.fetchall()
```

---

## Vector Operations

### Functionality

Vector operations provide pgvector functionality:
- **Embedding Storage**: Stores vector embeddings
- **Similarity Search**: Performs efficient similarity searches
- **Batch Operations**: Supports batch insertion
- **Indexing**: Supports vector indexes for performance

### Code Examples

#### Inserting Embeddings

```python
from src.core.postgresql_database import VectorOperations

vector_ops = VectorOperations(db)

# Insert single embedding
embedding_id = vector_ops.insert_embedding(
    document_id=123,
    embedding=[0.1, 0.2, 0.3, ...],
    model="text-embedding-3-small"
)

# Batch insert embeddings
embeddings_data = [
    (123, [0.1, 0.2, ...], "text-embedding-3-small"),
    (124, [0.3, 0.4, ...], "text-embedding-3-small")
]
vector_ops.batch_insert_embeddings(embeddings_data)
```

#### Similarity Search

```python
# Perform similarity search
results = vector_ops.similarity_search(
    query_embedding=[0.1, 0.2, 0.3, ...],
    limit=10,
    threshold=0.7,
    model="text-embedding-3-small",
    filters={"tenant_id": "tenant_123"}
)

for result in results:
    print(f"Document: {result['title']}")
    print(f"Similarity: {result['similarity']}")
```

---

## Query Execution

### Functionality

Query execution provides safe query execution:
- **Parameterized Queries**: Prevents SQL injection
- **Transaction Support**: Atomic operations
- **Error Handling**: Comprehensive error handling
- **Result Formatting**: Consistent result formatting

### Code Examples

#### Executing Queries

```python
# Execute query with parameters
result = db.execute_query(
    "SELECT * FROM documents WHERE tenant_id = %s",
    ("tenant_123",),
    fetch_one=True
)

# Execute query returning multiple rows
results = db.execute_query(
    "SELECT * FROM documents WHERE category = %s",
    ("tutorial",),
    fetch_all=True
)
```

---

## Exception Handling

The component handles database errors:
- **Connection Errors**: Handles connection failures
- **Query Errors**: Catches SQL errors
- **Transaction Errors**: Handles transaction failures

---

## Functions

### Factory Functions

```python
from src.core.postgresql_database import create_database_connection

# Create database connection
db = create_database_connection(
    host="localhost",
    port=5432,
    database="ai_app",
    user="postgres",
    password="password"
)
```

---

## Workflow

### Component Placement in SDK Architecture

The PostgreSQL Database is positioned in the **Infrastructure Layer**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SDK ARCHITECTURE OVERVIEW                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ API Backend  │  │   RAG System  │  │   Agents     │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
┌─────────┼──────────────────┼──────────────────┼─────────────────┐
│         │                  │                  │                  │
│  ┌──────▼──────────────────▼──────────────────▼──────┐          │
│  │  POSTGRESQL DATABASE (Infrastructure Layer)       │          │
│  │  ┌──────────────┐  ┌──────────────┐              │          │
│  │  │  Database    │  │   Vector     │              │          │
│  │  │  Connection │  │  Operations  │              │          │
│  │  │              │  │              │              │          │
│  │  │ Functions:   │  │ Functions:   │              │          │
│  │  │ - connect()  │  │ - insert_    │              │          │
│  │  │ - execute_   │  │   embedding()│              │          │
│  │  │   query()   │  │ - similarity_│              │          │
│  │  │ - get_       │  │   search()   │              │          │
│  │  │   connection()│ │ - batch_     │              │          │
│  │  │              │  │   insert_    │              │          │
│  │  │              │  │   embeddings()│            │          │
│  │  └──────────────┘  └──────────────┘              │          │
│  └───────────────────────────────────────────────────┘          │
│                  │                                              │
│                  ▼                                              │
│  ┌──────────────────────────────────────────────┐              │
│  │         PostgreSQL Database                   │              │
│  │  - documents table                            │              │
│  │  - embeddings table (with pgvector)          │              │
│  │  - Connection pool                           │              │
│  └──────────────────────────────────────────────┘              │
│                                                                  │
│                    INFRASTRUCTURE LAYER                          │
└──────────────────────────────────────────────────────────────────┘
```

### Database Connection Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│              DATABASE CONNECTION WORKFLOW                       │
└─────────────────────────────────────────────────────────────────┘

    [Database Connection Request]
           │
           │ Parameters:
           │ - config: DatabaseConfig
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 1: Connection Pool Creation                        │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ db = DatabaseConnection(config)                   │  │
    │  │ db.connect()                                      │  │
    │  │                                                   │  │
    │  │ Code Flow:                                       │  │
    │  │ 1. Create ThreadedConnectionPool:                │  │
    │  │    pool = ThreadedConnectionPool(                 │  │
    │  │        minconn=config.min_connections,           │  │
    │  │        maxconn=config.max_connections,           │  │
    │  │        host=config.host,                          │  │
    │  │        port=config.port,                         │  │
    │  │        database=config.database,                 │  │
    │  │        user=config.user,                        │  │
    │  │        password=config.password                 │  │
    │  │    )                                             │  │
    │  │ 2. Store pool in connection_pool                 │  │
    │  │                                                   │  │
    │  │ Pool Parameters:                                  │  │
    │  │ - min_connections: int (default: 1)              │  │
    │  │   Minimum connections in pool                    │  │
    │  │ - max_connections: int (default: 10)             │  │
    │  │   Maximum connections in pool                    │  │
    │  │ - connection_timeout: int (default: 30 seconds) │  │
    │  │   Timeout for getting connection                 │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 2: Get Connection from Pool                       │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ with db.get_connection() as conn:                │  │
    │  │     # Use connection                             │  │
    │  │                                                   │  │
    │  │ Code Flow:                                       │  │
    │  │ 1. Check if pool exists                          │  │
    │  │ 2. Get connection from pool:                     │  │
    │  │    conn = pool.getconn()                         │  │
    │  │ 3. Yield connection                              │  │
    │  │ 4. Return connection to pool:                    │  │
    │  │    pool.putconn(conn)                            │  │
    │  │                                                   │  │
    │  │ Connection Lifecycle:                            │  │
    │  │ - Acquired from pool                             │  │
    │  │ - Used for queries                               │  │
    │  │ - Returned to pool (reused)                      │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    [Connection Available for Use]
```

### Vector Similarity Search Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│              VECTOR SIMILARITY SEARCH WORKFLOW                   │
└─────────────────────────────────────────────────────────────────┘

    [Similarity Search Request]
           │
           │ Parameters:
           │ - query_embedding: List[float]
           │ - limit: int
           │ - threshold: float
           │ - model: Optional[str]
           │ - filters: Optional[Dict]
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 1: Embedding Format Conversion                     │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ embedding_str = "[" + ",".join(map(str, embedding)) + "]"│
    │  │                                                   │  │
    │  │ Format: "[0.1,0.2,0.3,...]"                      │  │
    │  │ Required for pgvector                              │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 2: SQL Query Construction                          │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ query = """                                       │  │
    │  │     SELECT                                        │  │
    │  │         e.id,                                     │  │
    │  │         e.document_id,                            │  │
    │  │         d.title,                                  │  │
    │  │         d.content,                                │  │
    │  │         d.metadata,                               │  │
    │  │         1 - (e.embedding <=> %s::vector) as similarity│
    │  │     FROM embeddings e                             │  │
    │  │     JOIN documents d ON e.document_id = d.id      │  │
    │  │     WHERE 1 - (e.embedding <=> %s::vector) >= %s  │  │
    │  │     ORDER BY e.embedding <=> %s::vector            │  │
    │  │     LIMIT %s                                       │  │
    │  │ """                                                │  │
    │  │                                                   │  │
    │  │ pgvector Operators:                                │  │
    │  │ - <=>: Cosine distance                            │  │
    │  │ - <->: L2 distance                                │  │
    │  │ - <#>: Inner product                              │  │
    │  │                                                   │  │
    │  │ Similarity Calculation:                            │  │
    │  │ similarity = 1 - (embedding1 <=> embedding2)     │  │
    │  │ Range: 0.0 (dissimilar) to 1.0 (identical)       │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 3: Filter Application (if provided)               │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ if filters:                                       │  │
    │  │     # Add WHERE clauses for filters              │  │
    │  │     if "tenant_id" in filters:                   │  │
    │  │         query += " AND d.tenant_id = %s"        │  │
    │  │     if "category" in filters:                     │  │
    │  │         query += " AND d.metadata->>'category' = %s"│
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 4: Query Execution                                │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ results = db.execute_query(                      │  │
    │  │     query,                                        │  │
    │  │     params,                                       │  │
    │  │     fetch_all=True                                │  │
    │  │ )                                                 │  │
    │  │                                                   │  │
    │  │ Result Structure:                                 │  │
    │  │ [                                                 │  │
    │  │     {                                             │  │
    │  │         "id": int,                                │  │
    │  │         "document_id": int,                       │  │
    │  │         "title": str,                             │  │
    │  │         "content": str,                            │  │
    │  │         "metadata": Dict,                         │  │
    │  │         "similarity": float                        │  │
    │  │     },                                            │  │
    │  │     ...                                           │  │
    │  │ ]                                                 │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    [Return Results Sorted by Similarity]
```

### Parameter Details

#### DatabaseConfig Parameters

```python
class DatabaseConfig(BaseModel):
    host: str = "localhost"  # Database host
                          # IP address or hostname
                          # Default: "localhost"

    port: int = 5432  # Database port
                     # Standard PostgreSQL port
                     # Range: 1 - 65535
                     # Default: 5432

    database: str = "ai_app"  # Database name
                            # Must exist in PostgreSQL
                            # Default: "ai_app"

    user: str = "postgres"  # Database user
                          # Must have appropriate permissions
                          # Default: "postgres"

    password: str = ""  # Database password
                      # Required for authentication
                      # Default: "" (empty)

    min_connections: int = 1  # Minimum connections in pool
                            # Connections created on startup
                            # Range: 1 - 100
                            # Default: 1

    max_connections: int = 10  # Maximum connections in pool
                             # Maximum concurrent connections
                             # Range: 1 - 1000
                             # Default: 10

    connection_timeout: int = 30  # Connection timeout (seconds)
                                # Time to wait for connection
                                # Range: 1 - 300
                                # Default: 30
```

#### similarity_search() Parameters

```python
def similarity_search(
    self,
    query_embedding: List[float],  # Query embedding vector
                                 # Required, list of floats
                                 # Must match embedding dimension
                                 # Example: [0.1, 0.2, 0.3, ...]

    limit: int = 10,             # Maximum number of results
                                # Range: 1 - 1000
                                # Default: 10
                                # Higher = more results, slower

    threshold: float = 0.0,      # Minimum similarity threshold
                                # Range: 0.0 - 1.0
                                # Default: 0.0 (no threshold)
                                # Higher = stricter matching

    model: Optional[str] = None,  # Embedding model filter
                                 # Filters embeddings by model
                                 # Example: "text-embedding-3-small"
                                 # None = no filter

    filters: Optional[Dict[str, Any]] = None  # Metadata filters
                                 # Filters documents by metadata
                                 # Common keys:
                                 #   - "tenant_id": str
                                 #   - "category": str
                                 #   - "tags": List[str]
) -> List[Dict[str, Any]]  # Returns list of documents with similarity scores
```

---

## Customization

### Configuration

```python
# Custom database configuration
config = DatabaseConfig(
    host="db.example.com",
    port=5432,
    database="custom_db",
    user="custom_user",
    password="secure_password",
    min_connections=5,
    max_connections=50,
    connection_timeout=60
)

db = DatabaseConnection(config)
```

---

## Best Practices

1. **Connection Pooling**: Configure appropriate pool sizes
2. **Indexing**: Create indexes on vector columns for performance
3. **Query Optimization**: Use parameterized queries
4. **Transaction Management**: Use transactions for atomic operations
5. **Error Handling**: Implement comprehensive error handling
6. **Connection Management**: Always return connections to pool
7. **Vector Dimensions**: Ensure consistent embedding dimensions
8. **Similarity Thresholds**: Set appropriate thresholds for quality

---

## Additional Resources

- **Component README**: `src/core/postgresql_database/README.md`
- **Examples**: `examples/basic_usage/03_postgresql_database_basic.py`

