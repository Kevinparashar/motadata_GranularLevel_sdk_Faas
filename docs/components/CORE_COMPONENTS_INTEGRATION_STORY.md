# Core Components Integration Story: NATS, OTEL, and CODEC

> **Document Purpose**: This document outlines the integration story for three core platform components (NATS, OTEL, CODEC) into the AI SDK, including implementation plan, validation strategy, testing approach, and weekly progress tracking framework.

## Executive Summary

This document describes how the AI SDK team will integrate three core platform components—**NATS** (messaging), **OTEL** (observability), and **CODEC** (serialization/deserialization)—into AI use cases built with Agent Framework, LiteLLM Gateway, RAG, MLOps, LLMOps, and Prompt Management components.

### Integration Goals

1. **Seamless Integration**: Integrate NATS, OTEL, and CODEC without rebuilding core functionality
2. **API-First Approach**: Use only exposed APIs/wrappers from the core SDK team
3. **Deterministic Validation**: Enable consistent, reviewable integration via PRs and CI
4. **Weekly Progress Tracking**: Demonstrate incremental progress through weekly PRs
5. **Comprehensive Testing**: Integration tests, performance benchmarking, and validation gates

---

## Table of Contents

1. [Component Overview](#component-overview)
2. [Repository Structure](#repository-structure)
3. [Integration Architecture](#integration-architecture)
4. [Component-by-Component Integration Details](#component-by-component-integration-details)
   - [1. Agent Framework Integration](#1-agent-framework-integration)
   - [2. LiteLLM Gateway Integration](#2-litellm-gateway-integration)
   - [3. RAG System Integration](#3-rag-system-integration)
   - [4. LLMOps Integration](#4-llmops-integration)
   - [5. MLOps Integration](#5-mlops-integration)
   - [6. Prompt Context Management Integration](#6-prompt-context-management-integration)
5. [Complete Integration Flow Example](#complete-integration-flow-example)
6. [Validation Strategy](#validation-strategy)
7. [Testing and Benchmarking](#testing-and-benchmarking)
8. [PR Workflow](#pr-workflow)
9. [Implementation Checklist](#implementation-checklist)
10. [Success Criteria](#success-criteria)

---

## Component Overview

### Core Components (Other Team - Platform SDK)

#### 1. NATS (Messaging)
- **Purpose**: Asynchronous messaging for AI component communication
- **Ownership**: Core SDK team
- **Integration Method**: Versioned dependency via internal package/artifact registry or git tag
- **Usage in AI SDK**: 
  - Agent-to-agent communication
  - RAG document processing queues
  - LLM request queuing
  - Event-driven workflows

#### 2. OTEL (OpenTelemetry - Observability)
- **Purpose**: Distributed tracing, metrics, and logging
- **Ownership**: Core SDK team
- **Integration Method**: Versioned dependency with bootstrap and propagation utilities
- **Usage in AI SDK**:
  - Trace AI operations across components
  - Monitor LLM API calls and costs
  - Track RAG query performance
  - Agent task execution monitoring

#### 3. CODEC (Serialization/Deserialization)
- **Purpose**: Message encoding/decoding with schema versioning
- **Ownership**: Core SDK team
- **Integration Method**: Versioned dependency with envelope and schema management
- **Usage in AI SDK**:
  - Serialize agent messages
  - Encode RAG document payloads
  - Format LLM request/response data
  - Version AI component data structures

### AI Components (This Team - AI SDK)

- **Agent Framework**: Autonomous AI agents with session, memory, tools
- **LiteLLM Gateway**: Unified interface for multiple LLM providers
- **RAG System**: Retrieval-Augmented Generation for document Q&A
- **MLOps/LLMOps**: Machine learning operations and LLM operations tracking
- **Prompt Management**: Template-based prompt system with versioning

---

## Repository Structure

### Repository 1: Core SDK (Other Team)
```
core-sdk/
├── nats/
│   ├── wrapper.py          # NATS client wrapper
│   ├── connection.py       # Connection management
│   └── messaging.py        # Message publishing/subscribing
├── otel/
│   ├── bootstrap.py        # OTEL initialization
│   ├── propagation.py      # Trace propagation
│   └── exporters.py        # Metrics/logging exporters
├── codec/
│   ├── envelope.py         # Message envelope
│   ├── schema.py           # Schema management
│   └── versioning.py       # Version handling
├── contracts/
│   ├── schemas/            # Contract schemas
│   └── fixtures/           # Test fixtures
└── validation/
    └── gates.py            # Validation gates
```

### Repository 2: AI SDK (This Team)
```
ai-sdk/
├── src/
│   ├── core/
│   │   ├── agno_agent_framework/
│   │   ├── litellm_gateway/
│   │   ├── rag/
│   │   ├── mlops/
│   │   ├── llmops/
│   │   └── prompt_context_management/
│   ├── integrations/
│   │   ├── nats_integration/      # NEW: NATS integration
│   │   ├── otel_integration/      # NEW: OTEL integration
│   │   └── codec_integration/     # NEW: CODEC integration
│   └── tests/
│       ├── integration_tests/
│       │   ├── test_nats_integration.py
│       │   ├── test_otel_integration.py
│       │   └── test_codec_integration.py
│       └── benchmarks/
│           ├── benchmark_nats_performance.py
│           ├── benchmark_otel_overhead.py
│           └── benchmark_codec_serialization.py
├── examples/
│   └── use_cases/
│       └── [use_case_with_integrations]/
└── docs/
    └── integration_guides/
        ├── nats_integration_guide.md
        ├── otel_integration_guide.md
        └── codec_integration_guide.md
```

---

## Integration Architecture

### High-Level Integration Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI SDK Components                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Agent      │  │ LiteLLM      │  │     RAG      │          │
│  │  Framework   │  │   Gateway    │  │    System    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                  │                   │
│         └─────────────────┼──────────────────┘                  │
│                           │                                     │
│         ┌─────────────────┴──────────────────┐                 │
│         │     Integration Layer               │                 │
│         │  ┌──────┐  ┌──────┐  ┌──────┐      │                 │
│         │  │ NATS │  │ OTEL │  │CODEC │      │                 │
│         │  └──────┘  └──────┘  └──────┘      │                 │
│         └─────────────────┬──────────────────┘                 │
│                           │                                     │
└───────────────────────────┼─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              Core SDK (Other Team)                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ NATS Wrapper│  │ OTEL Bootstrap│  │ CODEC Envelope│         │
│  │   + APIs     │  │   + Propagate │  │   + Schema   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### Integration Points

#### 1. NATS Integration Points
- **Agent Framework**: Agent-to-agent messaging, task distribution
- **RAG System**: Document processing queues, async ingestion
- **LiteLLM Gateway**: Request queuing, rate limit handling
- **MLOps/LLMOps**: Event publishing for operations tracking

#### 2. OTEL Integration Points
- **All AI Components**: Distributed tracing
- **LiteLLM Gateway**: LLM call metrics, token usage, costs
- **RAG System**: Query latency, retrieval performance
- **Agent Framework**: Task execution time, memory usage
- **MLOps/LLMOps**: Model training metrics, prediction latency

#### 3. CODEC Integration Points
- **Agent Framework**: Agent message serialization
- **RAG System**: Document payload encoding/decoding
- **LiteLLM Gateway**: Request/response formatting
- **All Components**: Schema versioning for data structures

---

## Component-by-Component Integration Details

This section provides detailed integration patterns for NATS, OTEL, and CODEC with each AI component, showing exactly how they are used at every integration point from start to finish.

---

## 1. Agent Framework Integration

### 1.1 NATS Integration with Agent Framework

#### Pub/Sub Topics and Channels

**Topic Naming Convention**: `ai.agent.{operation}.{tenant_id}`

| Operation | Topic | Publisher | Subscriber | Purpose |
|-----------|-------|-----------|------------|---------|
| Agent-to-Agent Messaging | `ai.agent.message.{tenant_id}` | Source Agent | Target Agent(s) | Direct agent communication |
| Task Distribution | `ai.agent.tasks.{tenant_id}` | Agent Manager | Worker Agents | Distribute tasks to available agents |
| Task Results | `ai.agent.results.{tenant_id}` | Worker Agent | Agent Manager | Return task execution results |
| Agent Status Updates | `ai.agent.status.{tenant_id}` | All Agents | Agent Manager | Broadcast agent status changes |
| Memory Updates | `ai.agent.memory.{tenant_id}` | Agent | Memory Service | Async memory persistence |
| Tool Execution Requests | `ai.agent.tools.{tenant_id}` | Agent | Tool Executor | Execute tools asynchronously |
| Tool Execution Results | `ai.agent.tool-results.{tenant_id}` | Tool Executor | Agent | Return tool execution results |

#### Integration Points

**1. Agent Task Execution**
```python
# When agent executes a task
async def execute_task(self, task: AgentTask):
    # OTEL: Start trace
    with otel_tracer.start_span("agent.task.execute") as span:
        span.set_attribute("agent.id", self.agent_id)
        span.set_attribute("task.id", task.task_id)
        span.set_attribute("tenant.id", self.tenant_id)
        
        # CODEC: Encode task message
        task_envelope = codec.encode({
            "task_id": task.task_id,
            "agent_id": self.agent_id,
            "task_type": task.task_type,
            "parameters": task.parameters,
            "schema_version": "1.0"
        })
        
        # NATS: Publish task to distribution queue
        await nats_client.publish(
            subject=f"ai.agent.tasks.{self.tenant_id}",
            payload=task_envelope
        )
        
        # OTEL: Record metric
        otel_metrics.increment_counter("agent.tasks.published", {
            "tenant_id": self.tenant_id,
            "agent_id": self.agent_id
        })
```

**2. Agent-to-Agent Communication**
```python
# When agent sends message to another agent
async def send_message(self, target_agent_id: str, message: AgentMessage):
    # OTEL: Start span
    with otel_tracer.start_span("agent.message.send") as span:
        span.set_attribute("source.agent.id", self.agent_id)
        span.set_attribute("target.agent.id", target_agent_id)
        
        # CODEC: Encode message
        message_envelope = codec.encode({
            "message_id": message.message_id,
            "source_agent_id": self.agent_id,
            "target_agent_id": target_agent_id,
            "content": message.content,
            "message_type": message.message_type,
            "timestamp": datetime.now().isoformat(),
            "schema_version": "1.0"
        })
        
        # NATS: Publish to agent message topic
        await nats_client.publish(
            subject=f"ai.agent.message.{self.tenant_id}",
            payload=message_envelope,
            headers={
                "target_agent_id": target_agent_id,
                "source_agent_id": self.agent_id
            }
        )
        
        # OTEL: Record metric
        otel_metrics.increment_counter("agent.messages.sent", {
            "tenant_id": self.tenant_id
        })
```

**3. Agent Memory Updates**
```python
# When agent updates memory
async def update_memory(self, memory_item: MemoryItem):
    # OTEL: Start span
    with otel_tracer.start_span("agent.memory.update") as span:
        span.set_attribute("agent.id", self.agent_id)
        span.set_attribute("memory.type", memory_item.memory_type)
        
        # CODEC: Encode memory item
        memory_envelope = codec.encode({
            "agent_id": self.agent_id,
            "memory_id": memory_item.memory_id,
            "memory_type": memory_item.memory_type,
            "content": memory_item.content,
            "metadata": memory_item.metadata,
            "timestamp": memory_item.timestamp.isoformat(),
            "schema_version": "1.0"
        })
        
        # NATS: Publish to memory update queue (async persistence)
        await nats_client.publish(
            subject=f"ai.agent.memory.{self.tenant_id}",
            payload=memory_envelope
        )
        
        # OTEL: Record metric
        otel_metrics.increment_counter("agent.memory.updates", {
            "tenant_id": self.tenant_id,
            "memory_type": memory_item.memory_type
        })
```

**4. Agent Subscribing to Messages**
```python
# Agent subscribes to receive messages
async def setup_message_subscription(self):
    # NATS: Subscribe to agent message topic
    async def message_handler(msg):
        # CODEC: Decode message
        try:
            message_data = codec.decode(msg.data)
            
            # OTEL: Start span for message processing
            with otel_tracer.start_span("agent.message.receive") as span:
                span.set_attribute("agent.id", self.agent_id)
                span.set_attribute("message.id", message_data["message_id"])
                
                # Process message
                if message_data["target_agent_id"] == self.agent_id:
                    await self.handle_message(message_data)
                    
                    # OTEL: Record metric
                    otel_metrics.increment_counter("agent.messages.received", {
                        "tenant_id": self.tenant_id
                    })
        except Exception as e:
            # OTEL: Record error
            otel_tracer.record_exception(e)
            logger.error(f"Error processing message: {e}")
    
    # Subscribe to topic
    await nats_client.subscribe(
        subject=f"ai.agent.message.{self.tenant_id}",
        callback=message_handler,
        queue=f"agent.{self.agent_id}"  # Queue group for load balancing
    )
```

### 1.2 OTEL Integration with Agent Framework

#### Tracing Points

| Operation | Span Name | Attributes | Metrics |
|-----------|-----------|------------|---------|
| Task Execution | `agent.task.execute` | agent.id, task.id, task.type | agent.tasks.executed, agent.task.duration |
| Message Send | `agent.message.send` | source.agent.id, target.agent.id | agent.messages.sent |
| Message Receive | `agent.message.receive` | agent.id, message.id | agent.messages.received |
| Memory Update | `agent.memory.update` | agent.id, memory.type | agent.memory.updates |
| Memory Retrieve | `agent.memory.retrieve` | agent.id, memory.type, query | agent.memory.retrievals, agent.memory.retrieval.duration |
| Tool Execution | `agent.tool.execute` | agent.id, tool.name | agent.tools.executed, agent.tool.duration |
| Session Management | `agent.session.create` | agent.id, session.id | agent.sessions.created |

#### Complete OTEL Integration Example

```python
class Agent:
    def __init__(self, agent_id: str, tenant_id: str, otel_tracer, otel_metrics):
        self.agent_id = agent_id
        self.tenant_id = tenant_id
        self.otel_tracer = otel_tracer
        self.otel_metrics = otel_metrics
    
    async def execute_task(self, task: AgentTask):
        # Start root span for task execution
        with self.otel_tracer.start_trace("agent.task.execute") as trace:
            # Set trace attributes
            trace.set_attribute("agent.id", self.agent_id)
            trace.set_attribute("task.id", task.task_id)
            trace.set_attribute("task.type", task.task_type)
            trace.set_attribute("tenant.id", self.tenant_id)
            
            # Record start time
            start_time = time.time()
            
            try:
                # Child span: Memory retrieval
                with self.otel_tracer.start_span("agent.memory.retrieve", parent=trace) as memory_span:
                    memories = await self.retrieve_memories(task)
                    memory_span.set_attribute("memory.count", len(memories))
                    self.otel_metrics.record_histogram(
                        "agent.memory.retrieval.duration",
                        time.time() - start_time
                    )
                
                # Child span: Tool execution (if needed)
                if task.requires_tools:
                    with self.otel_tracer.start_span("agent.tool.execute", parent=trace) as tool_span:
                        tool_results = await self.execute_tools(task.tools)
                        tool_span.set_attribute("tools.count", len(tool_results))
                        self.otel_metrics.increment_counter("agent.tools.executed")
                
                # Child span: LLM call (via Gateway - will have its own trace)
                with self.otel_tracer.start_span("agent.llm.call", parent=trace) as llm_span:
                    response = await self.gateway.generate_async(
                        prompt=task.prompt,
                        model=task.model
                    )
                    llm_span.set_attribute("llm.model", task.model)
                    llm_span.set_attribute("llm.tokens", response.total_tokens)
                    llm_span.set_attribute("llm.cost", response.cost)
                
                # Child span: Memory update
                with self.otel_tracer.start_span("agent.memory.update", parent=trace) as update_span:
                    await self.update_memory(task, response)
                    self.otel_metrics.increment_counter("agent.memory.updates")
                
                # Record success metrics
                duration = time.time() - start_time
                self.otel_metrics.record_histogram("agent.task.duration", duration)
                self.otel_metrics.increment_counter("agent.tasks.executed", {
                    "status": "success"
                })
                
                return response
                
            except Exception as e:
                # Record error
                trace.record_exception(e)
                trace.set_status(otel.Status.ERROR, str(e))
                self.otel_metrics.increment_counter("agent.tasks.executed", {
                    "status": "error",
                    "error_type": type(e).__name__
                })
                raise
```

### 1.3 CODEC Integration with Agent Framework

#### Schema Definitions

**Agent Message Schema (v1.0)**
```json
{
  "schema_version": "1.0",
  "message_type": "agent_message",
  "data": {
    "message_id": "string",
    "source_agent_id": "string",
    "target_agent_id": "string",
    "content": "string",
    "message_type": "string",
    "timestamp": "datetime",
    "metadata": {}
  }
}
```

**Agent Task Schema (v1.0)**
```json
{
  "schema_version": "1.0",
  "message_type": "agent_task",
  "data": {
    "task_id": "string",
    "agent_id": "string",
    "task_type": "string",
    "parameters": {},
    "priority": "integer",
    "timestamp": "datetime"
  }
}
```

#### Encoding/Decoding Examples

```python
# Encoding agent message
def encode_agent_message(message: AgentMessage) -> bytes:
    envelope = codec.create_envelope(
        message_type="agent_message",
        schema_version="1.0",
        data={
            "message_id": message.message_id,
            "source_agent_id": message.source_agent_id,
            "target_agent_id": message.target_agent_id,
            "content": message.content,
            "message_type": message.message_type,
            "timestamp": message.timestamp.isoformat(),
            "metadata": message.metadata
        }
    )
    return codec.encode(envelope)

# Decoding agent message
def decode_agent_message(payload: bytes) -> AgentMessage:
    envelope = codec.decode(payload)
    
    # Validate schema version
    if envelope["schema_version"] != "1.0":
        # Handle version migration
        envelope = codec.migrate_envelope(envelope, target_version="1.0")
    
    # Validate schema
    codec.validate_schema(envelope, schema_name="agent_message")
    
    data = envelope["data"]
    return AgentMessage(
        message_id=data["message_id"],
        source_agent_id=data["source_agent_id"],
        target_agent_id=data["target_agent_id"],
        content=data["content"],
        message_type=data["message_type"],
        timestamp=datetime.fromisoformat(data["timestamp"]),
        metadata=data["metadata"]
    )
```

---

## 2. LiteLLM Gateway Integration

### 2.1 NATS Integration with LiteLLM Gateway

#### Pub/Sub Topics and Channels

| Operation | Topic | Publisher | Subscriber | Purpose |
|-----------|-------|-----------|------------|---------|
| LLM Request Queue | `ai.gateway.requests.{tenant_id}` | API/Components | Gateway Workers | Queue LLM requests for processing |
| LLM Response Queue | `ai.gateway.responses.{tenant_id}` | Gateway Workers | Requesters | Return LLM responses |
| Rate Limit Events | `ai.gateway.rate-limit.{tenant_id}` | Rate Limiter | Monitoring | Rate limit events and violations |
| Cache Invalidation | `ai.gateway.cache.invalidate.{tenant_id}` | Gateway | Cache Service | Invalidate cached responses |
| Provider Health | `ai.gateway.health.{tenant_id}` | Gateway | Health Monitor | Provider health status updates |
| Cost Alerts | `ai.gateway.cost-alerts.{tenant_id}` | LLMOps | Alerting | Cost threshold alerts |

#### Integration Points

**1. LLM Request Queuing**
```python
async def generate_async(self, prompt: str, model: str, tenant_id: str):
    # OTEL: Start trace
    with otel_tracer.start_trace("gateway.generate") as trace:
        trace.set_attribute("gateway.model", model)
        trace.set_attribute("gateway.tenant_id", tenant_id)
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # CODEC: Encode request
        request_envelope = codec.encode({
            "request_id": request_id,
            "prompt": prompt,
            "model": model,
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
            "schema_version": "1.0"
        })
        
        # NATS: Publish to request queue
        await nats_client.publish(
            subject=f"ai.gateway.requests.{tenant_id}",
            payload=request_envelope,
            headers={
                "request_id": request_id,
                "model": model,
                "priority": "normal"
            }
        )
        
        # OTEL: Record metric
        otel_metrics.increment_counter("gateway.requests.queued", {
            "model": model,
            "tenant_id": tenant_id
        })
        
        # NATS: Subscribe to response queue for this request
        response = await nats_client.request(
            subject=f"ai.gateway.responses.{tenant_id}",
            payload=request_envelope,
            timeout=60.0
        )
        
        # CODEC: Decode response
        response_data = codec.decode(response.data)
        
        # OTEL: Record metrics
        otel_metrics.record_histogram("gateway.request.duration", response_data["duration"])
        otel_metrics.increment_counter("gateway.requests.completed", {
            "model": model,
            "status": response_data["status"]
        })
        
        return response_data
```

**2. Gateway Worker Processing**
```python
async def gateway_worker(tenant_id: str):
    # NATS: Subscribe to request queue
    async def process_request(msg):
        # CODEC: Decode request
        request_data = codec.decode(msg.data)
        
        # OTEL: Start span
        with otel_tracer.start_span("gateway.worker.process") as span:
            span.set_attribute("request.id", request_data["request_id"])
            span.set_attribute("model", request_data["model"])
            
            try:
                # Check cache first
                cache_key = generate_cache_key(request_data)
                cached_response = await cache.get(cache_key)
                
                if cached_response:
                    # OTEL: Record cache hit
                    otel_metrics.increment_counter("gateway.cache.hits")
                    span.set_attribute("cache.hit", True)
                    
                    # CODEC: Encode cached response
                    response_envelope = codec.encode(cached_response)
                else:
                    # OTEL: Record cache miss
                    otel_metrics.increment_counter("gateway.cache.misses")
                    span.set_attribute("cache.hit", False)
                    
                    # Make LLM call
                    llm_response = await make_llm_call(request_data)
                    
                    # CODEC: Encode response
                    response_envelope = codec.encode({
                        "request_id": request_data["request_id"],
                        "response": llm_response.text,
                        "tokens": llm_response.total_tokens,
                        "cost": llm_response.cost,
                        "model": request_data["model"],
                        "timestamp": datetime.now().isoformat(),
                        "schema_version": "1.0"
                    })
                    
                    # Cache response
                    await cache.set(cache_key, response_envelope)
                
                # NATS: Publish response
                await nats_client.publish(
                    subject=f"ai.gateway.responses.{tenant_id}",
                    payload=response_envelope,
                    headers={
                        "request_id": request_data["request_id"]
                    }
                )
                
            except Exception as e:
                # OTEL: Record error
                span.record_exception(e)
                span.set_status(otel.Status.ERROR)
                
                # Publish error response
                error_envelope = codec.encode({
                    "request_id": request_data["request_id"],
                    "error": str(e),
                    "status": "error",
                    "schema_version": "1.0"
                })
                await nats_client.publish(
                    subject=f"ai.gateway.responses.{tenant_id}",
                    payload=error_envelope
                )
    
    # Subscribe to request queue
    await nats_client.subscribe(
        subject=f"ai.gateway.requests.{tenant_id}",
        callback=process_request,
        queue="gateway.workers"  # Queue group for load balancing
    )
```

### 2.2 OTEL Integration with LiteLLM Gateway

#### Tracing Points

| Operation | Span Name | Attributes | Metrics |
|-----------|-----------|------------|---------|
| LLM Request | `gateway.generate` | model, tenant_id, request_id | gateway.requests.queued, gateway.request.duration |
| Cache Check | `gateway.cache.check` | cache.key, cache.hit | gateway.cache.hits, gateway.cache.misses |
| LLM Provider Call | `gateway.provider.call` | provider, model, tokens | gateway.provider.calls, gateway.tokens.used, gateway.cost |
| Rate Limiting | `gateway.rate-limit.check` | tenant_id, model | gateway.rate-limit.checks, gateway.rate-limit.violations |
| Response Validation | `gateway.validate` | validation.level, validation.passed | gateway.validation.checks |

#### Complete OTEL Integration

```python
class LiteLLMGateway:
    async def generate_async(self, prompt: str, model: str, tenant_id: str):
        # Start trace
        with self.otel_tracer.start_trace("gateway.generate") as trace:
            trace.set_attribute("gateway.model", model)
            trace.set_attribute("gateway.tenant_id", tenant_id)
            trace.set_attribute("gateway.prompt.length", len(prompt))
            
            start_time = time.time()
            
            try:
                # Child span: Cache check
                with self.otel_tracer.start_span("gateway.cache.check", parent=trace) as cache_span:
                    cache_key = self._generate_cache_key(prompt, model)
                    cached = await self.cache.get(cache_key)
                    cache_span.set_attribute("cache.key", cache_key)
                    cache_span.set_attribute("cache.hit", cached is not None)
                    
                    if cached:
                        self.otel_metrics.increment_counter("gateway.cache.hits")
                        return cached
                    else:
                        self.otel_metrics.increment_counter("gateway.cache.misses")
                
                # Child span: Rate limit check
                with self.otel_tracer.start_span("gateway.rate-limit.check", parent=trace) as rate_span:
                    allowed = await self.rate_limiter.acquire(tenant_id, model)
                    rate_span.set_attribute("rate-limit.allowed", allowed)
                    
                    if not allowed:
                        self.otel_metrics.increment_counter("gateway.rate-limit.violations")
                        raise RateLimitError("Rate limit exceeded")
                    
                    self.otel_metrics.increment_counter("gateway.rate-limit.checks")
                
                # Child span: LLM provider call
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
                
                # Child span: Response validation
                with self.otel_tracer.start_span("gateway.validate", parent=trace) as validate_span:
                    validation_result = await self.validation_manager.validate(response.text)
                    validate_span.set_attribute("validation.passed", validation_result.passed)
                    validate_span.set_attribute("validation.level", validation_result.level)
                    self.otel_metrics.increment_counter("gateway.validation.checks", {
                        "passed": validation_result.passed
                    })
                
                # Cache response
                await self.cache.set(cache_key, response)
                
                # Record success metrics
                duration = time.time() - start_time
                self.otel_metrics.record_histogram("gateway.request.duration", duration)
                self.otel_metrics.increment_counter("gateway.requests.completed", {
                    "status": "success",
                    "model": model
                })
                
                return response
                
            except Exception as e:
                trace.record_exception(e)
                trace.set_status(otel.Status.ERROR, str(e))
                self.otel_metrics.increment_counter("gateway.requests.completed", {
                    "status": "error",
                    "error_type": type(e).__name__
                })
                raise
```

### 2.3 CODEC Integration with LiteLLM Gateway

#### Schema Definitions

**LLM Request Schema (v1.0)**
```json
{
  "schema_version": "1.0",
  "message_type": "llm_request",
  "data": {
    "request_id": "string",
    "prompt": "string",
    "model": "string",
    "tenant_id": "string",
    "parameters": {
      "temperature": "float",
      "max_tokens": "integer"
    },
    "timestamp": "datetime"
  }
}
```

**LLM Response Schema (v1.0)**
```json
{
  "schema_version": "1.0",
  "message_type": "llm_response",
  "data": {
    "request_id": "string",
    "response": "string",
    "tokens": {
      "prompt": "integer",
      "completion": "integer",
      "total": "integer"
    },
    "cost": "float",
    "model": "string",
    "timestamp": "datetime"
  }
}
```

---

## 3. RAG System Integration

### 3.1 NATS Integration with RAG System

#### Pub/Sub Topics and Channels

| Operation | Topic | Publisher | Subscriber | Purpose |
|-----------|-------|-----------|------------|---------|
| Document Ingestion Queue | `ai.rag.ingest.{tenant_id}` | API/Components | RAG Workers | Queue documents for processing |
| Document Processing Status | `ai.rag.status.{tenant_id}` | RAG Workers | Requesters | Document processing status updates |
| Query Queue | `ai.rag.queries.{tenant_id}` | API/Components | RAG Workers | Queue RAG queries |
| Query Results | `ai.rag.results.{tenant_id}` | RAG Workers | Requesters | Return query results |
| Embedding Generation | `ai.rag.embeddings.{tenant_id}` | RAG Workers | Gateway | Request embeddings |
| Embedding Results | `ai.rag.embedding-results.{tenant_id}` | Gateway | RAG Workers | Return embeddings |

#### Integration Points

**1. Document Ingestion**
```python
async def ingest_document_async(self, document: Document, tenant_id: str):
    # OTEL: Start trace
    with otel_tracer.start_trace("rag.document.ingest") as trace:
        trace.set_attribute("rag.tenant_id", tenant_id)
        trace.set_attribute("rag.document.id", document.document_id)
        
        # CODEC: Encode document
        document_envelope = codec.encode({
            "document_id": document.document_id,
            "content": document.content,
            "metadata": document.metadata,
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
            "schema_version": "1.0"
        })
        
        # NATS: Publish to ingestion queue
        await nats_client.publish(
            subject=f"ai.rag.ingest.{tenant_id}",
            payload=document_envelope
        )
        
        # OTEL: Record metric
        otel_metrics.increment_counter("rag.documents.queued", {
            "tenant_id": tenant_id
        })
        
        # Subscribe to status updates
        status = await nats_client.request(
            subject=f"ai.rag.status.{tenant_id}",
            payload=document_envelope,
            timeout=300.0
        )
        
        return status
```

**2. RAG Query Processing**
```python
async def query_async(self, query: str, tenant_id: str):
    # OTEL: Start trace
    with otel_tracer.start_trace("rag.query") as trace:
        trace.set_attribute("rag.tenant_id", tenant_id)
        trace.set_attribute("rag.query.length", len(query))
        
        query_id = str(uuid.uuid4())
        
        # CODEC: Encode query
        query_envelope = codec.encode({
            "query_id": query_id,
            "query": query,
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
            "schema_version": "1.0"
        })
        
        # NATS: Publish to query queue
        await nats_client.publish(
            subject=f"ai.rag.queries.{tenant_id}",
            payload=query_envelope
        )
        
        # OTEL: Record metric
        otel_metrics.increment_counter("rag.queries.queued", {
            "tenant_id": tenant_id
        })
        
        # Subscribe to results
        result_envelope = await nats_client.request(
            subject=f"ai.rag.results.{tenant_id}",
            payload=query_envelope,
            timeout=30.0
        )
        
        # CODEC: Decode results
        results = codec.decode(result_envelope.data)
        
        # OTEL: Record metrics
        otel_metrics.record_histogram("rag.query.duration", results["duration"])
        otel_metrics.increment_counter("rag.queries.completed", {
            "tenant_id": tenant_id,
            "documents_retrieved": len(results["documents"])
        })
        
        return results
```

### 3.2 OTEL Integration with RAG System

#### Tracing Points

| Operation | Span Name | Attributes | Metrics |
|-----------|-----------|------------|---------|
| Document Ingestion | `rag.document.ingest` | tenant_id, document.id | rag.documents.ingested, rag.ingestion.duration |
| Document Processing | `rag.document.process` | tenant_id, chunks.count | rag.documents.processed |
| Embedding Generation | `rag.embedding.generate` | tenant_id, embedding.model | rag.embeddings.generated, rag.embedding.duration |
| Vector Search | `rag.vector.search` | tenant_id, query.id, results.count | rag.searches.executed, rag.search.duration |
| Query Processing | `rag.query` | tenant_id, query.id | rag.queries.executed, rag.query.duration |
| Response Generation | `rag.response.generate` | tenant_id, tokens | rag.responses.generated |

### 3.3 CODEC Integration with RAG System

#### Schema Definitions

**Document Schema (v1.0)**
```json
{
  "schema_version": "1.0",
  "message_type": "rag_document",
  "data": {
    "document_id": "string",
    "content": "string",
    "metadata": {},
    "chunks": [
      {
        "chunk_id": "string",
        "content": "string",
        "embedding": "array<float>",
        "metadata": {}
      }
    ],
    "tenant_id": "string",
    "timestamp": "datetime"
  }
}
```

**RAG Query Schema (v1.0)**
```json
{
  "schema_version": "1.0",
  "message_type": "rag_query",
  "data": {
    "query_id": "string",
    "query": "string",
    "tenant_id": "string",
    "parameters": {
      "top_k": "integer",
      "similarity_threshold": "float"
    },
    "timestamp": "datetime"
  }
}
```

---

## 4. LLMOps Integration

### 4.1 NATS Integration with LLMOps

#### Pub/Sub Topics

| Operation | Topic | Purpose |
|-----------|-------|---------|
| Operation Logging | `ai.llmops.operations.{tenant_id}` | Log LLM operations |
| Cost Alerts | `ai.llmops.cost-alerts.{tenant_id}` | Cost threshold alerts |
| Usage Reports | `ai.llmops.reports.{tenant_id}` | Usage report requests |

### 4.2 OTEL Integration with LLMOps

LLMOps uses OTEL for:
- Tracking all LLM operations
- Recording token usage and costs
- Monitoring operation latency
- Generating usage reports

### 4.3 CODEC Integration with LLMOps

**LLM Operation Schema (v1.0)**
```json
{
  "schema_version": "1.0",
  "message_type": "llm_operation",
  "data": {
    "operation_id": "string",
    "operation_type": "string",
    "model": "string",
    "tokens": {
      "prompt": "integer",
      "completion": "integer",
      "total": "integer"
    },
    "cost": "float",
    "latency_ms": "float",
    "status": "string",
    "tenant_id": "string",
    "timestamp": "datetime"
  }
}
```

---

## 5. MLOps Integration

### 5.1 NATS Integration with MLOps

| Operation | Topic | Purpose |
|-----------|-------|---------|
| Training Jobs | `ai.mlops.training.{tenant_id}` | Queue training jobs |
| Prediction Requests | `ai.mlops.predictions.{tenant_id}` | Queue prediction requests |
| Model Deployment | `ai.mlops.deploy.{tenant_id}` | Model deployment events |

### 5.2 OTEL Integration with MLOps

Tracks:
- Training job execution
- Model inference latency
- Model performance metrics
- Deployment events

### 5.3 CODEC Integration with MLOps

**Training Job Schema (v1.0)**
```json
{
  "schema_version": "1.0",
  "message_type": "ml_training_job",
  "data": {
    "job_id": "string",
    "model_type": "string",
    "training_data": "string",
    "parameters": {},
    "tenant_id": "string",
    "timestamp": "datetime"
  }
}
```

---

## 6. Prompt Context Management Integration

### 6.1 NATS Integration

| Operation | Topic | Purpose |
|-----------|-------|---------|
| Template Updates | `ai.prompt.templates.{tenant_id}` | Template update events |
| Context Building | `ai.prompt.context.{tenant_id}` | Context building requests |

### 6.2 OTEL Integration

Tracks:
- Template rendering
- Context building operations
- Token estimation

### 6.3 CODEC Integration

**Prompt Template Schema (v1.0)**
```json
{
  "schema_version": "1.0",
  "message_type": "prompt_template",
  "data": {
    "template_id": "string",
    "template": "string",
    "variables": {},
    "version": "string",
    "tenant_id": "string"
  }
}
```

---

## Validation Strategy

### Validation Gates

#### 1. Integration Tests
- **Purpose**: Verify NATS, OTEL, CODEC work correctly with AI components
- **Criteria**:
  - All integration tests pass
  - Test coverage > 80%
  - No regressions in existing functionality
- **Location**: `src/tests/integration_tests/`
- **Run Command**: `pytest src/tests/integration_tests/test_*_integration.py -v`

#### 2. Performance Benchmarking
- **Purpose**: Ensure integration doesn't degrade performance
- **Criteria**:
  - NATS messaging latency < 10ms
  - OTEL overhead < 5% of operation time
  - CODEC serialization < 1ms
  - No performance regressions
- **Location**: `src/tests/benchmarks/`
- **Run Command**: `pytest src/tests/benchmarks/benchmark_*_integration.py --benchmark-only`

#### 3. API Contract Validation
- **Purpose**: Verify correct usage of Core SDK APIs
- **Criteria**:
  - All API calls use correct interfaces
  - No direct access to internal Core SDK code
  - Schema validation passes
  - Version compatibility maintained
- **Validation Method**: Static analysis + integration tests

#### 4. Code Review Validation
- **Purpose**: Ensure code quality and integration correctness
- **Criteria**:
  - Code follows SDK patterns
  - Integration code is well-documented
  - Error handling is comprehensive
  - No breaking changes to existing APIs

### Validation Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    PR Created                                │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Automated CI Validation                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Integration  │  │  Performance │  │   Code       │     │
│  │    Tests      │  │  Benchmarks  │  │   Quality    │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                  │              │
│         └─────────────────┼──────────────────┘              │
│                           │                                  │
└───────────────────────────┼──────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ All Checks    │
                    │   Pass?       │
                    └───────┬───────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
            ▼                               ▼
    ┌───────────────┐              ┌───────────────┐
    │   YES         │              │      NO       │
    │               │              │               │
    │  Ready for    │              │  Fix Issues   │
    │  Code Review  │              │  & Resubmit   │
    └───────┬───────┘              └───────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│              Other Team Code Review                         │
│  - Integration correctness                                  │
│  - API usage validation                                     │
│  - Performance impact review                                │
│  - Documentation review                                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
                    ┌───────────────┐
                    │  Approved?    │
                    └───────┬───────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
            ▼                               ▼
    ┌───────────────┐              ┌───────────────┐
    │   YES         │              │      NO        │
    │               │              │               │
    │    MERGE      │              │  Address      │
    │               │              │  Feedback     │
    └───────────────┘              └───────────────┘
```

---

## Testing and Benchmarking

### Integration Tests

#### Test Structure
```
src/tests/integration_tests/
├── test_nats_integration.py
│   ├── test_nats_agent_messaging()
│   ├── test_nats_rag_queue()
│   ├── test_nats_gateway_queuing()
│   └── test_nats_error_handling()
├── test_otel_integration.py
│   ├── test_otel_gateway_tracing()
│   ├── test_otel_rag_metrics()
│   ├── test_otel_agent_tracing()
│   └── test_otel_trace_propagation()
├── test_codec_integration.py
│   ├── test_codec_agent_serialization()
│   ├── test_codec_rag_payload()
│   ├── test_codec_schema_validation()
│   └── test_codec_versioning()
└── test_full_integration.py
    ├── test_nats_otel_codec_together()
    ├── test_end_to_end_use_case()
    └── test_integration_error_recovery()
```

#### Test Requirements
- **Coverage**: > 80% for integration code
- **Execution Time**: < 5 minutes for full suite
- **Isolation**: Tests must be independent and parallelizable
- **Mocking**: Use Core SDK test fixtures where available

### Performance Benchmarks

#### Benchmark Structure
```
src/tests/benchmarks/
├── benchmark_nats_performance.py
│   ├── benchmark_agent_messaging_latency()
│   ├── benchmark_rag_queue_throughput()
│   └── benchmark_gateway_queuing_performance()
├── benchmark_otel_overhead.py
│   ├── benchmark_tracing_overhead()
│   ├── benchmark_metrics_collection_overhead()
│   └── benchmark_logging_overhead()
└── benchmark_codec_serialization.py
    ├── benchmark_agent_message_serialization()
    ├── benchmark_rag_payload_encoding()
    └── benchmark_schema_validation_latency()
```

#### Performance Targets

| Component | Metric | Target | Measurement |
|-----------|--------|--------|-------------|
| **NATS** | Agent messaging latency | < 10ms | P95 latency |
| | RAG queue throughput | > 100 msg/sec | Messages per second |
| | Gateway queuing latency | < 5ms | P95 latency |
| **OTEL** | Tracing overhead | < 5% | % of operation time |
| | Metrics collection overhead | < 2% | % of operation time |
| | Logging overhead | < 1% | % of operation time |
| **CODEC** | Agent message serialization | < 1ms | P95 latency |
| | RAG payload encoding | < 2ms | P95 latency |
| | Schema validation | < 0.5ms | P95 latency |

### Benchmark Execution

```bash
# Run all integration benchmarks
pytest src/tests/benchmarks/benchmark_*_integration.py --benchmark-only

# Run specific benchmark
pytest src/tests/benchmarks/benchmark_nats_performance.py -v --benchmark-only

# Generate benchmark report
pytest src/tests/benchmarks/ --benchmark-json=benchmark_results.json
```

---

## PR Workflow

### Cross-Repo PR Process

#### Step 1: Create Feature Branch
```bash
# In AI SDK repo
git checkout -b feature/nats-integration-week-2
```

#### Step 2: Implement Integration
- Write integration code
- Add integration tests
- Add performance benchmarks
- Update documentation

#### Step 3: Run Local Validation
```bash
# Run integration tests
pytest src/tests/integration_tests/test_nats_integration.py -v

# Run performance benchmarks
pytest src/tests/benchmarks/benchmark_nats_performance.py --benchmark-only

# Check code coverage
pytest src/tests/integration_tests/ --cov=src/integrations --cov-report=html
```

#### Step 4: Create PR
- **Title**: `[Integration] NATS Integration - Week 2: Agent Messaging`
- **Description Template**:
  ```markdown
  ## Integration: NATS with Agent Framework
  
  ### Changes
  - Implemented NATS messaging for agent-to-agent communication
  - Added integration tests (coverage: 85%)
  - Added performance benchmarks (latency: 8ms P95)
  
  ### Tests
  - [x] Integration tests passing
  - [x] Performance benchmarks meeting targets
  - [x] No regressions in existing functionality
  
  ### Documentation
  - [x] Integration guide updated
  - [x] API documentation updated
  
  ### Validation
  - Integration tests: ✅ Pass
  - Performance benchmarks: ✅ Pass (8ms < 10ms target)
  - Code coverage: ✅ 85% (> 80% target)
  
  ### Related
  - Closes #[issue-number]
  - Related to Core SDK: [core-sdk-version]
  ```

#### Step 5: CI Validation
- Automated integration tests run
- Performance benchmarks execute
- Code quality checks
- Coverage report generated

#### Step 6: Cross-Repo Review
- **Other Team Reviews**:
  - Integration correctness
  - API usage validation
  - Performance impact
  - Documentation quality
- **This Team Addresses Feedback**

#### Step 7: Merge
- After approval, merge PR
- Tag release if needed
- Update integration status

### PR Checklist Template

```markdown
## PR Checklist

### Code
- [ ] Integration code follows SDK patterns
- [ ] Error handling is comprehensive
- [ ] Code is well-documented
- [ ] No breaking changes to existing APIs

### Tests
- [ ] Integration tests added and passing
- [ ] Performance benchmarks added and meeting targets
- [ ] Test coverage > 80%
- [ ] No regressions in existing tests

### Documentation
- [ ] Integration guide updated
- [ ] API documentation updated
- [ ] Code examples provided
- [ ] Performance results documented

### Validation
- [ ] Integration tests: ✅ Pass
- [ ] Performance benchmarks: ✅ Pass
- [ ] Code coverage: ✅ > 80%
- [ ] Code review: ✅ Approved
```

---

## Complete Integration Flow Example

### End-to-End Use Case: Document Q&A with Full Integration

This example shows how NATS, OTEL, and CODEC work together in a complete use case flow.

#### Scenario: User asks a question about a document

**Step 1: User Query Received**
```python
# API receives query
query = "What is the refund policy?"
tenant_id = "tenant_123"
user_id = "user_456"
```

**Step 2: Query Routing (Unified Query Endpoint)**
```python
# OTEL: Start root trace
with otel_tracer.start_trace("use_case.document_qa") as root_trace:
    root_trace.set_attribute("tenant.id", tenant_id)
    root_trace.set_attribute("user.id", user_id)
    root_trace.set_attribute("query", query)
    
    # CODEC: Encode query request
    query_request = codec.encode({
        "query_id": str(uuid.uuid4()),
        "query": query,
        "tenant_id": tenant_id,
        "user_id": user_id,
        "mode": "auto",
        "timestamp": datetime.now().isoformat(),
        "schema_version": "1.0"
    })
    
    # NATS: Publish to query routing queue
    await nats_client.publish(
        subject=f"ai.api.queries.{tenant_id}",
        payload=query_request
    )
```

**Step 3: RAG Query Processing**
```python
# RAG worker subscribes to query queue
async def rag_worker():
    async def process_query(msg):
        # CODEC: Decode query
        query_data = codec.decode(msg.data)
        
        # OTEL: Start span for RAG processing
        with otel_tracer.start_span("rag.query.process", parent=root_trace) as rag_span:
            rag_span.set_attribute("rag.query.id", query_data["query_id"])
            
            # Step 3a: Generate query embedding
            with otel_tracer.start_span("rag.embedding.generate", parent=rag_span) as embed_span:
                # CODEC: Encode embedding request
                embed_request = codec.encode({
                    "request_id": str(uuid.uuid4()),
                    "text": query_data["query"],
                    "model": "text-embedding-3-small",
                    "tenant_id": tenant_id,
                    "schema_version": "1.0"
                })
                
                # NATS: Request embedding from Gateway
                embed_response = await nats_client.request(
                    subject=f"ai.gateway.embeddings.{tenant_id}",
                    payload=embed_request,
                    timeout=10.0
                )
                
                # CODEC: Decode embedding response
                embedding_data = codec.decode(embed_response.data)
                embed_span.set_attribute("embedding.dimension", len(embedding_data["embedding"]))
            
            # Step 3b: Vector search
            with otel_tracer.start_span("rag.vector.search", parent=rag_span) as search_span:
                results = await vector_db.similarity_search(
                    embedding=embedding_data["embedding"],
                    top_k=5
                )
                search_span.set_attribute("results.count", len(results))
                otel_metrics.increment_counter("rag.searches.executed")
            
            # Step 3c: Build context
            context = build_context(results)
            
            # Step 3d: Generate response via Gateway
            with otel_tracer.start_span("rag.response.generate", parent=rag_span) as gen_span:
                # CODEC: Encode LLM request
                llm_request = codec.encode({
                    "request_id": str(uuid.uuid4()),
                    "prompt": f"Context: {context}\n\nQuestion: {query_data['query']}",
                    "model": "gpt-4",
                    "tenant_id": tenant_id,
                    "schema_version": "1.0"
                })
                
                # NATS: Request LLM generation
                llm_response = await nats_client.request(
                    subject=f"ai.gateway.requests.{tenant_id}",
                    payload=llm_request,
                    timeout=30.0
                )
                
                # CODEC: Decode LLM response
                llm_data = codec.decode(llm_response.data)
                gen_span.set_attribute("llm.tokens", llm_data["tokens"]["total"])
                gen_span.set_attribute("llm.cost", llm_data["cost"])
            
            # Step 3e: Return results
            # CODEC: Encode final response
            response_envelope = codec.encode({
                "query_id": query_data["query_id"],
                "answer": llm_data["response"],
                "sources": [r["document_id"] for r in results],
                "metadata": {
                    "tokens": llm_data["tokens"],
                    "cost": llm_data["cost"],
                    "documents_retrieved": len(results)
                },
                "timestamp": datetime.now().isoformat(),
                "schema_version": "1.0"
            })
            
            # NATS: Publish response
            await nats_client.publish(
                subject=f"ai.rag.results.{tenant_id}",
                payload=response_envelope,
                headers={"query_id": query_data["query_id"]}
            )
            
            # OTEL: Record metrics
            otel_metrics.increment_counter("rag.queries.completed", {
                "tenant_id": tenant_id
            })
```

**Step 4: Response Delivery**
```python
# API subscribes to results
async def wait_for_response(query_id: str):
    # NATS: Subscribe to results
    response = await nats_client.subscribe(
        subject=f"ai.rag.results.{tenant_id}",
        filter={"query_id": query_id},
        timeout=30.0
    )
    
    # CODEC: Decode response
    result_data = codec.decode(response.data)
    
    # OTEL: End trace
    root_trace.set_attribute("response.received", True)
    root_trace.set_attribute("response.tokens", result_data["metadata"]["tokens"])
    
    return result_data
```

### Integration Summary Table

| Component | NATS Topics | OTEL Spans | CODEC Schemas |
|-----------|-------------|------------|---------------|
| **Agent Framework** | `ai.agent.message.*`<br>`ai.agent.tasks.*`<br>`ai.agent.results.*`<br>`ai.agent.memory.*`<br>`ai.agent.tools.*` | `agent.task.execute`<br>`agent.message.send`<br>`agent.memory.update`<br>`agent.tool.execute` | `agent_message`<br>`agent_task`<br>`memory_item` |
| **LiteLLM Gateway** | `ai.gateway.requests.*`<br>`ai.gateway.responses.*`<br>`ai.gateway.rate-limit.*`<br>`ai.gateway.cache.*` | `gateway.generate`<br>`gateway.cache.check`<br>`gateway.provider.call`<br>`gateway.validate` | `llm_request`<br>`llm_response`<br>`embedding_request` |
| **RAG System** | `ai.rag.ingest.*`<br>`ai.rag.queries.*`<br>`ai.rag.results.*`<br>`ai.rag.embeddings.*` | `rag.document.ingest`<br>`rag.query`<br>`rag.vector.search`<br>`rag.response.generate` | `rag_document`<br>`rag_query`<br>`rag_result` |
| **LLMOps** | `ai.llmops.operations.*`<br>`ai.llmops.cost-alerts.*` | `llmops.operation.log`<br>`llmops.cost.track` | `llm_operation` |
| **MLOps** | `ai.mlops.training.*`<br>`ai.mlops.predictions.*` | `mlops.training.job`<br>`mlops.prediction` | `ml_training_job`<br>`ml_prediction` |
| **Prompt Management** | `ai.prompt.templates.*`<br>`ai.prompt.context.*` | `prompt.template.render`<br>`prompt.context.build` | `prompt_template` |

---

## Use Case Integration Flow

### Example: Building a Use Case with NATS, OTEL, CODEC

#### Use Case: AI-Powered Document Q&A System

**Components Used**:
- RAG System (document retrieval)
- LiteLLM Gateway (LLM calls)
- Agent Framework (orchestration)
- NATS (async document processing)
- OTEL (tracing and metrics)
- CODEC (message serialization)

#### Integration Flow

```
1. User Query
   │
   ▼
2. Agent Framework receives query
   │
   ├─→ OTEL: Start trace
   │
   ▼
3. Agent publishes query to NATS queue
   │
   ├─→ CODEC: Serialize query message
   │
   ▼
4. RAG System consumes from NATS
   │
   ├─→ CODEC: Deserialize query
   │
   ├─→ OTEL: Add span for RAG processing
   │
   ▼
5. RAG retrieves documents
   │
   ├─→ OTEL: Record retrieval metrics
   │
   ▼
6. RAG publishes results to NATS
   │
   ├─→ CODEC: Serialize results
   │
   ▼
7. Agent consumes results from NATS
   │
   ├─→ CODEC: Deserialize results
   │
   ├─→ OTEL: Add span for agent processing
   │
   ▼
8. Agent calls LiteLLM Gateway
   │
   ├─→ OTEL: Trace LLM call, record tokens/cost
   │
   ▼
9. Agent formats response
   │
   ├─→ CODEC: Serialize response
   │
   ├─→ OTEL: End trace, record metrics
   │
   ▼
10. Return response to user
```

#### Code Example Structure

```python
# Example: Use case with integrated NATS, OTEL, CODEC

from src.integrations.nats_integration import NATSClient
from src.integrations.otel_integration import OTELTracer
from src.integrations.codec_integration import CodecSerializer
from src.core.rag import RAGSystem
from src.core.agno_agent_framework import Agent

class DocumentQAUseCase:
    def __init__(self):
        # Initialize integrations
        self.nats = NATSClient()
        self.otel = OTELTracer()
        self.codec = CodecSerializer()
        
        # Initialize AI components
        self.rag = RAGSystem()
        self.agent = Agent()
    
    async def process_query(self, query: str):
        # OTEL: Start trace
        with self.otel.start_trace("document_qa_query"):
            # CODEC: Serialize query
            query_msg = self.codec.serialize({"query": query})
            
            # NATS: Publish to queue
            await self.nats.publish("rag.queries", query_msg)
            
            # NATS: Consume results
            result_msg = await self.nats.consume("rag.results")
            
            # CODEC: Deserialize results
            results = self.codec.deserialize(result_msg)
            
            # Agent processes results
            response = await self.agent.process(results)
            
            # OTEL: Record metrics
            self.otel.record_metric("query.latency", latency)
            
            return response
```

---

## Success Criteria

### Integration Success Criteria

#### Functional Criteria
- ✅ All AI components can use NATS for messaging
- ✅ All AI components are traced via OTEL
- ✅ All AI component messages use CODEC serialization
- ✅ Integration tests pass (> 80% coverage)
- ✅ Performance benchmarks meet targets
- ✅ No regressions in existing functionality

#### Quality Criteria
- ✅ Code follows SDK patterns and conventions
- ✅ Comprehensive error handling
- ✅ Well-documented integration code
- ✅ Integration guides are complete
- ✅ Code review approved by other team

#### Performance Criteria
- ✅ NATS messaging latency < 10ms (P95)
- ✅ OTEL overhead < 5% of operation time
- ✅ CODEC serialization < 1ms (P95)
- ✅ No performance regressions

#### Process Criteria
- ✅ Weekly PRs demonstrate incremental progress
- ✅ All PRs pass CI validation
- ✅ Cross-repo reviews are completed
- ✅ Documentation is updated weekly

---

## Next Steps

1. **Week 1**: Set up dependencies and integration structure
2. **Week 2**: Implement NATS integration with Agent Framework
3. **Week 3-4**: Implement OTEL integration
4. **Week 5-6**: Implement CODEC integration
5. **Week 7-8**: End-to-end testing and performance optimization

---

## Appendix

### A. Integration Module Structure

```
src/integrations/
├── __init__.py
├── nats_integration/
│   ├── __init__.py
│   ├── client.py           # NATS client wrapper
│   ├── agent_messaging.py  # Agent messaging integration
│   ├── rag_queue.py        # RAG queue integration
│   └── gateway_queuing.py  # Gateway queuing integration
├── otel_integration/
│   ├── __init__.py
│   ├── bootstrap.py         # OTEL initialization
│   ├── gateway_tracing.py   # Gateway tracing
│   ├── rag_metrics.py       # RAG metrics
│   └── agent_tracing.py     # Agent tracing
└── codec_integration/
    ├── __init__.py
    ├── serializer.py        # Main serializer
    ├── agent_codec.py       # Agent message codec
    ├── rag_codec.py         # RAG payload codec
    └── versioning.py        # Schema versioning
```

### B. Test Structure

```
src/tests/
├── integration_tests/
│   ├── test_nats_integration.py
│   ├── test_otel_integration.py
│   ├── test_codec_integration.py
│   └── test_full_integration.py
└── benchmarks/
    ├── benchmark_nats_performance.py
    ├── benchmark_otel_overhead.py
    └── benchmark_codec_serialization.py
```

### C. Documentation Structure

```
docs/
└── integration_guides/
    ├── nats_integration_guide.md
    ├── otel_integration_guide.md
    └── codec_integration_guide.md
```

---

**Document Version**: 1.0  
**Last Updated**: [Date]  
**Owner**: AI SDK Team  
**Reviewers**: Core SDK Team

