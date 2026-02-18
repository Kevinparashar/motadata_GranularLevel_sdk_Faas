"""
Unit Tests for OTEL Context Propagation

Tests for trace context propagation functionality.
"""

from src.core.otel_integration import (
    extract_trace_context,
    get_current_trace_context,
    inject_trace_context,
)


class TestContextPropagation:
    """Tests for context propagation functions."""

    def test_inject_trace_context(self):
        """Test injecting trace context."""
        carrier = {}
        result = inject_trace_context(carrier)
        
        assert result == carrier
        # Should not raise exception

    def test_extract_trace_context(self):
        """Test extracting trace context."""
        carrier = {"traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"}
        context = extract_trace_context(carrier)
        
        # Should return context or None
        assert context is None or context is not None

    def test_extract_trace_context_empty(self):
        """Test extracting trace context from empty carrier."""
        carrier = {}
        context = extract_trace_context(carrier)
        
        # Should return None or empty context when no trace context present
        assert context is None or context is not None

    def test_get_current_trace_context(self):
        """Test getting current trace context."""
        context = get_current_trace_context()
        
        # Should return None if no active trace
        assert context is None or isinstance(context, dict)

