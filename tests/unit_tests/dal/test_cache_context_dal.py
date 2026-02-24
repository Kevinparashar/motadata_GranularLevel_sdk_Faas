"""
Unit Tests for Cache Context DAL

Tests for cache context and history persistence operations.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.faas.shared.dal.cache_context_dal import CacheContextDAL
from src.core.postgresql_database import DatabaseConnection


class TestCacheContextDAL:
    """Tests for CacheContextDAL."""

    @pytest.fixture
    def mock_db(self):
        """Mock database connection."""
        db = MagicMock(spec=DatabaseConnection)
        db.execute_query = AsyncMock()
        return db

    @pytest.fixture
    def cache_context_dal(self, mock_db):
        """CacheContextDAL fixture."""
        return CacheContextDAL(mock_db)

    @pytest.mark.asyncio
    async def test_save_cache_operation_set(self, cache_context_dal, mock_db):
        """Test successful cache set operation save."""
        mock_db.execute_query.return_value = {"operation_id": "op_123"}

        result = await cache_context_dal.save_cache_operation(
            cache_key="test_key",
            operation="set",
            tenant_id="tenant-1",
            user_id="user-1",
            conversation_id="conv-1",
            value_size=1024,
            ttl=300,
            reason="query_result",
        )

        assert result == "op_123"
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        assert "INSERT INTO cache_context" in call_args[0][0]
        params = call_args[1]["params"]
        assert params[1] == "test_key"
        assert params[2] == "set"
        assert params[3] == "tenant-1"

    @pytest.mark.asyncio
    async def test_save_cache_operation_get_hit(self, cache_context_dal, mock_db):
        """Test save cache get operation with hit."""
        mock_db.execute_query.return_value = {"operation_id": "op_456"}

        result = await cache_context_dal.save_cache_operation(
            cache_key="test_key",
            operation="get",
            tenant_id="tenant-1",
            cache_hit=True,
        )

        assert result == "op_456"
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        assert params[2] == "get"
        assert params[7] is True  # cache_hit

    @pytest.mark.asyncio
    async def test_save_cache_operation_get_miss(self, cache_context_dal, mock_db):
        """Test save cache get operation with miss."""
        mock_db.execute_query.return_value = {"operation_id": "op_789"}

        result = await cache_context_dal.save_cache_operation(
            cache_key="test_key",
            operation="get",
            tenant_id="tenant-1",
            cache_hit=False,
        )

        assert result == "op_789"
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        assert params[7] is False  # cache_hit

    @pytest.mark.asyncio
    async def test_save_cache_operation_with_metadata(self, cache_context_dal, mock_db):
        """Test save cache operation with metadata."""
        mock_db.execute_query.return_value = {"operation_id": "op_meta"}

        metadata = {"backend": "memory", "duration_ms": 10.5}
        result = await cache_context_dal.save_cache_operation(
            cache_key="test_key",
            operation="set",
            tenant_id="tenant-1",
            metadata=metadata,
        )

        assert result == "op_meta"
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        assert json.loads(params[11]) == metadata

    @pytest.mark.asyncio
    async def test_get_cache_history_basic(self, cache_context_dal, mock_db):
        """Test get cache history with basic filters."""
        mock_db.execute_query.return_value = [
            {
                "operation_id": "op1",
                "cache_key": "key1",
                "operation": "set",
                "tenant_id": "tenant-1",
                "created_at": datetime.now(),
            }
        ]

        results = await cache_context_dal.get_cache_history(
            tenant_id="tenant-1",
            limit=10,
            offset=0,
        )

        assert len(results) == 1
        assert results[0]["operation"] == "set"
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cache_history_with_all_filters(self, cache_context_dal, mock_db):
        """Test get cache history with all filters."""
        mock_db.execute_query.return_value = []

        results = await cache_context_dal.get_cache_history(
            tenant_id="tenant-1",
            user_id="user-1",
            conversation_id="conv-1",
            operation="get",
            limit=50,
            offset=10,
        )

        assert results == []
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "tenant_id" in query
        assert "user_id" in query
        assert "conversation_id" in query
        assert "operation" in query
        assert "LIMIT" in query
        assert "OFFSET" in query

    @pytest.mark.asyncio
    async def test_get_cache_history_with_json_parsing(self, cache_context_dal, mock_db):
        """Test get cache history with JSON metadata parsing."""
        mock_db.execute_query.return_value = [
            {
                "operation_id": "op1",
                "cache_key": "key1",
                "operation": "set",
                "metadata": json.dumps({"backend": "memory"}),
            }
        ]

        results = await cache_context_dal.get_cache_history()

        assert len(results) == 1
        assert isinstance(results[0]["metadata"], dict)

    @pytest.mark.asyncio
    async def test_get_cache_stats_basic(self, cache_context_dal, mock_db):
        """Test get cache stats."""
        mock_db.execute_query.return_value = {
            "total_operations": 100,
            "get_operations": 60,
            "set_operations": 30,
            "delete_operations": 10,
            "cache_hits": 40,
            "cache_misses": 20,
            "avg_value_size": 1024.5,
            "total_value_size": 102400,
        }

        stats = await cache_context_dal.get_cache_stats(tenant_id="tenant-1")

        assert stats["total_operations"] == 100
        assert stats["get_operations"] == 60
        assert stats["set_operations"] == 30
        assert stats["delete_operations"] == 10
        assert stats["cache_hits"] == 40
        assert stats["cache_misses"] == 20
        assert stats["hit_rate"] == pytest.approx(66.67, abs=0.01)
        assert stats["avg_value_size"] == 1024.5

    @pytest.mark.asyncio
    async def test_get_cache_stats_with_filters(self, cache_context_dal, mock_db):
        """Test get cache stats with all filters."""
        mock_db.execute_query.return_value = {
            "total_operations": 50,
            "get_operations": 30,
            "set_operations": 15,
            "delete_operations": 5,
            "cache_hits": 25,
            "cache_misses": 5,
            "avg_value_size": 512.0,
            "total_value_size": 25600,
        }

        stats = await cache_context_dal.get_cache_stats(
            tenant_id="tenant-1",
            user_id="user-1",
            conversation_id="conv-1",
            time_range_hours=24,
        )

        assert stats["total_operations"] == 50
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "tenant_id" in query
        assert "user_id" in query
        assert "conversation_id" in query
        assert "INTERVAL" in query

    @pytest.mark.asyncio
    async def test_get_cache_stats_empty(self, cache_context_dal, mock_db):
        """Test get cache stats when no data."""
        mock_db.execute_query.return_value = None

        stats = await cache_context_dal.get_cache_stats()

        assert stats["total_operations"] == 0
        assert stats["hit_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_get_cache_stats_zero_hits_misses(self, cache_context_dal, mock_db):
        """Test get cache stats with zero hits and misses."""
        mock_db.execute_query.return_value = {
            "total_operations": 10,
            "get_operations": 0,
            "set_operations": 10,
            "delete_operations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_value_size": 0,
            "total_value_size": 0,
        }

        stats = await cache_context_dal.get_cache_stats()

        assert stats["hit_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_invalidate_conversation_cache(self, cache_context_dal, mock_db):
        """Test invalidate conversation cache."""
        mock_db.execute_query.return_value = [
            {"cache_key": "key1"},
            {"cache_key": "key2"},
        ]

        keys = await cache_context_dal.invalidate_conversation_cache(
            conversation_id="conv-1",
            tenant_id="tenant-1",
        )

        assert len(keys) == 2
        assert "key1" in keys
        assert "key2" in keys
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "conversation_id = $1" in query
        assert "tenant_id = $2" in query

    @pytest.mark.asyncio
    async def test_invalidate_conversation_cache_without_tenant(self, cache_context_dal, mock_db):
        """Test invalidate conversation cache without tenant."""
        mock_db.execute_query.return_value = [{"cache_key": "key1"}]

        keys = await cache_context_dal.invalidate_conversation_cache(
            conversation_id="conv-1"
        )

        assert len(keys) == 1
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "tenant_id" not in query

    @pytest.mark.asyncio
    async def test_invalidate_session_cache(self, cache_context_dal, mock_db):
        """Test invalidate session cache."""
        mock_db.execute_query.return_value = [
            {"cache_key": "session_key1"},
            {"cache_key": "session_key2"},
        ]

        keys = await cache_context_dal.invalidate_session_cache(
            session_id="session-1",
            tenant_id="tenant-1",
        )

        assert len(keys) == 2
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "session_id = $1" in query

    @pytest.mark.asyncio
    async def test_invalidate_session_cache_empty(self, cache_context_dal, mock_db):
        """Test invalidate session cache with empty result."""
        mock_db.execute_query.return_value = None

        keys = await cache_context_dal.invalidate_session_cache(
            session_id="session-1"
        )

        assert keys == []

    @pytest.mark.asyncio
    async def test_get_cache_keys_by_reason(self, cache_context_dal, mock_db):
        """Test get cache keys by reason."""
        mock_db.execute_query.return_value = [
            {"cache_key": "query_key1"},
            {"cache_key": "query_key2"},
        ]

        keys = await cache_context_dal.get_cache_keys_by_reason(
            reason="query_result",
            tenant_id="tenant-1",
            limit=10,
        )

        assert len(keys) == 2
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "reason = $1" in query

    @pytest.mark.asyncio
    async def test_get_cache_keys_by_reason_without_tenant(self, cache_context_dal, mock_db):
        """Test get cache keys by reason without tenant."""
        mock_db.execute_query.return_value = [{"cache_key": "key1"}]

        keys = await cache_context_dal.get_cache_keys_by_reason(
            reason="embedding",
            limit=20,
        )

        assert len(keys) == 1
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "tenant_id" not in query

    @pytest.mark.asyncio
    async def test_cleanup_old_history(self, cache_context_dal, mock_db):
        """Test cleanup old history."""
        mock_db.execute_query.return_value = 25

        result = await cache_context_dal.cleanup_old_history(
            days=90,
            tenant_id="tenant-1",
        )

        assert result == 25
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "DELETE FROM cache_context" in query
        assert "INTERVAL" in query

    @pytest.mark.asyncio
    async def test_cleanup_old_history_without_tenant(self, cache_context_dal, mock_db):
        """Test cleanup old history without tenant."""
        mock_db.execute_query.return_value = 50

        result = await cache_context_dal.cleanup_old_history(days=30)

        assert result == 50

    @pytest.mark.asyncio
    async def test_get_conversation_cache_keys(self, cache_context_dal, mock_db):
        """Test get conversation cache keys with metadata."""
        mock_db.execute_query.return_value = [
            {
                "cache_key": "key1",
                "operation": "set",
                "cache_hit": None,
                "value_size": 1024,
                "ttl": 300,
                "reason": "query_result",
                "metadata": json.dumps({"backend": "memory"}),
                "created_at": datetime.now(),
            }
        ]

        results = await cache_context_dal.get_conversation_cache_keys(
            conversation_id="conv-1",
            tenant_id="tenant-1",
        )

        assert len(results) == 1
        assert results[0]["cache_key"] == "key1"
        assert isinstance(results[0]["metadata"], dict)

    @pytest.mark.asyncio
    async def test_get_conversation_cache_keys_empty(self, cache_context_dal, mock_db):
        """Test get conversation cache keys with empty result."""
        mock_db.execute_query.return_value = None

        results = await cache_context_dal.get_conversation_cache_keys(
            conversation_id="conv-1"
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_get_cache_history_empty(self, cache_context_dal, mock_db):
        """Test get cache history with empty result."""
        mock_db.execute_query.return_value = None

        results = await cache_context_dal.get_cache_history()

        assert results == []

    @pytest.mark.asyncio
    async def test_save_cache_operation_with_none_values(self, cache_context_dal, mock_db):
        """Test save cache operation with None optional values."""
        mock_db.execute_query.return_value = {"operation_id": "op_none"}

        result = await cache_context_dal.save_cache_operation(
            cache_key="test_key",
            operation="delete",
        )

        assert result == "op_none"
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        # Check that None values are handled
        assert params[3] is None  # tenant_id
        assert params[4] is None  # user_id
        assert params[5] is None  # conversation_id

