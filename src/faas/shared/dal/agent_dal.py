"""
Agent Data Access Layer (DAL)

Provides database abstraction for agent persistence.
Tables are assumed to exist (managed by migrations/DAL).
"""


import json
import logging
from typing import Any, Dict, List, Optional

from src.core.postgresql_database import DatabaseConnection  
logger = logging.getLogger(__name__)


class AgentDAL:
    """
    Data Access Layer for agent persistence.

    Handles all database operations for agents.
    Tables are assumed to exist (managed by migrations/DAL).
    """

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize Agent DAL.

        Args:
            db_connection: Database connection instance.
        """
        self.db = db_connection

    async def save_agent(
        self,
        agent_id: str,
        tenant_id: str,
        name: str,
        description: Optional[str],
        llm_model: Optional[str],
        llm_provider: Optional[str],
        system_prompt: Optional[str],
        capabilities: List[str],
        config: Dict[str, Any],
    ) -> None:
        """
        Save agent to database.

        Args:
            agent_id: Agent identifier.
            tenant_id: Tenant identifier for tenant isolation.
            name: Agent name.
            description: Agent description.
            llm_model: LLM model name.
            llm_provider: LLM provider name.
            system_prompt: System prompt text.
            capabilities: List of capability names.
            config: Agent configuration/metadata.

        Returns:
            None: Result of the operation.
        """
        await self.db.execute_query(
            """
            INSERT INTO agents (
                agent_id, tenant_id, name, description,
                llm_model, llm_provider, system_prompt,
                capabilities, config, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, CURRENT_TIMESTAMP)
            ON CONFLICT (agent_id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                llm_model = EXCLUDED.llm_model,
                llm_provider = EXCLUDED.llm_provider,
                system_prompt = EXCLUDED.system_prompt,
                capabilities = EXCLUDED.capabilities,
                config = EXCLUDED.config,
                updated_at = CURRENT_TIMESTAMP
            """,
            params=(
                agent_id,
                tenant_id,
                name,
                description,
                llm_model,
                llm_provider,
                system_prompt,
                json.dumps(capabilities),
                json.dumps(config),
            ),
            fetch_all=False,
        )

    async def load_agent(
        self, agent_id: str, tenant_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Load agent from database.

        Args:
            agent_id: Agent identifier.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            Optional[Dict[str, Any]]: Agent data if found, else None.
        """
        row = await self.db.execute_query(
            """
            SELECT 
                agent_id, name, description,
                llm_model, llm_provider, system_prompt,
                capabilities, config
            FROM agents
            WHERE agent_id = $1 AND tenant_id = $2
            """,
            params=(agent_id, tenant_id),
            fetch_one=True,
        )

        if not row:
            return None

        # Parse JSON fields
        result = dict(row)
        if result.get("capabilities"):
            result["capabilities"] = (
                json.loads(result["capabilities"])
                if isinstance(result["capabilities"], str)
                else result["capabilities"]
            )
        if result.get("config"):
            result["config"] = (
                json.loads(result["config"])
                if isinstance(result["config"], str)
                else result["config"]
            )

        return result

    async def list_agents(
        self, tenant_id: str, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List agents for a tenant.

        Args:
            tenant_id: Tenant identifier for tenant isolation.
            limit: Maximum number of agents to return.
            offset: Number of agents to skip.

        Returns:
            List[Dict[str, Any]]: List of agent dictionaries.
        """
        results = await self.db.execute_query(
            """
            SELECT 
                agent_id, name, description,
                llm_model, llm_provider,
                created_at, updated_at
            FROM agents
            WHERE tenant_id = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
            """,
            params=(tenant_id, limit, offset),
            fetch_all=True,
        )

        return results if results else []

    async def delete_agent(self, agent_id: str, tenant_id: str) -> bool:
        """
        Delete agent from database.

        Args:
            agent_id: Agent identifier.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            bool: True if deleted, False if not found.
        """
        result = await self.db.execute_query(
            """
            DELETE FROM agents
            WHERE agent_id = $1 AND tenant_id = $2
            """,
            params=(agent_id, tenant_id),
            fetch_all=False,
        )

        return result > 0

    async def agent_exists(self, agent_id: str, tenant_id: str) -> bool:
        """
        Check if agent exists.

        Args:
            agent_id: Agent identifier.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            bool: True if exists, False otherwise.
        """
        result = await self.db.execute_query(
            """
            SELECT 1 FROM agents
            WHERE agent_id = $1 AND tenant_id = $2
            LIMIT 1
            """,
            params=(agent_id, tenant_id),
            fetch_one=True,
        )

        return result is not None

