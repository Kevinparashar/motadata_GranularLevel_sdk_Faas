# Motadata OTEL Integration Guide

## Overview

This guide explains how to integrate OpenTelemetry observability with AI SDK components.

## Prerequisites

- Core SDK OTEL bootstrap and propagation (versioned dependency)
- OTEL collector or backend configured
- Proper exporter configuration

## Integration Points

### Distributed Tracing

#### Starting a Trace

```python
# Start root trace
with otel_tracer.start_trace("operation.name") as trace:
    trace.set_attribute("tenant.id", tenant_id)
    trace.set_attribute("user.id", user_id)
    
    # Operation code here
    pass
```

#### Creating Child Spans

```python
with otel_tracer.start_span("child.operation", parent=parent_span) as span:
    span.set_attribute("operation.detail", detail)
    # Child operation code here
    pass
```

### Metrics Collection

#### Counter Metrics

```python
# Increment counter
otel_metrics.increment_counter("operation.count", {
    "tenant_id": tenant_id,
    "status": "success"
})
```

#### Histogram Metrics

```python
# Record histogram
otel_metrics.record_histogram("operation.duration", duration, {
    "operation": "query"
})
```

#### Gauge Metrics

```python
# Set gauge
otel_metrics.set_gauge("active.connections", count, {
    "type": "database"
})
```

### LiteLLM Gateway Tracing

```python
with otel_tracer.start_trace("gateway.generate") as trace:
    trace.set_attribute("gateway.model", model)
    trace.set_attribute("gateway.tenant_id", tenant_id)
    
    # Cache check span
    with otel_tracer.start_span("gateway.cache.check", parent=trace):
        # Cache check code
        pass
    
    # Provider call span
    with otel_tracer.start_span("gateway.provider.call", parent=trace):
        # LLM call code
        pass
```

### RAG System Tracing

```python
with otel_tracer.start_trace("rag.query") as trace:
    trace.set_attribute("rag.tenant_id", tenant_id)
    
    # Embedding generation span
    with otel_tracer.start_span("rag.embedding.generate", parent=trace):
        # Embedding code
        pass
    
    # Vector search span
    with otel_tracer.start_span("rag.vector.search", parent=trace):
        # Search code
        pass
```

### Agent Framework Tracing

```python
with otel_tracer.start_trace("agent.task.execute") as trace:
    trace.set_attribute("agent.id", agent_id)
    trace.set_attribute("task.id", task_id)
    
    # Memory retrieval span
    with otel_tracer.start_span("agent.memory.retrieve", parent=trace):
        # Memory code
        pass
    
    # Tool execution span
    with otel_tracer.start_span("agent.tool.execute", parent=trace):
        # Tool code
        pass
```

## Trace Propagation

Traces automatically propagate across components when using the OTEL tracer. Ensure trace context is passed through component boundaries.

## Performance Targets

- Tracing overhead: < 5% of operation time
- Metrics collection overhead: < 2% of operation time
- Logging overhead: < 1% of operation time

## See Also

- [CORE_COMPONENTS_INTEGRATION_STORY.md](../../CORE_COMPONENTS_INTEGRATION_STORY.md)
- Core SDK OTEL bootstrap documentation

