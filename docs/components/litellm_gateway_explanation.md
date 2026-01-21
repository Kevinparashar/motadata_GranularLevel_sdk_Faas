# LiteLLM Gateway - Comprehensive Component Explanation

## Overview

The LiteLLM Gateway is the central AI operations hub for the entire SDK. It provides a unified interface for interacting with multiple Large Language Model (LLM) providers, abstracting away provider-specific complexities and enabling seamless integration across all AI components.

## Table of Contents

1. [Gateway Operations](#gateway-operations)
2. [Response Caching](#response-caching)
3. [Rate Limiting and Queuing](#rate-limiting-and-queuing)
4. [Request Batching and Deduplication](#request-batching-and-deduplication)
5. [Circuit Breaker](#circuit-breaker)
6. [Health Monitoring](#health-monitoring)
7. [LLMOps Integration](#llmops-integration)
8. [Validation and Guardrails](#validation-and-guardrails)
9. [Feedback Loop](#feedback-loop)
10. [Exception Handling](#exception-handling)
11. [Functions](#functions)
12. [Workflow](#workflow)
13. [Customization](#customization)

---

## Gateway Operations

### Functionality

The gateway provides unified access to multiple LLM providers:
- **Text Generation**: Synchronous and asynchronous text generation
- **Streaming**: Real-time token streaming for interactive applications
- **Embeddings**: Vector embedding generation for RAG and similarity search
- **Function Calling**: Support for LLM function calling capabilities
- **Multi-Provider Support**: OpenAI, Anthropic, Google, Cohere, and more

### Code Examples

#### Basic Gateway Creation

```python
from src.core.litellm_gateway import LiteLLMGateway, GatewayConfig

# Create gateway with configuration
config = GatewayConfig(
    model_list=[
        {"model_name": "gpt-4", "litellm_params": {"model": "gpt-4"}},
        {"model_name": "claude-3", "litellm_params": {"model": "claude-3-opus"}}
    ],
    timeout=60.0,
    max_retries=3
)

gateway = LiteLLMGateway(config=config)
```

#### Text Generation

```python
# Synchronous generation
response = gateway.generate(
    prompt="Explain quantum computing",
    model="gpt-4",
    tenant_id="tenant_123"
)
print(response.text)

# Asynchronous generation
response = await gateway.generate_async(
    prompt="Explain quantum computing",
    model="gpt-4",
    tenant_id="tenant_123"
)
print(response.text)
```

#### Streaming

```python
# Stream text generation
async for chunk in gateway.generate_stream_async(
    prompt="Tell me a story",
    model="gpt-4",
    tenant_id="tenant_123"
):
    print(chunk, end="", flush=True)
```

#### Embeddings

```python
# Generate embeddings
response = await gateway.embed_async(
    texts=["Hello world", "AI is amazing"],
    model="text-embedding-3-small",
    tenant_id="tenant_123"
)
print(response.embeddings)
```

---

## Response Caching

### Functionality

Response caching provides:
- **Automatic Caching**: Caches responses automatically
- **TTL Support**: Configurable time-to-live
- **Cache Invalidation**: Manual and automatic invalidation
- **Cost Reduction**: Reduces API costs by avoiding duplicate requests
- **KV Cache**: Stores attention key-value pairs for LLM generation optimization, reducing latency by 20-50% for long contexts (see [Advanced Features](advanced_features.md#kv-cache-for-llm-generation))

### Code Examples

```python
# Enable KV caching in gateway config
config = GatewayConfig(
    enable_kv_caching=True,
    kv_cache_default_ttl=3600,  # 1 hour
    kv_cache_max_size=1000
)

gateway = LiteLLMGateway(config=config)

# Generation automatically uses KV cache for repeated contexts
response = await gateway.generate_async(
    prompt="Long context with repeated information...",
    model="gpt-4",
    tenant_id="tenant_123"
)
```

**Note**: For detailed KV cache documentation, see [Advanced Features](advanced_features.md#kv-cache-for-llm-generation).

---

## Rate Limiting and Queuing

### Functionality

Advanced rate limiting with request queuing:
- **Token Bucket Algorithm**: Smooth rate limiting
- **Request Queuing**: Queues requests when rate limit exceeded
- **Per-Tenant Limits**: Tenant-specific rate limits
- **Burst Support**: Allows burst requests within limits

### Code Examples

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

# Requests automatically respect rate limits
response = await gateway.generate_async(
    prompt="Test",
    model="gpt-4",
    tenant_id="tenant_123"
)
```

---

## Request Batching and Deduplication

### Functionality

- **Request Batching**: Groups similar requests together
- **Request Deduplication**: Prevents processing identical requests
- **Automatic Processing**: Automatic batching and deduplication

### Code Examples

```python
# Enable batching and deduplication in config
config = GatewayConfig(
    enable_request_batching=True,
    enable_request_deduplication=True
)

gateway = LiteLLMGateway(config=config)

# Identical requests are deduplicated
response1 = await gateway.generate_async("What is AI?", tenant_id="tenant_123")
response2 = await gateway.generate_async("What is AI?", tenant_id="tenant_123")
# response2 uses cached result from response1
```

---

## Circuit Breaker

### Functionality

Circuit breaker for provider failures:
- **Automatic Failure Detection**: Monitors provider health
- **Provider Isolation**: Isolates failing providers
- **Automatic Recovery**: Attempts recovery after timeout

### Code Examples

```python
from src.core.utils.circuit_breaker import CircuitBreakerConfig

config = GatewayConfig(
    enable_circuit_breaker=True,
    circuit_breaker_config=CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=2,
        timeout=60.0
    )
)

gateway = LiteLLMGateway(config=config)
# Circuit breaker automatically protects LLM calls
```

---

## Health Monitoring

### Functionality

Comprehensive health monitoring:
- **Provider Health Status**: Tracks health per provider
- **Success/Failure Rates**: Records rates per provider
- **Error Classification**: Classifies and tracks errors

### Code Examples

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
#   }
# }
```

---

## LLMOps Integration

### Functionality

Comprehensive LLM operations logging:
- **Operation Logging**: Logs all LLM operations
- **Token Usage Tracking**: Tracks token usage
- **Cost Calculation**: Calculates and tracks costs
- **Latency Monitoring**: Monitors response times

### Code Examples

```python
# Get LLMOps metrics
metrics = gateway.get_llmops_metrics(
    tenant_id="tenant_123",
    time_range_hours=24
)
print(f"Total operations: {metrics['total_operations']}")
print(f"Total cost: ${metrics['total_cost_usd']:.2f}")

# Get cost summary
cost_summary = gateway.get_cost_summary(tenant_id="tenant_123")
print(f"Cost per 1K tokens: ${cost_summary['cost_per_1k_tokens']:.4f}")
```

---

## Validation and Guardrails

### Functionality

Output validation and guardrails:
- **Content Filtering**: Blocks outputs with blocked patterns
- **Format Validation**: Validates JSON and ITSM formats
- **Compliance Checking**: Ensures ITIL compliance
- **Validation Levels**: STRICT, MODERATE, LENIENT

### Code Examples

```python
from src.core.validation import ValidationLevel

config = GatewayConfig(
    enable_validation=True,
    validation_level=ValidationLevel.STRICT
)

gateway = LiteLLMGateway(config=config)

# Validation is automatic
response = await gateway.generate_async(
    prompt="Generate incident response",
    model="gpt-4",
    tenant_id="tenant_123"
)
# Output is automatically validated
```

---

## Feedback Loop

### Functionality

Feedback collection and processing:
- **Feedback Collection**: Records user feedback
- **Automatic Processing**: Processes feedback automatically
- **Learning Insights**: Extracts learning insights

### Code Examples

```python
from src.core.feedback_loop import FeedbackType

# Record feedback
feedback_id = gateway.record_feedback(
    query="How do I reset my password?",
    response="You can reset...",
    feedback_type=FeedbackType.CORRECTION,
    content="Actually, the process is different...",
    tenant_id="tenant_123"
)

# Get learning insights
insights = gateway.feedback_loop.get_learning_insights(tenant_id="tenant_123")
print(f"Average rating: {insights['average_rating']}")
```

---

## Exception Handling

### Error Types

- **Provider Failures**: Handled with circuit breaker and fallbacks
- **Rate Limiting**: Handled with queuing and retries
- **Network Errors**: Handled with retries and timeouts
- **Validation Errors**: Handled with detailed error messages

### Code Examples

```python
try:
    response = await gateway.generate_async(
        prompt="Test",
        model="gpt-4",
        tenant_id="tenant_123"
    )
except Exception as e:
    # Gateway handles errors automatically
    # Check health for provider status
    health = await gateway.get_health()
    print(f"Provider health: {health['provider_health']}")
```

---

## Functions

### Factory Functions

```python
from src.core.litellm_gateway import create_gateway

gateway = create_gateway(
    providers=["openai", "anthropic"],
    default_model="gpt-4",
    api_keys={"openai": "sk-...", "anthropic": "sk-..."}
)
```

### Convenience Functions

```python
from src.core.litellm_gateway import (
    generate_text,
    generate_embeddings,
    stream_text
)

# Generate text
text = generate_text(gateway, "What is AI?", model="gpt-4")

# Generate embeddings
embeddings = generate_embeddings(gateway, ["Hello", "World"])

# Stream text
async for chunk in stream_text(gateway, "Tell me a story"):
    print(chunk, end="")
```

---

## Workflow

### Component Placement in SDK Architecture

The LiteLLM Gateway is positioned in the **Infrastructure Layer** and serves as the central hub for all LLM operations:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SDK ARCHITECTURE OVERVIEW                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ API Backend  │  │   RAG System  │  │   Agents     │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          │                  │                  │
          │  ┌───────────────▼───────────────────┐                │
          │  │   LITELLM GATEWAY (Infrastructure) │                │
          │  │   ┌─────────────────────────────┐  │                │
          │  │   │  Core Operations:           │  │                │
          │  │   │  - generate()               │  │                │
          │  │   │  - embed()                  │  │                │
          │  │   │  - stream()                 │  │                │
          │  │   └─────────────────────────────┘  │                │
          │  │   ┌─────────────────────────────┐  │                │
          │  │   │  Advanced Features:         │  │                │
          │  │   │  - Rate Limiting            │  │                │
          │  │   │  - Circuit Breaker          │  │                │
          │  │   │  - Request Deduplication    │  │                │
          │  │   │  - Request Batching         │  │                │
          │  │   │  - Health Monitoring        │  │                │
          │  │   │  - LLMOps                   │  │                │
          │  │   │  - Validation               │  │                │
          │  │   │  - Feedback Loop            │  │                │
          │  │   └─────────────────────────────┘  │                │
          │  └─────────────────────────────────────┘                │
          │                  │                                      │
┌─────────┼──────────────────┼─────────────────────────────────────┐
│         │                  │                                      │
│  ┌──────▼──────┐  ┌────────▼────────┐  ┌──────────────┐         │
│  │   LLM       │  │   Observability │  │   Cache      │         │
│  │  Providers  │  │                 │  │  Mechanism   │         │
│  │             │  │                 │  │              │         │
│  │ - OpenAI    │  │ - Logging       │  │ - Response   │         │
│  │ - Anthropic │  │ - Tracing       │  │   Caching    │         │
│  │ - Google    │  │ - Metrics       │  │ - Embedding   │         │
│  │ - Cohere    │  │                 │  │   Caching    │         │
│  └─────────────┘  └─────────────────┘  └──────────────┘         │
│                                                                   │
│                    INFRASTRUCTURE LAYER                           │
└───────────────────────────────────────────────────────────────────┘
```

### Detailed Request Processing Workflow

The following diagram shows the complete flow of a request through the gateway with all components and their interactions:

```
┌─────────────────────────────────────────────────────────────────┐
│              GATEWAY REQUEST PROCESSING WORKFLOW                 │
└─────────────────────────────────────────────────────────────────┘

    [Client Request: generate_async()]
           │
           │ Parameters:
           │ - prompt: str
           │ - model: str
           │ - tenant_id: Optional[str]
           │ - **kwargs: Any
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 1: Request Pre-Processing                          │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ gateway.generate_async(prompt, model, tenant_id)  │  │
    │  │                                                   │  │
    │  │ Code Flow:                                       │  │
    │  │ 1. Validate input parameters                     │  │
    │  │ 2. Normalize model name                          │  │
    │  │ 3. Extract tenant_id (from param or context)    │  │
    │  │ 4. Create request_id for tracking                │  │
    │  │                                                   │  │
    │  │ Parameters Validated:                            │  │
    │  │ - prompt: Must be non-empty string              │  │
    │  │ - model: Must be valid model name               │  │
    │  │ - tenant_id: Optional, used for isolation      │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 2: Request Deduplication Check                    │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ if gateway.deduplicator:                          │  │
    │  │     cache_key = hash(prompt + model + tenant_id)  │  │
    │  │     cached_result = deduplicator.get(cache_key)   │  │
    │  │     if cached_result:                             │  │
    │  │         return cached_result  # Early return      │  │
    │  │                                                   │  │
    │  │ Parameters Used:                                  │  │
    │  │ - prompt: str (part of cache key)                │  │
    │  │ - model: str (part of cache key)                 │  │
    │  │ - tenant_id: Optional[str] (part of cache key)  │  │
    │  │                                                   │  │
    │  │ Deduplication Config:                            │  │
    │  │ - ttl: float = 300.0 (5 minutes)                 │  │
    │  │ - hash_function: SHA256                          │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 3: Rate Limiting Check                            │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ rate_limiter = gateway._get_rate_limiter(tenant_id)│  │
    │  │                                                   │  │
    │  │ if rate_limiter:                                  │  │
    │  │     # Token bucket algorithm                      │  │
    │  │     tokens_needed = estimate_tokens(prompt)      │  │
    │  │     if not rate_limiter.acquire(tokens_needed):  │  │
    │  │         if enable_queuing:                        │  │
    │  │             # Queue request                       │  │
    │  │             await rate_limiter.queue_request(    │  │
    │  │                 request,                         │  │
    │  │                 timeout=queue_timeout            │  │
    │  │             )                                     │  │
    │  │         else:                                     │  │
    │  │             raise RateLimitError                 │  │
    │  │                                                   │  │
    │  │ Rate Limiting Parameters:                        │  │
    │  │ - requests_per_minute: int (default: 60)        │  │
    │  │ - tokens_per_minute: int (default: 90000)       │  │
    │  │ - enable_queuing: bool (default: True)          │  │
    │  │ - queue_timeout: float (default: 30.0 seconds)   │  │
    │  │ - burst_size: int (default: 10)                 │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 4: Circuit Breaker Check                           │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ if gateway.circuit_breaker:                       │  │
    │  │     state = circuit_breaker.get_state()          │  │
    │  │     if state == CircuitState.OPEN:                │  │
    │  │         raise CircuitBreakerOpenError             │  │
    │  │     elif state == CircuitState.HALF_OPEN:         │  │
    │  │         # Allow one request to test recovery      │  │
    │  │         pass                                      │  │
    │  │                                                   │  │
    │  │ Circuit Breaker Parameters:                       │  │
    │  │ - failure_threshold: int (default: 5)           │  │
    │  │   Number of failures before opening circuit     │  │
    │  │ - success_threshold: int (default: 2)           │  │
    │  │   Number of successes to close circuit          │  │
    │  │ - timeout: float (default: 60.0 seconds)        │  │
    │  │   Time to wait before half-open state           │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 5: Request Batching (if enabled)                   │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ if gateway.batcher:                                │  │
    │  │     batched_request = batcher.add_request(       │  │
    │  │         request,                                  │  │
    │  │         batch_size=10,                           │  │
    │  │         batch_timeout=0.5                        │  │
    │  │     )                                             │  │
    │  │     if batched_request:                          │  │
    │  │         # Wait for batch to fill or timeout      │  │
    │  │         await batcher.wait_for_batch()           │  │
    │  │                                                   │  │
    │  │ Batching Parameters:                              │  │
    │  │ - batch_size: int (default: 10)                 │  │
    │  │   Number of requests per batch                   │  │
    │  │ - batch_timeout: float (default: 0.5 seconds)   │  │
    │  │   Max wait time for batch to fill               │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 6: LLM API Call                                    │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ start_time = time.time()                           │  │
    │  │                                                   │  │
    │  │ if gateway.router:                                │  │
    │  │     response = await gateway.router.acompletion( │  │
    │  │         model=model,                              │  │
    │  │         messages=[{"role": "user", "content": prompt}],│
    │  │         metadata={"tenant_id": tenant_id}         │  │
    │  │     )                                             │  │
    │  │ else:                                             │  │
    │  │     response = await acompletion(                 │  │
    │  │         model=model,                              │  │
    │  │         messages=[{"role": "user", "content": prompt}],│
    │  │         api_key=os.getenv(f"{provider}_API_KEY")  │  │
    │  │     )                                             │  │
    │  │                                                   │  │
    │  │ Parameters Passed to LLM:                         │  │
    │  │ - model: str (e.g., "gpt-4", "claude-3-opus")    │  │
    │  │ - messages: List[Dict] (conversation history)   │  │
    │  │ - temperature: float (0.0-2.0, default: 1.0)    │  │
    │  │ - max_tokens: int (default: None)               │  │
    │  │ - metadata: Dict (includes tenant_id)           │  │
    │  │                                                   │  │
    │  │ Response Structure:                              │  │
    │  │ - choices: List[Dict] (LLM responses)            │  │
    │  │ - usage: Dict (token usage)                     │  │
    │  │ - model: str (model used)                        │  │
    │  │                                                   │  │
    │  │ latency = time.time() - start_time               │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 7: LLMOps Logging                                 │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ if gateway.llmops:                                 │  │
    │  │     gateway.llmops.log_operation(                  │  │
    │  │         operation_type=LLMOperationType.COMPLETION,│
    │  │         model=model,                               │  │
    │  │         prompt_tokens=response.usage.prompt_tokens,│
    │  │         completion_tokens=response.usage.completion_tokens,│
    │  │         total_tokens=response.usage.total_tokens,  │  │
    │  │         latency_ms=latency * 1000,                │  │
    │  │         status=LLMOperationStatus.SUCCESS,        │  │
    │  │         tenant_id=tenant_id,                      │  │
    │  │         cost_usd=calculate_cost(...)              │  │
    │  │     )                                             │  │
    │  │                                                   │  │
    │  │ LLMOps Tracks:                                     │  │
    │  │ - Operation type (completion, embedding, etc.)   │  │
    │  │ - Token usage (prompt, completion, total)        │  │
    │  │ - Latency (request to response time)            │  │
    │  │ - Cost (calculated per model)                   │  │
    │  │ - Status (success, error)                       │  │
    │  │ - Tenant ID (for multi-tenant tracking)        │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 8: Response Validation                            │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ if gateway.validation_manager:                    │  │
    │  │     text = extract_text_from_response(response)   │  │
    │  │     validation_result = validation_manager.validate(│
    │  │         text,                                     │  │
    │  │         level=gateway.config.validation_level     │  │
    │  │     )                                             │  │
    │  │                                                   │  │
    │  │     if not validation_result.is_valid:           │  │
    │  │         raise ValidationError(                    │  │
    │  │             message=validation_result.errors     │  │
    │  │         )                                         │  │
    │  │                                                   │  │
    │  │ Validation Checks:                                │  │
    │  │ - Content filtering (blocked patterns)          │  │
    │  │ - PII detection                                  │  │
    │  │ - Format validation (JSON, ITSM formats)        │  │
    │  │ - Compliance checking (ITIL, security)           │  │
    │  │                                                   │  │
    │  │ Validation Levels:                               │  │
    │  │ - STRICT: All checks enforced                   │  │
    │  │ - MODERATE: Most checks enforced                │  │
    │  │ - LENIENT: Basic checks only                    │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 9: Health Metrics Update                          │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ gateway.provider_health[provider] = {              │  │
    │  │     "status": "healthy",                          │  │
    │  │     "last_success": datetime.now(),               │  │
    │  │     "success_count": count + 1,                   │  │
    │  │     "failure_count": 0,                           │  │
    │  │     "response_time_ms": latency * 1000,            │  │
    │  │     "last_error": None                            │  │
    │  │ }                                                  │  │
    │  │                                                   │  │
    │  │ Health Metrics Tracked:                           │  │
    │  │ - Status: "healthy", "degraded", "unhealthy"     │  │
    │  │ - Success/failure rates                          │  │
    │  │ - Response times (p50, p95, p99)                │  │
    │  │ - Last error message                             │  │
    │  │ - Error classification                           │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 10: Response Formatting                           │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ response = GenerateResponse(                        │  │
    │  │     text=extract_text(response),                   │  │
    │  │     model=response.model,                           │  │
    │  │     usage={                                        │  │
    │  │         "prompt_tokens": response.usage.prompt_tokens,│
    │  │         "completion_tokens": response.usage.completion_tokens,│
    │  │         "total_tokens": response.usage.total_tokens│
    │  │     },                                             │  │
    │  │     finish_reason=response.choices[0].finish_reason,│
    │  │     raw_response=response                          │  │
    │  │ )                                                  │  │
    │  │                                                   │  │
    │  │ GenerateResponse Fields:                          │  │
    │  │ - text: str (generated text)                     │  │
    │  │ - model: str (model used)                        │  │
    │  │ - usage: Dict (token usage)                      │  │
    │  │ - finish_reason: str (stop, length, etc.)        │  │
    │  │ - raw_response: Dict (original LLM response)     │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 11: Cache Result (Deduplication)                  │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ if gateway.deduplicator:                          │  │
    │  │     cache_key = hash(prompt + model + tenant_id)  │  │
    │  │     gateway.deduplicator.set(                     │  │
    │  │         cache_key,                                │  │
    │  │         response,                                 │  │
    │  │         ttl=300.0  # 5 minutes                   │  │
    │  │     )                                             │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    [Return GenerateResponse to Caller]
```

### Error Handling Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    ERROR HANDLING WORKFLOW                       │
└─────────────────────────────────────────────────────────────────┘

    [Error Occurs During Processing]
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  Error Classification                                    │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ error_type = gateway._classify_error(error)      │  │
    │  │                                                   │  │
    │  │ Error Types:                                      │  │
    │  │ - RateLimitError: Rate limit exceeded            │  │
    │  │ - CircuitBreakerError: Circuit breaker open      │  │
    │  │ - NetworkError: Network/timeout issues           │  │
    │  │ - ProviderError: Provider-specific errors        │  │
    │  │ - ValidationError: Output validation failed      │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ├─────────────────┬─────────────────┬──────────────┘
           │                 │                 │
           ▼                 ▼                 ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ RateLimit│    │ Circuit  │    │ Provider │
    │  Error   │    │ Breaker  │    │  Error   │
    └────┬─────┘    └────┬─────┘    └────┬─────┘
         │              │              │
         │              │              │
         ▼              ▼              ▼
    ┌─────────────────────────────────────────┐
    │  Error Handling Actions                 │
    │  ┌───────────────────────────────────┐  │
    │  │ RateLimitError:                   │  │
    │  │ - Queue request (if enabled)      │  │
    │  │ - Return 429 status               │  │
    │  │                                   │  │
    │  │ CircuitBreakerError:             │  │
    │  │ - Update circuit breaker state   │  │
    │  │ - Try fallback provider          │  │
    │  │ - Return 503 status              │  │
    │  │                                   │  │
    │  │ ProviderError:                   │  │
    │  │ - Update provider health         │  │
    │  │ - Try fallback provider          │  │
    │  │ - Log to LLMOps                  │  │
    │  │ - Retry (if retries remaining)  │  │
    │  └───────────────────────────────────┘  │
    └─────────────────────────────────────────┘
           │
           ▼
    [Return Error Response or Retry]
```

### Parameter Details

#### GatewayConfig Parameters

```python
class GatewayConfig(BaseModel):
    model_list: List[Dict[str, Any]] = []  # Model configurations
                                          # Each dict contains:
                                          #   - "model_name": str
                                          #   - "litellm_params": Dict
                                          #     - "model": str (provider model)
                                          #     - "api_key": str (optional)

    fallbacks: Optional[List[str]] = None  # Fallback model names
                                          # Used when primary model fails
                                          # Example: ["gpt-4", "gpt-3.5-turbo"]

    timeout: float = 60.0  # Request timeout in seconds
                          # Applies to all LLM operations
                          # Range: 1.0 - 300.0 seconds

    max_retries: int = 3  # Maximum retry attempts
                         # Applies to transient failures
                         # Range: 0 - 10

    retry_delay: float = 1.0  # Delay between retries (seconds)
                             # Uses exponential backoff
                             # Range: 0.1 - 10.0 seconds

    # Advanced Feature Flags
    enable_circuit_breaker: bool = True  # Enable circuit breaker
    enable_rate_limiting: bool = True    # Enable rate limiting
    enable_request_deduplication: bool = True  # Enable deduplication
    enable_request_batching: bool = False  # Enable request batching
    enable_health_monitoring: bool = True  # Enable health monitoring
    enable_llmops: bool = True  # Enable LLMOps logging
    enable_validation: bool = True  # Enable output validation
    enable_feedback_loop: bool = True  # Enable feedback collection

    # Advanced Feature Configs
    rate_limit_config: Optional[RateLimitConfig] = None
    circuit_breaker_config: Optional[CircuitBreakerConfig] = None
    validation_level: ValidationLevel = ValidationLevel.MODERATE
```

#### generate_async Parameters

```python
async def generate_async(
    self,
    prompt: str,                    # Input prompt text
                                   # Required, non-empty string
                                   # Can include variables for template rendering

    model: str,                     # LLM model name
                                   # Examples: "gpt-4", "claude-3-opus"
                                   # Must be in model_list or configured

    tenant_id: Optional[str] = None,  # Tenant identifier
                                   # Used for:
                                   #   - Rate limiting (per-tenant)
                                   #   - Cost tracking (per-tenant)
                                   #   - Cache isolation (per-tenant)
                                   #   - Logging and metrics

    temperature: Optional[float] = None,  # Sampling temperature
                                        # Range: 0.0 - 2.0
                                        # Lower = more deterministic
                                        # Higher = more creative
                                        # Default: model default (usually 1.0)

    max_tokens: Optional[int] = None,  # Maximum tokens to generate
                                      # Limits response length
                                      # Range: 1 - model_max_tokens
                                      # Default: None (no limit)

    stream: bool = False,           # Enable streaming
                                   # If True, returns AsyncIterator
                                   # If False, returns GenerateResponse
                                   # Default: False

    functions: Optional[List[Dict]] = None,  # Function calling schemas
                                           # List of function definitions
                                           # Each dict contains:
                                           #   - "name": str
                                           #   - "description": str
                                           #   - "parameters": Dict (JSON schema)

    **kwargs: Any                   # Additional LLM parameters
                                   # Passed directly to LLM provider
                                   # Examples:
                                   #   - top_p: float
                                   #   - frequency_penalty: float
                                   #   - presence_penalty: float
) -> GenerateResponse | AsyncIterator[str]
```

#### RateLimitConfig Parameters

```python
class RateLimitConfig:
    requests_per_minute: int = 60  # Max requests per minute
                                  # Applies per tenant
                                  # Range: 1 - 10000

    tokens_per_minute: int = 90000  # Max tokens per minute
                                   # Applies per tenant
                                   # Range: 1000 - 1000000

    enable_queuing: bool = True  # Enable request queuing
                                # If True, queue requests when limit exceeded
                                # If False, return error immediately

    queue_timeout: float = 30.0  # Queue timeout in seconds
                                # Max time to wait in queue
                                # Range: 1.0 - 300.0 seconds

    burst_size: int = 10  # Burst allowance
                         # Number of requests allowed in burst
                         # Range: 1 - 100
```

---

## Customization

### Configuration

```python
# Custom gateway configuration
config = GatewayConfig(
    model_list=[...],
    timeout=120.0,
    max_retries=5,
    enable_circuit_breaker=True,
    enable_rate_limiting=True,
    enable_llmops=True,
    enable_validation=True,
    validation_level=ValidationLevel.STRICT
)

gateway = LiteLLMGateway(config=config)
```

### Custom Validators

```python
# Add custom validator
guardrail = gateway.validation_manager.get_guardrail()
guardrail.add_validator(
    lambda output: (
        "incident_id" in output.lower(),
        "Missing incident_id in response"
    )
)
```

---

## Best Practices

1. **Configure Rate Limits**: Set appropriate rate limits per tenant
2. **Enable Circuit Breaker**: Protect against provider failures
3. **Monitor Health**: Regularly check gateway health
4. **Use LLMOps**: Track costs and usage
5. **Enable Validation**: Ensure output quality
6. **Collect Feedback**: Enable feedback loop for improvement

---

## Additional Resources

- **Component README**: `src/core/litellm_gateway/README.md`
- **Function Documentation**: `src/core/litellm_gateway/functions.py`
- **Examples**: `examples/basic_usage/05_litellm_gateway_basic.py`

