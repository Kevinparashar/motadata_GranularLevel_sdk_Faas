"""
Performance Benchmarks for LiteLLM Gateway

Measures LLM call latency, throughput, and cache performance.
"""

import asyncio
import time
from typing import List, Dict, Any
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.core.litellm_gateway import LiteLLMGateway, GatewayConfig
from src.core.cache_mechanism import CacheMechanism, CacheConfig


class BenchmarkGateway:
    """Benchmark suite for LiteLLM Gateway."""

    def __init__(self):
        """Initialize benchmark suite."""
        self.results: Dict[str, List[float]] = {}

    def record_latency(self, operation: str, latency: float):
        """Record operation latency."""
        if operation not in self.results:
            self.results[operation] = []
        self.results[operation].append(latency)

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
            "p99": sorted(latencies)[int(len(latencies) * 0.99)],
        }


@pytest.mark.benchmark
class TestGatewayBenchmarks:
    """Performance benchmarks for Gateway."""

    @pytest.fixture
    def gateway_with_cache(self):
        """Gateway with cache enabled."""
        cache = CacheMechanism(CacheConfig(default_ttl=3600))
        config = GatewayConfig(
            enable_caching=True,
            cache_ttl=3600,
            cache=cache
        )
        with patch('src.core.litellm_gateway.gateway.litellm') as mock_litellm:
            gateway = LiteLLMGateway(config=config)
            gateway._litellm = mock_litellm
            return gateway, mock_litellm

    @pytest.fixture
    def gateway_without_cache(self):
        """Gateway without cache."""
        config = GatewayConfig(enable_caching=False)
        with patch('src.core.litellm_gateway.gateway.litellm') as mock_litellm:
            gateway = LiteLLMGateway(config=config)
            gateway._litellm = mock_litellm
            return gateway, mock_litellm

    @pytest.mark.asyncio
    async def test_generate_latency(self, gateway_without_cache):
        """Benchmark text generation latency."""
        gateway, mock_litellm = gateway_without_cache
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated text"
        mock_response.model = "gpt-4"
        mock_litellm.acompletion = AsyncMock(return_value=mock_response)
        
        benchmark = BenchmarkGateway()
        iterations = 10
        
        for _ in range(iterations):
            start = time.time()
            await gateway.generate_async(
                prompt="Test prompt for benchmarking",
                model="gpt-4",
                tenant_id="benchmark_tenant"
            )
            latency = time.time() - start
            benchmark.record_latency("generate_async", latency)
        
        stats = benchmark.get_stats("generate_async")
        print(f"\nGenerate Latency Stats: {stats}")
        
        # Assertions
        assert stats["count"] == iterations
        assert stats["avg"] < 5.0  # Should complete in < 5 seconds (mocked)

    @pytest.mark.asyncio
    async def test_cache_hit_latency(self, gateway_with_cache):
        """Benchmark cache hit latency (should be very fast)."""
        gateway, mock_litellm = gateway_with_cache
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Cached response"
        mock_response.model = "gpt-4"
        mock_litellm.acompletion = AsyncMock(return_value=mock_response)
        
        # First call - cache miss (makes API call)
        await gateway.generate_async(
            prompt="Cache test prompt",
            model="gpt-4",
            tenant_id="benchmark_tenant"
        )
        
        benchmark = BenchmarkGateway()
        iterations = 100  # More iterations for cache hits
        
        # Subsequent calls - cache hits (no API call)
        for _ in range(iterations):
            start = time.time()
            await gateway.generate_async(
                prompt="Cache test prompt",
                model="gpt-4",
                tenant_id="benchmark_tenant"
            )
            latency = time.time() - start
            benchmark.record_latency("cache_hit", latency)
        
        stats = benchmark.get_stats("cache_hit")
        print(f"\nCache Hit Latency Stats: {stats}")
        
        # Cache hits should be very fast (< 10ms)
        assert stats["avg"] < 0.01  # < 10ms
        assert stats["p95"] < 0.02  # p95 < 20ms

    @pytest.mark.asyncio
    async def test_throughput(self, gateway_without_cache):
        """Benchmark throughput (requests per second)."""
        gateway, mock_litellm = gateway_without_cache
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.model = "gpt-4"
        mock_litellm.acompletion = AsyncMock(return_value=mock_response)
        
        concurrent_requests = 10
        total_requests = 50
        
        async def make_request():
            """Make a single request."""
            await gateway.generate_async(
                prompt="Throughput test",
                model="gpt-4",
                tenant_id="benchmark_tenant"
            )
        
        start = time.time()
        
        # Run concurrent requests
        tasks = []
        for _ in range(total_requests):
            tasks.append(make_request())
            if len(tasks) >= concurrent_requests:
                await asyncio.gather(*tasks)
                tasks = []
        
        if tasks:
            await asyncio.gather(*tasks)
        
        elapsed = time.time() - start
        throughput = total_requests / elapsed
        
        print(f"\nThroughput: {throughput:.2f} requests/second")
        print(f"Total time: {elapsed:.2f} seconds")
        print(f"Total requests: {total_requests}")
        
        # Assertions
        assert throughput > 1.0  # Should handle at least 1 req/sec

    @pytest.mark.asyncio
    async def test_cache_performance_improvement(self, gateway_with_cache):
        """Compare performance with and without cache."""
        gateway, mock_litellm = gateway_with_cache
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.model = "gpt-4"
        mock_litellm.acompletion = AsyncMock(return_value=mock_response)
        
        prompt = "Cache performance test"
        iterations = 20
        
        # First call (cache miss)
        start = time.time()
        await gateway.generate_async(
            prompt=prompt,
            model="gpt-4",
            tenant_id="benchmark_tenant"
        )
        cache_miss_time = time.time() - start
        
        # Subsequent calls (cache hits)
        cache_hit_times = []
        for _ in range(iterations):
            start = time.time()
            await gateway.generate_async(
                prompt=prompt,
                model="gpt-4",
                tenant_id="benchmark_tenant"
            )
            cache_hit_times.append(time.time() - start)
        
        avg_cache_hit = sum(cache_hit_times) / len(cache_hit_times)
        improvement = ((cache_miss_time - avg_cache_hit) / cache_miss_time) * 100
        
        print(f"\nCache Performance Improvement:")
        print(f"  Cache miss: {cache_miss_time*1000:.2f}ms")
        print(f"  Cache hit (avg): {avg_cache_hit*1000:.2f}ms")
        print(f"  Improvement: {improvement:.1f}%")
        
        # Cache should provide significant improvement
        assert improvement > 50  # At least 50% improvement

