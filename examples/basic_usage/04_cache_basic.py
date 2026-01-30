"""
Basic Cache Example

Demonstrates how to use the Cache component
for caching LLM responses and embeddings.

Dependencies: LiteLLM Gateway, RAG
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

load_dotenv(project_root / ".env")

from src.core.cache_mechanism import CacheConfig, CacheMechanism


def main():
    """Demonstrate basic caching features."""

    # 1. Memory Cache Example
    print("=== Memory Cache Example ===")

    cache_config = CacheConfig(backend="memory", default_ttl=300, max_size=1024)
    memory_cache = CacheMechanism(cache_config)

    # Set values
    memory_cache.set("key1", "value1", ttl=60)
    memory_cache.set("key2", {"data": "test"}, ttl=120)
    print("Set cache values")

    # Get values
    value1 = memory_cache.get("key1")
    value2 = memory_cache.get("key2")
    print(f"Retrieved key1: {value1}")
    print(f"Retrieved key2: {value2}")

    # Check if key exists (by checking if get returns None)
    exists = memory_cache.get("key1") is not None
    print(f"key1 exists: {exists}")

    # Delete key
    memory_cache.delete("key1")
    print("Deleted key1")

    # Get after deletion
    value1_after = memory_cache.get("key1")
    print(f"key1 after deletion: {value1_after}")

    # 2. Redis Cache Example (if available)
    print("\n=== Redis Cache Example ===")

    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6379))

    try:
        redis_config = CacheConfig(
            backend="dragonfly", dragonfly_url=f"redis://{redis_host}:{redis_port}/0"
        )
        redis_cache = CacheMechanism(redis_config)

        # Test Redis connection
        redis_cache.set("redis_key", "redis_value", ttl=300)
        redis_value = redis_cache.get("redis_key")
        print(f"Redis cache working: {redis_value}")

    except Exception as e:
        print(f"Redis not available (expected in example): {type(e).__name__}")
        print("To use Redis, install redis and start Redis server")

    # 3. LLM Response Caching
    print("\n=== LLM Response Caching ===")

    # Cache LLM response
    llm_cache_key = "llm:prompt:explain_ai"
    llm_response = "AI stands for Artificial Intelligence..."

    memory_cache.set(llm_cache_key, llm_response, ttl=3600)
    print("Cached LLM response")

    # Retrieve cached response
    cached_response = memory_cache.get(llm_cache_key)
    if cached_response:
        print(f"Cached LLM response: {cached_response[:50]}...")

    # 4. Embedding Caching
    print("\n=== Embedding Caching ===")

    embedding = [0.1] * 1536
    embedding_key = "embedding:text:hello_world"

    memory_cache.set(embedding_key, embedding, ttl=86400)  # 24 hours
    print("Cached embedding")

    cached_embedding = memory_cache.get(embedding_key)
    if cached_embedding:
        print(f"Cached embedding dimension: {len(cached_embedding)}")

    # 5. Cache Management
    print("\n=== Cache Management ===")

    # Note: CacheMechanism doesn't have built-in statistics
    print("Cache statistics: Not available in current implementation")
    
    # Clear specific keys using delete
    print("Clearing cache by deleting keys...")
    memory_cache.delete("key2")
    memory_cache.delete(llm_cache_key)
    memory_cache.delete(embedding_key)
    print("Deleted cache keys")

    print("\n✅ Cache example completed successfully!")


if __name__ == "__main__":
    main()
