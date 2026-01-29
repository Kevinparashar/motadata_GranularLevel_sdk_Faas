# Motadata Prompt Generator Service

## Overview

Prompt Generator Service is a FaaS implementation of the Prompt-Based Generator component. It provides REST API endpoints for creating agents and tools from natural language prompts, collecting feedback, and managing permissions.

## API Endpoints

### Agent Creation from Prompt

- `POST /api/v1/prompt/agents` - Create an agent from a natural language prompt

**Request Body:**
```json
{
  "prompt": "Create a customer support agent that categorizes tickets and suggests solutions",
  "agent_id": "optional-agent-id",
  "llm_model": "gpt-4",
  "llm_provider": "openai",
  "cache_enabled": true,
  "additional_config": {}
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "agent_id": "agent_abc123",
    "name": "Customer Support Agent",
    "description": "Categorizes tickets and suggests solutions",
    "capabilities": ["ticket_categorization", "solution_suggestion"],
    "system_prompt": "You are a customer support agent...",
    "config": {},
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### Tool Creation from Prompt

- `POST /api/v1/prompt/tools` - Create a tool from a natural language prompt

**Request Body:**
```json
{
  "prompt": "Create a tool that calculates priority based on urgency and impact",
  "tool_id": "optional-tool-id",
  "llm_model": "gpt-4",
  "cache_enabled": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "tool_id": "tool_xyz789",
    "name": "Priority Calculator",
    "description": "Calculates priority based on urgency and impact",
    "code": "def calculate_priority(urgency, impact): ...",
    "parameters": [...],
    "config": {},
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### Feedback Collection

- `POST /api/v1/prompt/agents/{agent_id}/rate` - Rate an agent
- `POST /api/v1/prompt/tools/{tool_id}/rate` - Rate a tool
- `GET /api/v1/prompt/agents/{agent_id}/feedback` - Get agent feedback statistics
- `GET /api/v1/prompt/tools/{tool_id}/feedback` - Get tool feedback statistics

### Permission Management

- `POST /api/v1/prompt/permissions` - Grant permission for a resource

## Service Dependencies

- **Gateway Service**: For LLM calls (text generation for prompt interpretation)
- **Database**: For storing generated agents/tools and feedback

## Usage

```python
from src.faas.services.prompt_generator_service import create_prompt_generator_service

# Create service
app = create_prompt_generator_service(
    service_name="prompt-generator-service",
    config_overrides={
        "database_url": "postgresql://user:pass@localhost/db",
        "gateway_service_url": "http://gateway-service:8080",
    }
)

# Run with uvicorn
# uvicorn src.faas.services.prompt_generator_service.service:app --host 0.0.0.0 --port 8087
```

## Example: Create Agent from Prompt

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8087/api/v1/prompt/agents",
        json={
            "prompt": "Create a customer support agent that categorizes tickets",
            "llm_model": "gpt-4"
        },
        headers={"X-Tenant-ID": "tenant_123"}
    )
    agent = response.json()["data"]
    print(f"Created agent: {agent['agent_id']}")
```

## Service Configuration

Configure via environment variables or config file:

```bash
# Service
SERVICE_NAME=prompt-generator-service
SERVICE_PORT=8087

# Dependencies
GATEWAY_SERVICE_URL=http://gateway-service:8080
DATABASE_URL=postgresql://user:pass@localhost/db

# Integrations
ENABLE_NATS=false
ENABLE_OTEL=false
```

## Health Check

- `GET /health` - Service health check

## Error Handling

The service returns standard error responses:

- `400 Bad Request`: Invalid request format
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side errors

All errors include correlation_id and request_id for tracing.

