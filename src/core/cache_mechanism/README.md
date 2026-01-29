# Motadata Cache Mechanism

## When to Use This Component

**✅ Use Cache Mechanism when:**
- Same queries are asked multiple times
- You want to reduce LLM API costs significantly
- You need faster response times for repeated requests
- You're building production systems with cost optimization
- You have predictable query patterns
- You want to cache embeddings, responses, or query results

**❌ Don't use Cache Mechanism when:**
- Every query is unique (no benefit from caching)
- You need real-time data that changes constantly
- You're in development/testing with no cost concerns
- Cache invalidation would be too complex for your use case
- Memory is extremely limited (in-memory cache uses RAM)

**Simple Example:**
```python
from src.core.cache_mechanism import create_memory_cache, cache_set, cache_get

cache = create_memory_cache(default_ttl=3600)

# Set a value
cache_set(cache, "user:123", {"name": "John"}, ttl=600)

# Get it back (instant, no API call)
value = cache_get(cache, "user:123")
```

**Cost Impact:** Caching can reduce LLM costs by **50-90%** for repeated queries. For example:
- Without cache: 1000 queries × $0.01 = $10
- With cache (50% hit rate): 500 API calls × $0.01 = $5 (saves $5)

---

## Overview

The Cache Mechanism component provides caching capabilities to improve performance, reduce costs, and enhance user experience. It offers in-memory (LRU + TTL) and Redis backends with pattern-based invalidation.

## Purpose and Functionality

- Reduce LLM and retrieval costs by caching responses and embeddings
- Improve latency through reuse of cached results
- Provide TTL management and simple eviction for memory-bound deployments
- Allow pattern-based invalidation for coordinated cache clears

## Connection to Other Components

### Integration with LiteLLM Gateway

The **LiteLLM Gateway** (`src/core/litellm_gateway/`) can use the cache mechanism to cache LLM responses. When the gateway receives a request, it can check the cache first. If a cached response exists and is still valid, it returns the cached response instead of making an API call. This significantly reduces costs and improves response times for repeated queries.

### Integration with RAG System

The **RAG System** (`src/core/rag/`) uses caching in multiple ways:
1. **Query Result Caching**: Frequently asked questions can be cached, avoiding expensive retrieval and generation operations
2. **Embedding Caching**: Document embeddings can be cached to avoid regenerating them
3. **Retrieved Document Caching**: Retrieved document sets can be cached for similar queries

This caching is particularly valuable for RAG systems, as retrieval and generation operations are computationally expensive.

### Integration with PostgreSQL Database

The **PostgreSQL Database** (`src/core/postgresql_database/`) can serve as a caching backend. When configured to use database caching, the cache mechanism stores cached data in the database, providing persistent caching that survives application restarts.

### Integration with Evaluation & Observability

The **Evaluation & Observability** component (`src/core/evaluation_observability/`) tracks cache performance metrics:
- **Cache Hit Rates**: Measures how often cached data is found
- **Cache Miss Rates**: Tracks cache misses
- **Cache Performance**: Monitors cache operation times
- **Cost Savings**: Estimates cost savings from caching

This monitoring helps optimize cache configurations and identify caching opportunities.

### Integration with API Backend Services

The **API Backend Services** (`src/core/api_backend_services/`) can use caching to improve API response times. Frequently accessed endpoints can cache their responses, reducing backend processing time and improving user experience.

## Backends

- **Memory**: OrderedDict-based LRU with TTL and max-size enforcement
- **Redis**: Optional; enabled when `redis` dependency and URL are provided

## Function-Driven API

The Cache Mechanism provides a **function-driven API** with factory functions, high-level convenience functions, and utilities for easy cache creation and usage.

### Factory Functions

Create caches with simplified configuration:

```python
from src.core.cache_mechanism import (
    create_cache,
    create_memory_cache,
    create_redis_cache
)

# Create in-memory cache
cache = create_memory_cache(default_ttl=600, max_size=2048)

# Create Redis cache
cache = create_redis_cache(
    redis_url="redis://localhost:6379/0",
    default_ttl=600
)

# Create cache with custom config
cache = create_cache(
    backend="memory",
    default_ttl=300,
    namespace="my_cache"
)
```

### High-Level Convenience Functions

Use simplified functions for common operations:

```python
from src.core.cache_mechanism import (
    cache_get,
    cache_set,
    cache_delete,
    cache_clear_pattern
)

# Get from cache
value = cache_get(cache, "user:123")

# Set in cache
cache_set(cache, "user:123", {"name": "John"}, ttl=600)

# Delete from cache
cache_delete(cache, "user:123")

# Clear pattern
cache_clear_pattern(cache, "user:*")
```

### Utility Functions

Use utility functions for advanced patterns:

```python
from src.core.cache_mechanism import (
    cache_or_compute,
    batch_cache_set,
    batch_cache_get
)

# Cache or compute
def expensive_operation():
    # Expensive computation
    return result

value = cache_or_compute(cache, "expensive:key", expensive_operation, ttl=3600)

# Batch operations
items = {"user:1": {"name": "John"}, "user:2": {"name": "Jane"}}
batch_cache_set(cache, items, ttl=600)

values = batch_cache_get(cache, ["user:1", "user:2", "user:3"])
```

See `src/core/cache_mechanism/functions.py` for complete function documentation.

## Key Features

### Core Features

- **TTL Management**: Configurable default TTL per instance
- **LRU Eviction**: Max-size enforcement for memory backend
- **Pattern Invalidation**: Clear keys matching simple patterns
- **Namespace Support**: Avoid collisions across components

### Cache Statistics

The component tracks cache statistics:
- **Hit/Miss Ratios**: Tracks cache effectiveness
- **Size Metrics**: Monitors cache size and memory usage
- **Performance Metrics**: Tracks cache operation performance

### Cache Warming Strategies

The cache mechanism now supports **cache warming** to pre-load frequently accessed data:

- **Pre-loading**: Pre-loads data into cache before it's needed
- **Warming Patterns**: Configurable patterns for identifying data to warm
- **Scheduled Warming**: Schedule cache warming at specific times
- **On-Demand Warming**: Trigger cache warming on demand

**Example:**
```python
from src.core.cache_mechanism.cache_enhancements import CacheWarmer

# Create cache warmer
warmer = CacheWarmer(
    cache=cache,
    warming_strategy="scheduled",  # or "on_demand", "automatic"
    warming_interval=3600  # seconds
)

# Define warming patterns
warmer.add_warming_pattern("user:*", priority=1)
warmer.add_warming_pattern("document:*", priority=2)

# Start warming
warmer.start_warming()
```

### Memory Usage Monitoring

The cache mechanism includes **memory usage monitoring** for better resource management:

- **Memory Tracking**: Tracks memory usage in real-time
- **Memory Alerts**: Alerts when memory usage exceeds thresholds
- **Memory Pressure Handling**: Automatically handles memory pressure
- **Memory Reports**: Provides detailed memory usage reports

**Example:**
```python
from src.core.cache_mechanism.cache_enhancements import CacheMonitor

# Create cache monitor
monitor = CacheMonitor(
    cache=cache,
    memory_threshold=0.8,  # Alert at 80% memory usage
    enable_alerts=True
)

# Get memory usage
usage = monitor.get_memory_usage()
print(f"Memory usage: {usage['usage_percent']}%")
print(f"Memory available: {usage['available_mb']}MB")

# Check memory pressure
if monitor.check_memory_pressure():
    monitor.handle_memory_pressure()
```

### Automatic Cache Sharding

The cache mechanism supports **automatic cache sharding** for improved performance:

- **Automatic Sharding**: Automatically shards cache across multiple nodes
- **Shard Management**: Manages shards and distributes load
- **Shard Recovery**: Recovers from shard failures
- **Shard Balancing**: Balances load across shards

**Example:**
```python
from src.core.cache_mechanism.cache_enhancements import CacheSharder

# Create cache sharder
sharder = CacheSharder(
    cache=cache,
    num_shards=4,
    sharding_strategy="consistent_hashing"  # or "round_robin", "key_based"
)

# Enable sharding
sharder.enable_sharding()

# Get shard for key
shard = sharder.get_shard("user:123")
```

### Cache Validation

The cache mechanism includes **cache validation processes** to ensure data integrity:

- **Data Validation**: Validates cached data before retrieval
- **Integrity Checks**: Checks data integrity and consistency
- **Validation Rules**: Configurable validation rules
- **Automatic Validation**: Automatically validates data on retrieval

**Example:**
```python
from src.core.cache_mechanism.cache_enhancements import CacheValidator

# Create cache validator
validator = CacheValidator(
    cache=cache,
    validate_on_get=True,
    validate_on_set=True,
    validation_rules=["schema_check", "integrity_check"]
)

# Add custom validation rule
validator.add_validation_rule(
    lambda data: isinstance(data, dict) and "id" in data,
    "Data must be a dict with 'id' field"
)

# Attach validator to cache
cache.attach_validator(validator)
```

### Automatic Recovery Mechanisms

The cache mechanism provides **automatic recovery** for cache failures:

- **Failure Detection**: Detects cache failures automatically
- **Automatic Recovery**: Automatically recovers from failures
- **Recovery Strategies**: Multiple recovery strategies (retry, fallback, rebuild)
- **Recovery Monitoring**: Monitors recovery process

**Example:**
```python
from src.core.cache_mechanism.cache_enhancements import CacheRecovery

# Create cache recovery
recovery = CacheRecovery(
    cache=cache,
    recovery_strategy="automatic",  # or "manual", "scheduled"
    retry_attempts=3,
    fallback_cache=fallback_cache  # Optional fallback cache
)

# Enable recovery
recovery.enable_recovery()

# Get recovery status
status = recovery.get_recovery_status()
print(f"Recovery status: {status['status']}")
print(f"Recovery attempts: {status['attempts']}")
```

## Error Handling

The component implements robust error handling:
- **Backend Failures**: Gracefully handles cache backend failures, falling back to direct operations
- **Serialization Errors**: Handles errors when serializing/deserializing cached data
- **Timeout Handling**: Manages timeouts when accessing distributed caches

## Configuration

`CacheConfig` supports:
- `backend`: `"memory"` or `"redis"`
- `default_ttl`: default TTL in seconds
- `max_size`: max entries for in-memory cache
- `redis_url`: optional Redis connection URL
- `namespace`: namespacing for keys

## Best Practices

1. **Appropriate TTL Values**: Set TTL values based on data volatility
2. **Cache Key Design**: Use consistent, unique cache keys
3. **Cache Invalidation**: Implement proper cache invalidation strategies
4. **Monitor Performance**: Track cache hit rates and adjust configurations
5. **Distributed Caching**: Use distributed caches (Redis) for multi-instance deployments
6. **Cost-Benefit Analysis**: Balance cache complexity with performance and cost benefits
7. **Cache Warming**: Use cache warming for frequently accessed data to improve performance
8. **Memory Monitoring**: Monitor memory usage to prevent memory pressure and optimize cache size
9. **Cache Sharding**: Use cache sharding for large-scale deployments to improve performance and scalability
10. **Cache Validation**: Enable cache validation to ensure data integrity and consistency
11. **Recovery Mechanisms**: Configure automatic recovery to handle cache failures gracefully
12. **Cache Statistics**: Regularly review cache statistics to optimize cache configuration
