"""
Document Data Access Layer (DAL)

Provides database abstraction for document persistence.
Tables are assumed to exist (managed by migrations/DAL).
"""


import json
import logging
from typing import Any, Dict, List, Optional

from src.core.postgresql_database import DatabaseConnection 

logger = logging.getLogger(__name__)


class DocumentDAL:
    """
    Data Access Layer for document persistence.

    Handles all database operations for documents.
    Tables are assumed to exist (managed by migrations/DAL).
    """

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize Document DAL.

        Args:
            db_connection: Database connection instance.
        """
        self.db = db_connection

    async def save_document(
        self,
        title: str,
        content: str,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
    ) -> str:
        """
        Save document to database.

        Args:
            title: Document title.
            content: Document content.
            source: Document source.
            metadata: Document metadata.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            str: Document ID.
        """
        query = """
        INSERT INTO documents (title, content, metadata, source, tenant_id)
        VALUES ($1, $2, $3::jsonb, $4, $5)
        RETURNING id;
        """

        metadata_json = json.dumps(metadata or {})

        result = await self.db.execute_query(
            query,
            params=(title, content, metadata_json, source, tenant_id),
            fetch_one=True,
        )

        return str(result["id"])

    async def load_document(
        self, document_id: str, tenant_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Load document from database.

        Args:
            document_id: Document identifier.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            Optional[Dict[str, Any]]: Document data if found, else None.
        """
        query = """
        SELECT id, title, content, source, metadata, created_at, updated_at
        FROM documents
        WHERE id = $1
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

        if not result:
            return None

        # Parse JSON metadata
        doc = dict(result)
        if doc.get("metadata"):
            doc["metadata"] = (
                json.loads(doc["metadata"])
                if isinstance(doc["metadata"], str)
                else doc["metadata"]
            )

        return doc

    async def list_documents(
        self,
        tenant_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List documents.

        Args:
            tenant_id: Tenant identifier for tenant isolation.
            limit: Maximum number of documents to return.
            offset: Number of documents to skip.

        Returns:
            List[Dict[str, Any]]: List of document dictionaries.
        """
        query = """
        SELECT id, title, source, created_at, updated_at
        FROM documents
        """
        params: List[Any] = []

        if tenant_id:
            query += " WHERE tenant_id = $1"
            params.append(tenant_id)

        query += " ORDER BY created_at DESC LIMIT $" + str(len(params) + 1) + " OFFSET $" + str(
            len(params) + 2
        )
        params.extend([limit, offset])

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        return results if results else []

    async def update_document(
        self,
        document_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """
        Update document in database.

        Args:
            document_id: Document identifier.
            title: Optional new title.
            content: Optional new content.
            metadata: Optional new metadata.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            bool: True if updated, False if not found.
        """
        update_fields = []
        params: List[Any] = []

        if title is not None:
            update_fields.append(f"title = ${len(params) + 1}")
            params.append(title)

        if content is not None:
            update_fields.append(f"content = ${len(params) + 1}")
            params.append(content)

        if metadata is not None:
            update_fields.append(f"metadata = ${len(params) + 1}::jsonb")
            params.append(json.dumps(metadata))

        if not update_fields:
            return False

        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(document_id)

        query = f"""
        UPDATE documents
        SET {', '.join(update_fields)}
        WHERE id = ${len(params)}
        """

        if tenant_id:
            query = query.replace(f"${len(params)}", f"${len(params)} AND tenant_id = ${len(params) + 1}")
            params.append(tenant_id)

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=False,
        )

        return result > 0

    async def delete_document(
        self, document_id: str, tenant_id: Optional[str] = None
    ) -> bool:
        """
        Delete document from database.

        Args:
            document_id: Document identifier.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            bool: True if deleted, False if not found.
        """
        query = """
        DELETE FROM documents
        WHERE id = $1
        """
        params: List[Any] = [document_id]

        if tenant_id:
            query = query.replace("$1", "$1 AND tenant_id = $2")
            params.append(tenant_id)

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=False,
        )

        return result > 0

    async def document_exists(
        self, document_id: str, tenant_id: Optional[str] = None
    ) -> bool:
        """
        Check if document exists.

        Args:
            document_id: Document identifier.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            bool: True if exists, False otherwise.
        """
        query = """
        SELECT 1 FROM documents
        WHERE id = $1
        """
        params: List[Any] = [document_id]

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

