# MOTADATA - LLMOPS SERVICE

**FaaS implementation of the LLMOps component providing REST API endpoints for logging, metrics, analytics, and cost tracking.**

## Overview

LLMOps Service is a FaaS implementation of the LLMOps component. It provides REST API endpoints for logging LLM operations, querying operation history, retrieving metrics and analytics, and performing cost analysis.

## API Endpoints

### Operation Logging

- `POST /api/v1/llmops/operations` - Log an LLM operation

**Request Body:**
```json
{
  "operation_type": "completion",
  "model": "gpt-4",
  "prompt_tokens": 100,
  "completion_tokens": 50,
  "total_tokens": 150,
  "latency_ms": 1250.5,
  "cost_usd": 0.003,
  "status": "success",
  "agent_id": "agent_123",
  "metadata": {}
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "operation_id": "op_abc123"
  }
}
```

### Query Operations

- `GET /api/v1/llmops/operations` - Query LLM operations with filters

**Query Parameters:**
- `tenant_id` (optional): Filter by tenant ID
- `agent_id` (optional): Filter by agent ID
- `model` (optional): Filter by model
- `operation_type` (optional): Filter by operation type (completion, embedding, chat, etc.)
- `status` (optional): Filter by status (success, error, timeout, etc.)
- `start_date` (optional): Start date for filtering
- `end_date` (optional): End date for filtering
- `limit` (default: 100): Maximum number of results
- `offset` (default: 0): Offset for pagination

**Response:**
```json
{
  "success": true,
  "data": {
    "operations": [
      {
        "operation_id": "op_abc123",
        "operation_type": "completion",
        "model": "gpt-4",
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "total_tokens": 150,
        "latency_ms": 1250.5,
        "cost_usd": 0.003,
        "status": "success",
        "timestamp": "2024-01-01T00:00:00Z"
      }
    ],
    "count": 1
  }
}
```

### Metrics

- `GET /api/v1/llmops/metrics` - Get LLM operations metrics

**Query Parameters:**
- `tenant_id` (optional): Filter by tenant ID
- `start_date` (optional): Start date for metrics
- `end_date` (optional): End date for metrics

**Response:**
```json
{
  "success": true,
  "data": {
    "total_operations": 1000,
    "total_tokens": 150000,
    "total_cost_usd": 4.50,
    "average_latency_ms": 1250.5,
    "success_rate": 0.98,
    "operations_by_type": {
      "completion": 800,
      "embedding": 200
    },
    "operations_by_model": {
      "gpt-4": 600,
      "gpt-3.5-turbo": 400
    },
    "cost_by_model": {
      "gpt-4": 3.00,
      "gpt-3.5-turbo": 1.50
    },
    "tokens_by_model": {
      "gpt-4": 90000,
      "gpt-3.5-turbo": 60000
    }
  }
}
```

### Cost Analysis

- `GET /api/v1/llmops/cost-analysis` - Get cost analysis

**Query Parameters:**
- `tenant_id` (optional): Filter by tenant ID
- `start_date` (optional): Start date for analysis
- `end_date` (optional): End date for analysis

**Response:**
```json
{
  "success": true,
  "data": {
    "total_cost_usd": 4.50,
    "cost_by_model": {
      "gpt-4": 3.00,
      "gpt-3.5-turbo": 1.50
    },
    "cost_by_operation_type": {
      "completion": 3.50,
      "embedding": 1.00
    },
    "cost_by_tenant": {
      "tenant_123": 4.50
    },
    "cost_trend": [],
    "period_start": "2024-01-01T00:00:00Z",
    "period_end": "2024-01-02T00:00:00Z"
  }
}
```

## Service Dependencies

- **Database**: For storing operation logs and metrics

## Usage

```python
from src.faas.services.llmops_service import create_llmops_service

# Create service
app = create_llmops_service(
    service_name="llmops-service",
    config_overrides={
        "database_url": "postgresql://user:pass@localhost/db",
    }
)

# Run with uvicorn
# uvicorn src.faas.services.llmops_service.service:app --host 0.0.0.0 --port 8088
```

## Example: Log Operation

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8088/api/v1/llmops/operations",
        json={
            "operation_type": "completion",
            "model": "gpt-4",
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
            "latency_ms": 1250.5,
            "cost_usd": 0.003,
            "status": "success"
        },
        headers={"X-Tenant-ID": "tenant_123"}
    )
    result = response.json()
    print(f"Logged operation: {result['data']['operation_id']}")
```

## Service Configuration

Configure via environment variables or config file:

```bash
# Service
SERVICE_NAME=llmops-service
SERVICE_PORT=8088

# Dependencies
DATABASE_URL=postgresql://user:pass@localhost/db

# Integrations
ENABLE_NATS=false
ENABLE_OTEL=false
```

## Health Check

- `GET /health` - Service health check

## Error Handling

The service returns standard error responses:

- `400 Bad Request`: Invalid request format
- `500 Internal Server Error`: Server-side errors

All errors include correlation_id and request_id for tracing.

