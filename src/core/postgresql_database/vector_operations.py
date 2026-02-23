"""
Vector Operations with pgvector

Provides functions for similarity search and vector operations using pgvector.
"""


from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from .connection import DatabaseConnection

if TYPE_CHECKING:
    from ...faas.shared.dal.embedding_dal import EmbeddingDAL  


class VectorOperations:
    """Vector operations using pgvector."""

    def __init__(
        self,
        db: DatabaseConnection,
        embedding_dal: Optional["EmbeddingDAL"] = None,
    ):
        """
        Initialize vector operations.
        
        Args:
            db (DatabaseConnection): Database connection/handle.
            embedding_dal: Optional EmbeddingDAL instance for database persistence.
        """
        self.db = db
        # Initialize EmbeddingDAL if not provided
        if embedding_dal is None:
            from ...faas.shared.dal.embedding_dal import EmbeddingDAL  
            self.embedding_dal = EmbeddingDAL(db)
        else:
            self.embedding_dal = embedding_dal

    async def insert_embedding(
        self,
        document_id: int,
        embedding: List[float],
        model: str = "text-embedding-3-small",
        tenant_id: Optional[str] = None,
    ) -> int:
        """
        Insert an embedding vector asynchronously.
        
        Args:
            document_id (int): Document ID to associate with embedding.
            embedding (List[float]): Embedding vector.
            model (str): Model name or identifier to use.
            tenant_id (Optional[str]): Tenant identifier for tenant isolation.
        
        Returns:
            int: Inserted embedding ID.
        """
        return await self.embedding_dal.insert_embedding(
            document_id=document_id,
            embedding=embedding,
            model=model,
            tenant_id=tenant_id,
        )

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
        return await self.embedding_dal.similarity_search(
            query_embedding=query_embedding,
            limit=limit,
            threshold=threshold,
            model=model,
            tenant_id=tenant_id,
        )

    async def batch_insert_embeddings(
        self,
        embeddings: List[Tuple[int, List[float], str]],
        tenant_id: Optional[str] = None,
    ) -> None:
        """
        Batch insert multiple embeddings asynchronously.
        
        Args:
            embeddings (List[Tuple[int, List[float], str]]): List of (doc_id, embedding, model) tuples.
            tenant_id (Optional[str]): Tenant identifier for tenant isolation.
        
        Returns:
            None: Result of the operation.
        """
        await self.embedding_dal.batch_insert_embeddings(
            embeddings_data=embeddings,
            tenant_id=tenant_id,
        )

    async def get_embedding(
        self, embedding_id: int, tenant_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get an embedding by ID asynchronously.
        
        Args:
            embedding_id (int): Embedding ID.
            tenant_id (Optional[str]): Tenant identifier for tenant isolation.
        
        Returns:
            Optional[Dict[str, Any]]: Embedding data or None.
        """
        return await self.embedding_dal.get_embedding(
            embedding_id=embedding_id,
            tenant_id=tenant_id,
        )

    async def delete_embeddings(
        self, document_id: int, tenant_id: Optional[str] = None
    ) -> int:
        """
        Delete all embeddings for a document asynchronously.
        
        Args:
            document_id (int): Document ID.
            tenant_id (Optional[str]): Tenant identifier for tenant isolation.
        
        Returns:
            int: Number of embeddings deleted.
        """
        return await self.embedding_dal.delete_embeddings(
            document_id=document_id,
            tenant_id=tenant_id,
        )

    async def update_embedding(
        self,
        embedding_id: int,
        new_embedding: List[float],
        tenant_id: Optional[str] = None,
    ) -> bool:
        """
        Update an existing embedding asynchronously.
        
        Args:
            embedding_id (int): Embedding ID to update.
            new_embedding (List[float]): New embedding vector.
            tenant_id (Optional[str]): Tenant identifier for tenant isolation.
        
        Returns:
            bool: True if update successful.
        """
        return await self.embedding_dal.update_embedding(
            embedding_id=embedding_id,
            new_embedding=new_embedding,
            tenant_id=tenant_id,
        )
