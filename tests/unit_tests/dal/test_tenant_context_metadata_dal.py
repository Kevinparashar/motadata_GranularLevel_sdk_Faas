"""
Unit tests for TenantContextMetadataDAL.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.faas.shared.dal.tenant_context_metadata_dal import TenantContextMetadataDAL
from src.core.postgresql_database import DatabaseConnection


@pytest.fixture
def mock_db():
    """Create a mock database connection."""
    db = MagicMock(spec=DatabaseConnection)
    db.execute_query = AsyncMock()
    return db


@pytest.fixture
def dal(mock_db):
    """Create a TenantContextMetadataDAL instance with mocked database."""
    return TenantContextMetadataDAL(mock_db)


class TestTenantContextMetadataDAL:
    """Test cases for TenantContextMetadataDAL."""

    @pytest.mark.asyncio
    async def test_save_tenant_metadata_new(self, dal, mock_db):
        """Test saving new tenant metadata."""
        tenant_id = "tenant-123"
        tenant_tier = "premium"
        configuration = {"max_requests": 1000}
        metadata = {"region": "us-east-1"}

        mock_db.execute_query.return_value = {"tenant_id": tenant_id}

        result = await dal.save_tenant_metadata(
            tenant_id=tenant_id,
            tenant_tier=tenant_tier,
            configuration=configuration,
            metadata=metadata,
        )

        assert result == tenant_id
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        assert call_args[1]["params"][0] == tenant_id
        assert call_args[1]["params"][1] == tenant_tier
        assert json.loads(call_args[1]["params"][2]) == configuration
        assert json.loads(call_args[1]["params"][3]) == metadata

    @pytest.mark.asyncio
    async def test_save_tenant_metadata_update(self, dal, mock_db):
        """Test updating existing tenant metadata."""
        tenant_id = "tenant-123"
        tenant_tier = "standard"

        mock_db.execute_query.return_value = {"tenant_id": tenant_id}

        result = await dal.save_tenant_metadata(
            tenant_id=tenant_id,
            tenant_tier=tenant_tier,
        )

        assert result == tenant_id
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_tenant_metadata_minimal(self, dal, mock_db):
        """Test saving tenant metadata with minimal fields."""
        tenant_id = "tenant-123"

        mock_db.execute_query.return_value = {"tenant_id": tenant_id}

        result = await dal.save_tenant_metadata(tenant_id=tenant_id)

        assert result == tenant_id
        call_args = mock_db.execute_query.call_args
        assert call_args[1]["params"][0] == tenant_id
        assert call_args[1]["params"][1] is None  # tenant_tier
        assert call_args[1]["params"][2] is None  # configuration
        assert json.loads(call_args[1]["params"][3]) == {}  # metadata

    @pytest.mark.asyncio
    async def test_get_tenant_metadata_exists(self, dal, mock_db):
        """Test getting existing tenant metadata."""
        tenant_id = "tenant-123"
        mock_result = {
            "tenant_id": tenant_id,
            "tenant_tier": "premium",
            "configuration": json.dumps({"max_requests": 1000}),
            "metadata": json.dumps({"region": "us-east-1"}),
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

        mock_db.execute_query.return_value = mock_result

        result = await dal.get_tenant_metadata(tenant_id)

        assert result is not None
        assert result["tenant_id"] == tenant_id
        assert result["tenant_tier"] == "premium"
        assert result["configuration"] == {"max_requests": 1000}
        assert result["metadata"] == {"region": "us-east-1"}
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        assert call_args[1]["params"][0] == tenant_id

    @pytest.mark.asyncio
    async def test_get_tenant_metadata_not_exists(self, dal, mock_db):
        """Test getting non-existent tenant metadata."""
        tenant_id = "tenant-unknown"

        mock_db.execute_query.return_value = None

        result = await dal.get_tenant_metadata(tenant_id)

        assert result is None
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_tenant_metadata_jsonb_already_dict(self, dal, mock_db):
        """Test getting tenant metadata when JSONB is already a dict."""
        tenant_id = "tenant-123"
        mock_result = {
            "tenant_id": tenant_id,
            "tenant_tier": "premium",
            "configuration": {"max_requests": 1000},  # Already a dict
            "metadata": {"region": "us-east-1"},  # Already a dict
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

        mock_db.execute_query.return_value = mock_result

        result = await dal.get_tenant_metadata(tenant_id)

        assert result is not None
        assert result["configuration"] == {"max_requests": 1000}
        assert result["metadata"] == {"region": "us-east-1"}

    @pytest.mark.asyncio
    async def test_save_tenant_activity(self, dal, mock_db):
        """Test saving tenant activity."""
        tenant_id = "tenant-123"
        activity_type = "request"
        activity_description = "API request"
        component = "gateway"
        user_id = "user-456"
        correlation_id = "corr-789"
        activity_data = {"endpoint": "/api/v1/query"}
        metadata = {"ip": "192.168.1.1"}

        activity_id = "tenant_activity_abc123"
        mock_db.execute_query.return_value = {"activity_id": activity_id}

        result = await dal.save_tenant_activity(
            tenant_id=tenant_id,
            activity_type=activity_type,
            activity_description=activity_description,
            component=component,
            user_id=user_id,
            correlation_id=correlation_id,
            activity_data=activity_data,
            metadata=metadata,
        )

        assert result == activity_id
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        assert params[1] == tenant_id
        assert params[2] == activity_type
        assert params[3] == activity_description
        assert params[4] == component
        assert params[5] == user_id
        assert params[6] == correlation_id
        assert json.loads(params[7]) == activity_data
        assert json.loads(params[8]) == metadata

    @pytest.mark.asyncio
    async def test_save_tenant_activity_minimal(self, dal, mock_db):
        """Test saving tenant activity with minimal fields."""
        tenant_id = "tenant-123"
        activity_type = "operation"

        activity_id = "tenant_activity_abc123"
        mock_db.execute_query.return_value = {"activity_id": activity_id}

        result = await dal.save_tenant_activity(
            tenant_id=tenant_id,
            activity_type=activity_type,
        )

        assert result == activity_id
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        assert params[1] == tenant_id
        assert params[2] == activity_type
        assert params[3] is None  # activity_description
        assert params[4] is None  # component
        assert params[5] is None  # user_id
        assert params[6] is None  # correlation_id
        assert params[7] is None  # activity_data
        assert json.loads(params[8]) == {}  # metadata

    @pytest.mark.asyncio
    async def test_get_tenant_activity_history(self, dal, mock_db):
        """Test getting tenant activity history."""
        tenant_id = "tenant-123"
        mock_results = [
            {
                "activity_id": "activity-1",
                "tenant_id": tenant_id,
                "activity_type": "request",
                "activity_description": "API request",
                "component": "gateway",
                "user_id": "user-456",
                "correlation_id": "corr-789",
                "activity_data": json.dumps({"endpoint": "/api/v1/query"}),
                "metadata": json.dumps({"ip": "192.168.1.1"}),
                "created_at": "2024-01-01T00:00:00",
            },
            {
                "activity_id": "activity-2",
                "tenant_id": tenant_id,
                "activity_type": "operation",
                "activity_description": "Document ingestion",
                "component": "rag",
                "user_id": None,
                "correlation_id": None,
                "activity_data": None,
                "metadata": json.dumps({}),
                "created_at": "2024-01-01T01:00:00",
            },
        ]

        mock_db.execute_query.return_value = mock_results

        result = await dal.get_tenant_activity_history(tenant_id, limit=10, offset=0)

        assert len(result) == 2
        assert result[0]["activity_id"] == "activity-1"
        assert result[0]["activity_type"] == "request"
        assert result[0]["activity_data"] == {"endpoint": "/api/v1/query"}
        assert result[1]["activity_type"] == "operation"
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_tenant_activity_history_with_filters(self, dal, mock_db):
        """Test getting tenant activity history with filters."""
        tenant_id = "tenant-123"
        activity_type = "request"
        component = "gateway"
        user_id = "user-456"

        mock_db.execute_query.return_value = []

        result = await dal.get_tenant_activity_history(
            tenant_id=tenant_id,
            activity_type=activity_type,
            component=component,
            user_id=user_id,
            limit=50,
            offset=10,
        )

        assert result == []
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "activity_type = $2" in query
        assert "component = $3" in query
        assert "user_id = $4" in query

    @pytest.mark.asyncio
    async def test_get_tenant_activity_history_empty(self, dal, mock_db):
        """Test getting tenant activity history when empty."""
        tenant_id = "tenant-123"

        mock_db.execute_query.return_value = None

        result = await dal.get_tenant_activity_history(tenant_id)

        assert result == []
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_tenant_configuration_exists(self, dal, mock_db):
        """Test getting tenant configuration when it exists."""
        tenant_id = "tenant-123"
        configuration = {"max_requests": 1000, "rate_limit": 100}
        mock_metadata = {
            "tenant_id": tenant_id,
            "tenant_tier": "premium",
            "configuration": json.dumps(configuration),
            "metadata": json.dumps({}),
        }

        mock_db.execute_query.return_value = mock_metadata

        result = await dal.get_tenant_configuration(tenant_id)

        assert result == configuration
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_tenant_configuration_not_exists(self, dal, mock_db):
        """Test getting tenant configuration when tenant doesn't exist."""
        tenant_id = "tenant-unknown"

        mock_db.execute_query.return_value = None

        result = await dal.get_tenant_configuration(tenant_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_tenant_configuration_no_config(self, dal, mock_db):
        """Test getting tenant configuration when config is None."""
        tenant_id = "tenant-123"
        mock_metadata = {
            "tenant_id": tenant_id,
            "tenant_tier": "premium",
            "configuration": None,
            "metadata": json.dumps({}),
        }

        mock_db.execute_query.return_value = mock_metadata

        result = await dal.get_tenant_configuration(tenant_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_update_tenant_configuration_new(self, dal, mock_db):
        """Test updating tenant configuration for new tenant."""
        tenant_id = "tenant-123"
        configuration = {"max_requests": 2000}

        # First call: get_tenant_metadata returns None
        # Second call: save_tenant_metadata
        mock_db.execute_query.side_effect = [
            None,  # get_tenant_metadata
            {"tenant_id": tenant_id},  # save_tenant_metadata
        ]

        result = await dal.update_tenant_configuration(tenant_id, configuration)

        assert result is True
        assert mock_db.execute_query.call_count == 2

    @pytest.mark.asyncio
    async def test_update_tenant_configuration_existing(self, dal, mock_db):
        """Test updating tenant configuration for existing tenant."""
        tenant_id = "tenant-123"
        existing_config = {"max_requests": 1000}
        new_config = {"rate_limit": 100}
        expected_merged = {"max_requests": 1000, "rate_limit": 100}

        mock_metadata = {
            "tenant_id": tenant_id,
            "tenant_tier": "premium",
            "configuration": json.dumps(existing_config),
            "metadata": json.dumps({}),
        }

        mock_db.execute_query.side_effect = [
            mock_metadata,  # get_tenant_metadata
            {"tenant_id": tenant_id},  # save_tenant_metadata
        ]

        result = await dal.update_tenant_configuration(tenant_id, new_config)

        assert result is True
        assert mock_db.execute_query.call_count == 2
        # Verify merged config was saved
        call_args = mock_db.execute_query.call_args
        saved_config = json.loads(call_args[1]["params"][2])
        assert saved_config == expected_merged

    @pytest.mark.asyncio
    async def test_get_tenant_tier_exists(self, dal, mock_db):
        """Test getting tenant tier when it exists."""
        tenant_id = "tenant-123"
        tenant_tier = "premium"
        mock_metadata = {
            "tenant_id": tenant_id,
            "tenant_tier": tenant_tier,
            "configuration": None,
            "metadata": json.dumps({}),
        }

        mock_db.execute_query.return_value = mock_metadata

        result = await dal.get_tenant_tier(tenant_id)

        assert result == tenant_tier
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_tenant_tier_not_exists(self, dal, mock_db):
        """Test getting tenant tier when tenant doesn't exist."""
        tenant_id = "tenant-unknown"

        mock_db.execute_query.return_value = None

        result = await dal.get_tenant_tier(tenant_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_set_tenant_tier_new(self, dal, mock_db):
        """Test setting tenant tier for new tenant."""
        tenant_id = "tenant-123"
        tenant_tier = "premium"

        mock_db.execute_query.side_effect = [
            None,  # get_tenant_metadata
            {"tenant_id": tenant_id},  # save_tenant_metadata
        ]

        result = await dal.set_tenant_tier(tenant_id, tenant_tier)

        assert result is True
        assert mock_db.execute_query.call_count == 2

    @pytest.mark.asyncio
    async def test_set_tenant_tier_existing(self, dal, mock_db):
        """Test setting tenant tier for existing tenant."""
        tenant_id = "tenant-123"
        tenant_tier = "standard"
        existing_config = {"max_requests": 1000}

        mock_metadata = {
            "tenant_id": tenant_id,
            "tenant_tier": "premium",
            "configuration": json.dumps(existing_config),
            "metadata": json.dumps({}),
        }

        mock_db.execute_query.side_effect = [
            mock_metadata,  # get_tenant_metadata
            {"tenant_id": tenant_id},  # save_tenant_metadata
        ]

        result = await dal.set_tenant_tier(tenant_id, tenant_tier)

        assert result is True
        assert mock_db.execute_query.call_count == 2
        # Verify tier was updated
        call_args = mock_db.execute_query.call_args
        assert call_args[1]["params"][1] == tenant_tier

    @pytest.mark.asyncio
    async def test_get_tenant_activity_stats(self, dal, mock_db):
        """Test getting tenant activity statistics."""
        tenant_id = "tenant-123"
        mock_stats = {
            "total_activities": 100,
            "unique_activity_types": 5,
            "unique_components": 3,
            "unique_users": 10,
            "unique_correlations": 50,
        }

        mock_db.execute_query.return_value = mock_stats

        result = await dal.get_tenant_activity_stats(tenant_id)

        assert result == mock_stats
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        assert call_args[1]["params"][0] == tenant_id

    @pytest.mark.asyncio
    async def test_get_tenant_activity_stats_with_time_range(self, dal, mock_db):
        """Test getting tenant activity statistics with time range."""
        tenant_id = "tenant-123"
        time_range_hours = 24
        mock_stats = {
            "total_activities": 50,
            "unique_activity_types": 3,
            "unique_components": 2,
            "unique_users": 5,
            "unique_correlations": 25,
        }

        mock_db.execute_query.return_value = mock_stats

        result = await dal.get_tenant_activity_stats(tenant_id, time_range_hours=time_range_hours)

        assert result == mock_stats
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "INTERVAL" in query
        assert call_args[1]["params"][1] == time_range_hours

    @pytest.mark.asyncio
    async def test_get_tenant_activity_stats_empty(self, dal, mock_db):
        """Test getting tenant activity statistics when no activities."""
        tenant_id = "tenant-123"

        mock_db.execute_query.return_value = None

        result = await dal.get_tenant_activity_stats(tenant_id)

        assert result == {
            "total_activities": 0,
            "unique_activity_types": 0,
            "unique_components": 0,
            "unique_users": 0,
            "unique_correlations": 0,
        }

    @pytest.mark.asyncio
    async def test_get_tenant_component_activity(self, dal, mock_db):
        """Test getting tenant activity for a specific component."""
        tenant_id = "tenant-123"
        component = "gateway"
        mock_results = [
            {
                "activity_id": "activity-1",
                "tenant_id": tenant_id,
                "activity_type": "request",
                "component": component,
                "activity_data": json.dumps({"endpoint": "/api/v1/query"}),
                "metadata": json.dumps({}),
                "created_at": "2024-01-01T00:00:00",
            },
        ]

        mock_db.execute_query.return_value = mock_results

        result = await dal.get_tenant_component_activity(tenant_id, component, limit=10)

        assert len(result) == 1
        assert result[0]["component"] == component
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        assert call_args[1]["params"][0] == tenant_id
        assert call_args[1]["params"][1] == component

    @pytest.mark.asyncio
    async def test_get_tenant_component_activity_with_time_range(self, dal, mock_db):
        """Test getting tenant component activity with time range."""
        tenant_id = "tenant-123"
        component = "rag"
        time_range_hours = 24

        mock_db.execute_query.return_value = []

        result = await dal.get_tenant_component_activity(
            tenant_id, component, time_range_hours=time_range_hours, limit=50
        )

        assert result == []
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "INTERVAL" in query

    @pytest.mark.asyncio
    async def test_list_tenants(self, dal, mock_db):
        """Test listing tenants."""
        mock_results = [
            {
                "tenant_id": "tenant-1",
                "tenant_tier": "premium",
                "configuration": json.dumps({"max_requests": 1000}),
                "metadata": json.dumps({}),
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            },
            {
                "tenant_id": "tenant-2",
                "tenant_tier": "standard",
                "configuration": None,
                "metadata": json.dumps({}),
                "created_at": "2024-01-01T01:00:00",
                "updated_at": "2024-01-01T01:00:00",
            },
        ]

        mock_db.execute_query.return_value = mock_results

        result = await dal.list_tenants(limit=10, offset=0)

        assert len(result) == 2
        assert result[0]["tenant_id"] == "tenant-1"
        assert result[0]["tenant_tier"] == "premium"
        assert result[1]["tenant_id"] == "tenant-2"
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tenants_with_tier_filter(self, dal, mock_db):
        """Test listing tenants with tier filter."""
        tenant_tier = "premium"
        mock_results = [
            {
                "tenant_id": "tenant-1",
                "tenant_tier": tenant_tier,
                "configuration": None,
                "metadata": json.dumps({}),
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            },
        ]

        mock_db.execute_query.return_value = mock_results

        result = await dal.list_tenants(tenant_tier=tenant_tier, limit=10, offset=0)

        assert len(result) == 1
        assert result[0]["tenant_tier"] == tenant_tier
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "tenant_tier = $1" in query
        assert call_args[1]["params"][0] == tenant_tier

    @pytest.mark.asyncio
    async def test_list_tenants_empty(self, dal, mock_db):
        """Test listing tenants when empty."""
        mock_db.execute_query.return_value = None

        result = await dal.list_tenants()

        assert result == []
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_old_activity_all_tenants(self, dal, mock_db):
        """Test cleaning up old activity for all tenants."""
        days = 90
        deleted_count = 50

        mock_db.execute_query.return_value = deleted_count

        result = await dal.cleanup_old_activity(days=days)

        assert result == deleted_count
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert f"{days} days" in query
        assert call_args[1]["params"] is None or len(call_args[1]["params"]) == 0

    @pytest.mark.asyncio
    async def test_cleanup_old_activity_specific_tenant(self, dal, mock_db):
        """Test cleaning up old activity for a specific tenant."""
        tenant_id = "tenant-123"
        days = 30
        deleted_count = 10

        mock_db.execute_query.return_value = deleted_count

        result = await dal.cleanup_old_activity(days=days, tenant_id=tenant_id)

        assert result == deleted_count
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert f"{days} days" in query
        assert "tenant_id = $1" in query
        assert call_args[1]["params"][0] == tenant_id

    @pytest.mark.asyncio
    async def test_cleanup_old_activity_no_result(self, dal, mock_db):
        """Test cleaning up old activity when no result returned."""
        days = 90

        mock_db.execute_query.return_value = None

        result = await dal.cleanup_old_activity(days=days)

        assert result == 0

