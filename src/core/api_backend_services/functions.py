"""
API Backend Services - High-Level Functions

Factory functions, convenience functions, and utilities for API backend services.
"""

from typing import Any, Dict, List, Optional, Callable
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware


# ============================================================================
# Factory Functions
# ============================================================================

def create_api_app(
    title: str = "Motadata AI SDK API",
    version: str = "0.1.0",
    description: str = "RESTful API for Motadata Python AI SDK",
    enable_cors: bool = True,
    cors_origins: List[str] = None,
    **kwargs: Any
) -> FastAPI:
    """
    Create and configure a FastAPI application with default settings.
    
    Args:
        title: API title
        version: API version
        description: API description
        enable_cors: Enable CORS middleware
        cors_origins: List of allowed CORS origins
        **kwargs: Additional FastAPI configuration
    
    Returns:
        Configured FastAPI instance
    
    Example:
        >>> app = create_api_app(
        ...     title="My AI API",
        ...     enable_cors=True,
        ...     cors_origins=["http://localhost:3000"]
        ... )
    """
    app = FastAPI(
        title=title,
        version=version,
        description=description,
        **kwargs
    )
    
    if enable_cors:
        origins = cors_origins or ["*"]
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    return app


def create_api_router(
    prefix: str = "",
    tags: Optional[List[str]] = None,
    **kwargs: Any
) -> APIRouter:
    """
    Create an API router with default settings.
    
    Args:
        prefix: URL prefix for all routes
        tags: Optional tags for OpenAPI documentation
        **kwargs: Additional router configuration
    
    Returns:
        Configured APIRouter instance
    
    Example:
        >>> router = create_api_router(prefix="/api/v1", tags=["agents"])
    """
    return APIRouter(
        prefix=prefix,
        tags=tags or [],
        **kwargs
    )


def configure_api_app(
    app: FastAPI,
    enable_cors: bool = True,
    cors_origins: List[str] = None,
    **kwargs: Any
) -> FastAPI:
    """
    Configure an existing FastAPI application.
    
    Args:
        app: FastAPI application instance
        enable_cors: Enable CORS middleware
        cors_origins: List of allowed CORS origins
        **kwargs: Additional configuration
    
    Returns:
        Configured FastAPI instance
    
    Example:
        >>> app = FastAPI()
        >>> app = configure_api_app(app, enable_cors=True)
    """
    if enable_cors and not any(isinstance(m, CORSMiddleware) for m in app.user_middleware):
        origins = cors_origins or ["*"]
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    return app


# ============================================================================
# High-Level Convenience Functions
# ============================================================================

def register_router(
    app: FastAPI,
    router: APIRouter,
    prefix: Optional[str] = None
) -> None:
    """
    Register a router with the FastAPI app (high-level convenience).
    
    Args:
        app: FastAPI application instance
        router: APIRouter instance
        prefix: Optional prefix override
    
    Example:
        >>> router = create_api_router(prefix="/api/v1")
        >>> register_router(app, router)
    """
    app.include_router(router, prefix=prefix)


def add_endpoint(
    router: APIRouter,
    path: str,
    method: str = "GET",
    handler: Optional[Callable] = None,
    **kwargs: Any
) -> None:
    """
    Add an endpoint to a router (high-level convenience).
    
    Args:
        router: APIRouter instance
        path: Endpoint path
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        handler: Endpoint handler function
        **kwargs: Additional endpoint configuration
    
    Example:
        >>> def get_status():
        ...     return {"status": "ok"}
        >>> add_endpoint(router, "/status", "GET", get_status)
    """
    if handler is None:
        return
    
    method = method.upper()
    if method == "GET":
        router.get(path, **kwargs)(handler)
    elif method == "POST":
        router.post(path, **kwargs)(handler)
    elif method == "PUT":
        router.put(path, **kwargs)(handler)
    elif method == "DELETE":
        router.delete(path, **kwargs)(handler)
    elif method == "PATCH":
        router.patch(path, **kwargs)(handler)
    else:
        router.add_api_route(path, handler, methods=[method], **kwargs)


def create_rag_endpoints(
    router: APIRouter,
    rag_system: Any,
    prefix: str = "/rag"
) -> None:
    """
    Create RAG system endpoints (high-level convenience).
    
    Args:
        router: APIRouter instance
        rag_system: RAGSystem instance
        prefix: URL prefix for RAG endpoints
    
    Example:
        >>> router = create_api_router()
        >>> create_rag_endpoints(router, rag_system, prefix="/api/rag")
    """
    from ..rag import quick_rag_query, ingest_document_simple
    
    @router.post(f"{prefix}/query")
    async def query_rag(request: Dict[str, Any]) -> Dict[str, Any]:
        """Query the RAG system."""
        query = request.get("query", "")
        top_k = request.get("top_k", 5)
        threshold = request.get("threshold", 0.7)
        return quick_rag_query(rag_system, query, top_k=top_k, threshold=threshold)
    
    @router.post(f"{prefix}/ingest")
    async def ingest_document(request: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest a document into the RAG system."""
        doc_id = ingest_document_simple(
            rag_system,
            title=request.get("title", ""),
            content=request.get("content", ""),
            source=request.get("source"),
            metadata=request.get("metadata")
        )
        return {"document_id": doc_id, "status": "success"}


def create_agent_endpoints(
    router: APIRouter,
    agent_manager: Any,
    prefix: str = "/agents"
) -> None:
    """
    Create agent framework endpoints (high-level convenience).
    
    Args:
        router: APIRouter instance
        agent_manager: AgentManager instance
        prefix: URL prefix for agent endpoints
    
    Example:
        >>> router = create_api_router()
        >>> create_agent_endpoints(router, agent_manager, prefix="/api/agents")
    """
    from ..agno_agent_framework import execute_task, chat_with_agent
    
    @router.get(f"{prefix}")
    async def list_agents() -> Dict[str, Any]:
        """List all agents."""
        return {
            "agents": agent_manager.list_agents(),
            "statuses": agent_manager.get_agent_statuses()
        }
    
    @router.get(f"{prefix}/{{agent_id}}")
    async def get_agent(agent_id: str) -> Dict[str, Any]:
        """Get agent by ID."""
        agent = agent_manager.get_agent(agent_id)
        if not agent:
            return {"error": "Agent not found"}
        return agent.get_status()
    
    @router.post(f"{prefix}/{{agent_id}}/chat")
    async def chat_agent(agent_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Chat with an agent."""
        agent = agent_manager.get_agent(agent_id)
        if not agent:
            return {"error": "Agent not found"}
        
        message = request.get("message", "")
        context = request.get("context")
        
        response = await chat_with_agent(agent, message, context=context)
        return response
    
    @router.post(f"{prefix}/{{agent_id}}/task")
    async def submit_task(agent_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a task to an agent."""
        agent = agent_manager.get_agent(agent_id)
        if not agent:
            return {"error": "Agent not found"}
        
        task_type = request.get("task_type", "")
        parameters = request.get("parameters", {})
        priority = request.get("priority", 0)
        
        result = await execute_task(agent, task_type, parameters, priority)
        return {"result": result, "status": "completed"}


def create_gateway_endpoints(
    router: APIRouter,
    gateway: Any,
    prefix: str = "/gateway"
) -> None:
    """
    Create LiteLLM Gateway endpoints (high-level convenience).
    
    Args:
        router: APIRouter instance
        gateway: LiteLLMGateway instance
        prefix: URL prefix for gateway endpoints
    
    Example:
        >>> router = create_api_router()
        >>> create_gateway_endpoints(router, gateway, prefix="/api/gateway")
    """
    from ..litellm_gateway import generate_text, generate_embeddings
    
    @router.post(f"{prefix}/generate")
    async def generate(request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text using the gateway."""
        prompt = request.get("prompt", "")
        model = request.get("model", "gpt-4")
        
        text = generate_text(gateway, prompt, model=model)
        return {"text": text, "model": model}
    
    @router.post(f"{prefix}/embed")
    async def embed(request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate embeddings using the gateway."""
        texts = request.get("texts", [])
        model = request.get("model", "text-embedding-3-small")
        
        embeddings = generate_embeddings(gateway, texts, model=model)
        return {"embeddings": embeddings, "model": model}


# ============================================================================
# Utility Functions
# ============================================================================

def add_health_check(
    app: FastAPI,
    path: str = "/health"
) -> None:
    """
    Add a health check endpoint (utility function).
    
    Args:
        app: FastAPI application instance
        path: Health check endpoint path
    
    Example:
        >>> add_health_check(app, path="/health")
    """
    @app.get(path)
    async def health_check() -> Dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy"}


def add_api_versioning(
    app: FastAPI,
    version: str = "v1",
    prefix: str = "/api"
) -> str:
    """
    Set up API versioning (utility function).
    
    Args:
        app: FastAPI application instance
        version: API version
        prefix: API prefix
    
    Returns:
        Versioned API prefix
    
    Example:
        >>> api_prefix = add_api_versioning(app, version="v1")
        >>> # Use api_prefix for all routes
    """
    return f"{prefix}/{version}"


__all__ = [
    # Factory functions
    "create_api_app",
    "create_api_router",
    "configure_api_app",
    # High-level convenience functions
    "register_router",
    "add_endpoint",
    "create_rag_endpoints",
    "create_agent_endpoints",
    "create_gateway_endpoints",
    # Utility functions
    "add_health_check",
    "add_api_versioning",
]

