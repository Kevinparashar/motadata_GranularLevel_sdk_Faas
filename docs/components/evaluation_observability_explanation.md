# MOTADATA - EVALUATION & OBSERVABILITY

**Comprehensive explanation of the Evaluation & Observability component providing distributed tracing, structured logging, and monitoring capabilities.**

## Overview

The Evaluation & Observability component provides comprehensive traceability, logging, and monitoring capabilities for the entire SDK. It enables tracking of all operations, performance metrics, error monitoring, and system health monitoring across all components using OpenTelemetry standards.

## Table of Contents

1. [Distributed Tracing](#distributed-tracing)
2. [Structured Logging](#structured-logging)
3. [Metrics Collection](#metrics-collection)
4. [Error Tracking](#error-tracking)
5. [Integration Points](#integration-points)
6. [Workflow](#workflow)
7. [Customization](#customization)

---

## Distributed Tracing

### Functionality

Distributed tracing tracks requests across components:
- **Span Creation**: Creates spans for each operation
- **Context Propagation**: Propagates trace context across boundaries
- **Span Relationships**: Maintains parent-child relationships
- **Attribute Tracking**: Records attributes and metadata

### Code Examples

#### Creating Spans

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

# Create span
with tracer.start_as_current_span("operation_name") as span:
    span.set_attribute("component", "agent")
    span.set_attribute("operation", "execute_task")
    # Perform operation
    result = await agent.execute_task(task)
    span.set_attribute("result", "success")
```

---

## Structured Logging

### Functionality

Structured logging provides consistent logs:
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Structured Data**: Parseable log fields
- **Context Information**: Automatic context inclusion
- **Correlation IDs**: Links related log entries

### Code Examples

#### Structured Logging

```python
import structlog

logger = structlog.get_logger()

# Structured log
logger.info(
    "task_executed",
    agent_id="agent_001",
    task_id="task_123",
    duration_ms=150,
    tenant_id="tenant_123"
)
```

---

## Metrics Collection

### Functionality

Metrics collection tracks performance:
- **Counter Metrics**: Event counts
- **Gauge Metrics**: Current values
- **Histogram Metrics**: Distributions
- **Summary Metrics**: Statistical summaries

### Code Examples

#### Recording Metrics

```python
from prometheus_client import Counter, Histogram

# Define metrics
request_count = Counter('requests_total', 'Total requests')
request_duration = Histogram('request_duration_seconds', 'Request duration')

# Record metrics
request_count.inc()
request_duration.observe(0.15)
```

---

## Error Tracking

### Functionality

Error tracking monitors errors:
- **Error Classification**: Classifies by type and severity
- **Error Aggregation**: Aggregates similar errors
- **Error Context**: Captures error context
- **Error Reporting**: Reports to monitoring systems

---

## Integration Points

The component integrates with all SDK components:
- **LiteLLM Gateway**: Tracks LLM calls, token usage, costs
- **RAG System**: Monitors ingestion, retrieval, generation
- **Agents**: Tracks activities, execution times
- **Database**: Monitors query performance
- **API Backend**: Tracks request volumes, response times
- **Cache**: Monitors hit rates, performance

---

## Workflow

### Component Placement in SDK Architecture

The Evaluation & Observability is positioned in the **Foundation Layer**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SDK ARCHITECTURE OVERVIEW                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    FOUNDATION LAYER                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │    EVALUATION & OBSERVABILITY (Foundation Layer)          │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │  │
│  │  │ Distributed │  │  Structured  │  │   Metrics   │    │  │
│  │  │  Tracing    │  │   Logging    │  │  Collection  │    │  │
│  │  │             │  │              │  │              │    │  │
│  │  │ Functions:  │  │ Functions:   │  │ Functions:   │    │  │
│  │  │ - create_  │  │ - log()      │  │ - record()   │    │  │
│  │  │   span()    │  │ - info()     │  │ - counter() │    │  │
│  │  │ - propagate │  │ - error()    │  │ - histogram()│    │  │
│  │  │   context() │  │              │  │              │    │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                      │
│                          │ (Integrates with all components)     │
│                          │                                      │
┌──────────────────────────┼───────────────────────────────────────┐
│                          │                                      │
│  ┌────────────────────────▼──────────────────────────────┐     │
│  │              ALL SDK COMPONENTS                        │     │
│  │  - Agents, RAG, Gateway, Database, API, Cache         │     │
│  │  - All components emit traces, logs, metrics           │     │
│  └───────────────────────────────────────────────────────┘     │
│                                                                  │
│                    APPLICATION/INFRASTRUCTURE LAYERS            │
└──────────────────────────────────────────────────────────────────┘
```

### Distributed Tracing Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│              DISTRIBUTED TRACING WORKFLOW                        │
└─────────────────────────────────────────────────────────────────┘

    [Request Initiated]
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 1: Trace Creation                                   │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ tracer = trace.get_tracer(__name__)               │  │
    │  │ root_span = tracer.start_span("request")          │  │
    │  │                                                   │  │
    │  │ Trace Structure:                                  │  │
    │  │ - Trace ID: Unique identifier                     │  │
    │  │ - Root Span: Entry point                          │  │
    │  │ - Child Spans: Component operations                │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 2: Context Propagation                            │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ context = trace.set_span_in_context(root_span)    │  │
    │  │                                                   │  │
    │  │ Context Propagation:                              │  │
    │  │ - Trace context passed to all components          │  │
    │  │ - Maintains parent-child relationships            │  │
    │  │ - Enables distributed tracing                     │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 3: Component Span Creation                        │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ # In each component:                              │  │
    │  │ with tracer.start_as_current_span("component_op"):│  │
    │  │     span.set_attribute("component", "agent")     │  │
    │  │     span.set_attribute("operation", "execute")    │  │
    │  │     # Perform operation                           │  │
    │  │     span.set_attribute("result", "success")       │  │
    │  │                                                   │  │
    │  │ Span Attributes:                                  │  │
    │  │ - component: Component name                      │  │
    │  │ - operation: Operation name                      │  │
    │  │ - duration: Operation duration                    │  │
    │  │ - result: Operation result                        │  │
    │  │ - tenant_id: Tenant identifier                   │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 4: Span Completion                                 │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ # Spans complete as operations finish             │  │
    │  │ span.end()                                        │  │
    │  │                                                   │  │
    │  │ Span Status:                                      │  │
    │  │ - OK: Operation succeeded                         │  │
    │  │ - ERROR: Operation failed                         │  │
    │  │                                                   │  │
    │  │ Span Events:                                      │  │
    │  │ - Exception events (if errors)                    │  │
    │  │ - Custom events                                   │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 5: Trace Export                                    │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ # Export trace to backend                         │  │
    │  │ exporter.export([span])                           │  │
    │  │                                                   │  │
    │  │ Export Destinations:                              │  │
    │  │ - OTLP endpoint (Jaeger, Tempo, etc.)             │  │
    │  │ - Console (for development)                       │  │
    │  │ - File (for debugging)                           │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    [Trace Available in Monitoring System]
```

### Logging Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    LOGGING WORKFLOW                               │
└─────────────────────────────────────────────────────────────────┘

    [Log Event Created]
           │
           │ Parameters:
           │ - level: str (DEBUG, INFO, WARNING, ERROR, CRITICAL)
           │ - message: str
           │ - **kwargs: Additional structured data
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 1: Context Enrichment                              │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ logger.info(                                      │  │
    │  │     "task_executed",                              │  │
    │  │     agent_id="agent_001",                         │  │
    │  │     task_id="task_123",                            │  │
    │  │     tenant_id="tenant_123"                         │  │
    │  │ )                                                 │  │
    │  │                                                   │  │
    │  │ Context Added:                                    │  │
    │  │ - Correlation ID (from trace context)           │  │
    │  │ - Timestamp                                       │  │
    │  │ - Component name                                  │  │
    │  │ - User/tenant context                             │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 2: Log Formatting                                  │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ # Format log as JSON or structured format        │  │
    │  │ {                                                 │  │
    │  │     "timestamp": "2024-01-01T12:00:00Z",         │  │
    │  │     "level": "INFO",                              │  │
    │  │     "message": "task_executed",                    │  │
    │  │     "agent_id": "agent_001",                      │  │
    │  │     "task_id": "task_123",                        │  │
    │  │     "correlation_id": "trace-123"                 │  │
    │  │ }                                                 │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 3: Log Output                                      │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ # Output to configured destinations              │  │
    │  │ - Console (stdout/stderr)                         │  │
    │  │ - File (log files)                               │  │
    │  │ - Centralized logging (ELK, Loki, etc.)          │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    [Log Available for Analysis]
```

### Metrics Collection Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    METRICS COLLECTION WORKFLOW                   │
└─────────────────────────────────────────────────────────────────┘

    [Metric Event]
           │
           │ Parameters:
           │ - metric_name: str
           │ - metric_type: Counter/Gauge/Histogram
           │ - value: float
           │ - labels: Dict[str, str]
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 1: Metric Recording                                 │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ # Record metric                                    │  │
    │  │ counter.inc(labels={"component": "agent"})       │  │
    │  │ histogram.observe(0.15, labels={"operation": "execute"})│
    │  │                                                   │  │
    │  │ Metric Types:                                      │  │
    │  │ - Counter: Incrementing count                    │  │
    │  │ - Gauge: Current value                            │  │
    │  │ - Histogram: Distribution                        │  │
    │  │ - Summary: Statistical summary                   │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 2: Metric Aggregation                             │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ # Metrics aggregated over time windows            │  │
    │  │ - Per-minute aggregations                         │  │
    │  │ - Per-hour aggregations                           │  │
    │  │ - Per-day aggregations                            │  │
    │  │                                                   │  │
    │  │ Aggregations:                                     │  │
    │  │ - Sum, average, min, max                         │  │
    │  │ - Percentiles (p50, p95, p99)                    │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 3: Metric Export                                   │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ # Export metrics to monitoring systems           │  │
    │  │ - Prometheus (pull-based)                        │  │
    │  │ - OTLP (push-based)                              │  │
    │  │ - Custom exporters                               │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    [Metrics Available in Monitoring System]
```

### Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│              COMPONENT INTERACTION FLOW                          │
└─────────────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │Observability │
                    │  (Foundation)│
                    └──────┬───────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   Tracing     │  │   Logging     │  │   Metrics    │
│               │  │               │  │               │
│ Functions:    │  │ Functions:    │  │ Functions:    │
│ - create_     │  │ - log()       │  │ - counter()  │
│   span()      │  │ - info()      │  │ - gauge()    │
│ - propagate() │  │ - error()     │  │ - histogram()│
└───────┬───────┘  └───────┬───────┘  └───────┬───────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  Exporters   │
                    │              │
                    │ - OTLP       │
                    │ - Prometheus │
                    │ - Jaeger     │
                    └──────────────┘
```

---

## Customization

### Configuration

```python
# Configure OpenTelemetry
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Set up tracer
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Configure exporter
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317")
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)
```

---

## Best Practices

1. **Comprehensive Instrumentation**: Instrument all key operations
2. **Meaningful Attributes**: Include meaningful attributes
3. **Performance Impact**: Minimize observability overhead
4. **Privacy**: Don't log sensitive data
5. **Correlation**: Use correlation IDs
6. **Monitoring**: Monitor observability system itself
7. **Retention**: Implement data retention policies

---

## Additional Resources

- **Component README**: `src/core/evaluation_observability/README.md`
- **OTEL Guide**: `working_progress/OTEL_IMPLEMENTATION_GUIDE.md`
- **Examples**: `examples/basic_usage/01_observability_basic.py`

