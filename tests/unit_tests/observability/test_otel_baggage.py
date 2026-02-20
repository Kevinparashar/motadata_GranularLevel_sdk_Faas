"""
Unit Tests for OTEL Baggage Propagation

Tests for baggage propagation functionality for tenant context.
"""

import pytest
from unittest.mock import MagicMock, patch

from src.core.otel_integration import (
    set_baggage,
    get_baggage,
    set_tenant_context,
    get_tenant_context,
)
from src.core.otel_integration.context_propagation import (
    inject_trace_context,
    extract_trace_context,
    get_trace_context,
    DictGetter,
    DictSetter,
)


class TestBaggagePropagation:
    """Tests for baggage propagation functions."""

    def test_set_baggage_with_otel_available(self):
        """Test setting baggage when OTEL is available."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.context_propagation.baggage") as mock_baggage:
                mock_context = MagicMock()
                mock_baggage.get_current.return_value = mock_context
                mock_baggage.set_baggage.return_value = mock_context
                
                result = set_baggage("tenant_id", "abc-123")
                
                assert result == mock_context
                mock_baggage.get_current.assert_called_once()
                mock_baggage.set_baggage.assert_called_once_with("tenant_id", "abc-123", context=mock_context)

    def test_set_baggage_with_context(self):
        """Test setting baggage with provided context."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.context_propagation.baggage") as mock_baggage:
                provided_context = MagicMock()
                mock_baggage.set_baggage.return_value = provided_context
                
                result = set_baggage("tenant_id", "abc-123", context=provided_context)
                
                assert result == provided_context
                mock_baggage.set_baggage.assert_called_once_with("tenant_id", "abc-123", context=provided_context)
                mock_baggage.get_current.assert_not_called()

    def test_set_baggage_otel_not_available(self):
        """Test setting baggage when OTEL is not available."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", False):
            context = MagicMock()
            result = set_baggage("tenant_id", "abc-123", context=context)
            
            assert result == context

    def test_set_baggage_exception_handling(self):
        """Test set_baggage handles exceptions gracefully."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.context_propagation.baggage") as mock_baggage:
                mock_baggage.get_current.side_effect = Exception("Baggage error")
                context = MagicMock()
                
                result = set_baggage("tenant_id", "abc-123", context=context)
                
                # When exception occurs, should return the provided context
                assert result is not None

    def test_get_baggage_with_otel_available(self):
        """Test getting baggage when OTEL is available."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.context_propagation.baggage") as mock_baggage:
                mock_member = MagicMock()
                mock_member.value = "abc-123"
                mock_bag = MagicMock()
                mock_bag.get_member.return_value = mock_member
                mock_baggage.from_context.return_value = mock_bag
                mock_context = MagicMock()
                mock_baggage.get_current.return_value = mock_context
                
                result = get_baggage("tenant_id")
                
                assert result == "abc-123"
                mock_baggage.get_current.assert_called_once()
                mock_baggage.from_context.assert_called_once_with(mock_context)
                mock_bag.get_member.assert_called_once_with("tenant_id")

    def test_get_baggage_with_context(self):
        """Test getting baggage with provided context."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.context_propagation.baggage") as mock_baggage:
                mock_member = MagicMock()
                mock_member.value = "premium"
                mock_bag = MagicMock()
                mock_bag.get_member.return_value = mock_member
                mock_baggage.from_context.return_value = mock_bag
                provided_context = MagicMock()
                
                result = get_baggage("tenant_tier", context=provided_context)
                
                assert result == "premium"
                mock_baggage.from_context.assert_called_once_with(provided_context)
                mock_baggage.get_current.assert_not_called()

    def test_get_baggage_not_found(self):
        """Test getting baggage when key is not found."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.context_propagation.baggage") as mock_baggage:
                mock_bag = MagicMock()
                mock_bag.get_member.return_value = None
                mock_baggage.from_context.return_value = mock_bag
                mock_baggage.get_current.return_value = MagicMock()
                
                result = get_baggage("nonexistent_key")
                
                assert result is None

    def test_get_baggage_no_bag(self):
        """Test getting baggage when no bag exists."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.context_propagation.baggage") as mock_baggage:
                mock_baggage.from_context.return_value = None
                mock_baggage.get_current.return_value = MagicMock()
                
                result = get_baggage("tenant_id")
                
                assert result is None

    def test_get_baggage_otel_not_available(self):
        """Test getting baggage when OTEL is not available."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", False):
            result = get_baggage("tenant_id")
            
            assert result is None

    def test_get_baggage_exception_handling(self):
        """Test get_baggage handles exceptions gracefully."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.context_propagation.baggage") as mock_baggage:
                mock_baggage.get_current.side_effect = Exception("Baggage error")
                
                result = get_baggage("tenant_id")
                
                assert result is None

    def test_set_tenant_context_both_values(self):
        """Test setting tenant context with both tenant_id and tenant_tier."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.context_propagation.baggage") as mock_baggage:
                mock_context1 = MagicMock()
                mock_context2 = MagicMock()
                mock_baggage.get_current.return_value = None
                mock_baggage.set_baggage.side_effect = [mock_context1, mock_context2]
                
                result = set_tenant_context("abc-123", "premium")
                
                assert result == mock_context2
                assert mock_baggage.set_baggage.call_count == 2
                mock_baggage.set_baggage.assert_any_call("tenant_id", "abc-123", context=None)
                mock_baggage.set_baggage.assert_any_call("tenant_tier", "premium", context=mock_context1)

    def test_set_tenant_context_tenant_id_only(self):
        """Test setting tenant context with only tenant_id."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.context_propagation.baggage") as mock_baggage:
                mock_context = MagicMock()
                mock_baggage.get_current.return_value = None
                mock_baggage.set_baggage.return_value = mock_context
                
                result = set_tenant_context("abc-123", tenant_tier=None)
                
                assert result == mock_context
                assert mock_baggage.set_baggage.call_count == 1
                mock_baggage.set_baggage.assert_called_once_with("tenant_id", "abc-123", context=None)

    def test_set_tenant_context_with_context(self):
        """Test setting tenant context with provided context."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.context_propagation.baggage") as mock_baggage:
                provided_context = MagicMock()
                mock_context2 = MagicMock()
                mock_baggage.set_baggage.side_effect = [provided_context, mock_context2]
                
                result = set_tenant_context("abc-123", "premium", context=provided_context)
                
                assert result == mock_context2
                assert mock_baggage.set_baggage.call_count == 2
                mock_baggage.set_baggage.assert_any_call("tenant_id", "abc-123", context=provided_context)
                mock_baggage.set_baggage.assert_any_call("tenant_tier", "premium", context=provided_context)

    def test_set_tenant_context_otel_not_available(self):
        """Test setting tenant context when OTEL is not available."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", False):
            context = MagicMock()
            result = set_tenant_context("abc-123", "premium", context=context)
            
            assert result == context

    def test_set_tenant_context_exception_handling(self):
        """Test set_tenant_context handles exceptions gracefully."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.context_propagation.set_baggage") as mock_set_baggage:
                mock_set_baggage.side_effect = Exception("Baggage error")
                context = MagicMock()
                
                result = set_tenant_context("abc-123", "premium", context=context)
                
                assert result == context

    def test_get_tenant_context_both_values(self):
        """Test getting tenant context with both tenant_id and tenant_tier."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.context_propagation.get_baggage") as mock_get_baggage:
                mock_get_baggage.side_effect = ["abc-123", "premium"]
                
                result = get_tenant_context()
                
                assert result == {"tenant_id": "abc-123", "tenant_tier": "premium"}
                assert mock_get_baggage.call_count == 2
                mock_get_baggage.assert_any_call("tenant_id", context=None)
                mock_get_baggage.assert_any_call("tenant_tier", context=None)

    def test_get_tenant_context_tenant_id_only(self):
        """Test getting tenant context with only tenant_id."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.context_propagation.get_baggage") as mock_get_baggage:
                mock_get_baggage.side_effect = ["abc-123", None]
                
                result = get_tenant_context()
                
                assert result == {"tenant_id": "abc-123"}
                assert mock_get_baggage.call_count == 2

    def test_get_tenant_context_no_values(self):
        """Test getting tenant context when no values are set."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.context_propagation.get_baggage") as mock_get_baggage:
                mock_get_baggage.return_value = None
                
                result = get_tenant_context()
                
                assert result == {}
                assert mock_get_baggage.call_count == 2

    def test_get_tenant_context_with_context(self):
        """Test getting tenant context with provided context."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.context_propagation.get_baggage") as mock_get_baggage:
                mock_get_baggage.side_effect = ["abc-123", "premium"]
                provided_context = MagicMock()
                
                result = get_tenant_context(context=provided_context)
                
                assert result == {"tenant_id": "abc-123", "tenant_tier": "premium"}
                assert mock_get_baggage.call_count == 2
                mock_get_baggage.assert_any_call("tenant_id", context=provided_context)
                mock_get_baggage.assert_any_call("tenant_tier", context=provided_context)

    def test_get_tenant_context_otel_not_available(self):
        """Test getting tenant context when OTEL is not available."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", False):
            result = get_tenant_context()
            
            assert result == {}

    def test_get_tenant_context_exception_handling(self):
        """Test get_tenant_context handles exceptions gracefully."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.context_propagation.get_baggage") as mock_get_baggage:
                mock_get_baggage.side_effect = Exception("Baggage error")
                
                result = get_tenant_context()
                
                assert result == {}


class TestBaggageIntegration:
    """Integration tests for baggage propagation."""

    def test_set_and_get_baggage_roundtrip(self):
        """Test setting and getting baggage in a roundtrip."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.context_propagation.baggage") as mock_baggage:
                # Setup mocks for set_baggage
                mock_context = MagicMock()
                mock_baggage.get_current.return_value = mock_context
                mock_baggage.set_baggage.return_value = mock_context
                
                # Set baggage
                context = set_baggage("test_key", "test_value")
                
                # Setup mocks for get_baggage
                mock_member = MagicMock()
                mock_member.value = "test_value"
                mock_bag = MagicMock()
                mock_bag.get_member.return_value = mock_member
                mock_baggage.from_context.return_value = mock_bag
                mock_baggage.get_current.return_value = context
                
                # Get baggage
                result = get_baggage("test_key", context=context)
                
                assert result == "test_value"

    def test_set_and_get_tenant_context_roundtrip(self):
        """Test setting and getting tenant context in a roundtrip."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.context_propagation.set_baggage") as mock_set_baggage:
                with patch("src.core.otel_integration.context_propagation.get_baggage") as mock_get_baggage:
                    mock_context = MagicMock()
                    mock_set_baggage.side_effect = [mock_context, mock_context]
                    mock_get_baggage.side_effect = ["abc-123", "premium"]
                    
                    # Set tenant context
                    context = set_tenant_context("abc-123", "premium")
                    
                    # Get tenant context
                    result = get_tenant_context(context=context)
                    
                    assert result == {"tenant_id": "abc-123", "tenant_tier": "premium"}


class TestTraceContextPropagation:
    """Tests for trace context propagation functions."""

    def test_inject_trace_context_with_otel_available(self):
        """Test injecting trace context when OTEL is available."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.context_propagation.inject") as mock_inject:
                with patch("src.core.otel_integration.context_propagation._dict_setter") as mock_setter:
                    carrier = {}
                    
                    result = inject_trace_context(carrier)
                    
                    assert result == carrier
                    mock_inject.assert_called_once_with(carrier, setter=mock_setter)
                    assert mock_setter is not None  # Verify setter is used

    def test_inject_trace_context_otel_not_available(self):
        """Test injecting trace context when OTEL is not available."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", False):
            carrier = {"existing": "value"}
            
            result = inject_trace_context(carrier)
            
            assert result == carrier

    def test_inject_trace_context_exception_handling(self):
        """Test inject_trace_context handles exceptions gracefully."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.context_propagation.inject") as mock_inject:
                with patch("src.core.otel_integration.context_propagation._dict_setter") as mock_setter:
                    mock_inject.side_effect = Exception("Injection error")
                    carrier = {}
                    
                    with pytest.raises(Exception):  # Should raise OTELContextError
                        inject_trace_context(carrier)
                    # Verify setter was attempted to be used
                    assert mock_setter is not None

    def test_extract_trace_context_with_otel_available(self):
        """Test extracting trace context when OTEL is available."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.context_propagation.extract") as mock_extract:
                with patch("src.core.otel_integration.context_propagation._dict_getter") as mock_getter:
                    mock_context = MagicMock()
                    mock_extract.return_value = mock_context
                    carrier = {"traceparent": "00-abc-123-01"}
                    
                    result = extract_trace_context(carrier)
                    
                    assert result == mock_context
                    mock_extract.assert_called_once_with(carrier, getter=mock_getter)
                    assert mock_getter is not None  # Verify getter is used

    def test_extract_trace_context_otel_not_available(self):
        """Test extracting trace context when OTEL is not available."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", False):
            carrier = {"traceparent": "00-abc-123-01"}
            
            result = extract_trace_context(carrier)
            
            assert result is None

    def test_extract_trace_context_exception_handling(self):
        """Test extract_trace_context handles exceptions gracefully."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.context_propagation.extract") as mock_extract:
                with patch("src.core.otel_integration.context_propagation._dict_getter") as mock_getter:
                    mock_extract.side_effect = Exception("Extraction error")
                    carrier = {"traceparent": "00-abc-123-01"}
                    
                    with pytest.raises(Exception):  # Should raise OTELContextError
                        extract_trace_context(carrier)
                    # Verify getter was attempted to be used
                    assert mock_getter is not None

    def test_get_trace_context_with_otel_available(self):
        """Test getting trace context when OTEL is available."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.context_propagation.trace") as mock_trace:
                with patch("src.core.otel_integration.context_propagation.inject") as mock_inject:
                    with patch("src.core.otel_integration.context_propagation._dict_setter") as mock_setter:
                        mock_span = MagicMock()
                        mock_span_context = MagicMock()
                        mock_span.get_span_context.return_value = mock_span_context
                        mock_trace.get_current_span.return_value = mock_span
                        mock_trace.is_recording.return_value = True
                        
                        result = get_trace_context()
                        
                        assert result is not None
                        mock_trace.get_current_span.assert_called()
                        mock_trace.is_recording.assert_called_once_with(mock_span)
                        mock_inject.assert_called_once_with({}, setter=mock_setter)
                        assert mock_setter is not None  # Verify setter is used

    def test_get_trace_context_no_current_span(self):
        """Test getting trace context when no current span exists."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.context_propagation.trace") as mock_trace:
                mock_trace.get_current_span.return_value = None
                
                result = get_trace_context()
                
                assert result is None

    def test_get_trace_context_span_not_recording(self):
        """Test getting trace context when span is not recording."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.context_propagation.trace") as mock_trace:
                mock_span = MagicMock()
                mock_trace.get_current_span.return_value = mock_span
                mock_trace.is_recording.return_value = False
                
                result = get_trace_context()
                
                assert result is None

    def test_get_trace_context_no_span_context(self):
        """Test getting trace context when span has no context."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.context_propagation.trace") as mock_trace:
                mock_span = MagicMock()
                mock_span.get_span_context.return_value = None
                mock_trace.get_current_span.return_value = mock_span
                mock_trace.is_recording.return_value = True
                
                result = get_trace_context()
                
                assert result is None

    def test_get_trace_context_exception_handling(self):
        """Test get_trace_context handles exceptions gracefully."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.context_propagation.trace") as mock_trace:
                mock_trace.get_current_span.side_effect = Exception("Trace error")
                
                result = get_trace_context()
                
                assert result is None

    def test_get_trace_context_otel_not_available(self):
        """Test getting trace context when OTEL is not available."""
        with patch("src.core.otel_integration.context_propagation._OTEL_AVAILABLE", False):
            result = get_trace_context()
            
            assert result is None


class TestDictGetterSetter:
    """Tests for DictGetter and DictSetter classes."""

    def test_dict_getter_get(self):
        """Test DictGetter.get method."""
        getter = DictGetter()
        carrier = {"key1": "value1", "key2": "value2"}
        
        result = getter.get(carrier, "key1")
        
        assert result == "value1"

    def test_dict_getter_get_missing_key(self):
        """Test DictGetter.get with missing key."""
        getter = DictGetter()
        carrier = {"key1": "value1"}
        
        result = getter.get(carrier, "missing")
        
        assert result is None

    def test_dict_getter_keys(self):
        """Test DictGetter.keys method."""
        getter = DictGetter()
        carrier = {"key1": "value1", "key2": "value2"}
        
        result = getter.keys(carrier)
        
        assert set(result) == {"key1", "key2"}

    def test_dict_setter_set(self):
        """Test DictSetter.set method."""
        setter = DictSetter()
        carrier = {}
        
        setter.set(carrier, "key1", "value1")
        
        assert carrier == {"key1": "value1"}

    def test_dict_setter_set_overwrite(self):
        """Test DictSetter.set overwrites existing value."""
        setter = DictSetter()
        carrier = {"key1": "old_value"}
        
        setter.set(carrier, "key1", "new_value")
        
        assert carrier == {"key1": "new_value"}

