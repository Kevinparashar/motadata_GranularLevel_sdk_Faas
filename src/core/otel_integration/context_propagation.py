"""
OTEL Context Propagation

Trace context propagation for distributed tracing across component boundaries.
"""

import logging
from typing import Any, Dict, Optional

# Initialize _OTEL_AVAILABLE before try/except to avoid constant redefinition warning
_OTEL_AVAILABLE = False

try:
    from opentelemetry import trace
    from opentelemetry.propagate import extract, inject
    from opentelemetry import baggage

    _OTEL_AVAILABLE = True  # pyright: ignore[reportConstantRedefinition]
except ImportError:
    trace = None
    extract = None
    inject = None
    baggage = None

from .exceptions import OTELContextError

logger = logging.getLogger(__name__)


class DictGetter:
    """Getter for dictionary-based carriers."""
    
    def get(self, carrier: Dict[str, str], key: str) -> Optional[str]:
        """Get value from dictionary carrier."""
        return carrier.get(key)
    
    def keys(self, carrier: Dict[str, str]) -> list:
        """Get all keys from dictionary carrier."""
        return list(carrier.keys())


class DictSetter:
    """Setter for dictionary-based carriers."""
    
    def set(self, carrier: Dict[str, str], key: str, value: str) -> None:
        """Set value in dictionary carrier."""
        carrier[key] = value


_dict_getter = DictGetter() if _OTEL_AVAILABLE else None
_dict_setter = DictSetter() if _OTEL_AVAILABLE else None


def inject_trace_context(carrier: Dict[str, str]) -> Dict[str, str]:
    """
    Inject trace context into a carrier dictionary.
    
    Args:
        carrier: Dictionary to inject context into
        
    Returns:
        Dictionary with trace context injected
    """
    if not _OTEL_AVAILABLE or not inject or not _dict_setter:
        return carrier
    
    try:
        inject(carrier, setter=_dict_setter)  # type: ignore
        return carrier
    except Exception as e:
        logger.error(f"Failed to inject trace context: {e}")
        raise OTELContextError(f"Failed to inject trace context: {e}", operation="inject", original_error=e)


def extract_trace_context(carrier: Dict[str, str]) -> Optional[Any]:
    """
    Extract trace context from a carrier dictionary.
    
    Args:
        carrier: Dictionary containing trace context
        
    Returns:
        Trace context or None if not available
    """
    if not _OTEL_AVAILABLE or not extract or not _dict_getter:
        return None
    
    try:
        context = extract(carrier, getter=_dict_getter)  # type: ignore
        return context
    except Exception as e:
        logger.error(f"Failed to extract trace context: {e}")
        raise OTELContextError(f"Failed to extract trace context: {e}", operation="extract", original_error=e)


def get_trace_context() -> Optional[Dict[str, str]]:
    """
    Get current trace context as a dictionary.
    
    Returns:
        Dictionary containing trace context or None
    """
    if not _OTEL_AVAILABLE or not trace or not inject or not _dict_setter:
        return None
    
    try:
        current_span = trace.get_current_span()
        if not current_span or not trace.is_recording(current_span):
            return None
        
        context = trace.get_current_span().get_span_context()
        if not context:
            return None
        
        # Convert context to dictionary format
        carrier = {}
        inject(carrier, setter=_dict_setter)  # type: ignore
        return carrier
    except Exception as e:
        logger.debug(f"Failed to get trace context: {e}")
        return None


def set_baggage(key: str, value: str, context: Optional[Any] = None) -> Optional[Any]:
    """
    Set baggage value in OpenTelemetry context.
    
    Baggage is used to propagate key-value pairs across service boundaries.
    Commonly used for tenant context (tenant_id, tenant_tier).
    
    Args:
        key: Baggage key
        value: Baggage value
        context: Optional context (uses current context if not provided)
        
    Returns:
        Updated context with baggage or None if OTEL not available
        
    Example:
        >>> ctx = set_baggage("tenant_id", "abc-123")
        >>> ctx = set_baggage("tenant_tier", "premium", context=ctx)
    """
    if not _OTEL_AVAILABLE or not baggage:
        return context
    
    try:
        if context is None:
            context = baggage.get_current()
        
        return baggage.set_baggage(key, value, context=context)
    except Exception as e:
        logger.debug(f"Failed to set baggage '{key}': {e}")
        return context


def get_baggage(key: str, context: Optional[Any] = None) -> Optional[str]:
    """
    Get baggage value from OpenTelemetry context.
    
    Args:
        key: Baggage key
        context: Optional context (uses current context if not provided)
        
    Returns:
        Baggage value or None if not found or OTEL not available
        
    Example:
        >>> tenant_id = get_baggage("tenant_id")
        >>> tenant_tier = get_baggage("tenant_tier")
    """
    if not _OTEL_AVAILABLE or not baggage:
        return None
    
    try:
        if context is None:
            context = baggage.get_current()
        
        bag = baggage.from_context(context)
        if bag:
            member = bag.get_member(key)
            if member:
                return member.value
        return None
    except Exception as e:
        logger.debug(f"Failed to get baggage '{key}': {e}")
        return None


def set_tenant_context(
    tenant_id: str,
    tenant_tier: Optional[str] = None,
    context: Optional[Any] = None,
) -> Optional[Any]:
    """
    Set tenant context in baggage for propagation across services.
    
    This is a convenience function that sets both tenant_id and tenant_tier
    in baggage for multi-tenant context propagation.
    
    Args:
        tenant_id: Tenant identifier (required)
        tenant_tier: Tenant tier (basic/standard/premium, optional)
        context: Optional context (uses current context if not provided)
        
    Returns:
        Updated context with tenant baggage or None if OTEL not available
        
    Example:
        >>> ctx = set_tenant_context("abc-123", "premium")
    """
    if not _OTEL_AVAILABLE or not baggage:
        return context
    
    try:
        if context is None:
            context = baggage.get_current()
        
        # Set tenant_id
        context = set_baggage("tenant_id", tenant_id, context=context)
        
        # Set tenant_tier if provided
        if tenant_tier:
            context = set_baggage("tenant_tier", tenant_tier, context=context)
        
        return context
    except Exception as e:
        logger.debug(f"Failed to set tenant context: {e}")
        return context


def get_tenant_context(context: Optional[Any] = None) -> Dict[str, Optional[str]]:
    """
    Get tenant context from baggage.
    
    Args:
        context: Optional context (uses current context if not provided)
        
    Returns:
        Dictionary with tenant_id and tenant_tier, or empty dict if not available
        
    Example:
        >>> tenant_ctx = get_tenant_context()
        >>> tenant_id = tenant_ctx.get("tenant_id")
        >>> tenant_tier = tenant_ctx.get("tenant_tier")
    """
    if not _OTEL_AVAILABLE or not baggage:
        return {}
    
    try:
        tenant_id = get_baggage("tenant_id", context=context)
        tenant_tier = get_baggage("tenant_tier", context=context)
        
        result = {}
        if tenant_id:
            result["tenant_id"] = tenant_id
        if tenant_tier:
            result["tenant_tier"] = tenant_tier
        
        return result
    except Exception as e:
        logger.debug(f"Failed to get tenant context: {e}")
        return {}

