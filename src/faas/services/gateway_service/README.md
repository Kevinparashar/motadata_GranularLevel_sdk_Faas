# MOTADATA - GATEWAY SERVICE

**FaaS implementation of the LiteLLM Gateway providing REST API endpoints for unified LLM access with rate limiting and caching.**

## Overview

Gateway Service is a FaaS implementation of the LiteLLM Gateway component. It provides REST API endpoints for unified LLM access across multiple providers (OpenAI, Anthropic, Google, etc.) with rate limiting, caching, and provider management.

## API Endpoints

### Text Generation

- `POST /api/v1/gateway/generate` - Generate text using LLM

**Request Body:**
```json
{
  "prompt": "Explain quantum computing",
  "model": "gpt-4",
  "max_tokens": 1000,
  "temperature": 0.7,
  "stream": false
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "text": "Quantum computing is...",
    "model": "gpt-4",
    "usage": {
      "prompt_tokens": 10,
      "completion_tokens": 100,
      "total_tokens": 110
    },
    "finish_reason": "stop"
  }
}
```

- `POST /api/v1/gateway/generate/stream` - Stream text generation

### Embeddings

- `POST /api/v1/gateway/embeddings` - Generate embeddings for text

**Request Body:**
```json
{
  "texts": ["Hello world", "AI is amazing"],
  "model": "text-embedding-3-small"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "embeddings": [[0.1, 0.2, ...], [0.3, 0.4, ...]],
    "model": "text-embedding-3-small",
    "usage": {
      "total_tokens": 5
    }
  }
}
```

### Provider Management

- `GET /api/v1/gateway/providers` - List available providers
- `GET /api/v1/gateway/rate-limits` - Get rate limit information

## Service Dependencies

- **Cache Service**: For response caching (optional)
- **Database**: For rate limiting and quota tracking (optional)

## Stateless Architecture

The Gateway Service is **stateless**:
- Gateway instances are created on-demand per request
- No in-memory caching of gateway instances
- Rate limiting and quotas stored in database

## Usage

```python
from src.faas.services.gateway_service import create_gateway_service

# Create service
service = create_gateway_service(
    service_name="gateway-service",
    config_overrides={
        "cache_service_url": "http://cache-service:8080",
    }
)

# Run service
# uvicorn service.app:app --host 0.0.0.0 --port 8080
```

## Integration with Other Services

### Called by Other Services

Gateway Service is called by:
- **Agent Service**: For LLM text generation
- **RAG Service**: For embeddings and generation
- **Prompt Generator Service**: For LLM calls
- **LLMOps Service**: For operation logging

### Using NATS for Events

```python
# Publish generation event
event = {
    "event_type": "gateway.generation.completed",
    "model": "gpt-4",
    "tokens": 110,
    "tenant_id": tenant_id,
}
await nats_client.publish(
    f"gateway.events.{tenant_id}",
    codec_manager.encode(event)
)
```

## Configuration

```bash
SERVICE_NAME=gateway-service
SERVICE_PORT=8080
CACHE_SERVICE_URL=http://cache-service:8080
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...
GOOGLE_API_KEY=...
DATABASE_URL=postgresql://user:pass@localhost/db
ENABLE_NATS=true
ENABLE_OTEL=true
```

## Example Request

```bash
# Generate text
curl -X POST http://localhost:8080/api/v1/gateway/generate \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant_123" \
  -d '{
    "prompt": "What is AI?",
    "model": "gpt-4",
    "max_tokens": 500
  }'

# Generate embeddings
curl -X POST http://localhost:8080/api/v1/gateway/embeddings \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant_123" \
  -d '{
    "texts": ["Hello world"],
    "model": "text-embedding-3-small"
  }'
```

## Features

- **Multi-Provider Support**: OpenAI, Anthropic, Google, and more
- **Rate Limiting**: Automatic rate limiting per tenant/provider
- **Request Queuing**: Queue requests when rate limits are hit
- **Request Deduplication**: Avoid processing identical requests
- **Circuit Breaker**: Automatic failover for provider failures
- **Health Monitoring**: Provider health checks
- **LLMOps Integration**: Comprehensive logging and metrics

