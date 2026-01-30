# MOTADATA - GETTING STARTED WITH CACHE MECHANISM

**Complete guide for getting started with the Cache Mechanism, from cache creation to data retrieval.**

## Overview

The Cache Mechanism provides high-performance caching with multiple backends (in-memory, Dragonfly) for improving application performance. This guide explains the complete workflow from cache creation to data retrieval.

## Entry Point

The primary entry point for creating caches is through factory functions:

```python
from src.core.cache_mechanism import (
    create_memory_cache,
    create_dragonfly_cache,
    cache_set,
    cache_get,
    cache_delete
)
```

## Input Requirements

### Required Inputs

1. **Cache Configuration** (for memory cache):
   - `default_ttl`: Default time-to-live in seconds (optional)

2. **Dragonfly Configuration** (for Dragonfly cache):
   - `host`: Dragonfly server host
   - `port`: Dragonfly server port
   - `default_ttl`: Default time-to-live in seconds

### Optional Inputs

- `max_size`: Maximum cache size (for memory cache)
- `password`: Dragonfly password (if required)
- `db`: Dragonfly database number
- `decode_responses`: Decode Dragonfly responses (default: True)

## Process Flow

### Step 1: Cache Creation

**What Happens:**
1. Cache backend is initialized (memory or Dragonfly)
2. Configuration is validated
3. Connection is established (for Dragonfly)
4. Cache instance is created

**Code:**
```python
# Memory cache
cache = create_memory_cache(default_ttl=600)

# Dragonfly cache
cache = create_dragonfly_cache(
    host="localhost",
    port=6379,
    default_ttl=600
)
```

**Internal Process:**
```
create_memory_cache()
  ├─> Initialize LRU cache
  ├─> Set default TTL
  ├─> Initialize eviction policy
  └─> Return cache instance

create_dragonfly_cache()
  ├─> Validate Dragonfly connection
  ├─> Connect to Dragonfly server
  ├─> Set default TTL
  └─> Return cache instance
```

### Step 2: Setting Values

**What Happens:**
1. Key is validated
2. Value is serialized (if needed)
3. TTL is calculated
4. Value is stored in cache
5. Metadata is recorded

**Code:**
```python
cache_set(
    cache,
    key="user:123",
    value={"name": "John", "email": "john@example.com"},
    ttl=300  # 5 minutes
)
```

**Input:**
- `cache`: Cache instance
- `key`: Cache key (string)
- `value`: Value to cache (any serializable type)
- `ttl`: Time-to-live in seconds (optional, uses default if not provided)
- `tenant_id`: Optional tenant ID for multi-tenancy

**Internal Process:**
```
cache_set()
  ├─> Validate key format
  ├─> Serialize value (JSON for complex types)
  ├─> Calculate expiration time
  ├─> Store in cache backend
  │   ├─> Memory: Store in LRU dict with expiration
  │   └─> Dragonfly: SET with EX (expiration)
  ├─> Update metadata
  └─> Return success
```

### Step 3: Getting Values

**What Happens:**
1. Key is validated
2. Cache is checked for key
3. Expiration is checked
4. Value is retrieved
5. Value is deserialized (if needed)
6. Value is returned

**Code:**
```python
value = cache_get(cache, key="user:123")
if value:
    print(value)  # {"name": "John", "email": "john@example.com"}
```

**Input:**
- `cache`: Cache instance
- `key`: Cache key to retrieve
- `tenant_id`: Optional tenant ID for multi-tenancy

**Internal Process:**
```
cache_get()
  ├─> Validate key format
  ├─> Check cache backend
  │   ├─> Memory: Check LRU dict
  │   │   ├─> Check expiration
  │   │   └─> Return if valid, delete if expired
  │   └─> Dragonfly: GET key
  │       ├─> Check expiration
  │       └─> Return if exists
  ├─> Deserialize value (if needed)
  └─> Return value or None
```

### Step 4: Deleting Values

**What Happens:**
1. Key is validated
2. Key is removed from cache
3. Metadata is updated

**Code:**
```python
cache_delete(cache, key="user:123")
```

## Output

### Set Operation Output

```python
# Returns True on success, False on failure
success = cache_set(cache, "key", "value")
```

### Get Operation Output

```python
# Returns cached value or None if not found/expired
value = cache_get(cache, "key")

# Example output:
{
    "name": "John",
    "email": "john@example.com"
}
```

### Delete Operation Output

```python
# Returns True if deleted, False if not found
deleted = cache_delete(cache, "key")
```

## Where Output is Used

### 1. Direct Usage

```python
# Cache API responses
response = cache_get(cache, "api:user:123")
if not response:
    response = fetch_from_api("user:123")
    cache_set(cache, "api:user:123", response, ttl=300)
```

### 2. Integration with RAG System

```python
# RAG uses cache for query results
rag = create_rag_system(db=db, gateway=gateway, cache=cache)

# Query results are automatically cached
result1 = rag.query("What is AI?")  # Generates response
result2 = rag.query("What is AI?")  # Returns cached result
```

### 3. Integration with LiteLLM Gateway

```python
# Gateway uses cache for LLM responses
gateway = LiteLLMGateway(
    config=GatewayConfig(
        enable_caching=True,
        cache=cache
    )
)

# Identical requests return cached responses
response1 = gateway.generate("What is AI?")  # Calls LLM
response2 = gateway.generate("What is AI?")  # Returns cached
```

### 4. Integration with Agent Framework

```python
# Agents can cache task results
agent = create_agent(agent_id="agent_001", gateway=gateway, ...)

# Cache task results
task_result = cache_get(cache, f"task:{task_id}")
if not task_result:
    task_result = await agent.execute_task(task)
    cache_set(cache, f"task:{task_id}", task_result, ttl=600)
```

### 5. Pattern-Based Invalidation

```python
# Invalidate all keys matching pattern
from src.core.cache_mechanism import cache_clear_pattern

# Clear all user keys
cache_clear_pattern(cache, pattern="user:*")

# Clear all API keys
cache_clear_pattern(cache, pattern="api:*")
```

## Complete Example

```python
from src.core.cache_mechanism import (
    create_memory_cache,
    cache_set,
    cache_get,
    cache_delete,
    cache_clear_pattern
)

# Step 1: Create Cache (Entry Point)
cache = create_memory_cache(
    default_ttl=600,  # 10 minutes default
    max_size=1000     # Maximum 1000 items
)

# Step 2: Set Values (Input)
cache_set(
    cache,
    key="user:123",
    value={
        "name": "John Doe",
        "email": "john@example.com",
        "role": "admin"
    },
    ttl=300  # 5 minutes
)

cache_set(
    cache,
    key="config:app",
    value={"theme": "dark", "language": "en"},
    ttl=3600  # 1 hour
)

# Step 3: Get Values (Process)
user_data = cache_get(cache, key="user:123")
if user_data:
    print(f"User: {user_data['name']}")
    print(f"Email: {user_data['email']}")

config = cache_get(cache, key="config:app")
if config:
    print(f"Theme: {config['theme']}")

# Step 4: Use Output
# Use cached data in your application
if user_data:
    display_user_profile(user_data)

# Step 5: Delete Values
cache_delete(cache, key="user:123")

# Step 6: Pattern-Based Operations
# Clear all user keys
cache_clear_pattern(cache, pattern="user:*")
```

## Important Information

### Memory Cache Features

```python
# LRU eviction when cache is full
cache = create_memory_cache(
    max_size=100,  # Evicts least recently used when full
    default_ttl=600
)

# Automatic expiration
cache_set(cache, "key", "value", ttl=60)  # Expires in 60 seconds
# After 60 seconds, cache_get() returns None
```

### Dragonfly Cache Features

```python
# Dragonfly backend for distributed caching
cache = create_dragonfly_cache(
    host="localhost",
    port=6379,
    password="your-password",
    db=0,
    default_ttl=600
)

# Supports multiple Dragonfly instances
# Shared cache across multiple application instances
```

### Batch Operations

```python
from src.core.cache_mechanism import batch_cache_set, batch_cache_get

# Set multiple values at once
batch_cache_set(
    cache,
    {
        "user:1": {"name": "Alice"},
        "user:2": {"name": "Bob"},
        "user:3": {"name": "Charlie"}
    },
    ttl=300
)

# Get multiple values at once
values = batch_cache_get(
    cache,
    ["user:1", "user:2", "user:3"]
)
```

### Cache Warming

```python
# Pre-populate cache with frequently accessed data
def warm_cache():
    frequently_accessed = [
        ("user:1", get_user_data(1)),
        ("user:2", get_user_data(2)),
        ("config:app", get_app_config())
    ]

    for key, value in frequently_accessed:
        cache_set(cache, key, value, ttl=3600)

warm_cache()
```

### Cache Validation

```python
# Validate cache integrity
from src.core.cache_mechanism import validate_cache

is_valid = validate_cache(cache)
if not is_valid:
    # Cache may be corrupted, clear and rebuild
    cache.clear()
```

### Multi-Tenancy

```python
# All operations support tenant isolation
# Keys are automatically prefixed with tenant_id

cache_set(
    cache,
    key="user:123",
    value={"name": "John"},
    tenant_id="tenant_123"
)

# Retrieval automatically filters by tenant
value = cache_get(
    cache,
    key="user:123",
    tenant_id="tenant_123"
)
```

### Error Handling

```python
try:
    cache_set(cache, "key", "value")
except CacheError as e:
    print(f"Cache error: {e.message}")
    print(f"Error type: {e.error_type}")
except DragonflyConnectionError as e:
    print(f"Dragonfly connection error: {e.message}")
    # Fallback to memory cache or direct database access
```

### Monitoring

```python
# Monitor cache performance
from src.core.cache_mechanism import get_cache_stats

stats = get_cache_stats(cache)
print(f"Hit rate: {stats['hit_rate']:.2%}")
print(f"Miss rate: {stats['miss_rate']:.2%}")
print(f"Size: {stats['size']} items")
print(f"Memory usage: {stats['memory_mb']} MB")
```

## Next Steps

- See [README.md](README.md) for detailed component documentation
- Check [docs/components/cache_mechanism_explanation.md](../../../docs/components/cache_mechanism_explanation.md) for comprehensive guide
- Review [troubleshooting guide](../../../docs/troubleshooting/cache_mechanism_troubleshooting.md) for common issues

