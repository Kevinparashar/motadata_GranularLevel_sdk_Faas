"""
Prompt Generator Service - Main service implementation.

Handles prompt-based agent and tool creation, feedback collection, and permission management.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException, status

from ....core.litellm_gateway import create_gateway
from ....core.prompt_based_generator import (
    create_agent_from_prompt,
    create_tool_from_prompt,
    get_agent_feedback_stats,
    get_tool_feedback_stats,
    grant_permission,
    rate_agent,
    rate_tool,
)
from ...integrations.codec import create_codec_manager
from ...integrations.nats import create_nats_client
from ...integrations.otel import create_otel_tracer
from ...shared.config import ServiceConfig, load_config
from ...shared.contracts import ServiceResponse, extract_headers
from ...shared.database import get_database_connection
from ...shared.middleware import setup_middleware
from .models import (
    CreateAgentFromPromptRequest,
    CreateToolFromPromptRequest,
    GrantPermissionRequest,
    RateAgentRequest,
    RateToolRequest,
)

logger = logging.getLogger(__name__)


class PromptGeneratorService:
    """
    Prompt Generator Service for creating agents and tools from prompts.

    Provides REST API for:
    - Agent creation from prompts
    - Tool creation from prompts
    - Feedback collection
    - Permission management
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
        Initialize Prompt Generator Service.

        Args:
            config: Service configuration
            db_connection: Database connection
            nats_client: NATS client (optional)
            otel_tracer: OTEL tracer (optional)
            codec_manager: Codec manager (optional)
        """
        self.config = config
        self.db = db_connection
        self.nats_client = nats_client
        self.otel_tracer = otel_tracer
        self.codec_manager = codec_manager or create_codec_manager()

        # Create gateway for LLM calls
        # Note: In production, API keys should come from environment or config
        import os

        api_key = os.getenv("OPENAI_API_KEY", "")
        if api_key:
            self.gateway = create_gateway(api_keys={"openai": api_key})
        else:
            # Gateway will be created per-request if needed
            self.gateway = None

        # Create FastAPI app
        self.app = FastAPI(
            title="Prompt Generator Service",
            description="FaaS service for prompt-based agent and tool creation",
            version=config.service_version,
        )

        # Setup middleware
        setup_middleware(self.app)

        # Register routes
        self._register_routes()

    def _register_routes(self):
        """Register FastAPI routes."""
        self.app.post(
            "/api/v1/prompt/agents",
            response_model=ServiceResponse,
            status_code=status.HTTP_201_CREATED,
        )(self._handle_create_agent_from_prompt)

        self.app.post(
            "/api/v1/prompt/tools",
            response_model=ServiceResponse,
            status_code=status.HTTP_201_CREATED,
        )(self._handle_create_tool_from_prompt)

        self.app.post("/api/v1/prompt/agents/{agent_id}/rate", response_model=ServiceResponse)(
            self._handle_rate_agent
        )

        self.app.post("/api/v1/prompt/tools/{tool_id}/rate", response_model=ServiceResponse)(
            self._handle_rate_tool
        )

        self.app.get("/api/v1/prompt/agents/{agent_id}/feedback", response_model=ServiceResponse)(
            self._handle_get_agent_feedback
        )

        self.app.get("/api/v1/prompt/tools/{tool_id}/feedback", response_model=ServiceResponse)(
            self._handle_get_tool_feedback
        )

        self.app.post("/api/v1/prompt/permissions", response_model=ServiceResponse)(
            self._handle_grant_permission
        )

        self.app.get("/health")(self._handle_health_check)

    async def _handle_create_agent_from_prompt(
        self, request: CreateAgentFromPromptRequest, headers: dict = Header(...)
    ):
        """Create an agent from a natural language prompt."""
        standard_headers = extract_headers(**headers)

        try:
            # Start OTEL span
            if self.otel_tracer:
                with self.otel_tracer.start_span("create_agent_from_prompt") as span:
                    span.set_attribute("tenant_id", standard_headers.tenant_id)
                    span.set_attribute("prompt_length", len(request.prompt))
                    result = await self._create_agent_from_prompt(request, standard_headers)
            else:
                result = await self._create_agent_from_prompt(request, standard_headers)

            return ServiceResponse(
                success=True,
                data=result,
                message="Agent created successfully from prompt",
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )
        except Exception as e:
            logger.error(f"Error creating agent from prompt: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create agent from prompt: {str(e)}",
            )

    async def _handle_create_tool_from_prompt(
        self, request: CreateToolFromPromptRequest, headers: dict = Header(...)
    ):
        """Create a tool from a natural language prompt."""
        standard_headers = extract_headers(**headers)

        try:
            if self.otel_tracer:
                with self.otel_tracer.start_span("create_tool_from_prompt") as span:
                    span.set_attribute("tenant_id", standard_headers.tenant_id)
                    result = await self._create_tool_from_prompt(request, standard_headers)
            else:
                result = await self._create_tool_from_prompt(request, standard_headers)

            return ServiceResponse(
                success=True,
                data=result,
                message="Tool created successfully from prompt",
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )
        except Exception as e:
            logger.error(f"Error creating tool from prompt: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create tool from prompt: {str(e)}",
            )

    async def _handle_rate_agent(  # noqa: S7503
        self, agent_id: str, request: RateAgentRequest, headers: dict = Header(...)
    ):
        """Rate an agent. Async required for FastAPI route handler."""
        standard_headers = extract_headers(**headers)

        try:
            # rate_agent is synchronous, not async
            # user_id is required, provide default if None
            user_id = standard_headers.user_id or standard_headers.tenant_id
            rate_agent(
                agent_id=agent_id,
                rating=request.rating,
                feedback_text=request.feedback,
                tenant_id=standard_headers.tenant_id,
                user_id=user_id,
            )

            return ServiceResponse(
                success=True,
                message="Agent rated successfully",
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )
        except Exception as e:
            logger.error(f"Error rating agent: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to rate agent: {str(e)}",
            )

    async def _handle_rate_tool(  # noqa: S7503
        self, tool_id: str, request: RateToolRequest, headers: dict = Header(...)
    ):
        """Rate a tool. Async required for FastAPI route handler."""
        standard_headers = extract_headers(**headers)

        try:
            # rate_tool is synchronous, not async
            # user_id is required, provide default if None
            user_id = standard_headers.user_id or standard_headers.tenant_id
            rate_tool(
                tool_id=tool_id,
                rating=request.rating,
                feedback_text=request.feedback,
                tenant_id=standard_headers.tenant_id,
                user_id=user_id,
            )

            return ServiceResponse(
                success=True,
                message="Tool rated successfully",
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )
        except Exception as e:
            logger.error(f"Error rating tool: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to rate tool: {str(e)}",
            )

    async def _handle_get_agent_feedback(  # noqa: S7503
        self, agent_id: str, headers: dict = Header(...)
    ):
        """Get feedback statistics for an agent. Async required for FastAPI route handler."""
        standard_headers = extract_headers(**headers)

        try:
            stats = get_agent_feedback_stats(
                agent_id=agent_id,
                tenant_id=standard_headers.tenant_id,
            )

            return ServiceResponse(
                success=True,
                data=stats,
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )
        except Exception as e:
            logger.error(f"Error getting agent feedback: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get agent feedback: {str(e)}",
            )

    async def _handle_get_tool_feedback(  # noqa: S7503
        self, tool_id: str, headers: dict = Header(...)
    ):
        """Get feedback statistics for a tool. Async required for FastAPI route handler."""
        standard_headers = extract_headers(**headers)

        try:
            stats = get_tool_feedback_stats(
                tool_id=tool_id,
                tenant_id=standard_headers.tenant_id,
            )

            return ServiceResponse(
                success=True,
                data=stats,
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )
        except Exception as e:
            logger.error(f"Error getting tool feedback: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get tool feedback: {str(e)}",
            )

    async def _handle_grant_permission(  # noqa: S7503
        self, request: GrantPermissionRequest, headers: dict = Header(...)
    ):
        """Grant permission for a resource. Async required for FastAPI route handler."""
        standard_headers = extract_headers(**headers)

        try:
            grant_permission(
                tenant_id=standard_headers.tenant_id,
                user_id=request.user_id,
                resource_type=request.resource_type,
                resource_id=request.resource_id,
                permission=request.permission,
            )

            return ServiceResponse(
                success=True,
                message="Permission granted successfully",
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )
        except Exception as e:
            logger.error(f"Error granting permission: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to grant permission: {str(e)}",
            )

    async def _handle_health_check(self):  # noqa: S7503
        """Health check endpoint. Async required for FastAPI route handler."""
        return {"status": "healthy", "service": "prompt-generator-service"}

    async def _create_agent_from_prompt(
        self, request: CreateAgentFromPromptRequest, headers: Any
    ) -> Dict[str, Any]:
        """Create agent from prompt."""
        # Create gateway if not already created
        if not self.gateway:
            import os

            api_key = os.getenv("OPENAI_API_KEY", "")
            gateway = create_gateway(api_keys={"openai": api_key}) if api_key else create_gateway()
        else:
            gateway = self.gateway

        agent = await create_agent_from_prompt(
            prompt=request.prompt,
            gateway=gateway,
            agent_id=request.agent_id,
            tenant_id=headers.tenant_id,
            user_id=headers.user_id,
            **request.additional_config or {},
        )

        return {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "description": agent.description,
            "capabilities": [cap.name for cap in agent.capabilities],
            "system_prompt": agent.system_prompt,
            "created_at": agent.created_at.isoformat() if hasattr(agent, "created_at") else "",
        }

    async def _create_tool_from_prompt(
        self, request: CreateToolFromPromptRequest, headers: Any
    ) -> Dict[str, Any]:
        """Create tool from prompt."""
        # Create gateway if not already created
        if not self.gateway:
            import os

            api_key = os.getenv("OPENAI_API_KEY", "")
            gateway = create_gateway(api_keys={"openai": api_key}) if api_key else create_gateway()
        else:
            gateway = self.gateway

        tool = await create_tool_from_prompt(
            prompt=request.prompt,
            gateway=gateway,
            tool_id=request.tool_id,
            tenant_id=headers.tenant_id,
            user_id=headers.user_id,
            **request.additional_config or {},
        )

        return {
            "tool_id": tool.tool_id,
            "name": tool.name,
            "description": tool.description,
            "tool_type": tool.tool_type.value if hasattr(tool.tool_type, "value") else str(tool.tool_type),
            "parameters": [
                {
                    "name": param.name,
                    "type": param.type,
                    "description": param.description,
                    "required": param.required,
                }
                for param in tool.parameters
            ],
            "metadata": tool.metadata,
        }


def create_prompt_generator_service(
    service_name: str = "prompt-generator-service",
    config_overrides: Optional[Dict[str, Any]] = None,
) -> FastAPI:
    """
    Create and configure Prompt Generator Service.

    Args:
        service_name: Service name
        config_overrides: Configuration overrides

    Returns:
        Configured FastAPI application
    """
    config = load_config(service_name, **(config_overrides or {}))
    db_manager = get_database_connection(config.database_url)
    db_connection = db_manager.get_connection()

    # Initialize integrations
    nats_client = create_nats_client() if config.enable_nats else None
    otel_tracer = create_otel_tracer() if config.enable_otel else None

    # Create service
    service = PromptGeneratorService(
        config=config,
        db_connection=db_connection,
        nats_client=nats_client,
        otel_tracer=otel_tracer,
    )

    return service.app
