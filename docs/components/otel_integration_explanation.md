# MOTADATA - OTEL INTEGRATION

**Comprehensive explanation of the OTEL Integration component providing observability through OpenTelemetry for distributed tracing, metrics, and logging.**

## Overview

The OTEL Integration component provides comprehensive observability for AI SDK components through OpenTelemetry, enabling distributed tracing, metrics collection, and structured logging across all operations.

## Table of Contents

1. [OTEL Integration Overview](#otel-integration-overview)
2. [Integration Points](#integration-points)
3. [Distributed Tracing](#distributed-tracing)
4. [Metrics Collection](#metrics-collection)
5. [Logging Integration](#logging-integration)
6. [Agent Framework Integration](#agent-framework-integration)
7. [LiteLLM Gateway Integration](#litellm-gateway-integration)
8. [RAG System Integration](#rag-system-integration)
9. [Trace Propagation](#trace-propagation)
10. [Performance Monitoring](#performance-monitoring)
11. [Workflow](#workflow)
12. [Customization](#customization)

---

## OTEL Integration Overview

### Purpose

OTEL integration enables:
- **Distributed Tracing**: Track requests across multiple components
- **Metrics Collection**: Monitor performance, usage, and costs
- **Structured Logging**: Consistent, searchable logs
- **Error Tracking**: Monitor and alert on errors
- **Performance Analysis**: Identify bottlenecks and optimize

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AI SDK Components                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Agent      │  │   Gateway    │  │     RAG      │     │
│  │  Framework   │  │              │  │   System     │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                  │              │
│         └─────────────────┼──────────────────┘              │
│                           │                                  │
│         ┌─────────────────┴──────────────────┐             │
│         │     OTEL Integration Layer           │             │
│         │  ┌──────────────────────────────┐   │             │
│         │  │  OTEL Tracer                 │   │             │
│         │  │  OTEL Metrics                │   │             │
│         │  │  OTEL Logger                 │   │             │
│         │  │  (from Core SDK)             │   │             │
│         │  └──────────────────────────────┘   │             │
│         └─────────────────┬──────────────────┘             │
│                           │                                  │
└───────────────────────────┼──────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              OTEL Collector / Backend                         │
│  (Jaeger, Zipkin, Prometheus, etc.)                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Integration Points

### Component Integration Matrix

| Component | Tracing | Metrics | Logging |
|-----------|---------|---------|---------|
| **Agent Framework** | ✅ Task execution, memory ops, tool execution | ✅ Task count, duration, memory usage | ✅ Task logs, errors |
| **LiteLLM Gateway** | ✅ LLM calls, cache checks, validation | ✅ Token usage, costs, latency | ✅ Request logs, errors |
| **RAG System** | ✅ Query processing, retrieval, generation | ✅ Query count, retrieval time, documents | ✅ Query logs, errors |
| **LLMOps** | ✅ Operation tracking | ✅ Cost tracking, usage stats | ✅ Operation logs |
| **MLOps** | ✅ Training jobs, predictions | ✅ Model performance, latency | ✅ Job logs, errors |

---

## Distributed Tracing

### Trace Structure

```
Root Trace: use_case.document_qa
├── Span: rag.query.process
│   ├── Span: rag.embedding.generate
│   ├── Span: rag.vector.search
│   └── Span: rag.response.generate
│       └── Span: gateway.provider.call
└── Span: agent.task.execute
    ├── Span: agent.memory.retrieve
    └── Span: agent.llm.call
        └── Span: gateway.generate
```

### Starting a Trace

```python
from src.integrations.otel_integration import OTELTracer

# Initialize tracer
tracer = OTELTracer(service_name="ai-sdk", environment="production")

# Start root trace
with tracer.start_trace("operation.name") as trace:
    trace.set_attribute("tenant.id", tenant_id)
    trace.set_attribute("user.id", user_id)
    
    # Operation code here
    result = await perform_operation()
    
    trace.set_attribute("result.status", "success")
```

### Creating Child Spans

```python
with tracer.start_trace("parent.operation") as parent:
    parent.set_attribute("parent.attr", "value")
    
    # Child span
    with tracer.start_span("child.operation", parent=parent) as child:
        child.set_attribute("child.attr", "value")
        # Child operation code
        pass
```

### Recording Exceptions

```python
try:
    # Operation code
    pass
except Exception as e:
    trace.record_exception(e)
    trace.set_status(otel.Status.ERROR, str(e))
    raise
```

---

## Metrics Collection

### Counter Metrics

```python
from src.integrations.otel_integration import OTELMetrics

metrics = OTELMetrics()

# Increment counter
metrics.increment_counter("operation.count", {
    "tenant_id": tenant_id,
    "status": "success"
})

# Increment with amount
metrics.increment_counter("tokens.used", amount=150, {
    "model": "gpt-4"
})
```

### Histogram Metrics

```python
# Record latency
metrics.record_histogram("operation.duration", duration_seconds, {
    "operation": "query",
    "tenant_id": tenant_id
})

# Record token usage
metrics.record_histogram("tokens.used", token_count, {
    "model": "gpt-4",
    "type": "completion"
})
```

### Gauge Metrics

```python
# Set gauge value
metrics.set_gauge("active.connections", connection_count, {
    "type": "database"
})

# Update gauge
metrics.set_gauge("cache.size", cache_size_bytes, {
    "backend": "dragonfly"
})
```

---

## Logging Integration

### Structured Logging

```python
from src.integrations.otel_integration import OTELLogger

logger = OTELLogger("component_name")

# Info log
logger.info("Operation started", extra={
    "operation_id": "op_123",
    "tenant_id": tenant_id
})

# Error log with exception
try:
    # Operation
    pass
except Exception as e:
    logger.error("Operation failed", exc_info=True, extra={
        "operation_id": "op_123",
        "error_type": type(e).__name__
    })
```

### Log Correlation with Traces

```python
# Logs automatically include trace context
with tracer.start_trace("operation") as trace:
    logger.info("Operation started")  # Includes trace_id and span_id
    # Operation code
    logger.info("Operation completed")  # Same trace context
```

---

## Agent Framework Integration

### Task Execution Tracing

```python
class Agent:
    async def execute_task(self, task: AgentTask):
        # Start trace
        with self.otel_tracer.start_trace("agent.task.execute") as trace:
            trace.set_attribute("agent.id", self.agent_id)
            trace.set_attribute("task.id", task.task_id)
            trace.set_attribute("task.type", task.task_type)
            
            start_time = time.time()
            
            try:
                # Memory retrieval span
                with self.otel_tracer.start_span("agent.memory.retrieve", parent=trace) as memory_span:
                    memories = await self.retrieve_memories(task)
                    memory_span.set_attribute("memory.count", len(memories))
                
                # Tool execution span
                if task.requires_tools:
                    with self.otel_tracer.start_span("agent.tool.execute", parent=trace) as tool_span:
                        tool_results = await self.execute_tools(task.tools)
                        tool_span.set_attribute("tools.count", len(tool_results))
                
                # LLM call span
                with self.otel_tracer.start_span("agent.llm.call", parent=trace) as llm_span:
                    response = await self.gateway.generate_async(task.prompt, task.model)
                    llm_span.set_attribute("llm.tokens", response.total_tokens)
                    llm_span.set_attribute("llm.cost", response.cost)
                
                # Record metrics
                duration = time.time() - start_time
                self.otel_metrics.record_histogram("agent.task.duration", duration)
                self.otel_metrics.increment_counter("agent.tasks.executed", {
                    "status": "success"
                })
                
                return response
                
            except Exception as e:
                trace.record_exception(e)
                trace.set_status(otel.Status.ERROR, str(e))
                self.otel_metrics.increment_counter("agent.tasks.executed", {
                    "status": "error",
                    "error_type": type(e).__name__
                })
                raise
```

### Memory Operation Tracking

```python
async def update_memory(self, memory_item: MemoryItem):
    with self.otel_tracer.start_span("agent.memory.update") as span:
        span.set_attribute("memory.type", memory_item.memory_type)
        span.set_attribute("memory.id", memory_item.memory_id)
        
        # Update memory
        await self.memory.store(memory_item)
        
        # Record metric
        self.otel_metrics.increment_counter("agent.memory.updates", {
            "memory_type": memory_item.memory_type
        })
```

---

## LiteLLM Gateway Integration

### LLM Call Tracing

```python
async def generate_async(self, prompt: str, model: str, tenant_id: str):
    with self.otel_tracer.start_trace("gateway.generate") as trace:
        trace.set_attribute("gateway.model", model)
        trace.set_attribute("gateway.tenant_id", tenant_id)
        trace.set_attribute("gateway.prompt.length", len(prompt))
        
        # Cache check span
        with self.otel_tracer.start_span("gateway.cache.check", parent=trace) as cache_span:
            cache_key = self._generate_cache_key(prompt, model)
            cached = await self.cache.get(cache_key)
            cache_span.set_attribute("cache.hit", cached is not None)
            
            if cached:
                self.otel_metrics.increment_counter("gateway.cache.hits")
                return cached
            else:
                self.otel_metrics.increment_counter("gateway.cache.misses")
        
        # Provider call span
        with self.otel_tracer.start_span("gateway.provider.call", parent=trace) as provider_span:
            provider_span.set_attribute("provider", self.provider)
            provider_span.set_attribute("model", model)
            
            response = await self._call_llm_provider(prompt, model)
            
            provider_span.set_attribute("tokens.prompt", response.prompt_tokens)
            provider_span.set_attribute("tokens.completion", response.completion_tokens)
            provider_span.set_attribute("tokens.total", response.total_tokens)
            provider_span.set_attribute("cost.usd", response.cost)
            
            # Record metrics
            self.otel_metrics.increment_counter("gateway.provider.calls", {
                "provider": self.provider,
                "model": model
            })
            self.otel_metrics.record_histogram("gateway.tokens.used", response.total_tokens)
            self.otel_metrics.record_histogram("gateway.cost", response.cost)
        
        return response
```

### Token and Cost Tracking

```python
# Track token usage
self.otel_metrics.record_histogram("gateway.tokens.used", token_count, {
    "model": model,
    "type": "completion"
})

# Track costs
self.otel_metrics.record_histogram("gateway.cost", cost_usd, {
    "model": model,
    "tenant_id": tenant_id
})

# Track per-tenant costs
self.otel_metrics.set_gauge("gateway.cost.per_tenant", total_cost, {
    "tenant_id": tenant_id
})
```

---

## RAG System Integration

### Query Processing Tracing

```python
async def query_async(self, query: str, tenant_id: str):
    with self.otel_tracer.start_trace("rag.query") as trace:
        trace.set_attribute("rag.tenant_id", tenant_id)
        trace.set_attribute("rag.query.length", len(query))
        
        # Embedding generation span
        with self.otel_tracer.start_span("rag.embedding.generate", parent=trace) as embed_span:
            embedding = await self.gateway.generate_embeddings_async(query)
            embed_span.set_attribute("embedding.dimension", len(embedding))
            self.otel_metrics.record_histogram("rag.embedding.duration", duration)
        
        # Vector search span
        with self.otel_tracer.start_span("rag.vector.search", parent=trace) as search_span:
            results = await self.retriever.search(embedding, top_k=5)
            search_span.set_attribute("results.count", len(results))
            self.otel_metrics.record_histogram("rag.search.duration", duration)
        
        # Response generation span
        with self.otel_tracer.start_span("rag.response.generate", parent=trace) as gen_span:
            response = await self.generator.generate(query, results)
            gen_span.set_attribute("response.tokens", response.tokens)
            self.otel_metrics.record_histogram("rag.generation.duration", duration)
        
        # Record overall metrics
        self.otel_metrics.increment_counter("rag.queries.completed", {
            "tenant_id": tenant_id,
            "documents_retrieved": len(results)
        })
        
        return response
```

### Document Ingestion Tracking

```python
async def ingest_document_async(self, document: Document):
    with self.otel_tracer.start_trace("rag.document.ingest") as trace:
        trace.set_attribute("rag.document.id", document.document_id)
        
        # Processing span
        with self.otel_tracer.start_span("rag.document.process", parent=trace) as process_span:
            chunks = await self.processor.process(document)
            process_span.set_attribute("chunks.count", len(chunks))
        
        # Embedding span
        with self.otel_tracer.start_span("rag.embedding.generate", parent=trace) as embed_span:
            embeddings = await self.generate_embeddings(chunks)
            embed_span.set_attribute("embeddings.count", len(embeddings))
        
        # Storage span
        with self.otel_tracer.start_span("rag.document.store", parent=trace) as store_span:
            await self.store_document(document, chunks, embeddings)
        
        # Record metrics
        self.otel_metrics.increment_counter("rag.documents.ingested", {
            "tenant_id": document.tenant_id
        })
```

---

## Trace Propagation

### Propagating Trace Context

```python
# Agent calls Gateway - trace propagates automatically
with tracer.start_trace("agent.task.execute") as agent_trace:
    # Trace context is automatically propagated
    response = await gateway.generate_async(
        prompt=task.prompt,
        model=task.model
    )
    # Gateway span is child of agent trace
```

### Manual Context Propagation

```python
# Get trace context
trace_context = tracer.get_context()

# Pass to another component
result = await other_component.process(
    data=data,
    trace_context=trace_context
)
```

---

## Performance Monitoring

### Key Metrics to Monitor

| Metric | Component | Purpose |
|--------|-----------|---------|
| `agent.task.duration` | Agent | Task execution time |
| `gateway.request.duration` | Gateway | LLM call latency |
| `rag.query.duration` | RAG | End-to-end query time |
| `gateway.tokens.used` | Gateway | Token consumption |
| `gateway.cost` | Gateway | Cost tracking |
| `rag.search.duration` | RAG | Vector search performance |
| `agent.memory.retrieval.duration` | Agent | Memory lookup time |

### Performance Targets

| Operation | Target P95 Latency | Metric |
|-----------|-------------------|--------|
| Agent task execution | < 5 seconds | `agent.task.duration` |
| Gateway LLM call | < 5 seconds | `gateway.request.duration` |
| RAG query | < 10 seconds | `rag.query.duration` |
| Vector search | < 100ms | `rag.search.duration` |
| Memory retrieval | < 50ms | `agent.memory.retrieval.duration` |

---

## Workflow

### Complete Observability Flow

```
1. Operation starts
   │
   ├─→ OTEL: Start trace
   │
   ▼
2. Operation execution
   │
   ├─→ OTEL: Create child spans
   ├─→ OTEL: Record metrics
   ├─→ OTEL: Log events
   │
   ▼
3. Component interactions
   │
   ├─→ OTEL: Propagate trace context
   │
   ▼
4. Operation completes
   │
   ├─→ OTEL: End trace
   ├─→ OTEL: Final metrics
   ├─→ OTEL: Log completion
   │
   ▼
5. Export to backend
   │
   ├─→ Jaeger/Zipkin: Traces
   ├─→ Prometheus: Metrics
   ├─→ ELK/Loki: Logs
```

---

## Customization

### Custom Attributes

```python
# Add custom attributes to spans
span.set_attribute("custom.business.id", business_id)
span.set_attribute("custom.feature.flag", feature_enabled)
```

### Custom Metrics

```python
# Define custom metrics
metrics.record_histogram("custom.metric", value, {
    "custom.tag": "value"
})
```

### Custom Exporters

```python
# Configure custom exporters
tracer.configure_exporter(
    exporter_type="jaeger",
    endpoint="http://jaeger:14268/api/traces"
)
```

---

## Best Practices

1. **Always start traces** for major operations
2. **Use meaningful span names** following naming conventions
3. **Set relevant attributes** for filtering and analysis
4. **Record exceptions** with `record_exception()`
5. **Propagate trace context** across component boundaries
6. **Monitor key metrics** for performance and costs
7. **Use structured logging** with trace correlation
8. **Set appropriate sampling rates** for high-volume operations

---

## See Also

- [CORE_COMPONENTS_INTEGRATION_STORY.md](../../CORE_COMPONENTS_INTEGRATION_STORY.md)
- [OTEL Integration Guide](../../docs/integration_guides/otel_integration_guide.md)
- Core SDK OTEL bootstrap documentation

