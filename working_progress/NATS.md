# NATS Pub/Sub Service Architecture

## Overview

The SDK uses **NATS (NATS Messaging System)** as the internal communication mechanism for distributed, scalable, and reliable messaging between components. NATS provides publish/subscribe (pub/sub), request/reply, and queue group patterns that enable loose coupling and event-driven communication across all SDK components.

## Purpose

NATS serves as the backbone for:
- **Agent-to-Agent Communication**: Enables distributed agent coordination
- **Component Event Broadcasting**: Allows components to notify each other of state changes
- **Cache Invalidation**: Efficient cache synchronization across instances
- **Async Task Processing**: Handles long-running operations asynchronously
- **System Monitoring**: Centralized event collection for observability

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    NATS Server                             │
│  (Central Message Broker)                                  │
│  Default: nats://localhost:4222                           │
└─────────────────────────────────────────────────────────────┘
         ▲              ▲              ▲              ▲
         │              │              │              │
    ┌────┴────┐    ┌────┴────┐   ┌────┴────┐   ┌────┴────┐
    │  PUB    │    │  PUB    │   │  SUB    │   │  SUB    │
    │         │    │         │   │         │   │         │
┌───▼─────────▼┐ ┌─▼─────────▼┐ ┌─▼─────────▼┐ ┌─▼─────────▼┐
│   Agent     │ │    RAG     │ │   Cache    │ │ Observability│
│  Framework  │ │  System    │ │ Mechanism  │ │             │
│             │ │            │ │            │ │             │
│ PUBLISHES:  │ │ PUBLISHES: │ │ PUBLISHES: │ │ SUBSCRIBES: │
│ - agent.*   │ │ - rag.*    │ │ - cache.*  │ │ - *.*       │
│             │ │            │ │            │ │ (all events)│
│ SUBSCRIBES: │ │ SUBSCRIBES:│ │ SUBSCRIBES:│ │             │
│ - agent.*   │ │ - rag.*    │ │ - cache.*  │ │ PUBLISHES:  │
│             │ │            │ │            │ │ - alerts    │
└─────────────┘ └────────────┘ └────────────┘ └─────────────┘
```

## Component Publisher/Subscriber Mapping

### 1. Agent Framework Component

**PUBLISHES (PUB):**

| Subject | Description | When | Payload |
|---------|-------------|------|---------|
| `agent.{agent_id}.inbox` | Direct messages to specific agents | Agent A sends message to Agent B | `{from_agent, to_agent, content, message_type, timestamp}` |
| `agent.broadcast` | Broadcast messages to all agents | `AgentManager.broadcast_message()` is called | `{from_agent, content, message_type}` |
| `agent.{agent_id}.status` | Agent status updates | Agent status changes (idle, running, error) | `{agent_id, status, timestamp}` |
| `agent.{agent_id}.task.completed` | Task completion notifications | Agent finishes executing a task | `{agent_id, task_id, result, timestamp}` |
| `agent.{agent_id}.task.failed` | Task failure notifications | Agent task execution fails | `{agent_id, task_id, error, timestamp}` |

**SUBSCRIBES (SUB):**

| Subject | Description | Action |
|---------|-------------|--------|
| `agent.{agent_id}.inbox` | Receives direct messages | Process message and update agent state |
| `agent.broadcast` | Receives broadcast messages | All agents receive and process |
| `agent.{agent_id}.tasks` | Receives task assignments | Add task to agent's task queue |

---

### 2. RAG System Component

**PUBLISHES (PUB):**

| Subject | Description | When | Payload |
|---------|-------------|------|---------|
| `rag.documents.ingested` | Document ingestion events | New document is added to knowledge base | `{document_id, title, chunk_count, timestamp}` |
| `rag.documents.updated` | Document update events | Existing document is updated | `{document_id, action: "updated", timestamp}` |
| `rag.documents.deleted` | Document deletion events | Document is removed | `{document_id, action: "deleted", timestamp}` |
| `rag.embeddings.generated` | Embedding generation events | New embeddings are created | `{document_id, embedding_count, timestamp}` |
| `rag.cache.invalidate` | Cache invalidation requests | Documents change, cache needs clearing | `{pattern: "rag.*", reason: "document_updated"}` |
| `rag.query.completed` | Query completion events | RAG query finishes processing | `{query_id, document_count, response_time}` |

**SUBSCRIBES (SUB):**

| Subject | Description | Action |
|---------|-------------|--------|
| `rag.documents.ingest.request` | Receives document ingestion requests | Process and ingest new document |
| `rag.cache.invalidate` | Receives cache invalidation events | Clear RAG-related cache entries |

---

### 3. Cache Mechanism Component

**PUBLISHES (PUB):**

| Subject | Description | When | Payload |
|---------|-------------|------|---------|
| `cache.hit` | Cache hit events (for monitoring) | Cache lookup succeeds | `{key, ttl_remaining, backend, timestamp}` |
| `cache.miss` | Cache miss events (for monitoring) | Cache lookup fails | `{key, backend, timestamp}` |
| `cache.invalidated` | Cache invalidation confirmations | Cache entry is invalidated | `{key, pattern, reason, timestamp}` |

**SUBSCRIBES (SUB):**

| Subject | Description | Action |
|---------|-------------|--------|
| `rag.cache.invalidate` | Receives RAG cache invalidation requests | Invalidate matching cache entries |
| `component.cache.invalidate` | Receives general cache invalidation requests | Invalidate cache based on pattern |
| `agent.cache.invalidate` | Receives agent-related cache invalidation | Clear agent-specific cache entries |
| `gateway.cache.invalidate` | Receives gateway cache invalidation requests | Clear LLM response cache entries |

---

### 4. API Backend Services Component

**PUBLISHES (PUB):**

| Subject | Description | When | Payload |
|---------|-------------|------|---------|
| `api.tasks.{task_id}` | Async task results | Long-running task completes | `{task_id, status, result, error, timestamp}` |
| `api.requests.received` | Request received events (for monitoring) | API receives incoming request | `{endpoint, method, request_id, timestamp}` |
| `api.responses.sent` | Response sent events (for monitoring) | API sends response | `{endpoint, status_code, response_time, timestamp}` |

**SUBSCRIBES (SUB):**

| Subject | Description | Action |
|---------|-------------|--------|
| `api.tasks.{task_id}` | Receives async task results | Return result to client (if waiting) |
| `agent.{agent_id}.task.completed` | Receives agent task completion events | Update API response for agent tasks |
| `rag.query.completed` | Receives RAG query completion events | Return RAG query results to client |

---

### 5. PostgreSQL Database Component

**PUBLISHES (PUB):**

| Subject | Description | When | Payload |
|---------|-------------|------|---------|
| `database.connection.status` | Database connection status changes | Connection pool status changes | `{status: "connected\|disconnected", pool_size, timestamp}` |
| `database.query.slow` | Slow query alerts | Query exceeds threshold | `{query, duration, threshold, timestamp}` |
| `database.transaction.committed` | Transaction commit events (optional, for audit) | Important transactions complete | `{table, operation, record_count, timestamp}` |

**SUBSCRIBES (SUB):**

| Subject | Description | Action |
|---------|-------------|--------|
| `database.health.check` | Receives health check requests | Perform health check and respond |

---

### 6. LiteLLM Gateway Component

**PUBLISHES (PUB):**

| Subject | Description | When | Payload |
|---------|-------------|------|---------|
| `gateway.llm.request` | LLM request events (for monitoring) | LLM API call is made | `{provider, model, prompt_length, request_id, timestamp}` |
| `gateway.llm.response` | LLM response events (for monitoring) | LLM API call completes | `{provider, model, tokens_used, latency, cost, timestamp}` |
| `gateway.rate_limit.warning` | Rate limit warnings | Approaching rate limits | `{provider, model, remaining_requests, timestamp}` |
| `gateway.rate_limit.exceeded` | Rate limit exceeded events | Rate limit is hit | `{provider, model, retry_after, timestamp}` |

**SUBSCRIBES (SUB):**

| Subject | Description | Action |
|---------|-------------|--------|
| `gateway.cache.invalidate` | Receives cache invalidation for LLM responses | Clear cached LLM responses |

---

### 7. Evaluation & Observability Component

**PUBLISHES (PUB):**

| Subject | Description | When | Payload |
|---------|-------------|------|---------|
| `observability.alerts` | System alerts | Thresholds exceeded, errors detected | `{alert_type, severity, component, message, timestamp}` |
| `observability.metrics.summary` | Periodic metrics summaries | Scheduled metrics aggregation | `{component, metrics, timestamp}` |

**SUBSCRIBES (SUB):**

| Subject Pattern | Description | Action |
|----------------|-------------|--------|
| `agent.*` | Receives ALL agent events | Log, trace, and collect metrics |
| `rag.*` | Receives ALL RAG events | Log, trace, and collect metrics |
| `cache.*` | Receives ALL cache events | Log, trace, and collect metrics |
| `api.*` | Receives ALL API events | Log, trace, and collect metrics |
| `gateway.*` | Receives ALL gateway events | Log, trace, and collect metrics |
| `database.*` | Receives ALL database events | Log, trace, and collect metrics |
| `component.*` | Receives ALL component events | Log, trace, and collect metrics |

---

## Subject Naming Convention

### Pattern Structure

```
{component}.{entity}.{action}
```

### Examples

- `agent.agent-123.inbox` - Direct message inbox for agent-123
- `agent.broadcast` - Broadcast to all agents
- `rag.documents.ingested` - Document ingestion event
- `cache.invalidated` - Cache invalidation confirmation
- `api.tasks.task-456` - Async task result for task-456
- `gateway.llm.request` - LLM request event
- `database.connection.status` - Database connection status

### Wildcard Patterns

- `agent.*` - All agent-related events
- `rag.*` - All RAG-related events
- `cache.*` - All cache-related events
- `*.*` - All events (used by Observability)

---

## Communication Flow Examples

### Flow 1: Agent-to-Agent Communication

```
Agent A (PUB) 
    ↓
    Publishes to: agent.agent-b.inbox
    ↓
NATS Server
    ↓
Agent B (SUB)
    ↓
    Receives and processes message
```

**Reverse Communication:**
```
Agent B (PUB) 
    ↓
    Publishes to: agent.agent-a.inbox
    ↓
NATS Server
    ↓
Agent A (SUB)
    ↓
    Receives and processes message
```

---

### Flow 2: RAG Document Update Triggers Cache Invalidation

```
RAG System (PUB)
    ↓
    Publishes: rag.documents.updated
    Payload: {document_id: "doc-123", action: "updated"}
    ↓
NATS Server
    ↓
    ├─→ Cache Mechanism (SUB)
    │   └─→ Receives event
    │       └─→ Invalidates matching cache entries
    │           └─→ Publishes: cache.invalidated
    │
    └─→ Observability (SUB)
        └─→ Receives event
            └─→ Logs and tracks metrics
```

---

### Flow 3: API Async Task Processing

```
API Backend (PUB)
    ↓
    Publishes: api.tasks.task-123
    Payload: {task_id: "task-123", type: "agent_task", params: {...}}
    ↓
NATS Server
    ↓
Agent Framework (SUB)
    ↓
    Receives task assignment
    ↓
    Executes task
    ↓
Agent Framework (PUB)
    ↓
    Publishes: agent.agent-123.task.completed
    Payload: {task_id: "task-123", result: {...}}
    ↓
NATS Server
    ↓
API Backend (SUB)
    ↓
    Receives completion
    ↓
    Returns result to client
```

---

### Flow 4: Observability Monitoring All Events

```
All Components (PUB)
    ↓
    Publish various events:
    - agent.*
    - rag.*
    - cache.*
    - api.*
    - gateway.*
    - database.*
    ↓
NATS Server
    ↓
Observability (SUB)
    ↓
    Subscribes to: *.* (all events)
    ↓
    Collects, logs, traces, and monitors
    ↓
    Publishes alerts if thresholds exceeded:
    observability.alerts
```

---

### Flow 5: Cache Hit/Miss Monitoring

```
Cache Mechanism
    ↓
    Cache lookup occurs
    ↓
    ├─→ Cache Hit (PUB)
    │   └─→ Publishes: cache.hit
    │       Payload: {key: "query-123", ttl_remaining: 300}
    │
    └─→ Cache Miss (PUB)
        └─→ Publishes: cache.miss
            Payload: {key: "query-123"}
    ↓
NATS Server
    ↓
Observability (SUB)
    ↓
    Receives event
    ↓
    Updates cache metrics (hit rate, miss rate)
```

---

## NATS Client Implementation

### Location

The NATS client is implemented in the **Connectivity Component**:

```
connectivity_clients/
├── client.py (existing)
├── nats_client.py (NATS implementation)
└── __init__.py
```

### Client Structure

```python
class NATSClient:
    """
    NATS pub/sub client for internal SDK communication.
    
    Supports:
    - Publish/Subscribe (pub/sub)
    - Request/Reply
    - Queue Groups (load balancing)
    """
    
    async def connect(self) -> None:
        """Connect to NATS server"""
        
    async def publish(self, subject: str, data: bytes) -> None:
        """Publish message to subject"""
        
    async def subscribe(
        self, 
        subject: str, 
        callback: Callable,
        queue_group: Optional[str] = None
    ) -> str:
        """Subscribe to subject with optional queue group"""
        
    async def request(
        self, 
        subject: str, 
        data: bytes, 
        timeout: float = 5.0
    ) -> bytes:
        """Request/Reply pattern"""
        
    async def close(self) -> None:
        """Close connection and cleanup"""
```

### Integration with ClientManager

```python
# Updated ClientManager in connectivity_clients/client.py

class ClientType(str, Enum):
    HTTP = "http"
    WEBSOCKET = "websocket"
    DATABASE = "database"
    MESSAGE_QUEUE = "message_queue"
    NATS = "nats"  # NEW

class ClientManager:
    def register_client(self, client_id: str, config: ClientConfig):
        # ... existing code ...
        
        if config.client_type == ClientType.NATS:
            client = NATSClient(config)
            await client.connect()
            self._clients[client_id] = client
```

---

## Configuration

### NATS Server Configuration

```python
# NATS Configuration
nats_config = ClientConfig(
    client_type=ClientType.NATS,
    base_url="nats://localhost:4222",  # NATS server URL
    timeout=30.0,
    retries=3,
    metadata={
        "servers": ["nats://localhost:4222"],
        "max_reconnect_attempts": 10,
        "reconnect_time_wait": 2.0,
        "ping_interval": 20,
        "max_outstanding_pings": 2
    }
)
```

### Environment Variables

```bash
# NATS Server Configuration
NATS_URL=nats://localhost:4222
NATS_MAX_RECONNECT_ATTEMPTS=10
NATS_RECONNECT_TIME_WAIT=2.0
NATS_PING_INTERVAL=20
NATS_MAX_OUTSTANDING_PINGS=2
```

---

## Usage Examples

### Example 1: Agent Sends Message to Another Agent

```python
# Agent A sends message to Agent B
await agent_a.nats_client.publish(
    subject=f"agent.{agent_b_id}.inbox",
    data=json.dumps({
        "from_agent": agent_a.agent_id,
        "to_agent": agent_b_id,
        "content": "Hello from Agent A",
        "message_type": "task",
        "timestamp": datetime.now().isoformat()
    }).encode()
)

# Agent B receives message
async def handle_message(msg):
    data = json.loads(msg.data.decode())
    agent_b.process_message(data)

await agent_b.nats_client.subscribe(
    subject=f"agent.{agent_b_id}.inbox",
    callback=handle_message
)
```

### Example 2: RAG System Publishes Document Update

```python
# RAG System publishes document update
await rag_system.nats_client.publish(
    subject="rag.documents.updated",
    data=json.dumps({
        "document_id": "doc-123",
        "action": "updated",
        "timestamp": datetime.now().isoformat()
    }).encode()
)

# Cache Mechanism subscribes and invalidates cache
async def invalidate_cache(msg):
    data = json.loads(msg.data.decode())
    if data["action"] == "updated":
        cache.invalidate_pattern("rag.*")

await cache.nats_client.subscribe(
    subject="rag.documents.updated",
    callback=invalidate_cache
)
```

### Example 3: Request/Reply Pattern

```python
# API Backend requests agent status
response = await api_backend.nats_client.request(
    subject=f"agent.{agent_id}.status",
    data=json.dumps({"request_id": "req-1"}).encode(),
    timeout=5.0
)

# Agent replies with status
async def handle_status_request(msg):
    status = agent.get_status()
    await agent.nats_client.publish(
        subject=msg.reply,
        data=json.dumps(status).encode()
    )

await agent.nats_client.subscribe(
    subject=f"agent.{agent_id}.status",
    callback=handle_status_request
)
```

### Example 4: Queue Groups (Load Balancing)

```python
# Multiple API instances subscribe to same queue group
# Only one instance processes each message
async def process_task(msg):
    task = json.loads(msg.data.decode())
    # Process task...
    pass

# All API instances subscribe with same queue group
await api_instance_1.nats_client.subscribe(
    subject="api.tasks.process",
    callback=process_task,
    queue_group="api-workers"  # Load balancing
)

await api_instance_2.nats_client.subscribe(
    subject="api.tasks.process",
    callback=process_task,
    queue_group="api-workers"  # Same queue group
)
```

---

## Benefits

### 1. Distributed Communication
- Agents and components can run across multiple services/instances
- No single point of failure for communication

### 2. Scalability
- Horizontal scaling of agents and components
- Queue groups enable load balancing

### 3. Reliability
- NATS provides message delivery guarantees
- Automatic reconnection and retry mechanisms

### 4. Performance
- Lightweight, high-throughput messaging
- Low latency pub/sub operations

### 5. Loose Coupling
- Components communicate through events, not direct calls
- Easy to add/remove components without breaking others

### 6. Observability
- Centralized event collection
- Easy to monitor all component interactions

---

## Summary Table

| Component | Primary Role | Publishes | Subscribes |
|-----------|-------------|-----------|------------|
| **Agent Framework** | Both | Agent messages, status, tasks | Agent inbox, broadcasts, tasks |
| **RAG System** | Both | Document events, cache invalidation | Document requests, cache invalidation |
| **Cache Mechanism** | Both | Cache hit/miss, invalidation confirmations | Cache invalidation requests |
| **API Backend** | Both | Task results, request/response events | Task results, component events |
| **PostgreSQL Database** | PUB | Connection status, slow queries | Health check requests |
| **LiteLLM Gateway** | PUB | LLM requests/responses, rate limits | Cache invalidation |
| **Observability** | Both | Alerts, metrics summaries | ALL events (monitoring) |

---

## Best Practices

1. **Subject Naming**: Follow the `{component}.{entity}.{action}` pattern consistently
2. **Error Handling**: Always handle connection failures and message processing errors
3. **Message Serialization**: Use JSON for structured data, ensure proper encoding/decoding
4. **Queue Groups**: Use queue groups for load balancing when multiple instances process same messages
5. **Monitoring**: Subscribe to relevant events for observability and debugging
6. **Resource Cleanup**: Always close subscriptions and connections when done
7. **Idempotency**: Design message handlers to be idempotent when possible
8. **Timeouts**: Set appropriate timeouts for request/reply patterns

---

## Dependencies

- **nats-py**: Python NATS client library
- **asyncio**: For async operations
- **json**: For message serialization
- **connectivity_clients**: Part of the Connectivity component

---

## Integration Points

1. **Connectivity Component**: NATS client implementation
2. **Agent Framework**: Agent-to-agent communication
3. **RAG System**: Document event broadcasting
4. **Cache Mechanism**: Cache invalidation events
5. **API Backend**: Async task processing
6. **Observability**: Event collection and monitoring

---

## Future Enhancements

- **NATS JetStream**: For persistent messaging and stream processing
- **NATS Key-Value Store**: For distributed configuration
- **NATS Object Store**: For large object storage
- **Message Encryption**: End-to-end encryption for sensitive data
- **Message Compression**: Compression for large payloads

