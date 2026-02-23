"""
Agent Storage for Stateless FaaS Services

Provides database-backed agent storage to replace in-memory state.
Uses AgentDAL for all database operations.
"""


import logging
from typing import Any, Dict, Optional

from ...core.agno_agent_framework import Agent, create_agent
from ...core.litellm_gateway import LiteLLMGateway
from .dal.agent_dal import AgentDAL

logger = logging.getLogger(__name__)


class AgentStorage:
    """
    Database-backed agent storage for stateless services.

    Stores agent definitions in database and recreates Agent instances on demand.
    Uses AgentDAL for all database operations.
    """

    def __init__(self, db_connection: Any):
        """
        Initialize agent storage.
        
        Args:
            db_connection: Database connection instance.
        """
        self.agent_dal = AgentDAL(db_connection)

    async def save_agent(
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
        await self.agent_dal.save_agent(
            agent_id=agent.agent_id,
            tenant_id=tenant_id,
            name=agent.name,
            description=agent.description,
            llm_model=agent.llm_model,
            llm_provider=agent.llm_provider,
            system_prompt=agent.system_prompt,
            capabilities=[cap.name for cap in agent.capabilities] if agent.capabilities else [],
            config=agent.metadata if agent.metadata else {},
        )

    async def load_agent(
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
        row = await self.agent_dal.load_agent(agent_id, tenant_id)

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
        if row.get("capabilities"):
            capabilities = row["capabilities"]
            for capability_name in capabilities:
                agent.add_capability(capability_name, f"Capability: {capability_name}")

        # Restore metadata/config
        if row.get("config"):
            config_data = row["config"]
            if isinstance(config_data, dict):
                agent.metadata.update(config_data)

        return agent

    async def list_agents(
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
        return await self.agent_dal.list_agents(tenant_id, limit, offset)

    async def delete_agent(
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
        return await self.agent_dal.delete_agent(agent_id, tenant_id)

    async def agent_exists(
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
        return await self.agent_dal.agent_exists(agent_id, tenant_id)
