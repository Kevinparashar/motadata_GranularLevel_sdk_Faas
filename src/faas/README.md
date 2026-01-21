# Motadata AI SDK - Function as a Service (FaaS) Architecture

## Overview

This package provides the FaaS implementation of the Motadata AI SDK, transforming each AI component into an independent, scalable service that can be deployed in serverless or containerized environments.

## Architecture

The FaaS architecture organizes AI components as independent services:

```
┌─────────────────────────────────────────────────────────────┐
│                    External Clients                          │
│  (Web Apps, Mobile Apps, Third-party Integrations)        │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTPS
                            │
┌─────────────────────────────────────────────────────────────┐
│              AWS API Gateway (Edge Layer)                    │
│  - JWT Authentication  - Rate Limiting  - Request Routing  │
│  - Context Injection (tenant_id, user_id from JWT)          │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP (GET, POST, PUT, DELETE)
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Agent Service│   │ RAG Service │   │ ML Service   │
│              │   │             │   │              │
│ - Create    │   │ - Ingest    │   │ - Train     │
│ - Execute   │   │ - Query     │   │ - Predict   │
│ - Chat      │   │ - Search    │   │ - Serve     │
│ - Manage    │   │ - Update    │   │ - Monitor   │
└──────┬───────┘   └──────┬──────┘   └──────┬──────┘
       │                  │                  │
       └──────────┬───────┴──────────┬───────┘
                  │                  │
                  ▼                  ▼
         ┌─────────────────┐  ┌──────────────┐
         │ Gateway Service │  │Cache Service │
         │                 │  │              │
         │ - Generate     │  │ - Get        │
         │ - Embed        │  │ - Set        │
         │ - Stream       │  │ - Invalidate │
         └─────────────────┘  └──────────────┘
                  │
                  │
         ┌────────┴────────┐
         │                 │
         ▼                 ▼
┌─────────────────┐  ┌──────────────┐
│ Prompt Service  │  │Data Ingestion│
│                 │  │   Service    │
│ - Templates     │  │              │
│ - Context       │  │ - Upload     │
│ - Versioning    │  │ - Process    │
└─────────────────┘  └──────────────┘
                  │
                  │
         ┌────────┴────────┐
         │                 │
         ▼                 ▼
┌──────────────────────────────────────┐
│      Integration Layer               │
│  - NATS (Message Bus)                │
│  - OTEL (Observability)              │
│  - CODEC (Serialization)             │
└──────────────────────────────────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  State Storage  │
         │  - PostgreSQL   │
         │  - Redis        │
         └─────────────────┘
```

## Folder Structure

```
src/faas/
├── __init__.py
├── README.md
├── services/                    # AI Component Services
│   ├── agent_service/          # Agent Framework Service
│   ├── rag_service/            # RAG System Service
│   ├── gateway_service/        # LiteLLM Gateway Service
│   ├── ml_service/             # ML Framework Service
│   ├── cache_service/          # Cache Mechanism Service
│   ├── prompt_service/         # Prompt Context Management Service
│   ├── data_ingestion_service/ # Data Ingestion Service
│   ├── prompt_generator_service/ # Prompt-Based Generator Service
│   └── llmops_service/        # LLMOps Service
├── integrations/                # Integration Layer
│   ├── nats/                   # NATS Message Bus Integration
│   ├── otel/                   # OpenTelemetry Integration
│   └── codec/                  # CODEC Serialization Integration
└── shared/                      # Shared Components
    ├── contracts.py            # Standard request/response schemas
    ├── middleware.py           # Common middleware (auth, logging, etc.)
    ├── database.py             # Database connection utilities
    ├── config.py               # Configuration management
    ├── exceptions.py           # Common exceptions
    ├── http_client.py          # HTTP client with retry and circuit breaker
    └── agent_storage.py        # Database-backed agent storage
```

## AI Component Services

### 1. Agent Service
- **Purpose**: Autonomous AI agent management and execution
- **Endpoints**: Agent CRUD, task execution, chat, memory management, tool management
- **Dependencies**: Gateway Service (for LLM calls), Cache Service (for caching)

### 2. RAG Service
- **Purpose**: Retrieval-Augmented Generation for document-based Q&A
- **Endpoints**: Document ingestion, query, search, document management
- **Dependencies**: Gateway Service (for embeddings and generation), Cache Service

### 3. Gateway Service
- **Purpose**: Unified LLM access via LiteLLM
- **Endpoints**: Text generation, embeddings, streaming, provider management
- **Dependencies**: Cache Service (for response caching)

### 4. ML Service
- **Purpose**: Machine learning model training and inference
- **Endpoints**: Model training, inference, model management
- **Dependencies**: Database (for model storage)

### 5. Cache Service
- **Purpose**: Distributed caching for performance optimization
- **Endpoints**: Get, set, delete, invalidate operations
- **Dependencies**: Redis

### 6. Prompt Service
- **Purpose**: Prompt template management and context building
- **Endpoints**: Template CRUD, prompt rendering, context management
- **Dependencies**: Database (for template storage)

### 7. Data Ingestion Service
- **Purpose**: File upload and multi-modal data processing
- **Endpoints**: File upload, processing, validation
- **Dependencies**: RAG Service (for document processing)

### 8. Prompt Generator Service
- **Purpose**: Create agents and tools from natural language prompts
- **Endpoints**: Agent creation from prompt, tool creation from prompt, feedback collection, permission management
- **Dependencies**: Gateway Service (for LLM calls)

### 9. LLMOps Service
- **Purpose**: LLM operations monitoring, metrics, and cost tracking
- **Endpoints**: Operation logging, query operations, metrics retrieval, cost analysis
- **Dependencies**: Database (for operation storage)

## Stateless Architecture

All FaaS services are designed to be **stateless** to ensure scalability and reliability:

### Key Principles

1. **No In-Memory State**: Services do not store client state between requests
2. **On-Demand Creation**: Core component instances (RAG, Gateway, Cache, etc.) are created on-demand per request
3. **Database-Backed Storage**: Persistent state (agents, templates, models) is stored in PostgreSQL
4. **Service-to-Service Communication**: Services communicate via HTTP with retry logic and circuit breakers

### HTTP Client Utilities

**File**: `src/faas/shared/http_client.py`

The SDK provides robust HTTP client utilities for service-to-service communication:

- **ServiceHTTPClient**: HTTP client with automatic retry (exponential backoff) and circuit breaker
- **ServiceClientManager**: Centralized management of service clients with lazy initialization
- **Retry Logic**: Configurable retry attempts with exponential backoff (via `tenacity`)
- **Circuit Breaker**: Fault tolerance with automatic circuit opening/closing
- **Standard Headers**: Automatic injection of tenant_id, user_id, correlation_id, request_id

**Usage**:
```python
from src.faas.shared import ServiceClientManager

# Initialize client manager
client_manager = ServiceClientManager(config)

# Get service client
gateway_client = client_manager.get_client("gateway")

# Make service-to-service call with automatic retry
response = await gateway_client.post(
    "/api/v1/gateway/generate",
    json_data={"prompt": "Hello", "model": "gpt-4"},
    headers=gateway_client.get_headers(tenant_id="tenant_123")
)
```

### Agent Storage

**File**: `src/faas/shared/agent_storage.py`

Agent Service uses database-backed storage to ensure statelessness:

- **Database Persistence**: Agents are stored in PostgreSQL with full metadata
- **On-Demand Loading**: Agents are loaded from database on each request
- **Tenant Isolation**: All operations are tenant-scoped
- **Automatic Schema Creation**: Database tables are created automatically

**Database Schema**:
```sql
CREATE TABLE agents (
    agent_id VARCHAR(255) PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    llm_model VARCHAR(255),
    llm_provider VARCHAR(255),
    system_prompt TEXT,
    status VARCHAR(50),
    capabilities JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## Integration Layer

### NATS Integration
- **Purpose**: Service-to-service messaging and event streaming
- **Usage**: Async communication between services, event publishing/subscribing
- **Placeholder**: Ready for NATS client integration

### OTEL Integration
- **Purpose**: Distributed tracing, metrics, and logging
- **Usage**: Observability across all services
- **Placeholder**: Ready for OpenTelemetry SDK integration

### CODEC Integration
- **Purpose**: Message serialization/deserialization
- **Usage**: Efficient data encoding for NATS messages
- **Placeholder**: Ready for CODEC library integration

## Service Integration Flow

### Example: Agent Using RAG

```
1. Client → Agent Service: Execute task
2. Agent Service → Gateway Service: Generate response
3. Agent Service → RAG Service: Retrieve relevant documents
4. RAG Service → Gateway Service: Generate embeddings
5. RAG Service → Gateway Service: Generate response with context
6. Agent Service → Cache Service: Cache result
7. Agent Service → Client: Return result
```

### Example: Document Ingestion

```
1. Client → Data Ingestion Service: Upload document
2. Data Ingestion Service → RAG Service: Ingest document
3. RAG Service → Gateway Service: Generate embeddings
4. RAG Service → Database: Store document and embeddings
5. RAG Service → Cache Service: Invalidate cache
6. Data Ingestion Service → Client: Return status
```

## Usage

### Starting a Service

```python
from src.faas.services.agent_service import create_agent_service

# Create service with dependencies
service = create_agent_service(
    gateway_service_url="http://gateway-service:8080",
    cache_service_url="http://cache-service:8080",
    db_connection=db,
    nats_client=nats_client,
    otel_tracer=tracer
)

# Run service
# uvicorn service.app:app --host 0.0.0.0 --port 8080
```

### Service-to-Service Communication

**Using HTTP Client Utilities (Recommended)**:

```python
from src.faas.shared import ServiceClientManager

# Initialize client manager with service config
client_manager = ServiceClientManager(config)

# Get gateway service client
gateway_client = client_manager.get_client("gateway")

# Make service call with automatic retry and circuit breaker
response = await gateway_client.post(
    "/api/v1/gateway/generate",
    json_data={"prompt": "Hello", "model": "gpt-4"},
    headers=gateway_client.get_headers(
        tenant_id="tenant_123",
        user_id="user_456",
        correlation_id="corr_789"
    )
)
```

**Direct HTTP Call (Alternative)**:

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://gateway-service:8080/api/v1/gateway/generate",
        json={"prompt": "Hello", "model": "gpt-4"},
        headers={"X-Tenant-ID": "tenant_123"}
    )
```

**Via NATS (Async Messaging)**:

```python
await nats_client.publish(
    subject="gateway.generate.request",
    payload=codec.encode({"prompt": "Hello", "model": "gpt-4"})
)
```

## Configuration

Each service can be configured via environment variables:

```bash
# Service Configuration
SERVICE_NAME=agent-service
SERVICE_PORT=8080
LOG_LEVEL=INFO

# Dependencies
GATEWAY_SERVICE_URL=http://gateway-service:8080
CACHE_SERVICE_URL=http://cache-service:8080
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379

# Integrations
NATS_URL=nats://localhost:4222
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
CODEC_TYPE=json  # or msgpack, protobuf
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

CMD ["uvicorn", "src.faas.services.agent_service.app:app", "--host", "0.0.0.0", "--port", "8080"]
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
```

## Testing

### Unit Tests

```bash
pytest src/tests/unit_tests/test_faas/services/
```

### Integration Tests

```bash
pytest src/tests/integration_tests/test_faas/
```

## Related Documentation

- [FaaS Implementation Guide](../../docs/architecture/FAAS_IMPLEMENTATION_GUIDE.md) - Complete FaaS implementation guide
- [FaaS Stateless Implementation](../../docs/architecture/FAAS_STATELESS_IMPLEMENTATION.md) - Stateless architecture details
- [Service Implementation Details](./services/agent_service/README.md) - Individual service documentation
- [Integration Layer Documentation](./integrations/README.md) - NATS, OTEL, CODEC integration
- [Shared Components](./shared/) - Contracts, middleware, HTTP client, agent storage
