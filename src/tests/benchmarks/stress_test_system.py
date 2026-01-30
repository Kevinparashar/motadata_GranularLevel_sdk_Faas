"""
Stress Testing for System Components

Tests system behavior under extreme load and stress conditions.
"""

import asyncio
import time
from typing import Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.core.cache_mechanism import CacheConfig, CacheMechanism
from src.core.litellm_gateway import GatewayConfig, LiteLLMGateway
from src.core.postgresql_database.connection import DatabaseConfig, DatabaseConnection


class StressTestResults:
    """Results from stress testing."""

    def __init__(self):
        """Initialize results."""
        self.operation_times: List[float] = []
        self.success_count = 0
        self.error_count = 0
        self.errors: List[str] = []

    def record_operation(self, latency: float, success: bool, error: str = None):
        """Record an operation."""
        self.operation_times.append(latency)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
            if error:
                self.errors.append(error)

    def get_stats(self) -> Dict[str, float]:
        """Get statistics."""
        if not self.operation_times:
            return {}

        sorted_times = sorted(self.operation_times)
        total = self.success_count + self.error_count
        return {
            "total_operations": total,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": (self.success_count / total * 100) if total > 0 else 0,
            "avg_latency": sum(self.operation_times) / len(self.operation_times),
            "max_latency": max(self.operation_times),
            "p95": sorted_times[int(len(sorted_times) * 0.95)],
            "p99": sorted_times[int(len(sorted_times) * 0.99)],
        }


@pytest.mark.benchmark
@pytest.mark.stress_test
class TestSystemStressTests:
    """Stress tests for system components."""

    @pytest.fixture
    def mock_gateway(self):
        """Mock gateway."""
        with patch("src.core.litellm_gateway.gateway.litellm") as mock_litellm:
            cache = CacheMechanism(CacheConfig(default_ttl=3600))
            config = GatewayConfig(enable_caching=True, cache=cache)
            gateway = LiteLLMGateway(config=config)
            gateway._litellm = mock_litellm

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Response"
            mock_response.model = "gpt-4"
            mock_litellm.acompletion = AsyncMock(return_value=mock_response)

            return gateway

    @pytest.mark.asyncio
    async def test_gateway_stress(self, mock_gateway):
        """Stress test gateway with high concurrent load."""
        results = StressTestResults()
        concurrent_requests = 50
        requests_per_worker = 20
        total_requests = concurrent_requests * requests_per_worker

        async def worker(worker_id: int):
            """Worker function for concurrent requests."""
            for i in range(requests_per_worker):
                try:
                    start = time.time()
                    await mock_gateway.generate_async(
                        prompt=f"Stress test {worker_id}-{i}",
                        model="gpt-4",
                        tenant_id="stress_tenant",
                    )
                    latency = time.time() - start
                    results.record_operation(latency, True)
                except Exception as e:
                    results.record_operation(0, False, str(e))

        # Run stress test
        start = time.time()
        tasks = [worker(i) for i in range(concurrent_requests)]
        await asyncio.gather(*tasks)
        elapsed = time.time() - start

        stats = results.get_stats()
        stats["total_time"] = elapsed
        stats["throughput"] = total_requests / elapsed

        print(f"\nGateway Stress Test:")
        print(f"  Concurrent workers: {concurrent_requests}")
        print(f"  Requests per worker: {requests_per_worker}")
        print(f"  Total requests: {total_requests}")
        print(f"  Success rate: {stats['success_rate']:.1f}%")
        print(f"  Throughput: {stats['throughput']:.2f} req/sec")
        print(f"  P95 latency: {stats['p95']*1000:.2f}ms")

        # Should handle stress with > 90% success
        assert stats["success_rate"] > 90.0

    def test_cache_stress(self):
        """Stress test cache with high volume operations."""
        cache = CacheMechanism(CacheConfig(default_ttl=3600, max_size=1000))
        results = StressTestResults()
        operations = 10000

        # Mix of set, get, and delete operations
        start = time.time()
        for i in range(operations):
            try:
                op_start = time.time()

                if i % 3 == 0:
                    # Set operation
                    cache.set(f"key_{i}", f"value_{i}", ttl=3600)
                elif i % 3 == 1:
                    # Get operation
                    cache.get(f"key_{i-1}")
                else:
                    # Delete operation
                    cache.delete(f"key_{i-2}")

                latency = time.time() - op_start
                results.record_operation(latency, True)
            except Exception as e:
                results.record_operation(0, False, str(e))

        elapsed = time.time() - start
        stats = results.get_stats()
        stats["total_time"] = elapsed
        stats["throughput"] = operations / elapsed

        print(f"\nCache Stress Test:")
        print(f"  Total operations: {operations}")
        print(f"  Success rate: {stats['success_rate']:.1f}%")
        print(f"  Throughput: {stats['throughput']:.0f} ops/sec")
        print(f"  Avg latency: {stats['avg_latency']*1000:.3f}ms")

        assert stats["success_rate"] > 99.0
        assert stats["throughput"] > 1000  # > 1k ops/sec

    @pytest.mark.asyncio
    async def test_memory_pressure(self, mock_gateway):
        """Stress test memory under pressure."""
        from src.core.agno_agent_framework.memory import AgentMemory

        memory = AgentMemory(
            agent_id="stress_test",
            max_episodic=100,  # Small limit for stress test
            max_semantic=200,
        )

        results = StressTestResults()
        operations = 500  # More than max_episodic

        # Store many memories to trigger pressure
        start = time.time()
        for i in range(operations):
            try:
                op_start = time.time()
                memory.store(content=f"Memory {i}", memory_type="episodic", metadata={"index": i})
                latency = time.time() - op_start
                results.record_operation(latency, True)
            except Exception as e:
                results.record_operation(0, False, str(e))

        elapsed = time.time() - start
        stats = results.get_stats()

        # Check memory size
        current_size = len(memory.episodic_memory)

        print(f"\nMemory Pressure Test:")
        print(f"  Operations: {operations}")
        print(f"  Max episodic: 100")
        print(f"  Current size: {current_size}")
        print(f"  Success rate: {stats['success_rate']:.1f}%")
        print(f"  Avg latency: {stats['avg_latency']*1000:.3f}ms")

        # Memory should be bounded
        assert current_size <= 100
        assert stats["success_rate"] > 95.0

    @pytest.mark.asyncio
    async def test_system_integration_stress(self, mock_gateway):
        """Stress test system integration (Gateway + Cache + Memory)."""
        cache = CacheMechanism(CacheConfig(default_ttl=3600))
        config = GatewayConfig(enable_caching=True, cache=cache)
        mock_gateway.config = config
        mock_gateway.cache = cache

        results = StressTestResults()
        concurrent_operations = 30
        operations_per_worker = 10

        async def worker(worker_id: int):
            """Worker for integrated operations."""
            for i in range(operations_per_worker):
                try:
                    start = time.time()
                    await mock_gateway.generate_async(
                        prompt=f"Integration stress {worker_id}-{i}",
                        model="gpt-4",
                        tenant_id="stress_tenant",
                    )
                    latency = time.time() - start
                    results.record_operation(latency, True)
                except Exception as e:
                    results.record_operation(0, False, str(e))

        start = time.time()
        tasks = [worker(i) for i in range(concurrent_operations)]
        await asyncio.gather(*tasks)
        elapsed = time.time() - start

        stats = results.get_stats()
        stats["total_time"] = elapsed

        print(f"\nSystem Integration Stress Test:")
        print(f"  Concurrent workers: {concurrent_operations}")
        print(f"  Operations per worker: {operations_per_worker}")
        print(f"  Total operations: {stats['total_operations']}")
        print(f"  Success rate: {stats['success_rate']:.1f}%")
        print(f"  P95 latency: {stats['p95']*1000:.2f}ms")

        assert stats["success_rate"] > 90.0
