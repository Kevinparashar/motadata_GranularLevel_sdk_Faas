"""
Agent Service - Main service implementation.

Handles agent management, task execution, chat interactions, and memory management.
"""


import logging
import os
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException, status

from ....core.agno_agent_framework import AgentTask, chat_with_agent, create_agent
from ....core.litellm_gateway import create_gateway
from ...integrations.codec import create_codec_manager
from ...integrations.nats import create_nats_client
from ...integrations.otel import create_otel_tracer
from ...shared.agent_storage import AgentStorage
from ...shared.config import ServiceConfig, load_config
from ...shared.contracts import ServiceResponse, extract_headers
from ...shared.exceptions import NotFoundError
from ...shared.http_client import ServiceClientManager
from ...shared.middleware import setup_middleware
from .models import ChatRequest, CreateAgentRequest, ExecuteTaskRequest

logger = logging.getLogger(__name__)


class AgentService:
    """
    Agent Service for managing AI agents.

    Provides REST API for:
    - Agent CRUD operations
    - Task execution
    - Chat interactions
    - Memory management
    - Tool management
    """

    def __init__(
        self,
        config: ServiceConfig,
        db_connection: Any,
        nats_client: Optional[Any] = None,
        otel_tracer: Optional[Any] = None,
        codec_manager: Optional[Any] = None,
    ):
        """
        Initialize Agent Service.
        
        Args:
            config (ServiceConfig): Configuration object or settings.
            db_connection (Any): Input parameter for this operation.
            nats_client (Optional[Any]): Input parameter for this operation.
            otel_tracer (Optional[Any]): Input parameter for this operation.
            codec_manager (Optional[Any]): Input parameter for this operation.
        """
        self.config = config
        self.db = db_connection
        self.nats_client = nats_client
        self.otel_tracer = otel_tracer
        self.codec_manager = codec_manager or create_codec_manager()

        # Create FastAPI app
        self.app = FastAPI(
            title="Agent Service",
            description="FaaS service for AI agent management and execution",
            version=config.service_version,
        )

        # Setup middleware
        setup_middleware(self.app)

        # Initialize agent storage (database-backed, stateless)
        self.agent_storage = AgentStorage(self.db)

        # Initialize service client manager for service-to-service calls
        self.service_clients = ServiceClientManager(self.config)

        # Register routes
        self._register_routes()

    def _register_routes(self):
        """Register FastAPI routes."""
        self.app.post(
            "/api/v1/agents",
            response_model=ServiceResponse,
            status_code=status.HTTP_201_CREATED,
        )(self._handle_create_agent)

        self.app.get("/api/v1/agents/{agent_id}", response_model=ServiceResponse)(
            self._handle_get_agent
        )

        self.app.post("/api/v1/agents/{agent_id}/execute", response_model=ServiceResponse)(
            self._handle_execute_task
        )

        self.app.post("/api/v1/agents/{agent_id}/chat", response_model=ServiceResponse)(
            self._handle_chat
        )

        self.app.get("/api/v1/agents", response_model=ServiceResponse)(self._handle_list_agents)

        self.app.get("/health")(self._handle_health_check)

    async def _handle_create_agent(
        self, request: CreateAgentRequest, headers: dict = Header(...)
    ):
        """
        Create a new agent.
        
        Args:
            request (CreateAgentRequest): Request payload object.
            headers (dict): HTTP headers passed from the caller.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            HTTPException: Raised when this function detects an invalid state or when an underlying call fails.
        """
        standard_headers = extract_headers(**headers)

        # Start OTEL span
        span = None
        if self.otel_tracer:
            span = self.otel_tracer.start_span("create_agent")
            span.set_attribute("agent.name", request.name)
            span.set_attribute("tenant.id", standard_headers.tenant_id)

        try:
            # Generate agent ID if not provided
            agent_id = request.agent_id or f"agent_{standard_headers.request_id[:8]}"

            # Create agent using core SDK
            gateway = self._get_gateway_client(standard_headers.tenant_id)
            agent = create_agent(
                agent_id=agent_id,
                name=request.name,
                description=request.description or "",
                gateway=gateway,
                llm_model=request.llm_model,
                llm_provider=request.llm_provider,
                tenant_id=standard_headers.tenant_id,
            )

            # Set system prompt if provided
            if request.system_prompt:
                agent.system_prompt = request.system_prompt

            # Add capabilities
            for capability in request.capabilities:
                agent.add_capability(capability, f"Capability: {capability}")

            # Store agent in database (stateless)
            await self.agent_storage.save_agent(agent, standard_headers.tenant_id)

            # Publish event via NATS (if enabled)
            if self.nats_client:
                event = {
                    "event_type": "agent.created",
                    "agent_id": agent_id,
                    "tenant_id": standard_headers.tenant_id,
                }
                await self.nats_client.publish(
                    f"agent.events.{standard_headers.tenant_id}",
                    await self.codec_manager.encode(event),
                )

            return ServiceResponse(
                success=True,
                data={
                    "agent_id": agent_id,
                    "name": agent.name,
                    "status": agent.status.value,
                },
                message="Agent created successfully",
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create agent: {str(e)}",
            )
        finally:
            if span:
                span.end()

    async def _handle_get_agent(self, agent_id: str, headers: dict = Header(...)):  # noqa: S7503
        """
        Get agent by ID. Async required for FastAPI route handler.
        
        Args:
            agent_id (str): Input parameter for this operation.
            headers (dict): HTTP headers passed from the caller.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            NotFoundError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        standard_headers = extract_headers(**headers)

        # Load agent from database (stateless)
        gateway = self._get_gateway_client(standard_headers.tenant_id)
        agent = await self.agent_storage.load_agent(agent_id, standard_headers.tenant_id, gateway)
        if not agent:
            raise NotFoundError("agent", agent_id)

        return ServiceResponse(
            success=True,
            data={
                "agent_id": agent.agent_id,
                "name": agent.name,
                "description": agent.description,
                "status": agent.status.value,
                "capabilities": [cap.name for cap in agent.capabilities],
            },
            correlation_id=standard_headers.correlation_id,
            request_id=standard_headers.request_id,
        )

    async def _handle_execute_task(
        self, agent_id: str, request: ExecuteTaskRequest, headers: dict = Header(...)
    ):
        """
        Execute a task with an agent.
        
        Args:
            agent_id (str): Input parameter for this operation.
            request (ExecuteTaskRequest): Request payload object.
            headers (dict): HTTP headers passed from the caller.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            HTTPException: Raised when this function detects an invalid state or when an underlying call fails.
            NotFoundError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        standard_headers = extract_headers(**headers)

        # Load agent from database (stateless)
        gateway = self._get_gateway_client(standard_headers.tenant_id)
        agent = await self.agent_storage.load_agent(agent_id, standard_headers.tenant_id, gateway)
        if not agent:
            raise NotFoundError("agent", agent_id)

        try:
            # Create task
            task = AgentTask(
                task_id=f"task_{standard_headers.request_id[:8]}",
                task_type=request.task_type,
                parameters=request.parameters,
                priority=request.priority,
            )

            # Execute task
            result = await agent.execute_task(task, tenant_id=standard_headers.tenant_id)

            return ServiceResponse(
                success=True,
                data={
                    "task_id": task.task_id,
                    "status": "completed",
                    "result": result,
                },
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )
        except Exception as e:
            logger.error(f"Error executing task: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to execute task: {str(e)}",
            )

    async def _handle_chat(self, agent_id: str, request: ChatRequest, headers: dict = Header(...)):
        """
        Chat with an agent.
        
        Args:
            agent_id (str): Input parameter for this operation.
            request (ChatRequest): Request payload object.
            headers (dict): HTTP headers passed from the caller.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            HTTPException: Raised when this function detects an invalid state or when an underlying call fails.
            NotFoundError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        standard_headers = extract_headers(**headers)

        # Load agent from database (stateless)
        gateway = self._get_gateway_client(standard_headers.tenant_id)
        agent = await self.agent_storage.load_agent(agent_id, standard_headers.tenant_id, gateway)
        if not agent:
            raise NotFoundError("agent", agent_id)

        try:
            # Chat with agent using chat_with_agent function
            response = await chat_with_agent(
                agent=agent,
                message=request.message,
                session_id=request.session_id,
                tenant_id=standard_headers.tenant_id,
            )

            return ServiceResponse(
                success=True,
                data={
                    "session_id": response.get("session_id"),
                    "message": response.get("answer"),
                    "metadata": response.get("result"),
                },
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to chat: {str(e)}",
            )

    async def _handle_list_agents(  # noqa: S7503
        self, headers: dict = Header(...), limit: int = 100, offset: int = 0
    ):
        """
        List all agents. Async required for FastAPI route handler.
        
        Args:
            headers (dict): HTTP headers passed from the caller.
            limit (int): Input parameter for this operation.
            offset (int): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        """
        standard_headers = extract_headers(**headers)

        # Load agents from database (stateless)
        agents = await self.agent_storage.list_agents(
            standard_headers.tenant_id, limit=limit, offset=offset
        )

        return ServiceResponse(
            success=True,
            data={
                "agents": agents,
                "total": len(agents),
            },
            correlation_id=standard_headers.correlation_id,
            request_id=standard_headers.request_id,
        )

    async def _handle_health_check(self):  # noqa: S7503
        """
        Health check endpoint. Async required for FastAPI route handler.
        
        Returns:
            Any: Result of the operation.
        """
        return {"status": "healthy", "service": "agent-service"}

    def _get_gateway_client(self, tenant_id: str):  # noqa: S1172
        """
        Get gateway client for LLM calls.
        
        Uses Gateway Service via HTTP if configured, otherwise falls back to direct SDK.
        
        Args:
            tenant_id (str): Tenant identifier used for tenant isolation.
        
        Returns:
            Any: Result of the operation.
        """
        # Try to use Gateway Service via HTTP if configured
        gateway_client = self.service_clients.get_client("gateway")
        if gateway_client:
            # Return a wrapper that uses HTTP client for Gateway Service calls
            # For now, fall back to direct SDK for simplicity
            # In production, you could create a GatewayServiceClient wrapper
            pass

        # Fallback to direct SDK (for development or when Gateway Service not available)
        # In production, this should use Gateway Service via HTTP
        # Get API key from environment variable
        openai_api_key = os.getenv("OPENAI_API_KEY", "")
        gateway = create_gateway(
            api_keys={"openai": openai_api_key}, default_model="gpt-4"
        )
        return gateway


def create_agent_service(
    service_name: str = "agent-service",
    config_overrides: Optional[Dict[str, Any]] = None,
) -> AgentService:
    """
    Create Agent Service instance.

    Args:
        service_name: Service name
        config_overrides: Configuration overrides

    Returns:
        AgentService instance
    """
    # Load configuration
    config = load_config(service_name, **(config_overrides or {}))

    # Get database connection (direct connection for stateless services)
    import asyncio
    from ....core.postgresql_database.connection import DatabaseConfig, DatabaseConnection

    # Parse database URL and create connection
    db_config = DatabaseConfig.from_env()
    db_connection = DatabaseConnection(db_config)
    
    # Connect to database (async method called from sync factory function)
    # This factory is typically called at startup before event loop is running
    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, we can't use run_until_complete
            # Connection will be established on first async operation
            import warnings
            warnings.warn(
                "Database connection called from running event loop. "
                "Connection will be established on first use.",
                RuntimeWarning
            )
        else:
            # Use existing loop
            loop.run_until_complete(db_connection.connect())
    except RuntimeError:
        # No event loop exists, create a new one
        asyncio.run(db_connection.connect())

    # Initialize integrations
    nats_client = create_nats_client() if config.enable_nats else None
    otel_tracer = create_otel_tracer(config.service_name) if config.enable_otel else None

    # Create service
    service = AgentService(
        config=config,
        db_connection=db_connection,
        nats_client=nats_client,
        otel_tracer=otel_tracer,
    )

    logger.info(f"Agent Service created: {service_name}")
    return service
