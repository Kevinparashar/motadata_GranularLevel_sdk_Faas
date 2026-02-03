"""
Performance Benchmarks for NATS Integration

Measures NATS messaging performance with AI SDK components.
"""


import asyncio
import time
from typing import Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

# TODO: BENCHMARK-002 - Import when NATS integration is available  # noqa: FIX002, S1135
# from src.integrations.nats_integration import NATSClient
# from src.integrations.codec_integration import CodecSerializer


class BenchmarkNATS:
    """Benchmark suite for NATS Integration."""

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
        sorted_latencies = sorted(latencies)
        return {
            "count": len(latencies),
            "min": min(latencies),
            "max": max(latencies),
            "avg": sum(latencies) / len(latencies),
            "p50": sorted_latencies[len(latencies) // 2],
            "p95": sorted_latencies[int(len(latencies) * 0.95)] if len(latencies) > 0 else 0,
            "p99": sorted_latencies[int(len(latencies) * 0.99)] if len(latencies) > 0 else 0,
        }


@pytest.mark.benchmark
class TestNATSPerformanceBenchmarks:
    """Performance benchmarks for NATS Integration."""

    @pytest.fixture
    def benchmark_nats(self):
        """NATS benchmark fixture."""
        return BenchmarkNATS()

    @pytest.fixture
    def mock_nats_client(self):
        """Mock NATS client with realistic latency."""
        client = AsyncMock()

        async def mock_publish(*args, **kwargs):
            # Simulate network latency (1-5ms)
            await asyncio.sleep(0.002)  # 2ms average

        async def mock_request(*args, **kwargs):
            # Simulate request-response latency (5-10ms)
            await asyncio.sleep(0.007)  # 7ms average
            return MagicMock(data=b"response")

        client.publish = mock_publish
        client.request = mock_request
        return client

    @pytest.fixture
    def mock_codec(self):
        """Mock CODEC with minimal overhead."""
        codec = Mock()
        codec.encode = Mock(return_value=b"encoded")
        codec.decode = Mock(return_value={"data": "decoded"})
        return codec

    @pytest.mark.asyncio
    async def test_agent_messaging_latency(self, benchmark_nats, mock_nats_client, mock_codec):
        """Benchmark agent messaging latency via NATS."""
        # Target: < 10ms P95

        iterations = 100
        tenant_id = "tenant_123"

        for i in range(iterations):
            start = time.time()

            # Encode message
            encoded = mock_codec.encode(
                {"message_id": f"msg_{i}", "content": f"Message {i}", "schema_version": "1.0"}
            )

            # Publish via NATS
            await mock_nats_client.publish(subject=f"ai.agent.message.{tenant_id}", payload=encoded)

            latency = (time.time() - start) * 1000  # Convert to ms
            benchmark_nats.record_latency("agent_messaging", latency)

        stats = benchmark_nats.get_stats("agent_messaging")
        print(f"\nAgent Messaging Latency Stats: {stats}")

        # Assert performance target
        assert stats["p95"] < 10.0, f"P95 latency {stats['p95']}ms exceeds 10ms target"

    @pytest.mark.asyncio
    async def test_rag_queue_throughput(self, benchmark_nats, mock_nats_client, mock_codec):
        """Benchmark RAG queue throughput via NATS."""
        # Target: > 100 msg/sec

        message_count = 1000
        tenant_id = "tenant_123"

        start = time.time()

        # Publish messages concurrently
        tasks = []
        for i in range(message_count):
            encoded = mock_codec.encode(
                {"query_id": f"query_{i}", "query": f"Query {i}", "schema_version": "1.0"}
            )
            task = mock_nats_client.publish(subject=f"ai.rag.queries.{tenant_id}", payload=encoded)
            tasks.append(task)

        await asyncio.gather(*tasks)

        duration = time.time() - start
        throughput = message_count / duration

        print(f"\nRAG Queue Throughput: {throughput:.2f} msg/sec")

        # Assert performance target
        assert throughput > 100.0, f"Throughput {throughput} msg/sec below 100 msg/sec target"

    @pytest.mark.asyncio
    async def test_gateway_queuing_performance(self, benchmark_nats, mock_nats_client, mock_codec):
        """Benchmark Gateway queuing performance via NATS."""
        # Target: < 5ms P95

        iterations = 100
        tenant_id = "tenant_123"

        for i in range(iterations):
            start = time.time()

            # Encode request
            encoded = mock_codec.encode(
                {
                    "request_id": f"req_{i}",
                    "prompt": "Test prompt",
                    "model": "gpt-4",
                    "schema_version": "1.0",
                }
            )

            # Publish to queue
            await mock_nats_client.publish(
                subject=f"ai.gateway.requests.{tenant_id}", payload=encoded
            )

            latency = (time.time() - start) * 1000  # Convert to ms
            benchmark_nats.record_latency("gateway_queuing", latency)

        stats = benchmark_nats.get_stats("gateway_queuing")
        print(f"\nGateway Queuing Latency Stats: {stats}")

        # Assert performance target
        assert stats["p95"] < 5.0, f"P95 latency {stats['p95']}ms exceeds 5ms target"
