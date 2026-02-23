"""
Data Access Layer for Prompt Templates.

Abstracts all database operations for prompt template persistence.
"""


import json
import logging
from typing import Any, Dict, List, Optional

from src.core.postgresql_database import DatabaseConnection 

logger = logging.getLogger(__name__)


class PromptTemplateDAL:
    """Data Access Layer for prompt template persistence."""

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize PromptTemplateDAL.

        Args:
            db_connection: Database connection instance.
        """
        self.db = db_connection

    async def save_template(
        self,
        name: str,
        version: str,
        content: str,
        tenant_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Save prompt template to database.

        Args:
            name: Template name.
            version: Template version.
            content: Template content.
            tenant_id: Tenant identifier for tenant isolation.
            metadata: Optional template metadata.
        """
        await self.db.execute_query(
            """
            INSERT INTO prompt_templates (
                name, version, content, metadata, tenant_id, created_at, updated_at
            ) VALUES ($1, $2, $3, $4::jsonb, $5, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (name, version, tenant_id) DO UPDATE SET
                content = EXCLUDED.content,
                metadata = EXCLUDED.metadata,
                updated_at = CURRENT_TIMESTAMP
            """,
            params=(name, version, content, json.dumps(metadata or {}), tenant_id),
            fetch_all=False,
        )

    async def load_template(
        self,
        name: str,
        tenant_id: Optional[str] = None,
        version: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Load prompt template from database.

        Args:
            name: Template name.
            tenant_id: Tenant identifier for tenant isolation.
            version: Optional version (latest if not provided).

        Returns:
            Template data if found, else None.
        """
        if version:
            query = """
            SELECT name, version, content, metadata, created_at, updated_at
            FROM prompt_templates
            WHERE name = $1 AND version = $2
            """
            params: List[Any] = [name, version]
            if tenant_id:
                query += " AND tenant_id = $3"
                params.append(tenant_id)
        else:
            query = """
            SELECT name, version, content, metadata, created_at, updated_at
            FROM prompt_templates
            WHERE name = $1
            """
            params = [name]
            if tenant_id:
                query += " AND tenant_id = $2"
                params.append(tenant_id)
            query += " ORDER BY version DESC LIMIT 1"

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_one=True,
        )

        if not result:
            return None

        template = dict(result)
        if template.get("metadata"):
            template["metadata"] = (
                json.loads(template["metadata"])
                if isinstance(template["metadata"], str)
                else template["metadata"]
            )
        return template

    async def list_templates(
        self,
        tenant_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List all prompt templates.

        Args:
            tenant_id: Tenant identifier for tenant isolation.
            limit: Maximum number of templates to return.
            offset: Offset for pagination.

        Returns:
            List of template dictionaries.
        """
        query = """
        SELECT DISTINCT ON (name) name, version, content, metadata, created_at, updated_at
        FROM prompt_templates
        """
        params: List[Any] = []
        if tenant_id:
            query += " WHERE tenant_id = $1"
            params.append(tenant_id)
        query += " ORDER BY name, version DESC LIMIT $" + str(len(params) + 1) + " OFFSET $" + str(
            len(params) + 2
        )
        params.extend([limit, offset])

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        if results:
            for template in results:
                if template.get("metadata"):
                    template["metadata"] = (
                        json.loads(template["metadata"])
                        if isinstance(template["metadata"], str)
                        else template["metadata"]
                    )
        return results if results else []

    async def list_versions(
        self,
        name: str,
        tenant_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List all versions of a template.

        Args:
            name: Template name.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            List of version dictionaries.
        """
        query = """
        SELECT name, version, content, metadata, created_at, updated_at
        FROM prompt_templates
        WHERE name = $1
        """
        params: List[Any] = [name]
        if tenant_id:
            query += " AND tenant_id = $2"
            params.append(tenant_id)
        query += " ORDER BY version DESC"

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        if results:
            for template in results:
                if template.get("metadata"):
                    template["metadata"] = (
                        json.loads(template["metadata"])
                        if isinstance(template["metadata"], str)
                        else template["metadata"]
                    )
        return results if results else []

    async def delete_template(
        self,
        name: str,
        tenant_id: Optional[str] = None,
        version: Optional[str] = None,
    ) -> bool:
        """
        Delete prompt template.

        Args:
            name: Template name.
            tenant_id: Tenant identifier for tenant isolation.
            version: Optional version (all versions if not provided).

        Returns:
            True if deleted, False if not found.
        """
        query = """
        DELETE FROM prompt_templates
        WHERE name = $1
        """
        params: List[Any] = [name]
        if version:
            query += f" AND version = ${len(params) + 1}"
            params.append(version)
        if tenant_id:
            query += f" AND tenant_id = ${len(params) + 1}"
            params.append(tenant_id)

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=False,
        )
        return result > 0

    async def template_exists(
        self,
        name: str,
        tenant_id: Optional[str] = None,
        version: Optional[str] = None,
    ) -> bool:
        """
        Check if template exists.

        Args:
            name: Template name.
            tenant_id: Tenant identifier for tenant isolation.
            version: Optional version.

        Returns:
            True if exists, False otherwise.
        """
        query = """
        SELECT 1 FROM prompt_templates
        WHERE name = $1
        """
        params: List[Any] = [name]
        if version:
            query += f" AND version = ${len(params) + 1}"
            params.append(version)
        if tenant_id:
            query += f" AND tenant_id = ${len(params) + 1}"
            params.append(tenant_id)
        query += " LIMIT 1"

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_one=True,
        )
        return result is not None

