# MOTADATA - OPENTELEMETRY (OTEL) INTEGRATION

**Comprehensive OpenTelemetry integration for distributed tracing, metrics collection, and observability across all AI SDK components.**

## When to Use This Component

**✅ Use OTEL Integration when:**
- You need distributed tracing across multiple services
- You want to monitor performance and latency
- You need metrics collection for dashboards
- You're deploying to production environments
- You need to debug complex multi-component workflows
- You want to track tenant-specific metrics and traces
- You need context propagation across async operations

**❌ Don't use OTEL Integration when:**
- You're just prototyping or testing locally
- You don't need observability or monitoring
- You're building simple scripts without distributed components
- Overhead is a critical concern (minimal, but exists)

**Note:** OTEL Integration is automatically used by all SDK components when configured. You just need to set the OTLP endpoint.

**Simple Setup:**
```python
# Set environment variable
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# Components automatically use OTEL when endpoint is configured
```

**Performance Impact:** Minimal overhead (~1-5% latency increase) with significant debugging and monitoring benefits.

---

## Overview

The OpenTelemetry (OTEL) Integration module provides comprehensive observability capabilities for the Motadata AI SDK. It implements distributed tracing, metrics collection, context propagation, and auto-instrumentation for all SDK components.

This module is the **implementation layer** for observability. The high-level observability component (`src/core/evaluation_observability/`) uses this module to provide observability features across the SDK.

## Purpose and Functionality

The OTEL Integration module provides:

- **Distributed Tracing**: Track requests as they flow through multiple components
- **Metrics Collection**: Collect and export performance metrics
- **Context Propagation**: Propagate trace context across component boundaries
- **Auto-Instrumentation**: Automatic instrumentation for FastAPI, HTTP clients, databases, and Redis
- **Tenant Context**: Multi-tenant support with tenant-specific attributes
- **Baggage Propagation**: Pass custom context data through traces

## Connection to Other Components

### Integration with Evaluation & Observability

The **Evaluation & Observability** component (`src/core/evaluation_observability/`) is the high-level interface for observability. It uses this OTEL Integration module as its implementation layer. All SDK components integrate with observability through this module.

### Integration with All SDK Components

All SDK components automatically use OTEL Integration when configured:

- **LiteLLM Gateway**: Traces all LLM API calls with token usage and cost metrics
- **RAG System**: Tracks document ingestion, retrieval, and generation operations
- **Agno Agent Framework**: Monitors agent task execution and communication
- **PostgreSQL Database**: Instruments database queries and connection pool usage
- **Cache Mechanism**: Tracks cache operations and hit rates
- **FaaS Services**: Full instrumentation for all service endpoints

## Key Components

### OTELTracer

Provides distributed tracing capabilities:

```python
from src.core.otel_integration import create_otel_tracer

# Create tracer
tracer = create_otel_tracer(
    service_name="ai-sdk",
    otlp_endpoint="http://localhost:4317",
    environment="production",
    service_version="1.0.0"
)

# Start a trace
with tracer.start_trace("operation_name") as span:
    span.set_attribute("key", "value")
    # Your code here
```

### OTELMetrics

Provides metrics collection:

```python
from src.core.otel_integration import create_otel_metrics

# Create metrics
metrics = create_otel_metrics(
    service_name="ai-sdk",
    otlp_endpoint="http://localhost:4317"
)

# Record metrics
metrics.increment_counter("operation.count", value=1)
metrics.record_gauge("active.connections", value=10)
metrics.record_histogram("response.time", value=150.5)
```

### Context Propagation

Propagate trace context across component boundaries:

```python
from src.core.otel_integration import (
    inject_trace_context,
    extract_trace_context,
    get_current_trace_context
)

# Inject context into headers
headers = {}
inject_trace_context(headers)

# Extract context from headers
context = extract_trace_context(headers)

# Get current context
current_context = get_current_trace_context()
```

### Auto-Instrumentation

Automatic instrumentation for common libraries:

```python
from src.core.otel_integration import (
    setup_fastapi_instrumentation,
    setup_httpx_instrumentation,
    setup_asyncpg_instrumentation,
    setup_all_instrumentation
)

# Instrument FastAPI app
setup_fastapi_instrumentation(app)

# Instrument HTTP clients
setup_httpx_instrumentation()

# Instrument database
setup_asyncpg_instrumentation()

# Or instrument everything
setup_all_instrumentation()
```

### Tenant Context

Multi-tenant support with tenant-specific attributes:

```python
from src.core.otel_integration import (
    set_tenant_context,
    get_tenant_context,
    ensure_tenant_attributes_on_span
)

# Set tenant context
set_tenant_context(tenant_id="tenant_123", user_id="user_456")

# Get tenant context
tenant_context = get_tenant_context()

# Ensure tenant attributes on span
with tracer.start_trace("operation") as span:
    ensure_tenant_attributes_on_span(span, tenant_id="tenant_123")
```

### Tenant Context Middleware

FastAPI middleware for automatic tenant context extraction:

```python
from src.core.otel_integration import create_tenant_middleware

# Create middleware
middleware = create_tenant_middleware(
    extract_from_jwt=True,
    extract_from_subdomain=True
)

# Add to FastAPI app
app.add_middleware(middleware)
```

## Function-Driven API

### Factory Functions

```python
from src.core.otel_integration import (
    create_otel_tracer,
    create_otel_metrics
)

# Create tracer
tracer = create_otel_tracer(
    service_name="ai-sdk",
    otlp_endpoint="http://localhost:4317"
)

# Create metrics
metrics = create_otel_metrics(
    service_name="ai-sdk",
    otlp_endpoint="http://localhost:4317"
)
```

### Context Propagation Functions

```python
from src.core.otel_integration import (
    inject_trace_context,
    extract_trace_context,
    get_trace_context,
    get_current_trace_context,
    set_baggage,
    get_baggage
)

# Inject/extract context
headers = {}
inject_trace_context(headers)
context = extract_trace_context(headers)

# Get trace context
trace_context = get_trace_context()

# Baggage operations
set_baggage("key", "value")
value = get_baggage("key")
```

### Tenant Context Functions

```python
from src.core.otel_integration import (
    set_tenant_context,
    get_tenant_context,
    extract_tenant_from_context,
    ensure_tenant_attributes_on_span
)

# Tenant context
set_tenant_context(tenant_id="tenant_123")
tenant_context = get_tenant_context()

# Extract from context
tenant_id = extract_tenant_from_context()

# Ensure on span
ensure_tenant_attributes_on_span(span, tenant_id="tenant_123")
```

## Configuration

### Environment Variables

```bash
# OTLP Exporter Endpoint (required for exporting traces/metrics)
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# Service Configuration
SERVICE_NAME=ai-sdk
SERVICE_VERSION=1.0.0
ENVIRONMENT=production

# Enable/Disable OTEL
ENABLE_OTEL=true
```

### Programmatic Configuration

```python
from src.core.otel_integration import create_otel_tracer

tracer = create_otel_tracer(
    service_name="ai-sdk",
    otlp_endpoint="http://localhost:4317",
    environment="production",
    service_version="1.0.0"
)
```

## Auto-Instrumentation

The module provides automatic instrumentation for:

- **FastAPI**: Automatic tracing of all endpoints
- **HTTPX**: Traces all HTTP requests
- **Requests**: Traces requests library calls
- **AsyncPG**: Traces PostgreSQL database operations
- **SQLAlchemy**: Traces SQLAlchemy queries
- **Redis**: Traces Redis operations

```python
from src.core.otel_integration import setup_all_instrumentation

# Instrument everything
setup_all_instrumentation()

# Or instrument selectively
from src.core.otel_integration import (
    setup_fastapi_instrumentation,
    setup_httpx_instrumentation
)

setup_fastapi_instrumentation(app)
setup_httpx_instrumentation()
```

## Error Handling

The OTEL Integration module implements robust error handling:

- **Graceful Degradation**: Continues operating even if OTEL is unavailable
- **Error Isolation**: OTEL errors don't affect core functionality
- **Retry Logic**: Implements retry logic for OTLP exporter
- **Fallback Mechanisms**: Falls back to no-op when OTEL is disabled

## Best Practices

1. **Configure OTLP Endpoint**: Always set `OTEL_EXPORTER_OTLP_ENDPOINT` in production
2. **Use Auto-Instrumentation**: Enable auto-instrumentation for automatic tracing
3. **Set Tenant Context**: Always set tenant context for multi-tenant applications
4. **Add Meaningful Attributes**: Include relevant attributes in spans
5. **Monitor Performance**: Monitor OTEL overhead and adjust sampling if needed
6. **Use Baggage Sparingly**: Baggage is propagated across all spans, use for essential context only
7. **Configure Sampling**: Use sampling for high-throughput applications

## Examples

### Basic Tracing

```python
from src.core.otel_integration import create_otel_tracer

tracer = create_otel_tracer(service_name="ai-sdk")

with tracer.start_trace("my_operation") as span:
    span.set_attribute("operation.type", "query")
    span.set_attribute("user.id", "user_123")
    # Your code here
    result = perform_operation()
    span.set_attribute("result.size", len(result))
```

### Metrics Collection

```python
from src.core.otel_integration import create_otel_metrics

metrics = create_otel_metrics(service_name="ai-sdk")

# Record counter
metrics.increment_counter("requests.total", value=1)

# Record gauge
metrics.record_gauge("active.connections", value=5)

# Record histogram
metrics.record_histogram("response.time", value=150.5)
```

### Context Propagation

```python
from src.core.otel_integration import inject_trace_context, extract_trace_context
import httpx

# Client side: Inject context
headers = {}
inject_trace_context(headers)

async with httpx.AsyncClient() as client:
    response = await client.get("http://api.example.com", headers=headers)

# Server side: Extract context
def handle_request(request_headers):
    context = extract_trace_context(request_headers)
    # Use context for tracing
```

### Tenant Context

```python
from src.core.otel_integration import set_tenant_context, ensure_tenant_attributes_on_span

# Set tenant context
set_tenant_context(tenant_id="tenant_123", user_id="user_456")

# Ensure on span
with tracer.start_trace("operation") as span:
    ensure_tenant_attributes_on_span(span, tenant_id="tenant_123")
```

## See Also

- **[Evaluation & Observability](../evaluation_observability/README.md)** - High-level observability component
- **[OTEL Integration Guide](../../../docs/integration_guides/otel_integration_guide.md)** - Comprehensive integration guide
- **[OpenTelemetry Documentation](https://opentelemetry.io/docs/)** - Official OpenTelemetry documentation

