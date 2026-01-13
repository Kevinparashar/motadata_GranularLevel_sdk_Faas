# NATS Integration - Comprehensive Component Explanation

## Overview

The NATS Integration component provides asynchronous messaging capabilities for AI SDK components, enabling decoupled communication, task distribution, and event-driven workflows through the NATS messaging system from the Core SDK.

## Table of Contents

1. [NATS Integration Overview](#nats-integration-overview)
2. [Integration Points](#integration-points)
3. [Pub/Sub Topics and Channels](#pubsub-topics-and-channels)
4. [Agent Framework Integration](#agent-framework-integration)
5. [LiteLLM Gateway Integration](#litellm-gateway-integration)
6. [RAG System Integration](#rag-system-integration)
7. [LLMOps/MLOps Integration](#llmopsmlops-integration)
8. [Error Handling](#error-handling)
9. [Performance Considerations](#performance-considerations)
10. [Workflow](#workflow)
11. [Customization](#customization)

---

## NATS Integration Overview

### Purpose

NATS integration enables:
- **Asynchronous Communication**: Decouple AI components for better scalability
- **Task Distribution**: Distribute work across multiple workers
- **Event-Driven Workflows**: React to events and trigger actions
- **Load Balancing**: Queue groups for automatic load distribution
- **Reliability**: Message persistence and delivery guarantees

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
│         │     NATS Integration Layer            │             │
│         │  ┌──────────────────────────────┐    │             │
│         │  │  NATS Client Wrapper         │    │             │
│         │  │  (from Core SDK)             │    │             │
│         │  └──────────────────────────────┘    │             │
│         └─────────────────┬──────────────────┘             │
│                           │                                  │
└───────────────────────────┼──────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    NATS Server                                │
│  (Message Broker - Core SDK Infrastructure)                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Integration Points

### Component Integration Matrix

| Component | NATS Usage | Primary Topics | Purpose |
|-----------|------------|----------------|---------|
| **Agent Framework** | High | `ai.agent.message.*`<br>`ai.agent.tasks.*`<br>`ai.agent.memory.*` | Agent communication, task distribution, memory updates |
| **LiteLLM Gateway** | High | `ai.gateway.requests.*`<br>`ai.gateway.responses.*` | Request queuing, response delivery |
| **RAG System** | High | `ai.rag.ingest.*`<br>`ai.rag.queries.*`<br>`ai.rag.results.*` | Document ingestion, query processing |
| **LLMOps** | Medium | `ai.llmops.operations.*`<br>`ai.llmops.cost-alerts.*` | Operation logging, cost alerts |
| **MLOps** | Medium | `ai.mlops.training.*`<br>`ai.mlops.predictions.*` | Training jobs, prediction requests |

---

## Pub/Sub Topics and Channels

### Topic Naming Convention

**Format**: `ai.{component}.{operation}.{tenant_id}`

- `ai` - Prefix for AI SDK topics
- `{component}` - Component name (agent, gateway, rag, etc.)
- `{operation}` - Operation type (message, tasks, queries, etc.)
- `{tenant_id}` - Tenant identifier for multi-tenancy

### Agent Framework Topics

#### Agent-to-Agent Messaging
- **Topic**: `ai.agent.message.{tenant_id}`
- **Publisher**: Source Agent
- **Subscriber**: Target Agent(s)
- **Queue Group**: `agent.{agent_id}` (for load balancing)
- **Purpose**: Direct agent-to-agent communication

#### Task Distribution
- **Topic**: `ai.agent.tasks.{tenant_id}`
- **Publisher**: Agent Manager
- **Subscriber**: Worker Agents
- **Queue Group**: `agent.workers` (for load balancing)
- **Purpose**: Distribute tasks to available agents

#### Task Results
- **Topic**: `ai.agent.results.{tenant_id}`
- **Publisher**: Worker Agent
- **Subscriber**: Agent Manager
- **Purpose**: Return task execution results

#### Memory Updates
- **Topic**: `ai.agent.memory.{tenant_id}`
- **Publisher**: Agent
- **Subscriber**: Memory Service
- **Purpose**: Async memory persistence

#### Tool Execution
- **Topic**: `ai.agent.tools.{tenant_id}`
- **Publisher**: Agent
- **Subscriber**: Tool Executor
- **Purpose**: Execute tools asynchronously

### LiteLLM Gateway Topics

#### LLM Request Queue
- **Topic**: `ai.gateway.requests.{tenant_id}`
- **Publisher**: API/Components
- **Subscriber**: Gateway Workers
- **Queue Group**: `gateway.workers` (for load balancing)
- **Purpose**: Queue LLM requests for processing

#### LLM Response Queue
- **Topic**: `ai.gateway.responses.{tenant_id}`
- **Publisher**: Gateway Workers
- **Subscriber**: Requesters
- **Purpose**: Return LLM responses

#### Rate Limit Events
- **Topic**: `ai.gateway.rate-limit.{tenant_id}`
- **Publisher**: Rate Limiter
- **Subscriber**: Monitoring
- **Purpose**: Rate limit events and violations

#### Cache Invalidation
- **Topic**: `ai.gateway.cache.invalidate.{tenant_id}`
- **Publisher**: Gateway
- **Subscriber**: Cache Service
- **Purpose**: Invalidate cached responses

### RAG System Topics

#### Document Ingestion Queue
- **Topic**: `ai.rag.ingest.{tenant_id}`
- **Publisher**: API/Components
- **Subscriber**: RAG Workers
- **Queue Group**: `rag.workers` (for load balancing)
- **Purpose**: Queue documents for processing

#### Query Queue
- **Topic**: `ai.rag.queries.{tenant_id}`
- **Publisher**: API/Components
- **Subscriber**: RAG Workers
- **Queue Group**: `rag.workers` (for load balancing)
- **Purpose**: Queue RAG queries

#### Query Results
- **Topic**: `ai.rag.results.{tenant_id}`
- **Publisher**: RAG Workers
- **Subscriber**: Requesters
- **Purpose**: Return query results

#### Embedding Generation
- **Topic**: `ai.rag.embeddings.{tenant_id}`
- **Publisher**: RAG Workers
- **Subscriber**: Gateway
- **Purpose**: Request embeddings

---

## Agent Framework Integration

### Agent-to-Agent Messaging

```python
from src.integrations.nats_integration import NATSClient
from src.integrations.codec_integration import CodecSerializer

class Agent:
    def __init__(self, agent_id: str, tenant_id: str):
        self.agent_id = agent_id
        self.tenant_id = tenant_id
        self.nats_client = NATSClient()
        self.codec = CodecSerializer()
    
    async def send_message(self, target_agent_id: str, content: str):
        """Send message to another agent via NATS."""
        # Encode message
        message_envelope = self.codec.encode({
            "message_id": str(uuid.uuid4()),
            "source_agent_id": self.agent_id,
            "target_agent_id": target_agent_id,
            "content": content,
            "message_type": "text",
            "timestamp": datetime.now().isoformat(),
            "schema_version": "1.0"
        })
        
        # Publish to NATS
        await self.nats_client.publish(
            subject=f"ai.agent.message.{self.tenant_id}",
            payload=message_envelope,
            headers={
                "target_agent_id": target_agent_id,
                "source_agent_id": self.agent_id
            }
        )
    
    async def setup_message_subscription(self):
        """Subscribe to receive messages."""
        async def message_handler(msg):
            # Decode message
            message_data = self.codec.decode(msg.data)
            
            # Process if message is for this agent
            if message_data["target_agent_id"] == self.agent_id:
                await self.handle_message(message_data)
        
        # Subscribe with queue group for load balancing
        await self.nats_client.subscribe(
            subject=f"ai.agent.message.{self.tenant_id}",
            callback=message_handler,
            queue=f"agent.{self.agent_id}"
        )
```

### Task Distribution

```python
async def distribute_task(self, task: AgentTask):
    """Distribute task to worker agents via NATS."""
    # Encode task
    task_envelope = self.codec.encode({
        "task_id": task.task_id,
        "agent_id": task.agent_id,
        "task_type": task.task_type,
        "parameters": task.parameters,
        "priority": task.priority,
        "timestamp": datetime.now().isoformat(),
        "schema_version": "1.0"
    })
    
    # Publish to task distribution queue
    await self.nats_client.publish(
        subject=f"ai.agent.tasks.{self.tenant_id}",
        payload=task_envelope
    )
```

---

## LiteLLM Gateway Integration

### Request Queuing

```python
async def generate_async(self, prompt: str, model: str, tenant_id: str):
    """Generate text via NATS queuing."""
    request_id = str(uuid.uuid4())
    
    # Encode request
    request_envelope = self.codec.encode({
        "request_id": request_id,
        "prompt": prompt,
        "model": model,
        "tenant_id": tenant_id,
        "timestamp": datetime.now().isoformat(),
        "schema_version": "1.0"
    })
    
    # Publish to request queue
    await self.nats_client.publish(
        subject=f"ai.gateway.requests.{tenant_id}",
        payload=request_envelope,
        headers={
            "request_id": request_id,
            "model": model,
            "priority": "normal"
        }
    )
    
    # Request response
    response = await self.nats_client.request(
        subject=f"ai.gateway.responses.{tenant_id}",
        payload=request_envelope,
        timeout=60.0
    )
    
    # Decode response
    response_data = self.codec.decode(response.data)
    return response_data
```

### Gateway Worker

```python
async def gateway_worker(tenant_id: str):
    """Gateway worker processing requests from queue."""
    async def process_request(msg):
        # Decode request
        request_data = codec.decode(msg.data)
        
        # Process LLM request
        response = await make_llm_call(request_data)
        
        # Encode response
        response_envelope = codec.encode({
            "request_id": request_data["request_id"],
            "response": response.text,
            "tokens": response.total_tokens,
            "cost": response.cost,
            "schema_version": "1.0"
        })
        
        # Publish response
        await nats_client.publish(
            subject=f"ai.gateway.responses.{tenant_id}",
            payload=response_envelope,
            headers={"request_id": request_data["request_id"]}
        )
    
    # Subscribe to request queue with queue group
    await nats_client.subscribe(
        subject=f"ai.gateway.requests.{tenant_id}",
        callback=process_request,
        queue="gateway.workers"  # Load balancing
    )
```

---

## RAG System Integration

### Document Ingestion Queue

```python
async def ingest_document_async(self, document: Document, tenant_id: str):
    """Ingest document via NATS queue."""
    # Encode document
    document_envelope = self.codec.encode({
        "document_id": document.document_id,
        "content": document.content,
        "metadata": document.metadata,
        "tenant_id": tenant_id,
        "timestamp": datetime.now().isoformat(),
        "schema_version": "1.0"
    })
    
    # Publish to ingestion queue
    await self.nats_client.publish(
        subject=f"ai.rag.ingest.{tenant_id}",
        payload=document_envelope
    )
    
    # Wait for processing status
    status = await self.nats_client.request(
        subject=f"ai.rag.status.{tenant_id}",
        payload=document_envelope,
        timeout=300.0
    )
    
    return status
```

### Query Processing Queue

```python
async def query_async(self, query: str, tenant_id: str):
    """Process query via NATS queue."""
    query_id = str(uuid.uuid4())
    
    # Encode query
    query_envelope = self.codec.encode({
        "query_id": query_id,
        "query": query,
        "tenant_id": tenant_id,
        "timestamp": datetime.now().isoformat(),
        "schema_version": "1.0"
    })
    
    # Publish to query queue
    await self.nats_client.publish(
        subject=f"ai.rag.queries.{tenant_id}",
        payload=query_envelope
    )
    
    # Request results
    result_envelope = await self.nats_client.request(
        subject=f"ai.rag.results.{tenant_id}",
        payload=query_envelope,
        timeout=30.0
    )
    
    # Decode results
    results = self.codec.decode(result_envelope.data)
    return results
```

---

## LLMOps/MLOps Integration

### Operation Logging

```python
async def log_operation(self, operation: LLMOperation):
    """Log LLM operation via NATS."""
    # Encode operation
    operation_envelope = self.codec.encode({
        "operation_id": operation.operation_id,
        "operation_type": operation.operation_type,
        "model": operation.model,
        "tokens": {
            "prompt": operation.prompt_tokens,
            "completion": operation.completion_tokens,
            "total": operation.total_tokens
        },
        "cost": operation.cost_usd,
        "latency_ms": operation.latency_ms,
        "status": operation.status,
        "tenant_id": operation.tenant_id,
        "timestamp": operation.timestamp.isoformat(),
        "schema_version": "1.0"
    })
    
    # Publish to operations queue
    await self.nats_client.publish(
        subject=f"ai.llmops.operations.{operation.tenant_id}",
        payload=operation_envelope
    )
```

---

## Error Handling

### Connection Failures

```python
async def publish_with_retry(self, subject: str, payload: bytes, max_retries: int = 3):
    """Publish with retry logic for connection failures."""
    for attempt in range(max_retries):
        try:
            await self.nats_client.publish(subject=subject, payload=payload)
            return
        except ConnectionError as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### Message Timeouts

```python
async def request_with_timeout(self, subject: str, payload: bytes, timeout: float):
    """Request with timeout handling."""
    try:
        response = await asyncio.wait_for(
            self.nats_client.request(subject=subject, payload=payload),
            timeout=timeout
        )
        return response
    except asyncio.TimeoutError:
        logger.warning(f"Request timeout for subject: {subject}")
        raise
```

### Queue Full Handling

```python
async def publish_with_backpressure(self, subject: str, payload: bytes):
    """Publish with backpressure handling."""
    try:
        await self.nats_client.publish(subject=subject, payload=payload)
    except QueueFullError:
        # Wait and retry
        await asyncio.sleep(0.1)
        await self.nats_client.publish(subject=subject, payload=payload)
```

---

## Performance Considerations

### Latency Targets

| Operation | Target P95 Latency |
|-----------|-------------------|
| Agent messaging | < 10ms |
| Gateway queuing | < 5ms |
| RAG query queuing | < 5ms |
| Document ingestion queuing | < 10ms |

### Throughput Targets

| Operation | Target Throughput |
|-----------|------------------|
| RAG queue | > 100 msg/sec |
| Gateway queue | > 50 msg/sec |
| Agent messaging | > 200 msg/sec |

### Optimization Strategies

1. **Queue Groups**: Use queue groups for automatic load balancing
2. **Batch Publishing**: Batch multiple messages when possible
3. **Connection Pooling**: Reuse NATS connections
4. **Message Compression**: Compress large payloads
5. **Async Processing**: Use async/await for non-blocking operations

---

## Workflow

### Complete Message Flow

```
1. Component creates message
   │
   ├─→ CODEC: Encode message
   │
   ▼
2. NATS: Publish to topic
   │
   ├─→ Queue Group: Distribute to workers
   │
   ▼
3. Worker receives message
   │
   ├─→ CODEC: Decode message
   │
   ├─→ OTEL: Start trace
   │
   ▼
4. Process message
   │
   ├─→ OTEL: Record metrics
   │
   ▼
5. Create response
   │
   ├─→ CODEC: Encode response
   │
   ├─→ OTEL: End trace
   │
   ▼
6. NATS: Publish response
   │
   ▼
7. Original requester receives response
   │
   ├─→ CODEC: Decode response
   │
   ▼
8. Return to caller
```

---

## Customization

### Custom Topic Naming

```python
# Custom topic naming pattern
def get_topic(component: str, operation: str, tenant_id: str) -> str:
    return f"custom.{component}.{operation}.{tenant_id}"
```

### Custom Queue Groups

```python
# Custom queue group for specific workers
await nats_client.subscribe(
    subject="ai.agent.tasks.tenant_123",
    callback=handler,
    queue="custom.worker.group"
)
```

### Message Headers

```python
# Add custom headers
await nats_client.publish(
    subject="ai.agent.message.tenant_123",
    payload=encoded,
    headers={
        "priority": "high",
        "retry_count": "0",
        "custom_header": "value"
    }
)
```

---

## Best Practices

1. **Always use queue groups** for load balancing
2. **Set appropriate timeouts** for request/response patterns
3. **Handle connection failures** with retry logic
4. **Use message headers** for routing and metadata
5. **Monitor queue depths** to prevent backpressure
6. **Implement circuit breakers** for unhealthy NATS connections
7. **Use CODEC for all messages** to ensure schema validation
8. **Integrate OTEL** for observability of NATS operations

---

## See Also

- [CORE_COMPONENTS_INTEGRATION_STORY.md](../../CORE_COMPONENTS_INTEGRATION_STORY.md)
- [NATS Integration Guide](../../docs/integration_guides/nats_integration_guide.md)
- Core SDK NATS wrapper documentation

