# MOTADATA - CACHE MECHANISM

**Comprehensive explanation of the Cache Mechanism with pluggable backends, TTL, LRU eviction, pattern-based invalidation, and advanced features.**

## Overview

The Cache Mechanism provides a pluggable cache layer with in-memory and Dragonfly backends, supporting TTL, LRU eviction, pattern-based invalidation, and advanced features like warming, monitoring, sharding, validation, and recovery.

## Table of Contents

1. [Cache Operations](#cache-operations)
2. [Cache Backends](#cache-backends)
3. [Advanced Features](#advanced-features)
4. [Exception Handling](#exception-handling)
5. [Functions](#functions)
6. [Workflow](#workflow)
7. [Customization](#customization)

---

## Cache Operations

### Functionality

Cache operations provide basic caching functionality:
- **Set**: Store values with optional TTL and tenant isolation
- **Get**: Retrieve values with automatic expiration handling
- **Delete**: Remove specific keys
- **Pattern Invalidation**: Invalidate keys matching patterns
- **LRU Eviction**: Automatic eviction for memory backend

### Code Examples

#### Basic Cache Operations

```python
from src.core.cache_mechanism import create_memory_cache

# Create cache
cache = create_memory_cache(
    default_ttl=600,  # 10 minutes
    max_size=2048
)

# Set value
cache.set(
    key="user:123",
    value={"name": "John", "email": "john@example.com"},
    tenant_id="tenant_123",
    ttl=300  # 5 minutes
)

# Get value
value = cache.get("user:123", tenant_id="tenant_123")
print(value)  # {"name": "John", "email": "john@example.com"}

# Delete value
cache.delete("user:123", tenant_id="tenant_123")
```

#### Pattern Invalidation

```python
# Invalidate all keys matching pattern
cache.invalidate_pattern(
    pattern="user:*",
    tenant_id="tenant_123"
)

# This removes all keys like:
# - sdk_cache:tenant_123:user:123
# - sdk_cache:tenant_123:user:456
# etc.
```

---

## Cache Backends

### Memory Backend

In-memory cache with LRU eviction:
- **Fast Access**: O(1) get/set operations
- **LRU Eviction**: Automatically evicts least recently used items
- **TTL Support**: Automatic expiration
- **Size Limits**: Configurable max_size

### Dragonfly Backend

Distributed cache using Dragonfly:
- **Distributed**: Shared across multiple instances
- **Persistence**: Optional persistence to disk
- **Scalability**: Handles large datasets
- **TTL Support**: Native Dragonfly TTL

### Code Examples

#### Memory Cache

```python
from src.core.cache_mechanism import create_memory_cache

cache = create_memory_cache(
    default_ttl=600,
    max_size=2048,  # Max 2048 entries
    namespace="my_cache"
)
```

#### Dragonfly Cache

```python
from src.core.cache_mechanism import create_dragonfly_cache

cache = create_dragonfly_cache(
    dragonfly_url="dragonfly://localhost:6379/0",
    default_ttl=600,
    namespace="my_cache"
)
```

---

## Advanced Features

### Cache Warming

Pre-loads frequently accessed data:

```python
from src.core.cache_mechanism.cache_enhancements import CacheWarmer, CacheWarmingConfig

# Configure warming
warming_config = CacheWarmingConfig(
    enabled=True,
    warm_on_startup=True,
    warm_keys=["user:popular", "config:default"]
)

warmer = CacheWarmer(cache, config=warming_config)

# Warm cache
await warmer.warm_cache(tenant_id="tenant_123")
```

### Memory Monitoring

Monitors cache memory usage:

```python
from src.core.cache_mechanism.cache_enhancements import CacheMonitor

monitor = CacheMonitor(cache)

# Get memory usage
usage = monitor.get_memory_usage()
print(f"Memory usage: {usage['usage_percent']}%")
print(f"Cache size: {usage['cache_size']}")

# Check memory pressure
if monitor.check_memory_pressure():
    monitor.handle_memory_pressure()
```

### Cache Sharding

Automatic cache sharding for scalability:

```python
from src.core.cache_mechanism.cache_enhancements import CacheSharder, CacheShardingConfig

# Configure sharding
sharding_config = CacheShardingConfig(
    enabled=True,
    num_shards=4,
    shard_key_func=lambda key: hash(key) % 4
)

sharder = CacheSharder(cache, config=sharding_config)
sharder.enable_sharding()
```

---

## Exception Handling

The cache mechanism handles errors gracefully:
- **Backend Failures**: Falls back to direct operations
- **Serialization Errors**: Handles serialization issues
- **Timeout Handling**: Manages timeouts for distributed caches

---

## Functions

### Factory Functions

```python
from src.core.cache_mechanism import (
    create_cache,
    create_memory_cache,
    create_dragonfly_cache
)

# Create cache
cache = create_cache(
    backend="memory",
    default_ttl=600,
    max_size=2048
)

# Create memory cache
cache = create_memory_cache(default_ttl=600)

# Create Dragonfly cache
cache = create_dragonfly_cache(dragonfly_url="dragonfly://localhost:6379/0")
```

### Convenience Functions

```python
from src.core.cache_mechanism import (
    cache_get,
    cache_set,
    cache_delete,
    cache_clear_pattern
)

# Get from cache
value = cache_get(cache, "user:123", tenant_id="tenant_123")

# Set in cache
cache_set(cache, "user:123", {"name": "John"}, ttl=600, tenant_id="tenant_123")

# Delete from cache
cache_delete(cache, "user:123", tenant_id="tenant_123")

# Clear pattern
cache_clear_pattern(cache, "user:*", tenant_id="tenant_123")
```

---

## Workflow

### Component Placement in SDK Architecture

The Cache Mechanism is positioned in the **Infrastructure Layer** and serves all components:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SDK ARCHITECTURE OVERVIEW                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ API Backend  │  │   RAG System │  │   Agents     │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          │                  │                  │
          │  ┌───────────────▼───────────────────┐                │
          │  │   CACHE MECHANISM (Infrastructure)│                │
          │  │   ┌─────────────────────────────┐  │                │
          │  │   │  Core Operations:           │  │                │
          │  │   │  - set()                    │  │                │
          │  │   │  - get()                    │  │                │
          │  │   │  - delete()                 │  │                │
          │  │   │  - invalidate_pattern()     │  │                │
          │  │   └─────────────────────────────┘  │                │
          │  │   ┌─────────────────────────────┐  │                │
          │  │   │  Advanced Features:         │  │                │
          │  │   │  - Cache Warming            │  │                │
          │  │   │  - Memory Monitoring        │  │                │
          │  │   │  - Cache Sharding           │  │                │
          │  │   │  - Cache Validation         │  │                │
          │  │   │  - Cache Recovery           │  │                │
          │  │   └─────────────────────────────┘  │                │
          │  └─────────────────────────────────────┘                │
          │                  │                                      │
┌─────────┼──────────────────┼─────────────────────────────────────┐
│         │                  │                                      │
│  ┌──────▼──────┐  ┌────────▼────────┐  ┌──────────────┐         │
│  │   Memory    │  │      Dragonfly      │  │  Monitoring  │         │
│  │   Backend   │  │     Backend     │  │   Tools      │         │
│  │             │  │                 │  │              │         │
│  │ - LRU       │  │ - Distributed   │  │ - Metrics     │         │
│  │ - TTL       │  │ - Persistent   │  │ - Alerts      │         │
│  │ - Fast      │  │ - Scalable     │  │ - Reports     │         │
│  └─────────────┘  └─────────────────┘  └──────────────┘         │
│                                                                   │
│                    INFRASTRUCTURE LAYER                           │
└───────────────────────────────────────────────────────────────────┘
```

### Cache Set Workflow

The following diagram shows the complete flow of setting a value in cache:

```
┌─────────────────────────────────────────────────────────────────┐
│                    CACHE SET WORKFLOW                            │
└─────────────────────────────────────────────────────────────────┘

    [Cache Set Request]
           │
           │ Parameters:
           │ - key: str
           │ - value: Any
           │ - tenant_id: Optional[str]
           │ - ttl: Optional[int]
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 1: Key Namespacing                                 │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ cache.set(key, value, tenant_id, ttl)            │  │
    │  │                                                   │  │
    │  │ Code Flow:                                       │  │
    │  │ 1. Get TTL (use provided or default)            │  │
    │  │ 2. Calculate expiration time:                  │  │
    │  │    expires_at = time.time() + ttl              │  │
    │  │ 3. Create namespaced key:                      │  │
    │  │    if tenant_id:                               │  │
    │  │        namespaced = f"{namespace}:{tenant_id}:{key}"│
    │  │    else:                                        │  │
    │  │        namespaced = f"{namespace}:{key}"       │  │
    │  │                                                   │  │
    │  │ Key Format:                                       │  │
    │  │ - Without tenant: "sdk_cache:user:123"         │  │
    │  │ - With tenant: "sdk_cache:tenant_123:user:123"│  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ├─────────────────┬─────────────────┘
           │                 │
           ▼                 ▼
    ┌──────────┐    ┌──────────┐
    │  Memory  │    │  Dragonfly   │
    │  Backend │    │  Backend  │
    └────┬─────┘    └────┬─────┘
         │              │
         │              │
         ▼              ▼
    ┌─────────────────────────────────────────┐
    │  Memory Backend Processing              │
    │  ┌───────────────────────────────────┐  │
    │  │ 1. Store in OrderedDict:          │  │
    │  │    _store[namespaced] = (value, expires_at)│
    │  │ 2. Move to end (LRU update):       │  │
    │  │    _store.move_to_end(namespaced) │  │
    │  │ 3. Check if eviction needed:       │  │
    │  │    if len(_store) > max_size:     │  │
    │  │        _evict_if_needed()         │  │
    │  │                                   │  │
    │  │ Eviction Logic:                   │  │
    │  │ - Remove oldest (LRU) items       │  │
    │  │ - Continue until size <= max_size │  │
    │  └───────────────────────────────────┘  │
    └─────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────┐
    │  Dragonfly Backend Processing               │
    │  ┌───────────────────────────────────┐  │
    │  │ 1. Serialize value (if needed):    │  │
    │  │    serialized = json.dumps(value)  │  │
    │  │ 2. Set in Dragonfly with TTL:         │  │
    │  │    dragonfly_client.set(               │  │
    │  │        namespaced,                 │  │
    │  │        serialized,                 │  │
    │  │        ex=ttl  # TTL in seconds   │  │
    │  │    )                               │  │
    │  │                                   │  │
    │  │ Dragonfly Operations:                  │  │
    │  │ - SET key value EX ttl            │  │
    │  │ - Automatic expiration             │  │
    │  │ - Distributed storage              │  │
    │  └───────────────────────────────────┘  │
    └─────────────────────────────────────────┘
           │
           ▼
    [Value Stored in Cache]
```

### Cache Get Workflow

The following diagram shows the complete flow of getting a value from cache:

```
┌─────────────────────────────────────────────────────────────────┐
│                    CACHE GET WORKFLOW                            │
└─────────────────────────────────────────────────────────────────┘

    [Cache Get Request]
           │
           │ Parameters:
           │ - key: str
           │ - tenant_id: Optional[str]
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 1: Key Namespacing                                 │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ cache.get(key, tenant_id)                         │  │
    │  │                                                   │  │
    │  │ Code Flow:                                       │  │
    │  │ 1. Create namespaced key (same as set)          │  │
    │  │ 2. Check backend type                           │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ├─────────────────┬─────────────────┘
           │                 │
           ▼                 ▼
    ┌──────────┐    ┌──────────┐
    │  Memory  │    │  Dragonfly   │
    │  Backend │    │  Backend  │
    └────┬─────┘    └────┬─────┘
         │              │
         │              │
         ▼              ▼
    ┌─────────────────────────────────────────┐
    │  Memory Backend Processing              │
    │  ┌───────────────────────────────────┐  │
    │  │ 1. Check if key exists:           │  │
    │  │    if namespaced not in _store:   │  │
    │  │        return None  # Cache miss  │  │
    │  │                                   │  │
    │  │ 2. Get value and expiration:     │  │
    │  │    value, expires_at = _store[namespaced]│
    │  │                                   │  │
    │  │ 3. Check expiration:              │  │
    │  │    if expires_at < time.time():   │  │
    │  │        _store.pop(namespaced)    │  │
    │  │        return None  # Expired    │  │
    │  │                                   │  │
    │  │ 4. Update LRU (move to end):      │  │
    │  │    _store.move_to_end(namespaced) │  │
    │  │                                   │  │
    │  │ 5. Return value                   │  │
    │  └───────────────────────────────────┘  │
    └─────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────┐
    │  Dragonfly Backend Processing               │
    │  ┌───────────────────────────────────┐  │
    │  │ 1. Get from Dragonfly:                │  │
    │  │    value = dragonfly_client.get(namespaced)│
    │  │                                   │  │
    │  │ 2. Check if exists:               │  │
    │  │    if value is None:              │  │
    │  │        return None  # Cache miss  │  │
    │  │                                   │  │
    │  │ 3. Deserialize (if needed):       │  │
    │  │    deserialized = json.loads(value)│
    │  │                                   │  │
    │  │ 4. Return value                   │  │
    │  │                                   │  │
    │  │ Note: Dragonfly handles TTL automatically│
    │  └───────────────────────────────────┘  │
    └─────────────────────────────────────────┘
           │
           ▼
    [Return Value or None]
```

### Cache Warming Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    CACHE WARMING WORKFLOW                        │
└─────────────────────────────────────────────────────────────────┘

    [Warm Cache Request]
           │
           │ Parameters:
           │ - tenant_id: Optional[str]
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 1: Check Warming Configuration                     │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ if not config.enabled:                            │  │
    │  │     return  # Warming disabled                    │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 2: Warm Predefined Keys                           │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ for key in config.warm_keys:                      │  │
    │  │     if key not in warmed_keys:                    │  │
    │  │         # Get warm function if provided           │  │
    │  │         if warm_func:                             │  │
    │  │             value = await warm_func()             │  │
    │  │             cache.set(key, value, tenant_id)      │  │
    │  │             warmed_keys.add(key)                   │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 3: Warm Using Functions                           │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ for func in config.warm_functions:                 │  │
    │  │     result = await func()                          │  │
    │  │     if isinstance(result, tuple):                  │  │
    │  │         key, value = result                        │  │
    │  │         cache.set(key, value, tenant_id)          │  │
    │  │         warmed_keys.add(key)                       │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    [Cache Warmed]
```

### Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│              COMPONENT INTERACTION FLOW                          │
└─────────────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │CacheMechanism│
                    │   (Core)     │
                    └──────┬───────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   Memory      │  │     Dragonfly     │  │  Enhancements │
│   Backend     │  │    Backend    │  │               │
│               │  │               │  │ - Warmer      │
│ Functions:    │  │ Functions:     │  │ - Monitor     │
│ - OrderedDict │  │ - SET/GET     │  │ - Sharder     │
│ - LRU         │  │ - TTL         │  │ - Validator   │
│ - TTL         │  │ - Distributed │  │ - Recovery    │
└───────────────┘  └───────────────┘  └───────────────┘
```

### Parameter Details

#### CacheConfig Parameters

```python
@dataclass
class CacheConfig:
    backend: str = "memory"  # Cache backend type
                          # Values:
                          #   - "memory": In-memory cache
                          #   - "dragonfly": Dragonfly cache
                          # Default: "memory"

    default_ttl: int = 300  # Default TTL in seconds
                          # Applies when ttl not specified in set()
                          # Range: 1 - 86400 (1 day)
                          # Default: 300 (5 minutes)

    max_size: int = 1024  # Maximum cache size (entries)
                         # Only applies to memory backend
                         # Range: 1 - 1000000
                         # Default: 1024
                         # LRU eviction when exceeded

    dragonfly_url: Optional[str] = None  # Dragonfly connection URL
                                   # Required for Dragonfly backend
                                   # Format: "dragonfly://host:port/db"
                                   # Example: "dragonfly://localhost:6379/0"

    namespace: str = "sdk_cache"  # Cache namespace
                                 # Prevents key collisions
                                 # Format: "{namespace}:{tenant_id}:{key}"
                                 # Default: "sdk_cache"
```

#### set() Parameters

```python
def set(
    self,
    key: str,                    # Cache key
                               # Required, non-empty string
                               # Should be descriptive and unique

    value: Any,                  # Value to cache
                               # Can be any serializable type
                               # For Dragonfly: must be JSON serializable

    tenant_id: Optional[str] = None,  # Tenant identifier
                               # Used for key namespacing
                               # Ensures tenant isolation
                               # Format: "{namespace}:{tenant_id}:{key}"

    ttl: Optional[int] = None   # Time-to-live in seconds
                               # Overrides default_ttl if provided
                               # Range: 1 - 86400
                               # None = use default_ttl
                               # 0 = no expiration (not recommended)
) -> None
```

#### get() Parameters

```python
def get(
    self,
    key: str,                    # Cache key to retrieve
                               # Must match key used in set()

    tenant_id: Optional[str] = None  # Tenant identifier
                               # Must match tenant_id used in set()
                               # Ensures tenant isolation
) -> Optional[Any]  # Returns cached value or None
                   # None indicates:
                   #   - Key not found (cache miss)
                   #   - Value expired
                   #   - Key was deleted
```

#### invalidate_pattern() Parameters

```python
def invalidate_pattern(
    self,
    pattern: str,                # Pattern to match keys
                               # Simple substring matching
                               # Examples:
                               #   - "user:*" matches "user:123", "user:456"
                               #   - "*:config" matches "app:config", "sys:config"

    tenant_id: Optional[str] = None  # Tenant identifier
                               # Limits invalidation to specific tenant
                               # If provided, pattern is scoped to tenant
                               # Format: "{tenant_id}:{pattern}"
) -> None
```

---

## Customization

### Configuration

```python
# Custom cache configuration
config = CacheConfig(
    backend="dragonfly",
    default_ttl=600,  # 10 minutes
    max_size=10000,   # Larger cache
    dragonfly_url="dragonfly://localhost:6379/0",
    namespace="custom_cache"
)

cache = CacheMechanism(config=config)
```

### Custom Warming Strategy

```python
# Custom warming configuration
warming_config = CacheWarmingConfig(
    enabled=True,
    warm_on_startup=True,
    warm_keys=["popular:users", "config:default"],
    warm_functions=[
        lambda: ("popular:users", fetch_popular_users()),
        lambda: ("config:default", fetch_default_config())
    ]
)

warmer = CacheWarmer(cache, config=warming_config)
await warmer.warm_cache(tenant_id="tenant_123")
```

### Custom Sharding Strategy

```python
# Custom sharding configuration
def custom_shard_key(key: str) -> int:
    """Custom shard key function."""
    # Hash key and modulo by number of shards
    return hash(key) % 4

sharding_config = CacheShardingConfig(
    enabled=True,
    num_shards=4,
    shard_key_func=custom_shard_key
)

sharder = CacheSharder(cache, config=sharding_config)
sharder.enable_sharding()
```

---

## Best Practices

1. **TTL Values**: Set appropriate TTL based on data volatility
2. **Key Design**: Use consistent, descriptive cache keys
3. **Tenant Isolation**: Always use tenant_id for multi-tenant deployments
4. **Pattern Invalidation**: Use pattern invalidation for related keys
5. **Memory Management**: Monitor memory usage for memory backend
6. **Dragonfly for Scale**: Use Dragonfly backend for distributed deployments
7. **Cache Warming**: Warm frequently accessed data on startup
8. **Error Handling**: Handle cache failures gracefully
9. **Monitoring**: Monitor cache hit/miss rates
10. **Sharding**: Use sharding for large-scale deployments

---

## Additional Resources

- **Component README**: `src/core/cache_mechanism/README.md`
- **Function Documentation**: `src/core/cache_mechanism/functions.py`
- **Examples**: `examples/basic_usage/06_cache_basic.py`

