"""
Comprehensive tests for PromptHistoryDAL (FaaS version).

Tests all methods and edge cases to achieve >85% coverage.
This file tests the FaaS version in src/faas/shared/dal/prompt_history_dal.py
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.faas.shared.dal.prompt_history_dal import PromptHistoryDAL


class TestPromptHistoryDAL:
    """Test PromptHistoryDAL class."""

    @pytest.fixture
    def mock_db_connection(self):
        """Create a mock database connection."""
        db = MagicMock()
        db.execute_query = AsyncMock()
        return db

    @pytest.fixture
    def dal(self, mock_db_connection):
        """Create PromptHistoryDAL instance."""
        return PromptHistoryDAL(mock_db_connection)

    @pytest.mark.asyncio
    async def test_init(self, mock_db_connection):
        """Test PromptHistoryDAL initialization."""
        dal = PromptHistoryDAL(mock_db_connection)
        assert dal.db == mock_db_connection

    @pytest.mark.asyncio
    async def test_save_history_basic(self, dal, mock_db_connection):
        """Test save_history() with basic parameters."""
        mock_db_connection.execute_query.return_value = {"id": "history-123"}
        
        result = await dal.save_history("Test prompt")
        
        assert result == "history-123"
        call_args = mock_db_connection.execute_query.call_args
        assert "INSERT INTO prompt_history" in call_args[0][0]
        assert call_args[1]["params"][0] == "Test prompt"

    @pytest.mark.asyncio
    async def test_save_history_with_all_params(self, dal, mock_db_connection):
        """Test save_history() with all parameters."""
        mock_db_connection.execute_query.return_value = {"id": "history-123"}
        metadata = {"key": "value", "source": "test"}
        
        result = await dal.save_history(
            prompt="Test prompt",
            tenant_id="tenant-1",
            user_id="user-1",
            context_id="context-1",
            metadata=metadata
        )
        
        assert result == "history-123"
        call_args = mock_db_connection.execute_query.call_args
        assert call_args[1]["params"][1] == "tenant-1"
        assert call_args[1]["params"][2] == "user-1"
        assert call_args[1]["params"][3] == "context-1"
        assert call_args[1]["params"][4] == json.dumps(metadata)

    @pytest.mark.asyncio
    async def test_save_history_with_none_metadata(self, dal, mock_db_connection):
        """Test save_history() with None metadata."""
        mock_db_connection.execute_query.return_value = {"id": "history-123"}
        
        _result = await dal.save_history("Test prompt", metadata=None)
        
        call_args = mock_db_connection.execute_query.call_args
        assert call_args[1]["params"][4] == json.dumps({})

    @pytest.mark.asyncio
    async def test_get_history_basic(self, dal, mock_db_connection):
        """Test get_history() with basic parameters."""
        mock_results = [
            {
                "id": "history-1",
                "prompt": "Test prompt 1",
                "tenant_id": "tenant-1",
                "user_id": "user-1",
                "context_id": "context-1",
                "metadata": json.dumps({"key": "value"}),
                "created_at": "2024-01-01T12:00:00"
            }
        ]
        mock_db_connection.execute_query.return_value = mock_results
        
        result = await dal.get_history()
        
        assert len(result) == 1
        assert result[0]["id"] == "history-1"
        assert result[0]["metadata"] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_history_with_tenant_id(self, dal, mock_db_connection):
        """Test get_history() with tenant_id filter."""
        mock_results = []
        mock_db_connection.execute_query.return_value = mock_results
        
        _result = await dal.get_history(tenant_id="tenant-1")
        
        call_args = mock_db_connection.execute_query.call_args
        assert "AND tenant_id = $" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_history_with_user_id(self, dal, mock_db_connection):
        """Test get_history() with user_id filter."""
        mock_results = []
        mock_db_connection.execute_query.return_value = mock_results
        
        _result = await dal.get_history(user_id="user-1")
        
        call_args = mock_db_connection.execute_query.call_args
        assert "AND user_id = $" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_history_with_context_id(self, dal, mock_db_connection):
        """Test get_history() with context_id filter."""
        mock_results = []
        mock_db_connection.execute_query.return_value = mock_results
        
        _result = await dal.get_history(context_id="context-1")
        
        call_args = mock_db_connection.execute_query.call_args
        assert "AND context_id = $" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_history_with_all_filters(self, dal, mock_db_connection):
        """Test get_history() with all filters."""
        mock_results = []
        mock_db_connection.execute_query.return_value = mock_results
        
        _result = await dal.get_history(
            tenant_id="tenant-1",
            user_id="user-1",
            context_id="context-1",
            limit=50,
            offset=10
        )
        
        call_args = mock_db_connection.execute_query.call_args
        assert "AND tenant_id = $" in call_args[0][0]
        assert "AND user_id = $" in call_args[0][0]
        assert "AND context_id = $" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_history_parses_metadata(self, dal, mock_db_connection):
        """Test get_history() parses metadata correctly."""
        mock_results = [
            {
                "id": "history-1",
                "prompt": "Test prompt",
                "tenant_id": "tenant-1",
                "user_id": None,
                "context_id": None,
                "metadata": json.dumps({"key": "value"}),
                "created_at": "2024-01-01T12:00:00"
            }
        ]
        mock_db_connection.execute_query.return_value = mock_results
        
        result = await dal.get_history()
        
        assert result[0]["metadata"] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_history_metadata_as_dict(self, dal, mock_db_connection):
        """Test get_history() when metadata is already a dict."""
        mock_results = [
            {
                "id": "history-1",
                "prompt": "Test prompt",
                "tenant_id": "tenant-1",
                "user_id": None,
                "context_id": None,
                "metadata": {"key": "value"},  # Already a dict
                "created_at": "2024-01-01T12:00:00"
            }
        ]
        mock_db_connection.execute_query.return_value = mock_results
        
        result = await dal.get_history()
        
        assert result[0]["metadata"] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_history_empty_result(self, dal, mock_db_connection):
        """Test get_history() with empty result."""
        mock_db_connection.execute_query.return_value = None
        
        result = await dal.get_history()
        
        assert result == []

    @pytest.mark.asyncio
    async def test_delete_history_basic(self, dal, mock_db_connection):
        """Test delete_history() with basic parameters."""
        mock_db_connection.execute_query.return_value = 1  # Rows affected
        
        result = await dal.delete_history("history-123")
        
        assert result is True
        call_args = mock_db_connection.execute_query.call_args
        assert "DELETE FROM prompt_history" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_delete_history_with_tenant_id(self, dal, mock_db_connection):
        """Test delete_history() with tenant_id."""
        mock_db_connection.execute_query.return_value = 1
        
        _result = await dal.delete_history("history-123", tenant_id="tenant-1")
        
        call_args = mock_db_connection.execute_query.call_args
        assert "AND tenant_id = $2" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_delete_history_not_found(self, dal, mock_db_connection):
        """Test delete_history() when history not found."""
        mock_db_connection.execute_query.return_value = 0  # No rows affected
        
        result = await dal.delete_history("nonexistent")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_cleanup_old_history_basic(self, dal, mock_db_connection):
        """Test cleanup_old_history() with basic parameters."""
        mock_db_connection.execute_query.return_value = 5  # Rows deleted
        
        result = await dal.cleanup_old_history(days=30)
        
        assert result == 5
        call_args = mock_db_connection.execute_query.call_args
        assert "DELETE FROM prompt_history" in call_args[0][0]
        assert "INTERVAL '30 days'" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_cleanup_old_history_with_tenant_id(self, dal, mock_db_connection):
        """Test cleanup_old_history() with tenant_id."""
        mock_db_connection.execute_query.return_value = 3
        
        result = await dal.cleanup_old_history(days=30, tenant_id="tenant-1")
        
        assert result == 3
        call_args = mock_db_connection.execute_query.call_args
        assert "WHERE tenant_id = $1 AND" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_cleanup_old_history_no_rows_deleted(self, dal, mock_db_connection):
        """Test cleanup_old_history() when no rows deleted."""
        mock_db_connection.execute_query.return_value = None
        
        result = await dal.cleanup_old_history(days=30)
        
        assert result == 0

    @pytest.mark.asyncio
    async def test_cleanup_old_history_custom_days(self, dal, mock_db_connection):
        """Test cleanup_old_history() with custom days."""
        mock_db_connection.execute_query.return_value = 10
        
        _result = await dal.cleanup_old_history(days=60)
        
        call_args = mock_db_connection.execute_query.call_args
        assert "INTERVAL '60 days'" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_save_context_window_state_basic(self, dal, mock_db_connection):
        """Test save_context_window_state() with basic parameters."""
        mock_db_connection.execute_query.return_value = {"state_id": "state-123"}
        
        result = await dal.save_context_window_state(
            tenant_id="tenant-1",
            max_tokens=4000,
            safety_margin=200,
            current_tokens=1000
        )
        
        assert result == "state-123"
        call_args = mock_db_connection.execute_query.call_args
        assert "INSERT INTO prompt_context_window_state" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_save_context_window_state_with_all_params(self, dal, mock_db_connection):
        """Test save_context_window_state() with all parameters."""
        mock_db_connection.execute_query.return_value = {"state_id": "state-123"}
        window_state = {"messages": ["msg1", "msg2"]}
        metadata = {"key": "value"}
        
        result = await dal.save_context_window_state(
            tenant_id="tenant-1",
            user_id="user-1",
            context_id="context-1",
            max_tokens=4000,
            safety_margin=200,
            current_tokens=1000,
            window_state=window_state,
            metadata=metadata
        )
        
        assert result == "state-123"
        call_args = mock_db_connection.execute_query.call_args
        assert call_args[1]["params"][1] == "tenant-1"
        assert call_args[1]["params"][2] == "user-1"
        assert call_args[1]["params"][3] == "context-1"
        assert call_args[1]["params"][7] == json.dumps(window_state)
        assert call_args[1]["params"][8] == json.dumps(metadata)

    @pytest.mark.asyncio
    async def test_save_context_window_state_with_none_window_state(self, dal, mock_db_connection):
        """Test save_context_window_state() with None window_state."""
        mock_db_connection.execute_query.return_value = {"state_id": "state-123"}
        
        _result = await dal.save_context_window_state(
            tenant_id="tenant-1",
            window_state=None
        )
        
        call_args = mock_db_connection.execute_query.call_args
        assert call_args[1]["params"][7] is None

    @pytest.mark.asyncio
    async def test_save_context_window_state_with_none_metadata(self, dal, mock_db_connection):
        """Test save_context_window_state() with None metadata."""
        mock_db_connection.execute_query.return_value = {"state_id": "state-123"}
        
        _result = await dal.save_context_window_state(
            tenant_id="tenant-1",
            metadata=None
        )
        
        call_args = mock_db_connection.execute_query.call_args
        assert call_args[1]["params"][8] == json.dumps({})

    @pytest.mark.asyncio
    async def test_save_context_window_state_on_conflict_update(self, dal, mock_db_connection):
        """Test save_context_window_state() updates on conflict."""
        mock_db_connection.execute_query.return_value = {"state_id": "state-123"}
        
        _result = await dal.save_context_window_state(
            tenant_id="tenant-1",
            current_tokens=2000
        )
        
        call_args = mock_db_connection.execute_query.call_args
        assert "ON CONFLICT" in call_args[0][0]
        assert "DO UPDATE SET" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_save_context_window_state_no_result(self, dal, mock_db_connection):
        """Test save_context_window_state() when no result returned."""
        mock_db_connection.execute_query.return_value = None
        
        result = await dal.save_context_window_state(tenant_id="tenant-1")
        
        # Should return the generated state_id
        assert result is not None
        assert result.startswith("context_window_state_")

    @pytest.mark.asyncio
    async def test_get_context_window_state_basic(self, dal, mock_db_connection):
        """Test get_context_window_state() with basic parameters."""
        mock_result = {
            "state_id": "state-123",
            "tenant_id": "tenant-1",
            "user_id": None,
            "context_id": None,
            "max_tokens": 4000,
            "safety_margin": 200,
            "current_tokens": 1000,
            "window_state": json.dumps({"messages": ["msg1"]}),
            "metadata": json.dumps({"key": "value"}),
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00"
        }
        mock_db_connection.execute_query.return_value = mock_result
        
        result = await dal.get_context_window_state(tenant_id="tenant-1")
        
        assert result is not None
        assert result["state_id"] == "state-123"
        assert result["window_state"] == {"messages": ["msg1"]}
        assert result["metadata"] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_context_window_state_with_user_context(self, dal, mock_db_connection):
        """Test get_context_window_state() with user_id and context_id."""
        mock_result = {
            "state_id": "state-123",
            "tenant_id": "tenant-1",
            "user_id": "user-1",
            "context_id": "context-1",
            "max_tokens": 4000,
            "safety_margin": 200,
            "current_tokens": 1000,
            "window_state": None,
            "metadata": None,
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00"
        }
        mock_db_connection.execute_query.return_value = mock_result
        
        result = await dal.get_context_window_state(
            tenant_id="tenant-1",
            user_id="user-1",
            context_id="context-1"
        )
        
        assert result is not None
        call_args = mock_db_connection.execute_query.call_args
        assert call_args[1]["params"][1] == "user-1"
        assert call_args[1]["params"][2] == "context-1"

    @pytest.mark.asyncio
    async def test_get_context_window_state_not_found(self, dal, mock_db_connection):
        """Test get_context_window_state() when state not found."""
        mock_db_connection.execute_query.return_value = None
        
        result = await dal.get_context_window_state(tenant_id="tenant-1")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_context_window_state_window_state_as_dict(self, dal, mock_db_connection):
        """Test get_context_window_state() when window_state is already a dict."""
        mock_result = {
            "state_id": "state-123",
            "tenant_id": "tenant-1",
            "user_id": None,
            "context_id": None,
            "max_tokens": 4000,
            "safety_margin": 200,
            "current_tokens": 1000,
            "window_state": {"messages": ["msg1"]},  # Already a dict
            "metadata": None,
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00"
        }
        mock_db_connection.execute_query.return_value = mock_result
        
        result = await dal.get_context_window_state(tenant_id="tenant-1")
        
        assert result["window_state"] == {"messages": ["msg1"]}

    @pytest.mark.asyncio
    async def test_get_context_window_state_metadata_as_dict(self, dal, mock_db_connection):
        """Test get_context_window_state() when metadata is already a dict."""
        mock_result = {
            "state_id": "state-123",
            "tenant_id": "tenant-1",
            "user_id": None,
            "context_id": None,
            "max_tokens": 4000,
            "safety_margin": 200,
            "current_tokens": 1000,
            "window_state": None,
            "metadata": {"key": "value"},  # Already a dict
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00"
        }
        mock_db_connection.execute_query.return_value = mock_result
        
        result = await dal.get_context_window_state(tenant_id="tenant-1")
        
        assert result["metadata"] == {"key": "value"}

