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

    def insert_embedding(
        self, document_id: int, embedding: List[float], model: str = "text-embedding-3-small"
    ) -> int:
        """
        Insert an embedding vector.
        
        Args:
            document_id (int): Input parameter for this operation.
            embedding (List[float]): Input parameter for this operation.
            model (str): Model name or identifier to use.
        
        Returns:
            int: Result of the operation.
        """
        query = """
        INSERT INTO embeddings (document_id, embedding, model)
        VALUES (%s, %s::vector, %s)
        RETURNING id;
        """

        # Convert list to string format for pgvector
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"

        result = self.db.execute_query(query, (document_id, embedding_str, model), fetch_one=True)
        return result["id"]

    def similarity_search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.0,
        model: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search using cosine distance.
        
        Args:
            query_embedding (List[float]): Input parameter for this operation.
            limit (int): Input parameter for this operation.
            threshold (float): Input parameter for this operation.
            model (Optional[str]): Model name or identifier to use.
        
        Returns:
            List[Dict[str, Any]]: Dictionary result of the operation.
        """
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

        if model:
            query = """
            SELECT 
                e.id,
                e.document_id,
                d.title,
                d.content,
                d.metadata,
                d.source,
                1 - (e.embedding <=> %s::vector) as similarity
            FROM embeddings e
            JOIN documents d ON e.document_id = d.id
            WHERE e.model = %s
                AND 1 - (e.embedding <=> %s::vector) >= %s
            ORDER BY e.embedding <=> %s::vector
            LIMIT %s;
            """
            params = (embedding_str, model, embedding_str, threshold, embedding_str, limit)
        else:
            query = """
            SELECT 
                e.id,
                e.document_id,
                d.title,
                d.content,
                d.metadata,
                d.source,
                1 - (e.embedding <=> %s::vector) as similarity
            FROM embeddings e
            JOIN documents d ON e.document_id = d.id
            WHERE 1 - (e.embedding <=> %s::vector) >= %s
            ORDER BY e.embedding <=> %s::vector
            LIMIT %s;
            """
            params = (embedding_str, embedding_str, threshold, embedding_str, limit)

        return self.db.execute_query(query, params)

    def batch_insert_embeddings(self, embeddings: List[Tuple[int, List[float], str]]) -> None:
        """
        Batch insert multiple embeddings.
        
        Args:
            embeddings (List[Tuple[int, List[float], str]]): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        """
        # Prepare data for batch insert
        values = []
        for doc_id, embedding, model in embeddings:
            embedding_str = "[" + ",".join(map(str, embedding)) + "]"
            values.append((doc_id, embedding_str, model))

        with self.db.get_cursor() as cursor:
            from psycopg2.extras import execute_values

            execute_values(
                cursor, "INSERT INTO embeddings (document_id, embedding, model) VALUES %s", values
            )
