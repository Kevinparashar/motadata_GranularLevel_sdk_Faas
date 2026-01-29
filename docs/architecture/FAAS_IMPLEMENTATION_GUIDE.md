# Motadata FaaS Implementation Guide - AI Components as Services

## Overview

This guide documents the FaaS implementation of the Motadata AI SDK, where each AI component is transformed into an independent, scalable service that can be deployed in serverless or containerized environments.

## Architecture Principles

### 1. Component as Service
Each AI component (Agent, RAG, Gateway, ML, Cache, Prompt, Data Ingestion, Prompt Generator, LLMOps) is implemented as an independent service with:
- REST API endpoints
- Independent deployment
- Independent scaling
- Service-to-service communication

### 2. Service Integration
Services communicate via:
- **Direct HTTP calls**: Synchronous service-to-service calls
- **NATS messaging**: Asynchronous event-driven communication
- **Shared state**: PostgreSQL for persistent state, Dragonfly for caching

### 3. Observability
All services integrate with:
- **OTEL**: Distributed tracing, metrics, logging
- **Structured logging**: Consistent log format across services
- **Health checks**: Service health monitoring

### 4. Message Serialization
All inter-service messages use:
- **CODEC**: Standardized serialization (JSON, MessagePack, Protobuf)
- **Consistent format**: Same encoding/decoding across services

## Folder Structure

```
src/faas/
├── __init__.py
├── README.md                          # Main FaaS documentation
├── services/                          # AI Component Services
│   ├── __init__.py
│   ├── agent_service/                # Agent Framework Service
│   │   ├── __init__.py
│   │   ├── service.py                # Main service implementation
│   │   ├── models.py                 # Request/Response models
│   │   └── README.md                 # Service documentation
│   ├── rag_service/                  # RAG System Service
│   │   ├── __init__.py
│   │   ├── service.py
│   │   ├── models.py
│   │   └── README.md
│   ├── gateway_service/              # LiteLLM Gateway Service
│   │   ├── __init__.py
│   │   ├── service.py
│   │   ├── models.py
│   │   └── README.md
│   ├── ml_service/                   # ML Framework Service
│   │   ├── __init__.py
│   │   ├── service.py
│   │   ├── models.py
│   │   └── README.md
│   ├── cache_service/                # Cache Mechanism Service
│   │   ├── __init__.py
│   │   ├── service.py
│   │   ├── models.py
│   │   └── README.md
│   ├── prompt_service/               # Prompt Context Management Service
│   │   ├── __init__.py
│   │   ├── service.py
│   │   ├── models.py
│   │   └── README.md
│   ├── data_ingestion_service/       # Data Ingestion Service
│   │   ├── __init__.py
│   │   ├── service.py
│   │   ├── models.py
│   │   └── README.md
│   ├── prompt_generator_service/     # Prompt-Based Generator Service
│   │   ├── __init__.py
│   │   ├── service.py
│   │   ├── models.py
│   │   └── README.md
│   └── llmops_service/               # LLMOps Service
│       ├── __init__.py
│       ├── service.py
│       ├── models.py
│       └── README.md
├── integrations/                      # Integration Layer
│   ├── __init__.py
│   ├── nats.py                       # NATS Message Bus
│   ├── otel.py                       # OpenTelemetry
│   ├── codec.py                      # Message Serialization
│   └── README.md                     # Integration documentation
└── shared/                           # Shared Components
    ├── __init__.py
    ├── contracts.py                  # Standard request/response schemas
    ├── middleware.py                 # Common middleware
    ├── database.py                   # Database utilities
    ├── config.py                     # Configuration management
    └── exceptions.py                 # Common exceptions
```

## Service Structure Pattern

Each service follows this structure:

```python
# service.py
from fastapi import FastAPI
from ...shared.config import ServiceConfig
from ...shared.middleware import setup_middleware
from ...integrations import create_nats_client, create_otel_tracer, create_codec_manager

class ComponentService:
    def __init__(self, config: ServiceConfig, ...):
        self.config = config
        self.nats_client = create_nats_client() if config.enable_nats else None
        self.otel_tracer = create_otel_tracer(config.service_name) if config.enable_otel else None
        self.codec_manager = create_codec_manager()
        
        self.app = FastAPI(title="Component Service")
        setup_middleware(self.app)
        self._register_routes()
    
    def _register_routes(self):
        # Register API endpoints
        pass
```

## Service Integration Patterns

### Pattern 1: Direct HTTP Call

```python
# Agent Service calling Gateway Service
async with httpx.AsyncClient() as client:
    response = await client.post(
        f"{gateway_service_url}/api/v1/gateway/generate",
        json={"prompt": prompt, "model": "gpt-4"},
        headers={
            "X-Tenant-ID": tenant_id,
            "X-Correlation-ID": correlation_id,
        }
    )
    result = response.json()
```

### Pattern 2: NATS Message Bus

```python
# Agent Service publishing event
event = {
    "event_type": "agent.task.completed",
    "agent_id": agent_id,
    "task_id": task_id,
    "result": result,
}

await nats_client.publish(
    subject=f"agent.events.{tenant_id}",
    payload=codec_manager.encode(event)
)

# RAG Service subscribing to events
async def handle_agent_event(msg):
    event = codec_manager.decode(msg.data)
    if event["event_type"] == "agent.task.completed":
        # Process event
        pass

await nats_client.subscribe(
    subject=f"agent.events.{tenant_id}",
    callback=handle_agent_event
)
```

### Pattern 3: Request-Response via NATS

```python
# Agent Service requesting RAG query
request = {
    "query": "What is AI?",
    "top_k": 5,
}

response = await nats_client.request(
    subject=f"rag.query.{tenant_id}",
    payload=codec_manager.encode(request),
    timeout=10.0
)

result = codec_manager.decode(response)
```

## Service Dependencies

### Dependency Graph

```
Agent Service
    ├─> Gateway Service (LLM calls)
    ├─> Cache Service (response caching)
    └─> RAG Service (document retrieval)

RAG Service
    ├─> Gateway Service (embeddings, generation)
    ├─> Cache Service (query caching)
    └─> Database (document storage)

Gateway Service
    └─> Cache Service (response caching)

ML Service
    ├─> Database (model storage)
    └─> Cache Service (prediction caching)

Data Ingestion Service
    └─> RAG Service (document processing)

Prompt Service
    └─> Database (template storage)

Cache Service
    └─> Dragonfly (cache backend)
```

## Integration Order

### Service Startup Order

1. **Infrastructure Services** (start first):
   - Database (PostgreSQL)
   - Dragonfly (Cache)
   - NATS (if enabled)
   - OTEL Collector (if enabled)

2. **Core Services** (start second):
   - Gateway Service (used by all services)
   - Cache Service (used by all services)

3. **AI Services** (start third):
   - RAG Service
   - Prompt Service
   - ML Service

4. **Orchestration Services** (start last):
   - Agent Service (depends on Gateway, RAG, Cache)
   - Data Ingestion Service (depends on RAG)

### Service Communication Flow

```
Client Request
    │
    ▼
AWS API Gateway
    │
    ▼
Agent Service
    │
    ├─> Gateway Service (LLM call)
    │   └─> Cache Service (check cache)
    │
    ├─> RAG Service (document retrieval)
    │   ├─> Gateway Service (embeddings)
    │   └─> Cache Service (query cache)
    │
    └─> Cache Service (cache result)
    │
    ▼
Client Response
```

## NATS Integration (Placeholder)

### Purpose
- Async service-to-service communication
- Event streaming
- Pub/Sub messaging

### Current Status
- ✅ Placeholder implementation complete
- ⏳ Actual NATS client integration pending

### Usage Pattern

```python
# Initialize
nats_client = create_nats_client()

# Connect
await nats_client.connect()

# Publish
await nats_client.publish(
    subject="service.event",
    payload=codec_manager.encode(data)
)

# Subscribe
await nats_client.subscribe(
    subject="service.event",
    callback=handle_message
)
```

## OTEL Integration (Placeholder)

### Purpose
- Distributed tracing
- Metrics collection
- Log correlation

### Current Status
- ✅ Placeholder implementation complete
- ⏳ Actual OTEL SDK integration pending

### Usage Pattern

```python
# Initialize
tracer = create_otel_tracer(service_name="agent-service")

# Create span
with tracer.start_span("operation_name") as span:
    span.set_attribute("key", "value")
    # Execute operation
    span.add_event("event.name")
```

## CODEC Integration (Placeholder)

### Purpose
- Message serialization
- Efficient data encoding
- Multiple format support

### Current Status
- ✅ JSON encoding/decoding implemented
- ⏳ MessagePack encoding pending
- ⏳ Protobuf encoding pending

### Usage Pattern

```python
# Initialize
codec_manager = create_codec_manager(codec_type="json")

# Encode
data = {"key": "value"}
encoded = codec_manager.encode(data)  # bytes

# Decode
decoded = codec_manager.decode(encoded)  # dict
```

## Standard Headers

All service requests include standard headers:

```
X-Tenant-ID: tenant_123          # Tenant ID (from JWT)
X-User-ID: user_456              # User ID (from JWT)
X-Correlation-ID: corr_789      # Request correlation ID
X-Request-ID: req_abc123         # Unique request ID
```

## Error Handling

All services use consistent error responses:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message",
    "details": {}
  },
  "correlation_id": "corr_789",
  "request_id": "req_abc123",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Configuration

Each service is configured via environment variables:

```bash
# Service Identity
SERVICE_NAME=agent-service
SERVICE_VERSION=1.0.0
SERVICE_PORT=8080

# Dependencies
GATEWAY_SERVICE_URL=http://gateway-service:8080
CACHE_SERVICE_URL=http://cache-service:8080
RAG_SERVICE_URL=http://rag-service:8080

# Database
DATABASE_URL=postgresql://user:pass@localhost/db
DRAGONFLY_URL=dragonfly://localhost:6379

# Integrations
ENABLE_NATS=true
NATS_URL=nats://localhost:4222

ENABLE_OTEL=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

ENABLE_CODEC=true
CODEC_TYPE=json
```

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY .env .

CMD ["uvicorn", "src.faas.services.agent_service.service:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-service
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: agent-service
        image: motadata/agent-service:latest
        env:
        - name: GATEWAY_SERVICE_URL
          value: "http://gateway-service:8080"
        - name: CACHE_SERVICE_URL
          value: "http://cache-service:8080"
        ports:
        - containerPort: 8080
```

## Testing

### Unit Tests

```bash
pytest src/tests/unit_tests/test_faas/services/agent_service/
```

### Integration Tests

```bash
pytest src/tests/integration_tests/test_faas/
```

## Next Steps

1. **Complete Service Implementations**:
   - RAG Service
   - Gateway Service
   - ML Service
   - Cache Service
   - Prompt Service
   - Data Ingestion Service

2. **Complete Integrations**:
   - NATS client implementation
   - OTEL SDK integration
   - MessagePack codec
   - Protobuf codec

3. **Testing**:
   - Unit tests for all services
   - Integration tests for service interactions
   - End-to-end workflow tests

4. **Documentation**:
   - API documentation for each service
   - Deployment guides
   - Troubleshooting guides

