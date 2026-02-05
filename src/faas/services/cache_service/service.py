"""
Cache Service - Main service implementation.

Provides distributed caching operations.
"""


import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException, status

from ....core.cache_mechanism import CacheMechanism, create_cache
from ...integrations.codec import create_codec_manager
from ...integrations.nats import create_nats_client
from ...integrations.otel import create_otel_tracer
from ...shared.config import ServiceConfig, load_config
from ...shared.contracts import ServiceResponse, extract_headers
from ...shared.middleware import setup_middleware
from .models import InvalidateCacheRequest, SetCacheRequest

logger = logging.getLogger(__name__)


class CacheService:
    """
    Cache Service for distributed caching.

    Provides REST API for:
    - Get cached values
    - Set cached values
    - Delete cached values
    - Invalidate cache by pattern
    - Clear tenant cache
    """

    def __init__(
        self,
        config: ServiceConfig,
        nats_client: Optional[Any] = None,
        otel_tracer: Optional[Any] = None,
        codec_manager: Optional[Any] = None,
    ):
        """
        Initialize Cache Service.
        
        Args:
            config (ServiceConfig): Configuration object or settings.
            nats_client (Optional[Any]): Input parameter for this operation.
            otel_tracer (Optional[Any]): Input parameter for this operation.
            codec_manager (Optional[Any]): Input parameter for this operation.
        """
        self.config = config
        self.nats_client = nats_client
        self.otel_tracer = otel_tracer
        self.codec_manager = codec_manager or create_codec_manager()

        # Cache instances are created on-demand per request (stateless)
        # CacheMechanism itself uses Dragonfly/memory backend, so instances are lightweight

        # Create FastAPI app
        self.app = FastAPI(
            title="Cache Service",
            description="FaaS service for distributed caching",
            version=config.service_version,
        )

        # Setup middleware
        setup_middleware(self.app)

        # Register routes
        self._register_routes()

    def _get_cache(self, tenant_id: str) -> CacheMechanism:
        """
        Create cache for tenant (stateless - created on-demand).
        
        Args:
            tenant_id (str): Tenant identifier used for tenant isolation.
        
        Returns:
            CacheMechanism: Result of the operation.
        """
        # Create cache on-demand (stateless)
        # CacheMechanism uses Dragonfly/memory backend, so instances are lightweight
        cache = create_cache(
            backend="dragonfly" if self.config.dragonfly_url else "memory",
            dragonfly_url=self.config.dragonfly_url,
            namespace=f"cache_{tenant_id}",
        )
        return cache

    def _register_routes(self):
        """Register FastAPI routes."""
        self.app.get("/api/v1/cache/{key}", response_model=ServiceResponse)(
            self._handle_get_cache
        )

        self.app.post(
            "/api/v1/cache", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED
        )(self._handle_set_cache)

        self.app.delete("/api/v1/cache/{key}", status_code=status.HTTP_204_NO_CONTENT)(
            self._handle_delete_cache
        )

        self.app.post("/api/v1/cache/invalidate", response_model=ServiceResponse)(
            self._handle_invalidate_cache
        )

        self.app.delete("/api/v1/cache/tenant/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)(
            self._handle_clear_tenant_cache
        )

        self.app.get("/health")(self._handle_health_check)

    async def _handle_get_cache(self, key: str, headers: dict = Header(...)):  # noqa: S7503
        """
        Get cached value. Async required for FastAPI route handler.
        
        Args:
            key (str): Input parameter for this operation.
            headers (dict): HTTP headers passed from the caller.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            HTTPException: Raised when this function detects an invalid state or when an underlying call fails.
        """
        standard_headers = extract_headers(**headers)

        span = None
        if self.otel_tracer:
            span = self.otel_tracer.start_span("cache_get")
            span.set_attribute("cache.key", key)
            span.set_attribute("tenant.id", standard_headers.tenant_id)

        try:
            # Get cache
            cache = self._get_cache(standard_headers.tenant_id)

            # Get value
            value = await cache.get(key, tenant_id=standard_headers.tenant_id)

            if value is None:
                return ServiceResponse(
                    success=True,
                    data={"key": key, "found": False},
                    correlation_id=standard_headers.correlation_id,
                    request_id=standard_headers.request_id,
                )

            return ServiceResponse(
                success=True,
                data={"key": key, "value": value, "found": True},
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )
        except Exception as e:
            logger.error(f"Error getting cache: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get cache: {str(e)}",
            )
        finally:
            if span:
                span.end()

    async def _handle_set_cache(self, request: SetCacheRequest, headers: dict = Header(...)):
        """
        Set cached value.
        
        Args:
            request (SetCacheRequest): Request payload object.
            headers (dict): HTTP headers passed from the caller.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            HTTPException: Raised when this function detects an invalid state or when an underlying call fails.
        """
        standard_headers = extract_headers(**headers)

        span = None
        if self.otel_tracer:
            span = self.otel_tracer.start_span("cache_set")
            span.set_attribute("cache.key", request.key)
            span.set_attribute("tenant.id", standard_headers.tenant_id)

        try:
            # Get cache
            cache = self._get_cache(standard_headers.tenant_id)

            # Set value
            await cache.set(
                key=request.key,
                value=request.value,
                ttl=request.ttl,
                tenant_id=standard_headers.tenant_id,
            )

            # Publish event via NATS
            if self.nats_client:
                event = {
                    "event_type": "cache.set",
                    "key": request.key,
                    "tenant_id": standard_headers.tenant_id,
                }
                await self.nats_client.publish(
                    f"cache.events.{standard_headers.tenant_id}",
                    await self.codec_manager.encode(event),
                )

            return ServiceResponse(
                success=True,
                data={"key": request.key, "status": "set"},
                message="Cache value set successfully",
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )
        except Exception as e:
            logger.error(f"Error setting cache: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to set cache: {str(e)}",
            )
        finally:
            if span:
                span.end()

    async def _handle_delete_cache(self, key: str, headers: dict = Header(...)):  # noqa: S7503
        """
        Delete cached value. Async required for FastAPI route handler.
        
        Args:
            key (str): Input parameter for this operation.
            headers (dict): HTTP headers passed from the caller.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            HTTPException: Raised when this function detects an invalid state or when an underlying call fails.
        """
        standard_headers = extract_headers(**headers)

        try:
            # Get cache
            cache = self._get_cache(standard_headers.tenant_id)

            # Delete value
            await cache.delete(key, tenant_id=standard_headers.tenant_id)

            return None
        except Exception as e:
            logger.error(f"Error deleting cache: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete cache: {str(e)}",
            )

    async def _handle_invalidate_cache(  # noqa: S7503
        self, request: InvalidateCacheRequest, headers: dict = Header(...)
    ):
        """
        Invalidate cache by pattern. Async required for FastAPI route handler.
        
        Args:
            request (InvalidateCacheRequest): Request payload object.
            headers (dict): HTTP headers passed from the caller.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            HTTPException: Raised when this function detects an invalid state or when an underlying call fails.
        """
        standard_headers = extract_headers(**headers)

        try:
            # Get cache
            tenant_id = request.tenant_id or standard_headers.tenant_id
            cache = self._get_cache(tenant_id)

            # Invalidate by pattern
            if request.pattern:
                await cache.invalidate_pattern(request.pattern, tenant_id=tenant_id)
            else:
                # Clear all cache for tenant by invalidating all patterns
                await cache.invalidate_pattern("*", tenant_id=tenant_id)

            return ServiceResponse(
                success=True,
                data={"pattern": request.pattern, "status": "invalidated"},
                message="Cache invalidated successfully",
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )
        except Exception as e:
            logger.error(f"Error invalidating cache: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to invalidate cache: {str(e)}",
            )

    async def _handle_clear_tenant_cache(  # noqa: S7503
        self, tenant_id: str, headers: dict = Header(...)
    ):
        """
        Clear all cache for a tenant. Async required for FastAPI route handler.
        
        Args:
            tenant_id (str): Tenant identifier used for tenant isolation.
            headers (dict): HTTP headers passed from the caller.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            HTTPException: Raised when this function detects an invalid state or when an underlying call fails.
        """
        extract_headers(**headers)  # Extract headers for validation

        try:
            # Get cache
            cache = self._get_cache(tenant_id)

            # Clear cache by invalidating all patterns
            await cache.invalidate_pattern("*", tenant_id=tenant_id)

            return None
        except Exception as e:
            logger.error(f"Error clearing tenant cache: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to clear tenant cache: {str(e)}",
            )

    async def _handle_health_check(self):  # noqa: S7503
        """
        Health check endpoint. Async required for FastAPI route handler.
        
        Returns:
            Any: Result of the operation.
        """
        return {"status": "healthy", "service": "cache-service"}


def create_cache_service(
    service_name: str = "cache-service",
    config_overrides: Optional[Dict[str, Any]] = None,
) -> CacheService:
    """
    Create Cache Service instance.

    Args:
        service_name: Service name
        config_overrides: Configuration overrides

    Returns:
        CacheService instance
    """
    # Load configuration
    config = load_config(service_name, **(config_overrides or {}))

    # Initialize integrations
    nats_client = create_nats_client() if config.enable_nats else None
    otel_tracer = create_otel_tracer(config.service_name) if config.enable_otel else None

    # Create service
    service = CacheService(
        config=config,
        nats_client=nats_client,
        otel_tracer=otel_tracer,
    )

    logger.info(f"Cache Service created: {service_name}")
    return service
