# MOTADATA - API BACKEND SERVICES

**Comprehensive explanation of the API Backend Services component providing RESTful API endpoints and backend integration for the SDK.**

## Overview

The API Backend Services component provides RESTful API endpoints and backend integration for the SDK. It exposes SDK functionality through HTTP APIs, enabling external systems and applications to interact with the SDK's capabilities.

## Table of Contents

1. [API Application](#api-application)
2. [API Routing](#api-routing)
3. [Endpoint Creation](#endpoint-creation)
4. [Unified Query Endpoint](#unified-query-endpoint)
5. [Request Validation](#request-validation)
6. [Exception Handling](#exception-handling)
7. [Functions](#functions)
8. [Workflow](#workflow)
9. [Customization](#customization)

---

## API Application

### Functionality

API application provides FastAPI-based REST API:
- **FastAPI Integration**: Uses FastAPI for high-performance APIs
- **CORS Support**: Configurable CORS middleware
- **API Documentation**: Automatic OpenAPI/Swagger documentation
- **Request Validation**: Automatic request validation
- **Response Formatting**: Consistent response formats

### Code Examples

#### Creating API Application

```python
from src.core.api_backend_services import create_api_app

# Create API app
app = create_api_app(
    title="Motadata AI SDK API",
    version="1.0.0",
    description="RESTful API for Motadata Python AI SDK",
    enable_cors=True,
    cors_origins=["http://localhost:3000"]
)
```

---

## API Routing

### Functionality

API routing provides endpoint organization:
- **Router Creation**: Create organized API routers
- **Route Registration**: Register routes with routers
- **Prefix Support**: URL prefixing for versioning
- **Tag Support**: OpenAPI tags for documentation

### Code Examples

#### Creating API Router

```python
from src.core.api_backend_services import create_api_router

# Create router
router = create_api_router(
    prefix="/api/v1",
    tags=["agents", "rag"]
)
```

---

## Endpoint Creation

### Functionality

Endpoint creation provides SDK component endpoints:
- **Agent Endpoints**: Endpoints for agent operations
- **RAG Endpoints**: Endpoints for RAG operations
- **Gateway Endpoints**: Endpoints for LLM operations
- **Health Endpoints**: Health check endpoints

### Code Examples

#### Creating Agent Endpoints

```python
from src.core.api_backend_services import create_agent_endpoints

# Create agent endpoints
create_agent_endpoints(
    router,
    agent_manager,
    prefix="/agents"
)
```

#### Creating RAG Endpoints

```python
from src.core.api_backend_services import create_rag_endpoints

# Create RAG endpoints
create_rag_endpoints(
    router,
    rag_system,
    prefix="/rag"
)
```

---

## Request Validation

### Functionality

Request validation ensures data integrity:
- **Pydantic Models**: Request/response validation
- **Type Checking**: Automatic type validation
- **Required Fields**: Enforces required fields
- **Format Validation**: Validates data formats

---

## Exception Handling

The component handles API errors:
- **HTTP Exceptions**: Standard HTTP error responses
- **Validation Errors**: Request validation errors
- **Component Errors**: SDK component errors
- **Error Formatting**: Consistent error response format

---

## Functions

### Factory Functions

```python
from src.core.api_backend_services import (
    create_api_app,
    create_api_router,
    configure_api_app
)

# Create API app
app = create_api_app(title="My API")

# Create router
router = create_api_router(prefix="/api/v1")

# Configure app
app = configure_api_app(app, enable_cors=True)
```

### Convenience Functions

```python
from src.core.api_backend_services import (
    register_router,
    add_health_check,
    create_agent_endpoints,
    create_rag_endpoints
)

# Register router
register_router(app, router)

# Add health check
add_health_check(app, path="/health")

# Create endpoints
create_agent_endpoints(router, agent_manager)
create_rag_endpoints(router, rag_system)
```

---

## Workflow

### Component Placement in SDK Architecture

The API Backend Services is positioned in the **Application Layer**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SDK ARCHITECTURE OVERVIEW                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         API BACKEND SERVICES (Application Layer)         │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │  FastAPI     │  │  API Router  │  │  Endpoints   │  │   │
│  │  │  Application │  │              │  │              │  │   │
│  │  │              │  │ Functions:   │  │ - Agent      │  │   │
│  │  │ Functions:   │  │ - create_    │  │ - RAG        │  │   │
│  │  │ - create_    │  │   router()   │  │ - Gateway    │  │   │
│  │  │   app()      │  │ - register_  │  │ - Health     │  │   │
│  │  │ - configure_ │  │   router()   │  │              │  │   │
│  │  │   app()      │  │              │  │              │  │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │   │
│  │         │                 │                  │          │   │
│  │         └─────────────────┼──────────────────┘          │   │
│  │                           │                             │   │
│  │                    ┌──────▼───────┐                     │   │
│  │                    │  Request     │                     │   │
│  │                    │  Handler     │                     │   │
│  │                    └──────┬───────┘                     │   │
│  └───────────────────────────┼─────────────────────────────┘   │
│                              │                                   │
┌──────────────────────────────┼───────────────────────────────────┐
│                              │                                   │
│  ┌────────────────────────────▼──────────────────────────────┐   │
│  │              CORE LAYER                                    │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │   │
│  │  │   Agents     │  │   RAG System  │  │LiteLLM       │   │   │
│  │  │              │  │              │  │Gateway       │   │   │
│  │  │ - execute_   │  │ - query()    │  │ - generate() │   │   │
│  │  │   task()     │  │ - ingest_    │  │ - embed()    │   │   │
│  │  │              │  │   document() │  │              │   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│                    CORE LAYER                                    │
└───────────────────────────────────────────────────────────────────┘
```

### API Request Processing Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│              API REQUEST PROCESSING WORKFLOW                     │
└─────────────────────────────────────────────────────────────────┘

    [HTTP Request]
           │
           │ Request:
           │ - Method: GET/POST/PUT/DELETE
           │ - Path: /api/v1/agents/{agent_id}/tasks
           │ - Headers: Content-Type, Authorization
           │ - Body: JSON (if applicable)
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 1: Request Reception                              │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ FastAPI receives HTTP request                     │  │
    │  │                                                   │  │
    │  │ FastAPI Processing:                               │  │
    │  │ 1. Parse request path                             │  │
    │  │ 2. Match route to endpoint                       │  │
    │  │ 3. Extract path parameters                       │  │
    │  │ 4. Parse request body (if JSON)                  │  │
    │  │ 5. Extract query parameters                      │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 2: Request Validation                              │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ FastAPI validates request using Pydantic models  │  │
    │  │                                                   │  │
    │  │ Validation Checks:                                 │  │
    │  │ 1. Request body structure                         │  │
    │  │ 2. Parameter types                                │  │
    │  │ 3. Required fields                                │  │
    │  │ 4. Value constraints                              │  │
    │  │                                                   │  │
    │  │ If validation fails:                              │  │
    │  │     return 422 Unprocessable Entity               │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 3: Authentication/Authorization (if enabled)        │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ if authentication_enabled:                       │  │
    │  │     token = extract_token(request)                │  │
    │  │     user = validate_token(token)                 │  │
    │  │     if not user:                                 │  │
    │  │         return 401 Unauthorized                  │  │
    │  │                                                   │  │
    │  │     # Check authorization                        │  │
    │  │     if not has_permission(user, endpoint):       │  │
    │  │         return 403 Forbidden                      │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 4: Route to SDK Component                          │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ @router.post("/agents/{agent_id}/tasks")          │  │
    │  │ async def create_task(agent_id: str, task: Task): │  │
    │  │     # Route to agent manager                      │  │
    │  │     agent = agent_manager.get_agent(agent_id)     │  │
    │  │     result = await agent.execute_task(task)        │  │
    │  │     return result                                 │  │
    │  │                                                   │  │
    │  │ Component Routing:                                │  │
    │  │ - /agents/* → Agent Framework                     │  │
    │  │ - /rag/* → RAG System                            │  │
    │  │ - /llm/* → LiteLLM Gateway                       │  │
    │  │ - /health → Health Check                          │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 5: SDK Component Execution                         │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ # Execute SDK component operation                 │  │
    │  │ result = await component.operation(params)        │  │
    │  │                                                   │  │
    │  │ Component Operations:                             │  │
    │  │ - Agent: execute_task(), get_status()            │  │
    │  │ - RAG: query(), ingest_document()                │  │
    │  │ - Gateway: generate(), embed()                   │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 6: Response Formatting                             │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ response = {                                      │  │
    │  │     "status": "success",                          │  │
    │  │     "data": result,                               │  │
    │  │     "timestamp": datetime.now().isoformat()       │  │
    │  │ }                                                 │  │
    │  │                                                   │  │
    │  │ Response Format:                                  │  │
    │  │ - Success: 200 OK with data                      │  │
    │  │ - Error: Appropriate HTTP status with error       │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    [Return HTTP Response]
```

### Parameter Details

#### create_api_app() Parameters

```python
def create_api_app(
    title: str = "Motadata AI SDK API",  # API title
                                    # Used in OpenAPI docs
                                    # Default: "Motadata AI SDK API"

    version: str = "0.1.0",         # API version
                                  # Semantic versioning
                                  # Default: "0.1.0"

    description: str = "...",       # API description
                                  # Used in OpenAPI docs
                                  # Default: "RESTful API for..."

    enable_cors: bool = True,       # Enable CORS middleware
                                  # Allows cross-origin requests
                                  # Default: True

    cors_origins: List[str] = None,  # Allowed CORS origins
                                   # List of allowed origins
                                   # None = ["*"] (all origins)
                                   # Example: ["http://localhost:3000"]

    **kwargs: Any                   # Additional FastAPI config
                                   # Passed to FastAPI constructor
) -> FastAPI
```

---

## Customization

### Configuration

```python
# Custom API configuration
app = create_api_app(
    title="Custom API",
    version="2.0.0",
    enable_cors=True,
    cors_origins=["https://app.example.com"]
)
```

---

## Best Practices

1. **API Versioning**: Use URL prefixes for versioning
2. **Request Validation**: Always validate requests
3. **Error Handling**: Provide clear error messages
4. **Authentication**: Implement proper authentication
5. **Rate Limiting**: Implement rate limiting
6. **Documentation**: Keep API documentation updated
7. **CORS Configuration**: Configure CORS appropriately
8. **Response Formatting**: Use consistent response formats

---

## Additional Resources

- **Component README**: `src/core/api_backend_services/README.md`
- **Function Documentation**: `src/core/api_backend_services/functions.py`
- **Examples**: `examples/basic_usage/10_api_backend_basic.py`

