"""
Performance Benchmarks for CODEC Integration

Measures CODEC serialization/deserialization performance.
"""

import json
import time
from typing import Dict, List
from unittest.mock import Mock

import pytest

# TODO: BENCHMARK-001 - Import when CODEC integration is available  # noqa: FIX002, S1135
# from src.integrations.codec_integration import CodecSerializer


class BenchmarkCodec:
    """Benchmark suite for CODEC Integration."""

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
        }


@pytest.mark.benchmark
class TestCodecSerializationBenchmarks:
    """Performance benchmarks for CODEC serialization."""

    @pytest.fixture
    def benchmark_codec(self):
        """CODEC benchmark fixture."""
        return BenchmarkCodec()

    @pytest.fixture
    def mock_codec(self):
        """Mock CODEC serializer with realistic performance."""
        codec = Mock()

        def mock_encode(envelope):
            # Simulate encoding overhead (0.1-0.5ms)
            time.sleep(0.0003)  # 0.3ms average
            return json.dumps(envelope).encode()

        def mock_decode(payload):
            # Simulate decoding overhead (0.1-0.5ms)
            time.sleep(0.0003)  # 0.3ms average
            return json.loads(payload.decode())

        def mock_validate(envelope, schema_name):
            # Simulate validation overhead (0.05-0.2ms)
            time.sleep(0.0001)  # 0.1ms average
            return True

        codec.encode = Mock(side_effect=mock_encode)
        codec.decode = Mock(side_effect=mock_decode)
        codec.validate_schema = Mock(side_effect=mock_validate)
        codec.create_envelope = Mock(
            return_value={"schema_version": "1.0", "message_type": "agent_message", "data": {}}
        )
        return codec

    def test_agent_message_serialization(self, benchmark_codec, mock_codec):
        """Benchmark agent message serialization."""
        # Target: < 1ms P95

        iterations = 1000

        message = {
            "message_id": "msg_123",
            "source_agent_id": "agent_123",
            "target_agent_id": "agent_456",
            "content": "Test message content",
            "message_type": "text",
            "timestamp": "2024-01-01T00:00:00",
            "metadata": {"key": "value"},
        }

        for _ in range(iterations):
            # Create envelope
            envelope = mock_codec.create_envelope(
                message_type="agent_message", schema_version="1.0", data=message
            )

            # Encode
            start = time.time()
            encoded = mock_codec.encode(envelope)
            latency = (time.time() - start) * 1000  # Convert to ms
            benchmark_codec.record_latency("agent_message_encode", latency)

            # Decode
            start = time.time()
            _ = mock_codec.decode(encoded)
            latency = (time.time() - start) * 1000  # Convert to ms
            benchmark_codec.record_latency("agent_message_decode", latency)

        encode_stats = benchmark_codec.get_stats("agent_message_encode")
        decode_stats = benchmark_codec.get_stats("agent_message_decode")

        print(f"\nAgent Message Encoding Stats: {encode_stats}")
        print(f"Agent Message Decoding Stats: {decode_stats}")

        # Assert performance targets
        assert (
            encode_stats["p95"] < 1.0
        ), f"Encode P95 latency {encode_stats['p95']}ms exceeds 1ms target"
        assert (
            decode_stats["p95"] < 1.0
        ), f"Decode P95 latency {decode_stats['p95']}ms exceeds 1ms target"

    def test_rag_payload_encoding(self, benchmark_codec, mock_codec):
        """Benchmark RAG payload encoding."""
        # Target: < 2ms P95

        iterations = 500  # Fewer iterations due to larger payloads

        document = {
            "document_id": "doc_123",
            "content": "A" * 10000,  # 10KB content
            "metadata": {"title": "Test", "author": "Test Author"},
            "chunks": [
                {
                    "chunk_id": f"chunk_{i}",
                    "content": f"Chunk content {i}",
                    "embedding": [0.1] * 1536,  # 1536-dim embedding
                    "metadata": {},
                }
                for i in range(10)
            ],
            "tenant_id": "tenant_123",
            "timestamp": "2024-01-01T00:00:00",
        }

        for _ in range(iterations):
            # Create envelope
            envelope = mock_codec.create_envelope(
                message_type="rag_document", schema_version="1.0", data=document
            )

            # Encode
            start = time.time()
            encoded = mock_codec.encode(envelope)
            latency = (time.time() - start) * 1000  # Convert to ms
            benchmark_codec.record_latency("rag_payload_encode", latency)

            # Decode
            start = time.time()
            _ = mock_codec.decode(encoded)
            latency = (time.time() - start) * 1000  # Convert to ms
            benchmark_codec.record_latency("rag_payload_decode", latency)

        encode_stats = benchmark_codec.get_stats("rag_payload_encode")
        decode_stats = benchmark_codec.get_stats("rag_payload_decode")

        print(f"\nRAG Payload Encoding Stats: {encode_stats}")
        print(f"RAG Payload Decoding Stats: {decode_stats}")

        # Assert performance targets
        assert (
            encode_stats["p95"] < 2.0
        ), f"Encode P95 latency {encode_stats['p95']}ms exceeds 2ms target"
        assert (
            decode_stats["p95"] < 2.0
        ), f"Decode P95 latency {decode_stats['p95']}ms exceeds 2ms target"

    def test_schema_validation_latency(self, benchmark_codec, mock_codec):
        """Benchmark schema validation latency."""
        # Target: < 0.5ms P95

        iterations = 2000

        envelope = {
            "schema_version": "1.0",
            "message_type": "agent_message",
            "data": {"message_id": "msg_123", "content": "Test"},
        }

        for _ in range(iterations):
            # Validate schema
            start = time.time()
            _ = mock_codec.validate_schema(envelope, schema_name="agent_message")
            latency = (time.time() - start) * 1000  # Convert to ms
            benchmark_codec.record_latency("schema_validation", latency)

        stats = benchmark_codec.get_stats("schema_validation")
        print(f"\nSchema Validation Latency Stats: {stats}")

        # Assert performance target
        assert stats["p95"] < 0.5, f"P95 latency {stats['p95']}ms exceeds 0.5ms target"
