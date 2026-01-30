# MOTADATA - POSTGRESQL DATABASE TROUBLESHOOTING

**Troubleshooting guide for diagnosing and resolving common issues with the PostgreSQL Database component.**

This guide helps diagnose and resolve common issues encountered when using the PostgreSQL Database component.

## Table of Contents

1. [Connection Failures](#connection-failures)
2. [Connection Pool Issues](#connection-pool-issues)
3. [Query Execution Errors](#query-execution-errors)
4. [Vector Operations Problems](#vector-operations-problems)
5. [pgvector Extension Issues](#pgvector-extension-issues)
6. [Transaction Problems](#transaction-problems)
7. [Performance Issues](#performance-issues)

## Connection Failures

### Problem: Cannot connect to database

**Symptoms:**
- Connection refused errors
- Timeout errors
- Authentication failures
- Network errors

**Diagnosis:**
```python
# Test database connection
try:
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        print("Connection successful")
except Exception as e:
    print(f"Connection error: {e}")
```

**Solutions:**

1. **Check Database Configuration:**
   ```python
   from src.core.postgresql_database import DatabaseConfig

   config = DatabaseConfig(
       host="localhost",
       port=5432,
       database="ai_app",
       user="postgres",
       password="password"
   )
   ```

2. **Verify Database is Running:**
   - Check PostgreSQL service status
   - Verify database is accessible
   - Test connection with psql

3. **Check Network Connectivity:**
   - Verify host and port
   - Check firewall rules
   - Test network connectivity

4. **Verify Credentials:**
   - Check username and password
   - Verify database name exists
   - Test authentication

## Connection Pool Issues

### Problem: Connection pool exhaustion

**Symptoms:**
- All connections in use
- Connection timeout errors
- Pool exhausted errors
- High connection wait times

**Diagnosis:**
```python
# Check pool configuration
print(f"Min connections: {db.config.min_connections}")
print(f"Max connections: {db.config.max_connections}")
```

**Solutions:**

1. **Increase Pool Size:**
   ```python
   config = DatabaseConfig(
       min_connections=5,
       max_connections=20  # Increase max connections
   )
   ```

2. **Check Connection Usage:**
   - Monitor active connections
   - Identify connection leaks
   - Close connections properly

3. **Optimize Connection Timeout:**
   ```python
   config = DatabaseConfig(
       connection_timeout=60  # Increase timeout
   )
   ```

4. **Use Connection Context Managers:**
   ```python
   # Always use context managers
   with db.get_connection() as conn:
       # Use connection
       pass
   # Connection automatically returned to pool
   ```

## Query Execution Errors

### Problem: Query execution fails

**Symptoms:**
- SQL syntax errors
- Parameter errors
- Query timeout errors
- Transaction errors

**Diagnosis:**
```python
try:
    result = db.execute_query(
        "SELECT * FROM documents WHERE id = %s",
        (document_id,),
        fetch_one=True
    )
except Exception as e:
    print(f"Query error: {e}")
```

**Solutions:**

1. **Check SQL Syntax:**
   - Verify SQL syntax
   - Test query in psql
   - Check parameter placeholders

2. **Validate Parameters:**
   ```python
   # Use parameterized queries
   db.execute_query(
       "SELECT * FROM documents WHERE tenant_id = %s",
       (tenant_id,),  # Tuple of parameters
       fetch_one=True
   )
   ```

3. **Handle Query Errors:**
   ```python
   try:
       result = db.execute_query(query, params)
   except psycopg2.Error as e:
       logger.error(f"Database error: {e}")
       # Handle error
   ```

4. **Check Table Existence:**
   ```python
   # Verify table exists
   result = db.execute_query(
       "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'documents')",
       fetch_one=True
   )
   ```

## Vector Operations Problems

### Problem: Vector operations fail

**Symptoms:**
- Embedding insertion fails
- Similarity search errors
- Vector dimension mismatches
- pgvector operator errors

**Diagnosis:**
```python
from src.core.postgresql_database import VectorOperations

vector_ops = VectorOperations(db)
# Test vector operation
try:
    embedding_id = vector_ops.insert_embedding(
        document_id=1,
        embedding=[0.1, 0.2, 0.3],
        model="text-embedding-3-small"
    )
except Exception as e:
    print(f"Vector operation error: {e}")
```

**Solutions:**

1. **Verify pgvector Extension:**
   ```python
   # Check pgvector is installed
   result = db.execute_query(
       "SELECT * FROM pg_extension WHERE extname = 'vector'",
       fetch_one=True
   )
   if not result:
       # Install pgvector extension
       db.execute_query("CREATE EXTENSION IF NOT EXISTS vector")
   ```

2. **Check Vector Column Type:**
   ```python
   # Verify embeddings table has vector column
   result = db.execute_query(
       "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'embeddings' AND column_name = 'embedding'",
       fetch_one=True
   )
   # Should be 'USER-DEFINED' with type 'vector'
   ```

3. **Verify Embedding Dimensions:**
   - Ensure all embeddings have same dimension
   - Check embedding model dimension
   - Verify vector column dimension

4. **Check Similarity Operators:**
   ```python
   # Test similarity operator
   # <=> for cosine distance
   # <-> for L2 distance
   # <#> for inner product
   ```

## pgvector Extension Issues

### Problem: pgvector extension not available

**Symptoms:**
- Extension not found errors
- Vector type not recognized
- Operator not found errors
- Extension installation fails

**Diagnosis:**
```python
# Check if pgvector is installed
result = db.execute_query(
    "SELECT * FROM pg_extension WHERE extname = 'vector'",
    fetch_one=True
)
if not result:
    print("pgvector extension not installed")
```

**Solutions:**

1. **Install pgvector Extension:**
   ```python
   # Install extension
   db.execute_query("CREATE EXTENSION IF NOT EXISTS vector")
   ```

2. **Verify Extension Version:**
   ```python
   result = db.execute_query(
       "SELECT extversion FROM pg_extension WHERE extname = 'vector'",
       fetch_one=True
   )
   print(f"pgvector version: {result['extversion']}")
   ```

3. **Check Permissions:**
   - Ensure user has CREATE EXTENSION permission
   - Check database superuser access
   - Verify extension availability

4. **Install from Source (if needed):**
   - Follow pgvector installation guide
   - Compile from source if needed
   - Verify installation

## Transaction Problems

### Problem: Transaction failures

**Symptoms:**
- Transaction rollback errors
- Deadlock errors
- Transaction timeout
- Isolation level issues

**Diagnosis:**
```python
# Check transaction status
with db.get_connection() as conn:
    try:
        conn.begin()
        # Perform operations
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Transaction error: {e}")
```

**Solutions:**

1. **Use Transactions Properly:**
   ```python
   with db.get_connection() as conn:
       try:
           # Start transaction
           cursor = conn.cursor()
           cursor.execute("INSERT INTO documents ...")
           cursor.execute("INSERT INTO embeddings ...")
           conn.commit()
       except Exception as e:
           conn.rollback()
           raise
   ```

2. **Handle Deadlocks:**
   - Retry on deadlock errors
   - Use appropriate isolation levels
   - Optimize query order

3. **Set Transaction Timeout:**
   ```python
   # Set statement timeout
   db.execute_query("SET statement_timeout = '30s'")
   ```

4. **Use Savepoints:**
   ```python
   with db.get_connection() as conn:
       cursor = conn.cursor()
       cursor.execute("SAVEPOINT sp1")
       try:
           # Operations
           cursor.execute("RELEASE SAVEPOINT sp1")
       except:
           cursor.execute("ROLLBACK TO SAVEPOINT sp1")
   ```

## Performance Issues

### Problem: Database queries are slow

**Symptoms:**
- High query latency
- Slow similarity searches
- High CPU usage
- Timeout errors

**Diagnosis:**
```python
import time

# Measure query time
start = time.time()
result = vector_ops.similarity_search(
    query_embedding=[0.1] * 1536,
    limit=10
)
duration = time.time() - start
print(f"Query took {duration} seconds")
```

**Solutions:**

1. **Create Indexes:**
   ```python
   # Create index on vector column
   db.execute_query(
       "CREATE INDEX IF NOT EXISTS embeddings_vector_idx ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
   )
   ```

2. **Optimize Query:**
   - Use appropriate LIMIT
   - Add WHERE clauses for filtering
   - Use EXPLAIN to analyze queries

3. **Optimize Connection Pool:**
   ```python
   config = DatabaseConfig(
       min_connections=10,
       max_connections=50
   )
   ```

4. **Use Batch Operations:**
   ```python
   # Batch insert embeddings
   vector_ops.batch_insert_embeddings(embeddings_data)
   ```

5. **Monitor Performance:**
   - Use EXPLAIN ANALYZE
   - Check query plans
   - Monitor slow queries

## Best Practices

1. **Always Use Context Managers:**
   ```python
   with db.get_connection() as conn:
       # Use connection
       pass
   ```

2. **Use Parameterized Queries:**
   ```python
   db.execute_query(
       "SELECT * FROM documents WHERE id = %s",
       (document_id,)
   )
   ```

3. **Handle Errors Gracefully:**
   ```python
   try:
       result = db.execute_query(query, params)
   except psycopg2.Error as e:
       logger.error(f"Database error: {e}")
       # Handle error
   ```

4. **Monitor Connection Pool:**
   - Track connection usage
   - Monitor pool statistics
   - Optimize pool size

5. **Optimize Queries:**
   - Use indexes
   - Optimize query plans
   - Monitor performance

## Getting Help

If you continue to experience issues:

1. Check the logs for detailed error messages
2. Review the PostgreSQL Database documentation
3. Verify your configuration matches the examples
4. Test database connectivity separately
5. Check pgvector extension installation
6. Review PostgreSQL and pgvector documentation

