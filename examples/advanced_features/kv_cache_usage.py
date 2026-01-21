"""
KV Cache Usage Example

Demonstrates how to use KV cache for optimizing LLM generation,
especially useful for long contexts and multi-turn conversations.
"""

from src.core.litellm_gateway import create_gateway, KVCacheManager
from src.core.cache_mechanism import create_cache_mechanism


def main():
    # Initialize cache
    cache = create_cache_mechanism()
    
    # Create gateway with KV cache enabled
    gateway = create_gateway(
        api_keys={"openai": "sk-..."},
        enable_kv_cache=True,
        kv_cache_ttl=3600  # 1 hour
    )
    
    # Example 1: Generate with KV cache (automatic)
    print("Generating response with KV cache...")
    response1 = gateway.generate(
        prompt="Explain quantum computing in detail",
        model="gpt-4",
        max_tokens=1000
    )
    print(f"Response: {response1.text[:200]}...")
    
    # Example 2: Check KV cache statistics
    if gateway.kv_cache:
        stats = gateway.kv_cache.get_cache_stats()
        print(f"\nKV Cache Statistics:")
        print(f"  Enabled: {stats['enabled']}")
        print(f"  Memory entries: {stats['memory_entries']}")
        print(f"  Memory size: {stats['memory_size_mb']} MB")
        print(f"  Has persistent cache: {stats['has_persistent_cache']}")
    
    # Example 3: Manual KV cache management
    print("\nManual KV cache management...")
    kv_cache = KVCacheManager(cache=cache, enable_kv_cache=True)
    
    # Generate cache key
    cache_key = kv_cache.generate_cache_key(
        prompt="What is machine learning?",
        model="gpt-4"
    )
    print(f"Cache key: {cache_key}")
    
    # Check if cached
    cached_entry = kv_cache.get_kv_cache(cache_key)
    if cached_entry:
        print("KV cache hit!")
    else:
        print("KV cache miss - would generate and cache")
    
    # Example 4: Invalidate KV cache
    print("\nInvalidating KV cache...")
    invalidated = kv_cache.invalidate_kv_cache(model="gpt-4")
    print(f"Invalidated {invalidated} entries")
    
    # Example 5: Clear all KV cache
    print("\nClearing all KV cache...")
    cleared = kv_cache.clear_cache()
    print(f"Cleared {cleared} entries")


if __name__ == "__main__":
    main()

