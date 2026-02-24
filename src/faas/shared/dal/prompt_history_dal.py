"""
Data Access Layer for Prompt History.

Abstracts all database operations for prompt history persistence.
"""


import json
import logging
from typing import Any, Dict, List, Optional

from src.core.postgresql_database import DatabaseConnection  

logger = logging.getLogger(__name__)


class PromptHistoryDAL:
    """Data Access Layer for prompt history persistence."""

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize PromptHistoryDAL.

        Args:
            db_connection: Database connection instance.
        """
        self.db = db_connection

    async def save_history(
        self,
        prompt: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        context_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Save prompt to history.

        Args:
            prompt: Prompt text.
            tenant_id: Tenant identifier for tenant isolation.
            user_id: Optional user identifier.
            context_id: Optional context identifier (e.g., conversation_id, agent_id).
            metadata: Optional metadata.

        Returns:
            History record ID.
        """
        result = await self.db.execute_query(
            """
            INSERT INTO prompt_history (
                prompt, tenant_id, user_id, context_id, metadata, created_at
            ) VALUES ($1, $2, $3, $4, $5::jsonb, CURRENT_TIMESTAMP)
            RETURNING id;
            """,
            params=(
                prompt,
                tenant_id,
                user_id,
                context_id,
                json.dumps(metadata or {}),
            ),
            fetch_one=True,
        )
        return str(result["id"])

    async def get_history(
        self,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        context_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get prompt history.

        Args:
            tenant_id: Tenant identifier for tenant isolation.
            user_id: Optional user identifier.
            context_id: Optional context identifier.
            limit: Maximum number of records to return.
            offset: Offset for pagination.

        Returns:
            List of history records.
        """
        query = """
        SELECT id, prompt, tenant_id, user_id, context_id, metadata, created_at
        FROM prompt_history
        WHERE 1=1
        """
        params: List[Any] = []
        if tenant_id:
            query += f" AND tenant_id = ${len(params) + 1}"
            params.append(tenant_id)
        if user_id:
            query += f" AND user_id = ${len(params) + 1}"
            params.append(user_id)
        if context_id:
            query += f" AND context_id = ${len(params) + 1}"
            params.append(context_id)
        query += f" ORDER BY created_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
        params.extend([limit, offset])

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        if results:
            for record in results:
                if record.get("metadata"):
                    record["metadata"] = (
                        json.loads(record["metadata"])
                        if isinstance(record["metadata"], str)
                        else record["metadata"]
                    )
        return results if results else []

    async def delete_history(
        self,
        history_id: str,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """
        Delete prompt history record.

        Args:
            history_id: History record ID.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            True if deleted, False if not found.
        """
        query = """
        DELETE FROM prompt_history
        WHERE id = $1
        """
        params: List[Any] = [history_id]
        if tenant_id:
            query += " AND tenant_id = $2"
            params.append(tenant_id)

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=False,
        )
        return result > 0

    async def cleanup_old_history(
        self,
        days: int = 30,
        tenant_id: Optional[str] = None,
    ) -> int:
        """
        Clean up old prompt history records.

        Args:
            days: Number of days to keep (delete older records).
            tenant_id: Optional tenant identifier.

        Returns:
            Number of records deleted.
        """
        query = """
        DELETE FROM prompt_history
        WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
        """ % days
        params: List[Any] = []
        if tenant_id:
            query = query.replace("WHERE", "WHERE tenant_id = $1 AND")
            params.append(tenant_id)

        result = await self.db.execute_query(
            query,
            params=tuple(params) if params else None,
            fetch_all=False,
        )
        return result if result else 0

    async def save_context_window_state(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        context_id: Optional[str] = None,
        max_tokens: int = 4000,
        safety_margin: int = 200,
        current_tokens: int = 0,
        window_state: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Save context window state.

        Args:
            tenant_id: Tenant identifier.
            user_id: Optional user identifier.
            context_id: Optional context identifier.
            max_tokens: Maximum tokens for context window.
            safety_margin: Safety margin for token estimation.
            current_tokens: Current token count.
            window_state: Optional window state dictionary.
            metadata: Optional metadata.

        Returns:
            State record ID.
        """
        import uuid
        state_id = f"context_window_state_{uuid.uuid4().hex[:16]}"

        result = await self.db.execute_query(
            """
            INSERT INTO prompt_context_window_state (
                state_id, tenant_id, user_id, context_id, max_tokens, safety_margin,
                current_tokens, window_state, metadata, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9::jsonb, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            ON CONFLICT (tenant_id, COALESCE(user_id, ''), COALESCE(context_id, '')) DO UPDATE SET
                max_tokens = EXCLUDED.max_tokens,
                safety_margin = EXCLUDED.safety_margin,
                current_tokens = EXCLUDED.current_tokens,
                window_state = EXCLUDED.window_state,
                metadata = EXCLUDED.metadata,
                updated_at = CURRENT_TIMESTAMP
            RETURNING state_id;
            """,
            params=(
                state_id,
                tenant_id,
                user_id,
                context_id,
                max_tokens,
                safety_margin,
                current_tokens,
                json.dumps(window_state) if window_state else None,
                json.dumps(metadata or {}),
            ),
            fetch_one=True,
        )
        return str(result["state_id"]) if result else state_id

    async def get_context_window_state(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        context_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get context window state.

        Args:
            tenant_id: Tenant identifier.
            user_id: Optional user identifier.
            context_id: Optional context identifier.

        Returns:
            Context window state record or None.
        """
        result = await self.db.execute_query(
            """
            SELECT 
                state_id, tenant_id, user_id, context_id, max_tokens, safety_margin,
                current_tokens, window_state, metadata, created_at, updated_at
            FROM prompt_context_window_state
            WHERE tenant_id = $1
                AND COALESCE(user_id, '') = COALESCE($2, '')
                AND COALESCE(context_id, '') = COALESCE($3, '')
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            params=(tenant_id, user_id, context_id),
            fetch_one=True,
        )

        if result:
            if result.get("window_state"):
                result["window_state"] = (
                    json.loads(result["window_state"])
                    if isinstance(result["window_state"], str)
                    else result["window_state"]
                )
            if result.get("metadata"):
                result["metadata"] = (
                    json.loads(result["metadata"])
                    if isinstance(result["metadata"], str)
                    else result["metadata"]
                )
        return result

