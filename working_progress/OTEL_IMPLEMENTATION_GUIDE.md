# OpenTelemetry (OTEL) Implementation Guide for Motadata Python AI SDK

## Introduction

OpenTelemetry (OTEL) provides comprehensive observability through distributed tracing, metrics collection, and log correlation. This guide outlines how OTEL is integrated into the Motadata Python AI SDK, where it's utilized, and how data flows through the system.

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation and Setup](#installation-and-setup)
4. [Component Integration](#component-integration)
5. [Instrumentation Points](#instrumentation-points)
6. [Data Flow](#data-flow)
7. [Exporters and Backends](#exporters-and-backends)
8. [Usage Examples](#usage-examples)
9. [Best Practices](#best-practices)

## Overview

### What is OTEL in This SDK?

OTEL in the Motadata Python AI SDK provides:
- **Distributed Tracing**: Track requests across Agent → RAG → Gateway → Database
- **Metrics Collection**: Monitor performance, token usage, error rates
- **Context Propagation**: Maintain trace context across async operations and NATS messaging
- **Log Correlation**: Correlate logs with traces using trace IDs
- **Performance Monitoring**: Measure latency, throughput, and resource usage

### Why OTEL?

- **Unified Observability**: Single standard for all observability data
- **Vendor Agnostic**: Works with Jaeger, Prometheus, Grafana, and more
- **Context Propagation**: Maintains trace context across components and async operations
- **Production Ready**: Industry-standard for microservices observability

## Architecture

### OTEL Components in SDK

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  (Agent Framework, RAG System, API Backend)                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              OTEL Instrumentation Layer                     │
│  - Tracers (distributed tracing)                            │
│  - Meters (metrics collection)                              │
│  - Loggers (structured logging with trace correlation)      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              OTEL SDK Core                                   │
│  - Context Propagation                                      │
│  - Span Processing                                          │
│  - Metric Aggregation                                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Exporters                                       │
│  - OTLP Exporter (OpenTelemetry Protocol)                   │
│  - Jaeger Exporter                                          │
│  - Prometheus Exporter                                      │
│  - Console Exporter (development)                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Observability Backends                          │
│  - Jaeger (tracing)                                          │
│  - Prometheus (metrics)                                      │
│  - Grafana (visualization)                                  │
│  - Custom backends via OTLP                                  │
└─────────────────────────────────────────────────────────────┘
```

### Integration Points

1. **Agent Framework**: Trace agent task execution, multi-agent coordination
2. **RAG System**: Trace document ingestion, retrieval, and generation
3. **LiteLLM Gateway**: Trace LLM API calls, token usage, latency
4. **Database Operations**: Trace queries, connection pooling
5. **NATS Messaging**: Propagate trace context across pub/sub
6. **API Backend**: Trace HTTP requests end-to-end
7. **Cache Operations**: Trace cache hits/misses, performance

## Installation and Setup

### Prerequisites

```bash
pip install opentelemetry-api opentelemetry-sdk
pip install opentelemetry-instrumentation-fastapi
pip install opentelemetry-exporter-otlp
pip install opentelemetry-exporter-jaeger
pip install opentelemetry-exporter-prometheus
```

### SDK Configuration

Create an OTEL configuration module:

```python
# src/core/evaluation_observability/otel_config.py

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.resources import Resource

def setup_otel(
    service_name: str = "motadata-ai-sdk",
    otlp_endpoint: str = None,
    jaeger_endpoint: str = None,
    enable_console: bool = False
):
    """
    Initialize OpenTelemetry SDK.
    
    Args:
        service_name: Service name for resource identification
        otlp_endpoint: OTLP gRPC endpoint (e.g., "http://localhost:4317")
        jaeger_endpoint: Jaeger endpoint (e.g., "http://localhost:14250")
        enable_console: Enable console exporter for development
    """
    # Create resource
    resource = Resource.create({
        "service.name": service_name,
        "service.version": "1.0.0"
    })
    
    # Setup Tracer Provider
    trace.set_tracer_provider(TracerProvider(resource=resource))
    tracer_provider = trace.get_tracer_provider()
    
    # Add span processors
    if enable_console:
        console_exporter = ConsoleSpanExporter()
        tracer_provider.add_span_processor(
            BatchSpanProcessor(console_exporter)
        )
    
    if otlp_endpoint:
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        tracer_provider.add_span_processor(
            BatchSpanProcessor(otlp_exporter)
        )
    
    if jaeger_endpoint:
        from opentelemetry.exporter.jaeger import JaegerExporter
        jaeger_exporter = JaegerExporter(agent_host_name="localhost", agent_port=6831)
        tracer_provider.add_span_processor(
            BatchSpanProcessor(jaeger_exporter)
        )
    
    # Setup Meter Provider
    if otlp_endpoint:
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        
        metric_exporter = OTLPMetricExporter(endpoint=otlp_endpoint)
        metric_reader = PeriodicExportingMetricReader(metric_exporter)
        metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))
    
    return trace.get_tracer(__name__), metrics.get_meter(__name__)
```

## Component Integration

### 1. Agent Framework Instrumentation

```python
# src/core/agno_agent_framework/agent.py

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

tracer = trace.get_tracer(__name__)

class Agent:
    async def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute task with OTEL tracing."""
        with tracer.start_as_current_span("agent.execute_task") as span:
            span.set_attribute("agent.id", self.agent_id)
            span.set_attribute("agent.name", self.name)
            span.set_attribute("task.id", task.task_id)
            span.set_attribute("task.type", task.task_type)
            
            try:
                # Task execution logic
                result = await self._execute_task_internal(task)
                
                span.set_attribute("task.status", "completed")
                span.set_status(Status(StatusCode.OK))
                return result
                
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
```

### 2. RAG System Instrumentation

```python
# src/core/rag/rag_system.py

from opentelemetry import trace, metrics

tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

# Create metrics
rag_query_counter = meter.create_counter(
    "rag.queries.total",
    description="Total number of RAG queries"
)
rag_query_duration = meter.create_histogram(
    "rag.query.duration",
    description="RAG query duration in seconds"
)
rag_documents_retrieved = meter.create_histogram(
    "rag.documents.retrieved",
    description="Number of documents retrieved per query"
)

class RAGSystem:
    def query(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.7,
        max_tokens: int = 1000,
        use_query_rewriting: bool = True,
        retrieval_strategy: str = "vector"
    ) -> Dict[str, Any]:
        """Query RAG system with OTEL instrumentation."""
        with tracer.start_as_current_span("rag.query") as span:
            span.set_attribute("rag.query.text", query[:100])  # Truncate for privacy
            span.set_attribute("rag.query.top_k", top_k)
            span.set_attribute("rag.query.strategy", retrieval_strategy)
            span.set_attribute("rag.query.rewriting", use_query_rewriting)
            
            start_time = time.time()
            rag_query_counter.add(1, {"strategy": retrieval_strategy})
            
            try:
                # Query rewriting span
                if use_query_rewriting:
                    with tracer.start_as_current_span("rag.query.rewrite") as rewrite_span:
                        query = self._rewrite_query(query)
                        rewrite_span.set_attribute("rag.query.rewritten", query[:100])
                
                # Retrieval span
                with tracer.start_as_current_span("rag.retrieve") as retrieve_span:
                    retrieved_docs = self.retriever.retrieve(
                        query=query,
                        top_k=top_k,
                        threshold=threshold
                    )
                    retrieve_span.set_attribute("rag.documents.count", len(retrieved_docs))
                    rag_documents_retrieved.record(len(retrieved_docs))
                
                # Generation span
                with tracer.start_as_current_span("rag.generate") as generate_span:
                    answer = self.generator.generate(
                        query=query,
                        context_documents=retrieved_docs,
                        max_tokens=max_tokens
                    )
                    generate_span.set_attribute("rag.answer.length", len(answer))
                
                duration = time.time() - start_time
                rag_query_duration.record(duration)
                
                span.set_status(Status(StatusCode.OK))
                return {
                    "answer": answer,
                    "retrieved_documents": retrieved_docs,
                    "num_documents": len(retrieved_docs)
                }
                
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
```

### 3. LiteLLM Gateway Instrumentation

```python
# src/core/litellm_gateway/gateway.py

from opentelemetry import trace, metrics

tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

# Metrics
llm_requests_total = meter.create_counter(
    "llm.requests.total",
    description="Total LLM API requests"
)
llm_tokens_total = meter.create_counter(
    "llm.tokens.total",
    description="Total tokens used"
)
llm_request_duration = meter.create_histogram(
    "llm.request.duration",
    description="LLM request duration in seconds"
)
llm_errors_total = meter.create_counter(
    "llm.errors.total",
    description="Total LLM API errors"
)

class LiteLLMGateway:
    def generate(
        self,
        prompt: str,
        model: str = None,
        **kwargs
    ) -> LLMResponse:
        """Generate text with OTEL instrumentation."""
        model = model or self.default_model
        
        with tracer.start_as_current_span("llm.generate") as span:
            span.set_attribute("llm.provider", self._get_provider(model))
            span.set_attribute("llm.model", model)
            span.set_attribute("llm.prompt.length", len(prompt))
            
            start_time = time.time()
            llm_requests_total.add(1, {"model": model, "provider": self._get_provider(model)})
            
            try:
                response = self._call_llm_api(prompt, model, **kwargs)
                
                duration = time.time() - start_time
                llm_request_duration.record(duration)
                
                # Record token usage
                if hasattr(response, 'usage'):
                    tokens = response.usage.total_tokens
                    llm_tokens_total.add(tokens, {"model": model})
                    span.set_attribute("llm.tokens.prompt", response.usage.prompt_tokens)
                    span.set_attribute("llm.tokens.completion", response.usage.completion_tokens)
                    span.set_attribute("llm.tokens.total", tokens)
                
                span.set_status(Status(StatusCode.OK))
                return response
                
            except Exception as e:
                llm_errors_total.add(1, {"model": model, "error": type(e).__name__})
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
```

### 4. NATS Context Propagation

```python
# src/core/connectivity_clients/nats_client.py

from opentelemetry import trace
from opentelemetry.propagate import inject, extract
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

tracer = trace.get_tracer(__name__)
propagator = TraceContextTextMapPropagator()

class NATSClient:
    async def publish(
        self,
        subject: str,
        message: Dict[str, Any]
    ) -> None:
        """Publish message with trace context propagation."""
        with tracer.start_as_current_span("nats.publish") as span:
            span.set_attribute("nats.subject", subject)
            span.set_attribute("nats.message.size", len(str(message)))
            
            # Inject trace context into message headers
            headers = {}
            inject(headers)
            message["_trace_context"] = headers
            
            await self._nats_connection.publish(subject, json.dumps(message).encode())
    
    async def subscribe(
        self,
        subject: str,
        callback: Callable
    ) -> None:
        """Subscribe with trace context extraction."""
        async def wrapped_callback(msg):
            # Extract trace context from message
            message_data = json.loads(msg.data.decode())
            trace_context = message_data.pop("_trace_context", {})
            
            # Create span with extracted context
            ctx = extract(trace_context)
            with tracer.start_as_current_span("nats.consume", context=ctx) as span:
                span.set_attribute("nats.subject", subject)
                span.set_attribute("nats.message.size", len(msg.data))
                
                await callback(message_data)
        
        await self._nats_connection.subscribe(subject, cb=wrapped_callback)
```

### 5. Database Operations Instrumentation

```python
# src/core/postgresql_database/connection.py

from opentelemetry import trace, metrics

tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

db_query_duration = meter.create_histogram(
    "db.query.duration",
    description="Database query duration in seconds"
)
db_connections_active = meter.create_up_down_counter(
    "db.connections.active",
    description="Active database connections"
)

class DatabaseConnection:
    def execute_query(
        self,
        query: str,
        params: Tuple = None,
        fetch_one: bool = False,
        fetch_all: bool = False
    ) -> Any:
        """Execute query with OTEL instrumentation."""
        with tracer.start_as_current_span("db.query") as span:
            # Truncate query for attribute (avoid sensitive data)
            span.set_attribute("db.query.text", query[:200])
            span.set_attribute("db.query.type", self._get_query_type(query))
            
            start_time = time.time()
            
            try:
                result = self._execute_internal(query, params, fetch_one, fetch_all)
                
                duration = time.time() - start_time
                db_query_duration.record(duration)
                
                span.set_attribute("db.query.rows", len(result) if isinstance(result, list) else 1)
                span.set_status(Status(StatusCode.OK))
                return result
                
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
```

## Instrumentation Points

### Summary of Instrumentation

| Component | Traces | Metrics | Logs |
|-----------|--------|---------|------|
| **Agent Framework** | Task execution, coordination | Task count, duration | Task events |
| **RAG System** | Query, retrieval, generation | Query count, latency, docs retrieved | Query events |
| **LiteLLM Gateway** | LLM API calls | Request count, tokens, latency | API events |
| **Database** | Query execution | Query duration, connection pool | Query events |
| **NATS** | Pub/sub operations | Message count, latency | Message events |
| **API Backend** | HTTP requests | Request count, latency, errors | Request events |
| **Cache** | Cache operations | Hit/miss ratio, latency | Cache events |

## Data Flow

### End-to-End Trace Flow

```
HTTP Request (API)
    │
    ├─> [Span: api.request] (HTTP endpoint)
    │       │
    │       ├─> [Span: agent.execute_task] (Agent Framework)
    │       │       │
    │       │       ├─> [Span: rag.query] (RAG System)
    │       │       │       │
    │       │       │       ├─> [Span: rag.query.rewrite] (Query Rewriting)
    │       │       │       ├─> [Span: rag.retrieve] (Document Retrieval)
    │       │       │       │       │
    │       │       │       │       ├─> [Span: db.query] (Database Query)
    │       │       │       │       └─> [Span: llm.generate] (Embedding Generation)
    │       │       │       │
    │       │       │       └─> [Span: rag.generate] (Response Generation)
    │       │       │               │
    │       │       │               └─> [Span: llm.generate] (LLM API Call)
    │       │       │
    │       │       └─> [Span: nats.publish] (Agent Communication)
    │       │
    │       └─> [Span: cache.get] (Cache Lookup)
    │
    └─> [Span: api.response] (HTTP Response)
```

### Context Propagation

1. **HTTP Request**: Trace context extracted from HTTP headers
2. **Agent Task**: Context propagated to agent execution
3. **RAG Query**: Context propagated to RAG operations
4. **LLM Gateway**: Context propagated to LLM API calls
5. **Database**: Context propagated to database queries
6. **NATS**: Context injected into message headers, extracted on consume
7. **Async Operations**: Context maintained across async boundaries

## Exporters and Backends

### Supported Exporters

1. **OTLP Exporter** (Recommended)
   - OpenTelemetry Protocol (gRPC/HTTP)
   - Works with any OTLP-compatible backend
   - Configuration:
     ```python
     setup_otel(
         service_name="motadata-ai-sdk",
         otlp_endpoint="http://localhost:4317"
     )
     ```

2. **Jaeger Exporter**
   - Direct export to Jaeger
   - Configuration:
     ```python
     setup_otel(
         service_name="motadata-ai-sdk",
         jaeger_endpoint="http://localhost:14250"
     )
     ```

3. **Prometheus Exporter**
   - Metrics export for Prometheus
   - Configuration:
     ```python
     from opentelemetry.exporter.prometheus import PrometheusMetricReader
     metric_reader = PrometheusMetricReader()
     ```

4. **Console Exporter** (Development)
   - Print traces to console
   - Useful for debugging
   - Configuration:
     ```python
     setup_otel(enable_console=True)
     ```

### Backend Integration

#### Jaeger (Tracing)
```yaml
# docker-compose.yml
services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # UI
      - "14250:14250"  # gRPC
      - "6831:6831/udp"  # UDP
```

#### Prometheus (Metrics)
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'motadata-ai-sdk'
    static_configs:
      - targets: ['localhost:8000']
```

#### Grafana (Visualization)
- Connect to Jaeger for traces
- Connect to Prometheus for metrics
- Create dashboards for SDK components

## Usage Examples

### Basic Setup

```python
# main.py
from src.core.evaluation_observability.otel_config import setup_otel
from src.core.agno_agent_framework import create_agent
from src.core.rag import create_rag_system

# Initialize OTEL
tracer, meter = setup_otel(
    service_name="my-ai-service",
    otlp_endpoint="http://localhost:4317",
    enable_console=True  # For development
)

# Use SDK components (automatically instrumented)
gateway = create_gateway()
agent = create_agent("agent1", "Assistant", gateway)
rag = create_rag_system(db, gateway)

# All operations are automatically traced
result = await agent.execute_task(task)
```

### Custom Instrumentation

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def my_custom_function():
    with tracer.start_as_current_span("custom.operation") as span:
        span.set_attribute("custom.param", "value")
        # Your code here
        span.set_status(Status(StatusCode.OK))
```

### Metrics Collection

```python
from opentelemetry import metrics

meter = metrics.get_meter(__name__)

# Create custom counter
custom_counter = meter.create_counter(
    "my.custom.counter",
    description="My custom counter"
)

# Increment counter
custom_counter.add(1, {"label": "value"})
```

## Best Practices

### 1. Span Naming
- Use hierarchical naming: `component.operation.suboperation`
- Examples: `rag.query`, `rag.query.rewrite`, `llm.generate`

### 2. Attributes
- Include relevant context: IDs, types, sizes
- Avoid sensitive data: passwords, tokens, PII
- Use consistent attribute names across components

### 3. Error Handling
- Always set span status on errors
- Record exceptions with `span.record_exception()`
- Include error details in attributes

### 4. Performance
- Use batch span processors for production
- Set appropriate sampling rates
- Monitor exporter performance

### 5. Context Propagation
- Always propagate context in async operations
- Use context managers for automatic cleanup
- Extract/inject context for external calls

### 6. Metrics
- Use appropriate metric types (counter, histogram, gauge)
- Include relevant labels/dimensions
- Avoid high-cardinality labels

## Conclusion

OpenTelemetry provides comprehensive observability for the Motadata Python AI SDK, enabling:

- **End-to-End Tracing**: Track requests across all components
- **Performance Monitoring**: Measure latency and throughput
- **Error Tracking**: Identify and debug issues quickly
- **Context Propagation**: Maintain trace context across async operations and messaging
- **Vendor Agnostic**: Works with any OTLP-compatible backend

For more information, see:
- [OpenTelemetry Python Documentation](https://opentelemetry.io/docs/instrumentation/python/)
- [OTEL Best Practices](https://opentelemetry.io/docs/specs/otel/)
- Component-specific README files in `src/core/`

