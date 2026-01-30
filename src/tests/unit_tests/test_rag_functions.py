"""
Unit Tests for RAG System Functions

Tests factory functions, convenience functions, and utilities for RAG system.
"""

from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.core.rag.document_processor import DocumentProcessor
from src.core.rag.functions import (  # Factory functions; Convenience functions; Utility functions
    batch_ingest_documents,
    batch_ingest_documents_async,
    batch_process_documents,
    create_document_processor,
    create_rag_system,
    delete_document_simple,
    ingest_document_simple,
    ingest_document_simple_async,
    quick_rag_query,
    quick_rag_query_async,
    update_document_simple,
)
from src.core.rag.rag_system import RAGSystem


class TestFactoryFunctions:
    """Test factory functions for RAG system creation."""

    @pytest.fixture
    def mock_db(self):
        """Mock database connection."""
        return Mock()

    @pytest.fixture
    def mock_gateway(self):
        """Mock LiteLLM Gateway."""
        gateway = Mock()
        gateway.generate_embeddings_async = AsyncMock(return_value=Mock(embeddings=[[0.1] * 1536]))
        gateway.generate_async = AsyncMock(return_value=Mock(text="Generated response"))
        return gateway

    def test_create_rag_system(self, mock_db, mock_gateway):
        """Test create_rag_system factory function."""
        rag = create_rag_system(
            db=mock_db,
            gateway=mock_gateway,
            embedding_model="text-embedding-3-small",
            generation_model="gpt-4",
        )

        assert isinstance(rag, RAGSystem)
        assert rag.embedding_model == "text-embedding-3-small"
        assert rag.generation_model == "gpt-4"

    def test_create_rag_system_with_defaults(self, mock_db, mock_gateway):
        """Test create_rag_system with default parameters."""
        rag = create_rag_system(db=mock_db, gateway=mock_gateway)

        assert isinstance(rag, RAGSystem)
        assert rag.embedding_model == "text-embedding-3-small"
        assert rag.generation_model == "gpt-4"

    def test_create_rag_system_with_kwargs(self, mock_db, mock_gateway):
        """Test create_rag_system with additional kwargs."""
        rag = create_rag_system(db=mock_db, gateway=mock_gateway, custom_param="value")

        assert isinstance(rag, RAGSystem)

    def test_create_document_processor(self):
        """Test create_document_processor factory function."""
        processor = create_document_processor(
            chunk_size=500, chunk_overlap=100, strategy="sentence"
        )

        assert isinstance(processor, DocumentProcessor)
        assert processor.chunk_size == 500
        assert processor.chunk_overlap == 100
        assert processor.strategy == "sentence"

    def test_create_document_processor_defaults(self):
        """Test create_document_processor with default parameters."""
        processor = create_document_processor()

        assert isinstance(processor, DocumentProcessor)
        assert processor.chunk_size == 1000
        assert processor.chunk_overlap == 200
        assert processor.strategy == "fixed"


class TestConvenienceFunctions:
    """Test high-level convenience functions."""

    @pytest.fixture
    def mock_rag_system(self):
        """Create a mock RAG system."""
        rag = Mock(spec=RAGSystem)
        rag.query = Mock(
            return_value={
                "answer": "Test answer",
                "sources": [{"id": "doc1", "content": "Test content"}],
                "metadata": {},
            }
        )
        rag.query_async = AsyncMock(
            return_value={
                "answer": "Async answer",
                "sources": [{"id": "doc1", "content": "Test content"}],
                "metadata": {},
            }
        )
        rag.ingest_document = Mock(return_value="doc-123")
        rag.ingest_document_async = AsyncMock(return_value="doc-456")
        return rag

    def test_quick_rag_query(self, mock_rag_system):
        """Test quick_rag_query convenience function."""
        result = quick_rag_query(
            rag_system=mock_rag_system, query="What is AI?", top_k=5, threshold=0.7, max_tokens=1000
        )

        assert result["answer"] == "Test answer"
        assert "sources" in result
        mock_rag_system.query.assert_called_once()

    def test_quick_rag_query_defaults(self, mock_rag_system):
        """Test quick_rag_query with default parameters."""
        result = quick_rag_query(mock_rag_system, "Test query")

        assert "answer" in result
        mock_rag_system.query.assert_called_once()

    def test_quick_rag_query_with_hybrid(self, mock_rag_system):
        """Test quick_rag_query with hybrid retrieval strategy."""
        result = quick_rag_query(mock_rag_system, "Test query", retrieval_strategy="hybrid")

        assert "answer" in result
        # Verify hybrid strategy was passed
        call_args = mock_rag_system.query.call_args
        assert call_args[1]["retrieval_strategy"] == "hybrid"

    def test_quick_rag_query_with_rewriting(self, mock_rag_system):
        """Test quick_rag_query with query rewriting."""
        result = quick_rag_query(mock_rag_system, "Test query", use_query_rewriting=True)

        assert "answer" in result
        call_args = mock_rag_system.query.call_args
        assert call_args[1]["use_query_rewriting"] is True

    @pytest.mark.asyncio
    async def test_quick_rag_query_async(self, mock_rag_system):
        """Test quick_rag_query_async convenience function."""
        result = await quick_rag_query_async(
            rag_system=mock_rag_system, query="What is AI?", top_k=5, threshold=0.7, max_tokens=1000
        )

        assert result["answer"] == "Async answer"
        assert "sources" in result
        mock_rag_system.query_async.assert_called_once()

    def test_ingest_document_simple(self, mock_rag_system):
        """Test ingest_document_simple convenience function."""
        doc_id = ingest_document_simple(
            rag_system=mock_rag_system,
            title="Test Document",
            content="Test content",
            source="test_source",
            metadata={"author": "Test Author"},
        )

        assert doc_id == "doc-123"
        mock_rag_system.ingest_document.assert_called_once()

    def test_ingest_document_simple_minimal(self, mock_rag_system):
        """Test ingest_document_simple with minimal parameters."""
        doc_id = ingest_document_simple(rag_system=mock_rag_system, title="Test", content="Content")

        assert doc_id == "doc-123"

    @pytest.mark.asyncio
    async def test_ingest_document_simple_async(self, mock_rag_system):
        """Test ingest_document_simple_async convenience function."""
        doc_id = await ingest_document_simple_async(
            rag_system=mock_rag_system, title="Test Document", content="Test content"
        )

        assert doc_id == "doc-456"
        mock_rag_system.ingest_document_async.assert_called_once()

    def test_batch_ingest_documents(self, mock_rag_system):
        """Test batch_ingest_documents convenience function."""
        documents = [
            {"title": "Doc 1", "content": "Content 1"},
            {"title": "Doc 2", "content": "Content 2"},
            {"title": "Doc 3", "content": "Content 3"},
        ]

        doc_ids = batch_ingest_documents(
            rag_system=mock_rag_system, documents=documents, batch_size=2
        )

        assert len(doc_ids) == 3
        assert mock_rag_system.ingest_document.call_count == 3

    def test_batch_ingest_documents_empty(self, mock_rag_system):
        """Test batch_ingest_documents with empty document list."""
        doc_ids = batch_ingest_documents(rag_system=mock_rag_system, documents=[], batch_size=10)

        assert doc_ids == []
        mock_rag_system.ingest_document.assert_not_called()

    @pytest.mark.asyncio
    async def test_batch_ingest_documents_async(self, mock_rag_system):
        """Test batch_ingest_documents_async convenience function."""
        documents = [
            {"title": "Doc 1", "content": "Content 1"},
            {"title": "Doc 2", "content": "Content 2"},
        ]

        doc_ids = await batch_ingest_documents_async(
            rag_system=mock_rag_system, documents=documents, batch_size=10
        )

        assert len(doc_ids) == 2
        assert mock_rag_system.ingest_document_async.call_count == 2


class TestUtilityFunctions:
    """Test utility functions."""

    def test_batch_process_documents(self):
        """Test batch_process_documents utility function."""
        documents = [
            {"id": "doc1", "content": "Content 1"},
            {"id": "doc2", "content": "Content 2"},
            {"id": "doc3", "content": "Content 3"},
        ]

        def process_func(doc: Dict[str, Any]) -> str:
            return f"Processed: {doc['id']}"

        results = batch_process_documents(
            documents=documents, processor_func=process_func, batch_size=2
        )

        assert len(results) == 3
        assert results[0] == "Processed: doc1"
        assert results[1] == "Processed: doc2"
        assert results[2] == "Processed: doc3"

    def test_batch_process_documents_with_errors(self):
        """Test batch_process_documents with processing errors."""
        documents = [
            {"id": "doc1", "content": "Content 1"},
            {"id": "doc2", "content": "Content 2"},
            {"id": "doc3", "content": "Content 3"},
        ]

        def process_func(doc: Dict[str, Any]) -> str:
            if doc["id"] == "doc2":
                raise Exception("Processing error")
            return f"Processed: {doc['id']}"

        results = batch_process_documents(
            documents=documents, processor_func=process_func, batch_size=2
        )

        # Should skip failed documents
        assert len(results) == 2
        assert results[0] == "Processed: doc1"
        assert results[1] == "Processed: doc3"

    def test_batch_process_documents_empty(self):
        """Test batch_process_documents with empty document list."""

        def process_func(doc: Dict[str, Any]) -> str:
            return "processed"

        results = batch_process_documents(documents=[], processor_func=process_func, batch_size=10)

        assert results == []

    def test_update_document_simple(self, mock_rag_system):
        """Test update_document_simple convenience function."""
        mock_rag_system.update_document = Mock(return_value=True)

        success = update_document_simple(
            rag_system=mock_rag_system,
            document_id="doc-123",
            title="Updated Title",
            content="Updated content",
        )

        assert success is True
        mock_rag_system.update_document.assert_called_once_with(
            "doc-123", "Updated Title", "Updated content", None
        )

    def test_delete_document_simple(self, mock_rag_system):
        """Test delete_document_simple convenience function."""
        mock_rag_system.delete_document = Mock(return_value=True)

        success = delete_document_simple(rag_system=mock_rag_system, document_id="doc-123")

        assert success is True
        mock_rag_system.delete_document.assert_called_once_with("doc-123")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
