"""
Embedding Data Access Layer (DAL)

Provides database abstraction for vector embedding persistence.
Tables are assumed to exist (managed by migrations/DAL).
"""


import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from src.core.postgresql_database import DatabaseConnection 

logger = logging.getLogger(__name__)


class EmbeddingDAL:
    """
    Data Access Layer for vector embedding persistence.

    Handles all database operations for embeddings.
    Tables are assumed to exist (managed by migrations/DAL).
    """

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize Embedding DAL.

        Args:
            db_connection: Database connection instance.
        """
        self.db = db_connection

    async def insert_embedding(
        self,
        document_id: int,
        embedding: List[float],
        model: str = "text-embedding-3-small",
        tenant_id: Optional[str] = None,
    ) -> int:
        """
        Insert an embedding vector.

        Args:
            document_id: Document ID to associate with embedding.
            embedding: Embedding vector.
            model: Model name or identifier.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            int: Inserted embedding ID.
        """
        # Convert list to string format for pgvector
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"

        query = """
        INSERT INTO embeddings (document_id, embedding, model)
        VALUES ($1, $2::vector, $3)
        RETURNING id;
        """

        result = await self.db.execute_query(
            query,
            params=(document_id, embedding_str, model),
            fetch_one=True,
        )

        return result["id"] if result else 0

    async def batch_insert_embeddings(
        self,
        embeddings_data: List[Tuple[int, List[float], str]],
        tenant_id: Optional[str] = None,
    ) -> None:
        """
        Batch insert multiple embeddings.

        Args:
            embeddings_data: List of (document_id, embedding, model) tuples.
            tenant_id: Tenant identifier for tenant isolation.
        """
        if not embeddings_data:
            return

        # Prepare batch insert queries
        queries = []
        for doc_id, embedding, model in embeddings_data:
            embedding_str = "[" + ",".join(map(str, embedding)) + "]"
            query = """
            INSERT INTO embeddings (document_id, embedding, model)
            VALUES ($1, $2::vector, $3)
            """
            queries.append((query, (doc_id, embedding_str, model)))

        # Execute all in a transaction
        await self.db.execute_transaction(queries)

    async def similarity_search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.0,
        model: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search using cosine distance.

        Args:
            query_embedding: Query embedding vector.
            limit: Maximum number of results.
            threshold: Similarity threshold (0.0 to 1.0).
            model: Model name or identifier to use.
            tenant_id: Tenant identifier for multi-tenancy.

        Returns:
            List[Dict[str, Any]]: List of similar documents with similarity scores.
        """
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

        if model and tenant_id:
            query = """
            SELECT 
                e.id,
                e.document_id,
                d.title,
                d.content,
                d.metadata,
                d.source,
                1 - (e.embedding <=> $1::vector) as similarity
            FROM embeddings e
            JOIN documents d ON e.document_id = d.id
            WHERE e.model = $2
                AND d.tenant_id = $3
                AND 1 - (e.embedding <=> $1::vector) >= $4
            ORDER BY e.embedding <=> $1::vector
            LIMIT $5;
            """
            params = (embedding_str, model, tenant_id, threshold, limit)
        elif model:
            query = """
            SELECT 
                e.id,
                e.document_id,
                d.title,
                d.content,
                d.metadata,
                d.source,
                1 - (e.embedding <=> $1::vector) as similarity
            FROM embeddings e
            JOIN documents d ON e.document_id = d.id
            WHERE e.model = $2
                AND 1 - (e.embedding <=> $1::vector) >= $3
            ORDER BY e.embedding <=> $1::vector
            LIMIT $4;
            """
            params = (embedding_str, model, threshold, limit)
        elif tenant_id:
            query = """
            SELECT 
                e.id,
                e.document_id,
                d.title,
                d.content,
                d.metadata,
                d.source,
                1 - (e.embedding <=> $1::vector) as similarity
            FROM embeddings e
            JOIN documents d ON e.document_id = d.id
            WHERE d.tenant_id = $2
                AND 1 - (e.embedding <=> $1::vector) >= $3
            ORDER BY e.embedding <=> $1::vector
            LIMIT $4;
            """
            params = (embedding_str, tenant_id, threshold, limit)
        else:
            query = """
            SELECT 
                e.id,
                e.document_id,
                d.title,
                d.content,
                d.metadata,
                d.source,
                1 - (e.embedding <=> $1::vector) as similarity
            FROM embeddings e
            JOIN documents d ON e.document_id = d.id
            WHERE 1 - (e.embedding <=> $1::vector) >= $2
            ORDER BY e.embedding <=> $1::vector
            LIMIT $3;
            """
            params = (embedding_str, threshold, limit)

        results = await self.db.execute_query(query, params, fetch_all=True)
        
        # Parse JSON metadata for each result
        if results:
            for result in results:
                if isinstance(result, dict) and result.get("metadata"):
                    result["metadata"] = (
                        json.loads(result["metadata"])
                        if isinstance(result["metadata"], str)
                        else result["metadata"]
                    )
        
        return results if results else []

    async def get_embedding(
        self, embedding_id: int, tenant_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get an embedding by ID.

        Args:
            embedding_id: Embedding ID.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            Optional[Dict[str, Any]]: Embedding data if found, else None.
        """
        query = """
        SELECT e.id, e.document_id, e.embedding::text, e.model, d.tenant_id
        FROM embeddings e
        JOIN documents d ON e.document_id = d.id
        WHERE e.id = $1
        """
        params: List[Any] = [embedding_id]

        if tenant_id:
            query += " AND d.tenant_id = $2"
            params.append(tenant_id)

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_one=True,
        )

        return result if result else None

    async def delete_embeddings(
        self, document_id: int, tenant_id: Optional[str] = None
    ) -> int:
        """
        Delete all embeddings for a document.

        Args:
            document_id: Document ID.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            int: Number of embeddings deleted.
        """
        if tenant_id:
            query = """
            DELETE FROM embeddings
            WHERE document_id = $1
                AND document_id IN (
                    SELECT id FROM documents WHERE tenant_id = $2
                );
            """
            params = (document_id, tenant_id)
        else:
            query = """
            DELETE FROM embeddings
            WHERE document_id = $1;
            """
            params = (document_id,)

        result = await self.db.execute_query(
            query,
            params=params,
            fetch_all=False,
        )

        return result if result else 0

    async def update_embedding(
        self,
        embedding_id: int,
        new_embedding: List[float],
        tenant_id: Optional[str] = None,
    ) -> bool:
        """
        Update an existing embedding.

        Args:
            embedding_id: Embedding ID to update.
            new_embedding: New embedding vector.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            bool: True if update successful, False otherwise.
        """
        embedding_str = "[" + ",".join(map(str, new_embedding)) + "]"

        if tenant_id:
            query = """
            UPDATE embeddings
            SET embedding = $1::vector
            WHERE id = $2
                AND document_id IN (
                    SELECT id FROM documents WHERE tenant_id = $3
                );
            """
            params = (embedding_str, embedding_id, tenant_id)
        else:
            query = """
            UPDATE embeddings
            SET embedding = $1::vector
            WHERE id = $2;
            """
            params = (embedding_str, embedding_id)

        result = await self.db.execute_query(
            query,
            params=params,
            fetch_all=False,
        )

        return result > 0

    async def get_embeddings_by_document(
        self, document_id: int, tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all embeddings for a document.

        Args:
            document_id: Document ID.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            List[Dict[str, Any]]: List of embeddings for the document.
        """
        if tenant_id:
            query = """
            SELECT e.id, e.document_id, e.embedding::text, e.model
            FROM embeddings e
            JOIN documents d ON e.document_id = d.id
            WHERE e.document_id = $1 AND d.tenant_id = $2;
            """
            params = (document_id, tenant_id)
        else:
            query = """
            SELECT id, document_id, embedding::text, model
            FROM embeddings
            WHERE document_id = $1;
            """
            params = (document_id,)

        results = await self.db.execute_query(
            query,
            params=params,
            fetch_all=True,
        )

        return results if results else []

    async def embedding_exists(
        self, embedding_id: int, tenant_id: Optional[str] = None
    ) -> bool:
        """
        Check if embedding exists.

        Args:
            embedding_id: Embedding ID.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            bool: True if exists, False otherwise.
        """
        if tenant_id:
            query = """
            SELECT 1 FROM embeddings e
            JOIN documents d ON e.document_id = d.id
            WHERE e.id = $1 AND d.tenant_id = $2
            LIMIT 1;
            """
            params = (embedding_id, tenant_id)
        else:
            query = """
            SELECT 1 FROM embeddings
            WHERE id = $1
            LIMIT 1;
            """
            params = (embedding_id,)

        result = await self.db.execute_query(
            query,
            params=params,
            fetch_one=True,
        )

        return result is not None

