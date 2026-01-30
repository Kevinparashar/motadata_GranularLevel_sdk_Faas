# MOTADATA - AGENT SERVICE

**FaaS implementation of the Agent Framework providing REST API endpoints for managing AI agents, executing tasks, and handling chat interactions.**

## Overview

Agent Service is a FaaS implementation of the Agent Framework component. It provides REST API endpoints for managing AI agents, executing tasks, handling chat interactions, and managing agent memory and tools.

## API Endpoints

### Agent Management

- `POST /api/v1/agents` - Create a new agent
- `GET /api/v1/agents/{agent_id}` - Get agent by ID
- `PUT /api/v1/agents/{agent_id}` - Update agent
- `DELETE /api/v1/agents/{agent_id}` - Delete agent
- `GET /api/v1/agents` - List all agents

### Task Execution

- `POST /api/v1/agents/{agent_id}/execute` - Execute a task with an agent

### Chat Interactions

- `POST /api/v1/agents/{agent_id}/chat` - Chat with an agent
- `POST /api/v1/agents/{agent_id}/chat/stream` - Stream chat response

### Memory Management

- `GET /api/v1/agents/{agent_id}/memory` - Get agent memory
- `POST /api/v1/agents/{agent_id}/memory` - Store memory
- `DELETE /api/v1/agents/{agent_id}/memory/{memory_id}` - Delete memory

### Tool Management

- `POST /api/v1/agents/{agent_id}/tools` - Add tool to agent
- `GET /api/v1/agents/{agent_id}/tools` - List agent tools
- `DELETE /api/v1/agents/{agent_id}/tools/{tool_id}` - Remove tool

## Service Dependencies

- **Gateway Service**: For LLM calls (text generation)
- **Cache Service**: For caching agent responses
- **Database**: For agent state persistence

## Usage

```python
from src.faas.services.agent_service import create_agent_service

# Create service
service = create_agent_service(
    service_name="agent-service",
    config_overrides={
        "gateway_service_url": "http://gateway-service:8080",
        "cache_service_url": "http://cache-service:8080",
    }
)

# Run service
# uvicorn service.app:app --host 0.0.0.0 --port 8080
```

## Integration with Other Services

### Using Gateway Service

```python
# Agent Service calls Gateway Service for LLM generation
async with httpx.AsyncClient() as client:
    response = await client.post(
        f"{gateway_service_url}/api/v1/gateway/generate",
        json={"prompt": prompt, "model": "gpt-4"},
        headers={"X-Tenant-ID": tenant_id}
    )
```

### Using NATS for Events

```python
# Publish agent creation event
event = {
    "event_type": "agent.created",
    "agent_id": agent_id,
    "tenant_id": tenant_id,
}
await nats_client.publish(
    f"agent.events.{tenant_id}",
    codec_manager.encode(event)
)
```

## Configuration

```bash
SERVICE_NAME=agent-service
SERVICE_PORT=8080
GATEWAY_SERVICE_URL=http://gateway-service:8080
CACHE_SERVICE_URL=http://cache-service:8080
DATABASE_URL=postgresql://user:pass@localhost/db
ENABLE_NATS=true
ENABLE_OTEL=true
```

