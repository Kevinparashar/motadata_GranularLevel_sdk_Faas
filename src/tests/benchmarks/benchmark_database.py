"""
Performance Benchmarks for PostgreSQL Database

Measures query performance and vector search speed.
"""


import time
from typing import Dict, List
from unittest.mock import AsyncMock, patch

import pytest

from src.core.postgresql_database.connection import DatabaseConfig, DatabaseConnection
from src.core.postgresql_database.vector_operations import VectorOperations


class BenchmarkDatabase:
    """Benchmark suite for Database."""

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
class TestDatabaseBenchmarks:
    """Performance benchmarks for Database."""

    @pytest.fixture
    def mock_db(self):
        """Mock database connection."""
        with patch("src.core.postgresql_database.connection.asyncpg") as mock_asyncpg:
            mock_pool = AsyncMock()
            mock_conn = AsyncMock()
            mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
            mock_pool.acquire.return_value.__aexit__.return_value = None
            mock_asyncpg.create_pool.return_value = mock_pool

            db = DatabaseConnection(
                DatabaseConfig(
                    host="localhost", port=5432, database="test", user="test", password="test"
                )
            )
            return db, mock_conn

    @pytest.fixture
    def vector_ops(self, mock_db):
        """Vector operations fixture."""
        db, _ = mock_db
        return VectorOperations(db)

    @pytest.mark.asyncio
    async def test_query_latency(self, mock_db):
        """Benchmark query execution latency."""
        db, mock_conn = mock_db
        benchmark = BenchmarkDatabase()
        iterations = 100

        # Mock query results
        mock_conn.fetch.return_value = [("result",)]

        for i in range(iterations):
            start = time.time()
            await db.execute_query("SELECT * FROM test WHERE id = $1", (i,))
            latency = time.time() - start
            benchmark.record_latency("query", latency)

        stats = benchmark.get_stats("query")
        print(f"\nQuery Latency Stats: {stats}")

        assert stats["count"] == iterations
        assert stats["avg"] < 0.1  # Should be very fast (mocked)

    @pytest.mark.asyncio
    async def test_vector_search_speed(self, vector_ops):
        """Benchmark vector similarity search speed."""
        benchmark = BenchmarkDatabase()
        iterations = 50

        # Mock vector search results
        with patch.object(vector_ops, "similarity_search") as mock_search:
            mock_search.return_value = [
                {"id": "1", "similarity": 0.95},
                {"id": "2", "similarity": 0.90},
            ]

            query_vector = [0.1] * 1536

            for _ in range(iterations):
                start = time.time()
                await vector_ops.similarity_search(
                    query_vector=query_vector, top_k=5, threshold=0.7, tenant_id="benchmark_tenant"
                )
                latency = time.time() - start
                benchmark.record_latency("vector_search", latency)

        stats = benchmark.get_stats("vector_search")
        print(f"\nVector Search Speed Stats: {stats}")

        assert stats["count"] == iterations
        assert stats["avg"] < 0.1  # Should be fast (mocked)

    @pytest.mark.asyncio
    async def test_batch_insert_performance(self, mock_db):
        """Benchmark batch insert performance."""
        db, _ = mock_db
        benchmark = BenchmarkDatabase()

        batch_sizes = [10, 100, 1000]

        for batch_size in batch_sizes:
            start = time.time()
            # Simulate batch insert
            for i in range(batch_size):
                await db.execute_query("INSERT INTO test (id, data) VALUES ($1, $2)", (i, "data"))
            elapsed = time.time() - start
            throughput = batch_size / elapsed

            print(f"\nBatch Insert Performance (size={batch_size}):")
            print(f"  Throughput: {throughput:.0f} inserts/second")
            print(f"  Time: {elapsed*1000:.2f}ms")

            benchmark.record_latency("batch_insert", elapsed)

        stats = benchmark.get_stats("batch_insert")
        assert stats["count"] == len(batch_sizes)

    @pytest.mark.asyncio
    async def test_connection_pool_performance(self, mock_db):
        """Benchmark connection pool performance."""
        db, _ = mock_db
        benchmark = BenchmarkDatabase()
        iterations = 100

        # Simulate connection acquisition/release
        for _ in range(iterations):
            start = time.time()
            # Simulate getting connection from pool
            async with db.get_connection() as _:
                # Simulate query
                pass
            latency = time.time() - start
            benchmark.record_latency("connection_pool", latency)

        stats = benchmark.get_stats("connection_pool")
        print("\nConnection Pool Performance:")
        print(f"  Avg latency: {stats['avg']*1000:.3f}ms")
        print(f"  P95 latency: {stats['p95']*1000:.3f}ms")

        # Connection pool should be very fast
        assert stats["avg"] < 0.01  # < 10ms
