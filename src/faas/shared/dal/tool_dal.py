"""
Data Access Layer for Tools.

Abstracts all database operations for tool definition persistence.
"""


import json
import logging
from typing import Any, Dict, List, Optional

from src.core.postgresql_database import DatabaseConnection 

logger = logging.getLogger(__name__)


class ToolDAL:
    """Data Access Layer for tool definition persistence."""

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize ToolDAL.

        Args:
            db_connection: Database connection instance.
        """
        self.db = db_connection

    async def save_tool(
        self,
        tool_id: str,
        name: str,
        description: str,
        tool_type: str,
        parameters: List[Dict[str, Any]],
        tenant_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> None:
        """
        Save tool definition to database.

        Args:
            tool_id: Tool identifier.
            name: Tool name.
            description: Tool description.
            tool_type: Tool type (function, api, database, file, custom).
            parameters: List of tool parameters.
            tenant_id: Tenant identifier for tenant isolation.
            metadata: Optional tool metadata.
            tags: Optional tool tags.
        """
        await self.db.execute_query(
            """
            INSERT INTO tools (
                tool_id, name, description, tool_type, parameters,
                metadata, tags, tenant_id, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7, $8, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (tool_id, tenant_id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                tool_type = EXCLUDED.tool_type,
                parameters = EXCLUDED.parameters,
                metadata = EXCLUDED.metadata,
                tags = EXCLUDED.tags,
                updated_at = CURRENT_TIMESTAMP
            """,
            params=(
                tool_id,
                name,
                description,
                tool_type,
                json.dumps(parameters),
                json.dumps(metadata or {}),
                json.dumps(tags or []),
                tenant_id,
            ),
            fetch_all=False,
        )

    async def load_tool(
        self, tool_id: str, tenant_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Load tool definition from database.

        Args:
            tool_id: Tool identifier.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            Tool data if found, else None.
        """
        query = """
        SELECT tool_id, name, description, tool_type, parameters, metadata, tags
        FROM tools
        WHERE tool_id = $1
        """
        params: List[Any] = [tool_id]
        if tenant_id:
            query += " AND tenant_id = $2"
            params.append(tenant_id)

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_one=True,
        )

        if not result:
            return None

        tool = dict(result)
        # Parse JSON fields
        if tool.get("parameters"):
            tool["parameters"] = (
                json.loads(tool["parameters"])
                if isinstance(tool["parameters"], str)
                else tool["parameters"]
            )
        if tool.get("metadata"):
            tool["metadata"] = (
                json.loads(tool["metadata"])
                if isinstance(tool["metadata"], str)
                else tool["metadata"]
            )
        if tool.get("tags"):
            tool["tags"] = (
                json.loads(tool["tags"])
                if isinstance(tool["tags"], str)
                else tool["tags"]
            )
        return tool

    async def list_tools(
        self,
        tenant_id: Optional[str] = None,
        tool_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List all tools.

        Args:
            tenant_id: Tenant identifier for tenant isolation.
            tool_type: Optional tool type filter.
            tags: Optional tags filter.
            limit: Maximum number of tools to return.
            offset: Offset for pagination.

        Returns:
            List of tool dictionaries.
        """
        query = """
        SELECT tool_id, name, description, tool_type, parameters, metadata, tags
        FROM tools
        WHERE 1=1
        """
        params: List[Any] = []
        if tenant_id:
            query += f" AND tenant_id = ${len(params) + 1}"
            params.append(tenant_id)
        if tool_type:
            query += f" AND tool_type = ${len(params) + 1}"
            params.append(tool_type)
        if tags:
            # Filter by tags (using JSONB contains)
            for tag in tags:
                query += f" AND tags::jsonb @> ${len(params) + 1}::jsonb"
                params.append(json.dumps([tag]))
        query += f" ORDER BY created_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
        params.extend([limit, offset])

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        if results:
            for tool in results:
                if tool.get("parameters"):
                    tool["parameters"] = (
                        json.loads(tool["parameters"])
                        if isinstance(tool["parameters"], str)
                        else tool["parameters"]
                    )
                if tool.get("metadata"):
                    tool["metadata"] = (
                        json.loads(tool["metadata"])
                        if isinstance(tool["metadata"], str)
                        else tool["metadata"]
                    )
                if tool.get("tags"):
                    tool["tags"] = (
                        json.loads(tool["tags"])
                        if isinstance(tool["tags"], str)
                        else tool["tags"]
                    )
        return results if results else []

    async def delete_tool(
        self, tool_id: str, tenant_id: Optional[str] = None
    ) -> bool:
        """
        Delete tool definition.

        Args:
            tool_id: Tool identifier.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            True if deleted, False if not found.
        """
        query = """
        DELETE FROM tools
        WHERE tool_id = $1
        """
        params: List[Any] = [tool_id]
        if tenant_id:
            query += " AND tenant_id = $2"
            params.append(tenant_id)

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=False,
        )
        return result > 0

    async def tool_exists(
        self, tool_id: str, tenant_id: Optional[str] = None
    ) -> bool:
        """
        Check if tool exists.

        Args:
            tool_id: Tool identifier.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            True if exists, False otherwise.
        """
        query = """
        SELECT 1 FROM tools
        WHERE tool_id = $1
        """
        params: List[Any] = [tool_id]
        if tenant_id:
            query += " AND tenant_id = $2"
            params.append(tenant_id)
        query += " LIMIT 1"

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_one=True,
        )
        return result is not None

