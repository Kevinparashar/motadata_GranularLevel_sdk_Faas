"""
Request/Response models for Cache Service.
"""


from typing import Any, Optional

from pydantic import BaseModel, Field


class GetCacheRequest(BaseModel):
    """Request to get cached value."""

    key: str = Field(..., description="Cache key")


class SetCacheRequest(BaseModel):
    """Request to set cached value."""

    key: str = Field(..., description="Cache key")
    value: Any = Field(..., description="Value to cache")
    ttl: Optional[int] = Field(None, description="Time to live in seconds")


class InvalidateCacheRequest(BaseModel):
    """Request to invalidate cache."""

    pattern: Optional[str] = Field(
        None, description="Key pattern to invalidate (supports wildcards)"
    )
    tenant_id: Optional[str] = Field(None, description="Tenant ID to clear cache for")


class CacheResponse(BaseModel):
    """Cache response model."""

    key: str
    value: Optional[Any] = None
    found: bool = Field(False, description="Whether key was found in cache")
    ttl: Optional[int] = Field(None, description="Remaining TTL in seconds")
