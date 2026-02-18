"""
Mock RAG System Implementation

Mock implementation of RAGSystem for testing.

Copyright (c) 2024 Motadata. All rights reserved.
"""

import asyncio
import uuid
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock


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

    async def ingest_document_async(
        self,
        title: str,
        content: str,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
    ) -> str:
        """
        Mock ingest_document_async method - stores document in mock storage.
        
        Args:
            title: Document title
            content: Document content
            source: Optional source URL/path
            metadata: Optional document metadata
            tenant_id: Optional tenant ID (for interface compatibility)
            
        Returns:
            Document ID string
        """
        # Minimal async operation to satisfy linter
        await asyncio.sleep(0)
        
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        self._documents[document_id] = {
            "id": document_id,
            "title": title,
            "content": content,
            "source": source,
            "metadata": metadata or {},
            "tenant_id": tenant_id,
        }
        # Mock embedding generation
        self._embeddings[document_id] = [0.1] * 1536  # Mock embedding vector
        
        return document_id

    async def query_async(
        self,
        query: str,
        tenant_id: Optional[str] = None,
        top_k: int = 5,
        threshold: float = 0.7,
        max_tokens: int = 1000,
        use_query_rewriting: bool = True,
        retrieval_strategy: str = "vector",
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Mock query_async method - returns mock RAG response.
        
        Args:
            query: User query text
            tenant_id: Optional tenant ID (for interface compatibility)
            top_k: Number of documents to retrieve
            threshold: Minimum relevance score (for interface compatibility)
            max_tokens: Maximum tokens for generation (for interface compatibility)
            use_query_rewriting: Enable query rewriting (for interface compatibility)
            retrieval_strategy: Retrieval strategy (for interface compatibility)
            user_id: Optional user ID (for interface compatibility)
            conversation_id: Optional conversation ID (for interface compatibility)
            
        Returns:
            Mock RAG response with retrieved documents and generated answer
        """
        # Minimal async operation to satisfy linter
        await asyncio.sleep(0)
        
        # Use parameters to avoid unused warnings (interface compatibility)
        _ = threshold, max_tokens, use_query_rewriting, retrieval_strategy, user_id, conversation_id
        
        # Filter documents by tenant_id if provided
        documents = list(self._documents.values())
        if tenant_id:
            documents = [doc for doc in documents if doc.get("tenant_id") == tenant_id]
        
        # Mock document retrieval
        retrieved_docs = documents[:top_k]
        
        # Mock LLM generation
        mock_response = {
            "answer": f"Mock answer for query: {query}",
            "retrieved_documents": retrieved_docs,
            "num_documents": len(retrieved_docs),
            "query_used": query,
            "original_query": query,
            "memory_used": 0,
        }
        
        return mock_response

    async def delete_document(self, document_id: str) -> bool:
        """
        Mock delete_document method - removes document from mock storage.
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            True if document was deleted, False if not found
        """
        # Minimal async operation to satisfy linter
        await asyncio.sleep(0)
        
        if document_id in self._documents:
            self._documents.pop(document_id, None)
            self._embeddings.pop(document_id, None)
            return True
        return False

    def clear_all(self) -> None:
        """Clear all mock documents and embeddings."""
        self._documents.clear()
        self._embeddings.clear()


__all__ = ["MockRAGSystem"]

