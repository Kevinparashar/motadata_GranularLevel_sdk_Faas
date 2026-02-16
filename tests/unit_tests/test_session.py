"""
Unit Tests for Agent Session Management

Tests session management functionality for agents.
"""


from datetime import datetime, timedelta

import pytest

from src.core.agno_agent_framework.session import (
    AgentSession,
    SessionManager,
    SessionMessage,
    SessionStatus,
)


class TestSessionStatus:
    """Test SessionStatus enum."""

    def test_session_status_values(self):
        """Test SessionStatus enum values."""
        assert SessionStatus.ACTIVE == "active"
        assert SessionStatus.PAUSED == "paused"
        assert SessionStatus.COMPLETED == "completed"
        assert SessionStatus.EXPIRED == "expired"


class TestSessionMessage:
    """Test SessionMessage class."""

    def test_session_message_init(self):
        """Test SessionMessage initialization."""
        message = SessionMessage(role="user", content="Hello")

        assert message.role == "user"
        assert message.content == "Hello"
        assert message.message_id is not None
        assert message.timestamp is not None
        assert message.metadata == {}

    def test_session_message_with_metadata(self):
        """Test SessionMessage with metadata."""
        message = SessionMessage(
            role="assistant", content="Hi", metadata={"key": "value"}
        )

        assert message.metadata == {"key": "value"}


class TestAgentSession:
    """Test AgentSession class."""

    @pytest.fixture
    def session(self):
        """Create an AgentSession instance."""
        return AgentSession(agent_id="agent1")

    def test_init(self):
        """Test AgentSession initialization."""
        session = AgentSession(agent_id="agent1", max_history=50)

        assert session.agent_id == "agent1"
        assert session.status == SessionStatus.ACTIVE
        assert session.max_history == 50
        assert len(session.messages) == 0
        assert len(session.context) == 0
        assert len(session.variables) == 0

    def test_add_message(self, session):
        """Test add_message method to cover lines 77-86."""
        message = session.add_message("user", "Hello", metadata={"key": "value"})

        assert message.role == "user"
        assert message.content == "Hello"
        assert message.metadata == {"key": "value"}
        assert len(session.messages) == 1
        assert session.messages[0] == message

    def test_add_message_trims_history(self, session):
        """Test add_message trims history when exceeds max to cover lines 83-84."""
        session.max_history = 5

        # Add more messages than max_history
        for i in range(10):
            session.add_message("user", f"Message {i}")

        assert len(session.messages) == 5
        # Should keep the last 5 messages
        assert session.messages[0].content == "Message 5"

    def test_get_conversation_history(self, session):
        """Test get_conversation_history method."""
        session.add_message("user", "Hello")
        session.add_message("assistant", "Hi")
        session.add_message("user", "How are you?")

        history = session.get_conversation_history()

        assert len(history) == 3

    def test_get_conversation_history_with_limit(self, session):
        """Test get_conversation_history with limit to cover lines 106-107."""
        for i in range(5):
            session.add_message("user", f"Message {i}")

        history = session.get_conversation_history(limit=3)

        assert len(history) == 3
        assert history[0].content == "Message 2"

    def test_get_conversation_history_with_role_filter(self, session):
        """Test get_conversation_history with role_filter to cover lines 103-104."""
        session.add_message("user", "Hello")
        session.add_message("assistant", "Hi")
        session.add_message("user", "How are you?")

        user_messages = session.get_conversation_history(role_filter="user")

        assert len(user_messages) == 2
        assert all(m.role == "user" for m in user_messages)

    def test_set_context(self, session):
        """Test set_context method to cover lines 122-123."""
        session.set_context("key1", "value1")

        assert session.context["key1"] == "value1"
        assert session.last_activity is not None

    def test_get_context(self, session):
        """Test get_context method to cover line 136."""
        session.set_context("key1", "value1")

        value = session.get_context("key1")
        assert value == "value1"

        default = session.get_context("nonexistent", "default")
        assert default == "default"

    def test_set_variable(self, session):
        """Test set_variable method to cover lines 149-150."""
        session.set_variable("var1", "value1")

        assert session.variables["var1"] == "value1"
        assert session.last_activity is not None

    def test_get_variable(self, session):
        """Test get_variable method to cover line 163."""
        session.set_variable("var1", "value1")

        value = session.get_variable("var1")
        assert value == "value1"

        default = session.get_variable("nonexistent", "default")
        assert default == "default"

    def test_is_expired_no_expiry(self, session):
        """Test is_expired when no expiry set to cover line 172."""
        assert session.is_expired() is False

    def test_is_expired_not_expired(self, session):
        """Test is_expired when not expired to cover line 174."""
        session.expires_at = datetime.now() + timedelta(hours=1)

        assert session.is_expired() is False

    def test_is_expired_expired(self, session):
        """Test is_expired when expired."""
        session.expires_at = datetime.now() - timedelta(hours=1)

        assert session.is_expired() is True

    def test_pause(self, session):
        """Test pause method to cover lines 183-184."""
        session.pause()

        assert session.status == SessionStatus.PAUSED
        assert session.last_activity is not None

    def test_resume(self, session):
        """Test resume method to cover lines 193-195."""
        session.pause()
        session.resume()

        assert session.status == SessionStatus.ACTIVE
        assert session.last_activity is not None

    def test_resume_when_not_paused(self, session):
        """Test resume when session is not paused."""
        # Session is already active
        session.resume()

        assert session.status == SessionStatus.ACTIVE

    def test_complete(self, session):
        """Test complete method to cover lines 204-205."""
        session.complete()

        assert session.status == SessionStatus.COMPLETED
        assert session.last_activity is not None


class TestSessionManager:
    """Test SessionManager class."""

    @pytest.fixture
    def manager(self):
        """Create a SessionManager instance."""
        return SessionManager()

    def test_init(self, manager):
        """Test SessionManager initialization to cover line 213."""
        assert len(manager._sessions) == 0

    def test_create_session(self, manager):
        """Test create_session method to cover lines 229-232."""
        session = manager.create_session("agent1", max_history=50)

        assert session.agent_id == "agent1"
        assert session.max_history == 50
        assert session.session_id in manager._sessions

    def test_create_session_with_expiry(self, manager):
        """Test create_session with expires_at."""
        expires_at = datetime.now() + timedelta(hours=1)
        session = manager.create_session("agent1", expires_at=expires_at)

        assert session.expires_at == expires_at

    def test_get_session(self, manager):
        """Test get_session method to cover line 244."""
        session = manager.create_session("agent1")
        session_id = session.session_id

        retrieved = manager.get_session(session_id)

        assert retrieved == session

    def test_get_session_not_found(self, manager):
        """Test get_session with nonexistent session."""
        retrieved = manager.get_session("nonexistent")

        assert retrieved is None

    def test_get_session_expired(self, manager):
        """Test get_session with expired session to cover lines 246-248."""
        session = manager.create_session("agent1")
        session.expires_at = datetime.now() - timedelta(hours=1)
        session_id = session.session_id

        retrieved = manager.get_session(session_id)

        assert retrieved is None
        assert session.status == SessionStatus.EXPIRED

    def test_get_agent_sessions(self, manager):
        """Test get_agent_sessions method to cover lines 262-266."""
        session1 = manager.create_session("agent1")
        session2 = manager.create_session("agent1")
        manager.create_session("agent2")  # Different agent

        sessions = manager.get_agent_sessions("agent1")

        assert len(sessions) == 2
        assert session1 in sessions
        assert session2 in sessions

    def test_get_agent_sessions_excludes_expired(self, manager):
        """Test get_agent_sessions excludes expired sessions."""
        session1 = manager.create_session("agent1")
        session2 = manager.create_session("agent1")
        session2.expires_at = datetime.now() - timedelta(hours=1)

        sessions = manager.get_agent_sessions("agent1")

        assert len(sessions) == 1
        assert session1 in sessions
        assert session2 not in sessions

    def test_delete_session(self, manager):
        """Test delete_session method to cover line 278."""
        session = manager.create_session("agent1")
        session_id = session.session_id

        manager.delete_session(session_id)

        assert session_id not in manager._sessions

    def test_delete_session_nonexistent(self, manager):
        """Test delete_session with nonexistent session."""
        # Should not raise
        manager.delete_session("nonexistent")

    def test_cleanup_expired(self, manager):
        """Test cleanup_expired method to cover lines 287-294."""
        session1 = manager.create_session("agent1")
        session2 = manager.create_session("agent1")
        session2.expires_at = datetime.now() - timedelta(hours=1)
        session3 = manager.create_session("agent1")
        session3.expires_at = datetime.now() - timedelta(hours=1)

        count = manager.cleanup_expired()

        assert count == 2
        assert session1.session_id in manager._sessions
        assert session2.session_id not in manager._sessions
        assert session3.session_id not in manager._sessions

    def test_cleanup_expired_no_expired(self, manager):
        """Test cleanup_expired when no expired sessions."""
        manager.create_session("agent1")

        count = manager.cleanup_expired()

        assert count == 0

