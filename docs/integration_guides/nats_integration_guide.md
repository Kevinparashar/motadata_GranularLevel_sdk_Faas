# NATS Integration Guide

## Overview

This guide explains how to integrate NATS messaging with AI SDK components.

## Prerequisites

- Core SDK NATS wrapper (versioned dependency)
- NATS server running and accessible
- Proper authentication and connection configuration

## Integration Points

### Agent Framework

#### Agent-to-Agent Messaging

**Topic**: `ai.agent.message.{tenant_id}`

```python
# Publishing agent message
await nats_client.publish(
    subject=f"ai.agent.message.{tenant_id}",
    payload=encoded_message,
    headers={
        "target_agent_id": target_agent_id,
        "source_agent_id": source_agent_id
    }
)

# Subscribing to agent messages
await nats_client.subscribe(
    subject=f"ai.agent.message.{tenant_id}",
    callback=message_handler,
    queue=f"agent.{agent_id}"
)
```

#### Task Distribution

**Topic**: `ai.agent.tasks.{tenant_id}`

```python
# Publishing task
await nats_client.publish(
    subject=f"ai.agent.tasks.{tenant_id}",
    payload=encoded_task
)

# Subscribing to tasks
await nats_client.subscribe(
    subject=f"ai.agent.tasks.{tenant_id}",
    callback=task_handler,
    queue="agent.workers"
)
```

### LiteLLM Gateway

#### Request Queuing

**Topic**: `ai.gateway.requests.{tenant_id}`

```python
# Publishing LLM request
await nats_client.publish(
    subject=f"ai.gateway.requests.{tenant_id}",
    payload=encoded_request,
    headers={
        "request_id": request_id,
        "model": model,
        "priority": "normal"
    }
)
```

#### Response Delivery

**Topic**: `ai.gateway.responses.{tenant_id}`

```python
# Requesting response
response = await nats_client.request(
    subject=f"ai.gateway.responses.{tenant_id}",
    payload=encoded_request,
    timeout=60.0
)
```

### RAG System

#### Document Ingestion

**Topic**: `ai.rag.ingest.{tenant_id}`

```python
# Publishing document for ingestion
await nats_client.publish(
    subject=f"ai.rag.ingest.{tenant_id}",
    payload=encoded_document
)
```

#### Query Processing

**Topic**: `ai.rag.queries.{tenant_id}`

```python
# Publishing query
await nats_client.publish(
    subject=f"ai.rag.queries.{tenant_id}",
    payload=encoded_query
)

# Requesting results
results = await nats_client.request(
    subject=f"ai.rag.results.{tenant_id}",
    payload=encoded_query,
    timeout=30.0
)
```

## Error Handling

- Connection failures: Retry with exponential backoff
- Message timeouts: Implement timeout handling
- Queue full: Implement backpressure handling

## Performance Targets

- Agent messaging latency: < 10ms P95
- Gateway queuing latency: < 5ms P95
- RAG queue throughput: > 100 msg/sec

## See Also

- [CORE_COMPONENTS_INTEGRATION_STORY.md](../../CORE_COMPONENTS_INTEGRATION_STORY.md)
- Core SDK NATS wrapper documentation

