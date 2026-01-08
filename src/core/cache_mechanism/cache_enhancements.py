"""
Cache Enhancements

Advanced cache features: warming, monitoring, sharding, auto-caching, validation, recovery.
"""

from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import hashlib
import json
import psutil
import os


@dataclass
class CacheWarmingConfig:
    """Configuration for cache warming."""
    enabled: bool = True
    warm_on_startup: bool = True
    warm_keys: List[str] = field(default_factory=list)
    warm_functions: List[Callable] = field(default_factory=list)


@dataclass
class CacheShardingConfig:
    """Configuration for cache sharding."""
    enabled: bool = False
    num_shards: int = 4
    shard_key_func: Optional[Callable[[str], int]] = None


class CacheWarmer:
    """
    Cache warmer for pre-loading frequently accessed data.
    """
    
    def __init__(self, cache, config: Optional[CacheWarmingConfig] = None):
        """
        Initialize cache warmer.
        
        Args:
            cache: Cache mechanism instance
            config: Warming configuration
        """
        self.cache = cache
        self.config = config or CacheWarmingConfig()
        self.warmed_keys: set = set()
    
    async def warm_cache(self, tenant_id: Optional[str] = None) -> None:
        """
        Warm the cache by pre-loading data.
        
        Args:
            tenant_id: Optional tenant ID
        """
        if not self.config.enabled:
            return
        
        # Warm predefined keys
        for key in self.config.warm_keys:
            if key not in self.warmed_keys:
                # Try to get value (will be cached if function provided)
                if key in self.config.warm_functions:
                    func = self.config.warm_functions[self.config.warm_keys.index(key)]
                    try:
                        if asyncio.iscoroutinefunction(func):
                            value = await func()
                        else:
                            value = func()
                        self.cache.set(key, value, tenant_id=tenant_id)
                        self.warmed_keys.add(key)
                    except Exception as e:
                        # Log error but continue
                        pass
        
        # Warm using functions
        for func in self.config.warm_functions:
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func()
                else:
                    result = func()
                # Function should return (key, value) tuple
                if isinstance(result, tuple) and len(result) == 2:
                    key, value = result
                    self.cache.set(key, value, tenant_id=tenant_id)
                    self.warmed_keys.add(key)
            except Exception as e:
                # Log error but continue
                pass
    
    def add_warm_key(self, key: str, warm_func: Optional[Callable] = None) -> None:
        """
        Add a key to warm.
        
        Args:
            key: Cache key to warm
            warm_func: Optional function to generate value
        """
        if key not in self.config.warm_keys:
            self.config.warm_keys.append(key)
        if warm_func and warm_func not in self.config.warm_functions:
            self.config.warm_functions.append(warm_func)


class CacheMonitor:
    """
    Memory usage monitor for cache.
    """
    
    def __init__(self, cache):
        """
        Initialize cache monitor.
        
        Args:
            cache: Cache mechanism instance
        """
        self.cache = cache
        self.metrics: Dict[str, Any] = {
            "memory_usage_bytes": 0,
            "cache_size": 0,
            "hit_rate": 0.0,
            "miss_rate": 0.0,
            "total_requests": 0,
            "hits": 0,
            "misses": 0,
            "last_check": None
        }
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """
        Get current memory usage.
        
        Returns:
            Dictionary with memory usage information
        """
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        # Calculate cache memory if memory backend
        cache_memory = 0
        if self.cache.backend == "memory" and hasattr(self.cache, '_store'):
            # Estimate memory usage
            for key, (value, _) in self.cache._store.items():
                cache_memory += len(str(key).encode())
                cache_memory += len(str(value).encode())
        
        self.metrics.update({
            "memory_usage_bytes": memory_info.rss,
            "cache_size": len(self.cache._store) if hasattr(self.cache, '_store') else 0,
            "cache_memory_bytes": cache_memory,
            "last_check": datetime.now().isoformat()
        })
        
        return self.metrics
    
    def record_hit(self) -> None:
        """Record a cache hit."""
        self.metrics["hits"] += 1
        self.metrics["total_requests"] += 1
        self._update_rates()
    
    def record_miss(self) -> None:
        """Record a cache miss."""
        self.metrics["misses"] += 1
        self.metrics["total_requests"] += 1
        self._update_rates()
    
    def _update_rates(self) -> None:
        """Update hit and miss rates."""
        total = self.metrics["total_requests"]
        if total > 0:
            self.metrics["hit_rate"] = self.metrics["hits"] / total
            self.metrics["miss_rate"] = self.metrics["misses"] / total


class CacheSharder:
    """
    Automatic cache sharding for improved performance and scalability.
    """
    
    def __init__(self, cache, config: Optional[CacheShardingConfig] = None):
        """
        Initialize cache sharder.
        
        Args:
            cache: Cache mechanism instance
            config: Sharding configuration
        """
        self.cache = cache
        self.config = config or CacheShardingConfig()
        self.shards: List[Any] = []
        
        if self.config.enabled:
            self._initialize_shards()
    
    def _initialize_shards(self) -> None:
        """Initialize cache shards."""
        # Create shard instances (simplified - in production, these would be separate cache instances)
        for i in range(self.config.num_shards):
            # In a real implementation, each shard would be a separate cache instance
            self.shards.append(f"shard_{i}")
    
    def _get_shard(self, key: str) -> int:
        """
        Get shard index for a key.
        
        Args:
            key: Cache key
        
        Returns:
            Shard index
        """
        if self.config.shard_key_func:
            return self.config.shard_key_func(key) % self.config.num_shards
        
        # Default: hash-based sharding
        return int(hashlib.md5(key.encode()).hexdigest(), 16) % self.config.num_shards
    
    def get_sharded_key(self, key: str) -> str:
        """
        Get sharded key.
        
        Args:
            key: Original key
        
        Returns:
            Sharded key
        """
        if not self.config.enabled:
            return key
        
        shard = self._get_shard(key)
        return f"shard_{shard}:{key}"


class CacheValidator:
    """
    Cache validation to ensure integrity of cached data.
    """
    
    def __init__(self, cache):
        """
        Initialize cache validator.
        
        Args:
            cache: Cache mechanism instance
        """
        self.cache = cache
        self.validation_checks: List[Callable] = []
    
    def add_validation_check(self, check_func: Callable) -> None:
        """
        Add a validation check function.
        
        Args:
            check_func: Function that validates cache value
        """
        self.validation_checks.append(check_func)
    
    def validate(self, key: str, value: Any, tenant_id: Optional[str] = None) -> bool:
        """
        Validate a cached value.
        
        Args:
            key: Cache key
            value: Cached value
            tenant_id: Optional tenant ID
        
        Returns:
            True if valid, False otherwise
        """
        for check_func in self.validation_checks:
            try:
                if not check_func(key, value, tenant_id):
                    return False
            except Exception:
                return False
        return True
    
    def validate_and_get(self, key: str, tenant_id: Optional[str] = None) -> Optional[Any]:
        """
        Get and validate a cached value.
        
        Args:
            key: Cache key
            tenant_id: Optional tenant ID
        
        Returns:
            Validated value or None if invalid/not found
        """
        value = self.cache.get(key, tenant_id=tenant_id)
        if value is None:
            return None
        
        if not self.validate(key, value, tenant_id):
            # Invalid, remove from cache
            self.cache.delete(key, tenant_id=tenant_id)
            return None
        
        return value


class CacheRecovery:
    """
    Automatic recovery mechanisms for cache failures.
    """
    
    def __init__(self, cache):
        """
        Initialize cache recovery.
        
        Args:
            cache: Cache mechanism instance
        """
        self.cache = cache
        self.recovery_strategies: List[Callable] = []
        self.failure_count = 0
        self.last_failure: Optional[datetime] = None
    
    def add_recovery_strategy(self, strategy: Callable) -> None:
        """
        Add a recovery strategy.
        
        Args:
            strategy: Recovery strategy function
        """
        self.recovery_strategies.append(strategy)
    
    async def recover(self) -> bool:
        """
        Attempt to recover from cache failure.
        
        Returns:
            True if recovery successful, False otherwise
        """
        for strategy in self.recovery_strategies:
            try:
                if asyncio.iscoroutinefunction(strategy):
                    success = await strategy(self.cache)
                else:
                    success = strategy(self.cache)
                
                if success:
                    self.failure_count = 0
                    self.last_failure = None
                    return True
            except Exception:
                continue
        
        self.failure_count += 1
        self.last_failure = datetime.now()
        return False
    
    def record_failure(self) -> None:
        """Record a cache failure."""
        self.failure_count += 1
        self.last_failure = datetime.now()
    
    def should_attempt_recovery(self) -> bool:
        """Check if recovery should be attempted."""
        if self.failure_count == 0:
            return False
        
        # Attempt recovery if failures exceed threshold
        return self.failure_count >= 3


def auto_cache(
    cache,
    key_func: Optional[Callable] = None,
    ttl: Optional[int] = None,
    tenant_id: Optional[str] = None
):
    """
    Decorator for automatic caching of function results.
    
    Args:
        cache: Cache mechanism instance
        key_func: Optional function to generate cache key from function args
        ttl: Optional TTL for cached value
        tenant_id: Optional tenant ID
    
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        async def async_wrapper(*args, **kwargs) -> Any:
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default: hash of function name and arguments
                key_data = json.dumps({
                    "func": func.__name__,
                    "args": args,
                    "kwargs": kwargs
                }, sort_keys=True, default=str)
                cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Check cache
            cached_value = cache.get(cache_key, tenant_id=tenant_id)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            cache.set(cache_key, result, tenant_id=tenant_id, ttl=ttl)
            
            return result
        
        def sync_wrapper(*args, **kwargs) -> Any:
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default: hash of function name and arguments
                key_data = json.dumps({
                    "func": func.__name__,
                    "args": args,
                    "kwargs": kwargs
                }, sort_keys=True, default=str)
                cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Check cache
            cached_value = cache.get(cache_key, tenant_id=tenant_id)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            cache.set(cache_key, result, tenant_id=tenant_id, ttl=ttl)
            
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


