"""
KV Cache Management

Provides key-value cache management for LLM generation to optimize
attention computation and reduce latency for long contexts.
"""


# Standard library imports
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

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
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize KV cache entry.
        
        Args:
            cache_key (str): Input parameter for this operation.
            keys (List[List[float]]): Input parameter for this operation.
            values (List[List[float]]): Input parameter for this operation.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
        """
        self.cache_key = cache_key
        self.keys = keys
        self.values = values
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for storage.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        return {
            "cache_key": self.cache_key,
            "keys": self.keys,
            "values": self.values,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KVCacheEntry":
        """
        Create from dictionary.
        
        Args:
            data (Dict[str, Any]): Input parameter for this operation.
        
        Returns:
            'KVCacheEntry': Builder instance (returned for call chaining).
        """
        return cls(
            cache_key=data["cache_key"],
            keys=data["keys"],
            values=data["values"],
            metadata=data.get("metadata", {}),
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
        max_cache_size_mb: int = 1000,  # 1GB default
    ):
        """
        Initialize KV cache manager.
        
        Args:
            cache (Optional[CacheMechanism]): Cache instance used to store and fetch cached results.
            enable_kv_cache (bool): Flag to enable or disable kv cache.
            kv_cache_ttl (int): Input parameter for this operation.
            max_cache_size_mb (int): Input parameter for this operation.
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
        prefix_length: Optional[int] = None,
    ) -> str:
        """
        Generate cache key for a prompt/context.
        
        Args:
            prompt (str): Prompt text sent to the model.
            model (str): Model name or identifier to use.
            messages (Optional[List[Dict[str, Any]]]): Chat messages in role/content format.
            prefix_length (Optional[int]): Input parameter for this operation.
        
        Returns:
            str: Returned text value.
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
        self, cache_key: str, tenant_id: Optional[str] = None
    ) -> Optional[KVCacheEntry]:
        """
        Retrieve KV cache entry.
        
        Args:
            cache_key (str): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            Optional[KVCacheEntry]: Result if available, else None.
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
                if cached_data and isinstance(cached_data, dict):
                    entry = KVCacheEntry.from_dict(cached_data)
                    # Store in memory cache for faster access
                    self._memory_cache[cache_key] = entry
                    logger.debug(f"KV cache hit (persistent): {cache_key}")
                    return entry
            except Exception as e:
                logger.warning(f"Error retrieving KV cache: {str(e)}")

        logger.debug(f"KV cache miss: {cache_key}")
        return None

    def set_kv_cache(self, entry: KVCacheEntry, tenant_id: Optional[str] = None) -> bool:
        """
        Store KV cache entry.
        
        Args:
            entry (KVCacheEntry): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            bool: True if the operation succeeds, else False.
        """
        if not self.enable_kv_cache:
            return False

        # Store in memory cache
        self._memory_cache[entry.cache_key] = entry

        # Store in persistent cache if available
        if self.cache:
            try:
                self.cache.set(
                    entry.cache_key, entry.to_dict(), ttl=self.kv_cache_ttl, tenant_id=tenant_id
                )
                logger.debug(f"KV cache stored: {entry.cache_key}")
                return True
            except Exception as e:
                logger.warning(f"Error storing KV cache: {str(e)}")
                return False

        return True

    def _invalidate_specific_key(self, cache_key: str, tenant_id: Optional[str]) -> int:
        """
        Invalidate a specific cache key.
        
        Args:
            cache_key (str): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            int: Result of the operation.
        """
        count = 0
        if cache_key in self._memory_cache:
            del self._memory_cache[cache_key]
            count += 1

        if self.cache:
            try:
                self.cache.delete(cache_key, tenant_id=tenant_id)
                count += 1
            except Exception as e:
                logger.warning(f"Error invalidating KV cache: {str(e)}")

        return count

    def _get_keys_to_invalidate(self, model: Optional[str]) -> List[str]:
        """
        Get list of keys that match the model filter.
        
        Args:
            model (Optional[str]): Model name or identifier to use.
        
        Returns:
            List[str]: List result of the operation.
        """
        keys_to_delete = []
        for key in self._memory_cache.keys():
            if model and not key.startswith(f"kv_cache:{model}:"):
                continue
            keys_to_delete.append(key)
        return keys_to_delete

    def _invalidate_memory_keys(self, keys_to_delete: List[str]) -> int:
        """
        Invalidate keys from memory cache.
        
        Args:
            keys_to_delete (List[str]): Input parameter for this operation.
        
        Returns:
            int: Result of the operation.
        """
        for key in keys_to_delete:
            del self._memory_cache[key]
        return len(keys_to_delete)

    def invalidate_kv_cache(
        self,
        cache_key: Optional[str] = None,
        model: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> int:
        """
        Invalidate KV cache entries.
        
        Args:
            cache_key (Optional[str]): Input parameter for this operation.
            model (Optional[str]): Model name or identifier to use.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            int: Result of the operation.
        """
        if cache_key:
            return self._invalidate_specific_key(cache_key, tenant_id)

        # Invalidate all matching entries
        keys_to_delete = self._get_keys_to_invalidate(model)
        count = self._invalidate_memory_keys(keys_to_delete)

        # Persistent cache (would need pattern matching)
        if self.cache and model:
            logger.info(f"Invalidated {count} KV cache entries for model {model}")

        return count

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get KV cache statistics.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        memory_count = len(self._memory_cache)

        # Estimate memory size
        memory_size_mb = 0
        for entry in self._memory_cache.values():
            # Rough estimate: each float is 4 bytes
            keys_size = sum(
                len(layer) * len(layer[0])
                if layer and isinstance(layer, list) and len(layer) > 0 and isinstance(layer[0], list)
                else 0
                for layer in entry.keys
            ) * 4
            values_size = (
                sum(
                    len(layer) * len(layer[0])
                    if layer and isinstance(layer, list) and len(layer) > 0 and isinstance(layer[0], list)
                    else 0
                    for layer in entry.values
                ) * 4
            )
            memory_size_mb += (keys_size + values_size) / (1024 * 1024)

        return {
            "enabled": self.enable_kv_cache,
            "memory_entries": memory_count,
            "memory_size_mb": round(memory_size_mb, 2),
            "max_cache_size_mb": self.max_cache_size_mb,
            "ttl_seconds": self.kv_cache_ttl,
            "has_persistent_cache": self.cache is not None,
        }

    def clear_cache(self) -> int:
        """
        Clear all KV cache entries.
        
        Returns:
            int: Result of the operation.
        """
        count = len(self._memory_cache)
        self._memory_cache.clear()

        # Note: Clearing persistent cache would require pattern matching
        # This is a simplified version

        logger.info(f"Cleared {count} KV cache entries")
        return count


def create_kv_cache_manager(
    cache: Optional[CacheMechanism] = None, enable_kv_cache: bool = True, **kwargs: Any
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
    return KVCacheManager(cache=cache, enable_kv_cache=enable_kv_cache, **kwargs)
