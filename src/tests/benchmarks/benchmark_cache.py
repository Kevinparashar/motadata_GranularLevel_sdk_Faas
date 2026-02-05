"""
Performance Benchmarks for Cache Mechanism

Measures cache hit rates, performance, and TTL behavior.
"""


import asyncio
import time
from typing import Dict, List

import pytest

from src.core.cache_mechanism import CacheConfig, CacheMechanism


class BenchmarkCache:
    """Benchmark suite for Cache Mechanism."""

    def __init__(self):
        """Initialize benchmark suite."""
        self.results: Dict[str, List[float]] = {}
        self.hits = 0
        self.misses = 0

    def record_latency(self, operation: str, latency: float):
        """Record operation latency."""
        if operation not in self.results:
            self.results[operation] = []
        self.results[operation].append(latency)

    def record_hit(self):
        """Record cache hit."""
        self.hits += 1

    def record_miss(self):
        """Record cache miss."""
        self.misses += 1

    def get_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return (self.hits / total) * 100

    def get_stats(self, operation: str) -> Dict[str, float]:
        """Get statistics for an operation."""
        if operation not in self.results or not self.results[operation]:
            return {}

        latencies = self.results[operation]
        return {
            "count": len(latencies),
            "min": min(latencies),
            "max": max(latencies),
            "avg": sum(latencies) / len(latencies),
            "p50": sorted(latencies)[len(latencies) // 2],
            "p95": sorted(latencies)[int(len(latencies) * 0.95)],
        }


@pytest.mark.benchmark
class TestCacheBenchmarks:
    """Performance benchmarks for Cache Mechanism."""

    @pytest.fixture
    def cache(self):
        """Cache mechanism fixture."""
        return CacheMechanism(CacheConfig(default_ttl=3600, max_size=10000))

    @pytest.mark.asyncio
    async def test_set_get_latency(self, cache):
        """Benchmark set/get operations."""
        benchmark = BenchmarkCache()
        iterations = 1000

        # Benchmark set operations
        for i in range(iterations):
            start = time.time()
            await cache.set(f"key_{i}", f"value_{i}", ttl=3600)
            latency = time.time() - start
            benchmark.record_latency("set", latency)

        # Benchmark get operations
        for i in range(iterations):
            start = time.time()
            value = await cache.get(f"key_{i}")
            latency = time.time() - start
            benchmark.record_latency("get", latency)
            assert value == f"value_{i}"

        set_stats = benchmark.get_stats("set")
        get_stats = benchmark.get_stats("get")

        print("\nCache Operation Latency:")
        print(f"  Set: avg={set_stats['avg']*1000:.3f}ms, p95={set_stats['p95']*1000:.3f}ms")
        print(f"  Get: avg={get_stats['avg']*1000:.3f}ms, p95={get_stats['p95']*1000:.3f}ms")

        # Cache operations should be very fast
        assert set_stats["avg"] < 0.001  # < 1ms
        assert get_stats["avg"] < 0.001  # < 1ms

    @pytest.mark.asyncio
    async def test_cache_hit_rate(self, cache):
        """Benchmark cache hit rate."""
        benchmark = BenchmarkCache()
        iterations = 100

        # Fill cache
        for i in range(iterations):
            await cache.set(f"key_{i}", f"value_{i}", ttl=3600)

        # Test hit rate with repeated access
        for _ in range(5):  # 5 rounds
            for i in range(iterations):
                value = await cache.get(f"key_{i}")
                if value:
                    benchmark.record_hit()
                else:
                    benchmark.record_miss()

        hit_rate = benchmark.get_hit_rate()
        print(f"\nCache Hit Rate: {hit_rate:.1f}%")

        # Should have high hit rate (> 95%)
        assert hit_rate > 95.0

    @pytest.mark.asyncio
    async def test_cache_throughput(self, cache):
        """Benchmark cache throughput (operations per second)."""
        iterations = 10000

        start = time.time()

        # Mix of set and get operations
        for i in range(iterations):
            await cache.set(f"key_{i}", f"value_{i}", ttl=3600)
            await cache.get(f"key_{i}")

        elapsed = time.time() - start
        throughput = (iterations * 2) / elapsed  # 2 ops per iteration (set + get)

        print(f"\nCache Throughput: {throughput:.0f} operations/second")
        print(f"  Total operations: {iterations * 2}")
        print(f"  Time: {elapsed:.2f} seconds")

        # Should handle high throughput (> 10k ops/sec)
        assert throughput > 10000

    @pytest.mark.asyncio
    async def test_cache_eviction_performance(self, cache):
        """Benchmark cache eviction performance."""
        max_size = 1000
        eviction_cache = CacheMechanism(CacheConfig(default_ttl=3600, max_size=max_size))

        # Fill cache beyond max size
        overflow = 500
        total_keys = max_size + overflow

        start = time.time()
        for i in range(total_keys):
            await eviction_cache.set(f"key_{i}", f"value_{i}", ttl=3600)
        fill_time = time.time() - start

        # Check that eviction worked
        current_size = 0
        for k in range(total_keys):
            if await eviction_cache.get(f"key_{k}"):
                current_size += 1

        print("\nCache Eviction Performance:")
        print(f"  Max size: {max_size}")
        print(f"  Keys inserted: {total_keys}")
        print(f"  Current size: {current_size}")
        print(f"  Fill time: {fill_time*1000:.2f}ms")

        # Should evict old entries
        assert current_size <= max_size
        assert fill_time < 1.0  # Should complete quickly

    @pytest.mark.asyncio
    async def test_ttl_expiration_performance(self, cache):
        """Benchmark TTL expiration performance."""
        ttl_cache = CacheMechanism(CacheConfig(default_ttl=1, max_size=1000))  # 1 second TTL

        # Set values with short TTL
        for i in range(100):
            await ttl_cache.set(f"key_{i}", f"value_{i}", ttl=1)

        # Wait for expiration
        await asyncio.sleep(1.1)

        start = time.time()
        expired_count = 0
        for i in range(100):
            if await ttl_cache.get(f"key_{i}") is None:
                expired_count += 1
        check_time = time.time() - start

        print("\nTTL Expiration Performance:")
        print(f"  Expired keys: {expired_count}/100")
        print(f"  Check time: {check_time*1000:.2f}ms")

        # Most keys should be expired
        assert expired_count > 90
        assert check_time < 0.1  # Should check quickly
