"""
Orchestrator Service - Main service implementation.

Provides intelligent query routing and unified caching for all AI features.
"""

import logging
import os
from typing import Any, Optional

from fastapi import FastAPI, Header, HTTPException, status

from ....core.cache_mechanism import CacheConfig, CacheMechanism
from ....core.litellm_gateway import create_gateway
from ...integrations.codec import create_codec_manager
from ...orchestrator import (
    create_cache_manager,
    create_query_router,
    create_service_selector,
)
from ...shared.config import ServiceConfig
from ...shared.contracts import extract_headers
from ...shared.http_client import ServiceClientManager, ServiceClientError
from ...shared.middleware import setup_middleware
from .models import (
    CacheInvalidateRequest,
    CacheInvalidateResponse,
    IntentAnalysisRequest,
    IntentAnalysisResponse,
    OrchestrateRequest,
    OrchestrateResponse,
)

logger = logging.getLogger(__name__)


class OrchestratorService:
    """
    Orchestrator Service for intelligent query routing and unified caching.

    Provides:
    - Intelligent query intent analysis
    - Automatic service routing
    - Unified caching across all AI features
    - Single entry point for all AI operations
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
        Initialize Orchestrator Service.

        Args:
            config: Service configuration
            db_connection: Database connection
            nats_client: Optional NATS client
            otel_tracer: Optional OTEL tracer
            codec_manager: Optional codec manager
        """
        self.config = config
        self.db = db_connection
        self.nats_client = nats_client
        self.otel_tracer = otel_tracer
        self.codec_manager = codec_manager or create_codec_manager()

        # Create FastAPI app
        self.app = FastAPI(
            title="Orchestrator Service",
            description="AI entry point with intelligent routing and unified caching",
            version=config.service_version,
        )

        # Setup middleware
        setup_middleware(self.app)

        # Initialize cache mechanism
        # Auto-detect backend: use Dragonfly if URL is provided, otherwise use memory
        cache_backend = "dragonfly" if config.dragonfly_url else "memory"
        cache_config = CacheConfig(
            backend=cache_backend,
            default_ttl=300,
            max_size=2048,
            dragonfly_url=config.dragonfly_url,
            namespace="orchestrator",
        )
        logger.info(f"Initializing orchestrator cache with backend: {cache_backend}")
        if cache_backend == "dragonfly":
            logger.info(f"Dragonfly URL: {config.dragonfly_url}")
        self.cache_mechanism = CacheMechanism(
            config=cache_config,
            otel_tracer=self.otel_tracer,
        )

        # Initialize cache manager
        self.cache_manager = create_cache_manager(
            cache=self.cache_mechanism,
            cache_config=cache_config,
        )

        # Initialize gateway for intent classification
        openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.gateway = create_gateway(
            providers=["openai"],
            default_model="gpt-4",
            api_keys={"openai": openai_api_key},
        )

        # Initialize query router
        self.query_router = create_query_router(
            gateway=self.gateway,
            enable_llm_classification=True,
            cache=self.cache_mechanism,
        )

        # Initialize service selector
        self.service_selector = create_service_selector(config=self.config)

        # Initialize service client manager
        self.service_clients = ServiceClientManager(self.config)

        # Register routes
        self._register_routes()

    def _register_routes(self):
        """Register FastAPI routes."""
        self.app.post("/api/v1/orchestrate", response_model=OrchestrateResponse)(
            self._handle_orchestrate
        )

        self.app.post("/api/v1/intent/analyze", response_model=IntentAnalysisResponse)(
            self._handle_analyze_intent
        )

        self.app.post("/api/v1/cache/invalidate", response_model=CacheInvalidateResponse)(
            self._handle_invalidate_cache
        )

        self.app.get("/health")(self._handle_health_check)

    async def _handle_orchestrate(
        self, request: OrchestrateRequest, headers: dict = Header(...)
    ):
        """
        Orchestrate a query - route to appropriate service.

        Args:
            request: Orchestration request
            headers: HTTP headers

        Returns:
            Orchestration response
        """
        standard_headers = extract_headers(**headers)

        # Start OTEL trace
        span = None
        if self.otel_tracer:
            span = self.otel_tracer.start_trace("orchestrator.orchestrate")
            span.set_attribute("orchestrator.query", request.query[:100])
            span.set_attribute("tenant.id", standard_headers.tenant_id)

        try:
            # Check cache first
            cached_response = None
            if request.cache_enabled:
                cached_response = await self.cache_manager.get(
                    feature=request.intent or "unknown",
                    query=request.query,
                    tenant_id=standard_headers.tenant_id,
                    context=request.context,
                )

                if cached_response:
                    logger.info(f"Cache hit for query: {request.query[:50]}")
                    if span:
                        span.set_attribute("orchestrator.cached", True)
                    return OrchestrateResponse(
                        success=True,
                        data=cached_response.get("data"),
                        intent=cached_response.get("intent", "unknown"),
                        service=cached_response.get("service", "unknown"),
                        endpoint=cached_response.get("endpoint", ""),
                        cached=True,
                        message="Response served from cache",
                        correlation_id=standard_headers.correlation_id,
                        request_id=standard_headers.request_id,
                        metadata=cached_response.get("metadata", {}),
                    )

            # Analyze intent if not provided
            intent_result = None
            if request.intent:
                intent_result = {
                    "intent": request.intent,
                    "confidence": 1.0,
                    "reasoning": "Explicit intent provided",
                }
            else:
                intent_result = await self.query_router.analyze_intent(
                    query=request.query,
                    tenant_id=standard_headers.tenant_id,
                    context=request.context,
                )

            intent = intent_result.get("intent", "unknown")
            if span:
                span.set_attribute("orchestrator.intent", intent)
                span.set_attribute("orchestrator.confidence", intent_result.get("confidence", 0.0))

            # Select service
            routing_config = self.service_selector.select_service(
                intent=intent,
                query=request.query,
                context=request.context,
                tenant_id=standard_headers.tenant_id,
            )

            service_name = routing_config["service"]
            endpoint = routing_config["endpoint"]
            payload = routing_config["payload"]

            if span:
                span.set_attribute("orchestrator.service", service_name)
                span.set_attribute("orchestrator.endpoint", endpoint)

            # Route to service
            service_client = self.service_clients.get_client(service_name)
            if not service_client:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Service {service_name} is not available",
                )

            # Add standard headers to payload
            headers_dict = {
                "X-Tenant-ID": standard_headers.tenant_id,
                "X-User-ID": standard_headers.user_id or "",
                "X-Correlation-ID": standard_headers.correlation_id,
                "X-Request-ID": standard_headers.request_id,
            }

            # Call service
            try:
                response = await service_client.post(
                    endpoint=endpoint,
                    headers=headers_dict,
                    json_data=payload,
                )

                response_data = response.get("data", {})
                if span:
                    span.set_attribute("orchestrator.service_response.success", response.get("success", False))

                # Cache response if enabled
                if request.cache_enabled:
                    cache_value = {
                        "data": response_data,
                        "intent": intent,
                        "service": service_name,
                        "endpoint": endpoint,
                        "metadata": response.get("metadata", {}),
                    }
                    await self.cache_manager.set(
                        feature=intent,
                        query=request.query,
                        value=cache_value,
                        tenant_id=standard_headers.tenant_id,
                        context=request.context,
                    )

                return OrchestrateResponse(
                    success=response.get("success", True),
                    data=response_data,
                    intent=intent,
                    service=service_name,
                    endpoint=endpoint,
                    cached=False,
                    message=response.get("message"),
                    correlation_id=standard_headers.correlation_id,
                    request_id=standard_headers.request_id,
                    metadata=response.get("metadata", {}),
                )

            except ServiceClientError as e:
                logger.error(f"Service call failed: {e}")
                if span:
                    span.record_exception(e)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Service {service_name} call failed: {str(e)}",
                )

        except Exception as e:
            logger.error(f"Orchestration failed: {e}", exc_info=True)
            if span:
                span.record_exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Orchestration failed: {str(e)}",
            )
        finally:
            if span:
                span.end()

    async def _handle_analyze_intent(
        self, request: IntentAnalysisRequest, headers: dict = Header(...)
    ):
        """
        Analyze query intent only (no routing).

        Args:
            request: Intent analysis request
            headers: HTTP headers

        Returns:
            Intent analysis response
        """
        standard_headers = extract_headers(**headers)

        try:
            intent_result = await self.query_router.analyze_intent(
                query=request.query,
                tenant_id=standard_headers.tenant_id,
                context=request.context,
            )

            intent = intent_result.get("intent", "unknown")
            routing_config = self.service_selector.select_service(
                intent=intent,
                query=request.query,
                context=request.context,
                tenant_id=standard_headers.tenant_id,
            )

            return IntentAnalysisResponse(
                intent=intent,
                confidence=intent_result.get("confidence", 0.0),
                reasoning=intent_result.get("reasoning", ""),
                suggested_service=routing_config["service"],
                suggested_endpoint=routing_config["endpoint"],
            )

        except Exception as e:
            logger.error(f"Intent analysis failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Intent analysis failed: {str(e)}",
            )

    async def _handle_invalidate_cache(
        self, request: CacheInvalidateRequest, headers: dict = Header(...)
    ):
        """
        Invalidate cache entries.

        Args:
            request: Cache invalidation request
            headers: HTTP headers

        Returns:
            Cache invalidation response
        """
        standard_headers = extract_headers(**headers)

        try:
            tenant_id = request.tenant_id or standard_headers.tenant_id

            await self.cache_manager.invalidate(
                feature=request.feature,
                tenant_id=tenant_id,
                pattern=request.pattern,
            )

            return CacheInvalidateResponse(
                success=True,
                message="Cache invalidated successfully",
            )

        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Cache invalidation failed: {str(e)}",
            )

    async def _handle_health_check(self):
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "orchestrator",
            "version": self.config.service_version,
        }

