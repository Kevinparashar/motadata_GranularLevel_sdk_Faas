"""
Agent Session Management

Manages agent sessions, conversation history, and session state.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from ...faas.shared.dal.session_dal import SessionDAL


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
            role (str): Input parameter for this operation.
            content (str): Content text.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
        
        Returns:
            SessionMessage: Result of the operation.
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
            limit (Optional[int]): Input parameter for this operation.
            role_filter (Optional[str]): Input parameter for this operation.
        
        Returns:
            List[SessionMessage]: List result of the operation.
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
            key (str): Input parameter for this operation.
            value (Any): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        """
        self.context[key] = value
        self.last_activity = datetime.now()

    def get_context(self, key: str, default: Any = None) -> Any:
        """
        Get context variable.
        
        Args:
            key (str): Input parameter for this operation.
            default (Any): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        """
        return self.context.get(key, default)

    def set_variable(self, key: str, value: Any) -> None:
        """
        Set session variable.
        
        Args:
            key (str): Input parameter for this operation.
            value (Any): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        """
        self.variables[key] = value
        self.last_activity = datetime.now()

    def get_variable(self, key: str, default: Any = None) -> Any:
        """
        Get session variable.
        
        Args:
            key (str): Input parameter for this operation.
            default (Any): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        """
        return self.variables.get(key, default)

    def is_expired(self) -> bool:
        """
        Check if session is expired.
        
        Returns:
            bool: True if the operation succeeds, else False.
        """
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def pause(self) -> None:
        """
        Pause the session.
        
        Returns:
            None: Result of the operation.
        """
        self.status = SessionStatus.PAUSED
        self.last_activity = datetime.now()

    def resume(self) -> None:
        """
        Resume the session.
        
        Returns:
            None: Result of the operation.
        """
        if self.status == SessionStatus.PAUSED:
            self.status = SessionStatus.ACTIVE
            self.last_activity = datetime.now()

    def complete(self) -> None:
        """
        Mark session as completed.
        
        Returns:
            None: Result of the operation.
        """
        self.status = SessionStatus.COMPLETED
        self.last_activity = datetime.now()


class SessionManager:
    """
    Manager for agent sessions.
    
    Supports both in-memory storage (default) and database persistence via SessionDAL.
    """

    def __init__(
        self,
        session_dal: Optional[SessionDAL] = None,
        tenant_id: Optional[str] = None,
    ):
        """
        Initialize session manager.
        
        Args:
            session_dal: Optional SessionDAL instance for database persistence.
            tenant_id: Optional tenant ID for multi-tenant isolation (required if using DAL).
        """
        self._sessions: Dict[str, AgentSession] = {}
        self._session_dal = session_dal
        self._tenant_id = tenant_id

    def create_session(
        self, agent_id: str, max_history: int = 100, expires_at: Optional[datetime] = None
    ) -> AgentSession:
        """
        Create a new session.
        
        Args:
            agent_id (str): Input parameter for this operation.
            max_history (int): Input parameter for this operation.
            expires_at (Optional[datetime]): Input parameter for this operation.
        
        Returns:
            AgentSession: Result of the operation.
        """
        session = AgentSession(agent_id=agent_id, max_history=max_history, expires_at=expires_at)

        # Store in-memory (for backward compatibility and caching)
        self._sessions[session.session_id] = session
        
        # Persist to database if DAL is available (will be saved on next async operation)
        # Note: create_session is sync, so we can't await here. Persistence happens in save_session().
        
        return session

    async def get_session(self, session_id: str) -> Optional[AgentSession]:
        """
        Get a session by ID.
        
        Args:
            session_id (str): Input parameter for this operation.
        
        Returns:
            Optional[AgentSession]: Result if available, else None.
        """
        # Try in-memory first
        session = self._sessions.get(session_id)

        # If not in memory and DAL is available, load from database
        if not session and self._session_dal and self._tenant_id:
            session = await self._session_dal.load_session(session_id, self._tenant_id)
            if session:
                # Cache in memory
                self._sessions[session_id] = session

        if session and session.is_expired():
            session.status = SessionStatus.EXPIRED
            return None

        return session
    
    def get_session_sync(self, session_id: str) -> Optional[AgentSession]:
        """
        Get a session by ID (synchronous version for backward compatibility).
        
        Args:
            session_id (str): Input parameter for this operation.
        
        Returns:
            Optional[AgentSession]: Result if available, else None.
        """
        session = self._sessions.get(session_id)

        if session and session.is_expired():
            session.status = SessionStatus.EXPIRED
            return None

        return session

    async def get_agent_sessions(self, agent_id: str) -> List[AgentSession]:
        """
        Get all sessions for an agent.
        
        Args:
            agent_id (str): Input parameter for this operation.
        
        Returns:
            List[AgentSession]: List result of the operation.
        """
        # If DAL is available, load from database
        if self._session_dal and self._tenant_id:
            sessions = await self._session_dal.list_agent_sessions(agent_id, self._tenant_id)
            # Cache in memory
            for session in sessions:
                self._sessions[session.session_id] = session
            return sessions
        
        # Fallback to in-memory
        return [
            session
            for session in self._sessions.values()
            if session.agent_id == agent_id and not session.is_expired()
        ]
    
    def get_agent_sessions_sync(self, agent_id: str) -> List[AgentSession]:
        """
        Get all sessions for an agent (synchronous version for backward compatibility).
        
        Args:
            agent_id (str): Input parameter for this operation.
        
        Returns:
            List[AgentSession]: List result of the operation.
        """
        return [
            session
            for session in self._sessions.values()
            if session.agent_id == agent_id and not session.is_expired()
        ]

    async def delete_session(self, session_id: str) -> None:
        """
        Delete a session.
        
        Args:
            session_id (str): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        """
        # Delete from memory
        self._sessions.pop(session_id, None)
        
        # Delete from database if DAL is available
        if self._session_dal and self._tenant_id:
            await self._session_dal.delete_session(session_id, self._tenant_id)
    
    def delete_session_sync(self, session_id: str) -> None:
        """
        Delete a session (synchronous version for backward compatibility).
        
        Args:
            session_id (str): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        """
        self._sessions.pop(session_id, None)

    async def cleanup_expired(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            int: Result of the operation.
        """
        # Clean up in-memory
        expired = [
            session_id for session_id, session in self._sessions.items() if session.is_expired()
        ]

        for session_id in expired:
            self._sessions.pop(session_id, None)
        
        # Clean up from database if DAL is available
        if self._session_dal:
            db_count = await self._session_dal.cleanup_expired_sessions()
            return len(expired) + db_count

        return len(expired)
    
    def cleanup_expired_sync(self) -> int:
        """
        Clean up expired sessions (synchronous version for backward compatibility).
        
        Returns:
            int: Result of the operation.
        """
        expired = [
            session_id for session_id, session in self._sessions.items() if session.is_expired()
        ]

        for session_id in expired:
            self._sessions.pop(session_id, None)

        return len(expired)
    
    async def save_session(self, session: AgentSession) -> None:
        """
        Save session to database (if DAL is available).
        
        Args:
            session: Session to save.
        
        Returns:
            None: Result of the operation.
        """
        # Update in-memory cache
        self._sessions[session.session_id] = session
        
        # Persist to database if DAL is available
        if self._session_dal and self._tenant_id:
            await self._session_dal.save_session(session, self._tenant_id)
