"""
KV Cache Management

Provides key-value cache management for LLM generation to optimize
attention computation and reduce latency for long contexts.
"""

# Standard library imports
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

# Local application/library specific imports
from ..cache_mechanism import CacheMechanism

logger = logging.getLogger(__name__)


class KVCacheEntry:
    """Represents a KV cache entry for a generation context."""
    
    def __init__(
        self,
        cache_key: str,
        keys: List[List[float]],
        values: List[List[float]],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize KV cache entry.
        
        Args:
            cache_key: Unique cache key
            keys: Attention keys (list of layers, each layer is list of key vectors)
            values: Attention values (list of layers, each layer is list of value vectors)
            metadata: Optional metadata (model, prompt_hash, etc.)
        """
        self.cache_key = cache_key
        self.keys = keys
        self.values = values
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "cache_key": self.cache_key,
            "keys": self.keys,
            "values": self.values,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KVCacheEntry":
        """Create from dictionary."""
        return cls(
            cache_key=data["cache_key"],
            keys=data["keys"],
            values=data["values"],
            metadata=data.get("metadata", {})
        )


class KVCacheManager:
    """
    Manages KV cache for LLM generation optimization.
    
    Stores and retrieves attention key-value pairs to avoid recomputation
    during generation, especially useful for long contexts and multi-turn conversations.
    """
    
    def __init__(
        self,
        cache: Optional[CacheMechanism] = None,
        enable_kv_cache: bool = True,
        kv_cache_ttl: int = 3600,  # 1 hour default
        max_cache_size_mb: int = 1000  # 1GB default
    ):
        """
        Initialize KV cache manager.
        
        Args:
            cache: Cache mechanism instance (if None, uses in-memory cache)
            enable_kv_cache: Whether to enable KV caching
            kv_cache_ttl: TTL for KV cache entries in seconds
            max_cache_size_mb: Maximum cache size in MB
        """
        self.cache = cache
        self.enable_kv_cache = enable_kv_cache
        self.kv_cache_ttl = kv_cache_ttl
        self.max_cache_size_mb = max_cache_size_mb
        
        # In-memory cache as fallback
        self._memory_cache: Dict[str, KVCacheEntry] = {}
    
    def generate_cache_key(
        self,
        prompt: str,
        model: str,
        messages: Optional[List[Dict[str, Any]]] = None,
        prefix_length: Optional[int] = None
    ) -> str:
        """
        Generate cache key for a prompt/context.
        
        Args:
            prompt: Input prompt
            model: Model identifier
            messages: Optional message history
            prefix_length: Optional prefix length for partial caching
        
        Returns:
            Cache key string
        """
        # Create hash of prompt/model combination
        if messages:
            # Use messages for multi-turn conversations
            context_str = json.dumps(messages, sort_keys=True)
        else:
            context_str = prompt
        
        if prefix_length:
            context_str = context_str[:prefix_length]
        
        hash_input = f"{model}:{context_str}"
        hash_value = hashlib.sha256(hash_input.encode()).hexdigest()
        
        return f"kv_cache:{model}:{hash_value}"
    
    def get_kv_cache(
        self,
        cache_key: str,
        tenant_id: Optional[str] = None
    ) -> Optional[KVCacheEntry]:
        """
        Retrieve KV cache entry.
        
        Args:
            cache_key: Cache key
            tenant_id: Optional tenant ID
        
        Returns:
            KV cache entry or None if not found
        """
        if not self.enable_kv_cache:
            return None
        
        # Try memory cache first
        if cache_key in self._memory_cache:
            logger.debug(f"KV cache hit (memory): {cache_key}")
            return self._memory_cache[cache_key]
        
        # Try persistent cache
        if self.cache:
            try:
                cached_data = self.cache.get(cache_key, tenant_id=tenant_id)
                if cached_data:
                    if isinstance(cached_data, dict):
                        entry = KVCacheEntry.from_dict(cached_data)
                        # Store in memory cache for faster access
                        self._memory_cache[cache_key] = entry
                        logger.debug(f"KV cache hit (persistent): {cache_key}")
                        return entry
            except Exception as e:
                logger.warning(f"Error retrieving KV cache: {str(e)}")
        
        logger.debug(f"KV cache miss: {cache_key}")
        return None
    
    def set_kv_cache(
        self,
        entry: KVCacheEntry,
        tenant_id: Optional[str] = None
    ) -> bool:
        """
        Store KV cache entry.
        
        Args:
            entry: KV cache entry
            tenant_id: Optional tenant ID
        
        Returns:
            True if stored successfully
        """
        if not self.enable_kv_cache:
            return False
        
        # Store in memory cache
        self._memory_cache[entry.cache_key] = entry
        
        # Store in persistent cache if available
        if self.cache:
            try:
                self.cache.set(
                    entry.cache_key,
                    entry.to_dict(),
                    ttl=self.kv_cache_ttl,
                    tenant_id=tenant_id
                )
                logger.debug(f"KV cache stored: {entry.cache_key}")
                return True
            except Exception as e:
                logger.warning(f"Error storing KV cache: {str(e)}")
                return False
        
        return True
    
    def invalidate_kv_cache(
        self,
        cache_key: Optional[str] = None,
        model: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> int:
        """
        Invalidate KV cache entries.
        
        Args:
            cache_key: Specific cache key to invalidate (if None, invalidates all)
            model: Optional model filter
            tenant_id: Optional tenant ID filter
        
        Returns:
            Number of entries invalidated
        """
        count = 0
        
        if cache_key:
            # Invalidate specific key
            if cache_key in self._memory_cache:
                del self._memory_cache[cache_key]
                count += 1
            
            if self.cache:
                try:
                    self.cache.delete(cache_key, tenant_id=tenant_id)
                    count += 1
                except Exception as e:
                    logger.warning(f"Error invalidating KV cache: {str(e)}")
        else:
            # Invalidate all matching entries
            keys_to_delete = []
            
            # Memory cache
            for key in list(self._memory_cache.keys()):
                if model and not key.startswith(f"kv_cache:{model}:"):
                    continue
                keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del self._memory_cache[key]
                count += 1
            
            # Persistent cache (would need pattern matching)
            if self.cache and model:
                # Note: This is a simplified version
                # Full implementation would need cache pattern matching
                logger.info(f"Invalidated {count} KV cache entries for model {model}")
        
        return count
    
    def get_cache_stats(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get KV cache statistics.
        
        Args:
            tenant_id: Optional tenant ID
        
        Returns:
            Dictionary with cache statistics
        """
        memory_count = len(self._memory_cache)
        
        # Estimate memory size
        memory_size_mb = 0
        for entry in self._memory_cache.values():
            # Rough estimate: each float is 4 bytes
            keys_size = sum(len(layer) * len(layer[0]) if layer else 0 for layer in entry.keys) * 4
            values_size = sum(len(layer) * len(layer[0]) if layer else 0 for layer in entry.values) * 4
            memory_size_mb += (keys_size + values_size) / (1024 * 1024)
        
        return {
            "enabled": self.enable_kv_cache,
            "memory_entries": memory_count,
            "memory_size_mb": round(memory_size_mb, 2),
            "max_cache_size_mb": self.max_cache_size_mb,
            "ttl_seconds": self.kv_cache_ttl,
            "has_persistent_cache": self.cache is not None
        }
    
    def clear_cache(self, tenant_id: Optional[str] = None) -> int:
        """
        Clear all KV cache entries.
        
        Args:
            tenant_id: Optional tenant ID
        
        Returns:
            Number of entries cleared
        """
        count = len(self._memory_cache)
        self._memory_cache.clear()
        
        # Note: Clearing persistent cache would require pattern matching
        # This is a simplified version
        
        logger.info(f"Cleared {count} KV cache entries")
        return count


def create_kv_cache_manager(
    cache: Optional[CacheMechanism] = None,
    enable_kv_cache: bool = True,
    **kwargs: Any
) -> KVCacheManager:
    """
    Create a KV cache manager instance.
    
    Args:
        cache: Optional cache mechanism
        enable_kv_cache: Whether to enable KV caching
        **kwargs: Additional configuration
    
    Returns:
        KVCacheManager instance
    """
    return KVCacheManager(
        cache=cache,
        enable_kv_cache=enable_kv_cache,
        **kwargs
    )

