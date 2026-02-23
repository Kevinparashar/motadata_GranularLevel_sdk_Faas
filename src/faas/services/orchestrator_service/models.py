"""
Request/Response models for Orchestrator Service.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class OrchestrateRequest(BaseModel):
    """Request to orchestrate a query."""

    query: str = Field(..., description="User query text")
    context: Optional[Dict[str, Any]] = Field(
        None, description="Optional context (agent_id, session_id, model, etc.)"
    )
    intent: Optional[str] = Field(None, description="Optional explicit intent (overrides analysis)")
    cache_enabled: bool = Field(default=True, description="Enable caching for this request")
    stream: bool = Field(default=False, description="Enable streaming response")


class OrchestrateResponse(BaseModel):
    """Orchestrator response model."""

    success: bool
    data: Optional[Dict[str, Any]] = None
    intent: str
    service: str
    endpoint: str
    cached: bool = Field(default=False, description="Whether response was served from cache")
    message: Optional[str] = None
    correlation_id: str
    request_id: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class IntentAnalysisRequest(BaseModel):
    """Request for intent analysis only."""

    query: str = Field(..., description="User query text")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional context")


class IntentAnalysisResponse(BaseModel):
    """Intent analysis response model."""

    intent: str
    confidence: float
    reasoning: str
    suggested_service: str
    suggested_endpoint: str


class CacheInvalidateRequest(BaseModel):
    """Request to invalidate cache."""

    feature: Optional[str] = Field(None, description="Feature name to invalidate")
    pattern: Optional[str] = Field(None, description="Cache key pattern to match")
    tenant_id: Optional[str] = Field(None, description="Tenant ID to invalidate")


class CacheInvalidateResponse(BaseModel):
    """Cache invalidation response model."""

    success: bool
    message: str
    keys_invalidated: Optional[int] = None

