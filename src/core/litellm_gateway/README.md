# MOTADATA - LITELLM GATEWAY

**Unified interface for multiple LLM providers with rate limiting, caching, circuit breakers, and observability.**

## When to Use This Component

**✅ Use LiteLLM Gateway when:**
- You need to call AI models (OpenAI, Anthropic, Google, etc.)
- You want a unified interface for multiple LLM providers
- You need embeddings for vector search
- You want built-in rate limiting, caching, and cost tracking
- You're building Agents, RAG systems, or any AI-powered feature
- You need to switch between providers easily

**❌ Don't use LiteLLM Gateway when:**
- You only need simple HTTP calls to a single provider (use provider SDK directly)
- You don't need AI capabilities at all
- You're building a non-AI application
- You need direct provider-specific features not supported by LiteLLM

**Simple Example:**
```python
from src.core.litellm_gateway import create_gateway

gateway = create_gateway(api_key="your-key", provider="openai")
response = await gateway.generate_async("Hello, world!")
print(response.text)
```

**Cost Note:** Gateway calls cost ~$0.001-0.01 per request (depends on model). Enable caching to reduce costs by 50-90% for repeated queries.

---

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

See the [Function-Driven API](#function-driven-api) section below for complete function documentation.

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

The gateway includes **comprehensive LLMOps capabilities** for tracking LLM operations:

- **Operation Logging**: Logs all LLM operations (completion, embedding, chat, etc.)
- **Token Usage Tracking**: Tracks token usage per operation
- **Cost Calculation**: Calculates and tracks costs per tenant and per operation
- **Latency Monitoring**: Monitors response times and latency
- **Success/Error Rates**: Tracks success and error rates
- **Persistent Storage**: Stores metrics for analysis

**When to use LLMOps:**
- You need better production visibility into model cost over time
- You want to track slow requests and error rates
- You need to monitor token usage and costs per tenant

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

**LLMOps Implementation:** The LLMOps module (`src/core/llmops/llmops.py`) provides utilities for tracking request latency, token usage, estimated cost, and success/failure status. The gateway automatically integrates with LLMOps when enabled.

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

The gateway includes **validation and guardrails** for output quality. See [Validation & Guardrails README](../validation/README.md) for complete documentation.

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

The gateway supports **feedback loop** for continuous learning. See [Feedback Loop README](../feedback_loop/README.md) for complete documentation.

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

---

## Getting Started Guide

This section provides a complete step-by-step guide for getting started with the LiteLLM Gateway, from gateway creation to receiving responses.

### Entry Point

The primary entry point for creating gateways is through factory functions:

```python
from src.core.litellm_gateway import create_gateway, generate_text, generate_text_async
```

### Input Requirements

#### Required Inputs

1. **API Key**: Provider API key
   ```python
   api_key = os.getenv("OPENAI_API_KEY")  # or ANTHROPIC_API_KEY, etc.
   ```

2. **Provider**: LLM provider name
   - `"openai"` - OpenAI models
   - `"anthropic"` - Anthropic Claude models
   - `"google"` - Google Gemini models
   - `"cohere"` - Cohere models

#### Optional Inputs

- `default_model`: Default model to use (e.g., "gpt-4", "claude-3-opus")
- `timeout`: Request timeout in seconds
- `max_retries`: Maximum retry attempts
- `rate_limit_config`: Rate limiting configuration
- `enable_caching`: Enable response caching

### Process Flow

#### Step 1: Gateway Creation

**What Happens:**
1. Gateway configuration is validated
2. Provider connection is initialized
3. Rate limiter is configured (if enabled)
4. Circuit breaker is initialized
5. Health monitoring is set up

**Code:**
```python
# Basic gateway creation
gateway = create_gateway(
    api_key="your-api-key",
    provider="openai",
    default_model="gpt-4",
    timeout=60.0,
    max_retries=3
)

# Gateway with cache enabled
from src.core.cache_mechanism import CacheMechanism, CacheConfig

cache = CacheMechanism(CacheConfig(default_ttl=3600))  # 1 hour TTL
gateway = create_gateway(
    api_key="your-api-key",
    provider="openai",
    default_model="gpt-4",
    enable_caching=True,
    cache_ttl=3600,  # 1 hour default
    cache=cache
)
```

**Internal Process:**
```
create_gateway()
  ├─> Validate API key format
  ├─> Initialize provider client
  ├─> Configure rate limiter
  ├─> Set up circuit breaker
  ├─> Initialize health monitor
  ├─> Initialize cache mechanism (if enabled)
  └─> Return gateway instance
```

#### Step 2: Request Preparation

**What Happens:**
1. Request parameters are validated
2. Rate limit is checked
3. Request is queued (if rate limit exceeded)
4. Circuit breaker state is checked
5. Request is deduplicated (if enabled)

**Code:**
```python
# Synchronous request
response = gateway.generate(
    prompt="Explain quantum computing",
    model="gpt-4",
    max_tokens=500,
    temperature=0.7,
    tenant_id="tenant_123"
)
```

**Input:**
- `prompt`: Text prompt to send to LLM
- `model`: Model to use (optional, uses default if not specified)
- `max_tokens`: Maximum tokens in response
- `temperature`: Sampling temperature (0.0-2.0)
- `tenant_id`: Optional tenant ID for multi-tenancy

**Internal Process:**
```
gateway.generate()
  ├─> Validate input parameters
  ├─> Check rate limits
  ├─> Check circuit breaker
  ├─> Check request cache (if enabled)
  ├─> Queue request (if rate limit exceeded)
  └─> Proceed to execution
```

#### Step 3: Request Execution

**What Happens:**
1. Request is sent to LLM provider
2. Provider processes the request
3. Response is received
4. Response is validated
5. Response is cached (if enabled)
6. Metrics are recorded

**Internal Process:**
```
Request Execution
  ├─> Format request for provider
  ├─> Send HTTP request to provider API
  ├─> Wait for response
  ├─> Parse response
  ├─> Validate response format
  ├─> Apply guardrails/validation (if enabled)
  ├─> Cache response (if enabled)
  ├─> Record metrics (tokens, cost, latency)
  └─> Return response
```

#### Step 4: Response Processing

**What Happens:**
1. Response is parsed
2. Validation rules are applied
3. Response is formatted
4. Usage metrics are extracted
5. Response object is created

**Code:**
```python
# Response structure
response = {
    "text": "Quantum computing is...",
    "model": "gpt-4",
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 150,
        "total_tokens": 160
    },
    "finish_reason": "stop",
    "metadata": {
        "provider": "openai",
        "request_id": "req_123",
        "latency": 2.5
    }
}
```

### Output Structure

#### Generate Response Structure

```python
class GenerateResponse:
    text: str                    # Generated text
    model: str                   # Model used
    usage: TokenUsage            # Token usage
    finish_reason: str          # Completion reason
    metadata: Dict[str, Any]    # Additional metadata
```

#### Output Fields

- **`text`**: The generated text response from the LLM
- **`model`**: The model that generated the response
- **`usage`**: Token usage information
  - `prompt_tokens`: Tokens in input
  - `completion_tokens`: Tokens in output
  - `total_tokens`: Total tokens used
- **`finish_reason`**: Why generation stopped ("stop", "length", "content_filter")
- **`metadata`**: Additional information
  - `provider`: LLM provider used
  - `request_id`: Unique request identifier
  - `latency`: Request latency in seconds
  - `cost`: Estimated cost (if available)

### Complete Example

```python
import os
import asyncio
from src.core.litellm_gateway import create_gateway, generate_text_async

async def main():
    # Step 1: Create Gateway (Entry Point)
    gateway = create_gateway(
        api_key=os.getenv("OPENAI_API_KEY"),
        provider="openai",
        default_model="gpt-4",
        timeout=60.0
    )

    # Step 2: Prepare Request (Input)
    prompt = "Explain artificial intelligence in detail."
    model = "gpt-4"
    max_tokens = 500

    # Step 3: Execute Request (Process)
    response = await generate_text_async(
        gateway,
        prompt=prompt,
        model=model,
        max_tokens=max_tokens,
        temperature=0.7,
        tenant_id="tenant_123"
    )

    # Step 4: Process Output
    generated_text = response.text
    tokens_used = response.usage.total_tokens
    latency = response.metadata.get('latency', 0)

    print(f"Generated Text: {generated_text}")
    print(f"Tokens Used: {tokens_used}")
    print(f"Latency: {latency}s")

    # Step 5: Use Output
    # Use generated_text in your application
    return generated_text

# Run the example
result = asyncio.run(main())
```

### Important Information

#### Rate Limiting

```python
from src.core.litellm_gateway.rate_limiter import RateLimitConfig

rate_limit_config = RateLimitConfig(
    requests_per_minute=60,
    tokens_per_minute=90000,
    enable_queuing=True,
    queue_timeout=30.0
)

gateway.configure_rate_limiting(rate_limit_config)
# Requests automatically respect rate limits
```

#### Circuit Breaker

```python
# Circuit breaker automatically opens on repeated failures
# Prevents cascading failures
# Automatically attempts recovery after timeout

# Check circuit breaker status
status = gateway.get_health()
if status['circuit_breaker']['state'] == 'open':
    print("Circuit breaker is open - provider unavailable")
```

#### Request Batching

```python
# Enable batching for similar requests
config = GatewayConfig(
    enable_request_batching=True,
    batch_size=10,
    batch_timeout=1.0
)

gateway = LiteLLMGateway(config=config)
# Similar requests are automatically batched
```

#### Request Deduplication

```python
# Enable deduplication to avoid processing identical requests
config = GatewayConfig(
    enable_request_deduplication=True,
    deduplication_ttl=300  # 5 minutes
)

gateway = LiteLLMGateway(config=config)
# Identical requests within deduplication window return cached result
```

#### Response Caching

```python
from src.core.cache_mechanism import CacheMechanism, CacheConfig

# Create cache mechanism
cache = CacheMechanism(CacheConfig(default_ttl=3600))  # 1 hour TTL

# Create gateway with caching enabled
gateway = create_gateway(
    api_key="your-api-key",
    provider="openai",
    default_model="gpt-4",
    enable_caching=True,
    cache_ttl=3600,  # 1 hour default
    cache=cache
)

# First request - makes API call and caches response
response1 = await gateway.generate_async(
    prompt="What is AI?",
    model="gpt-4",
    tenant_id="tenant_123"
)

# Second identical request - uses cached response (no API call)
response2 = await gateway.generate_async(
    prompt="What is AI?",
    model="gpt-4",
    tenant_id="tenant_123"
)
# response2 uses cached result from response1 (faster, cheaper)
```

#### Error Handling

```python
try:
    response = gateway.generate(prompt="Test")
except GatewayError as e:
    print(f"Gateway error: {e.message}")
    print(f"Provider: {e.provider}")
    print(f"Status code: {e.status_code}")
except RateLimitError as e:
    print(f"Rate limit exceeded: {e.message}")
    print(f"Retry after: {e.retry_after} seconds")
```

#### Health Monitoring

```python
# Check gateway health
health = gateway.get_health()
print(f"Status: {health['status']}")
print(f"Provider: {health['provider']}")
print(f"Circuit Breaker: {health['circuit_breaker']['state']}")
print(f"Rate Limit: {health['rate_limit']['remaining']} requests remaining")
```

---

## Detailed Class Documentation

This section provides comprehensive documentation for the `LiteLLMGateway` class and related components.

### Class Structure

#### `GatewayConfig` (BaseModel)

Configuration model for the LiteLLM Gateway with comprehensive settings:

**Core Configuration:**
- `model_list`: List of model configurations for routing
- `fallbacks`: Fallback models if primary fails
- `timeout`: Request timeout in seconds (default: 60.0)
- `max_retries`: Maximum retry attempts (default: 3)
- `retry_delay`: Delay between retries (default: 1.0)

**Feature Flags:**
- `enable_circuit_breaker`: Enable circuit breaker pattern
- `enable_rate_limiting`: Enable rate limiting per tenant
- `enable_request_deduplication`: Deduplicate identical requests
- `enable_request_batching`: Batch multiple requests
- `enable_health_monitoring`: Monitor gateway health
- `enable_llmops`: Enable LLM operations tracking
- `enable_validation`: Enable response validation
- `enable_feedback_loop`: Enable feedback collection
- `enable_caching`: Enable response caching
- `enable_kv_cache`: Enable KV cache for attention

**Cache Configuration:**
- `cache_ttl`: Cache time-to-live in seconds (default: 3600)
- `kv_cache_ttl`: KV cache TTL in seconds (default: 3600)
- `cache`: Optional CacheMechanism instance
- `cache_config`: Optional CacheConfig

**Advanced Configuration:**
- `rate_limit_config`: Rate limiting configuration
- `circuit_breaker_config`: Circuit breaker configuration
- `validation_level`: Validation strictness level
- `batch_size`: Batch size for request batching
- `batch_timeout`: Timeout for batch collection

#### `GenerateResponse` (BaseModel)

Response model for text generation:
- `text`: Generated text content
- `model`: Model used for generation
- `usage`: Token usage information
- `finish_reason`: Reason for completion
- `raw_response`: Raw provider response

#### `EmbedResponse` (BaseModel)

Response model for embedding generation:
- `embeddings`: List of embedding vectors
- `model`: Model used for embeddings
- `usage`: Token usage information

#### `LiteLLMGateway` (Class)

Main gateway class providing unified LLM access.

**Core Attributes:**
- `config`: Gateway configuration
- `router`: LiteLLM Router instance for model routing
- `circuit_breaker`: Circuit breaker for fault tolerance
- `rate_limiters`: Per-tenant rate limiters
- `deduplicator`: Request deduplicator
- `batcher`: Request batcher
- `cache`: Cache mechanism instance
- `kv_cache`: KV cache manager
- `llmops`: LLMOps instance for tracking
- `validation_manager`: Validation manager
- `feedback_loop`: Feedback collection system
- `health_check`: Health monitoring

### Key Methods

#### `generate(prompt, model=None, **kwargs) -> GenerateResponse`

Synchronous text generation.

**Parameters:**
- `prompt`: Input prompt text
- `model`: Optional model name (uses router default if not provided)
- `**kwargs`: Additional generation parameters:
  - `temperature`: Sampling temperature
  - `max_tokens`: Maximum tokens to generate
  - `stream`: Enable streaming (returns iterator)
  - `functions`: Function calling definitions
  - `tenant_id`: Tenant ID for rate limiting

**Process:**
1. Validates input and checks circuit breaker
2. Applies rate limiting (if enabled)
3. Checks cache (if enabled)
4. Deduplicates request (if enabled)
5. Calls LiteLLM completion
6. Validates response (if enabled)
7. Caches response (if enabled)
8. Tracks operation in LLMOps
9. Returns formatted response

**Returns:** `GenerateResponse` with generated text

#### `async def generate_async(prompt, model=None, **kwargs) -> GenerateResponse`

Asynchronous text generation (recommended for production).

**Parameters:** Same as `generate()`

**Process:** Same as `generate()` but async

**Returns:** `GenerateResponse` with generated text

#### `async def generate_stream(prompt, model=None, **kwargs) -> AsyncIterator[str]`

Streaming text generation for real-time responses.

**Parameters:** Same as `generate()` with `stream=True`

**Returns:** Async iterator yielding text chunks

**Example:**
```python
async for chunk in gateway.generate_stream("Tell me a story"):
    print(chunk, end="", flush=True)
```

#### `embed(text, model=None, **kwargs) -> EmbedResponse`

Synchronous embedding generation.

**Parameters:**
- `text`: Text to embed (string or list of strings)
- `model`: Optional embedding model name
- `**kwargs`: Additional parameters

**Process:**
1. Validates input
2. Checks cache for embeddings
3. Calls LiteLLM embedding
4. Caches embeddings
5. Tracks in LLMOps
6. Returns embeddings

**Returns:** `EmbedResponse` with embedding vectors

#### `async def embed_async(text, model=None, **kwargs) -> EmbedResponse`

Asynchronous embedding generation.

**Parameters:** Same as `embed()`

**Returns:** `EmbedResponse` with embedding vectors

#### `check_health() -> HealthCheckResult`

Performs health check on the gateway.

**Checks:**
- Router connectivity
- Circuit breaker state
- Cache availability
- Rate limiter status

**Returns:** `HealthCheckResult` with health status

#### `get_usage_stats(tenant_id=None) -> Dict[str, Any]`

Gets usage statistics for a tenant.

**Parameters:**
- `tenant_id`: Optional tenant ID (all tenants if None)

**Returns:** Dictionary with usage statistics

### Usage Instructions

#### Basic Gateway Creation

```python
from src.core.litellm_gateway import LiteLLMGateway, GatewayConfig

# Create with default configuration
gateway = LiteLLMGateway()

# Or with custom configuration
config = GatewayConfig(
    timeout=120.0,
    max_retries=5,
    enable_caching=True,
    cache_ttl=7200
)
gateway = LiteLLMGateway(config=config)
```

#### Text Generation

```python
# Synchronous generation
response = gateway.generate(
    prompt="Explain quantum computing",
    model="gpt-4",
    temperature=0.7,
    max_tokens=500
)
print(response.text)

# Asynchronous generation (recommended)
response = await gateway.generate_async(
    prompt="Explain quantum computing",
    model="gpt-4"
)
print(response.text)
```

#### Streaming Generation

```python
# Streaming for real-time responses
async for chunk in gateway.generate_stream(
    prompt="Tell me a story about AI",
    model="gpt-4"
):
    print(chunk, end="", flush=True)
```

#### Embedding Generation

```python
# Generate embeddings
response = await gateway.embed_async(
    text="This is a sample text",
    model="text-embedding-ada-002"
)
embeddings = response.embeddings[0]  # First embedding vector

# Batch embeddings
response = await gateway.embed_async(
    text=["Text 1", "Text 2", "Text 3"],
    model="text-embedding-ada-002"
)
# Returns list of embedding vectors
```

#### Multi-Provider Configuration

```python
from src.core.litellm_gateway import LiteLLMGateway, GatewayConfig

config = GatewayConfig(
    model_list=[
        {
            "model_name": "gpt-4",
            "litellm_params": {
                "model": "openai/gpt-4",
                "api_key": "your-openai-key"
            }
        },
        {
            "model_name": "claude-3",
            "litellm_params": {
                "model": "anthropic/claude-3-opus",
                "api_key": "your-anthropic-key"
            }
        }
    ],
    fallbacks=["gpt-3.5-turbo"]  # Fallback if primary fails
)

gateway = LiteLLMGateway(config=config)

# Gateway automatically routes to appropriate provider
response = await gateway.generate_async("Hello", model="gpt-4")
```

#### With Caching

```python
config = GatewayConfig(
    enable_caching=True,
    cache_ttl=3600,  # Cache for 1 hour
    cache_config=CacheConfig(
        backend="dragonfly",  # or "memory"
        dragonfly_url="dragonfly://localhost:6379"
    )
)

gateway = LiteLLMGateway(config=config)

# First call - hits LLM
response1 = await gateway.generate_async("What is AI?")

# Second call - returns cached result (faster, cheaper)
response2 = await gateway.generate_async("What is AI?")
```

#### With Rate Limiting

```python
from src.core.litellm_gateway.rate_limiter import RateLimitConfig

config = GatewayConfig(
    enable_rate_limiting=True,
    rate_limit_config=RateLimitConfig(
        requests_per_minute=60,
        requests_per_hour=1000
    )
)

gateway = LiteLLMGateway(config=config)

# Rate limiting is applied per tenant_id
response = await gateway.generate_async(
    prompt="Hello",
    tenant_id="tenant_123"  # Rate limits scoped per tenant
)
```

#### Health Monitoring

```python
# Check gateway health
health = gateway.check_health()

if health.status == "healthy":
    print("Gateway is operational")
else:
    print(f"Issues: {health.details}")

# Get usage statistics
stats = gateway.get_usage_stats(tenant_id="tenant_123")
print(f"Total requests: {stats['total_requests']}")
print(f"Total cost: ${stats['total_cost']:.2f}")
```

### Connection to Other Components

#### Agent Framework
The Agent Framework (`src/core/agno_agent_framework/`) uses the gateway for all LLM operations:
- Agents inject gateway during initialization
- All agent reasoning and generation goes through gateway
- Gateway handles rate limiting per agent/tenant

**Integration Point:** `agent.gateway` attribute

#### RAG System
The RAG System (`src/core/rag/`) uses the gateway for:
- Embedding generation for document indexing
- Text generation for query responses
- Both operations benefit from gateway caching

**Integration Point:** `rag_system.gateway` attribute

#### Cache Mechanism
The gateway integrates with Cache Mechanism (`src/core/cache_mechanism/`):
- Caches generation responses
- Caches embeddings
- Reduces costs and improves performance

**Integration Point:** `gateway.cache` attribute

#### KV Cache
The gateway uses KV Cache (`src/core/litellm_gateway/kv_cache.py`):
- Attention key-value caching
- Optimizes repeated generation requests
- Reduces token usage

**Integration Point:** `gateway.kv_cache` attribute

#### Rate Limiter
The gateway uses Rate Limiter (`src/core/litellm_gateway/rate_limiter.py`):
- Per-tenant rate limiting
- Request batching and deduplication
- Prevents API quota exhaustion

**Integration Point:** `gateway.rate_limiters` and `gateway.deduplicator`

#### Circuit Breaker
Uses Circuit Breaker (`src/core/utils/circuit_breaker.py`):
- Fault tolerance for provider failures
- Automatic recovery
- Prevents cascade failures

**Integration Point:** `gateway.circuit_breaker`

#### LLMOps
Integrates with LLMOps (`src/core/llmops/`):
- Tracks all LLM operations
- Monitors costs and usage
- Provides analytics

**Integration Point:** `gateway.llmops`

#### Validation Manager
Uses Validation Manager (`src/core/validation/`):
- Validates LLM responses
- Safety checks
- Content filtering

**Integration Point:** `gateway.validation_manager`

#### Feedback Loop
Integrates with Feedback Loop (`src/core/feedback_loop/`):
- Collects user feedback
- Improves response quality
- Tracks satisfaction

**Integration Point:** `gateway.feedback_loop`

### Where Used
- **All AI Components**: Gateway is the central LLM access point
- **FaaS Gateway Service**: REST API wrapper for gateway
- **Examples**: All examples use gateway for LLM operations
- **API Backend Services**: HTTP endpoints use gateway

---

## Detailed Function Documentation

This section provides comprehensive documentation for the function-driven API.

### Function Categories

The function-driven API is organized into several categories:

#### 1. Factory Functions

Factory functions create and configure gateways:

- **`create_gateway()`**: Create gateway with simplified configuration
- **`configure_gateway()`**: Create GatewayConfig with specified settings

#### 2. Text Generation Functions

High-level functions for text generation:

- **`generate_text()`**: Synchronous text generation
- **`generate_text_async()`**: Asynchronous text generation
- **`stream_text()`**: Streaming text generation

#### 3. Embedding Functions

Functions for generating embeddings:

- **`generate_embeddings()`**: Synchronous embedding generation
- **`generate_embeddings_async()`**: Asynchronous embedding generation

#### 4. Batch Processing Functions

Utilities for batch operations:

- **`batch_generate()`**: Batch text generation

### Key Functions

#### `create_gateway(providers, default_model, api_keys, **kwargs) -> LiteLLMGateway`

Creates a LiteLLM Gateway instance with validation and helpful error messages.

**Parameters:**
- `providers`: List of provider names (e.g., ['openai', 'anthropic'])
- `default_model`: Default model to use (e.g., 'gpt-4', 'claude-3-opus')
- `api_keys`: Dictionary mapping provider names to API keys
- `fallbacks`: List of fallback models to try if primary fails
- `timeout`: Request timeout in seconds (default: 60.0)
- `max_retries`: Maximum number of retries (default: 3)
- `retry_delay`: Delay between retries in seconds (default: 1.0)
- `**kwargs`: Additional configuration options

**Returns:** Configured `LiteLLMGateway` instance

**Raises:**
- `ConfigurationError`: If configuration is invalid with helpful suggestions

**Example:**
```python
gateway = create_gateway(
    providers=['openai'],
    default_model='gpt-4',
    api_keys={'openai': 'sk-...'}
)
```

**Validation:**
- Validates timeout, max_retries, retry_delay ranges
- Validates model name format
- Checks for API keys with helpful suggestions
- Provides clear error messages

#### `configure_gateway(model_list, fallbacks, timeout, max_retries, retry_delay) -> GatewayConfig`

Creates a GatewayConfig with specified settings.

**Parameters:**
- `model_list`: List of model configurations
- `fallbacks`: List of fallback models
- `timeout`: Request timeout (default: 60.0)
- `max_retries`: Maximum retries (default: 3)
- `retry_delay`: Retry delay (default: 1.0)

**Returns:** `GatewayConfig` instance

**Example:**
```python
config = configure_gateway(
    model_list=[...],
    fallbacks=['gpt-3.5-turbo'],
    timeout=120.0
)
gateway = LiteLLMGateway(config=config)
```

#### `generate_text(gateway, prompt, model=None, **kwargs) -> str`

Synchronous text generation convenience function.

**Parameters:**
- `gateway`: LiteLLMGateway instance
- `prompt`: Input prompt text
- `model`: Optional model name
- `**kwargs`: Additional generation parameters

**Returns:** Generated text string

**Example:**
```python
text = generate_text(gateway, "Hello, world!", model="gpt-4")
```

#### `async def generate_text_async(gateway, prompt, model=None, **kwargs) -> str`

Asynchronous text generation convenience function.

**Parameters:** Same as `generate_text()`

**Returns:** Generated text string

**Example:**
```python
text = await generate_text_async(gateway, "Hello, world!")
```

#### `stream_text(gateway, prompt, model=None, **kwargs) -> Iterator[str]`

Streaming text generation convenience function.

**Parameters:** Same as `generate_text()`

**Returns:** Iterator yielding text chunks

**Example:**
```python
for chunk in stream_text(gateway, "Tell me a story"):
    print(chunk, end="", flush=True)
```

#### `generate_embeddings(gateway, text, model=None, **kwargs) -> List[List[float]]`

Synchronous embedding generation convenience function.

**Parameters:**
- `gateway`: LiteLLMGateway instance
- `text`: Text to embed (string or list of strings)
- `model`: Optional embedding model name
- `**kwargs`: Additional parameters

**Returns:** List of embedding vectors

**Example:**
```python
embeddings = generate_embeddings(
    gateway,
    "This is a sample text",
    model="text-embedding-ada-002"
)
```

#### `async def generate_embeddings_async(gateway, text, model=None, **kwargs) -> List[List[float]]`

Asynchronous embedding generation convenience function.

**Parameters:** Same as `generate_embeddings()`

**Returns:** List of embedding vectors

#### `batch_generate(gateway, prompts, model=None, **kwargs) -> List[str]`

Batch text generation for multiple prompts.

**Parameters:**
- `gateway`: LiteLLMGateway instance
- `prompts`: List of prompt strings
- `model`: Optional model name
- `**kwargs`: Additional generation parameters

**Returns:** List of generated texts

**Example:**
```python
prompts = ["What is AI?", "What is ML?", "What is NLP?"]
results = batch_generate(gateway, prompts, model="gpt-4")
```

### Function Usage Examples

#### Basic Gateway Creation

```python
from src.core.litellm_gateway import create_gateway

# Simple creation with API key
gateway = create_gateway(
    providers=['openai'],
    default_model='gpt-4',
    api_keys={'openai': 'your-api-key'}
)
```

#### Multi-Provider Gateway

```python
# Create gateway with multiple providers
gateway = create_gateway(
    providers=['openai', 'anthropic'],
    default_model='gpt-4',
    api_keys={
        'openai': 'sk-openai-key',
        'anthropic': 'sk-anthropic-key'
    },
    fallbacks=['gpt-3.5-turbo']
)
```

#### Text Generation

```python
from src.core.litellm_gateway import create_gateway, generate_text_async

gateway = create_gateway(api_keys={'openai': 'key'}, default_model='gpt-4')

# Async generation (recommended)
text = await generate_text_async(
    gateway,
    prompt="Explain quantum computing",
    model="gpt-4",
    temperature=0.7
)
print(text)
```

#### Streaming Generation

```python
from src.core.litellm_gateway import create_gateway, stream_text

gateway = create_gateway(api_keys={'openai': 'key'}, default_model='gpt-4')

# Streaming for real-time responses
for chunk in stream_text(gateway, "Tell me a story"):
    print(chunk, end="", flush=True)
```

#### Embedding Generation

```python
from src.core.litellm_gateway import create_gateway, generate_embeddings_async

gateway = create_gateway(api_keys={'openai': 'key'}, default_model='gpt-4')

# Single text embedding
embeddings = await generate_embeddings_async(
    gateway,
    "This is a sample text",
    model="text-embedding-ada-002"
)

# Batch embeddings
texts = ["Text 1", "Text 2", "Text 3"]
all_embeddings = await generate_embeddings_async(
    gateway,
    texts,
    model="text-embedding-ada-002"
)
```

#### Batch Processing

```python
from src.core.litellm_gateway import create_gateway, batch_generate

gateway = create_gateway(api_keys={'openai': 'key'}, default_model='gpt-4')

# Generate multiple texts at once
prompts = [
    "What is artificial intelligence?",
    "What is machine learning?",
    "What is deep learning?"
]
results = batch_generate(gateway, prompts, model="gpt-4")
for prompt, result in zip(prompts, results):
    print(f"Q: {prompt}\nA: {result}\n")
```

#### Advanced Configuration

```python
from src.core.litellm_gateway import create_gateway, configure_gateway
from src.core.litellm_gateway.gateway import LiteLLMGateway

# Create custom configuration
config = configure_gateway(
    model_list=[
        {
            "model_name": "gpt-4",
            "litellm_params": {
                "model": "openai/gpt-4",
                "api_key": "sk-..."
            }
        }
    ],
    fallbacks=['gpt-3.5-turbo'],
    timeout=120.0,
    max_retries=5
)

# Create gateway with custom config
gateway = LiteLLMGateway(config=config)
```

### Function Best Practices

#### 1. Use Factory Functions

Always use factory functions instead of directly instantiating `LiteLLMGateway`:
```python
# Good: Use factory function
gateway = create_gateway(api_keys={'openai': 'key'}, default_model='gpt-4')

# Bad: Direct instantiation (unless you need full control)
from src.core.litellm_gateway.gateway import LiteLLMGateway, GatewayConfig
config = GatewayConfig(...)
gateway = LiteLLMGateway(config=config)
```

#### 2. Use Async Functions

Always prefer async functions for production:
```python
# Good: Async for better performance
text = await generate_text_async(gateway, "prompt")

# Bad: Synchronous blocks event loop
text = generate_text(gateway, "prompt")
```

#### 3. Provide API Keys Explicitly

Always provide API keys explicitly for clarity:
```python
# Good: Explicit API keys
gateway = create_gateway(
    api_keys={'openai': 'sk-...'},
    default_model='gpt-4'
)

# Bad: Relying on environment variables (less explicit)
gateway = create_gateway(default_model='gpt-4')  # May fail if env var not set
```

#### 4. Use Fallbacks

Configure fallback models for reliability:
```python
# Good: Fallback models
gateway = create_gateway(
    providers=['openai'],
    default_model='gpt-4',
    fallbacks=['gpt-3.5-turbo'],
    api_keys={'openai': 'key'}
)

# Bad: No fallback (single point of failure)
gateway = create_gateway(
    providers=['openai'],
    default_model='gpt-4',
    api_keys={'openai': 'key'}
)
```

#### 5. Handle Errors

Always handle errors appropriately:
```python
# Good: Error handling
try:
    text = await generate_text_async(gateway, "prompt")
except Exception as e:
    logger.error(f"Generation failed: {e}")
    # Handle error

# Bad: No error handling
text = await generate_text_async(gateway, "prompt")  # May crash
```

#### 6. Use Batch Processing

Use batch processing for multiple requests:
```python
# Good: Batch processing
prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]
results = batch_generate(gateway, prompts)

# Bad: Sequential processing
results = []
for prompt in prompts:
    result = await generate_text_async(gateway, prompt)
    results.append(result)
```

#### 7. Use Streaming for Long Responses

Use streaming for better user experience:
```python
# Good: Streaming for long responses
for chunk in stream_text(gateway, "Long prompt"):
    print(chunk, end="")

# Bad: Waiting for complete response
text = await generate_text_async(gateway, "Long prompt")  # Blocks
print(text)
```

#### 8. Validate Configuration

Let the factory function validate configuration:
```python
# Good: Factory function validates
gateway = create_gateway(
    timeout=120.0,  # Validated automatically
    max_retries=5
)

# Bad: Manual validation (error-prone)
if timeout < 1.0 or timeout > 300.0:
    raise ValueError("Invalid timeout")
# ... manual validation code
```

---

## Additional Resources

### Documentation
- **[Gateway Troubleshooting](../../../docs/troubleshooting/litellm_gateway_troubleshooting.md)** - Common issues and solutions

### Related Components
- **[Rate Limiter](rate_limiter.py)** - Rate limiting implementation
- **[KV Cache](kv_cache.py)** - Attention caching
- **[Cache Mechanism](../cache_mechanism/README.md)** - Response caching
- **[LLMOps](../llmops/README.md)** - Operations tracking
- **[Validation & Guardrails](../validation/README.md)** - Output validation
- **[Feedback Loop](../feedback_loop/README.md)** - Feedback collection

### External Resources
- **[LiteLLM Documentation](https://docs.litellm.ai/)** - Official LiteLLM docs
- **[OpenAI API Reference](https://platform.openai.com/docs/api-reference)** - OpenAI API docs
- **[Anthropic API Reference](https://docs.anthropic.com/claude/reference)** - Anthropic API docs
- **[Async/Await in Python](https://docs.python.org/3/library/asyncio.html)** - Async programming

### Examples
- **[Basic Gateway Example](../../../../examples/basic_usage/03_litellm_gateway_basic.py)** - Simple gateway usage
- **[Gateway with Caching Example](../../../../examples/)** - Caching examples
- **[Multi-Provider Example](../../../../examples/)** - Multiple providers

### Best Practices References
- **[Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)** - Fault tolerance
- **[Rate Limiting Strategies](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)** - Rate limiting guide
- **[Caching Strategies](https://aws.amazon.com/caching/)** - Caching best practices
