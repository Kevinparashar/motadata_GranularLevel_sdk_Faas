"""
Vector Operations with pgvector

Provides functions for similarity search and vector operations using pgvector.
"""


import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from .connection import DatabaseConnection

if TYPE_CHECKING:
    from ...faas.shared.dal.embedding_dal import EmbeddingDAL  

logger = logging.getLogger(__name__)


class VectorOperations:
    """Vector operations using pgvector."""

    def __init__(
        self,
        db: DatabaseConnection,
        embedding_dal: Optional["EmbeddingDAL"] = None,
        verify_extension: bool = True,
        default_dimension: int = 1536,
    ):
        """
        Initialize vector operations.
        
        Args:
            db (DatabaseConnection): Database connection/handle.
            embedding_dal: Optional EmbeddingDAL instance for database persistence.
            verify_extension (bool): Whether to verify pgvector extension on initialization.
            default_dimension (int): Default embedding dimension for validation.
        """
        self.db = db
        self.default_dimension = default_dimension
        self._extension_verified = False
        
        # Initialize EmbeddingDAL if not provided
        if embedding_dal is None:
            from ...faas.shared.dal.embedding_dal import EmbeddingDAL  
            self.embedding_dal = EmbeddingDAL(db)
        else:
            self.embedding_dal = embedding_dal
        
        # Verify extension if requested
        if verify_extension:
            # Note: This is async, so we'll verify on first operation
            # Store the flag to verify later
            self._verify_on_first_operation = True
        else:
            self._verify_on_first_operation = False

    async def _ensure_extension(self) -> None:
        """
        Ensure pgvector extension is available.
        
        Raises:
            RuntimeError: If pgvector extension is not available.
        """
        if self._extension_verified:
            return
        
        # OTEL Integration (optional)
        tracer = None
        try:
            from ..otel_integration import create_otel_tracer
            tracer = create_otel_tracer(service_name="vector-operations")
        except (ImportError, Exception):
            tracer = None
        
        if tracer:
            with tracer.start_trace("vector_operations.verify_extension") as trace:
                trace.set_attribute("operation", "verify_pgvector_extension")
                
                try:
                    is_available = await self.db.verify_pgvector_extension()
                    trace.set_attribute("extension.available", str(is_available))
                    
                    if not is_available:
                        trace.record_exception(RuntimeError("pgvector extension not found"))
                        raise RuntimeError(
                            "pgvector extension is not installed. "
                            "Please install it using: CREATE EXTENSION vector;"
                        )
                    
                    self._extension_verified = True
                except Exception as e:
                    trace.record_exception(e)
                    raise
        else:
            # No OTEL - execute without tracing
            is_available = await self.db.verify_pgvector_extension()
            
            if not is_available:
                raise RuntimeError(
                    "pgvector extension is not installed. "
                    "Please install it using: CREATE EXTENSION vector;"
                )
            
            self._extension_verified = True

    def _validate_embedding_dimension(self, embedding: List[float], expected_dim: Optional[int] = None) -> None:
        """
        Validate embedding dimension.
        
        Args:
            embedding (List[float]): Embedding vector to validate.
            expected_dim (Optional[int]): Expected dimension. Uses default_dimension if None.
        
        Raises:
            ValueError: If embedding dimension doesn't match expected dimension.
        """
        if not embedding:
            raise ValueError("Embedding cannot be empty")
        
        actual_dim = len(embedding)
        expected = expected_dim or self.default_dimension
        
        if actual_dim != expected:
            raise ValueError(
                f"Embedding dimension mismatch: expected {expected}, got {actual_dim}"
            )

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check for vector operations.
        
        Returns:
            Dict[str, Any]: Health check results including extension status and connection status.
        """
        health_status: Dict[str, Any] = {
            "connection": False,
            "pgvector_extension": False,
            "embedding_dal": False,
        }
        
        try:
            # Check database connection
            health_status["connection"] = await self.db.check_connection()
            
            # Check pgvector extension
            if health_status["connection"]:
                health_status["pgvector_extension"] = await self.db.verify_pgvector_extension()
            
            # Check EmbeddingDAL (basic check)
            health_status["embedding_dal"] = self.embedding_dal is not None
            
            return health_status
        except Exception as e:
            logger.error(f"Vector operations health check failed: {e}")
            health_status["error"] = str(e)
            return health_status

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
        
        Raises:
            RuntimeError: If pgvector extension is not available.
            ValueError: If embedding dimension is invalid.
        """
        # Verify extension on first operation if needed
        if self._verify_on_first_operation:
            await self._ensure_extension()
        
        # Validate embedding dimension
        self._validate_embedding_dimension(embedding)
        
        # OTEL Integration (optional)
        tracer = None
        try:
            from ..otel_integration import create_otel_tracer
            tracer = create_otel_tracer(service_name="vector-operations")
        except (ImportError, Exception):
            tracer = None
        
        if tracer:
            with tracer.start_trace("vector_operations.insert_embedding") as trace:
                trace.set_attribute("operation", "insert_embedding")
                trace.set_attribute("document_id", document_id)
                trace.set_attribute("model", model)
                trace.set_attribute("embedding_dimension", len(embedding))
                
                try:
                    result = await self.embedding_dal.insert_embedding(
                        document_id=document_id,
                        embedding=embedding,
                        model=model,
                        tenant_id=tenant_id,
                    )
                    trace.set_attribute("embedding_id", result)
                    return result
                except Exception as e:
                    trace.record_exception(e)
                    raise
        else:
            # No OTEL - execute without tracing
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
        
        Raises:
            RuntimeError: If pgvector extension is not available.
            ValueError: If query embedding dimension is invalid.
        """
        # Verify extension on first operation if needed
        if self._verify_on_first_operation:
            await self._ensure_extension()
        
        # Validate query embedding dimension
        self._validate_embedding_dimension(query_embedding)
        
        # OTEL Integration (optional)
        tracer = None
        try:
            from ..otel_integration import create_otel_tracer
            tracer = create_otel_tracer(service_name="vector-operations")
        except (ImportError, Exception):
            tracer = None
        
        if tracer:
            with tracer.start_trace("vector_operations.similarity_search") as trace:
                trace.set_attribute("operation", "similarity_search")
                trace.set_attribute("limit", limit)
                trace.set_attribute("threshold", threshold)
                trace.set_attribute("query_dimension", len(query_embedding))
                
                try:
                    results = await self.embedding_dal.similarity_search(
                        query_embedding=query_embedding,
                        limit=limit,
                        threshold=threshold,
                        model=model,
                        tenant_id=tenant_id,
                    )
                    trace.set_attribute("results_count", len(results))
                    return results
                except Exception as e:
                    trace.record_exception(e)
                    raise
        else:
            # No OTEL - execute without tracing
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
        
        Raises:
            RuntimeError: If pgvector extension is not available.
            ValueError: If any embedding dimension is invalid.
        """
        if not embeddings:
            return
        
        # Verify extension on first operation if needed
        if self._verify_on_first_operation:
            await self._ensure_extension()
        
        # Validate all embedding dimensions
        for _doc_id, embedding, _model in embeddings:
            self._validate_embedding_dimension(embedding)
        
        # OTEL Integration (optional)
        tracer = None
        try:
            from ..otel_integration import create_otel_tracer
            tracer = create_otel_tracer(service_name="vector-operations")
        except (ImportError, Exception):
            tracer = None
        
        if tracer:
            with tracer.start_trace("vector_operations.batch_insert_embeddings") as trace:
                trace.set_attribute("operation", "batch_insert_embeddings")
                trace.set_attribute("batch_size", len(embeddings))
                
                try:
                    await self.embedding_dal.batch_insert_embeddings(
                        embeddings_data=embeddings,
                        tenant_id=tenant_id,
                    )
                except Exception as e:
                    trace.record_exception(e)
                    raise
        else:
            # No OTEL - execute without tracing
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
        
        Raises:
            RuntimeError: If pgvector extension is not available.
            ValueError: If embedding dimension is invalid.
        """
        # Verify extension on first operation if needed
        if self._verify_on_first_operation:
            await self._ensure_extension()
        
        # Validate embedding dimension
        self._validate_embedding_dimension(new_embedding)
        
        # OTEL Integration (optional)
        tracer = None
        try:
            from ..otel_integration import create_otel_tracer
            tracer = create_otel_tracer(service_name="vector-operations")
        except (ImportError, Exception):
            tracer = None
        
        if tracer:
            with tracer.start_trace("vector_operations.update_embedding") as trace:
                trace.set_attribute("operation", "update_embedding")
                trace.set_attribute("embedding_id", embedding_id)
                trace.set_attribute("embedding_dimension", len(new_embedding))
                
                try:
                    result = await self.embedding_dal.update_embedding(
                        embedding_id=embedding_id,
                        new_embedding=new_embedding,
                        tenant_id=tenant_id,
                    )
                    trace.set_attribute("update_success", result)
                    return result
                except Exception as e:
                    trace.record_exception(e)
                    raise
        else:
            # No OTEL - execute without tracing
            return await self.embedding_dal.update_embedding(
                embedding_id=embedding_id,
                new_embedding=new_embedding,
                tenant_id=tenant_id,
            )
