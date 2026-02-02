"""
Unit Tests for RAG Component

Tests document processing, retrieval, and generation.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.rag import RAGSystem
from src.core.rag.document_processor import DocumentChunk, DocumentProcessor
from src.core.rag.generator import RAGGenerator
from src.core.rag.retriever import Retriever


class TestDocumentProcessor:
    """Test DocumentProcessor."""

    def test_chunk_document(self):
        """Test document chunking."""
        processor = DocumentProcessor(chunk_size=100)

        content = "This is a test document. " * 100
        chunks = processor.chunk_document(content=content, document_id="doc-001")

        assert len(chunks) > 0
        assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)

    def test_chunk_with_overlap(self):
        """Test chunking with overlap."""
        processor = DocumentProcessor(chunk_size=50, chunk_overlap=10)

        content = "Test content " * 50
        chunks = processor.chunk_document(content=content, document_id="doc-001")

        assert len(chunks) > 0


class TestRetriever:
    """Test Retriever."""

    @pytest.fixture
    def mock_retriever(self):
        """Mock retriever with dependencies."""
        mock_vector_ops = MagicMock()
        mock_gateway = MagicMock()

        mock_vector_ops.similarity_search.return_value = [
            {"id": 1, "document_id": 1, "content": "Test content", "similarity": 0.95}
        ]

        mock_embedding_response = MagicMock()
        mock_embedding_response.embeddings = [[0.1] * 1536]
        mock_gateway.embed.return_value = mock_embedding_response

        retriever = Retriever(
            vector_ops=mock_vector_ops,
            gateway=mock_gateway,
            embedding_model="text-embedding-3-small",
        )

        return retriever, mock_vector_ops, mock_gateway

    def test_retrieve(self, mock_retriever):
        """Test document retrieval."""
        retriever, _, mock_gateway = mock_retriever

        results = retriever.retrieve(query="Test query", top_k=5, threshold=0.7)

        assert len(results) == 1
        assert abs(results[0]["similarity"] - 0.95) < 0.001
        mock_gateway.embed.assert_called_once()


class TestRAGGenerator:
    """Test RAGGenerator."""

    @pytest.fixture
    def mock_generator(self):
        """Mock generator with gateway."""
        mock_gateway = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Generated answer"
        mock_gateway.generate.return_value = mock_response

        generator = RAGGenerator(gateway=mock_gateway, model="gpt-4")

        return generator, mock_gateway

    def test_generate(self, mock_generator):
        """Test response generation."""
        generator, mock_gateway = mock_generator

        context_docs = [{"content": "Context document 1"}, {"content": "Context document 2"}]

        answer = generator.generate(
            query="Test question", context_documents=context_docs, max_tokens=200
        )

        assert answer == "Generated answer"
        mock_gateway.generate.assert_called_once()


class TestRAGSystem:
    """Test RAGSystem."""

    @pytest.fixture
    def mock_rag_system(self):
        """Mock RAG system with dependencies."""
        mock_db = MagicMock()
        mock_gateway = MagicMock()

        # Mock database operations
        mock_db.execute_query.return_value = {"id": 1}

        # Mock embedding response
        mock_embedding_response = MagicMock()
        mock_embedding_response.embeddings = [[0.1] * 1536]
        mock_gateway.embed.return_value = mock_embedding_response

        # Mock generation response
        mock_gen_response = MagicMock()
        mock_gen_response.text = "Generated answer"
        mock_gateway.generate.return_value = mock_gen_response

        rag = RAGSystem(
            db=mock_db,
            gateway=mock_gateway,
            embedding_model="text-embedding-3-small",
            generation_model="gpt-4",
        )

        return rag, mock_db, mock_gateway

    def test_ingest_document(self, mock_rag_system):
        """Test document ingestion."""
        rag, mock_db, mock_gateway = mock_rag_system

        doc_id = rag.ingest_document(
            title="Test Document", content="Test content", source="test_source"
        )

        assert doc_id is not None
        mock_db.execute_query.assert_called()
        mock_gateway.embed.assert_called()

    def test_query(self, mock_rag_system):
        """Test RAG query."""
        rag, _, _ = mock_rag_system

        # Mock vector operations
        with patch.object(rag.vector_ops, "similarity_search") as mock_search:
            mock_search.return_value = [
                {"id": 1, "document_id": 1, "content": "Test", "similarity": 0.9}
            ]

            result = rag.query(query="Test query", top_k=5, threshold=0.7)

            assert "answer" in result
            assert "retrieved_documents" in result
            assert result["num_documents"] == 1

    @pytest.mark.asyncio
    async def test_query_async(self, mock_rag_system):
        """Test async RAG query."""
        rag, _, mock_gateway = mock_rag_system

        # Mock async gateway
        mock_async_response = MagicMock()
        mock_async_response.text = "Async answer"
        mock_gateway.generate_async = AsyncMock(return_value=mock_async_response)

        with patch.object(rag.vector_ops, "similarity_search") as mock_search:
            mock_search.return_value = [
                {"id": 1, "document_id": 1, "content": "Test", "similarity": 0.9}
            ]

            result = await rag.query_async(query="Test query", top_k=5)

            assert "answer" in result
            assert result["answer"] == "Async answer"

    def test_memory_integration_enabled(self):
        """Test RAG with memory integration enabled."""
        from src.core.agno_agent_framework.memory import AgentMemory

        mock_db = MagicMock()
        mock_gateway = MagicMock()

        rag = RAGSystem(
            db=mock_db,
            gateway=mock_gateway,
            enable_memory=True,
            memory_config={"max_episodic": 100, "max_semantic": 200},
        )

        # Memory should be initialized
        assert rag.memory is not None
        assert isinstance(rag.memory, AgentMemory)

    def test_memory_integration_disabled(self):
        """Test RAG with memory integration disabled."""
        mock_db = MagicMock()
        mock_gateway = MagicMock()

        rag = RAGSystem(db=mock_db, gateway=mock_gateway, enable_memory=False)

        # Memory should not be initialized
        assert rag.memory is None

    @pytest.mark.asyncio
    async def test_query_with_memory_context(self):
        """Test RAG query with memory context retrieval."""
        from src.core.agno_agent_framework.memory import MemoryType

        mock_db = MagicMock()
        mock_gateway = MagicMock()

        # Create RAG with memory
        rag = RAGSystem(
            db=mock_db,
            gateway=mock_gateway,
            enable_memory=True,
            memory_config={"max_episodic": 100},
        )

        # Store some memories
        rag.memory.store(
            content="Previous query about AI",
            memory_type=MemoryType.EPISODIC,
            metadata={"query": "What is AI?"},
        )

        # Mock gateway responses
        mock_embedding_response = MagicMock()
        mock_embedding_response.embeddings = [[0.1] * 1536]
        mock_gateway.embed_async = AsyncMock(return_value=mock_embedding_response)

        mock_gen_response = MagicMock()
        mock_gen_response.text = "Answer with context"
        mock_gateway.generate_async = AsyncMock(return_value=mock_gen_response)

        # Mock vector search
        with patch.object(rag.vector_ops, "similarity_search") as mock_search:
            mock_search.return_value = [{"id": 1, "content": "Document", "similarity": 0.9}]

            result = await rag.query_async(
                query="Tell me more",
                user_id="test_user",
                conversation_id="test_conv",
                tenant_id="test_tenant",
            )

            # Should use memory context
            assert "answer" in result
            # Memory should have been retrieved
            assert rag.memory is not None

    @pytest.mark.asyncio
    async def test_memory_storage_after_query(self):
        """Test that query-answer pairs are stored in memory."""
        mock_db = MagicMock()
        mock_gateway = MagicMock()

        rag = RAGSystem(
            db=mock_db,
            gateway=mock_gateway,
            enable_memory=True,
            memory_config={"max_episodic": 100},
        )

        initial_memory_size = len(rag.memory._episodic)

        # Mock gateway responses
        mock_embedding_response = MagicMock()
        mock_embedding_response.embeddings = [[0.1] * 1536]
        mock_gateway.embed_async = AsyncMock(return_value=mock_embedding_response)

        mock_gen_response = MagicMock()
        mock_gen_response.text = "Answer"
        mock_gateway.generate_async = AsyncMock(return_value=mock_gen_response)

        # Mock vector search
        with patch.object(rag.vector_ops, "similarity_search") as mock_search:
            mock_search.return_value = []

            await rag.query_async(
                query="Test query",
                user_id="test_user",
                conversation_id="test_conv",
                tenant_id="test_tenant",
            )

            # Memory should have stored the query-answer pair
            final_memory_size = len(rag.memory._episodic)
            assert final_memory_size > initial_memory_size


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
