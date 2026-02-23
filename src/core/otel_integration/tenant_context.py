"""
Tenant Context for OTEL

Centralized tenant context management for OpenTelemetry spans, metrics, and logs.
Ensures tenant.id and tenant.tier are consistently attached to all telemetry.
"""

import logging
from typing import Any, Dict, Optional

from ..utils.tenant_utils import (
    add_tenant_attributes_to_span,
    get_tenant_tier,
)

logger = logging.getLogger(__name__)

# Initialize _OTEL_AVAILABLE before try/except
_OTEL_AVAILABLE = False

try:
    from opentelemetry import baggage, context

    _OTEL_AVAILABLE = True  # pyright: ignore[reportConstantRedefinition]
except ImportError:
    baggage = None
    context = None


def extract_tenant_from_context() -> Dict[str, Optional[str]]:
    """
    Extract tenant context from current OTEL context (baggage).
    
    Returns:
        Dictionary with tenant_id and tenant_tier, or empty dict if not available
        
    Example:
        >>> tenant_ctx = extract_tenant_from_context()
        >>> tenant_id = tenant_ctx.get("tenant_id")
    """
    if not _OTEL_AVAILABLE or not baggage:
        return {}
    
    try:
        ctx = context.get_current()
        tenant_id = baggage.get_baggage("tenant_id", context=ctx)
        tenant_tier = baggage.get_baggage("tenant_tier", context=ctx)
        
        result = {}
        if tenant_id:
            result["tenant_id"] = tenant_id
        if tenant_tier:
            result["tenant_tier"] = tenant_tier
        
        return result
    except Exception as e:
        logger.debug(f"Failed to extract tenant from context: {e}")
        return {}


def ensure_tenant_attributes_on_span(
    span: Any,
    tenant_id: Optional[str] = None,
    tenant_tier: Optional[str] = None,
    tier_map: Optional[Dict[str, str]] = None,
) -> None:
    """
    Ensure tenant.id and tenant.tier are set on a span.
    
    This function:
    1. Uses provided tenant_id/tenant_tier if given
    2. Falls back to extracting from current OTEL context (baggage)
    3. Looks up tenant_tier if not provided
    4. Sets attributes on the span
    
    Args:
        span: OTEL span object (OTELSpan or OpenTelemetry span)
        tenant_id: Tenant identifier (optional, will be extracted from context if not provided)
        tenant_tier: Tenant tier (optional, will be looked up if not provided)
        tier_map: Optional custom tier mapping
        
    Example:
        >>> from src.core.otel_integration import OTELTracer
        >>> tracer = OTELTracer("test")
        >>> with tracer.start_trace("operation") as span:
        ...     ensure_tenant_attributes_on_span(span, "abc-123")
    """
    if not span:
        return
    
    # Use provided tenant_id or extract from context
    if not tenant_id:
        tenant_ctx = extract_tenant_from_context()
        tenant_id = tenant_ctx.get("tenant_id")
        if not tenant_tier:
            tenant_tier = tenant_ctx.get("tenant_tier")
    
    if not tenant_id:
        # No tenant context available
        logger.debug("No tenant_id available for span")
        return
    
    # Use provided tenant_tier or look it up
    if not tenant_tier:
        tenant_tier = get_tenant_tier(tenant_id, tier_map=tier_map)
    
    # Add tenant attributes to span
    add_tenant_attributes_to_span(
        span=span,
        tenant_id=tenant_id,
        tenant_tier=tenant_tier,
        tier_map=tier_map,
        attribute_prefix="tenant",
    )


def set_tenant_context_in_baggage(
    tenant_id: str,
    tenant_tier: Optional[str] = None,
    ctx: Optional[Any] = None,
) -> Optional[Any]:
    """
    Set tenant context in OTEL baggage for propagation.
    
    This is a convenience wrapper that sets tenant_id and tenant_tier in baggage
    and returns the updated context. Use this to propagate tenant context across
    service boundaries.
    
    Args:
        tenant_id: Tenant identifier (required)
        tenant_tier: Tenant tier (optional)
        ctx: Optional context (uses current context if not provided)
        
    Returns:
        Updated context with tenant baggage, or None if OTEL not available
        
    Example:
        >>> from opentelemetry import context
        >>> ctx = set_tenant_context_in_baggage("abc-123", "premium")
        >>> context.attach(ctx)
    """
    if not _OTEL_AVAILABLE or not baggage:
        return ctx
    
    original_ctx = ctx
    try:
        if ctx is None:
            ctx = context.get_current()
        
        # Set tenant_id
        ctx = baggage.set_baggage("tenant_id", tenant_id, context=ctx)
        
        # Set tenant_tier if provided
        if tenant_tier:
            ctx = baggage.set_baggage("tenant_tier", tenant_tier, context=ctx)
        
        return ctx
    except Exception as e:
        logger.debug(f"Failed to set tenant context in baggage: {e}")
        # Return the original ctx if provided, otherwise None
        return original_ctx


def get_tenant_attributes_for_metrics(
    tenant_id: Optional[str] = None,
    tenant_tier: Optional[str] = None,
    tier_map: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """
    Get tenant attributes dictionary for use in metric recording.
    
    This function ensures tenant.id and tenant.tier are available for metrics,
    extracting from context if not provided.
    
    Args:
        tenant_id: Tenant identifier (optional, will be extracted from context if not provided)
        tenant_tier: Tenant tier (optional, will be looked up if not provided)
        tier_map: Optional custom tier mapping
        
    Returns:
        Dictionary with tenant.id and tenant.tier (if available)
        
    Example:
        >>> attrs = get_tenant_attributes_for_metrics("abc-123")
        >>> metrics.increment_counter("operation.count", attributes=attrs)
    """
    attributes = {}
    
    # Use provided tenant_id or extract from context
    if not tenant_id:
        tenant_ctx = extract_tenant_from_context()
        tenant_id = tenant_ctx.get("tenant_id")
        if not tenant_tier:
            tenant_tier = tenant_ctx.get("tenant_tier")
    
    if tenant_id:
        attributes["tenant.id"] = tenant_id
        
        # Use provided tenant_tier or look it up
        if not tenant_tier:
            tenant_tier = get_tenant_tier(tenant_id, tier_map=tier_map)
        
        if tenant_tier:
            attributes["tenant.tier"] = tenant_tier
    
    return attributes

