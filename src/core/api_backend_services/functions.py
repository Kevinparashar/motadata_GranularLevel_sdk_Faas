"""
API Backend Services - High-Level Functions

Factory functions, convenience functions, and utilities for API backend services.
"""


from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Constants
AGENT_NOT_FOUND_ERROR = "Agent not found"

# ============================================================================
# Factory Functions
# ============================================================================


def create_api_app(
    title: str = "Motadata AI SDK API",
    version: str = "0.1.0",
    description: str = "RESTful API for Motadata Python AI SDK",
    enable_cors: bool = True,
    cors_origins: Optional[List[str]] = None,
    **kwargs: Any,
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
    app = FastAPI(title=title, version=version, description=description, **kwargs)

    if enable_cors:
        origins: List[str] = cors_origins if cors_origins is not None else ["*"]
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    return app


def create_api_router(
    prefix: str = "", tags: Optional[List[str]] = None, **kwargs: Any
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
    # FastAPI accepts list[str | Enum] | None, but we only use str
    # Type ignore needed due to FastAPI's type system
    tags_list: List[str] = tags if tags is not None else []
    return APIRouter(prefix=prefix, tags=tags_list if tags_list else None, **kwargs)  # type: ignore[arg-type]


def configure_api_app(
    app: FastAPI, enable_cors: bool = True, cors_origins: Optional[List[str]] = None, **kwargs: Any
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


def register_router(app: FastAPI, router: APIRouter, prefix: Optional[str] = None) -> None:
    """
    Register a router with the FastAPI app (high-level convenience).
    
    Example:
                            >>> router = create_api_router(prefix="/api/v1")
                            >>> register_router(app, router)
    
    Args:
        app (FastAPI): Input parameter for this operation.
        router (APIRouter): Input parameter for this operation.
        prefix (Optional[str]): Input parameter for this operation.
    
    Returns:
        None: Result of the operation.
    """
    if prefix:
        app.include_router(router, prefix=prefix)
    else:
        app.include_router(router)


def add_endpoint(
    router: APIRouter,
    path: str,
    method: str = "GET",
    handler: Optional[Callable] = None,
    **kwargs: Any,
) -> None:
    """
    Add an endpoint to a router (high-level convenience).
    
    Example:
                            >>> def get_status():
                            ...     return {"status": "ok"}
                            >>> add_endpoint(router, "/status", "GET", get_status)
    
    Args:
        router (APIRouter): Input parameter for this operation.
        path (str): Input parameter for this operation.
        method (str): Input parameter for this operation.
        handler (Optional[Callable]): Input parameter for this operation.
        **kwargs (Any): Input parameter for this operation.
    
    Returns:
        None: Result of the operation.
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


def create_rag_endpoints(router: APIRouter, rag_system: Any, prefix: str = "/rag") -> None:
    """
    Create RAG system endpoints (high-level convenience).
    
    Example:
                            >>> router = create_api_router()
                            >>> create_rag_endpoints(router, rag_system, prefix="/api/rag")
    
    Args:
        router (APIRouter): Input parameter for this operation.
        rag_system (Any): Input parameter for this operation.
        prefix (str): Input parameter for this operation.
    
    Returns:
        None: Result of the operation.
    """
    from ..rag import ingest_document_simple, quick_rag_query

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
            metadata=request.get("metadata"),
        )
        return {"document_id": doc_id, "status": "success"}


def create_agent_endpoints(router: APIRouter, agent_manager: Any, prefix: str = "/agents") -> None:
    """
    Create agent framework endpoints (high-level convenience).
    
    Example:
                            >>> router = create_api_router()
                            >>> create_agent_endpoints(router, agent_manager, prefix="/api/agents")
    
    Args:
        router (APIRouter): Input parameter for this operation.
        agent_manager (Any): Input parameter for this operation.
        prefix (str): Input parameter for this operation.
    
    Returns:
        None: Result of the operation.
    """
    from ..agno_agent_framework import chat_with_agent, execute_task

    @router.get(f"{prefix}")
    async def list_agents() -> Dict[str, Any]:
        """List all agents."""
        return {
            "agents": agent_manager.list_agents(),
            "statuses": agent_manager.get_agent_statuses(),
        }

    @router.get(f"{prefix}/{{agent_id}}")
    async def get_agent(agent_id: str) -> Dict[str, Any]:
        """Get agent by ID."""
        agent = agent_manager.get_agent(agent_id)
        if not agent:
            return {"error": AGENT_NOT_FOUND_ERROR}
        return agent.get_status()

    @router.post(f"{prefix}/{{agent_id}}/chat")
    async def chat_agent(agent_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Chat with an agent."""
        agent = agent_manager.get_agent(agent_id)
        if not agent:
            return {"error": AGENT_NOT_FOUND_ERROR}

        message = request.get("message", "")
        context = request.get("context")

        response = await chat_with_agent(agent, message, context=context)
        return response

    @router.post(f"{prefix}/{{agent_id}}/task")
    async def submit_task(agent_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a task to an agent."""
        agent = agent_manager.get_agent(agent_id)
        if not agent:
            return {"error": AGENT_NOT_FOUND_ERROR}

        task_type = request.get("task_type", "")
        parameters = request.get("parameters", {})
        priority = request.get("priority", 0)

        result = await execute_task(agent, task_type, parameters, priority)
        return {"result": result, "status": "completed"}


def _determine_processing_mode(mode: str, query: str) -> tuple[bool, bool]:
    """
    Determine whether to use RAG and/or Agent based on mode and query.
    
    Args:
        mode (str): Input parameter for this operation.
        query (str): Input parameter for this operation.
    
    Returns:
        tuple[bool, bool]: True if the operation succeeds, else False.
    """
    use_rag = mode in ["rag", "both", "auto"]
    use_agent = mode in ["agent", "both", "auto"]

    if mode == "auto":
        knowledge_indicators = [
            "what",
            "how",
            "explain",
            "tell me",
            "describe",
            "who",
            "when",
            "where",
        ]
        if any(query.lower().startswith(indicator) for indicator in knowledge_indicators):
            use_rag = True
            use_agent = False
        else:
            use_agent = True
            use_rag = False

    return use_rag, use_agent


def _process_rag_query(
    rag_system: Any, query: str, request: Dict[str, Any], tenant_id: Optional[str]
) -> Dict[str, Any]:
    """
    Process query with RAG system.
    
    Args:
        rag_system (Any): Input parameter for this operation.
        query (str): Input parameter for this operation.
        request (Dict[str, Any]): Request payload object.
        tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
    
    Returns:
        Dict[str, Any]: Dictionary result of the operation.
    """
    from ..rag import quick_rag_query

    try:
        rag_result = quick_rag_query(
            rag_system,
            query=query,
            top_k=request.get("top_k", 5),
            threshold=request.get("threshold", 0.7),
            tenant_id=tenant_id,
        )
        return {
            "rag_response": {
                "answer": rag_result.get("answer"),
                "sources": rag_result.get("sources", []),
                "num_documents": rag_result.get("num_documents", 0),
                "memory_used": rag_result.get("memory_used", 0),
            }
        }
    except Exception as e:
        return {"rag_error": str(e)}


async def _process_agent_query(
    agent_manager: Any,
    query: str,
    request: Dict[str, Any],
    tenant_id: Optional[str],
    rag_context: Optional[str],
) -> Dict[str, Any]:
    """
    Process query with Agent system.
    
    Args:
        agent_manager (Any): Input parameter for this operation.
        query (str): Input parameter for this operation.
        request (Dict[str, Any]): Request payload object.
        tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        rag_context (Optional[str]): Input parameter for this operation.
    
    Returns:
        Dict[str, Any]: Dictionary result of the operation.
    """
    from ..agno_agent_framework import chat_with_agent

    try:
        agent_id = request.get("agent_id")
        if not agent_id:
            agents = agent_manager.list_agents() if agent_manager else []
            agent_id = agents[0] if agents else None

        if not agent_id:
            return {"agent_error": "No agent available"}

        agent = agent_manager.get_agent(agent_id)
        if not agent:
            return {"agent_error": f"Agent {agent_id} not found"}

        # Convert string context to dict format expected by chat_with_agent
        context_dict = {"rag_context": rag_context} if rag_context else None
        agent_response = await chat_with_agent(
            agent, message=query, context=context_dict, tenant_id=tenant_id
        )
        return {"agent_response": agent_response}
    except Exception as e:
        return {"agent_error": str(e)}


def _determine_final_answer(result: Dict[str, Any], use_rag: bool, use_agent: bool) -> str:
    """
    Determine final answer from RAG and/or Agent responses.
    
    Args:
        result (Dict[str, Any]): Input parameter for this operation.
        use_rag (bool): Input parameter for this operation.
        use_agent (bool): Input parameter for this operation.
    
    Returns:
        str: Returned text value.
    """
    if use_rag and "rag_response" in result:
        return result["rag_response"]["answer"]
    elif use_agent and "agent_response" in result:
        return result["agent_response"].get("answer", "")
    elif "combined_answer" in result:
        return result["combined_answer"]
    else:
        return "Unable to process query"


def create_unified_query_endpoint(
    router: APIRouter, agent_manager: Any, rag_system: Any, prefix: str = "/query"
) -> None:
    """
    Create unified query endpoint that orchestrates Agent and RAG.
    
    This endpoint automatically determines whether to use Agent or RAG
                        based on the query and provides a single entry point for all queries.
    
                        Example:
                            >>> router = create_api_router()
                            >>> create_unified_query_endpoint(
                            ...     router, agent_manager, rag_system, prefix="/api/query"
                            ... )
    
    Args:
        router (APIRouter): Input parameter for this operation.
        agent_manager (Any): Input parameter for this operation.
        rag_system (Any): Input parameter for this operation.
        prefix (str): Input parameter for this operation.
    
    Returns:
        None: Result of the operation.
    """

    @router.post(f"{prefix}")
    async def unified_query(request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Unified query endpoint that orchestrates Agent and RAG.

        Automatically determines the best processing path:
        - Uses RAG for knowledge base queries
        - Uses Agent for complex tasks and workflows
        - Can use both for comprehensive responses
        """
        query = request.get("query", "")
        tenant_id = request.get("tenant_id")
        user_id = request.get("user_id")
        conversation_id = request.get("conversation_id")
        mode = request.get("mode", "auto")

        use_rag, use_agent = _determine_processing_mode(mode, query)

        result = {
            "query": query,
            "mode": mode,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "conversation_id": conversation_id,
        }

        if use_rag:
            result.update(_process_rag_query(rag_system, query, request, tenant_id))

        if use_agent:
            rag_context = result.get("rag_response", {}).get("answer") if use_rag else None
            result.update(
                await _process_agent_query(agent_manager, query, request, tenant_id, rag_context)
            )

        if use_rag and use_agent:
            rag_answer = result.get("rag_response", {}).get("answer", "")
            agent_answer = result.get("agent_response", {}).get("answer", "")
            result["combined_answer"] = f"{rag_answer}\n\n{agent_answer}"

        result["answer"] = _determine_final_answer(result, use_rag, use_agent)
        return result


def create_gateway_endpoints(router: APIRouter, gateway: Any, prefix: str = "/gateway") -> None:
    """
    Create LiteLLM Gateway endpoints (high-level convenience).
    
    Example:
                            >>> router = create_api_router()
                            >>> create_gateway_endpoints(router, gateway, prefix="/api/gateway")
    
    Args:
        router (APIRouter): Input parameter for this operation.
        gateway (Any): Gateway client used for LLM calls.
        prefix (str): Input parameter for this operation.
    
    Returns:
        None: Result of the operation.
    """
    from ..litellm_gateway import generate_embeddings, generate_text

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


def add_health_check(app: FastAPI, path: str = "/health") -> None:  # noqa: ARG001
    """
    Add a health check endpoint (utility function).
    
    Example:
                            >>> add_health_check(app, path="/health")
    
    Args:
        app (FastAPI): Input parameter for this operation.
        path (str): Input parameter for this operation.
    
    Returns:
        None: Result of the operation.
    """

    @app.get(path)
    async def health_check() -> Dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy"}


def add_api_versioning(version: str = "v1", prefix: str = "/api") -> str:
    """
    Set up API versioning (utility function).

    Args:
        version: API version
        prefix: API prefix

    Returns:
        Versioned API prefix

    Example:
        >>> api_prefix = add_api_versioning(version="v1")
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
