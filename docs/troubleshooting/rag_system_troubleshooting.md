# Motadata RAG System Troubleshooting Guide

This guide helps diagnose and resolve common issues encountered when using the RAG System.

## Table of Contents

1. [Document Ingestion Failures](#document-ingestion-failures)
2. [Retrieval Issues](#retrieval-issues)
3. [Generation Errors](#generation-errors)
4. [Embedding Problems](#embedding-problems)
5. [Database Connection Issues](#database-connection-issues)
6. [Chunking Problems](#chunking-problems)
7. [Performance Issues](#performance-issues)
8. [Cache Issues](#cache-issues)

## Document Ingestion Failures

### Problem: Documents fail to ingest

**Symptoms:**
- `DocumentProcessingError` exceptions
- Documents not appearing in database
- Ingestion hangs or times out
- Chunking errors

**Diagnosis:**
1. Check document content:
```python
try:
    result = rag_system.ingest_document(
        title="Test",
        content="Test content",
        tenant_id="tenant_123"
    )
except DocumentProcessingError as e:
    print(f"Error: {e.message}")
    print(f"Document ID: {e.document_id}")
    print(f"Operation: {e.operation}")
```

2. Check database connection:
```python
# Test database connection
with rag_system.db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
```

**Solutions:**

1. **Empty or Invalid Content:**
   - Ensure document content is not empty
   - Validate content format
   - Check content encoding

2. **Database Connection Issues:**
   - Verify database is accessible
   - Check connection pool configuration
   - Test database connectivity

3. **Chunking Errors:**
   - Adjust chunk size:
   ```python
   processor = DocumentProcessor(chunk_size=500)
   ```
   - Try different chunking strategies
   - Validate document format

4. **Embedding Generation Failures:**
   - Check LiteLLM Gateway configuration
   - Verify embedding model is available
   - Test embedding generation separately

## Retrieval Issues

### Problem: No documents retrieved

**Symptoms:**
- Empty retrieval results
- Low similarity scores
- No relevant documents found
- Retrieval returns empty list

**Diagnosis:**
1. Check retrieval parameters:
```python
results = rag_system.query(
    query="test query",
    top_k=5,
    threshold=0.7,
    tenant_id="tenant_123"
)
print(f"Retrieved: {len(results['retrieved_documents'])}")
```

2. Check database content:
```python
# Verify documents exist
with rag_system.db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM documents WHERE tenant_id = %s", ("tenant_123",))
    count = cursor.fetchone()[0]
    print(f"Documents in database: {count}")
```

**Solutions:**

1. **Lower Similarity Threshold:**
   ```python
   results = rag_system.query(
       query="test query",
       threshold=0.5  # Lower threshold
   )
   ```

2. **Increase Top-K:**
   ```python
   results = rag_system.query(
       query="test query",
       top_k=10  # Retrieve more documents
   )
   ```

3. **Use Hybrid Retrieval:**
   ```python
   results = rag_system.query(
       query="test query",
       retrieval_strategy="hybrid"  # Combine vector and keyword search
   )
   ```

4. **Check Embedding Quality:**
   - Verify embeddings are generated correctly
   - Check embedding dimensions match
   - Ensure embedding model is appropriate

5. **Verify Document Ingestion:**
   - Ensure documents are ingested successfully
   - Check document metadata
   - Verify tenant_id matches

## Generation Errors

### Problem: Response generation fails

**Symptoms:**
- `GenerationError` exceptions
- Empty or null responses
- Generation timeouts
- Invalid response format

**Diagnosis:**
```python
try:
    result = rag_system.query(query="test")
except GenerationError as e:
    print(f"Generation error: {e.message}")
    print(f"Query: {e.query}")
    print(f"Context: {e.context}")
```

**Solutions:**

1. **Check Gateway Configuration:**
   - Verify LiteLLM Gateway is configured
   - Test gateway separately
   - Check API keys and quotas

2. **Reduce Context Size:**
   ```python
   results = rag_system.query(
       query="test query",
       top_k=3  # Reduce context size
   )
   ```

3. **Adjust Max Tokens:**
   ```python
   results = rag_system.query(
       query="test query",
       max_tokens=500  # Reduce max tokens
   )
   ```

4. **Check Retrieved Documents:**
   - Ensure documents are retrieved
   - Verify document content is valid
   - Check document format

5. **Review Generation Model:**
   - Verify model is available
   - Check model compatibility
   - Try different model

## Embedding Problems

### Problem: Embedding generation fails

**Symptoms:**
- `EmbeddingError` exceptions
- Embeddings not generated
- Invalid embedding format
- Embedding dimension mismatches

**Diagnosis:**
```python
try:
    embedding = await rag_system.retriever.gateway.embed_async(
        text="test",
        model="text-embedding-3-small"
    )
except EmbeddingError as e:
    print(f"Embedding error: {e.message}")
    print(f"Text: {e.text}")
    print(f"Model: {e.model}")
```

**Solutions:**

1. **Check Gateway Configuration:**
   - Verify gateway is initialized
   - Check embedding model is configured
   - Test gateway embedding separately

2. **Verify Model Availability:**
   - Check model is in gateway model_list
   - Verify API keys for embedding provider
   - Test model directly

3. **Check Text Input:**
   - Ensure text is not empty
   - Validate text encoding
   - Check text length limits

4. **Dimension Consistency:**
   - Ensure all embeddings use same model
   - Verify embedding dimensions match
   - Check database vector column type

## Database Connection Issues

### Problem: Database connection failures

**Symptoms:**
- Connection errors
- Query timeouts
- Connection pool exhaustion
- Transaction failures

**Diagnosis:**
```python
# Test database connection
try:
    with rag_system.db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
except Exception as e:
    print(f"Database error: {e}")
```

**Solutions:**

1. **Check Database Configuration:**
   - Verify database host, port, credentials
   - Test database connectivity
   - Check firewall rules

2. **Connection Pool Configuration:**
   ```python
   from src.core.postgresql_database import DatabaseConfig

   config = DatabaseConfig(
       min_connections=5,
       max_connections=20,
       connection_timeout=60
   )
   ```

3. **Verify pgvector Extension:**
   ```python
   # Check pgvector is installed
   with db.get_connection() as conn:
       cursor = conn.cursor()
       cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
       if not cursor.fetchone():
           print("pgvector extension not installed")
   ```

4. **Check Database Tables:**
   - Verify `documents` table exists
   - Verify `embeddings` table exists
   - Check table schemas match

## Chunking Problems

### Problem: Chunking fails or produces poor results

**Symptoms:**
- `ChunkingError` exceptions
- Chunks too large or too small
- Poor chunk boundaries
- Missing content

**Diagnosis:**
```python
try:
    chunks = rag_system.document_processor.chunk_document(
        content="test content",
        chunk_size=1000
    )
except ChunkingError as e:
    print(f"Chunking error: {e.message}")
    print(f"Strategy: {e.chunking_strategy}")
```

**Solutions:**

1. **Adjust Chunk Size:**
   ```python
   processor = DocumentProcessor(chunk_size=500)  # Smaller chunks
   ```

2. **Try Different Strategy:**
   ```python
   processor = DocumentProcessor(
       chunk_size=1000,
       chunk_overlap=200  # Add overlap
   )
   ```

3. **Validate Content:**
   - Ensure content is not empty
   - Check content encoding
   - Validate content format

4. **Check Chunking Parameters:**
   - Verify chunk_size is appropriate
   - Check chunk_overlap settings
   - Review chunking strategy

## Performance Issues

### Problem: RAG system is slow

**Symptoms:**
- High latency
- Slow query responses
- Timeout errors
- High resource usage

**Diagnosis:**
1. Measure query time:
```python
import time
start = time.time()
result = rag_system.query("test query")
duration = time.time() - start
print(f"Query took {duration} seconds")
```

2. Check component performance:
```python
# Test retrieval separately
start = time.time()
docs = rag_system.retriever.retrieve("test", top_k=5)
print(f"Retrieval: {time.time() - start} seconds")

# Test generation separately
start = time.time()
answer = rag_system.generator.generate("test", docs)
print(f"Generation: {time.time() - start} seconds")
```

**Solutions:**

1. **Enable Caching:**
   ```python
   from src.core.cache_mechanism import CacheMechanism, CacheConfig

   cache = CacheMechanism(CacheConfig(default_ttl=600))
   rag_system = RAGSystem(db, gateway, cache=cache)
   ```

2. **Optimize Retrieval:**
   - Reduce top_k if possible
   - Use hybrid retrieval for better results
   - Optimize similarity threshold

3. **Optimize Generation:**
   - Reduce max_tokens
   - Use faster models
   - Reduce context size

4. **Database Optimization:**
   - Create indexes on vector columns
   - Optimize database queries
   - Use connection pooling

5. **Batch Operations:**
   - Use batch ingestion
   - Batch embedding generation
   - Optimize database inserts

## Cache Issues

### Problem: Cache not working

**Symptoms:**
- Cache misses
- Stale results
- Cache not being used
- High cache miss rate

**Diagnosis:**
```python
# Check cache configuration
if rag_system.cache:
    # Test cache
    rag_system.cache.set("test", "value", ttl=300)
    value = rag_system.cache.get("test")
    print(f"Cache test: {value}")
```

**Solutions:**

1. **Verify Cache is Configured:**
   ```python
   from src.core.cache_mechanism import CacheMechanism, CacheConfig

   cache = CacheMechanism(CacheConfig(default_ttl=600))
   rag_system = RAGSystem(db, gateway, cache=cache)
   ```

2. **Check Cache Keys:**
   - Ensure cache keys are consistent
   - Include tenant_id in cache keys
   - Verify key format

3. **Adjust TTL:**
   ```python
   cache_config = CacheConfig(default_ttl=3600)  # 1 hour
   ```

4. **Check Cache Backend:**
   - Verify Redis connection (if using Redis)
   - Check memory cache size limits
   - Monitor cache performance

## Best Practices

1. **Handle Errors Gracefully:**
   ```python
   try:
       result = rag_system.query(query="test")
   except RetrievalError as e:
       logger.error(f"Retrieval failed: {e}")
   except GenerationError as e:
       logger.error(f"Generation failed: {e}")
   ```

2. **Monitor Performance:**
   - Track query response times
   - Monitor retrieval performance
   - Check generation metrics

3. **Validate Inputs:**
   - Validate queries before processing
   - Check document content before ingestion
   - Verify tenant_id is provided

4. **Use Appropriate Parameters:**
   - Set appropriate top_k values
   - Use suitable similarity thresholds
   - Configure appropriate chunk sizes

5. **Enable Caching:**
   - Cache query results
   - Cache embeddings when possible
   - Monitor cache hit rates

## Getting Help

If you continue to experience issues:

1. Check the logs for detailed error messages
2. Review the RAG System documentation
3. Verify your configuration matches the examples
4. Test with minimal configuration to isolate issues
5. Check database and gateway connectivity
6. Review GitHub issues for known problems

