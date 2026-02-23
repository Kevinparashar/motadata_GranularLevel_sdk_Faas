"""
Unit Tests for Session DAL

Tests database operations for agent session persistence.
"""


import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.agno_agent_framework.session import (
    AgentSession,
    SessionStatus,
)
from src.faas.shared.dal.session_dal import SessionDAL


class TestSessionDAL:
    """Test SessionDAL class."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database connection."""
        db = MagicMock()
        db.execute_query = AsyncMock()
        return db

    @pytest.fixture
    def session_dal(self, mock_db):
        """Create a SessionDAL instance."""
        return SessionDAL(mock_db)

    @pytest.fixture
    def sample_session(self):
        """Create a sample AgentSession."""
        session = AgentSession(
            agent_id="agent1",
            max_history=100,
            expires_at=datetime.now() + timedelta(hours=1),
        )
        session.add_message("user", "Hello")
        session.add_message("assistant", "Hi there")
        session.set_context("key1", "value1")
        session.set_variable("var1", "val1")
        return session

    @pytest.mark.asyncio
    async def test_save_session(self, session_dal, mock_db, sample_session):
        """Test saving a session to database."""
        await session_dal.save_session(sample_session, "tenant_123")

        # Verify session was saved
        assert mock_db.execute_query.call_count >= 2  # Session + messages
        session_call = mock_db.execute_query.call_args_list[0]
        assert "INSERT INTO agent_sessions" in session_call[0][0]
        assert session_call[1]["params"][0] == sample_session.session_id
        assert session_call[1]["params"][1] == "agent1"
        assert session_call[1]["params"][2] == "tenant_123"

    @pytest.mark.asyncio
    async def test_save_session_with_messages(self, session_dal, mock_db, sample_session):
        """Test saving session with messages."""
        await session_dal.save_session(sample_session, "tenant_123")

        # Verify messages were deleted and re-inserted
        delete_call = None
        insert_calls = []
        for call in mock_db.execute_query.call_args_list:
            query = call[0][0]
            if "DELETE FROM session_messages" in query:
                delete_call = call
            elif "INSERT INTO session_messages" in query:
                insert_calls.append(call)

        assert delete_call is not None
        assert len(insert_calls) == 2  # Two messages

    @pytest.mark.asyncio
    async def test_load_session(self, session_dal, mock_db):
        """Test loading a session from database."""
        # Mock session row
        session_row = {
            "session_id": "session_123",
            "agent_id": "agent1",
            "status": "active",
            "max_history": 100,
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "expires_at": None,
            "context": json.dumps({"key1": "value1"}),
            "variables": json.dumps({"var1": "val1"}),
            "metadata": json.dumps({}),
        }

        # Mock messages rows
        messages_rows = [
            {
                "message_id": "msg1",
                "session_id": "session_123",
                "role": "user",
                "content": "Hello",
                "timestamp": datetime.now(),
                "metadata": json.dumps({}),
            },
            {
                "message_id": "msg2",
                "session_id": "session_123",
                "role": "assistant",
                "content": "Hi",
                "timestamp": datetime.now(),
                "metadata": json.dumps({}),
            },
        ]

        mock_db.execute_query.side_effect = [session_row, messages_rows]

        session = await session_dal.load_session("session_123", "tenant_123")

        assert session is not None
        assert session.session_id == "session_123"
        assert session.agent_id == "agent1"
        assert session.status == SessionStatus.ACTIVE
        assert len(session.messages) == 2
        assert session.messages[0].content == "Hello"
        assert session.messages[1].content == "Hi"

    @pytest.mark.asyncio
    async def test_load_session_not_found(self, session_dal, mock_db):
        """Test loading non-existent session."""
        mock_db.execute_query.return_value = None

        session = await session_dal.load_session("nonexistent", "tenant_123")

        assert session is None

    @pytest.mark.asyncio
    async def test_load_session_no_messages(self, session_dal, mock_db):
        """Test loading session with no messages."""
        session_row = {
            "session_id": "session_123",
            "agent_id": "agent1",
            "status": "active",
            "max_history": 100,
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "expires_at": None,
            "context": json.dumps({}),
            "variables": json.dumps({}),
            "metadata": json.dumps({}),
        }

        mock_db.execute_query.side_effect = [session_row, []]

        session = await session_dal.load_session("session_123", "tenant_123")

        assert session is not None
        assert len(session.messages) == 0

    @pytest.mark.asyncio
    async def test_list_agent_sessions(self, session_dal, mock_db):
        """Test listing sessions for an agent."""
        session_rows = [
            {
                "session_id": "session_1",
                "agent_id": "agent1",
                "status": "active",
                "max_history": 100,
                "created_at": datetime.now(),
                "last_activity": datetime.now(),
                "expires_at": None,
                "context": json.dumps({}),
                "variables": json.dumps({}),
                "metadata": json.dumps({}),
            },
            {
                "session_id": "session_2",
                "agent_id": "agent1",
                "status": "paused",
                "max_history": 50,
                "created_at": datetime.now(),
                "last_activity": datetime.now(),
                "expires_at": None,
                "context": json.dumps({}),
                "variables": json.dumps({}),
                "metadata": json.dumps({}),
            },
        ]

        mock_db.execute_query.side_effect = [session_rows, [], []]  # Sessions, then messages for each

        sessions = await session_dal.list_agent_sessions("agent1", "tenant_123")

        assert len(sessions) == 2
        assert sessions[0].session_id == "session_1"
        assert sessions[1].session_id == "session_2"

    @pytest.mark.asyncio
    async def test_list_agent_sessions_empty(self, session_dal, mock_db):
        """Test listing sessions when none exist."""
        mock_db.execute_query.return_value = []

        sessions = await session_dal.list_agent_sessions("agent1", "tenant_123")

        assert len(sessions) == 0

    @pytest.mark.asyncio
    async def test_delete_session(self, session_dal, mock_db):
        """Test deleting a session."""
        mock_db.execute_query.return_value = 1  # 1 row deleted

        result = await session_dal.delete_session("session_123", "tenant_123")

        assert result is True
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        assert "DELETE FROM agent_sessions" in call_args[0][0]
        assert call_args[1]["params"][0] == "session_123"
        assert call_args[1]["params"][1] == "tenant_123"

    @pytest.mark.asyncio
    async def test_delete_session_not_found(self, session_dal, mock_db):
        """Test deleting non-existent session."""
        mock_db.execute_query.return_value = 0  # 0 rows deleted

        result = await session_dal.delete_session("nonexistent", "tenant_123")

        assert result is False

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, session_dal, mock_db):
        """Test cleaning up expired sessions."""
        mock_db.execute_query.return_value = 5  # 5 sessions deleted

        count = await session_dal.cleanup_expired_sessions()

        assert count == 5
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        assert "DELETE FROM agent_sessions" in call_args[0][0]
        assert "expires_at < CURRENT_TIMESTAMP" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_update_session_activity(self, session_dal, mock_db):
        """Test updating session activity."""
        mock_db.execute_query.return_value = 1  # 1 row updated
        last_activity = datetime.now()

        result = await session_dal.update_session_activity(
            "session_123", "tenant_123", last_activity
        )

        assert result is True
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        assert "UPDATE agent_sessions" in call_args[0][0]
        assert call_args[1]["params"][0] == last_activity

    @pytest.mark.asyncio
    async def test_update_session_activity_default(self, session_dal, mock_db):
        """Test updating session activity with default timestamp."""
        mock_db.execute_query.return_value = 1

        result = await session_dal.update_session_activity("session_123", "tenant_123")

        assert result is True
        call_args = mock_db.execute_query.call_args
        assert call_args[1]["params"][0] is not None

    @pytest.mark.asyncio
    async def test_update_session_activity_not_found(self, session_dal, mock_db):
        """Test updating activity for non-existent session."""
        mock_db.execute_query.return_value = 0  # 0 rows updated

        result = await session_dal.update_session_activity("nonexistent", "tenant_123")

        assert result is False

    @pytest.mark.asyncio
    async def test_session_exists(self, session_dal, mock_db):
        """Test checking if session exists."""
        mock_db.execute_query.return_value = {"1": 1}  # Row exists

        result = await session_dal.session_exists("session_123", "tenant_123")

        assert result is True
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        assert "SELECT 1 FROM agent_sessions" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_session_exists_not_found(self, session_dal, mock_db):
        """Test checking if non-existent session exists."""
        mock_db.execute_query.return_value = None

        result = await session_dal.session_exists("nonexistent", "tenant_123")

        assert result is False

    @pytest.mark.asyncio
    async def test_save_session_with_json_context(self, session_dal, mock_db, sample_session):
        """Test saving session with complex JSON context."""
        sample_session.context = {"nested": {"key": "value"}, "list": [1, 2, 3]}
        sample_session.variables = {"var1": "val1", "var2": 42}

        await session_dal.save_session(sample_session, "tenant_123")

        session_call = mock_db.execute_query.call_args_list[0]
        context_param = session_call[1]["params"][8]  # context is 9th param (index 8)
        variables_param = session_call[1]["params"][9]  # variables is 10th param (index 9)

        # Verify JSON serialization
        assert isinstance(context_param, str)
        assert isinstance(variables_param, str)
        parsed_context = json.loads(context_param)
        assert parsed_context["nested"]["key"] == "value"

    @pytest.mark.asyncio
    async def test_load_session_with_dict_context(self, session_dal, mock_db):
        """Test loading session when context is already a dict (not JSON string)."""
        session_row = {
            "session_id": "session_123",
            "agent_id": "agent1",
            "status": "active",
            "max_history": 100,
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "expires_at": None,
            "context": {"key1": "value1"},  # Already a dict
            "variables": {"var1": "val1"},  # Already a dict
            "metadata": {},  # Already a dict
        }

        mock_db.execute_query.side_effect = [session_row, []]

        session = await session_dal.load_session("session_123", "tenant_123")

        assert session is not None
        assert isinstance(session.context, dict)
        assert session.context["key1"] == "value1"

