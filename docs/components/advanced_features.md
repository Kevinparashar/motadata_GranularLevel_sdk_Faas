# Motadata Advanced Features

This document describes the advanced features implemented in the SDK for production-grade AI applications.

## Table of Contents

1. [Vector Index Management](#vector-index-management)
2. [KV Cache for LLM Generation](#kv-cache-for-llm-generation)
3. [Hallucination Detection](#hallucination-detection)

---

## Vector Index Management

### Overview

Vector indexes are critical for optimal search performance in RAG systems. The SDK provides comprehensive index management including creation, monitoring, and automatic reindexing.

### Features

- **IVFFlat Index**: Efficient for large datasets with configurable lists parameter
- **HNSW Index**: Better for high-dimensional vectors with M and ef_construction parameters
- **Automatic Reindexing**: Automatically rebuilds indexes when embeddings change
- **Concurrent Reindexing**: Non-blocking index rebuilds for production systems
- **Index Statistics**: Monitor index size, usage, and performance

### Usage

```python
from src.core.rag import create_rag_system, IndexType, IndexDistance

# Create RAG system
rag = create_rag_system(db, gateway)

# Create IVFFlat index
rag.create_index(
    index_type=IndexType.IVFFLAT,
    distance=IndexDistance.COSINE,
    lists=100  # Auto-calculated if not provided
)

# Create HNSW index
rag.create_index(
    index_type=IndexType.HNSW,
    distance=IndexDistance.COSINE,
    m=16,
    ef_construction=64
)

# Reindex after model change or bulk updates
reindexed = rag.reindex(concurrently=True)

# Get index information
indexes = rag.get_index_info()
```

### When to Reindex

- After changing embedding models
- After bulk document ingestion
- When search performance degrades
- After significant data updates

---

## KV Cache for LLM Generation

### Overview

KV (Key-Value) cache stores attention key-value pairs during LLM generation to avoid recomputation, significantly improving performance for long contexts and multi-turn conversations.

### Features

- **Automatic Caching**: Integrated into gateway generation methods
- **Memory and Persistent Cache**: Supports both in-memory and persistent storage
- **Cache Statistics**: Monitor cache usage and performance
- **Selective Invalidation**: Invalidate by model, key, or tenant

### Usage

```python
from src.core.litellm_gateway import create_gateway

# Create gateway with KV cache enabled
gateway = create_gateway(
    api_keys={"openai": "sk-..."},
    enable_kv_cache=True,
    kv_cache_ttl=3600  # 1 hour
)

# Generation automatically uses KV cache
response = gateway.generate(
    prompt="Long context prompt...",
    model="gpt-4"
)

# Check cache statistics
if gateway.kv_cache:
    stats = gateway.kv_cache.get_cache_stats()
    print(f"Cache entries: {stats['memory_entries']}")
```

### Benefits

- **Reduced Latency**: Faster generation for repeated or similar prompts
- **Cost Savings**: Avoids recomputation of attention layers
- **Better Performance**: Especially beneficial for long contexts (>4K tokens)

---

## Hallucination Detection

### Overview

Hallucination detection ensures that RAG-generated responses are grounded in the retrieved context documents, preventing false or unsupported information.

### Features

- **Multi-Strategy Detection**: Uses semantic similarity, fact extraction, and citation checking
- **LLM-Based Verification**: Optional LLM verification for complex cases
- **Sentence-Level Analysis**: Identifies which sentences are grounded vs ungrounded
- **Confidence Scoring**: Provides confidence levels for detection results

### Usage

```python
from src.core.rag import create_rag_system

# Create RAG system
rag = create_rag_system(db, gateway)

# Query with hallucination detection
result = rag.query(
    query="What is AI?",
    top_k=3,
    check_hallucination=True  # Enable detection
)

# Check results
if 'hallucination_result' in result:
    hallucination = result['hallucination_result']
    print(f"Is hallucination: {hallucination['is_hallucination']}")
    print(f"Confidence: {hallucination['confidence']}")
    print(f"Grounded ratio: {hallucination['metadata']['grounded_ratio']}")
```

### Manual Detection

```python
from src.core.rag import HallucinationDetector

detector = HallucinationDetector(
    gateway=gateway,
    enable_llm_verification=True,
    similarity_threshold=0.7,
    min_grounded_ratio=0.6
)

result = detector.detect(
    response=generated_text,
    context_documents=retrieved_docs,
    query=original_query
)
```

### Configuration

- **similarity_threshold**: Minimum similarity for grounding (default: 0.7)
- **min_grounded_ratio**: Minimum ratio of sentences that must be grounded (default: 0.6)
- **enable_llm_verification**: Use LLM for verification (default: True)

---

## Integration Examples

See the following example files for complete usage:

- `examples/advanced_features/vector_index_management.py`
- `examples/advanced_features/kv_cache_usage.py`
- `examples/advanced_features/hallucination_detection.py`

---

## Best Practices

### Vector Index Management

1. **Create indexes after initial data ingestion** for optimal performance
2. **Use HNSW for high-dimensional vectors** (>768 dimensions)
3. **Use IVFFlat for large datasets** (>1M vectors)
4. **Reindex after model changes** to maintain search quality
5. **Monitor index statistics** regularly

### KV Cache

1. **Enable for production** to improve performance
2. **Set appropriate TTL** based on your use case
3. **Monitor cache hit rates** to optimize configuration
4. **Invalidate when models change** to avoid stale data

### Hallucination Detection

1. **Enable for production RAG** to ensure quality
2. **Use LLM verification** for critical applications
3. **Adjust thresholds** based on your domain
4. **Monitor detection results** to improve prompts and retrieval

---

## Performance Impact

- **Vector Indexes**: 10-100x faster search queries
- **KV Cache**: 20-50% latency reduction for repeated contexts
- **Hallucination Detection**: <5% overhead, critical for quality assurance

---

## Related Documentation

- [RAG System Documentation](../src/core/rag/README.md)
- [LiteLLM Gateway Documentation](../src/core/litellm_gateway/README.md)
- [Vector Database Documentation](../src/core/postgresql_database/vector_database/README.md)

