"""
Mock RAG System Implementation

Mock implementation of RAGSystem for testing.
"""

from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock


class MockRAGSystem:
    """
    Mock implementation of RAGSystem for testing.
    
    Provides a mock RAG system that can be used in tests
    without requiring actual database or LLM connections.
    """

    def __init__(
        self,
        db: Optional[Any] = None,
        gateway: Optional[Any] = None,
        embedding_model: str = "text-embedding-3-small",
        generation_model: str = "gpt-4",
    ):
        """
        Initialize mock RAG system.
        
        Args:
            db: Optional mock database connection
            gateway: Optional mock LLM gateway
            embedding_model: Embedding model name
            generation_model: Generation model name
        """
        self.db = db or MagicMock()
        self.gateway = gateway or MagicMock()
        self.embedding_model = embedding_model
        self.generation_model = generation_model
        self._documents: Dict[str, Dict[str, Any]] = {}
        self._embeddings: Dict[str, List[float]] = {}

    async def ingest_document(
        self, document_id: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Mock ingest_document method - stores document in mock storage.
        
        Args:
            document_id: Unique document identifier
            content: Document content
            metadata: Optional document metadata
        """
        self._documents[document_id] = {
            "id": document_id,
            "content": content,
            "metadata": metadata or {},
        }
        # Mock embedding generation
        self._embeddings[document_id] = [0.1] * 1536  # Mock embedding vector

    async def query(
        self, query: str, top_k: int = 5, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Mock query method - returns mock RAG response.
        
        Args:
            query: User query
            top_k: Number of documents to retrieve
            **kwargs: Additional query parameters
            
        Returns:
            Mock RAG response with retrieved documents and generated answer
        """
        # Mock document retrieval
        retrieved_docs = list(self._documents.values())[:top_k]
        
        # Mock LLM generation
        mock_response = {
            "text": f"Mock answer for query: {query}",
            "model": self.generation_model,
            "retrieved_documents": retrieved_docs,
            "metadata": {
                "query": query,
                "top_k": top_k,
                "num_documents": len(retrieved_docs),
            },
        }
        
        return mock_response

    async def delete_document(self, document_id: str) -> None:
        """
        Mock delete_document method - removes document from mock storage.
        
        Args:
            document_id: Document ID to delete
        """
        self._documents.pop(document_id, None)
        self._embeddings.pop(document_id, None)

    def clear_all(self) -> None:
        """Clear all mock documents and embeddings."""
        self._documents.clear()
        self._embeddings.clear()


__all__ = ["MockRAGSystem"]

