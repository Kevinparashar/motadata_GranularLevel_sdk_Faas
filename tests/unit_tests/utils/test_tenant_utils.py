"""
Tests for tenant utilities.
"""

from unittest.mock import MagicMock

from src.core.utils.tenant_utils import (
    get_tenant_tier,
    set_tenant_tier_mapping,
    set_tenant_tier_mappings,
    clear_tenant_tier_mappings,
    get_tenant_tier_mappings,
    add_tenant_attributes_to_span,
)


class TestGetTenantTier:
    """Test get_tenant_tier function."""
    
    def test_get_tenant_tier_with_mapping(self):
        """Test getting tenant tier from provided mapping."""
        tier_map = {"abc-123": "premium", "def-456": "standard"}
        assert get_tenant_tier("abc-123", tier_map=tier_map) == "premium"
        assert get_tenant_tier("def-456", tier_map=tier_map) == "standard"
        assert get_tenant_tier("unknown", tier_map=tier_map) is None
    
    def test_get_tenant_tier_from_default_mapping(self):
        """Test getting tenant tier from default mapping."""
        clear_tenant_tier_mappings()
        set_tenant_tier_mapping("abc-123", "premium")
        assert get_tenant_tier("abc-123") == "premium"
        assert get_tenant_tier("unknown") is None
    
    def test_get_tenant_tier_none_tenant_id(self):
        """Test getting tenant tier with None tenant_id."""
        assert get_tenant_tier(None) is None
        assert get_tenant_tier("") is None
    
    def test_get_tenant_tier_priority(self):
        """Test that provided mapping takes priority over default."""
        clear_tenant_tier_mappings()
        set_tenant_tier_mapping("abc-123", "basic")
        tier_map = {"abc-123": "premium"}
        assert get_tenant_tier("abc-123", tier_map=tier_map) == "premium"


class TestSetTenantTierMapping:
    """Test set_tenant_tier_mapping function."""
    
    def test_set_tenant_tier_mapping(self):
        """Test setting a single tenant tier mapping."""
        clear_tenant_tier_mappings()
        set_tenant_tier_mapping("abc-123", "premium")
        assert get_tenant_tier("abc-123") == "premium"
    
    def test_set_tenant_tier_mapping_overwrite(self):
        """Test overwriting existing tenant tier mapping."""
        clear_tenant_tier_mappings()
        set_tenant_tier_mapping("abc-123", "basic")
        set_tenant_tier_mapping("abc-123", "premium")
        assert get_tenant_tier("abc-123") == "premium"
    
    def test_set_tenant_tier_mapping_empty_values(self):
        """Test setting mapping with empty values."""
        clear_tenant_tier_mappings()
        set_tenant_tier_mapping("", "premium")
        set_tenant_tier_mapping("abc-123", "")
        # Empty values should not be set
        assert get_tenant_tier("") is None
        assert get_tenant_tier("abc-123") is None


class TestSetTenantTierMappings:
    """Test set_tenant_tier_mappings function."""
    
    def test_set_tenant_tier_mappings(self):
        """Test setting multiple tenant tier mappings."""
        clear_tenant_tier_mappings()
        mappings = {"abc-123": "premium", "def-456": "standard", "ghi-789": "basic"}
        set_tenant_tier_mappings(mappings)
        assert get_tenant_tier("abc-123") == "premium"
        assert get_tenant_tier("def-456") == "standard"
        assert get_tenant_tier("ghi-789") == "basic"
    
    def test_set_tenant_tier_mappings_empty(self):
        """Test setting empty mappings."""
        clear_tenant_tier_mappings()
        set_tenant_tier_mapping("abc-123", "premium")
        set_tenant_tier_mappings({})
        # Existing mappings should remain
        assert get_tenant_tier("abc-123") == "premium"


class TestClearTenantTierMappings:
    """Test clear_tenant_tier_mappings function."""
    
    def test_clear_tenant_tier_mappings(self):
        """Test clearing all tenant tier mappings."""
        set_tenant_tier_mapping("abc-123", "premium")
        clear_tenant_tier_mappings()
        assert get_tenant_tier("abc-123") is None


class TestGetTenantTierMappings:
    """Test get_tenant_tier_mappings function."""
    
    def test_get_tenant_tier_mappings(self):
        """Test getting current tenant tier mappings."""
        clear_tenant_tier_mappings()
        set_tenant_tier_mapping("abc-123", "premium")
        set_tenant_tier_mapping("def-456", "standard")
        mappings = get_tenant_tier_mappings()
        assert mappings == {"abc-123": "premium", "def-456": "standard"}
    
    def test_get_tenant_tier_mappings_copy(self):
        """Test that returned mappings are a copy."""
        clear_tenant_tier_mappings()
        set_tenant_tier_mapping("abc-123", "premium")
        mappings = get_tenant_tier_mappings()
        mappings["def-456"] = "standard"
        # Original should not be affected
        assert get_tenant_tier("def-456") is None


class TestAddTenantAttributesToSpan:
    """Test add_tenant_attributes_to_span function."""
    
    def test_add_tenant_attributes_to_span_with_tenant_id(self):
        """Test adding tenant attributes with tenant_id."""
        span = MagicMock()
        add_tenant_attributes_to_span(span, "abc-123")
        span.set_attribute.assert_any_call("tenant.id", "abc-123")
    
    def test_add_tenant_attributes_to_span_with_tenant_tier(self):
        """Test adding tenant attributes with tenant_tier."""
        span = MagicMock()
        add_tenant_attributes_to_span(span, "abc-123", tenant_tier="premium")
        span.set_attribute.assert_any_call("tenant.id", "abc-123")
        span.set_attribute.assert_any_call("tenant.tier", "premium")
    
    def test_add_tenant_attributes_to_span_lookup_tier(self):
        """Test looking up tenant tier when not provided."""
        clear_tenant_tier_mappings()
        set_tenant_tier_mapping("abc-123", "premium")
        span = MagicMock()
        add_tenant_attributes_to_span(span, "abc-123")
        span.set_attribute.assert_any_call("tenant.id", "abc-123")
        span.set_attribute.assert_any_call("tenant.tier", "premium")
    
    def test_add_tenant_attributes_to_span_custom_prefix(self):
        """Test adding tenant attributes with custom prefix."""
        span = MagicMock()
        add_tenant_attributes_to_span(span, "abc-123", tenant_tier="premium", attribute_prefix="rag")
        span.set_attribute.assert_any_call("rag.id", "abc-123")
        span.set_attribute.assert_any_call("rag.tier", "premium")
    
    def test_add_tenant_attributes_to_span_none_tenant_id(self):
        """Test adding tenant attributes with None tenant_id."""
        span = MagicMock()
        add_tenant_attributes_to_span(span, None)
        # Should not call set_attribute
        span.set_attribute.assert_not_called()
    
    def test_add_tenant_attributes_to_span_with_otel_span(self):
        """Test adding tenant attributes to OTEL span object."""
        span = MagicMock()
        span._span = MagicMock()
        add_tenant_attributes_to_span(span, "abc-123", tenant_tier="premium")
        # Should try both methods
        assert span.set_attribute.called or span._span.set_attribute.called
    
    def test_add_tenant_attributes_to_span_no_span(self):
        """Test adding tenant attributes with None span."""
        add_tenant_attributes_to_span(None, "abc-123")
        # Should not raise error
    
    def test_add_tenant_attributes_to_span_tier_map(self):
        """Test using custom tier_map."""
        span = MagicMock()
        tier_map = {"abc-123": "premium"}
        add_tenant_attributes_to_span(span, "abc-123", tier_map=tier_map)
        span.set_attribute.assert_any_call("tenant.id", "abc-123")
        span.set_attribute.assert_any_call("tenant.tier", "premium")
    
    def test_add_tenant_attributes_to_span_otel_span_exception(self):
        """Test adding attributes to OTEL span with exception handling."""
        span = MagicMock()
        span._span = MagicMock()
        span._span.set_attribute.side_effect = Exception("OTEL error")
        # Should not raise, should handle gracefully
        add_tenant_attributes_to_span(span, "abc-123", tenant_tier="premium")
        # Should have tried to set attributes
        assert span.set_attribute.called or span._span.set_attribute.called
    
    def test_add_tenant_attributes_to_span_no_set_attribute_method(self):
        """Test adding attributes to span without set_attribute method."""
        span = MagicMock()
        del span.set_attribute
        span._span = MagicMock()
        add_tenant_attributes_to_span(span, "abc-123", tenant_tier="premium")
        # Should use _span.set_attribute
        span._span.set_attribute.assert_any_call("tenant.id", "abc-123")

