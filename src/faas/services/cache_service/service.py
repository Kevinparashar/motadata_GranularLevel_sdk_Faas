"""
Cache Service - Main service implementation.

Provides distributed caching operations.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Header, status

from ....core.cache_mechanism import create_cache, CacheMechanism
from ...shared.config import ServiceConfig, load_config
from ...shared.contracts import ServiceResponse, extract_headers
from ...shared.exceptions import NotFoundError
from ...shared.middleware import setup_middleware
from .models import (
    GetCacheRequest,
    SetCacheRequest,
    InvalidateCacheRequest,
    CacheResponse,
)
from ...integrations.nats import create_nats_client
from ...integrations.otel import create_otel_tracer
from ...integrations.codec import create_codec_manager

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
            config: Service configuration
            nats_client: NATS client (optional)
            otel_tracer: OTEL tracer (optional)
            codec_manager: Codec manager (optional)
        """
        self.config = config
        self.nats_client = nats_client
        self.otel_tracer = otel_tracer
        self.codec_manager = codec_manager or create_codec_manager()

        # Cache instances are created on-demand per request (stateless)
        # CacheMechanism itself uses Redis/memory backend, so instances are lightweight

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
            tenant_id: Tenant ID

        Returns:
            CacheMechanism instance
        """
        # Create cache on-demand (stateless)
        # CacheMechanism uses Redis/memory backend, so instances are lightweight
        cache = create_cache(
            backend="redis" if self.config.redis_url else "memory",
            redis_url=self.config.redis_url,
            namespace=f"cache_{tenant_id}",
        )
        return cache

    def _register_routes(self):
        """Register FastAPI routes."""

        @self.app.get("/api/v1/cache/{key}", response_model=ServiceResponse)
        async def get_cache(
            key: str,
            headers: dict = Header(...),
        ):
            """Get cached value."""
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
                value = await cache.get_async(key)

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

        @self.app.post("/api/v1/cache", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
        async def set_cache(
            request: SetCacheRequest,
            headers: dict = Header(...),
        ):
            """Set cached value."""
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
                await cache.set_async(
                    key=request.key,
                    value=request.value,
                    ttl=request.ttl,
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
                        self.codec_manager.encode(event),
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

        @self.app.delete("/api/v1/cache/{key}", status_code=status.HTTP_204_NO_CONTENT)
        async def delete_cache(
            key: str,
            headers: dict = Header(...),
        ):
            """Delete cached value."""
            standard_headers = extract_headers(**headers)

            try:
                # Get cache
                cache = self._get_cache(standard_headers.tenant_id)

                # Delete value
                await cache.delete_async(key)

                return None
            except Exception as e:
                logger.error(f"Error deleting cache: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to delete cache: {str(e)}",
                )

        @self.app.post("/api/v1/cache/invalidate", response_model=ServiceResponse)
        async def invalidate_cache(
            request: InvalidateCacheRequest,
            headers: dict = Header(...),
        ):
            """Invalidate cache by pattern."""
            standard_headers = extract_headers(**headers)

            try:
                # Get cache
                cache = self._get_cache(request.tenant_id or standard_headers.tenant_id)

                # Invalidate by pattern
                if request.pattern:
                    await cache.invalidate_pattern_async(request.pattern)
                else:
                    # Clear all cache for tenant
                    await cache.clear_async()

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

        @self.app.delete("/api/v1/cache/tenant/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
        async def clear_tenant_cache(
            tenant_id: str,
            headers: dict = Header(...),
        ):
            """Clear all cache for a tenant."""
            standard_headers = extract_headers(**headers)

            try:
                # Get cache
                cache = self._get_cache(tenant_id)

                # Clear cache
                await cache.clear_async()

                return None
            except Exception as e:
                logger.error(f"Error clearing tenant cache: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to clear tenant cache: {str(e)}",
                )

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
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

