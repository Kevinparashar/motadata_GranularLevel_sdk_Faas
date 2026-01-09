# LiteLLM Gateway

## Overview

The LiteLLM Gateway serves as the central AI operations hub for the entire SDK. It provides a unified interface for interacting with multiple Large Language Model (LLM) providers, abstracting away provider-specific complexities and enabling seamless integration across all AI components.

## Purpose and Functionality

The gateway acts as a critical middleware layer that standardizes how the SDK interacts with various LLM providers including OpenAI, Anthropic, Google, Cohere, and others. It handles provider-specific API differences, manages authentication, implements retry logic and fallback mechanisms, and provides consistent response formatting across all providers.

The gateway supports both synchronous and asynchronous operations, enabling efficient handling of concurrent requests. It also provides streaming capabilities for real-time response generation, which is essential for interactive applications.

## Connection to Other Components

### Integration with Agno Agent Framework

The **Agno Agent Framework** (`src/core/agno_agent_framework/`) depends directly on the LiteLLM Gateway for all LLM operations. When agents need to perform reasoning, generate responses, or analyze data, they call the gateway's `generate()` or `generate_async()` methods. The gateway instance is injected into each agent during initialization, creating a clear dependency relationship.

### Integration with RAG System

The **RAG System** (`src/core/rag/`) uses the gateway in two critical ways:
1. **Embedding Generation**: The RAG system's retriever component uses the gateway's `embed()` method to generate vector embeddings for both documents during ingestion and queries during retrieval.
2. **Response Generation**: After retrieving relevant documents, the RAG generator uses the gateway's `generate()` method to create context-aware responses using the retrieved information.

### Integration with Prompt Context Management

The **Prompt Context Management** component (`src/core/prompt_context_management/`) works closely with the gateway by providing formatted prompts and context. The gateway receives these prepared prompts and executes them against the configured LLM providers, returning structured responses that can be further processed.

### Integration with Evaluation & Observability

The **Evaluation & Observability** component (`src/core/evaluation_observability/`) monitors all gateway operations. It tracks metrics such as token usage, response times, error rates, and costs. The gateway emits events that the observability system captures for logging, tracing, and performance analysis.

### Integration with API Backend Services

The **API Backend Services** (`src/core/api_backend_services/`) expose the gateway's functionality through RESTful endpoints. When API requests come in for text generation or embeddings, the backend services route them to the gateway, which handles the actual LLM interactions.

## Libraries Utilized

- **litellm**: The core library that provides unified access to multiple LLM providers. It handles provider-specific API calls, authentication, and response formatting.
- **pydantic**: Used for data validation and configuration management, ensuring type safety and proper validation of gateway configurations and responses.
- **httpx**: Provides async HTTP client capabilities for efficient concurrent API requests to LLM providers.

## Function-Driven API

The LiteLLM Gateway provides a **function-driven API** with factory functions, high-level convenience functions, and utilities for easy gateway creation and usage.

### Factory Functions

Create gateways with simplified configuration:

```python
from src.core.litellm_gateway import create_gateway, configure_gateway

# Create gateway with providers
gateway = create_gateway(
    providers=["openai", "anthropic"],
    default_model="gpt-4",
    api_keys={"openai": "sk-...", "anthropic": "sk-..."}
)

# Configure gateway
config = configure_gateway(
    model_list=[{"model_name": "gpt-4", ...}],
    timeout=120.0
)
```

### High-Level Convenience Functions

Use simplified functions for common operations:

```python
from src.core.litellm_gateway import (
    generate_text,
    generate_embeddings,
    stream_text
)

# Generate text easily
text = generate_text(gateway, "What is AI?", model="gpt-4")

# Generate embeddings
embeddings = generate_embeddings(gateway, ["Hello", "World"])

# Stream text
async for chunk in stream_text(gateway, "Tell me a story"):
    print(chunk, end="", flush=True)
```

### Utility Functions

Use utility functions for batch operations:

```python
from src.core.litellm_gateway import batch_generate

# Generate text for multiple prompts
prompts = ["What is AI?", "What is ML?"]
texts = batch_generate(gateway, prompts)
```

See `src/core/litellm_gateway/functions.py` for complete function documentation.

## Key Methods and Their Roles

### `generate()` and `generate_async()`

These methods handle text generation requests. They accept prompts, model specifications, and various generation parameters. The methods abstract away provider differences, automatically handle retries and fallbacks, and return standardized response objects that other components can consume.

### `embed()` and `embed_async()`

These methods generate vector embeddings for text inputs. They are primarily used by the RAG system for document indexing and query processing. The methods support batch processing and return normalized embedding vectors.

### `generate_stream()` and `generate_stream_async()`

These methods provide streaming capabilities, allowing real-time token generation. They return async iterators that yield text chunks as they're generated, enabling interactive user experiences.

## Advanced Features

### Rate Limiting with Request Queuing

The gateway now includes **advanced rate limiting** with request queuing:

- **Token Bucket Algorithm**: Implements token bucket for smooth rate limiting
- **Request Queuing**: Queues requests when rate limit is exceeded instead of failing
- **Per-Tenant Rate Limiting**: Supports tenant-specific rate limits
- **Burst Support**: Allows burst requests within limits
- **Queue Timeout**: Configurable timeout for queued requests

**Example:**
```python
from src.core.litellm_gateway.rate_limiter import RateLimitConfig

# Configure rate limiting
rate_limit_config = RateLimitConfig(
    requests_per_minute=60,
    tokens_per_minute=90000,
    enable_queuing=True,
    queue_timeout=30.0
)
gateway.configure_rate_limiting(rate_limit_config)
```

### Request Batching and Deduplication

The gateway supports **request batching and deduplication** for improved efficiency:

- **Request Batching**: Groups similar requests together to reduce API calls
- **Request Deduplication**: Prevents processing identical requests multiple times
- **Automatic Batching**: Automatically batches requests when possible
- **Deduplication Window**: Configurable time window for deduplication

**Example:**
```python
# Batching and deduplication are automatic
# Multiple identical requests within the deduplication window return cached result
response1 = await gateway.generate_async("What is AI?", tenant_id="tenant1")
response2 = await gateway.generate_async("What is AI?", tenant_id="tenant1")
# response2 uses cached result from response1
```

### Circuit Breaker for Provider Failures

The gateway includes **Circuit Breaker** mechanism for provider failures:

- **Automatic Failure Detection**: Monitors provider health and opens circuit on failures
- **Provider Isolation**: Failing providers are isolated to prevent cascading failures
- **Automatic Recovery**: Attempts recovery after timeout period
- **Fallback Providers**: Automatically falls back to healthy providers

**Example:**
```python
from src.core.utils.circuit_breaker import CircuitBreakerConfig

# Configure circuit breaker
circuit_config = CircuitBreakerConfig(
    failure_threshold=5,
    success_threshold=2,
    timeout=60.0
)
gateway.configure_circuit_breaker(circuit_config)
```

### Health Monitoring

The gateway provides **comprehensive health monitoring** for providers:

- **Provider Health Status**: Tracks health status for each provider
- **Success/Failure Rates**: Records success and failure rates per provider
- **Error Classification**: Classifies and tracks different error types
- **Health Check Integration**: Automatic health checks for all providers

**Example:**
```python
# Get gateway health
health = await gateway.get_health()
print(health['provider_health'])
# {
#   "openai": {
#     "status": "healthy",
#     "success_rate": 0.98,
#     "last_error": None,
#     "response_time_ms": 150
#   },
#   "anthropic": {
#     "status": "degraded",
#     "success_rate": 0.85,
#     "last_error": "Rate limit exceeded",
#     "response_time_ms": 250
#   }
# }
```

### LLMOps Integration

The gateway includes **comprehensive LLMOps capabilities**:

- **Operation Logging**: Logs all LLM operations (completion, embedding, chat, etc.)
- **Token Usage Tracking**: Tracks token usage per operation
- **Cost Calculation**: Calculates and tracks costs per tenant and per operation
- **Latency Monitoring**: Monitors response times and latency
- **Success/Error Rates**: Tracks success and error rates
- **Persistent Storage**: Stores metrics for analysis

**Example:**
```python
# Get LLMOps metrics
metrics = gateway.get_llmops_metrics(tenant_id="tenant1", time_range_hours=24)
print(f"Total operations: {metrics['total_operations']}")
print(f"Total cost: ${metrics['total_cost_usd']:.2f}")
print(f"Average latency: {metrics['average_latency_ms']:.2f}ms")

# Get cost summary
cost_summary = gateway.get_cost_summary(tenant_id="tenant1")
print(f"Cost per 1K tokens: ${cost_summary['cost_per_1k_tokens']:.4f}")
```

### Response Caching

The gateway includes **automatic response caching** to reduce costs and improve performance:

- **Automatic Cache Checking**: Checks cache before making LLM API calls
- **Cache Key Generation**: Creates deterministic cache keys from request parameters
- **Tenant Isolation**: Cache keys include tenant_id for multi-tenant isolation
- **Configurable TTL**: Default 1-hour TTL, configurable per request
- **Stream Exclusion**: Streaming responses are not cached
- **Cache Integration**: Uses CacheMechanism component for storage

**Example:**
```python
from src.core.litellm_gateway import GatewayConfig
from src.core.cache_mechanism import CacheMechanism, CacheConfig

# Create cache
cache = CacheMechanism(CacheConfig(default_ttl=3600))

# Configure gateway with caching
config = GatewayConfig(
    enable_caching=True,
    cache_ttl=3600,  # 1 hour default
    cache=cache
)
gateway = LiteLLMGateway(config=config)

# First call - makes API call and caches result
response1 = await gateway.generate_async("What is AI?", tenant_id="tenant1")

# Second identical call - returns cached result (no API call)
response2 = await gateway.generate_async("What is AI?", tenant_id="tenant1")
# response2 is served from cache, saving API costs
```

**Benefits:**
- **Cost Reduction**: Identical requests don't incur API costs
- **Performance**: Cached responses are returned instantly
- **Multi-Tenant Safe**: Tenant isolation prevents cache pollution
- **Automatic**: No manual cache management required

### Validation/Guardrails Framework

The gateway includes **validation and guardrails** for output quality:

- **Content Filtering**: Blocks outputs containing blocked patterns or PII
- **Format Validation**: Validates JSON and ITSM-specific formats
- **Compliance Checking**: Ensures ITIL and security policy compliance
- **Validation Levels**: Three levels (STRICT, MODERATE, LENIENT)
- **Custom Validators**: Support for custom validation rules

**Example:**
```python
from src.core.validation import ValidationLevel

# Configure validation
config = GatewayConfig(
    enable_validation=True,
    validation_level=ValidationLevel.STRICT  # or MODERATE, LENIENT
)
gateway = LiteLLMGateway(config=config)

# Add custom validator
guardrail = gateway.validation_manager.get_guardrail()
guardrail.add_validator(
    lambda output: (
        "incident_id" in output.lower(),
        "Missing incident_id in response"
    )
)
```

### Feedback Loop Mechanism

The gateway supports **feedback loop** for continuous learning:

- **Feedback Collection**: Records user feedback (correction, rating, useful, improvement, error)
- **Automatic Processing**: Processes feedback with callback system
- **Learning Insights**: Extracts learning insights from feedback
- **Persistent Storage**: Stores feedback for analysis

**Example:**
```python
from src.core.feedback_loop import FeedbackType

# Record feedback
feedback_id = gateway.record_feedback(
    query="How do I reset my password?",
    response="You can reset your password...",
    feedback_type=FeedbackType.CORRECTION,
    content="Actually, the process is different...",
    tenant_id="tenant1"
)

# Get learning insights
insights = gateway.feedback_loop.get_learning_insights(tenant_id="tenant1")
print(f"Average rating: {insights['average_rating']}")
print(f"Common corrections: {insights['common_corrections']}")
```

## Error Handling

The gateway implements comprehensive error handling for various failure scenarios:

- **Provider Failures**: When a primary provider fails, the gateway automatically attempts fallback providers if configured. Circuit breaker prevents cascading failures.
- **Rate Limiting**: The gateway handles rate limit errors by implementing advanced rate limiting with queuing, exponential backoff, and retry logic.
- **Network Errors**: Transient network issues trigger automatic retries with configurable retry counts and delays.
- **Invalid Responses**: Malformed or invalid responses from providers are caught and converted to standardized error responses.
- **Validation Errors**: Output validation failures are caught and reported with detailed error messages.

All errors are logged and can be monitored through the Evaluation & Observability component and LLMOps.

## Configuration and Setup

The gateway is configured through the `GatewayConfig` class, which allows specification of:
- Model lists and routing rules
- Fallback provider chains
- Timeout and retry configurations
- Provider-specific API keys and endpoints

Configuration can be provided programmatically or loaded from environment variables, enabling flexible deployment scenarios.

## Best Practices

1. **Connection Reuse**: The gateway maintains persistent connections to providers when possible, reducing latency and overhead.
2. **Caching**: Responses can be cached through the Cache Mechanism component to reduce costs and improve response times.
3. **Monitoring**: All gateway operations should be monitored through the observability system and LLMOps to track usage, costs, and performance.
4. **Error Handling**: Components using the gateway should implement appropriate error handling for gateway failures. Circuit breaker provides automatic protection.
5. **Resource Management**: The gateway should be properly initialized and closed to ensure clean resource management.
6. **Rate Limiting**: Configure rate limits appropriately to avoid API throttling. Use request queuing for better handling of rate limits.
7. **Health Monitoring**: Regularly check gateway health to detect provider issues early.
8. **Validation**: Enable validation/guardrails to ensure output quality and compliance.
9. **Feedback Collection**: Collect user feedback to enable continuous improvement.
10. **Cost Management**: Monitor LLMOps metrics to track and optimize costs per tenant.
