"""
Session Data Access Layer (DAL)

Provides database abstraction for agent session persistence.
Tables are assumed to exist (managed by migrations/DAL).
"""


import json
import logging
from datetime import datetime
from typing import List, Optional

from src.core.agno_agent_framework.session import AgentSession, SessionMessage, SessionStatus  
from src.core.postgresql_database import DatabaseConnection  

logger = logging.getLogger(__name__)


class SessionDAL:
    """
    Data Access Layer for agent session persistence.

    Handles all database operations for sessions and messages.
    Tables are assumed to exist (managed by migrations/DAL).
    """

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize Session DAL.

        Args:
            db_connection: Database connection instance.
        """
        self.db = db_connection

    async def save_session(self, session: AgentSession, tenant_id: str) -> None:
        """
        Save session to database.

        Args:
            session: AgentSession instance to save.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            None: Result of the operation.
        """
        # Save session
        await self.db.execute_query(
            """
            INSERT INTO agent_sessions (
                session_id, agent_id, tenant_id, status, max_history,
                created_at, last_activity, expires_at, context, variables, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (session_id) DO UPDATE SET
                status = EXCLUDED.status,
                max_history = EXCLUDED.max_history,
                last_activity = EXCLUDED.last_activity,
                expires_at = EXCLUDED.expires_at,
                context = EXCLUDED.context,
                variables = EXCLUDED.variables,
                metadata = EXCLUDED.metadata,
                updated_at = CURRENT_TIMESTAMP
            """,
            params=(
                session.session_id,
                session.agent_id,
                tenant_id,
                session.status.value,
                session.max_history,
                session.created_at,
                session.last_activity,
                session.expires_at,
                json.dumps(session.context),
                json.dumps(session.variables),
                json.dumps(session.metadata),
            ),
            fetch_all=False,
        )

        # Save messages (delete existing and insert new)
        await self.db.execute_query(
            """
            DELETE FROM session_messages
            WHERE session_id = $1
            """,
            params=(session.session_id,),
            fetch_all=False,
        )

        for message in session.messages:
            await self._save_message(message, session.session_id)

    async def _save_message(self, message: SessionMessage, session_id: str) -> None:
        """
        Save a single message to database.

        Args:
            message: SessionMessage instance to save.
            session_id: Session identifier.

        Returns:
            None: Result of the operation.
        """
        await self.db.execute_query(
            """
            INSERT INTO session_messages (
                message_id, session_id, role, content, timestamp, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (message_id) DO UPDATE SET
                role = EXCLUDED.role,
                content = EXCLUDED.content,
                timestamp = EXCLUDED.timestamp,
                metadata = EXCLUDED.metadata
            """,
            params=(
                message.message_id,
                session_id,
                message.role,
                message.content,
                message.timestamp,
                json.dumps(message.metadata),
            ),
            fetch_all=False,
        )

    async def load_session(
        self, session_id: str, tenant_id: str
    ) -> Optional[AgentSession]:
        """
        Load session from database.

        Args:
            session_id: Session identifier.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            Optional[AgentSession]: Session if found, else None.
        """
        # Load session
        session_row = await self.db.execute_query(
            """
            SELECT * FROM agent_sessions
            WHERE session_id = $1 AND tenant_id = $2
            """,
            params=(session_id, tenant_id),
            fetch_one=True,
        )

        if not session_row:
            return None

        # Load messages
        messages_rows = await self.db.execute_query(
            """
            SELECT * FROM session_messages
            WHERE session_id = $1
            ORDER BY timestamp ASC
            """,
            params=(session_id,),
            fetch_all=True,
        )

        messages = []
        if messages_rows:
            for row in messages_rows:
                messages.append(
                    SessionMessage(
                        message_id=row["message_id"],
                        role=row["role"],
                        content=row["content"],
                        timestamp=row["timestamp"],
                        metadata=(
                            json.loads(row["metadata"])
                            if isinstance(row["metadata"], str)
                            else row["metadata"]
                        ),
                    )
                )

        # Reconstruct session
        return AgentSession(
            session_id=session_row["session_id"],
            agent_id=session_row["agent_id"],
            status=SessionStatus(session_row["status"]),
            max_history=session_row["max_history"],
            created_at=session_row["created_at"],
            last_activity=session_row["last_activity"],
            expires_at=session_row["expires_at"],
            context=(
                json.loads(session_row["context"])
                if isinstance(session_row["context"], str)
                else session_row["context"]
            ),
            variables=(
                json.loads(session_row["variables"])
                if isinstance(session_row["variables"], str)
                else session_row["variables"]
            ),
            metadata=(
                json.loads(session_row["metadata"])
                if isinstance(session_row["metadata"], str)
                else session_row["metadata"]
            ),
            messages=messages,
        )

    async def list_agent_sessions(
        self, agent_id: str, tenant_id: str
    ) -> List[AgentSession]:
        """
        List all sessions for an agent.

        Args:
            agent_id: Agent identifier.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            List[AgentSession]: List of sessions.
        """
        session_rows = await self.db.execute_query(
            """
            SELECT * FROM agent_sessions
            WHERE agent_id = $1 AND tenant_id = $2
            ORDER BY last_activity DESC
            """,
            params=(agent_id, tenant_id),
            fetch_all=True,
        )

        sessions: List[AgentSession] = []
        if session_rows:
            for row in session_rows:
                # Load messages for each session
                messages_rows = await self.db.execute_query(
                    """
                    SELECT * FROM session_messages
                    WHERE session_id = $1
                    ORDER BY timestamp ASC
                    """,
                    params=(row["session_id"],),
                    fetch_all=True,
                )

                messages = []
                if messages_rows:
                    for msg_row in messages_rows:
                        messages.append(
                            SessionMessage(
                                message_id=msg_row["message_id"],
                                role=msg_row["role"],
                                content=msg_row["content"],
                                timestamp=msg_row["timestamp"],
                                metadata=(
                                    json.loads(msg_row["metadata"])
                                    if isinstance(msg_row["metadata"], str)
                                    else msg_row["metadata"]
                                ),
                            )
                        )

                sessions.append(
                    AgentSession(
                        session_id=row["session_id"],
                        agent_id=row["agent_id"],
                        status=SessionStatus(row["status"]),
                        max_history=row["max_history"],
                        created_at=row["created_at"],
                        last_activity=row["last_activity"],
                        expires_at=row["expires_at"],
                        context=(
                            json.loads(row["context"])
                            if isinstance(row["context"], str)
                            else row["context"]
                        ),
                        variables=(
                            json.loads(row["variables"])
                            if isinstance(row["variables"], str)
                            else row["variables"]
                        ),
                        metadata=(
                            json.loads(row["metadata"])
                            if isinstance(row["metadata"], str)
                            else row["metadata"]
                        ),
                        messages=messages,
                    )
                )

        return sessions

    async def delete_session(self, session_id: str, tenant_id: str) -> bool:
        """
        Delete session from database.

        Args:
            session_id: Session identifier.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            bool: True if deleted, False if not found.
        """
        # Messages are deleted via CASCADE, but we can be explicit
        result = await self.db.execute_query(
            """
            DELETE FROM agent_sessions
            WHERE session_id = $1 AND tenant_id = $2
            """,
            params=(session_id, tenant_id),
            fetch_all=False,
        )

        return result > 0

    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions from database.

        Returns:
            int: Number of sessions deleted.
        """
        result = await self.db.execute_query(
            """
            DELETE FROM agent_sessions
            WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP
            """,
            fetch_all=False,
        )

        return result

    async def update_session_activity(
        self, session_id: str, tenant_id: str, last_activity: Optional[datetime] = None
    ) -> bool:
        """
        Update session last_activity timestamp.

        Args:
            session_id: Session identifier.
            tenant_id: Tenant identifier for tenant isolation.
            last_activity: Optional timestamp (defaults to now).

        Returns:
            bool: True if updated, False if not found.
        """
        if last_activity is None:
            last_activity = datetime.now()

        result = await self.db.execute_query(
            """
            UPDATE agent_sessions
            SET last_activity = $1, updated_at = CURRENT_TIMESTAMP
            WHERE session_id = $2 AND tenant_id = $3
            """,
            params=(last_activity, session_id, tenant_id),
            fetch_all=False,
        )

        return result > 0

    async def session_exists(self, session_id: str, tenant_id: str) -> bool:
        """
        Check if session exists.

        Args:
            session_id: Session identifier.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            bool: True if exists, False otherwise.
        """
        result = await self.db.execute_query(
            """
            SELECT 1 FROM agent_sessions
            WHERE session_id = $1 AND tenant_id = $2
            LIMIT 1
            """,
            params=(session_id, tenant_id),
            fetch_one=True,
        )

        return result is not None

