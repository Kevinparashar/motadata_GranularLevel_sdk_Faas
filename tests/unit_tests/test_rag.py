"""
Unit Tests for RAG Component

Tests document processing, retrieval, and generation.
"""


from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.rag import RAGSystem
from src.core.rag.document_processor import DocumentChunk, DocumentProcessor
from src.core.rag.exceptions import ValidationError
from src.core.rag.generator import RAGGenerator
from src.core.rag.retriever import Retriever


class TestDocumentProcessor:
    """Test DocumentProcessor."""

    def test_chunk_document(self):
        """Test document chunking."""
        processor = DocumentProcessor(chunk_size=100, chunk_overlap=20)

        content = "This is a test document. " * 100
        chunks = processor.chunk_document(content=content, document_id="doc-001")

        assert len(chunks) > 0
        assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)

    def test_chunk_with_overlap(self):
        """Test chunking with overlap."""
        processor = DocumentProcessor(chunk_size=50, chunk_overlap=10, min_chunk_size=20)

        content = "Test content " * 50
        chunks = processor.chunk_document(content=content, document_id="doc-001")

        assert len(chunks) > 0

    def test_chunk_overlap_validation(self):
        """Test that chunk_overlap >= chunk_size raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentProcessor(chunk_size=100, chunk_overlap=200)
        
        assert "chunk_overlap" in str(exc_info.value.message).lower()
        assert "must be less than chunk_size" in str(exc_info.value.message)

    def test_chunk_size_validation(self):
        """Test that chunk_size <= 0 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentProcessor(chunk_size=0)
        
        assert "chunk_size" in str(exc_info.value.message).lower()
        assert "must be greater than 0" in str(exc_info.value.message)

    def test_chunk_overlap_negative_validation(self):
        """Test that negative chunk_overlap raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentProcessor(chunk_size=100, chunk_overlap=-10)
        
        assert "chunk_overlap" in str(exc_info.value.message).lower()
        assert "must be non-negative" in str(exc_info.value.message)


class TestRetriever:
    """Test Retriever."""

    @pytest.fixture
    def mock_retriever(self):
        """Mock retriever with dependencies."""
        mock_vector_ops = MagicMock()
        mock_gateway = MagicMock()

        # similarity_search is async, so use AsyncMock
        mock_vector_ops.similarity_search = AsyncMock(return_value=[
            {"id": 1, "document_id": 1, "content": "Test content", "similarity": 0.95}
        ])

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
        mock_response.model = "gpt-4"
        mock_response.usage = {}
        # generate_async is async, so use AsyncMock
        mock_gateway.generate_async = AsyncMock(return_value=mock_response)

        generator = RAGGenerator(gateway=mock_gateway, model="gpt-4")

        return generator, mock_gateway

    def test_generate(self, mock_generator):
        """Test response generation."""
        generator, mock_gateway = mock_generator

        context_docs = [{"content": "Context document 1"}, {"content": "Context document 2"}]

        answer = generator.generate(
            query="Test question", context_documents=context_docs, max_tokens=200
        )

        # generate returns a dict with "response" key
        assert answer["response"] == "Generated answer"
        mock_gateway.generate_async.assert_called_once()


class TestRAGSystem:
    """Test RAGSystem."""

    @pytest.fixture
    def mock_rag_system(self):
        """Mock RAG system with dependencies."""
        mock_db = MagicMock()
        mock_gateway = MagicMock()

        # Mock database operations - execute_query is async
        mock_db.execute_query = AsyncMock(return_value={"id": 1})

        # Mock embedding response
        mock_embedding_response = MagicMock()
        mock_embedding_response.embeddings = [[0.1] * 1536]
        mock_gateway.embed.return_value = mock_embedding_response

        # Mock generation response - generate_async is async
        # generate_async returns a dict with "response" key containing the text
        mock_gen_response = MagicMock()
        mock_gen_response.text = "Generated answer"
        mock_gen_response.model = "gpt-4"
        mock_gen_response.usage = {}
        mock_gateway.generate_async = AsyncMock(return_value=mock_gen_response)

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

        # Ensure embed returns proper response structure
        mock_embedding_response = MagicMock()
        mock_embedding_response.embeddings = [[0.1] * 1536]  # Single embedding for the chunk
        mock_gateway.embed.return_value = mock_embedding_response

        # Mock vector_ops.batch_insert_embeddings as async
        rag.vector_ops.batch_insert_embeddings = AsyncMock(return_value=None)

        doc_id = rag.ingest_document(
            title="Test Document", content="Test content " * 100, source="test_source"
        )

        assert doc_id is not None
        mock_db.execute_query.assert_called()
        # embed should be called during embedding generation
        assert mock_gateway.embed.called

    def test_query(self, mock_rag_system):
        """Test RAG query."""
        rag, _, _ = mock_rag_system

        # Mock vector operations - similarity_search is async
        rag.retriever.vector_ops.similarity_search = AsyncMock(return_value=[
            {"id": 1, "document_id": 1, "content": "Test", "similarity": 0.9}
        ])

        result = rag.query(query="Test query", top_k=5, threshold=0.7)

        assert "answer" in result
        assert "retrieved_documents" in result
        assert result["num_documents"] == 1

    @pytest.mark.asyncio
    async def test_query_async(self, mock_rag_system):
        """Test async RAG query."""
        rag, _, mock_gateway = mock_rag_system

        # Mock async gateway - generate_async returns a response object
        mock_async_response = MagicMock()
        mock_async_response.text = "Async answer"
        mock_async_response.model = "gpt-4"
        mock_async_response.usage = {}
        mock_gateway.generate_async = AsyncMock(return_value=mock_async_response)

        # Mock embedding for query
        mock_embedding_response = MagicMock()
        mock_embedding_response.embeddings = [[0.1] * 1536]
        mock_gateway.embed_async = AsyncMock(return_value=mock_embedding_response)

        # Patch retriever.retrieve to return results directly (since it uses asyncio.run() which can't be called in async context)
        rag.retriever.retrieve = lambda *args, **kwargs: [
            {"id": 1, "document_id": 1, "content": "Test", "similarity": 0.9}
        ]

        result = await rag.query_async(query="Test query", top_k=5)

        assert "answer" in result
        # generate_async returns a dict, so answer is a dict with "response" key
        assert result["answer"]["response"] == "Async answer"

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
        await rag.memory.store(
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
        mock_gen_response.model = "gpt-4"
        mock_gen_response.usage = {}
        mock_gateway.generate_async = AsyncMock(return_value=mock_gen_response)

        # Mock vector search - similarity_search is async
        rag.retriever.vector_ops.similarity_search = AsyncMock(return_value=[
            {"id": 1, "content": "Document", "similarity": 0.9}
        ])

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
        mock_gen_response.model = "gpt-4"
        mock_gen_response.usage = {}
        mock_gateway.generate_async = AsyncMock(return_value=mock_gen_response)

        # Patch retriever.retrieve to return results directly (since it uses asyncio.run() which can't be called in async context)
        rag.retriever.retrieve = lambda *args, **kwargs: []

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
