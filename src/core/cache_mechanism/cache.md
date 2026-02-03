# MOTADATA - CACHE MECHANISM CLASS DOCUMENTATION

**Complete class documentation for the CacheMechanism class providing flexible caching with multiple backends.**

## Overview

The `cache.py` file contains the core `CacheMechanism` class implementation, which provides a flexible caching system for improving performance and reducing costs in AI operations. The cache supports multiple backends (in-memory, Dragonfly), tenant-scoped caching, TTL-based expiration, and pattern-based invalidation.

**Primary Functionality:**
- Multi-backend caching (in-memory LRU, Dragonfly)
- Tenant-scoped cache isolation
- TTL-based expiration
- Pattern-based cache invalidation
- Cache warming strategies
- Memory usage monitoring
- Automatic cache sharding
- Cache validation and recovery

## Code Explanation

### Class Structure

#### `CacheConfig` (BaseModel)
Configuration model for the cache mechanism:

**Backend Configuration:**
- `backend`: Cache backend ("memory" or "dragonfly")
- `dragonfly_url`: Dragonfly connection URL (if using Dragonfly)
- `max_size`: Maximum cache size (for in-memory)
- `ttl`: Default time-to-live in seconds

**Advanced Configuration:**
- `enable_sharding`: Enable automatic sharding
- `enable_validation`: Enable cache validation
- `enable_recovery`: Enable automatic recovery
- `shard_count`: Number of shards (if sharding enabled)

#### `CacheMechanism` (Class)
Main cache mechanism class.

**Core Attributes:**
- `config`: Cache configuration
- `backend`: Cache backend instance
- `shards`: Cache shards (if sharding enabled)
- `stats`: Cache statistics

### Key Methods

#### `get(key, tenant_id=None, default=None) -> Any`
Retrieves a value from cache.

**Parameters:**
- `key`: Cache key
- `tenant_id`: Optional tenant ID for tenant-scoped caching
- `default`: Default value if key not found

**Returns:** Cached value or default

**Example:**
```python
value = cache.get("my_key", tenant_id="tenant_123", default=None)
```

#### `set(key, value, ttl=None, tenant_id=None) -> bool`
Stores a value in cache.

**Parameters:**
- `key`: Cache key
- `value`: Value to cache
- `ttl`: Time-to-live in seconds (uses config default if not provided)
- `tenant_id`: Optional tenant ID for tenant-scoped caching

**Returns:** Boolean indicating success

**Example:**
```python
cache.set("my_key", "my_value", ttl=3600, tenant_id="tenant_123")
```

#### `delete(key, tenant_id=None) -> bool`
Deletes a key from cache.

**Parameters:**
- `key`: Cache key to delete
- `tenant_id`: Optional tenant ID

**Returns:** Boolean indicating success

#### `invalidate(pattern, tenant_id=None) -> int`
Invalidates keys matching a pattern.

**Parameters:**
- `pattern`: Pattern to match (supports wildcards)
- `tenant_id`: Optional tenant ID

**Returns:** Number of keys invalidated

**Example:**
```python
# Invalidate all keys starting with "user_"
count = cache.invalidate("user_*", tenant_id="tenant_123")
```

#### `clear(tenant_id=None) -> int`
Clears all cache entries (optionally for a tenant).

**Parameters:**
- `tenant_id`: Optional tenant ID

**Returns:** Number of keys cleared

#### `get_stats(tenant_id=None) -> Dict[str, Any]`
Gets cache statistics.

**Parameters:**
- `tenant_id`: Optional tenant ID

**Returns:** Dictionary with cache statistics:
- `hits`: Number of cache hits
- `misses`: Number of cache misses
- `size`: Current cache size
- `memory_usage`: Memory usage (if applicable)

#### `warm_cache(keys_and_values, tenant_id=None) -> int`
Warms cache with pre-loaded values.

**Parameters:**
- `keys_and_values`: Dictionary of key-value pairs
- `tenant_id`: Optional tenant ID

**Returns:** Number of keys warmed

## Usage Instructions

### Basic Cache Creation

```python
from src.core.cache_mechanism import CacheMechanism, CacheConfig

# In-memory cache
config = CacheConfig(
    backend="memory",
    max_size=1000,
    ttl=3600
)
cache = CacheMechanism(config)

# Dragonfly cache
config = CacheConfig(
    backend="dragonfly",
    dragonfly_url="dragonfly://localhost:6379",
    ttl=3600
)
cache = CacheMechanism(config)
```

### Basic Operations

```python
# Set value
cache.set("key1", "value1", ttl=3600, tenant_id="tenant_123")

# Get value
value = cache.get("key1", tenant_id="tenant_123")

# Delete key
cache.delete("key1", tenant_id="tenant_123")

# Clear all
cache.clear(tenant_id="tenant_123")
```

### Pattern-Based Invalidation

```python
# Invalidate all keys matching pattern
count = cache.invalidate("user_*", tenant_id="tenant_123")
print(f"Invalidated {count} keys")

# Invalidate all keys for tenant
count = cache.clear(tenant_id="tenant_123")
```

### Cache Warming

```python
# Warm cache with pre-loaded data
warm_data = {
    "key1": "value1",
    "key2": "value2",
    "key3": "value3"
}
count = cache.warm_cache(warm_data, tenant_id="tenant_123")
print(f"Warmed {count} keys")
```

### Statistics

```python
# Get cache statistics
stats = cache.get_stats(tenant_id="tenant_123")
print(f"Hits: {stats['hits']}, Misses: {stats['misses']}")
print(f"Hit Rate: {stats['hits'] / (stats['hits'] + stats['misses']) * 100:.2f}%")
```

### Prerequisites

1. **Python 3.10+**: Required for type hints
2. **Dependencies**: Install via `pip install -r requirements.txt`
   - `dragonfly`: For Dragonfly backend (optional)
   - `pydantic`: For data validation
3. **Dragonfly** (optional): For distributed caching

## Connection to Other Components

### LiteLLM Gateway
The gateway uses cache for:
- Response caching
- Embedding caching
- Cost reduction

**Integration Point:** `gateway.cache` attribute

### RAG System
The RAG system uses cache for:
- Query result caching
- Embedding caching
- Performance optimization

**Integration Point:** `rag.cache` attribute

### Agent Framework
Agents use cache for:
- Response caching
- Context caching
- Performance improvement

**Integration Point:** `agent.cache` attribute (if configured)

### Where Used
- **All AI Components**: Gateway, RAG, Agents use caching
- **FaaS Cache Service**: REST API wrapper for cache
- **Examples**: All examples can use caching

## Best Practices

### 1. Use Tenant-Scoped Caching
Always use tenant_id for multi-tenant applications:
```python
# Good: Tenant-scoped
cache.set("key", "value", tenant_id="tenant_123")

# Bad: Global cache (no tenant isolation)
cache.set("key", "value")
```

### 2. Set Appropriate TTL
Set TTL based on data volatility:
```python
# Good: Appropriate TTL
cache.set("key", "value", ttl=3600)  # 1 hour for semi-static data
cache.set("key", "value", ttl=60)    # 1 minute for dynamic data

# Bad: Too long or too short
cache.set("key", "value", ttl=86400)  # Too long (may serve stale data)
cache.set("key", "value", ttl=1)      # Too short (ineffective)
```

### 3. Use Dragonfly for Distributed Systems
Use Dragonfly backend for multi-instance deployments:
```python
# Good: Dragonfly for distributed
config = CacheConfig(backend="dragonfly", dragonfly_url="dragonfly://...")

# Bad: In-memory for distributed (not shared)
config = CacheConfig(backend="memory")
```

### 4. Monitor Cache Performance
Regularly check cache statistics:
```python
# Good: Monitor performance
stats = cache.get_stats(tenant_id="tenant_123")
if stats['hit_rate'] < 0.5:
    # Cache not effective, investigate
    logger.warning("Low cache hit rate")
```

### 5. Use Pattern Invalidation
Use pattern invalidation for related keys:
```python
# Good: Pattern invalidation
cache.invalidate("user_*", tenant_id="tenant_123")

# Bad: Individual deletion
for key in keys:
    cache.delete(key, tenant_id="tenant_123")
```

### 6. Warm Cache for Critical Data
Warm cache with frequently accessed data:
```python
# Good: Cache warming
frequent_data = load_frequent_data()
cache.warm_cache(frequent_data, tenant_id="tenant_123")

# Bad: No warming (cold cache initially)
```

## Additional Resources

### Documentation
- **[Cache README](README.md)** - Complete cache guide
- **[Cache Functions](functions.py)** - Factory functions
- **[Cache Troubleshooting](../../../docs/troubleshooting/cache_mechanism_troubleshooting.md)** - Common issues

### Related Components
- **[Cache Enhancements](cache_enhancements.py)** - Advanced features
- **[Dragonfly Integration](https://dragonfly.io/docs/)** - Dragonfly documentation

### External Resources
- **[Caching Strategies](https://aws.amazon.com/caching/)** - Caching best practices
- **[Dragonfly Documentation](https://dragonfly.io/docs/)** - Dragonfly reference

### Examples
- **[Basic Cache Example](../../../../examples/basic_usage/04_cache_basic.py)** - Simple usage
- **[Cache with Dragonfly Example](../../../../examples/)** - Dragonfly backend

