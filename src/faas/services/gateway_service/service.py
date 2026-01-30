"""
Gateway Service - Main service implementation.

Provides unified LLM access via LiteLLM with rate limiting, caching, and provider management.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException, status
from fastapi.responses import StreamingResponse

from ....core.litellm_gateway import LiteLLMGateway, create_gateway
from ...integrations.codec import create_codec_manager
from ...integrations.nats import create_nats_client
from ...integrations.otel import create_otel_tracer
from ...shared.config import ServiceConfig, load_config
from ...shared.contracts import ServiceResponse, extract_headers
from ...shared.database import get_database_connection
from ...shared.middleware import setup_middleware
from .models import (
    EmbedRequest,
    EmbedResponse,
    GenerateRequest,
    GenerateResponse,
    GenerateStreamRequest,
)

logger = logging.getLogger(__name__)


class GatewayService:
    """
    Gateway Service for unified LLM access.

    Provides REST API for:
    - Text generation
    - Embedding generation
    - Streaming generation
    - Provider management
    - Rate limiting
    """

    def __init__(
        self,
        config: ServiceConfig,
        db_connection: Optional[Any] = None,
        nats_client: Optional[Any] = None,
        otel_tracer: Optional[Any] = None,
        codec_manager: Optional[Any] = None,
    ):
        """
        Initialize Gateway Service.

        Args:
            config: Service configuration
            db_connection: Database connection (optional, for caching)
            nats_client: NATS client (optional)
            otel_tracer: OTEL tracer (optional)
            codec_manager: Codec manager (optional)
        """
        self.config = config
        self.db = db_connection
        self.nats_client = nats_client
        self.otel_tracer = otel_tracer
        self.codec_manager = codec_manager or create_codec_manager()

        # Gateways are created on-demand per request (stateless)
        # No in-memory caching to ensure statelessness

        # Create FastAPI app
        self.app = FastAPI(
            title="Gateway Service",
            description="FaaS service for unified LLM access via LiteLLM",
            version=config.service_version,
        )

        # Setup middleware
        setup_middleware(self.app)

        # Register routes
        self._register_routes()

    def _get_gateway(self, tenant_id: str) -> LiteLLMGateway:
        """
        Create gateway for tenant (stateless - created on-demand).

        Args:
            tenant_id: Tenant ID

        Returns:
            LiteLLMGateway instance
        """
        # Create gateway on-demand (stateless)
        gateway = create_gateway(
            providers=["openai"],
            default_model="gpt-4",
            api_keys={
                "openai": self.config.get("OPENAI_API_KEY", "placeholder")
            },  # Get from config
        )
        return gateway

    def _register_routes(self):
        """Register FastAPI routes."""

        @self.app.post("/api/v1/gateway/generate", response_model=ServiceResponse)
        async def generate(
            request: GenerateRequest,
            headers: dict = Header(...),
        ):
            """Generate text using LLM."""
            standard_headers = extract_headers(**headers)

            span = None
            if self.otel_tracer:
                span = self.otel_tracer.start_span("gateway_generate")
                span.set_attribute("model", request.model or "default")
                span.set_attribute("tenant.id", standard_headers.tenant_id)

            try:
                # Get gateway
                gateway = self._get_gateway(standard_headers.tenant_id)

                # Generate text
                result = await gateway.generate_async(
                    prompt=request.prompt,
                    model=request.model,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    top_p=request.top_p,
                    frequency_penalty=request.frequency_penalty,
                    presence_penalty=request.presence_penalty,
                    stop=request.stop,
                )

                # Publish event via NATS
                if self.nats_client:
                    event = {
                        "event_type": "gateway.generate.completed",
                        "model": result.model,
                        "tokens_used": result.usage.get("total_tokens") if result.usage else None,
                        "tenant_id": standard_headers.tenant_id,
                    }
                    await self.nats_client.publish(
                        f"gateway.events.{standard_headers.tenant_id}",
                        self.codec_manager.encode(event),
                    )

                return ServiceResponse(
                    success=True,
                    data={
                        "text": result.text,
                        "model": result.model,
                        "usage": result.usage,
                        "finish_reason": result.finish_reason,
                    },
                    correlation_id=standard_headers.correlation_id,
                    request_id=standard_headers.request_id,
                )
            except Exception as e:
                logger.error(f"Error generating text: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to generate text: {str(e)}",
                )
            finally:
                if span:
                    span.end()

        @self.app.post("/api/v1/gateway/generate/stream")
        async def generate_stream(
            request: GenerateStreamRequest,
            headers: dict = Header(...),
        ):
            """Generate text with streaming response."""
            standard_headers = extract_headers(**headers)

            try:
                # Get gateway
                gateway = self._get_gateway(standard_headers.tenant_id)

                # Generate stream
                async def stream_generator():
                    async for chunk in gateway.generate_stream_async(
                        prompt=request.prompt,
                        model=request.model,
                        max_tokens=request.max_tokens,
                        temperature=request.temperature,
                    ):
                        yield f"data: {chunk}\n\n"

                return StreamingResponse(stream_generator(), media_type="text/event-stream")
            except Exception as e:
                logger.error(f"Error streaming generation: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to stream generation: {str(e)}",
                )

        @self.app.post("/api/v1/gateway/embeddings", response_model=ServiceResponse)
        async def embed(
            request: EmbedRequest,
            headers: dict = Header(...),
        ):
            """Generate embeddings."""
            standard_headers = extract_headers(**headers)

            span = None
            if self.otel_tracer:
                span = self.otel_tracer.start_span("gateway_embed")
                span.set_attribute("text_count", len(request.texts))
                span.set_attribute("tenant.id", standard_headers.tenant_id)

            try:
                # Get gateway
                gateway = self._get_gateway(standard_headers.tenant_id)

                # Generate embeddings
                result = await gateway.embed_async(
                    texts=request.texts,
                    model=request.model,
                )

                return ServiceResponse(
                    success=True,
                    data={
                        "embeddings": result.embeddings,
                        "model": result.model,
                        "usage": result.usage,
                    },
                    correlation_id=standard_headers.correlation_id,
                    request_id=standard_headers.request_id,
                )
            except Exception as e:
                logger.error(f"Error generating embeddings: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to generate embeddings: {str(e)}",
                )
            finally:
                if span:
                    span.end()

        @self.app.get("/api/v1/gateway/providers", response_model=ServiceResponse)
        async def get_providers(
            headers: dict = Header(...),
        ):
            """Get available LLM providers."""
            standard_headers = extract_headers(**headers)

            # Return available providers
            providers = ["openai", "anthropic", "google", "cohere", "azure", "bedrock"]

            return ServiceResponse(
                success=True,
                data={"providers": providers},
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )

        @self.app.get("/api/v1/gateway/rate-limits", response_model=ServiceResponse)
        async def get_rate_limits(
            headers: dict = Header(...),
        ):
            """Get rate limit information."""
            standard_headers = extract_headers(**headers)

            # TODO: SDK-SVC-002 - Implement rate limit retrieval
            # Placeholder - replace with actual rate limit query implementation
            return ServiceResponse(
                success=True,
                data={"rate_limits": {}},
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "service": "gateway-service"}


def create_gateway_service(
    service_name: str = "gateway-service",
    config_overrides: Optional[Dict[str, Any]] = None,
) -> GatewayService:
    """
    Create Gateway Service instance.

    Args:
        service_name: Service name
        config_overrides: Configuration overrides

    Returns:
        GatewayService instance
    """
    # Load configuration
    config = load_config(service_name, **(config_overrides or {}))

    # Get database connection (optional, for caching)
    db_connection = None
    if config.database_url:
        db_manager = get_database_connection(config.database_url)
        db_connection = db_manager.get_connection()

    # Initialize integrations
    nats_client = create_nats_client() if config.enable_nats else None
    otel_tracer = create_otel_tracer(config.service_name) if config.enable_otel else None

    # Create service
    service = GatewayService(
        config=config,
        db_connection=db_connection,
        nats_client=nats_client,
        otel_tracer=otel_tracer,
    )

    logger.info(f"Gateway Service created: {service_name}")
    return service
