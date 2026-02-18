"""
Prompt Service - Main service implementation.

Handles prompt template management and context building.
"""


import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException, status

from ....core.prompt_context_management import create_prompt_manager
from ....core.prompt_context_management.prompt_manager import PromptContextManager
from ...integrations.codec import create_codec_manager
from ...integrations.nats import create_nats_client
from ...integrations.otel import create_otel_tracer
from ...shared.config import ServiceConfig, load_config
from ...shared.contracts import ServiceResponse, extract_headers
from ...shared.database import get_database_connection
from ...shared.middleware import setup_middleware
from .models import (
    BuildContextRequest,
    CreateTemplateRequest,
    RenderPromptRequest,
)

logger = logging.getLogger(__name__)


class PromptService:
    """
    Prompt Service for prompt template management.

    Provides REST API for:
    - Template CRUD operations
    - Prompt rendering
    - Context building
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
        Initialize Prompt Service.
        
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

        # Prompt managers are created on-demand per request (stateless)
        # No in-memory caching to ensure statelessness
        # Note: _prompt_managers is not used - managers are created fresh each time

        # Create FastAPI app
        self.app = FastAPI(
            title="Prompt Service",
            description="FaaS service for prompt template management",
            version=config.service_version,
        )

        # Setup middleware
        setup_middleware(self.app)

        # Register startup event to ensure database connection is ready
        @self.app.on_event("startup")
        async def startup_event():
            """Ensure database connection is ready on service startup."""
            if hasattr(self.db, "connect"):
                await self.db.connect()

        # Register routes
        self._register_routes()

    def _get_prompt_manager(self, tenant_id: str) -> PromptContextManager:  # noqa: S1172
        """
        Create prompt manager for tenant (stateless - created on-demand).
        
        Args:
            tenant_id (str): Tenant identifier used for tenant isolation.
        
        Returns:
            PromptContextManager: Result of the operation.
        """
        # Create prompt manager on-demand (stateless)
        # tenant_id is reserved for future multi-tenant support
        return create_prompt_manager(max_tokens=4000)

    def _register_routes(self):
        """Register FastAPI routes."""
        self.app.post(
            "/api/v1/prompts/templates",
            response_model=ServiceResponse,
            status_code=status.HTTP_201_CREATED,
        )(self._handle_create_template)

        self.app.get("/api/v1/prompts/templates/{template_id}", response_model=ServiceResponse)(
            self._handle_get_template
        )

        self.app.post("/api/v1/prompts/render", response_model=ServiceResponse)(
            self._handle_render_prompt
        )

        self.app.post("/api/v1/prompts/context", response_model=ServiceResponse)(
            self._handle_build_context
        )

        self.app.get("/api/v1/prompts/templates", response_model=ServiceResponse)(
            self._handle_list_templates
        )

        self.app.get("/health")(self._handle_health_check)

    async def _handle_create_template(
        self, request: CreateTemplateRequest, headers: dict = Header(...)
    ):
        """
        Create a prompt template.
        
        Args:
            request (CreateTemplateRequest): Request payload object.
            headers (dict): HTTP headers passed from the caller.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            HTTPException: Raised when this function detects an invalid state or when an underlying call fails.
        """
        standard_headers = extract_headers(**headers)

        span = None
        if self.otel_tracer:
            span = self.otel_tracer.start_span("create_template")
            span.set_attribute("template.name", request.name)
            span.set_attribute("tenant.id", standard_headers.tenant_id)

        try:
            # Get prompt manager
            prompt_manager = self._get_prompt_manager(standard_headers.tenant_id)

            # Generate template ID if not provided
            template_id = request.template_id or f"template_{standard_headers.request_id[:8]}"

            # Create template
            # Template storage in database - to be implemented
            # For now, add to prompt manager
            prompt_manager.add_template(
                name=request.name,
                content=request.content,
                version=request.version or "1.0.0",
                metadata=request.metadata,
            )

            # Publish event via NATS
            if self.nats_client:
                await self._publish_template_event(template_id, standard_headers.tenant_id)

            return ServiceResponse(
                success=True,
                data={
                    "template_id": template_id,
                    "name": request.name,
                    "version": request.version or "1.0.0",
                },
                message="Template created successfully",
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )
        except Exception as e:
            logger.error(f"Error creating template: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create template: {str(e)}",
            )
        finally:
            if span:
                span.end()

    async def _publish_template_event(self, template_id: str, tenant_id: str) -> None:
        """
        Publish template creation event via NATS.
        
        Args:
            template_id (str): Input parameter for this operation.
            tenant_id (str): Tenant identifier used for tenant isolation.
        
        Returns:
            None: Result of the operation.
        """
        event = {
            "event_type": "prompt.template.created",
            "template_id": template_id,
            "tenant_id": tenant_id,
        }
        await self.nats_client.publish(
            f"prompt.events.{tenant_id}",
            await self.codec_manager.encode(event),
        )

    async def _handle_get_template(  # noqa: S7503
        self, template_id: str, headers: dict = Header(...), version: Optional[str] = None  # noqa: ARG002
    ):
        """
        Get template by ID. Async required for FastAPI route handler.
        
        Args:
            template_id (str): Input parameter for this operation.
            headers (dict): HTTP headers passed from the caller.
            version (Optional[str]): Input parameter for this operation.
        
        Raises:
            HTTPException: Raised when this function detects an invalid state or when an underlying call fails.
        """
        extract_headers(**headers)  # Extract headers for validation

        # Template retrieval from database - to be implemented
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Template retrieval not yet implemented",
        )

    async def _handle_render_prompt(  # noqa: S7503
        self, request: RenderPromptRequest, headers: dict = Header(...)
    ):
        """
        Render a prompt template. Async required for FastAPI route handler.
        
        Args:
            request (RenderPromptRequest): Request payload object.
            headers (dict): HTTP headers passed from the caller.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            HTTPException: Raised when this function detects an invalid state or when an underlying call fails.
        """
        standard_headers = extract_headers(**headers)

        try:
            # Get prompt manager
            prompt_manager = self._get_prompt_manager(standard_headers.tenant_id)

            # Render prompt
            rendered = prompt_manager.render(
                template_name=request.template_name,
                variables=request.variables,
                version=request.version,
            )

            return ServiceResponse(
                success=True,
                data={
                    "rendered_prompt": rendered,
                    "template_name": request.template_name,
                    "variables_used": request.variables,
                },
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )
        except Exception as e:
            logger.error(f"Error rendering prompt: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to render prompt: {str(e)}",
            )

    async def _handle_build_context(  # noqa: S7503
        self, request: BuildContextRequest, headers: dict = Header(...)
    ):
        """
        Build context from messages. Async required for FastAPI route handler.
        
        Args:
            request (BuildContextRequest): Request payload object.
            headers (dict): HTTP headers passed from the caller.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            HTTPException: Raised when this function detects an invalid state or when an underlying call fails.
        """
        standard_headers = extract_headers(**headers)

        try:
            # Get prompt manager
            prompt_manager = self._get_prompt_manager(standard_headers.tenant_id)

            # Build context from messages
            message_list = self._prepare_messages(request.messages, request.system_prompt)

            # Use window.build_context which takes List[str] and max_tokens
            context = prompt_manager.window.build_context(
                messages=message_list,
                max_tokens=request.max_tokens,
            )

            return ServiceResponse(
                success=True,
                data={
                    "context": context,
                    "token_count": len(context.split()),  # Simplified
                    "messages_included": len(request.messages),
                },
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )
        except Exception as e:
            logger.error(f"Error building context: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to build context: {str(e)}",
            )

    def _prepare_messages(
        self, messages: Any, system_prompt: Optional[str]
    ) -> List[str]:
        """
        Prepare messages list for context building.
        
        Args:
            messages (Any): Chat messages in role/content format.
            system_prompt (Optional[str]): System prompt used to guide behaviour.
        
        Returns:
            List[str]: List result of the operation.
        """
        # Convert messages to list of strings if needed
        message_list = (
            messages if isinstance(messages, list) else [str(messages)]
        )
        # Add system prompt if provided
        if system_prompt:
            message_list = [system_prompt] + message_list
        return message_list

    async def _handle_list_templates(  # noqa: S7503
        self, headers: dict = Header(...), limit: int = 100, offset: int = 0  # noqa: ARG002
    ):
        """
        List templates. Async required for FastAPI route handler.
        
        Args:
            headers (dict): HTTP headers passed from the caller.
            limit (int): Input parameter for this operation.
            offset (int): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        """
        standard_headers = extract_headers(**headers)

        # Template listing from database - to be implemented
        # For now, return placeholder response
        return ServiceResponse(
            success=True,
            data={"templates": [], "total": 0},
            correlation_id=standard_headers.correlation_id,
            request_id=standard_headers.request_id,
        )

    async def _handle_health_check(self):  # noqa: S7503
        """
        Health check endpoint. Async required for FastAPI route handler.
        
        Returns:
            Any: Result of the operation.
        """
        return {"status": "healthy", "service": "prompt-service"}


def create_prompt_service(
    service_name: str = "prompt-service",
    config_overrides: Optional[Dict[str, Any]] = None,
) -> PromptService:
    """
    Create Prompt Service instance.

    Args:
        service_name: Service name
        config_overrides: Configuration overrides

    Returns:
        PromptService instance
    """
    # Load configuration
    config = load_config(service_name, **(config_overrides or {}))

    # Get database connection
    db_manager = get_database_connection(config.database_url)
    db_connection = db_manager.get_connection()

    # Initialize integrations
    nats_client = create_nats_client() if config.enable_nats else None
    otel_tracer = create_otel_tracer() if config.enable_otel else None

    # Create service
    service = PromptService(
        config=config,
        db_connection=db_connection,
        nats_client=nats_client,
        otel_tracer=otel_tracer,
    )

    logger.info(f"Prompt Service created: {service_name}")
    return service
