# MOTADATA - API BACKEND SERVICES

**RESTful API endpoints and backend integration for exposing SDK functionality through HTTP APIs.**

## When to Use This Component

**✅ Use API Backend Services when:**
- You need REST endpoints for external systems
- You're building a standalone API service
- You want to expose SDK functionality via HTTP
- You need API endpoints for Agents, RAG, or Gateway
- You're not using AWS API Gateway (or need additional endpoints)
- You want unified query endpoints that orchestrate multiple components

**❌ Don't use API Backend Services when:**
- You're using AWS API Gateway with Lambda (SDK is used as library)
- You only need direct Python usage (no API needed)
- You're building internal tools without API requirements
- You're integrating SDK into existing backend (use SDK as library)

**Simple Example:**
```python
from src.core.api_backend_services import create_api_app, create_unified_query_endpoint
from src.core.litellm_gateway import create_gateway
from src.core.agno_agent_framework import create_agent

gateway = create_gateway(api_key="your-key", provider="openai")
agent = create_agent("assistant", "AI Assistant", gateway)

app = create_api_app(title="AI SDK API")
create_unified_query_endpoint(app, agent, rag=None, gateway=gateway)
```

**Note:** If using AWS API Gateway, you typically use SDK components directly in Lambda functions rather than this API component.

---

## Overview

The API Backend Services component provides RESTful API endpoints and backend integration for the SDK. It exposes SDK functionality through HTTP APIs, enabling external systems and applications to interact with the SDK's capabilities.

## Purpose and Functionality

This component serves as the API gateway for the SDK, providing:
- **RESTful Endpoints**: Standard REST API endpoints for SDK operations
- **Request Validation**: Validates and sanitizes incoming requests
- **Response Formatting**: Provides consistent response formats
- **Error Handling**: Implements comprehensive error handling and reporting
- **Authentication**: Supports API key, OAuth2, and JWT authentication

The component abstracts SDK internals, providing a clean, standardized API interface that external systems can consume. It handles request routing, validation, and response formatting, allowing SDK components to focus on their core functionality.

## Connection to Other Components

### Integration with LiteLLM Gateway

The **LiteLLM Gateway** (`src/core/litellm_gateway/`) is accessed through API endpoints. When API requests come in for text generation or embeddings, the backend services route them to the gateway, which handles the actual LLM interactions. The backend services format the gateway responses into appropriate HTTP responses.

### Integration with RAG System

The **RAG System** (`src/core/rag/`) is exposed through API endpoints:
- **Document Ingestion**: Endpoints for adding documents to the knowledge base
- **Query Endpoints**: Endpoints for querying the RAG system
- **Document Management**: Endpoints for managing documents

The backend services handle request validation, route requests to the RAG system, and format responses for API consumers.

### Integration with Agno Agent Framework

The **Agno Agent Framework** (`src/core/agno_agent_framework/`) is accessible through API endpoints:
- **Agent Creation**: Endpoints for creating and managing agents
- **Task Submission**: Endpoints for submitting tasks to agents
- **Status Queries**: Endpoints for querying agent status

The backend services provide the HTTP interface that external systems use to interact with agents.

### Integration with Connectivity Clients

The **Connectivity Clients** (root level) are used by the backend services for making outbound HTTP requests. When the backend services need to call external APIs or services, they use connectivity clients to manage those connections efficiently.

### Integration with Evaluation & Observability

The **Evaluation & Observability** component (`src/core/evaluation_observability/`) monitors all API requests:
- **Request Metrics**: Tracks request volumes, response times, and error rates
- **API Usage**: Monitors API endpoint usage patterns
- **Performance Monitoring**: Tracks API performance and identifies bottlenecks
- **Error Tracking**: Logs and tracks API errors for debugging

This monitoring is essential for understanding API usage, optimizing performance, and debugging issues.

### Integration with Cache Mechanism

The **Cache Mechanism** (`src/core/cache_mechanism/`) can be used by the backend services to cache API responses. Frequently accessed endpoints can cache their responses, improving performance and reducing backend load.

### Integration with Machine Learning Components

The **Machine Learning Components** (`src/core/machine_learning/`) can be exposed through API endpoints:
- **ML Framework**: Endpoints for model training and inference
- **Model Serving**: Endpoints for model predictions (can use Model Server directly)
- **MLOps Pipeline**: Endpoints for experiment tracking and model deployment
- **Data Management**: Endpoints for data ingestion and feature store access

The backend services can integrate with ML components to provide ML capabilities through REST APIs, enabling external systems to train models, make predictions, and manage ML workflows.

### Unified Query Endpoint

The backend services provide a **unified query endpoint** that orchestrates Agent and RAG:
- **Automatic Routing**: Automatically determines whether to use Agent or RAG based on query
- **Dual Processing**: Can use both Agent and RAG for comprehensive responses
- **Mode Selection**: Supports "auto", "agent", "rag", or "both" modes
- **Single Entry Point**: One endpoint for all query types

**Example:**
```python
from src.core.api_backend_services import (
    create_api_app,
    create_api_router,
    create_unified_query_endpoint,
    register_router
)

app = create_api_app()
router = create_api_router(prefix="/api/v1")

# Create unified endpoint
create_unified_query_endpoint(
    router=router,
    agent_manager=agent_manager,
    rag_system=rag_system,
    gateway=gateway,
    prefix="/query"
)

register_router(app, router)

# Usage:
# POST /api/v1/query
# {
#   "query": "What is AI?",
#   "mode": "auto",  # or "agent", "rag", "both"
#   "tenant_id": "tenant1",
#   "user_id": "user123"
# }
```

**Benefits:**
- **Simplified Integration**: Single endpoint for all queries
- **Intelligent Routing**: Automatically chooses best processing path
- **Flexible**: Supports explicit mode selection when needed
- **Comprehensive**: Can combine Agent and RAG responses

## Libraries Utilized

- **fastapi**: Modern web framework for building APIs. It provides automatic API documentation, request validation, and async support.
- **uvicorn**: ASGI server for running FastAPI applications. It provides high-performance async request handling.
- **pydantic**: Used for request and response validation. All API request and response models are defined using Pydantic, ensuring type safety and validation.

## Function-Driven API

The API Backend Services provides a **function-driven API** with factory functions, high-level convenience functions, and utilities for easy API creation and endpoint management.

### Factory Functions

Create API applications and routers with simplified configuration:

```python
from src.core.api_backend_services import (
    create_api_app,
    create_api_router,
    configure_api_app
)

# Create FastAPI app
app = create_api_app(
    title="My AI API",
    enable_cors=True,
    cors_origins=["http://localhost:3000"]
)

# Create API router
router = create_api_router(prefix="/api/v1", tags=["agents"])

# Configure existing app
app = configure_api_app(app, enable_cors=True)
```

### High-Level Convenience Functions

Use simplified functions for common operations:

```python
from src.core.api_backend_services import (
    register_router,
    add_endpoint,
    create_rag_endpoints,
    create_agent_endpoints,
    create_gateway_endpoints
)

# Register router
register_router(app, router)

# Add endpoint
def get_status():
    return {"status": "ok"}

add_endpoint(router, "/status", "GET", get_status)

# Create component endpoints
create_rag_endpoints(router, rag_system, prefix="/api/rag")
create_agent_endpoints(router, agent_manager, prefix="/api/agents")
create_gateway_endpoints(router, gateway, prefix="/api/gateway")
```

### Utility Functions

Use utility functions for common API patterns:

```python
from src.core.api_backend_services import (
    add_health_check,
    add_api_versioning
)

# Add health check
add_health_check(app, path="/health")

# Set up API versioning
api_prefix = add_api_versioning(app, version="v1")
# Use api_prefix for all routes
```

### Complete Example

```python
from src.core.api_backend_services import (
    create_api_app,
    create_api_router,
    create_rag_endpoints,
    create_agent_endpoints,
    add_health_check
)

# Create app
app = create_api_app(title="AI SDK API", enable_cors=True)

# Create router
router = create_api_router(prefix="/api/v1")

# Add component endpoints
create_rag_endpoints(router, rag_system)
create_agent_endpoints(router, agent_manager)

# Register router
register_router(app, router)

# Add health check
add_health_check(app)

# Run with uvicorn
# uvicorn app:app --reload
```

See `src/core/api_backend_services/functions.py` for complete function documentation.

## Key Features

### RESTful API Design

The component follows REST principles:
- **Resource-based URLs**: URLs represent resources, not actions
- **HTTP Methods**: Uses appropriate HTTP methods (GET, POST, PUT, DELETE)
- **Status Codes**: Returns appropriate HTTP status codes
- **JSON Responses**: Provides JSON-formatted responses

### Request Validation

All incoming requests are validated:
- **Schema Validation**: Validates request bodies against defined schemas
- **Parameter Validation**: Validates query parameters and path parameters
- **Type Checking**: Ensures data types match expected types
- **Sanitization**: Sanitizes input to prevent security issues

### Error Handling

Comprehensive error handling:
- **Validation Errors**: Returns clear validation error messages
- **Business Logic Errors**: Handles and reports business logic errors
- **System Errors**: Gracefully handles system errors with appropriate error responses
- **Error Formatting**: Provides consistent error response formats

### Authentication and Authorization

Supports multiple authentication methods:
- **API Keys**: Simple API key authentication
- **OAuth2**: OAuth2 token-based authentication
- **JWT**: JSON Web Token authentication

## API Endpoints

### Query Endpoint

Provides RAG query functionality through HTTP POST requests. Accepts queries, model specifications, and retrieval parameters, returning generated responses with source documents.

### Document Ingestion Endpoint

Allows adding documents to the knowledge base through HTTP POST requests. Accepts document content, metadata, and source information, returning document IDs upon successful ingestion.

### Agent Task Endpoint

Enables task submission to agents through HTTP POST requests. Accepts task specifications and agent identifiers, returning task IDs and status information.

## Error Responses

The component provides standardized error responses:
- **400 Bad Request**: Invalid request format or parameters
- **401 Unauthorized**: Authentication required or failed
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server-side errors

All error responses include detailed error messages and error codes for debugging.

## Best Practices

1. **API Versioning**: Use versioning (e.g., /api/v1/) to maintain backward compatibility
2. **Rate Limiting**: Implement rate limiting to prevent abuse
3. **Input Validation**: Validate all inputs to prevent security issues
4. **Error Handling**: Provide clear, actionable error messages
5. **Documentation**: Maintain comprehensive API documentation
6. **Monitoring**: Monitor API usage and performance continuously
7. **Security**: Implement proper authentication and authorization
