# Motadata Getting Started with API Backend Services

## Overview

The API Backend Services component provides RESTful API endpoints for exposing SDK functionality. This guide explains the complete workflow from API creation to endpoint registration.

## Entry Point

The primary entry point for creating APIs:

```python
from src.core.api_backend_services import (
    create_api_app,
    create_api_router,
    register_router,
    create_rag_endpoints,
    create_agent_endpoints,
    create_unified_query_endpoint
)
```

## Input Requirements

### Required Inputs

1. **API Configuration**:
   - `title`: API title (optional, default: "Motadata AI SDK API")

### Optional Inputs

- `version`: API version
- `description`: API description
- `enable_cors`: Enable CORS middleware
- `cors_origins`: List of allowed CORS origins

## Process Flow

### Step 1: API Application Creation

**What Happens:**
1. FastAPI application is created
2. CORS middleware is configured (if enabled)
3. API metadata is set
4. Application is ready for routing

**Code:**
```python
app = create_api_app(
    title="AI SDK API",
    version="1.0.0",
    enable_cors=True,
    cors_origins=["http://localhost:3000"]
)
```

**Internal Process:**
```
create_api_app()
  ├─> Create FastAPI instance
  ├─> Configure CORS (if enabled)
  ├─> Set API metadata
  └─> Return app instance
```

### Step 2: Router Creation

**What Happens:**
1. API router is created
2. Prefix is set
3. Router is ready for endpoints

**Code:**
```python
router = create_api_router(prefix="/api/v1")
```

**Internal Process:**
```
create_api_router()
  ├─> Create APIRouter instance
  ├─> Set prefix
  └─> Return router instance
```

### Step 3: Endpoint Registration

**What Happens:**
1. Endpoints are added to router
2. Request validation is configured
3. Response formatting is set up
4. Error handling is configured

**Code:**
```python
# Custom endpoint
@router.get("/status")
def get_status():
    return {"status": "ok"}

# Component endpoints
create_rag_endpoints(router, rag_system, prefix="/rag")
create_agent_endpoints(router, agent_manager, prefix="/agents")

# Unified query endpoint (orchestrates Agent and RAG)
create_unified_query_endpoint(
    router=router,
    agent_manager=agent_manager,
    rag_system=rag_system,
    gateway=gateway,
    prefix="/query"
)
```

**Input:**
- `router`: API router instance
- Component instances (rag_system, agent_manager, gateway, etc.)
- `prefix`: URL prefix for endpoints

**Internal Process:**
```
create_rag_endpoints()
  ├─> Add POST /rag/query endpoint
  ├─> Add POST /rag/ingest endpoint
  ├─> Configure request validation
  ├─> Set up response formatting
  └─> Add error handling

create_agent_endpoints()
  ├─> Add GET /agents endpoint
  ├─> Add POST /agents/{agent_id}/execute endpoint
  ├─> Configure request validation
  └─> Set up response formatting

create_unified_query_endpoint()
  ├─> Add POST /query endpoint
  ├─> Configure automatic routing (auto/agent/rag/both modes)
  ├─> Set up intelligent query routing
  ├─> Configure request validation
  └─> Set up response formatting
```

### Step 4: Router Registration

**What Happens:**
1. Router is registered with app
2. Routes are mounted
3. API is ready to serve

**Code:**
```python
register_router(app, router)
```

**Internal Process:**
```
register_router()
  ├─> Include router in app
  ├─> Mount routes
  └─> API ready
```

## Output

### API Response Structure

```python
# Success response
{
    "status": "success",
    "data": {...},
    "metadata": {...}
}

# Error response
{
    "status": "error",
    "error": {
        "message": "Error message",
        "code": "ERROR_CODE",
        "details": {...}
    }
}
```

### Endpoint Responses

**RAG Query Endpoint:**
```python
POST /api/v1/rag/query
{
    "query": "What is AI?",
    "top_k": 5,
    "tenant_id": "tenant_123"
}

Response:
{
    "status": "success",
    "data": {
        "answer": "AI is...",
        "sources": [...]
    }
}
```

**Agent Execute Endpoint:**
```python
POST /api/v1/agents/{agent_id}/execute
{
    "task_type": "llm_query",
    "parameters": {
        "prompt": "What is AI?",
        "model": "gpt-4"
    }
}

Response:
{
    "status": "success",
    "data": {
        "task_id": "task_123",
        "result": {...}
    }
}
```

**Unified Query Endpoint:**
```python
POST /api/v1/query
{
    "query": "What is AI?",
    "mode": "auto",  # or "agent", "rag", "both"
    "tenant_id": "tenant_123",
    "user_id": "user_456",
    "conversation_id": "conv_789"
}

Response:
{
    "status": "success",
    "data": {
        "answer": "AI is...",
        "mode_used": "rag",  # or "agent", "both"
        "sources": [...],  # if RAG was used
        "agent_response": {...}  # if Agent was used
    }
}
```

## Where Output is Used

### 1. HTTP API Access

```python
# External systems can call API endpoints
import requests

response = requests.post(
    "http://localhost:8000/api/v1/rag/query",
    json={
        "query": "What is AI?",
        "top_k": 5
    }
)

result = response.json()
print(result["data"]["answer"])
```

### 2. Frontend Integration

```python
# Frontend applications can consume API
# JavaScript example:
fetch('http://localhost:8000/api/v1/rag/query', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        query: "What is AI?",
        top_k: 5
    })
})
.then(response => response.json())
.then(data => console.log(data.data.answer));
```

### 3. API Documentation

```python
# Automatic OpenAPI/Swagger documentation
# Available at: http://localhost:8000/docs
# Interactive API explorer
```

## Complete Example

```python
from fastapi import FastAPI
from src.core.api_backend_services import (
    create_api_app,
    create_api_router,
    register_router,
    create_rag_endpoints,
    create_agent_endpoints,
    add_health_check
)
from src.core.rag import create_rag_system
from src.core.agno_agent_framework import AgentManager
from src.core.postgresql_database import DatabaseConnection
from src.core.litellm_gateway import create_gateway

# Step 1: Initialize Components (Entry Point)
db = DatabaseConnection(...)
gateway = create_gateway(api_key="...", provider="openai")
rag = create_rag_system(db=db, gateway=gateway)
agent_manager = AgentManager()

# Step 2: Create API App (Entry Point)
app = create_api_app(
    title="AI SDK API",
    version="1.0.0",
    enable_cors=True,
    cors_origins=["http://localhost:3000"]
)

# Step 3: Create Router (Input)
router = create_api_router(prefix="/api/v1")

# Step 4: Add Custom Endpoints (Input)
@router.get("/status")
def get_status():
    return {"status": "ok", "version": "1.0.0"}

# Step 5: Add Component Endpoints (Process)
create_rag_endpoints(router, rag, prefix="/rag")
create_agent_endpoints(router, agent_manager, prefix="/agents")

# Step 6: Register Router (Process)
register_router(app, router)

# Step 7: Add Health Check
add_health_check(app)

# Step 8: Run API
# uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## Important Information

### Request Validation

```python
from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    tenant_id: Optional[str] = None

@router.post("/custom/query")
def custom_query(request: QueryRequest):
    # Request is automatically validated
    return {"query": request.query, "top_k": request.top_k}
```

### Error Handling

```python
from fastapi import HTTPException

@router.get("/data/{item_id}")
def get_item(item_id: str):
    if item_id not in items:
        raise HTTPException(
            status_code=404,
            detail="Item not found"
        )
    return {"item": items[item_id]}
```

### Authentication

```python
from fastapi import Depends, HTTPException, Header

def verify_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")
    token = authorization.split(" ")[1]
    # Verify token
    return token

@router.get("/protected")
def protected_endpoint(token: str = Depends(verify_token)):
    return {"message": "Access granted"}
```

### CORS Configuration

```python
app = create_api_app(
    enable_cors=True,
    cors_origins=[
        "http://localhost:3000",
        "https://example.com"
    ]
)
```

### API Versioning

```python
# Multiple version routers
v1_router = create_api_router(prefix="/api/v1")
v2_router = create_api_router(prefix="/api/v2")

register_router(app, v1_router)
register_router(app, v2_router)
```

## Next Steps

- See [README.md](README.md) for detailed component documentation
- Check [docs/components/api_backend_services_explanation.md](../../../docs/components/api_backend_services_explanation.md) for comprehensive guide
- Review [troubleshooting guide](../../../docs/troubleshooting/api_backend_services_troubleshooting.md) for common issues
- Run API: `uvicorn app:app --reload`

