"""
Tests for tenant utilities.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.core.utils.tenant_utils import (
    get_tenant_tier,
    get_tenant_tier_async,
    set_tenant_tier_mapping,
    set_tenant_tier_mapping_async,
    set_tenant_tier_mappings,
    set_tenant_tier_mappings_async,
    clear_tenant_tier_mappings,
    get_tenant_tier_mappings,
    add_tenant_attributes_to_span,
    TenantContextManager,
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


class TestGetTenantTierAsync:
    """Test get_tenant_tier_async function."""
    
    @pytest.mark.asyncio
    async def test_get_tenant_tier_async_with_mapping(self):
        """Test getting tenant tier from provided mapping."""
        tier_map = {"abc-123": "premium", "def-456": "standard"}
        result = await get_tenant_tier_async("abc-123", tier_map=tier_map)
        assert result == "premium"
    
    @pytest.mark.asyncio
    async def test_get_tenant_tier_async_with_dal(self):
        """Test getting tenant tier from DAL."""
        mock_dal = MagicMock()
        mock_dal.get_tenant_tier = AsyncMock(return_value="premium")
        
        result = await get_tenant_tier_async("abc-123", tenant_context_dal=mock_dal)
        
        assert result == "premium"
        mock_dal.get_tenant_tier.assert_called_once_with("abc-123")
    
    @pytest.mark.asyncio
    async def test_get_tenant_tier_async_dal_priority_over_default(self):
        """Test that DAL takes priority over default mapping."""
        clear_tenant_tier_mappings()
        set_tenant_tier_mapping("abc-123", "basic")
        
        mock_dal = MagicMock()
        mock_dal.get_tenant_tier = AsyncMock(return_value="premium")
        
        result = await get_tenant_tier_async("abc-123", tenant_context_dal=mock_dal)
        
        assert result == "premium"  # DAL result, not default
    
    @pytest.mark.asyncio
    async def test_get_tenant_tier_async_dal_fallback_to_default(self):
        """Test that default mapping is used when DAL returns None."""
        clear_tenant_tier_mappings()
        set_tenant_tier_mapping("abc-123", "standard")
        
        mock_dal = MagicMock()
        mock_dal.get_tenant_tier = AsyncMock(return_value=None)
        
        result = await get_tenant_tier_async("abc-123", tenant_context_dal=mock_dal)
        
        assert result == "standard"  # Falls back to default
    
    @pytest.mark.asyncio
    async def test_get_tenant_tier_async_dal_exception_handling(self):
        """Test that DAL exceptions are handled gracefully."""
        clear_tenant_tier_mappings()
        set_tenant_tier_mapping("abc-123", "standard")
        
        mock_dal = MagicMock()
        mock_dal.get_tenant_tier = AsyncMock(side_effect=Exception("DAL error"))
        
        result = await get_tenant_tier_async("abc-123", tenant_context_dal=mock_dal)
        
        assert result == "standard"  # Falls back to default on exception
    
    @pytest.mark.asyncio
    async def test_get_tenant_tier_async_none_tenant_id(self):
        """Test getting tenant tier with None tenant_id."""
        result = await get_tenant_tier_async(None)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_tenant_tier_async_mapping_priority_over_dal(self):
        """Test that provided mapping takes priority over DAL."""
        mock_dal = MagicMock()
        mock_dal.get_tenant_tier = AsyncMock(return_value="basic")
        
        tier_map = {"abc-123": "premium"}
        result = await get_tenant_tier_async("abc-123", tenant_context_dal=mock_dal, tier_map=tier_map)
        
        assert result == "premium"  # Mapping takes priority
        mock_dal.get_tenant_tier.assert_not_called()  # DAL not called when mapping provided


class TestSetTenantTierMappingAsync:
    """Test set_tenant_tier_mapping_async function."""
    
    @pytest.mark.asyncio
    async def test_set_tenant_tier_mapping_async_basic(self):
        """Test setting tenant tier mapping (async)."""
        clear_tenant_tier_mappings()
        await set_tenant_tier_mapping_async("abc-123", "premium")
        assert get_tenant_tier("abc-123") == "premium"
    
    @pytest.mark.asyncio
    async def test_set_tenant_tier_mapping_async_with_dal(self):
        """Test setting tenant tier mapping with DAL persistence."""
        clear_tenant_tier_mappings()
        mock_dal = MagicMock()
        mock_dal.set_tenant_tier = AsyncMock()
        mock_dal.save_tenant_activity = AsyncMock()
        
        await set_tenant_tier_mapping_async("abc-123", "premium", tenant_context_dal=mock_dal)
        
        assert get_tenant_tier("abc-123") == "premium"
        mock_dal.set_tenant_tier.assert_called_once_with("abc-123", "premium")
        mock_dal.save_tenant_activity.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_set_tenant_tier_mapping_async_with_activity_tracking(self):
        """Test setting tenant tier mapping with activity tracking."""
        clear_tenant_tier_mappings()
        mock_dal = MagicMock()
        mock_dal.set_tenant_tier = AsyncMock()
        mock_dal.save_tenant_activity = AsyncMock()
        
        await set_tenant_tier_mapping_async(
            "abc-123",
            "premium",
            tenant_context_dal=mock_dal,
            component="test_component",
            user_id="user-1",
            correlation_id="corr-1"
        )
        
        activity_call = mock_dal.save_tenant_activity.call_args
        assert activity_call[1]["tenant_id"] == "abc-123"
        assert activity_call[1]["activity_type"] == "config_change"
        assert activity_call[1]["component"] == "test_component"
        assert activity_call[1]["user_id"] == "user-1"
        assert activity_call[1]["correlation_id"] == "corr-1"
    
    @pytest.mark.asyncio
    async def test_set_tenant_tier_mapping_async_dal_exception(self):
        """Test that DAL exceptions are handled gracefully."""
        clear_tenant_tier_mappings()
        mock_dal = MagicMock()
        mock_dal.set_tenant_tier = AsyncMock(side_effect=Exception("DAL error"))
        
        await set_tenant_tier_mapping_async("abc-123", "premium", tenant_context_dal=mock_dal)
        
        # Should still set in default mapping
        assert get_tenant_tier("abc-123") == "premium"
    
    @pytest.mark.asyncio
    async def test_set_tenant_tier_mapping_async_empty_values(self):
        """Test setting mapping with empty values."""
        clear_tenant_tier_mappings()
        await set_tenant_tier_mapping_async("", "premium")
        await set_tenant_tier_mapping_async("abc-123", "")
        # Empty values should not be set
        assert get_tenant_tier("") is None
        assert get_tenant_tier("abc-123") is None


class TestSetTenantTierMappingsAsync:
    """Test set_tenant_tier_mappings_async function."""
    
    @pytest.mark.asyncio
    async def test_set_tenant_tier_mappings_async_basic(self):
        """Test setting multiple tenant tier mappings (async)."""
        clear_tenant_tier_mappings()
        mappings = {"abc-123": "premium", "def-456": "standard"}
        await set_tenant_tier_mappings_async(mappings)
        assert get_tenant_tier("abc-123") == "premium"
        assert get_tenant_tier("def-456") == "standard"
    
    @pytest.mark.asyncio
    async def test_set_tenant_tier_mappings_async_with_dal(self):
        """Test setting multiple mappings with DAL persistence."""
        clear_tenant_tier_mappings()
        mock_dal = MagicMock()
        mock_dal.set_tenant_tier = AsyncMock()
        mock_dal.save_tenant_activity = AsyncMock()
        
        mappings = {"abc-123": "premium", "def-456": "standard"}
        await set_tenant_tier_mappings_async(mappings, tenant_context_dal=mock_dal)
        
        assert mock_dal.set_tenant_tier.call_count == 2
        assert mock_dal.save_tenant_activity.call_count == 2
    
    @pytest.mark.asyncio
    async def test_set_tenant_tier_mappings_async_dal_exception(self):
        """Test that DAL exceptions are handled gracefully."""
        clear_tenant_tier_mappings()
        mock_dal = MagicMock()
        mock_dal.set_tenant_tier = AsyncMock(side_effect=Exception("DAL error"))
        
        mappings = {"abc-123": "premium"}
        await set_tenant_tier_mappings_async(mappings, tenant_context_dal=mock_dal)
        
        # Should still set in default mapping
        assert get_tenant_tier("abc-123") == "premium"
    
    @pytest.mark.asyncio
    async def test_set_tenant_tier_mappings_async_empty_mappings(self):
        """Test setting empty mappings."""
        clear_tenant_tier_mappings()
        set_tenant_tier_mapping("abc-123", "premium")
        await set_tenant_tier_mappings_async({})
        # Existing mappings should remain
        assert get_tenant_tier("abc-123") == "premium"


class TestTenantContextManager:
    """Test TenantContextManager class."""
    
    @pytest.fixture
    def mock_dal(self):
        """Create a mock TenantContextMetadataDAL."""
        dal = MagicMock()
        dal.save_tenant_activity = AsyncMock(return_value="activity-123")
        dal.get_tenant_metadata = AsyncMock(return_value={"tier": "premium"})
        dal.save_tenant_metadata = AsyncMock(return_value="tenant-1")
        dal.get_tenant_configuration = AsyncMock(return_value={"setting": "value"})
        dal.update_tenant_configuration = AsyncMock(return_value=True)
        dal.get_tenant_activity_history = AsyncMock(return_value=[{"id": "act-1"}])
        return dal
    
    @pytest.fixture
    def manager_no_dal(self):
        """Create TenantContextManager without DAL."""
        return TenantContextManager()
    
    @pytest.fixture
    def manager_with_dal(self, mock_dal):
        """Create TenantContextManager with DAL."""
        return TenantContextManager(tenant_context_dal=mock_dal)
    
    @pytest.mark.asyncio
    async def test_init_without_dal(self):
        """Test TenantContextManager initialization without DAL."""
        manager = TenantContextManager()
        assert manager.tenant_context_dal is None
    
    @pytest.mark.asyncio
    async def test_init_with_dal(self, mock_dal):
        """Test TenantContextManager initialization with DAL."""
        manager = TenantContextManager(tenant_context_dal=mock_dal)
        assert manager.tenant_context_dal == mock_dal
    
    @pytest.mark.asyncio
    async def test_track_tenant_activity_with_dal(self, manager_with_dal, mock_dal):
        """Test track_tenant_activity() with DAL."""
        result = await manager_with_dal.track_tenant_activity(
            tenant_id="tenant-1",
            activity_type="test_activity",
            activity_description="Test description",
            component="test_component",
            user_id="user-1",
            correlation_id="corr-1",
            activity_data={"key": "value"},
            metadata={"meta": "data"}
        )
        
        assert result == "activity-123"
        mock_dal.save_tenant_activity.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_track_tenant_activity_without_dal(self, manager_no_dal):
        """Test track_tenant_activity() without DAL."""
        result = await manager_no_dal.track_tenant_activity(
            tenant_id="tenant-1",
            activity_type="test_activity"
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_track_tenant_activity_dal_exception(self, manager_with_dal, mock_dal):
        """Test track_tenant_activity() when DAL raises exception."""
        mock_dal.save_tenant_activity = AsyncMock(side_effect=Exception("DAL error"))
        
        result = await manager_with_dal.track_tenant_activity(
            tenant_id="tenant-1",
            activity_type="test_activity"
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_tenant_metadata_with_dal(self, manager_with_dal, mock_dal):
        """Test get_tenant_metadata() with DAL."""
        result = await manager_with_dal.get_tenant_metadata("tenant-1")
        
        assert result == {"tier": "premium"}
        mock_dal.get_tenant_metadata.assert_called_once_with("tenant-1")
    
    @pytest.mark.asyncio
    async def test_get_tenant_metadata_without_dal(self, manager_no_dal):
        """Test get_tenant_metadata() without DAL."""
        result = await manager_no_dal.get_tenant_metadata("tenant-1")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_tenant_metadata_dal_exception(self, manager_with_dal, mock_dal):
        """Test get_tenant_metadata() when DAL raises exception."""
        mock_dal.get_tenant_metadata = AsyncMock(side_effect=Exception("DAL error"))
        
        result = await manager_with_dal.get_tenant_metadata("tenant-1")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_save_tenant_metadata_with_dal(self, manager_with_dal, mock_dal):
        """Test save_tenant_metadata() with DAL."""
        result = await manager_with_dal.save_tenant_metadata(
            tenant_id="tenant-1",
            tenant_tier="premium",
            configuration={"setting": "value"},
            metadata={"meta": "data"}
        )
        
        assert result == "tenant-1"
        mock_dal.save_tenant_metadata.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_tenant_metadata_without_dal(self, manager_no_dal):
        """Test save_tenant_metadata() without DAL."""
        result = await manager_no_dal.save_tenant_metadata("tenant-1")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_save_tenant_metadata_dal_exception(self, manager_with_dal, mock_dal):
        """Test save_tenant_metadata() when DAL raises exception."""
        mock_dal.save_tenant_metadata = AsyncMock(side_effect=Exception("DAL error"))
        
        result = await manager_with_dal.save_tenant_metadata("tenant-1")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_tenant_configuration_with_dal(self, manager_with_dal, mock_dal):
        """Test get_tenant_configuration() with DAL."""
        result = await manager_with_dal.get_tenant_configuration("tenant-1")
        
        assert result == {"setting": "value"}
        mock_dal.get_tenant_configuration.assert_called_once_with("tenant-1")
    
    @pytest.mark.asyncio
    async def test_get_tenant_configuration_without_dal(self, manager_no_dal):
        """Test get_tenant_configuration() without DAL."""
        result = await manager_no_dal.get_tenant_configuration("tenant-1")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_tenant_configuration_dal_exception(self, manager_with_dal, mock_dal):
        """Test get_tenant_configuration() when DAL raises exception."""
        mock_dal.get_tenant_configuration = AsyncMock(side_effect=Exception("DAL error"))
        
        result = await manager_with_dal.get_tenant_configuration("tenant-1")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_tenant_configuration_with_dal_success(self, manager_with_dal, mock_dal):
        """Test update_tenant_configuration() with DAL success."""
        result = await manager_with_dal.update_tenant_configuration(
            tenant_id="tenant-1",
            configuration={"new_setting": "new_value"},
            component="test_component",
            user_id="user-1",
            correlation_id="corr-1"
        )
        
        assert result is True
        mock_dal.update_tenant_configuration.assert_called_once()
        mock_dal.save_tenant_activity.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_tenant_configuration_without_dal(self, manager_no_dal):
        """Test update_tenant_configuration() without DAL."""
        result = await manager_no_dal.update_tenant_configuration(
            tenant_id="tenant-1",
            configuration={"setting": "value"}
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_tenant_configuration_dal_exception(self, manager_with_dal, mock_dal):
        """Test update_tenant_configuration() when DAL raises exception."""
        mock_dal.update_tenant_configuration = AsyncMock(side_effect=Exception("DAL error"))
        
        result = await manager_with_dal.update_tenant_configuration(
            tenant_id="tenant-1",
            configuration={"setting": "value"}
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_tenant_configuration_no_activity_on_failure(self, manager_with_dal, mock_dal):
        """Test that activity is not tracked when update fails."""
        mock_dal.update_tenant_configuration = AsyncMock(return_value=False)
        
        result = await manager_with_dal.update_tenant_configuration(
            tenant_id="tenant-1",
            configuration={"setting": "value"}
        )
        
        assert result is False
        mock_dal.save_tenant_activity.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_tenant_activity_history_with_dal(self, manager_with_dal, mock_dal):
        """Test get_tenant_activity_history() with DAL."""
        result = await manager_with_dal.get_tenant_activity_history(
            tenant_id="tenant-1",
            activity_type="test_activity",
            component="test_component",
            user_id="user-1",
            limit=50,
            offset=10
        )
        
        assert len(result) == 1
        mock_dal.get_tenant_activity_history.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_tenant_activity_history_without_dal(self, manager_no_dal):
        """Test get_tenant_activity_history() without DAL."""
        result = await manager_no_dal.get_tenant_activity_history("tenant-1")
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_tenant_activity_history_dal_exception(self, manager_with_dal, mock_dal):
        """Test get_tenant_activity_history() when DAL raises exception."""
        mock_dal.get_tenant_activity_history = AsyncMock(side_effect=Exception("DAL error"))
        
        result = await manager_with_dal.get_tenant_activity_history("tenant-1")
        
        assert result == []

