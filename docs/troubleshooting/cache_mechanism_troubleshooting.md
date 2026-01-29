# Motadata Cache Mechanism Troubleshooting Guide

This guide helps diagnose and resolve common issues encountered when using the Cache Mechanism.

## Table of Contents

1. [Cache Misses](#cache-misses)
2. [Memory Backend Issues](#memory-backend-issues)
3. [Redis Backend Issues](#redis-backend-issues)
4. [Cache Invalidation Problems](#cache-invalidation-problems)
5. [Performance Issues](#performance-issues)
6. [Memory Pressure](#memory-pressure)
7. [Cache Warming Issues](#cache-warming-issues)
8. [Sharding Problems](#sharding-problems)

## Cache Misses

### Problem: High cache miss rate

**Symptoms:**
- Cache misses frequently
- Low cache hit rate
- Cache not being used effectively
- Repeated queries not cached

**Diagnosis:**
1. Check cache statistics:
```python
from src.core.cache_mechanism.cache_enhancements import CacheMonitor

monitor = CacheMonitor(cache)
stats = monitor.get_memory_usage()
print(f"Hit rate: {stats['hit_rate']}")
print(f"Miss rate: {stats['miss_rate']}")
```

2. Check cache keys:
```python
# Verify cache key format
key = cache._namespaced_key("test_key", tenant_id="tenant_123")
print(f"Cache key: {key}")
```

**Solutions:**

1. **Verify Cache is Being Used:**
   ```python
   # Test cache
   cache.set("test", "value", tenant_id="tenant_123")
   value = cache.get("test", tenant_id="tenant_123")
   assert value == "value"
   ```

2. **Check TTL Configuration:**
   ```python
   from src.core.cache_mechanism import CacheConfig

   config = CacheConfig(default_ttl=3600)  # Increase TTL
   cache = CacheMechanism(config)
   ```

3. **Ensure Consistent Keys:**
   - Use consistent key format
   - Include tenant_id when needed
   - Verify key generation logic

4. **Check Cache Backend:**
   - Verify backend is initialized
   - Test backend connectivity
   - Check backend configuration

## Memory Backend Issues

### Problem: Memory cache issues

**Symptoms:**
- Memory cache not working
- Values not persisting
- Cache eviction too aggressive
- Memory usage high

**Diagnosis:**
```python
# Check memory cache state
if cache.backend == "memory":
    print(f"Cache size: {len(cache._store)}")
    print(f"Max size: {cache.config.max_size}")
```

**Solutions:**

1. **Increase Cache Size:**
   ```python
   config = CacheConfig(
       backend="memory",
       max_size=2048  # Increase max size
   )
   ```

2. **Adjust TTL:**
   ```python
   config = CacheConfig(
       default_ttl=600  # 10 minutes
   )
   ```

3. **Check LRU Eviction:**
   - Monitor eviction frequency
   - Adjust max_size if needed
   - Consider using Redis for larger caches

4. **Memory Usage:**
   - Monitor memory usage
   - Use cache monitoring
   - Consider cache sharding

## Redis Backend Issues

### Problem: Redis connection failures

**Symptoms:**
- Redis connection errors
- Cache operations failing
- Timeout errors
- Connection refused

**Diagnosis:**
```python
# Test Redis connection
if cache.backend == "redis":
    try:
        cache._client.ping()
        print("Redis connected")
    except Exception as e:
        print(f"Redis error: {e}")
```

**Solutions:**

1. **Check Redis Configuration:**
   ```python
   config = CacheConfig(
       backend="redis",
       redis_url="redis://localhost:6379/0"
   )
   ```

2. **Verify Redis is Running:**
   - Check Redis service status
   - Verify Redis port is accessible
   - Test Redis connectivity

3. **Check Redis URL:**
   - Verify URL format: `redis://host:port/db`
   - Check authentication if required
   - Verify database number

4. **Network Issues:**
   - Check firewall rules
   - Verify network connectivity
   - Test with different Redis instance

## Cache Invalidation Problems

### Problem: Cache invalidation not working

**Symptoms:**
- Stale data in cache
- Invalidated keys still present
- Pattern invalidation not working
- Cache not clearing

**Diagnosis:**
```python
# Test invalidation
cache.set("test:1", "value1")
cache.set("test:2", "value2")
cache.invalidate_pattern("test:*")
value1 = cache.get("test:1")  # Should be None
value2 = cache.get("test:2")  # Should be None
```

**Solutions:**

1. **Verify Pattern Matching:**
   - Check pattern format
   - Test pattern matching logic
   - Verify tenant_id is included if needed

2. **Manual Invalidation:**
   ```python
   # Invalidate specific key
   cache.delete("test_key", tenant_id="tenant_123")

   # Invalidate pattern
   cache.invalidate_pattern("user:*", tenant_id="tenant_123")
   ```

3. **Check Tenant Isolation:**
   - Ensure tenant_id is used correctly
   - Verify tenant-specific invalidation
   - Check key namespacing

4. **Redis Pattern Matching:**
   - For Redis, verify pattern syntax
   - Check Redis KEYS command usage
   - Consider SCAN for large key sets

## Performance Issues

### Problem: Cache is slow

**Symptoms:**
- High latency for cache operations
- Slow get/set operations
- Timeout errors
- High CPU usage

**Diagnosis:**
```python
import time

# Measure cache performance
start = time.time()
cache.set("test", "value")
set_time = time.time() - start

start = time.time()
value = cache.get("test")
get_time = time.time() - start

print(f"Set time: {set_time}, Get time: {get_time}")
```

**Solutions:**

1. **Optimize Cache Backend:**
   - Use Redis for distributed caching
   - Optimize Redis configuration
   - Use connection pooling

2. **Reduce Cache Size:**
   ```python
   config = CacheConfig(max_size=512)  # Smaller cache
   ```

3. **Optimize Key Design:**
   - Use shorter keys
   - Avoid complex key structures
   - Optimize key generation

4. **Enable Cache Monitoring:**
   ```python
   from src.core.cache_mechanism.cache_enhancements import CacheMonitor

   monitor = CacheMonitor(cache)
   stats = monitor.get_memory_usage()
   # Review performance metrics
   ```

## Memory Pressure

### Problem: High memory usage

**Symptoms:**
- High memory consumption
- Memory warnings
- Cache eviction too frequent
- System slowdown

**Diagnosis:**
```python
from src.core.cache_mechanism.cache_enhancements import CacheMonitor

monitor = CacheMonitor(cache)
usage = monitor.get_memory_usage()
print(f"Memory usage: {usage['usage_percent']}%")
print(f"Cache size: {usage['cache_size']}")
```

**Solutions:**

1. **Reduce Cache Size:**
   ```python
   config = CacheConfig(max_size=512)  # Reduce size
   ```

2. **Enable Memory Monitoring:**
   ```python
   monitor = CacheMonitor(cache)
   if monitor.check_memory_pressure():
       monitor.handle_memory_pressure()
   ```

3. **Use Redis Backend:**
   ```python
   config = CacheConfig(
       backend="redis",
       redis_url="redis://localhost:6379/0"
   )
   ```

4. **Implement Cache Sharding:**
   ```python
   from src.core.cache_mechanism.cache_enhancements import CacheSharder, CacheShardingConfig

   sharder = CacheSharder(cache, CacheShardingConfig(enabled=True, num_shards=4))
   sharder.enable_sharding()
   ```

5. **Adjust TTL:**
   - Reduce TTL for less persistent data
   - Use shorter TTL for frequently changing data
   - Balance freshness vs. performance

## Cache Warming Issues

### Problem: Cache warming not working

**Symptoms:**
- Cache not pre-populated
- Warming fails silently
- Slow startup performance
- Warming errors

**Diagnosis:**
```python
from src.core.cache_mechanism.cache_enhancements import CacheWarmer, CacheWarmingConfig

warmer = CacheWarmer(cache, CacheWarmingConfig(enabled=True))
# Check warmed keys
print(f"Warmed keys: {warmer.warmed_keys}")
```

**Solutions:**

1. **Enable Cache Warming:**
   ```python
   config = CacheWarmingConfig(
       enabled=True,
       warm_on_startup=True,
       warm_keys=["popular:data", "config:default"]
   )
   warmer = CacheWarmer(cache, config)
   await warmer.warm_cache(tenant_id="tenant_123")
   ```

2. **Add Warm Functions:**
   ```python
   def fetch_popular_data():
       return ("popular:data", {"data": "value"})

   config.warm_functions.append(fetch_popular_data)
   ```

3. **Check Warming Errors:**
   - Review warming logs
   - Verify warm functions work
   - Test warming separately

4. **Optimize Warming:**
   - Warm only critical data
   - Use async warming
   - Batch warming operations

## Sharding Problems

### Problem: Cache sharding issues

**Symptoms:**
- Sharding not working
- Uneven distribution
- Shard lookup failures
- Performance degradation

**Diagnosis:**
```python
from src.core.cache_mechanism.cache_enhancements import CacheSharder

sharder = CacheSharder(cache, config)
# Check sharding status
print(f"Sharding enabled: {sharder.config.enabled}")
```

**Solutions:**

1. **Enable Sharding:**
   ```python
   from src.core.cache_mechanism.cache_enhancements import CacheShardingConfig

   config = CacheShardingConfig(
       enabled=True,
       num_shards=4
   )
   sharder = CacheSharder(cache, config)
   sharder.enable_sharding()
   ```

2. **Custom Shard Key Function:**
   ```python
   def custom_shard_key(key: str) -> int:
       return hash(key) % 4

   config = CacheShardingConfig(
       enabled=True,
       num_shards=4,
       shard_key_func=custom_shard_key
   )
   ```

3. **Optimize Shard Count:**
   - Balance shard count with performance
   - Consider cache size
   - Monitor shard distribution

## Best Practices

1. **Monitor Cache Performance:**
   ```python
   monitor = CacheMonitor(cache)
   stats = monitor.get_memory_usage()
   # Review metrics regularly
   ```

2. **Use Appropriate TTL:**
   - Set TTL based on data volatility
   - Balance freshness vs. performance
   - Monitor cache hit rates

3. **Handle Cache Failures:**
   ```python
   try:
       value = cache.get("key")
   except Exception as e:
       # Fallback to direct operation
       value = fetch_from_source()
   ```

4. **Use Tenant Isolation:**
   - Always include tenant_id
   - Verify tenant-specific keys
   - Test tenant isolation

5. **Optimize Key Design:**
   - Use consistent key format
   - Keep keys short and descriptive
   - Include necessary identifiers

## Getting Help

If you continue to experience issues:

1. Check the logs for detailed error messages
2. Review the Cache Mechanism documentation
3. Verify your configuration matches the examples
4. Test with minimal configuration to isolate issues
5. Check Redis connectivity (if using Redis)
6. Review GitHub issues for known problems

