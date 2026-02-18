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

    _OTEL_AVAILABLE = True  # pyright: ignore[reportConstantRedefinition]
except ImportError:
    trace = None
    extract = None
    inject = None

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

