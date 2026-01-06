# Cache Mechanism

## Overview

The Cache Mechanism component provides caching capabilities to improve performance, reduce costs, and enhance user experience. It offers in-memory (LRU + TTL) and Redis backends with pattern-based invalidation.

## Purpose and Functionality

- Reduce LLM and retrieval costs by caching responses and embeddings
- Improve latency through reuse of cached results
- Provide TTL management and simple eviction for memory-bound deployments
- Allow pattern-based invalidation for coordinated cache clears

## Connection to Other Components

### Integration with LiteLLM Gateway

The **LiteLLM Gateway** (`src/core/litellm_gateway/`) can use the cache mechanism to cache LLM responses. When the gateway receives a request, it can check the cache first. If a cached response exists and is still valid, it returns the cached response instead of making an API call. This significantly reduces costs and improves response times for repeated queries.

### Integration with RAG System

The **RAG System** (`src/core/rag/`) uses caching in multiple ways:
1. **Query Result Caching**: Frequently asked questions can be cached, avoiding expensive retrieval and generation operations
2. **Embedding Caching**: Document embeddings can be cached to avoid regenerating them
3. **Retrieved Document Caching**: Retrieved document sets can be cached for similar queries

This caching is particularly valuable for RAG systems, as retrieval and generation operations are computationally expensive.

### Integration with PostgreSQL Database

The **PostgreSQL Database** (`src/core/postgresql_database/`) can serve as a caching backend. When configured to use database caching, the cache mechanism stores cached data in the database, providing persistent caching that survives application restarts.

### Integration with Evaluation & Observability

The **Evaluation & Observability** component (`src/core/evaluation_observability/`) tracks cache performance metrics:
- **Cache Hit Rates**: Measures how often cached data is found
- **Cache Miss Rates**: Tracks cache misses
- **Cache Performance**: Monitors cache operation times
- **Cost Savings**: Estimates cost savings from caching

This monitoring helps optimize cache configurations and identify caching opportunities.

### Integration with API Backend Services

The **API Backend Services** (`src/core/api_backend_services/`) can use caching to improve API response times. Frequently accessed endpoints can cache their responses, reducing backend processing time and improving user experience.

## Backends

- **Memory**: OrderedDict-based LRU with TTL and max-size enforcement
- **Redis**: Optional; enabled when `redis` dependency and URL are provided

## Key Features

### Key Features

- **TTL Management**: Configurable default TTL per instance
- **LRU Eviction**: Max-size enforcement for memory backend
- **Pattern Invalidation**: Clear keys matching simple patterns
- **Namespace Support**: Avoid collisions across components

### Cache Statistics

The component tracks cache statistics:
- **Hit/Miss Ratios**: Tracks cache effectiveness
- **Size Metrics**: Monitors cache size and memory usage
- **Performance Metrics**: Tracks cache operation performance

## Error Handling

The component implements robust error handling:
- **Backend Failures**: Gracefully handles cache backend failures, falling back to direct operations
- **Serialization Errors**: Handles errors when serializing/deserializing cached data
- **Timeout Handling**: Manages timeouts when accessing distributed caches

## Configuration

`CacheConfig` supports:
- `backend`: `"memory"` or `"redis"`
- `default_ttl`: default TTL in seconds
- `max_size`: max entries for in-memory cache
- `redis_url`: optional Redis connection URL
- `namespace`: namespacing for keys

## Best Practices

1. **Appropriate TTL Values**: Set TTL values based on data volatility
2. **Cache Key Design**: Use consistent, unique cache keys
3. **Cache Invalidation**: Implement proper cache invalidation strategies
4. **Monitor Performance**: Track cache hit rates and adjust configurations
5. **Distributed Caching**: Use distributed caches (Redis) for multi-instance deployments
6. **Cost-Benefit Analysis**: Balance cache complexity with performance and cost benefits
