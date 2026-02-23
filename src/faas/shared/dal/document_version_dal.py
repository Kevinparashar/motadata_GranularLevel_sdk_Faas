"""
Document Version Data Access Layer (DAL)

Provides database abstraction for document version persistence.
Tables are assumed to exist (managed by migrations/DAL).
"""


import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

from src.core.postgresql_database import DatabaseConnection 

logger = logging.getLogger(__name__)


class DocumentVersionDAL:
    """
    Data Access Layer for document version persistence.

    Handles all database operations for document versions.
    Tables are assumed to exist (managed by migrations/DAL).
    """

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize Document Version DAL.

        Args:
            db_connection: Database connection instance.
        """
        self.db = db_connection

    async def create_version(
        self,
        document_id: str,
        content: str,
        tenant_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new document version.

        Args:
            document_id: Document identifier.
            content: Document content.
            tenant_id: Tenant identifier for tenant isolation.
            metadata: Optional version metadata.

        Returns:
            Dict[str, Any]: Version data including version number, content_hash, created_at.
        """
        # Calculate content hash
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Get current max version
        query = """
        SELECT MAX(version) as max_version
        FROM document_versions
        WHERE document_id = $1
        """
        params: List[Any] = [document_id]

        if tenant_id:
            query += " AND tenant_id = $2"
            params.append(tenant_id)

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_one=True,
        )

        next_version = (result.get("max_version") or 0) + 1

        # Insert new version
        insert_query = """
        INSERT INTO document_versions (document_id, version, content_hash, content, metadata, tenant_id)
        VALUES ($1, $2, $3, $4, $5::jsonb, $6)
        RETURNING id, created_at
        """
        metadata_json = json.dumps(metadata or {})
        insert_params: List[Any] = [document_id, next_version, content_hash, content, metadata_json]

        if tenant_id:
            insert_params.append(tenant_id)
        else:
            insert_query = insert_query.replace("$6", "NULL")

        result = await self.db.execute_query(
            insert_query,
            params=tuple(insert_params),
            fetch_one=True,
        )

        return {
            "version": next_version,
            "document_id": document_id,
            "content_hash": content_hash,
            "created_at": result["created_at"],
            "metadata": metadata or {},
        }

    async def get_versions(
        self, document_id: str, tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all versions of a document.

        Args:
            document_id: Document identifier.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            List[Dict[str, Any]]: List of version dictionaries.
        """
        query = """
        SELECT version, content_hash, created_at, metadata
        FROM document_versions
        WHERE document_id = $1
        """
        params: List[Any] = [document_id]

        if tenant_id:
            query += " AND tenant_id = $2"
            params.append(tenant_id)

        query += " ORDER BY version ASC"

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        # Parse JSON metadata for each version
        if results:
            for version_data in results:
                if version_data.get("metadata"):
                    version_data["metadata"] = (
                        json.loads(version_data["metadata"])
                        if isinstance(version_data["metadata"], str)
                        else version_data["metadata"]
                    )

        return results if results else []

    async def get_version(
        self,
        document_id: str,
        version: int,
        tenant_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific document version.

        Args:
            document_id: Document identifier.
            version: Version number.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            Optional[Dict[str, Any]]: Version data if found, else None.
        """
        query = """
        SELECT version, content_hash, content, created_at, metadata
        FROM document_versions
        WHERE document_id = $1 AND version = $2
        """
        params: List[Any] = [document_id, version]

        if tenant_id:
            query += " AND tenant_id = $3"
            params.append(tenant_id)

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_one=True,
        )

        if not result:
            return None

        # Parse JSON metadata
        version_data = dict(result)
        if version_data.get("metadata"):
            version_data["metadata"] = (
                json.loads(version_data["metadata"])
                if isinstance(version_data["metadata"], str)
                else version_data["metadata"]
            )

        return version_data

    async def delete_version(
        self,
        document_id: str,
        version: int,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """
        Delete a document version.

        Args:
            document_id: Document identifier.
            version: Version number.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            bool: True if deleted, False if not found.
        """
        query = """
        DELETE FROM document_versions
        WHERE document_id = $1 AND version = $2
        """
        params: List[Any] = [document_id, version]

        if tenant_id:
            query += " AND tenant_id = $3"
            params.append(tenant_id)

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=False,
        )

        return result > 0

    async def get_latest_version(
        self, document_id: str, tenant_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get the latest version of a document.

        Args:
            document_id: Document identifier.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            Optional[Dict[str, Any]]: Latest version data if found, else None.
        """
        query = """
        SELECT version, content_hash, content, created_at, metadata
        FROM document_versions
        WHERE document_id = $1
        """
        params: List[Any] = [document_id]

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

        # Parse JSON metadata
        version_data = dict(result)
        if version_data.get("metadata"):
            version_data["metadata"] = (
                json.loads(version_data["metadata"])
                if isinstance(version_data["metadata"], str)
                else version_data["metadata"]
            )

        return version_data

