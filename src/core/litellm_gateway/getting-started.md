# Getting Started with LiteLLM Gateway

## Overview

The LiteLLM Gateway provides a unified interface for interacting with multiple LLM providers (OpenAI, Anthropic, Google, etc.). This guide explains the complete workflow from gateway creation to receiving responses.

## Entry Point

The primary entry point for creating gateways is through factory functions:

```python
from src.core.litellm_gateway import create_gateway, generate_text, generate_text_async
```

## Input Requirements

### Required Inputs

1. **API Key**: Provider API key
   ```python
   api_key = os.getenv("OPENAI_API_KEY")  # or ANTHROPIC_API_KEY, etc.
   ```

2. **Provider**: LLM provider name
   - `"openai"` - OpenAI models
   - `"anthropic"` - Anthropic Claude models
   - `"google"` - Google Gemini models
   - `"cohere"` - Cohere models

### Optional Inputs

- `default_model`: Default model to use (e.g., "gpt-4", "claude-3-opus")
- `timeout`: Request timeout in seconds
- `max_retries`: Maximum retry attempts
- `rate_limit_config`: Rate limiting configuration
- `enable_caching`: Enable response caching

## Process Flow

### Step 1: Gateway Creation

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

### Step 2: Request Preparation

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

### Step 3: Request Execution

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

### Step 4: Response Processing

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

## Output

### Generate Response Structure

```python
class GenerateResponse:
    text: str                    # Generated text
    model: str                   # Model used
    usage: TokenUsage            # Token usage
    finish_reason: str          # Completion reason
    metadata: Dict[str, Any]    # Additional metadata
```

### Output Fields

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

## Where Output is Used

### 1. Direct Usage

```python
response = gateway.generate(prompt="What is AI?")
print(response.text)
print(f"Tokens used: {response.usage.total_tokens}")
```

### 2. Integration with Agent Framework

```python
# Agent uses gateway output
agent = create_agent(agent_id="agent_001", gateway=gateway, ...)
# When agent executes task, it uses gateway.generate() internally
result = await agent.execute_task(task)
# result contains gateway response
```

### 3. Integration with RAG System

```python
# RAG uses gateway for embeddings and generation
rag = create_rag_system(db=db, gateway=gateway, ...)

# Gateway generates embeddings
embeddings = await gateway.embed_async(texts=["document text"])

# Gateway generates final response
result = rag.query("What is AI?")
# result['answer'] contains gateway-generated text
```

### 4. Integration with API Backend

```python
# API exposes gateway functionality
@app.post("/api/generate")
async def generate_api(request: GenerateRequest):
    response = gateway.generate(
        prompt=request.prompt,
        model=request.model
    )
    return {
        "text": response.text,
        "tokens": response.usage.total_tokens
    }
```

### 5. Streaming Responses

```python
# For real-time streaming
async for chunk in gateway.generate_stream_async(
    prompt="Tell me a story",
    model="gpt-4"
):
    print(chunk, end="", flush=True)
    # Output is streamed token by token
```

## Complete Example

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

## Important Information

### Rate Limiting

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

### Circuit Breaker

```python
# Circuit breaker automatically opens on repeated failures
# Prevents cascading failures
# Automatically attempts recovery after timeout

# Check circuit breaker status
status = gateway.get_health()
if status['circuit_breaker']['state'] == 'open':
    print("Circuit breaker is open - provider unavailable")
```

### Request Batching

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

### Request Deduplication

```python
# Enable deduplication to avoid processing identical requests
config = GatewayConfig(
    enable_request_deduplication=True,
    deduplication_ttl=300  # 5 minutes
)

gateway = LiteLLMGateway(config=config)
# Identical requests within deduplication window return cached result
```

### Response Caching

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

### Error Handling

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

### Health Monitoring

```python
# Check gateway health
health = gateway.get_health()
print(f"Status: {health['status']}")
print(f"Provider: {health['provider']}")
print(f"Circuit Breaker: {health['circuit_breaker']['state']}")
print(f"Rate Limit: {health['rate_limit']['remaining']} requests remaining")
```

### LLMOps Integration

```python
# Gateway automatically logs operations
# Track token usage, costs, and performance
# Access logs through LLMOps component

from src.core.llmops import LLMOps

llmops = LLMOps(storage_path="./llmops_data")
# Gateway automatically uses LLMOps if configured
```

## Next Steps

- See [README.md](README.md) for detailed component documentation
- Check [component_explanation/litellm_gateway_explanation.md](../../../component_explanation/litellm_gateway_explanation.md) for comprehensive guide
- Review [troubleshooting guide](../../../docs/troubleshooting/litellm_gateway_troubleshooting.md) for common issues
- Explore [examples/basic_usage/05_litellm_gateway_basic.py](../../../examples/basic_usage/05_litellm_gateway_basic.py) for more examples

