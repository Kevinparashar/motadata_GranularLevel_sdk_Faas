# Motadata Performance Benchmarks

This directory contains performance benchmarking tests for all SDK components.

## Overview

Benchmarks measure:
- **Latency**: Response time for operations
- **Throughput**: Operations per second
- **Cache Performance**: Hit rates and performance improvements
- **Memory Overhead**: Impact of memory integration
- **Load Handling**: Performance under concurrent load
- **Stress Testing**: System behavior under extreme conditions

## Benchmark Files

### Component Benchmarks

- **`benchmark_gateway.py`**: LiteLLM Gateway performance
  - LLM call latency
  - Throughput (requests per second)
  - Cache hit latency
  - Cache performance improvement

- **`benchmark_rag.py`**: RAG System performance
  - Query latency
  - Retrieval speed
  - Memory integration overhead
  - Concurrent query handling

- **`benchmark_cache.py`**: Cache Mechanism performance
  - Set/get operation latency
  - Cache hit rates
  - Throughput (operations per second)
  - Eviction performance
  - TTL expiration performance

- **`benchmark_agent.py`**: Agent Framework performance
  - Task execution latency
  - Memory overhead
  - Concurrent task handling

- **`benchmark_database.py`**: PostgreSQL Database performance
  - Query latency
  - Vector search speed
  - Batch insert performance
  - Connection pool performance

### Core Platform Integration Benchmarks

- **`benchmark_nats_performance.py`**: NATS messaging performance
  - Agent messaging latency (< 10ms P95 target)
  - RAG queue throughput (> 100 msg/sec target)
  - Gateway queuing performance (< 5ms P95 target)

- **`benchmark_otel_overhead.py`**: OTEL observability overhead
  - Tracing overhead (< 5% of operation time target)
  - Metrics collection overhead (< 2% target)
  - Logging overhead (< 1% target)

- **`benchmark_codec_serialization.py`**: CODEC serialization performance
  - Agent message serialization (< 1ms P95 target)
  - RAG payload encoding (< 2ms P95 target)
  - Schema validation latency (< 0.5ms P95 target)

### System Benchmarks

- **`load_test_api.py`**: API endpoint load testing
  - Health endpoint load
  - Generate endpoint load
  - Concurrent request handling

- **`stress_test_system.py`**: System stress testing
  - Gateway stress under high concurrent load
  - Cache stress with high volume operations
  - Memory pressure testing
  - System integration stress

## Running Benchmarks

### Prerequisites

```bash
# Install benchmark dependencies
pip install pytest-benchmark
```

### Run All Benchmarks

```bash
# Run all benchmarks
pytest src/tests/benchmarks/ -v

# Run with benchmark output
pytest src/tests/benchmarks/ --benchmark-only

# Run specific benchmark
pytest src/tests/benchmarks/benchmark_gateway.py -v
```

### Run Specific Benchmark Types

```bash
# Run only load tests
pytest src/tests/benchmarks/load_test_api.py -v

# Run only stress tests
pytest src/tests/benchmarks/stress_test_system.py -v

# Run component benchmarks
pytest src/tests/benchmarks/benchmark_*.py -v
```

### Benchmark Output

Benchmarks output detailed statistics:
- **Count**: Number of operations
- **Min/Max**: Minimum and maximum latency
- **Avg**: Average latency
- **P50/P95/P99**: Percentile latencies
- **Throughput**: Operations per second
- **Success Rate**: Percentage of successful operations

## Benchmark Results

### Expected Performance Targets

#### Gateway
- **Generate Latency**: < 5 seconds (mocked)
- **Cache Hit Latency**: < 10ms
- **Throughput**: > 1 req/sec

#### RAG System
- **Query Latency**: < 10 seconds (mocked)
- **Memory Overhead**: < 100ms
- **Concurrent Queries**: > 0.5 queries/sec

#### Cache Mechanism
- **Set/Get Latency**: < 1ms
- **Hit Rate**: > 95%
- **Throughput**: > 10k ops/sec

#### Agent Framework
- **Task Execution**: < 5 seconds (mocked)
- **Memory Overhead**: < 20%
- **Concurrent Tasks**: > 0.5 tasks/sec

#### Database
- **Query Latency**: < 100ms (mocked)
- **Vector Search**: < 100ms (mocked)
- **Connection Pool**: < 10ms

#### API Endpoints
- **Health Endpoint**: < 100ms avg, < 200ms P95
- **Success Rate**: > 99%
- **Concurrent Requests**: > 95% success

#### Core Platform Integrations
- **NATS Messaging**: < 10ms P95 latency for agent messaging
- **OTEL Overhead**: < 5% tracing overhead, < 2% metrics overhead
- **CODEC Serialization**: < 1ms P95 for agent messages, < 2ms for RAG payloads

#### Stress Tests
- **Gateway Stress**: > 90% success under high load
- **Cache Stress**: > 99% success, > 1k ops/sec
- **Memory Pressure**: Bounded memory, > 95% success
- **System Integration**: > 90% success

## Continuous Benchmarking

Benchmarks can be integrated into CI/CD pipelines:

```bash
# Run benchmarks and save results
pytest src/tests/benchmarks/ --benchmark-json=benchmark_results.json

# Compare with previous results
pytest src/tests/benchmarks/ --benchmark-compare
```

## Best Practices

1. **Run benchmarks regularly**: Track performance over time
2. **Compare results**: Use `--benchmark-compare` to detect regressions
3. **Set thresholds**: Use assertions to enforce performance targets
4. **Monitor trends**: Track performance metrics over releases
5. **Test under load**: Use stress tests to find breaking points

## Notes

- Benchmarks use mocked external services (LLM APIs, databases) for consistency
- Real-world performance may vary based on network conditions and external service latency
- Stress tests are designed to find system limits and should be run in isolated environments

