# Motadata PostgreSQL Database Connection Documentation

## Overview

The `connection.py` file contains the core `DatabaseConnection` class implementation, which provides a robust, production-ready interface for connecting to and managing PostgreSQL databases. This class handles connection pooling, health monitoring, transaction management, and tenant-scoped operations for multi-tenant SaaS applications.

**Primary Functionality:**
- PostgreSQL database connection management
- Connection pooling for performance
- Health monitoring and status checks
- Transaction management (begin, commit, rollback)
- Tenant-scoped query execution
- Connection retry logic
- Query execution with error handling
- Database schema management

## Code Explanation

### Class Structure

#### `DatabaseConnection` (Class)
Main database connection class.

**Core Attributes:**
- `connection_string`: PostgreSQL connection string
- `pool`: Connection pool instance
- `max_connections`: Maximum pool connections
- `min_connections`: Minimum pool connections
- `health_check`: Health monitoring instance

### Key Methods

#### `connect() -> None`
Establishes database connection and creates connection pool.

**Process:**
1. Parses connection string
2. Creates connection pool
3. Validates connection
4. Sets up health monitoring

#### `execute_query(query, parameters=None, tenant_id=None) -> List[Dict[str, Any]]`
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

#### `execute_update(query, parameters=None, tenant_id=None) -> int`
Executes an UPDATE, INSERT, or DELETE query.

**Parameters:**
- `query`: SQL query string
- `parameters`: Query parameters
- `tenant_id`: Optional tenant ID

**Returns:** Number of affected rows

#### `begin_transaction() -> None`
Begins a database transaction.

#### `commit_transaction() -> None`
Commits the current transaction.

#### `rollback_transaction() -> None`
Rolls back the current transaction.

#### `check_health() -> Dict[str, Any]`
Checks database connection health.

**Returns:** Dictionary with health status

#### `close() -> None`
Closes database connections and pool.

## Usage Instructions

### Basic Connection

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

### With Transactions

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

### Tenant-Scoped Queries

```python
# Tenant-scoped query
results = db.execute_query(
    "SELECT * FROM documents WHERE tenant_id = %s",
    parameters=(tenant_id,),
    tenant_id=tenant_id
)
```

### Health Monitoring

```python
# Check health
health = db.check_health()
if health["status"] == "healthy":
    print("Database is operational")
```

### Prerequisites

1. **Python 3.10+**: Required for type hints
2. **Dependencies**: Install via `pip install -r requirements.txt`
   - `psycopg2` or `psycopg2-binary`: PostgreSQL adapter
   - `pgvector`: For vector operations (optional)
3. **PostgreSQL**: PostgreSQL database server
4. **pgvector Extension**: For vector operations (optional)

## Connection to Other Components

### Vector Operations
Used by `VectorOperations` from `src/core/postgresql_database/vector_operations.py`:
- Provides database connection for vector operations
- Enables vector similarity search

**Integration Point:** `vector_ops.db` attribute

### RAG System
Used by `RAGSystem` from `src/core/rag/rag_system.py`:
- Stores document metadata
- Stores vector embeddings
- Enables document retrieval

**Integration Point:** `rag.db` attribute

### Vector Index Manager
Used by `VectorIndexManager` from `src/core/postgresql_database/vector_index_manager.py`:
- Creates and manages vector indexes
- Optimizes search performance

**Integration Point:** `index_manager.db` attribute

### Where Used
- **All Components**: RAG, Agents, and other components use database
- **FaaS Services**: All FaaS services use database for persistence
- **Examples**: All database examples use this class

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

## Additional Resources

### Documentation
- **[PostgreSQL Database README](README.md)** - Complete database guide
- **[Vector Operations Documentation](vector_operations.md)** - Vector operations
- **[Vector Index Manager Documentation](vector_index_manager.md)** - Index management

### Related Components
- **[Vector Operations](vector_operations.py)** - Vector database operations
- **[Vector Index Manager](vector_index_manager.py)** - Index management

### External Resources
- **[PostgreSQL Documentation](https://www.postgresql.org/docs/)** - PostgreSQL reference
- **[psycopg2 Documentation](https://www.psycopg.org/docs/)** - Python PostgreSQL adapter
- **[pgvector Documentation](https://github.com/pgvector/pgvector)** - Vector extension

### Examples
- **[Basic Database Example](../../../../examples/basic_usage/02_postgresql_database_basic.py)** - Simple usage
- **[Vector Operations Example](../../../../examples/)** - Vector search

