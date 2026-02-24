"""
Unit tests for PromptHistoryDAL context window state methods.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.faas.shared.dal.prompt_history_dal import PromptHistoryDAL
from src.core.postgresql_database import DatabaseConnection


@pytest.fixture
def mock_db():
    """Create a mock database connection."""
    db = MagicMock(spec=DatabaseConnection)
    db.execute_query = AsyncMock()
    return db


@pytest.fixture
def dal(mock_db):
    """Create a PromptHistoryDAL instance with mocked database."""
    return PromptHistoryDAL(mock_db)


class TestPromptHistoryDALContextWindow:
    """Test cases for PromptHistoryDAL context window state methods."""

    @pytest.mark.asyncio
    async def test_save_context_window_state_new(self, dal, mock_db):
        """Test saving new context window state."""
        tenant_id = "tenant-123"
        max_tokens = 8000
        safety_margin = 300
        current_tokens = 1000
        window_state = {"messages": ["msg1", "msg2"]}

        state_id = "context_window_state_abc123"
        mock_db.execute_query.return_value = {"state_id": state_id}

        result = await dal.save_context_window_state(
            tenant_id=tenant_id,
            user_id="user-456",
            context_id="context-789",
            max_tokens=max_tokens,
            safety_margin=safety_margin,
            current_tokens=current_tokens,
            window_state=window_state,
        )

        assert result == state_id
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        assert params[1] == tenant_id
        assert params[2] == "user-456"
        assert params[3] == "context-789"
        assert params[4] == max_tokens
        assert params[5] == safety_margin
        assert params[6] == current_tokens
        assert json.loads(params[7]) == window_state

    @pytest.mark.asyncio
    async def test_save_context_window_state_update(self, dal, mock_db):
        """Test updating existing context window state."""
        tenant_id = "tenant-123"
        state_id = "context_window_state_abc123"

        mock_db.execute_query.return_value = {"state_id": state_id}

        result = await dal.save_context_window_state(
            tenant_id=tenant_id,
            max_tokens=6000,
            safety_margin=200,
            current_tokens=500,
        )

        assert result == state_id
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "ON CONFLICT" in query  # Should use UPSERT

    @pytest.mark.asyncio
    async def test_get_context_window_state_exists(self, dal, mock_db):
        """Test getting existing context window state."""
        tenant_id = "tenant-123"
        mock_state = {
            "state_id": "state-1",
            "tenant_id": tenant_id,
            "user_id": "user-456",
            "context_id": "context-789",
            "max_tokens": 8000,
            "safety_margin": 300,
            "current_tokens": 1000,
            "window_state": json.dumps({"messages": ["msg1"]}),
            "metadata": json.dumps({}),
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

        mock_db.execute_query.return_value = mock_state

        result = await dal.get_context_window_state(
            tenant_id=tenant_id,
            user_id="user-456",
            context_id="context-789",
        )

        assert result is not None
        assert result["max_tokens"] == 8000
        assert result["safety_margin"] == 300
        assert result["current_tokens"] == 1000
        assert result["window_state"] == {"messages": ["msg1"]}
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_context_window_state_not_exists(self, dal, mock_db):
        """Test getting non-existent context window state."""
        tenant_id = "tenant-unknown"

        mock_db.execute_query.return_value = None

        result = await dal.get_context_window_state(
            tenant_id=tenant_id,
        )

        assert result is None
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_context_window_state_jsonb_already_dict(self, dal, mock_db):
        """Test getting context window state when JSONB is already a dict."""
        tenant_id = "tenant-123"
        mock_state = {
            "state_id": "state-1",
            "tenant_id": tenant_id,
            "max_tokens": 8000,
            "safety_margin": 300,
            "current_tokens": 1000,
            "window_state": {"messages": ["msg1"]},  # Already a dict
            "metadata": {},  # Already a dict
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

        mock_db.execute_query.return_value = mock_state

        result = await dal.get_context_window_state(tenant_id=tenant_id)

        assert result is not None
        assert result["window_state"] == {"messages": ["msg1"]}
        assert result["metadata"] == {}

