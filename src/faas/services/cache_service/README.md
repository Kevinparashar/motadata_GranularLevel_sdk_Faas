# MOTADATA - CACHE SERVICE

**FaaS implementation of the Cache Mechanism providing REST API endpoints for distributed caching operations with tenant-scoped isolation.**

## Overview

Cache Service is a FaaS implementation of the Cache Mechanism component. It provides REST API endpoints for distributed caching operations, including get, set, delete, and invalidation operations with tenant-scoped isolation.

## API Endpoints

### Cache Operations

- `GET /api/v1/cache/{key}` - Get cached value by key
- `POST /api/v1/cache` - Set cached value

**Request Body:**
```json
{
  "key": "user:123",
  "value": {"name": "John", "email": "john@example.com"},
  "ttl": 3600
}
```

- `DELETE /api/v1/cache/{key}` - Delete cached value by key

### Cache Invalidation

- `POST /api/v1/cache/invalidate` - Invalidate cache by pattern

**Request Body:**
```json
{
  "pattern": "user:*"
}
```

- `DELETE /api/v1/cache/tenant/{tenant_id}` - Clear all cache for a tenant

## Service Dependencies

- **Dragonfly**: For distributed caching backend (optional, falls back to in-memory)

## Stateless Architecture

The Cache Service is **stateless**:
- Cache instances are created on-demand per request
- Cache backend (Dragonfly/memory) handles state persistence
- All cache operations are tenant-scoped

## Usage

```python
from src.faas.services.cache_service import create_cache_service

# Create service
service = create_cache_service(
    service_name="cache-service",
    config_overrides={
        "dragonfly_url": "dragonfly://localhost:6379/0",
    }
)

# Run service
# uvicorn service.app:app --host 0.0.0.0 --port 8080
```

## Integration with Other Services

### Called by Other Services

Cache Service is called by:
- **Agent Service**: For caching agent responses
- **RAG Service**: For caching query results and embeddings
- **Gateway Service**: For caching LLM responses
- **All Services**: For general caching needs

### Using Service Client

```python
from src.faas.shared import ServiceClientManager

client_manager = ServiceClientManager(config)
cache_client = client_manager.get_client("cache")

# Set cache
await cache_client.post(
    "/api/v1/cache",
    json_data={"key": "result:123", "value": {"data": "..."}, "ttl": 600},
    headers=cache_client.get_headers(tenant_id=tenant_id)
)

# Get cache
response = await cache_client.get(
    "/api/v1/cache/result:123",
    headers=cache_client.get_headers(tenant_id=tenant_id)
)
```

## Configuration

```bash
SERVICE_NAME=cache-service
SERVICE_PORT=8080
DRAGONFLY_URL=dragonfly://localhost:6379/0
# If DRAGONFLY_URL is not set, uses in-memory cache
ENABLE_NATS=true
ENABLE_OTEL=true
```

## Example Request

```bash
# Set cache
curl -X POST http://localhost:8080/api/v1/cache \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant_123" \
  -d '{
    "key": "user:123",
    "value": {"name": "John"},
    "ttl": 3600
  }'

# Get cache
curl -X GET http://localhost:8080/api/v1/cache/user:123 \
  -H "X-Tenant-ID: tenant_123"

# Invalidate pattern
curl -X POST http://localhost:8080/api/v1/cache/invalidate \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant_123" \
  -d '{
    "pattern": "user:*"
  }'
```

## Features

- **Multi-Backend Support**: Dragonfly or in-memory caching
- **Tenant Isolation**: All cache keys are tenant-scoped
- **TTL Support**: Time-to-live for cached values
- **Pattern Invalidation**: Invalidate multiple keys by pattern
- **Automatic Sharding**: For large-scale deployments
- **Memory Monitoring**: Track cache memory usage

