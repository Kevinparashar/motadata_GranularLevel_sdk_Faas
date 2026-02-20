"""
Unit Tests for OTEL Tenant Context

Tests for tenant context management in OpenTelemetry.
"""

from unittest.mock import MagicMock, patch

from src.core.otel_integration.tenant_context import (
    extract_tenant_from_context,
    ensure_tenant_attributes_on_span,
    set_tenant_context_in_baggage,
    get_tenant_attributes_for_metrics,
)


class TestExtractTenantFromContext:
    """Test extract_tenant_from_context function."""

    def test_extract_tenant_with_otel_available(self):
        """Test extracting tenant from context when OTEL is available."""
        with patch("src.core.otel_integration.tenant_context._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.tenant_context.baggage") as mock_baggage, \
                 patch("src.core.otel_integration.tenant_context.context") as mock_context:
                mock_ctx = MagicMock()
                mock_context.get_current.return_value = mock_ctx
                mock_baggage.get_baggage.side_effect = ["abc-123", "premium"]
                
                result = extract_tenant_from_context()
                
                assert result == {"tenant_id": "abc-123", "tenant_tier": "premium"}
                assert mock_baggage.get_baggage.call_count == 2
                mock_baggage.get_baggage.assert_any_call("tenant_id", context=mock_ctx)
                mock_baggage.get_baggage.assert_any_call("tenant_tier", context=mock_ctx)

    def test_extract_tenant_id_only(self):
        """Test extracting tenant with only tenant_id."""
        with patch("src.core.otel_integration.tenant_context._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.tenant_context.baggage") as mock_baggage, \
                 patch("src.core.otel_integration.tenant_context.context") as mock_context:
                mock_ctx = MagicMock()
                mock_context.get_current.return_value = mock_ctx
                mock_baggage.get_baggage.side_effect = ["abc-123", None]
                
                result = extract_tenant_from_context()
                
                assert result == {"tenant_id": "abc-123"}

    def test_extract_tenant_no_values(self):
        """Test extracting tenant when no values are set."""
        with patch("src.core.otel_integration.tenant_context._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.tenant_context.baggage") as mock_baggage, \
                 patch("src.core.otel_integration.tenant_context.context") as mock_context:
                mock_ctx = MagicMock()
                mock_context.get_current.return_value = mock_ctx
                mock_baggage.get_baggage.return_value = None
                
                result = extract_tenant_from_context()
                
                assert result == {}

    def test_extract_tenant_otel_not_available(self):
        """Test extracting tenant when OTEL is not available."""
        with patch("src.core.otel_integration.tenant_context._OTEL_AVAILABLE", False):
            result = extract_tenant_from_context()
            assert result == {}

    def test_extract_tenant_exception_handling(self):
        """Test exception handling in extract_tenant_from_context."""
        with patch("src.core.otel_integration.tenant_context._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.tenant_context.context") as mock_context:
                mock_context.get_current.side_effect = Exception("OTEL error")
                
                result = extract_tenant_from_context()
                assert result == {}


class TestEnsureTenantAttributesOnSpan:
    """Test ensure_tenant_attributes_on_span function."""

    def test_ensure_attributes_with_provided_tenant_id(self):
        """Test ensuring attributes with provided tenant_id."""
        span = MagicMock()
        
        ensure_tenant_attributes_on_span(span, tenant_id="abc-123", tenant_tier="premium")
        
        span.set_attribute.assert_any_call("tenant.id", "abc-123")
        span.set_attribute.assert_any_call("tenant.tier", "premium")

    def test_ensure_attributes_extract_from_context(self):
        """Test ensuring attributes by extracting from context."""
        span = MagicMock()
        
        with patch("src.core.otel_integration.tenant_context.extract_tenant_from_context") as mock_extract:
            mock_extract.return_value = {"tenant_id": "abc-123", "tenant_tier": "premium"}
            
            ensure_tenant_attributes_on_span(span)
            
            span.set_attribute.assert_any_call("tenant.id", "abc-123")
            span.set_attribute.assert_any_call("tenant.tier", "premium")

    def test_ensure_attributes_lookup_tier(self):
        """Test ensuring attributes with tier lookup."""
        span = MagicMock()
        
        with patch("src.core.otel_integration.tenant_context.get_tenant_tier") as mock_get_tier:
            mock_get_tier.return_value = "premium"
            
            ensure_tenant_attributes_on_span(span, tenant_id="abc-123")
            
            span.set_attribute.assert_any_call("tenant.id", "abc-123")
            span.set_attribute.assert_any_call("tenant.tier", "premium")
            mock_get_tier.assert_called_once_with("abc-123", tier_map=None)

    def test_ensure_attributes_no_tenant_id(self):
        """Test ensuring attributes when no tenant_id is available."""
        span = MagicMock()
        
        with patch("src.core.otel_integration.tenant_context.extract_tenant_from_context") as mock_extract:
            mock_extract.return_value = {}
            
            ensure_tenant_attributes_on_span(span)
            
            span.set_attribute.assert_not_called()

    def test_ensure_attributes_none_span(self):
        """Test ensuring attributes with None span."""
        ensure_tenant_attributes_on_span(None, tenant_id="abc-123")
        # Should not raise error

    def test_ensure_attributes_with_tier_map(self):
        """Test ensuring attributes with custom tier_map."""
        span = MagicMock()
        tier_map = {"abc-123": "premium"}
        
        with patch("src.core.otel_integration.tenant_context.get_tenant_tier") as mock_get_tier:
            mock_get_tier.return_value = "premium"
            
            ensure_tenant_attributes_on_span(span, tenant_id="abc-123", tier_map=tier_map)
            
            mock_get_tier.assert_called_once_with("abc-123", tier_map=tier_map)


class TestSetTenantContextInBaggage:
    """Test set_tenant_context_in_baggage function."""

    def test_set_tenant_context_with_otel_available(self):
        """Test setting tenant context when OTEL is available."""
        with patch("src.core.otel_integration.tenant_context._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.tenant_context.baggage") as mock_baggage, \
                 patch("src.core.otel_integration.tenant_context.context") as mock_context:
                mock_ctx = MagicMock()
                mock_context.get_current.return_value = mock_ctx
                mock_baggage.set_baggage.side_effect = [mock_ctx, mock_ctx]
                
                result = set_tenant_context_in_baggage("abc-123", "premium")
                
                assert result == mock_ctx
                assert mock_baggage.set_baggage.call_count == 2
                mock_baggage.set_baggage.assert_any_call("tenant_id", "abc-123", context=mock_ctx)
                mock_baggage.set_baggage.assert_any_call("tenant_tier", "premium", context=mock_ctx)

    def test_set_tenant_context_tenant_id_only(self):
        """Test setting tenant context with only tenant_id."""
        with patch("src.core.otel_integration.tenant_context._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.tenant_context.baggage") as mock_baggage, \
                 patch("src.core.otel_integration.tenant_context.context") as mock_context:
                mock_ctx = MagicMock()
                mock_context.get_current.return_value = mock_ctx
                mock_baggage.set_baggage.return_value = mock_ctx
                
                result = set_tenant_context_in_baggage("abc-123")
                
                assert result == mock_ctx
                mock_baggage.set_baggage.assert_called_once_with("tenant_id", "abc-123", context=mock_ctx)

    def test_set_tenant_context_with_provided_context(self):
        """Test setting tenant context with provided context."""
        with patch("src.core.otel_integration.tenant_context._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.tenant_context.baggage") as mock_baggage:
                mock_ctx = MagicMock()
                mock_baggage.set_baggage.return_value = mock_ctx
                
                result = set_tenant_context_in_baggage("abc-123", "premium", ctx=mock_ctx)
                
                assert result == mock_ctx
                mock_baggage.set_baggage.assert_any_call("tenant_id", "abc-123", context=mock_ctx)
                mock_baggage.set_baggage.assert_any_call("tenant_tier", "premium", context=mock_ctx)

    def test_set_tenant_context_otel_not_available(self):
        """Test setting tenant context when OTEL is not available."""
        with patch("src.core.otel_integration.tenant_context._OTEL_AVAILABLE", False):
            mock_ctx = MagicMock()
            result = set_tenant_context_in_baggage("abc-123", "premium", ctx=mock_ctx)
            assert result == mock_ctx

    def test_set_tenant_context_exception_handling(self):
        """Test exception handling in set_tenant_context_in_baggage."""
        with patch("src.core.otel_integration.tenant_context._OTEL_AVAILABLE", True):
            with patch("src.core.otel_integration.tenant_context.context") as mock_context:
                mock_context.get_current.side_effect = Exception("OTEL error")
                mock_ctx = MagicMock()
                
                result = set_tenant_context_in_baggage("abc-123", ctx=mock_ctx)
                assert result == mock_ctx


class TestGetTenantAttributesForMetrics:
    """Test get_tenant_attributes_for_metrics function."""

    def test_get_attributes_with_provided_tenant_id(self):
        """Test getting attributes with provided tenant_id."""
        with patch("src.core.otel_integration.tenant_context.get_tenant_tier") as mock_get_tier:
            mock_get_tier.return_value = "premium"
            
            result = get_tenant_attributes_for_metrics(tenant_id="abc-123", tenant_tier="premium")
            
            assert result == {"tenant.id": "abc-123", "tenant.tier": "premium"}

    def test_get_attributes_extract_from_context(self):
        """Test getting attributes by extracting from context."""
        with patch("src.core.otel_integration.tenant_context.extract_tenant_from_context") as mock_extract:
            mock_extract.return_value = {"tenant_id": "abc-123", "tenant_tier": "premium"}
            
            result = get_tenant_attributes_for_metrics()
            
            assert result == {"tenant.id": "abc-123", "tenant.tier": "premium"}

    def test_get_attributes_lookup_tier(self):
        """Test getting attributes with tier lookup."""
        with patch("src.core.otel_integration.tenant_context.extract_tenant_from_context") as mock_extract, \
             patch("src.core.otel_integration.tenant_context.get_tenant_tier") as mock_get_tier:
            mock_extract.return_value = {"tenant_id": "abc-123"}
            mock_get_tier.return_value = "premium"
            
            result = get_tenant_attributes_for_metrics()
            
            assert result == {"tenant.id": "abc-123", "tenant.tier": "premium"}

    def test_get_attributes_no_tenant_id(self):
        """Test getting attributes when no tenant_id is available."""
        with patch("src.core.otel_integration.tenant_context.extract_tenant_from_context") as mock_extract:
            mock_extract.return_value = {}
            
            result = get_tenant_attributes_for_metrics()
            
            assert result == {}

    def test_get_attributes_tenant_id_only(self):
        """Test getting attributes with only tenant_id (no tier)."""
        with patch("src.core.otel_integration.tenant_context.get_tenant_tier") as mock_get_tier:
            mock_get_tier.return_value = None
            
            result = get_tenant_attributes_for_metrics(tenant_id="abc-123")
            
            assert result == {"tenant.id": "abc-123"}

    def test_get_attributes_with_tier_map(self):
        """Test getting attributes with custom tier_map."""
        tier_map = {"abc-123": "premium"}
        
        with patch("src.core.otel_integration.tenant_context.get_tenant_tier") as mock_get_tier:
            mock_get_tier.return_value = "premium"
            
            result = get_tenant_attributes_for_metrics(tenant_id="abc-123", tier_map=tier_map)
            
            assert result == {"tenant.id": "abc-123", "tenant.tier": "premium"}
            mock_get_tier.assert_called_once_with("abc-123", tier_map=tier_map)

