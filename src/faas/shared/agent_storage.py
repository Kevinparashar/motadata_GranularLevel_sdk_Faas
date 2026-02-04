"""
Agent Storage for Stateless FaaS Services

Provides database-backed agent storage to replace in-memory state.
"""


import json
import logging
from typing import Any, Dict, Optional

from ...core.agno_agent_framework import Agent, create_agent
from ...core.litellm_gateway import LiteLLMGateway
from ...core.postgresql_database import DatabaseConnection

logger = logging.getLogger(__name__)


class AgentStorage:
    """
    Database-backed agent storage for stateless services.

    Stores agent definitions in database and recreates Agent instances on demand.
    """

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize agent storage.
        
        Args:
            db_connection: Database connection instance.
        """
        self.db = db_connection
        self._ensure_table()

    def _ensure_table(self):
        """Ensure agents table exists."""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS agents (
                        agent_id VARCHAR(255) PRIMARY KEY,
                        tenant_id VARCHAR(255) NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        description TEXT,
                        llm_model VARCHAR(255),
                        llm_provider VARCHAR(255),
                        system_prompt TEXT,
                        capabilities JSONB,
                        config JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )
                # Create index separately (MySQL syntax)
                try:
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tenant_id ON agents(tenant_id)")
                except Exception:
                    # Index might already exist or syntax differs
                    pass
        except Exception as e:
            logger.warning(f"Could not create agents table (may already exist): {e}")

    def save_agent(
        self,
        agent: Agent,
        tenant_id: str,
    ) -> None:
        """
        Save agent to database.
        
        Args:
            agent (Agent): Input parameter for this operation.
            tenant_id (str): Tenant identifier used for tenant isolation.
        
        Returns:
            None: Result of the operation.
        """
        with self.db.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO agents (
                    agent_id, tenant_id, name, description,
                    llm_model, llm_provider, system_prompt,
                    capabilities, config, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                (
                    agent.agent_id,
                    tenant_id,
                    agent.name,
                    agent.description,
                    agent.llm_model,
                    agent.llm_provider,
                    agent.system_prompt,
                    json.dumps(
                        [cap.name for cap in agent.capabilities] if agent.capabilities else []
                    ),
                    json.dumps(agent.metadata if agent.metadata else {}),
                ),
            )

    def load_agent(
        self,
        agent_id: str,
        tenant_id: str,
        gateway: LiteLLMGateway,
    ) -> Optional[Agent]:
        """
        Load agent from database and recreate Agent instance.
        
        Args:
            agent_id (str): Input parameter for this operation.
            tenant_id (str): Tenant identifier used for tenant isolation.
            gateway (LiteLLMGateway): Gateway client used for LLM calls.
        
        Returns:
            Optional[Agent]: Result if available, else None.
        """
        from psycopg2.extras import RealDictCursor

        with self.db.get_cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT 
                    agent_id, name, description,
                    llm_model, llm_provider, system_prompt,
                    capabilities, config
                FROM agents
                WHERE agent_id = %s AND tenant_id = %s
            """,
                (agent_id, tenant_id),
            )

            row = cursor.fetchone()
            if not row:
                return None

            # Recreate agent
            agent = create_agent(
                agent_id=row["agent_id"],
                name=row["name"],
                description=row["description"],
                gateway=gateway,
                llm_model=row["llm_model"],
                llm_provider=row["llm_provider"],
                system_prompt=row["system_prompt"],
                tenant_id=tenant_id,
            )

            # Restore capabilities
            if row["capabilities"]:
                capabilities = (
                    json.loads(row["capabilities"])
                    if isinstance(row["capabilities"], str)
                    else row["capabilities"]
                )
                for capability_name in capabilities:
                    agent.add_capability(capability_name, f"Capability: {capability_name}")

            # Restore metadata/config
            if row.get("config"):
                config_data = (
                    json.loads(row["config"])
                    if isinstance(row["config"], str)
                    else row["config"]
                )
                if isinstance(config_data, dict):
                    agent.metadata.update(config_data)

            return agent

    def list_agents(
        self,
        tenant_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Dict[str, Any]]:
        """
        List agents for a tenant.
        
        Args:
            tenant_id: Tenant identifier used for tenant isolation.
            limit: Maximum number of agents to return.
            offset: Number of agents to skip.
        
        Returns:
            List of agent dictionaries.
        """
        from psycopg2.extras import RealDictCursor

        with self.db.get_cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT 
                    agent_id, name, description,
                    llm_model, llm_provider,
                    created_at, updated_at
                FROM agents
                WHERE tenant_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """,
                (tenant_id, limit, offset),
            )

            return [dict(row) for row in cursor.fetchall()]

    def delete_agent(
        self,
        agent_id: str,
        tenant_id: str,
    ) -> bool:
        """
        Delete agent from database.
        
        Args:
            agent_id (str): Input parameter for this operation.
            tenant_id (str): Tenant identifier used for tenant isolation.
        
        Returns:
            bool: True if the operation succeeds, else False.
        """
        with self.db.get_cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM agents
                WHERE agent_id = %s AND tenant_id = %s
            """,
                (agent_id, tenant_id),
            )

            return cursor.rowcount > 0

    def agent_exists(
        self,
        agent_id: str,
        tenant_id: str,
    ) -> bool:
        """
        Check if agent exists.
        
        Args:
            agent_id (str): Input parameter for this operation.
            tenant_id (str): Tenant identifier used for tenant isolation.
        
        Returns:
            bool: True if the operation succeeds, else False.
        """
        with self.db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT 1 FROM agents
                WHERE agent_id = %s AND tenant_id = %s
                LIMIT 1
            """,
                (agent_id, tenant_id),
            )

            return cursor.fetchone() is not None
