# MOTADATA - LITELLM GATEWAY CLASS DOCUMENTATION

**Complete class documentation for the LiteLLMGateway class providing unified interface for multiple LLM providers.**

## Overview

The `gateway.py` file contains the core `LiteLLMGateway` class implementation, which provides a unified interface for interacting with multiple Large Language Model (LLM) providers through LiteLLM. This gateway serves as the central AI operations hub for the entire SDK, abstracting provider-specific complexities and enabling seamless integration across all AI components.

**Primary Functionality:**
- Unified LLM provider access (OpenAI, Anthropic, Google, Cohere, etc.)
- Text generation (synchronous and asynchronous)
- Embedding generation for vector operations
- Streaming responses for real-time applications
- Rate limiting and request management
- Circuit breaker for fault tolerance
- Request deduplication and batching
- Caching for cost optimization
- KV cache for attention optimization
- LLMOps integration for monitoring and cost tracking
- Health monitoring and validation

## Code Explanation

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

## Usage Instructions

### Basic Gateway Creation

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

### Text Generation

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

### Streaming Generation

```python
# Streaming for real-time responses
async for chunk in gateway.generate_stream(
    prompt="Tell me a story about AI",
    model="gpt-4"
):
    print(chunk, end="", flush=True)
```

### Embedding Generation

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

### Multi-Provider Configuration

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

### With Caching

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

### With Rate Limiting

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

### Health Monitoring

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

### Prerequisites

1. **Python 3.10+**: Required for type hints and async/await
2. **Dependencies**: Install via `pip install -r requirements.txt`
   - `litellm`: Core LLM library
   - `pydantic`: For data validation
   - `dragonfly`: Optional, for Dragonfly caching
3. **API Keys**: Configure provider API keys:
   - OpenAI: `OPENAI_API_KEY`
   - Anthropic: `ANTHROPIC_API_KEY`
   - Google: `GOOGLE_API_KEY`
   - Or pass via `api_keys` parameter
4. **Optional Dependencies**:
   - Dragonfly: For distributed caching
   - PostgreSQL: For persistent storage (if needed)

## Connection to Other Components

### Agent Framework
The Agent Framework (`src/core/agno_agent_framework/`) uses the gateway for all LLM operations:
- Agents inject gateway during initialization
- All agent reasoning and generation goes through gateway
- Gateway handles rate limiting per agent/tenant

**Integration Point:** `agent.gateway` attribute

### RAG System
The RAG System (`src/core/rag/`) uses the gateway for:
- Embedding generation for document indexing
- Text generation for query responses
- Both operations benefit from gateway caching

**Integration Point:** `rag_system.gateway` attribute

### Cache Mechanism
The gateway integrates with Cache Mechanism (`src/core/cache_mechanism/`):
- Caches generation responses
- Caches embeddings
- Reduces costs and improves performance

**Integration Point:** `gateway.cache` attribute

### KV Cache
The gateway uses KV Cache (`src/core/litellm_gateway/kv_cache.py`):
- Attention key-value caching
- Optimizes repeated generation requests
- Reduces token usage

**Integration Point:** `gateway.kv_cache` attribute

### Rate Limiter
The gateway uses Rate Limiter (`src/core/litellm_gateway/rate_limiter.py`):
- Per-tenant rate limiting
- Request batching and deduplication
- Prevents API quota exhaustion

**Integration Point:** `gateway.rate_limiters` and `gateway.deduplicator`

### Circuit Breaker
Uses Circuit Breaker (`src/core/utils/circuit_breaker.py`):
- Fault tolerance for provider failures
- Automatic recovery
- Prevents cascade failures

**Integration Point:** `gateway.circuit_breaker`

### LLMOps
Integrates with LLMOps (`src/core/llmops/`):
- Tracks all LLM operations
- Monitors costs and usage
- Provides analytics

**Integration Point:** `gateway.llmops`

### Validation Manager
Uses Validation Manager (`src/core/validation/`):
- Validates LLM responses
- Safety checks
- Content filtering

**Integration Point:** `gateway.validation_manager`

### Feedback Loop
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

## Best Practices

### 1. Use Async Methods
Always prefer async methods for production:
```python
# Good: Async for better performance
response = await gateway.generate_async("prompt")

# Bad: Synchronous blocks event loop
response = gateway.generate("prompt")
```

### 2. Enable Caching
Enable caching to reduce costs:
```python
# Good: Caching enabled
config = GatewayConfig(enable_caching=True, cache_ttl=3600)
gateway = LiteLLMGateway(config=config)

# Bad: No caching (higher costs)
gateway = LiteLLMGateway()  # Caching disabled by default
```

### 3. Configure Rate Limiting
Always configure rate limiting for production:
```python
# Good: Rate limiting configured
config = GatewayConfig(
    enable_rate_limiting=True,
    rate_limit_config=RateLimitConfig(requests_per_minute=60)
)

# Bad: No rate limiting (risk of quota exhaustion)
config = GatewayConfig()
```

### 4. Use Tenant IDs
Always provide tenant_id for multi-tenant applications:
```python
# Good: Tenant-scoped operations
response = await gateway.generate_async(
    prompt="Hello",
    tenant_id="tenant_123"
)

# Bad: Missing tenant_id in multi-tenant system
response = await gateway.generate_async(prompt="Hello")
```

### 5. Handle Errors
Always handle errors appropriately:
```python
# Good: Error handling
try:
    response = await gateway.generate_async("prompt")
except Exception as e:
    logger.error(f"Generation failed: {e}")
    # Handle error

# Bad: No error handling
response = await gateway.generate_async("prompt")  # May crash
```

### 6. Monitor Health
Regularly check gateway health:
```python
# Good: Health monitoring
health = gateway.check_health()
if health.status != "healthy":
    # Alert or handle unhealthy state
    logger.warning(f"Gateway unhealthy: {health.details}")
```

### 7. Use Streaming for Long Responses
Use streaming for better user experience:
```python
# Good: Streaming for long responses
async for chunk in gateway.generate_stream("Long prompt"):
    print(chunk, end="")

# Bad: Waiting for complete response
response = await gateway.generate_async("Long prompt")  # Blocks
print(response.text)
```

### 8. Configure Timeouts
Set appropriate timeouts:
```python
# Good: Reasonable timeout
config = GatewayConfig(timeout=120.0)  # 2 minutes

# Bad: Too short (may timeout) or too long (blocks)
config = GatewayConfig(timeout=5.0)  # Too short
```

### 9. Use Model Routing
Configure model routing for reliability:
```python
# Good: Fallback models
config = GatewayConfig(
    model_list=[...],
    fallbacks=["gpt-3.5-turbo"]  # Fallback if primary fails
)

# Bad: Single model (no fallback)
config = GatewayConfig(model_list=[{"model_name": "gpt-4", ...}])
```

### 10. Track Usage
Monitor usage and costs:
```python
# Good: Track usage
stats = gateway.get_usage_stats(tenant_id="tenant_123")
logger.info(f"Usage: {stats['total_requests']} requests, ${stats['total_cost']:.2f}")

# Bad: No usage tracking
# May exceed budget unexpectedly
```

## Additional Resources

### Documentation
- **[Gateway README](README.md)** - Complete gateway guide
- **[Gateway Functions Documentation](functions.md)** - Factory and convenience functions
- **[Gateway Troubleshooting](../../../docs/troubleshooting/litellm_gateway_troubleshooting.md)** - Common issues

### Related Components
- **[Rate Limiter](rate_limiter.py)** - Rate limiting implementation
- **[KV Cache](kv_cache.py)** - Attention caching
- **[Cache Mechanism](../../cache_mechanism/README.md)** - Response caching
- **[LLMOps](../../llmops/README.md)** - Operations tracking

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

