"""
Performance Benchmarks for Agent Framework

Measures agent task execution time and memory performance.
"""

import asyncio
import time
from typing import Dict, List
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock

from src.core.agno_agent_framework import Agent
from src.core.agno_agent_framework.memory import AgentMemory
from src.core.litellm_gateway import LiteLLMGateway, GatewayConfig


class BenchmarkAgent:
    """Benchmark suite for Agent Framework."""

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
        }


@pytest.mark.benchmark
class TestAgentBenchmarks:
    """Performance benchmarks for Agent Framework."""

    @pytest.fixture
    def mock_gateway(self):
        """Mock gateway."""
        with patch('src.core.litellm_gateway.gateway.litellm') as mock_litellm:
            config = GatewayConfig(enable_caching=True)
            gateway = LiteLLMGateway(config=config)
            gateway._litellm = mock_litellm
            
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Agent response"
            mock_response.model = "gpt-4"
            mock_litellm.acompletion = AsyncMock(return_value=mock_response)
            
            return gateway

    @pytest.fixture
    def agent_with_memory(self, mock_gateway):
        """Agent with memory enabled."""
        agent = Agent(
            agent_id="benchmark_agent",
            name="Benchmark Agent",
            gateway=mock_gateway
        )
        agent.attach_memory(
            persistence_path=None,
            max_episodic=100,
            max_semantic=200
        )
        return agent

    @pytest.fixture
    def agent_without_memory(self, mock_gateway):
        """Agent without memory."""
        return Agent(
            agent_id="benchmark_agent",
            name="Benchmark Agent",
            gateway=mock_gateway
        )

    @pytest.mark.asyncio
    async def test_task_execution_latency(self, agent_without_memory):
        """Benchmark task execution latency."""
        benchmark = BenchmarkAgent()
        iterations = 10
        
        for i in range(iterations):
            start = time.time()
            await agent_without_memory.execute_task_async(
                task_type="llm_query",
                parameters={
                    "prompt": f"Test task {i}",
                    "model": "gpt-4"
                },
                tenant_id="benchmark_tenant"
            )
            latency = time.time() - start
            benchmark.record_latency("task_execution", latency)
        
        stats = benchmark.get_stats("task_execution")
        print(f"\nTask Execution Latency Stats: {stats}")
        
        assert stats["count"] == iterations
        assert stats["avg"] < 5.0  # Should complete in < 5 seconds (mocked)

    @pytest.mark.asyncio
    async def test_memory_overhead(self, agent_with_memory, agent_without_memory):
        """Benchmark memory overhead on task execution."""
        benchmark = BenchmarkAgent()
        iterations = 10
        
        # Tasks without memory
        for i in range(iterations):
            start = time.time()
            await agent_without_memory.execute_task_async(
                task_type="llm_query",
                parameters={"prompt": f"Task {i}"},
                tenant_id="benchmark_tenant"
            )
            latency = time.time() - start
            benchmark.record_latency("without_memory", latency)
        
        # Tasks with memory
        for i in range(iterations):
            start = time.time()
            await agent_with_memory.execute_task_async(
                task_type="llm_query",
                parameters={"prompt": f"Task {i}"},
                tenant_id="benchmark_tenant"
            )
            latency = time.time() - start
            benchmark.record_latency("with_memory", latency)
        
        without_stats = benchmark.get_stats("without_memory")
        with_stats = benchmark.get_stats("with_memory")
        
        overhead = with_stats["avg"] - without_stats["avg"]
        overhead_pct = (overhead / without_stats["avg"]) * 100
        
        print(f"\nMemory Overhead:")
        print(f"  Without memory: {without_stats['avg']*1000:.2f}ms")
        print(f"  With memory: {with_stats['avg']*1000:.2f}ms")
        print(f"  Overhead: {overhead*1000:.2f}ms ({overhead_pct:.1f}%)")
        
        # Memory overhead should be minimal (< 20%)
        assert overhead_pct < 20

    @pytest.mark.asyncio
    async def test_concurrent_tasks(self, agent_without_memory):
        """Benchmark concurrent task execution."""
        concurrent_tasks = 5
        total_tasks = 20
        
        async def execute_task(task_num: int):
            """Execute a single task."""
            await agent_without_memory.execute_task_async(
                task_type="llm_query",
                parameters={"prompt": f"Concurrent task {task_num}"},
                tenant_id="benchmark_tenant"
            )
        
        start = time.time()
        
        # Run concurrent tasks
        tasks = []
        for i in range(total_tasks):
            tasks.append(execute_task(i))
            if len(tasks) >= concurrent_tasks:
                await asyncio.gather(*tasks)
                tasks = []
        
        if tasks:
            await asyncio.gather(*tasks)
        
        elapsed = time.time() - start
        throughput = total_tasks / elapsed
        
        print(f"\nConcurrent Task Performance:")
        print(f"  Throughput: {throughput:.2f} tasks/second")
        print(f"  Total time: {elapsed:.2f} seconds")
        print(f"  Concurrent tasks: {concurrent_tasks}")
        
        assert throughput > 0.5  # Should handle at least 0.5 tasks/sec

