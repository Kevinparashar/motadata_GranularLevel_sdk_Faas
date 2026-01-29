# Motadata FaaS Structure Summary

## Overview

This document summarizes the FaaS implementation structure, focusing on AI components as services with proper integration patterns.

## Folder Structure

```
src/faas/
├── __init__.py                       # Package initialization
├── README.md                         # Main FaaS documentation
│
├── services/                         # AI Component Services
│   ├── __init__.py
│   └── agent_service/                # ✅ Complete example
│       ├── __init__.py
│       ├── service.py                # Main service implementation
│       ├── models.py                 # Request/Response models
│       └── README.md                 # Service documentation
│
├── integrations/                     # Integration Layer
│   ├── __init__.py
│   ├── nats.py                       # ✅ NATS placeholder
│   ├── otel.py                       # ✅ OTEL placeholder
│   ├── codec.py                      # ✅ CODEC placeholder (JSON working)
│   └── README.md                     # Integration documentation
│
└── shared/                           # Shared Components
    ├── __init__.py
    ├── contracts.py                  # ✅ Standard request/response schemas
    ├── middleware.py                 # ✅ Common middleware (auth, logging, errors)
    ├── database.py                   # ✅ Database connection utilities
    ├── config.py                     # ✅ Configuration management
    └── exceptions.py                 # ✅ Common exceptions
```

## Implementation Status

### ✅ Completed

1. **Folder Structure**
   - Proper organization of services, integrations, and shared components
   - Each service has its own folder with service.py, models.py, README.md

2. **Shared Components**
   - Standard contracts (ServiceRequest, ServiceResponse, ErrorResponse)
   - Middleware (auth, logging, error handling)
   - Database utilities
   - Configuration management
   - Common exceptions

3. **Integration Layer**
   - NATS client placeholder (ready for actual implementation)
   - OTEL tracer placeholder (ready for actual implementation)
   - CODEC manager (JSON working, MessagePack/Protobuf placeholders)

4. **Agent Service (Example)**
   - Complete service implementation
   - REST API endpoints
   - Integration with Gateway Service
   - NATS event publishing
   - OTEL tracing
   - Proper error handling

5. **Documentation**
   - Main FaaS README
   - Service-specific READMEs
   - Integration documentation
   - Implementation guide

### ⏳ Pending (Placeholders Ready)

1. **Remaining Services**
   - RAG Service
   - Gateway Service
   - ML Service
   - Cache Service
   - Prompt Service
   - Data Ingestion Service

2. **Integration Implementations**
   - Actual NATS client (nats-py library)
   - Actual OTEL SDK integration
   - MessagePack codec
   - Protobuf codec

## Service Pattern

Each service follows this pattern:

```python
# service.py
class ComponentService:
    def __init__(self, config, db, nats_client, otel_tracer, codec_manager):
        self.config = config
        self.db = db
        self.nats_client = nats_client
        self.otel_tracer = otel_tracer
        self.codec_manager = codec_manager
        
        self.app = FastAPI(title="Component Service")
        setup_middleware(self.app)
        self._register_routes()
    
    def _register_routes(self):
        # Register REST API endpoints
        pass
```

## Integration Patterns

### 1. Service-to-Service HTTP

```python
# Direct HTTP call
async with httpx.AsyncClient() as client:
    response = await client.post(
        f"{service_url}/api/v1/endpoint",
        json=data,
        headers={"X-Tenant-ID": tenant_id}
    )
```

### 2. NATS Messaging

```python
# Publish event
await nats_client.publish(
    subject=f"service.event.{tenant_id}",
    payload=codec_manager.encode(data)
)

# Subscribe to events
await nats_client.subscribe(
    subject=f"service.event.{tenant_id}",
    callback=handle_message
)
```

### 3. OTEL Tracing

```python
# Create span
with otel_tracer.start_span("operation") as span:
    span.set_attribute("key", "value")
    # Execute operation
```

## Service Dependencies

```
Agent Service
    ├─> Gateway Service (LLM calls)
    ├─> Cache Service (caching)
    └─> RAG Service (document retrieval)

RAG Service
    ├─> Gateway Service (embeddings, generation)
    ├─> Cache Service (query caching)
    └─> Database (document storage)

Gateway Service
    └─> Cache Service (response caching)

All Services
    ├─> Database (state persistence)
    ├─> Redis (caching)
    ├─> NATS (messaging, if enabled)
    └─> OTEL (observability, if enabled)
```

## Standard Headers

All requests include:
- `X-Tenant-ID`: Tenant ID (from JWT)
- `X-User-ID`: User ID (from JWT)
- `X-Correlation-ID`: Request correlation ID
- `X-Request-ID`: Unique request ID

## Configuration

Each service configured via environment variables:
- Service identity (name, version, port)
- Dependency URLs (gateway, cache, rag, etc.)
- Database and Redis URLs
- Integration flags (NATS, OTEL, CODEC)

## Next Steps

1. **Implement Remaining Services**:
   - Follow Agent Service pattern
   - Use shared components
   - Integrate with other services

2. **Complete Integrations**:
   - Replace NATS placeholder with actual client
   - Replace OTEL placeholder with actual SDK
   - Implement MessagePack and Protobuf codecs

3. **Testing**:
   - Unit tests for each service
   - Integration tests for service interactions
   - End-to-end workflow tests

4. **Documentation**:
   - API documentation for each service
   - Deployment guides
   - Troubleshooting guides

## Code Quality

All code follows professional standards:
- Type hints throughout
- Comprehensive error handling
- Structured logging
- Proper exception hierarchy
- Consistent naming conventions
- Documentation strings
- Pydantic models for validation

