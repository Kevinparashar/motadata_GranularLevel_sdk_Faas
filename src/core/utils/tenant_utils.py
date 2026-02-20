"""
Tenant Utilities

Helper functions for tenant context management including tier determination.
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Default tenant tier mapping (can be overridden)
_DEFAULT_TENANT_TIER_MAP: Dict[str, str] = {}


def get_tenant_tier(tenant_id: Optional[str], tier_map: Optional[Dict[str, str]] = None) -> Optional[str]:
    """
    Get tenant tier for a given tenant ID.
    
    Determines tenant tier from:
    1. Provided tier_map (highest priority)
    2. Default tier map
    3. Returns None if not found
    
    Args:
        tenant_id: Tenant identifier
        tier_map: Optional custom tier mapping (tenant_id -> tier)
        
    Returns:
        Tenant tier ("basic", "standard", "premium") or None
        
    Example:
        >>> get_tenant_tier("abc-123", {"abc-123": "premium"})
        'premium'
        >>> get_tenant_tier("unknown")
        None
    """
    if not tenant_id:
        return None
    
    # Check provided tier map first
    if tier_map and tenant_id in tier_map:
        return tier_map[tenant_id]
    
    # Check default tier map
    if tenant_id in _DEFAULT_TENANT_TIER_MAP:
        return _DEFAULT_TENANT_TIER_MAP[tenant_id]
    
    return None


def set_tenant_tier_mapping(tenant_id: str, tier: str) -> None:
    """
    Set tenant tier in default mapping.
    
    Args:
        tenant_id: Tenant identifier
        tier: Tenant tier ("basic", "standard", "premium")
        
    Example:
        >>> set_tenant_tier_mapping("abc-123", "premium")
    """
    if tenant_id and tier:
        _DEFAULT_TENANT_TIER_MAP[tenant_id] = tier


def set_tenant_tier_mappings(mappings: Dict[str, str]) -> None:
    """
    Set multiple tenant tier mappings at once.
    
    Args:
        mappings: Dictionary mapping tenant_id to tier
        
    Example:
        >>> set_tenant_tier_mappings({"abc-123": "premium", "def-456": "standard"})
    """
    if mappings:
        _DEFAULT_TENANT_TIER_MAP.update(mappings)


def clear_tenant_tier_mappings() -> None:
    """Clear all tenant tier mappings."""
    _DEFAULT_TENANT_TIER_MAP.clear()


def get_tenant_tier_mappings() -> Dict[str, str]:
    """
    Get current tenant tier mappings.
    
    Returns:
        Dictionary of tenant_id -> tier mappings
    """
    return _DEFAULT_TENANT_TIER_MAP.copy()


def add_tenant_attributes_to_span(
    span: Any,
    tenant_id: Optional[str],
    tenant_tier: Optional[str] = None,
    tier_map: Optional[Dict[str, str]] = None,
    attribute_prefix: str = "tenant",
) -> None:
    """
    Add tenant.id and tenant.tier attributes to an OTEL span.
    
    This is a convenience function to ensure consistent tenant attribute naming
    across all spans in the SDK.
    
    Args:
        span: OTEL span object (OTELSpan or OpenTelemetry span)
        tenant_id: Tenant identifier
        tenant_tier: Tenant tier (optional, will be looked up if not provided)
        tier_map: Optional custom tier mapping
        attribute_prefix: Prefix for attribute keys (default: "tenant")
        
    Example:
        >>> from src.core.otel_integration import OTELTracer
        >>> tracer = OTELTracer("test")
        >>> with tracer.start_trace("test") as span:
        ...     add_tenant_attributes_to_span(span, "abc-123", "premium")
    """
    if not span:
        return
    
    # Set tenant.id if provided
    if tenant_id:
        attr_key = f"{attribute_prefix}.id"
        if hasattr(span, "set_attribute"):
            span.set_attribute(attr_key, tenant_id)
        elif hasattr(span, "_span") and span._span:
            try:
                span._span.set_attribute(attr_key, tenant_id)
            except Exception:
                pass
    
    # Determine tenant tier if not provided
    if tenant_id and not tenant_tier:
        tenant_tier = get_tenant_tier(tenant_id, tier_map=tier_map)
    
    # Set tenant.tier if available
    if tenant_tier:
        tier_key = f"{attribute_prefix}.tier"
        if hasattr(span, "set_attribute"):
            span.set_attribute(tier_key, tenant_tier)
        elif hasattr(span, "_span") and span._span:
            try:
                span._span.set_attribute(tier_key, tenant_tier)
            except Exception:
                pass

