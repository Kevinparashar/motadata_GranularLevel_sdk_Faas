"""
Performance Benchmarks for RAG System

Measures query latency, retrieval speed, and memory integration performance.
"""


import asyncio
import time
from typing import Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.litellm_gateway import GatewayConfig, LiteLLMGateway
from src.core.postgresql_database.connection import DatabaseConfig, DatabaseConnection
from src.core.rag import RAGSystem


class BenchmarkRAG:
    """Benchmark suite for RAG System."""

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
class TestRAGBenchmarks:
    """Performance benchmarks for RAG System."""

    @pytest.fixture
    def mock_db(self):
        """Mock database connection."""
        with patch("src.core.postgresql_database.connection.psycopg2") as mock_psycopg2:
            mock_conn = MagicMock()
            mock_psycopg2.connect.return_value = mock_conn
            db = DatabaseConnection(
                DatabaseConfig(
                    host="localhost", port=5432, database="test", user="test", password="test"
                )
            )
            return db

    @pytest.fixture
    def mock_gateway(self):
        """Mock gateway."""
        with patch("src.core.litellm_gateway.gateway.litellm") as mock_litellm:
            config = GatewayConfig(enable_caching=True)
            gateway = LiteLLMGateway(config=config)
            gateway._litellm = mock_litellm  # type: ignore[attr-defined]

            # Mock embedding response
            mock_embedding = MagicMock()
            mock_embedding.data = [MagicMock(embedding=[0.1] * 1536)]
            mock_litellm.aembedding = AsyncMock(return_value=mock_embedding)

            # Mock generation response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Generated answer"
            mock_response.model = "gpt-4"
            mock_litellm.acompletion = AsyncMock(return_value=mock_response)

            return gateway

    @pytest.fixture
    def rag_with_memory(self, mock_db, mock_gateway):
        """RAG system with memory enabled."""
        return RAGSystem(
            db=mock_db,
            gateway=mock_gateway,
            enable_memory=True,
            memory_config={"max_episodic": 100, "max_semantic": 200},
        )

    @pytest.fixture
    def rag_without_memory(self, mock_db, mock_gateway):
        """RAG system without memory."""
        return RAGSystem(db=mock_db, gateway=mock_gateway, enable_memory=False)

    @pytest.mark.asyncio
    async def test_query_latency(self, rag_without_memory):
        """Benchmark query latency."""
        benchmark = BenchmarkRAG()
        iterations = 10

        for i in range(iterations):
            start = time.time()
            await rag_without_memory.query_async(
                query=f"Test query {i}", tenant_id="benchmark_tenant"
            )
            latency = time.time() - start
            benchmark.record_latency("query_async", latency)

        stats = benchmark.get_stats("query_async")
        print(f"\nQuery Latency Stats: {stats}")

        assert stats["count"] == iterations
        assert stats["avg"] < 10.0  # Should complete in < 10 seconds (mocked)

    @pytest.mark.asyncio
    async def test_retrieval_speed(self, rag_without_memory):
        """Benchmark document retrieval speed."""
        benchmark = BenchmarkRAG()
        iterations = 20

        for _ in range(iterations):
            start = time.time()
            # Simulate retrieval operation
            await rag_without_memory.query_async(
                query="Retrieval speed test", tenant_id="benchmark_tenant"
            )
            latency = time.time() - start
            benchmark.record_latency("retrieval", latency)

        stats = benchmark.get_stats("retrieval")
        print(f"\nRetrieval Speed Stats: {stats}")

        assert stats["count"] == iterations

    @pytest.mark.asyncio
    async def test_memory_integration_performance(self, rag_with_memory):
        """Benchmark memory integration overhead."""
        benchmark = BenchmarkRAG()
        iterations = 10

        user_id = "benchmark_user"
        conversation_id = "benchmark_conv"

        # First query (no memory context)
        start = time.time()
        await rag_with_memory.query_async(
            query="First query",
            user_id=user_id,
            conversation_id=conversation_id,
            tenant_id="benchmark_tenant",
        )
        first_query_time = time.time() - start

        # Subsequent queries (with memory context)
        for i in range(iterations):
            start = time.time()
            await rag_with_memory.query_async(
                query=f"Follow-up query {i}",
                user_id=user_id,
                conversation_id=conversation_id,
                tenant_id="benchmark_tenant",
            )
            latency = time.time() - start
            benchmark.record_latency("query_with_memory", latency)

        stats = benchmark.get_stats("query_with_memory")
        print("\nMemory Integration Performance:")
        print(f"  First query (no memory): {first_query_time*1000:.2f}ms")
        print(f"  Subsequent queries (with memory): {stats['avg']*1000:.2f}ms")
        print(f"  Overhead: {(stats['avg'] - first_query_time)*1000:.2f}ms")

        # Memory overhead should be minimal (< 100ms)
        overhead = stats["avg"] - first_query_time
        assert overhead < 0.1  # < 100ms overhead

    @pytest.mark.asyncio
    async def test_concurrent_queries(self, rag_without_memory):
        """Benchmark concurrent query handling."""
        concurrent_requests = 5
        total_requests = 20

        async def make_query(query_num: int):
            """Make a single query."""
            await rag_without_memory.query_async(
                query=f"Concurrent query {query_num}", tenant_id="benchmark_tenant"
            )

        start = time.time()

        # Run concurrent queries
        tasks = []
        for i in range(total_requests):
            tasks.append(make_query(i))
            if len(tasks) >= concurrent_requests:
                await asyncio.gather(*tasks)
                tasks = []

        if tasks:
            await asyncio.gather(*tasks)

        elapsed = time.time() - start
        throughput = total_requests / elapsed

        print("\nConcurrent Query Performance:")
        print(f"  Throughput: {throughput:.2f} queries/second")
        print(f"  Total time: {elapsed:.2f} seconds")
        print(f"  Concurrent requests: {concurrent_requests}")

        assert throughput > 0.5  # Should handle at least 0.5 queries/sec
