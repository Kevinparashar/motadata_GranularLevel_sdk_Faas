"""
Vector Operations with pgvector

Provides functions for similarity search and vector operations using pgvector.
"""


from typing import Any, Dict, List, Optional, Tuple

from .connection import DatabaseConnection


class VectorOperations:
    """Vector operations using pgvector."""

    def __init__(self, db: DatabaseConnection):
        """
        Initialize vector operations.
        
        Args:
            db (DatabaseConnection): Database connection/handle.
        """
        self.db = db

    async def insert_embedding(
        self, document_id: int, embedding: List[float], model: str = "text-embedding-3-small"
    ) -> int:
        """
        Insert an embedding vector asynchronously.
        
        Args:
            document_id (int): Document ID to associate with embedding.
            embedding (List[float]): Embedding vector.
            model (str): Model name or identifier to use.
        
        Returns:
            int: Inserted embedding ID.
        """
        query = """
        INSERT INTO embeddings (document_id, embedding, model)
        VALUES ($1, $2::vector, $3)
        RETURNING id;
        """

        # Convert list to string format for pgvector
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"

        result = await self.db.execute_query(
            query, (document_id, embedding_str, model), fetch_one=True
        )
        return result["id"] if result else 0

    async def similarity_search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.0,
        model: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search using cosine distance asynchronously.
        
        Args:
            query_embedding (List[float]): Query embedding vector.
            limit (int): Maximum number of results.
            threshold (float): Similarity threshold (0.0 to 1.0).
            model (Optional[str]): Model name or identifier to use.
            tenant_id (Optional[str]): Tenant identifier for multi-tenancy.
        
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

        return await self.db.execute_query(query, params)

    async def batch_insert_embeddings(
        self, embeddings: List[Tuple[int, List[float], str]]
    ) -> None:
        """
        Batch insert multiple embeddings asynchronously.
        
        Args:
            embeddings (List[Tuple[int, List[float], str]]): List of (doc_id, embedding, model) tuples.
        
        Returns:
            None: Result of the operation.
        """
        if not embeddings:
            return

        # Prepare batch insert queries
        queries = []
        for doc_id, embedding, model in embeddings:
            embedding_str = "[" + ",".join(map(str, embedding)) + "]"
            query = """
            INSERT INTO embeddings (document_id, embedding, model)
            VALUES ($1, $2::vector, $3)
            """
            queries.append((query, (doc_id, embedding_str, model)))

        # Execute all in a transaction
        await self.db.execute_transaction(queries)

    async def get_embedding(self, embedding_id: int) -> Optional[Dict[str, Any]]:
        """
        Get an embedding by ID asynchronously.
        
        Args:
            embedding_id (int): Embedding ID.
        
        Returns:
            Optional[Dict[str, Any]]: Embedding data or None.
        """
        query = """
        SELECT id, document_id, embedding::text, model
        FROM embeddings
        WHERE id = $1;
        """
        return await self.db.execute_query(query, (embedding_id,), fetch_one=True)

    async def delete_embeddings(self, document_id: int) -> int:
        """
        Delete all embeddings for a document asynchronously.
        
        Args:
            document_id (int): Document ID.
        
        Returns:
            int: Number of embeddings deleted.
        """
        query = """
        DELETE FROM embeddings
        WHERE document_id = $1;
        """
        return await self.db.execute_query(query, (document_id,), fetch_all=False)

    async def update_embedding(
        self, embedding_id: int, new_embedding: List[float]
    ) -> bool:
        """
        Update an existing embedding asynchronously.
        
        Args:
            embedding_id (int): Embedding ID to update.
            new_embedding (List[float]): New embedding vector.
        
        Returns:
            bool: True if update successful.
        """
        embedding_str = "[" + ",".join(map(str, new_embedding)) + "]"
        query = """
        UPDATE embeddings
        SET embedding = $1::vector
        WHERE id = $2;
        """
        result = await self.db.execute_query(
            query, (embedding_str, embedding_id), fetch_all=False
        )
        return result > 0
