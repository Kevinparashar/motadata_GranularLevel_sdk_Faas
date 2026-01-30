"""
Prompt Service - Main service implementation.

Handles prompt template management and context building.
"""

import logging
from typing import Any, Dict, Optional

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
    ContextResponse,
    CreateTemplateRequest,
    RenderedPromptResponse,
    RenderPromptRequest,
    TemplateResponse,
    UpdateTemplateRequest,
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

        # Prompt managers are created on-demand per request (stateless)
        # No in-memory caching to ensure statelessness

        # Create FastAPI app
        self.app = FastAPI(
            title="Prompt Service",
            description="FaaS service for prompt template management",
            version=config.service_version,
        )

        # Setup middleware
        setup_middleware(self.app)

        # Register routes
        self._register_routes()

    def _get_prompt_manager(self, tenant_id: str) -> PromptContextManager:
        """
        Get or create prompt manager for tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            PromptContextManager instance
        """
        if tenant_id not in self._prompt_managers:
            # Create prompt manager
            prompt_manager = create_prompt_manager(max_tokens=4000)
            self._prompt_managers[tenant_id] = prompt_manager

        return self._prompt_managers[tenant_id]

    def _register_routes(self):
        """Register FastAPI routes."""

        @self.app.post(
            "/api/v1/prompts/templates",
            response_model=ServiceResponse,
            status_code=status.HTTP_201_CREATED,
        )
        async def create_template(
            request: CreateTemplateRequest,
            headers: dict = Header(...),
        ):
            """Create a prompt template."""
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
                # TODO: SDK-SVC-005 - Store template in database
                # Placeholder - replace with actual database storage implementation
                # For now, add to prompt manager
                prompt_manager.add_template(
                    name=request.name,
                    content=request.content,
                    version=request.version or "1.0.0",
                    metadata=request.metadata,
                )

                # Publish event via NATS
                if self.nats_client:
                    event = {
                        "event_type": "prompt.template.created",
                        "template_id": template_id,
                        "tenant_id": standard_headers.tenant_id,
                    }
                    await self.nats_client.publish(
                        f"prompt.events.{standard_headers.tenant_id}",
                        self.codec_manager.encode(event),
                    )

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

        @self.app.get("/api/v1/prompts/templates/{template_id}", response_model=ServiceResponse)
        async def get_template(
            template_id: str,
            headers: dict = Header(...),
            version: Optional[str] = None,
        ):
            """Get template by ID."""
            standard_headers = extract_headers(**headers)

            # TODO: SDK-SVC-005 - Implement template retrieval from database
            # Placeholder - replace with actual database query implementation
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Template retrieval not yet implemented",
            )

        @self.app.post("/api/v1/prompts/render", response_model=ServiceResponse)
        async def render_prompt(
            request: RenderPromptRequest,
            headers: dict = Header(...),
        ):
            """Render a prompt template."""
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

        @self.app.post("/api/v1/prompts/context", response_model=ServiceResponse)
        async def build_context(
            request: BuildContextRequest,
            headers: dict = Header(...),
        ):
            """Build context from messages."""
            standard_headers = extract_headers(**headers)

            try:
                # Get prompt manager
                prompt_manager = self._get_prompt_manager(standard_headers.tenant_id)

                # Build context
                context = prompt_manager.build_context(
                    messages=request.messages,
                    max_tokens=request.max_tokens,
                    system_prompt=request.system_prompt,
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

        @self.app.get("/api/v1/prompts/templates", response_model=ServiceResponse)
        async def list_templates(
            headers: dict = Header(...),
            limit: int = 100,
            offset: int = 0,
        ):
            """List templates."""
            standard_headers = extract_headers(**headers)

            # TODO: SDK-SVC-005 - Implement template listing from database
            # Placeholder - replace with actual database query implementation
            return ServiceResponse(
                success=True,
                data={"templates": [], "total": 0},
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
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
    otel_tracer = create_otel_tracer(config.service_name) if config.enable_otel else None

    # Create service
    service = PromptService(
        config=config,
        db_connection=db_connection,
        nats_client=nats_client,
        otel_tracer=otel_tracer,
    )

    logger.info(f"Prompt Service created: {service_name}")
    return service
