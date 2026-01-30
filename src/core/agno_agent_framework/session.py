"""
Agent Session Management

Manages agent sessions, conversation history, and session state.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    """Session status enumeration."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    EXPIRED = "expired"


class SessionMessage(BaseModel):
    """Message in a session."""

    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentSession(BaseModel):
    """
    Agent session for managing conversation context and state.

    Sessions maintain conversation history, context, and state
    across multiple interactions with an agent.
    """

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    status: SessionStatus = SessionStatus.ACTIVE

    # Conversation history
    messages: List[SessionMessage] = Field(default_factory=list)
    max_history: int = 100

    # Session metadata
    created_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

    # Session context
    context: Dict[str, Any] = Field(default_factory=dict)
    variables: Dict[str, Any] = Field(default_factory=dict)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_message(
        self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> SessionMessage:
        """
        Add a message to the session.

        Args:
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional message metadata

        Returns:
            Created message
        """
        message = SessionMessage(role=role, content=content, metadata=metadata or {})

        self.messages.append(message)
        self.last_activity = datetime.now()

        # Trim history if exceeds max
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history :]

        return message

    def get_conversation_history(
        self, limit: Optional[int] = None, role_filter: Optional[str] = None
    ) -> List[SessionMessage]:
        """
        Get conversation history.

        Args:
            limit: Optional limit on number of messages
            role_filter: Optional role filter

        Returns:
            List of messages
        """
        messages = self.messages

        if role_filter:
            messages = [m for m in messages if m.role == role_filter]

        if limit:
            messages = messages[-limit:]

        return messages

    def set_context(self, key: str, value: Any) -> None:
        """
        Set context variable.

        Args:
            key: Context key
            value: Context value
        """
        self.context[key] = value
        self.last_activity = datetime.now()

    def get_context(self, key: str, default: Any = None) -> Any:
        """
        Get context variable.

        Args:
            key: Context key
            default: Default value if key not found

        Returns:
            Context value
        """
        return self.context.get(key, default)

    def set_variable(self, key: str, value: Any) -> None:
        """
        Set session variable.

        Args:
            key: Variable key
            value: Variable value
        """
        self.variables[key] = value
        self.last_activity = datetime.now()

    def get_variable(self, key: str, default: Any = None) -> Any:
        """
        Get session variable.

        Args:
            key: Variable key
            default: Default value if key not found

        Returns:
            Variable value
        """
        return self.variables.get(key, default)

    def is_expired(self) -> bool:
        """
        Check if session is expired.

        Returns:
            True if expired
        """
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def pause(self) -> None:
        """Pause the session."""
        self.status = SessionStatus.PAUSED
        self.last_activity = datetime.now()

    def resume(self) -> None:
        """Resume the session."""
        if self.status == SessionStatus.PAUSED:
            self.status = SessionStatus.ACTIVE
            self.last_activity = datetime.now()

    def complete(self) -> None:
        """Mark session as completed."""
        self.status = SessionStatus.COMPLETED
        self.last_activity = datetime.now()


class SessionManager:
    """Manager for agent sessions."""

    def __init__(self):
        """Initialize session manager."""
        self._sessions: Dict[str, AgentSession] = {}

    def create_session(
        self, agent_id: str, max_history: int = 100, expires_at: Optional[datetime] = None
    ) -> AgentSession:
        """
        Create a new session.

        Args:
            agent_id: Agent identifier
            max_history: Maximum conversation history length
            expires_at: Optional expiration time

        Returns:
            Created session
        """
        session = AgentSession(agent_id=agent_id, max_history=max_history, expires_at=expires_at)

        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[AgentSession]:
        """
        Get a session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session or None
        """
        session = self._sessions.get(session_id)

        if session and session.is_expired():
            session.status = SessionStatus.EXPIRED
            return None

        return session

    def get_agent_sessions(self, agent_id: str) -> List[AgentSession]:
        """
        Get all sessions for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            List of sessions
        """
        return [
            session
            for session in self._sessions.values()
            if session.agent_id == agent_id and not session.is_expired()
        ]

    def delete_session(self, session_id: str) -> None:
        """
        Delete a session.

        Args:
            session_id: Session identifier
        """
        self._sessions.pop(session_id, None)

    def cleanup_expired(self) -> int:
        """
        Clean up expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        expired = [
            session_id for session_id, session in self._sessions.items() if session.is_expired()
        ]

        for session_id in expired:
            self._sessions.pop(session_id, None)

        return len(expired)
