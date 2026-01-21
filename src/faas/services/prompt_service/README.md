# Prompt Service

## Overview

Prompt Service is a FaaS implementation of the Prompt Context Management component. It provides REST API endpoints for prompt template management, prompt rendering, and context building operations.

## API Endpoints

### Template Management

- `POST /api/v1/prompts/templates` - Create a new prompt template

**Request Body:**
```json
{
  "name": "analysis_template",
  "version": "1.0.0",
  "content": "Analyze the following: {{text}}",
  "metadata": {"category": "analysis"}
}
```

- `GET /api/v1/prompts/templates/{template_id}` - Get template by ID
- `GET /api/v1/prompts/templates` - List all templates

### Prompt Rendering

- `POST /api/v1/prompts/render` - Render a prompt template with variables

**Request Body:**
```json
{
  "template_name": "analysis_template",
  "variables": {
    "text": "This is the text to analyze"
  },
  "version": "1.0.0"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "rendered_prompt": "Analyze the following: This is the text to analyze"
  }
}
```

### Context Building

- `POST /api/v1/prompts/context` - Build context from messages

**Request Body:**
```json
{
  "messages": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
  ]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "context": "User: Hello\nAssistant: Hi there!"
  }
}
```

## Service Dependencies

- **Database**: For template storage (optional, can use in-memory)

## Stateless Architecture

The Prompt Service is **stateless**:
- Prompt manager instances are created on-demand per request
- No in-memory caching of prompt managers
- Templates can be stored in database for persistence

## Usage

```python
from src.faas.services.prompt_service import create_prompt_service

# Create service
service = create_prompt_service(
    service_name="prompt-service",
    config_overrides={
        "database_url": "postgresql://user:pass@localhost/db",
    }
)

# Run service
# uvicorn service.app:app --host 0.0.0.0 --port 8080
```

## Integration with Other Services

### Called by Other Services

Prompt Service is called by:
- **Agent Service**: For prompt template rendering
- **RAG Service**: For context building
- **Gateway Service**: For prompt optimization

### Using Service Client

```python
from src.faas.shared import ServiceClientManager

client_manager = ServiceClientManager(config)
prompt_client = client_manager.get_client("prompt")

# Render prompt
response = await prompt_client.post(
    "/api/v1/prompts/render",
    json_data={
        "template_name": "analysis_template",
        "variables": {"text": "Analyze this"}
    },
    headers=prompt_client.get_headers(tenant_id=tenant_id)
)
```

## Configuration

```bash
SERVICE_NAME=prompt-service
SERVICE_PORT=8080
DATABASE_URL=postgresql://user:pass@localhost/db
ENABLE_NATS=true
ENABLE_OTEL=true
```

## Example Request

```bash
# Create template
curl -X POST http://localhost:8080/api/v1/prompts/templates \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant_123" \
  -d '{
    "name": "analysis_template",
    "content": "Analyze: {{text}}",
    "version": "1.0.0"
  }'

# Render prompt
curl -X POST http://localhost:8080/api/v1/prompts/render \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant_123" \
  -d '{
    "template_name": "analysis_template",
    "variables": {"text": "Hello world"}
  }'
```

## Features

- **Template Versioning**: Manage multiple versions of templates
- **Variable Substitution**: Dynamic prompt rendering
- **Context Building**: Build context from message history
- **Token Estimation**: Estimate tokens in prompts
- **Prompt Truncation**: Truncate prompts to fit token limits
- **Sensitive Data Redaction**: Strip sensitive information from prompts

