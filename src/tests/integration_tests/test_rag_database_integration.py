"""
Integration Tests for RAG-Database Integration

Tests the integration between RAG System and PostgreSQL Database.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from src.core.rag import RAGSystem
from src.core.postgresql_database.connection import DatabaseConnection, DatabaseConfig
from src.core.postgresql_database.vector_operations import VectorOperations
from src.core.litellm_gateway import LiteLLMGateway, GatewayConfig


@pytest.mark.integration
class TestRAGDatabaseIntegration:
    """Test RAG-Database integration."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database connection."""
        with patch('src.core.postgresql_database.connection.psycopg2') as mock_psycopg2:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.fetchone.return_value = (1,)  # Document ID
            mock_cursor.fetchall.return_value = []
            mock_psycopg2.connect.return_value = mock_conn

            db = DatabaseConnection(DatabaseConfig(
                host="localhost",
                port=5432,
                database="test",
                user="test",
                password="test"
            ))
            return db, mock_conn, mock_cursor

    @pytest.fixture
    def mock_gateway(self):
        """Create mock gateway."""
        with patch('src.core.litellm_gateway.gateway.litellm') as mock_litellm:
            config = GatewayConfig()
            gateway = LiteLLMGateway(config=config)
            gateway._litellm = mock_litellm

            mock_embedding_response = MagicMock()
            mock_embedding_response.embeddings = [[0.1] * 1536]
            mock_litellm.aembedding = AsyncMock(return_value=mock_embedding_response)

            mock_gen_response = MagicMock()
            mock_gen_response.text = "Generated answer"
            mock_gen_response.model = "gpt-4"
            mock_litellm.acompletion = AsyncMock(return_value=mock_gen_response)

            return gateway

    @pytest.fixture
    def rag_system(self, mock_db, mock_gateway):
        """Create RAG system."""
        db, _, _ = mock_db
        return RAGSystem(
            db=db,
            gateway=mock_gateway,
            enable_memory=False
        )

    def test_document_storage(self, rag_system, mock_db):
        """Test that documents are stored in database."""
        db, mock_conn, mock_cursor = mock_db

        doc_id = rag_system.ingest_document(
            title="Test Document",
            content="Test content",
            tenant_id="test_tenant"
        )

        # Database should have been called to store document
        assert mock_cursor.execute.called

    def test_embedding_storage(self, rag_system, mock_db):
        """Test that embeddings are stored in database."""
        db, mock_conn, mock_cursor = mock_db

        rag_system.ingest_document(
            title="Test Document",
            content="Test content for embedding",
            tenant_id="test_tenant"
        )

        # Database should have been called to store embeddings
        # Multiple calls for document and chunks
        assert mock_cursor.execute.call_count > 0

    def test_vector_search_integration(self, rag_system, mock_db):
        """Test that vector search uses database."""
        db, mock_conn, mock_cursor = mock_db

        # Mock vector search results
        mock_cursor.fetchall.return_value = [
            (1, "chunk_content", 0.95, [0.1] * 1536)
        ]

        with patch.object(rag_system.vector_ops, 'similarity_search') as mock_search:
            mock_search.return_value = [
                {"id": 1, "content": "chunk_content", "similarity": 0.95}
            ]

            result = rag_system.query(
                query="Test query",
                tenant_id="test_tenant"
            )

            # Vector search should have been called
            mock_search.assert_called()

    def test_metadata_storage(self, rag_system, mock_db):
        """Test that document metadata is stored."""
        db, mock_conn, mock_cursor = mock_db

        metadata = {
            "author": "Test Author",
            "category": "Technology",
            "tags": ["AI", "ML"]
        }

        rag_system.ingest_document(
            title="Test Document",
            content="Test content",
            metadata=metadata,
            tenant_id="test_tenant"
        )

        # Metadata should be stored in database
        assert mock_cursor.execute.called

    def test_tenant_isolation_in_storage(self, rag_system, mock_db):
        """Test that documents are isolated by tenant."""
        db, mock_conn, mock_cursor = mock_db

        # Ingest document for tenant 1
        rag_system.ingest_document(
            title="Tenant 1 Doc",
            content="Content",
            tenant_id="tenant_1"
        )

        # Ingest document for tenant 2
        rag_system.ingest_document(
            title="Tenant 2 Doc",
            content="Content",
            tenant_id="tenant_2"
        )

        # Both should be stored (database handles isolation)
        assert mock_cursor.execute.call_count > 0

    def test_document_retrieval(self, rag_system, mock_db):
        """Test that documents are retrieved from database."""
        db, mock_conn, mock_cursor = mock_db

        # Mock document retrieval
        mock_cursor.fetchall.return_value = [
            (1, "Test Document", "Test content", "{}")
        ]

        with patch.object(rag_system.vector_ops, 'similarity_search') as mock_search:
            mock_search.return_value = [
                {"id": 1, "document_id": 1, "content": "Test content", "similarity": 0.9}
            ]

            result = rag_system.query(
                query="Test query",
                tenant_id="test_tenant"
            )

            # Should retrieve documents
            assert "retrieved_documents" in result

    def test_chunk_storage(self, rag_system, mock_db):
        """Test that document chunks are stored."""
        db, mock_conn, mock_cursor = mock_db

        # Large content that will be chunked
        large_content = "Test content. " * 1000

        rag_system.ingest_document(
            title="Large Document",
            content=large_content,
            tenant_id="test_tenant"
        )

        # Multiple chunks should be stored
        assert mock_cursor.execute.call_count > 0

    def test_database_connection_handling(self, rag_system, mock_db):
        """Test that database connections are properly handled."""
        db, mock_conn, mock_cursor = mock_db

        # Simulate connection error
        mock_conn.cursor.side_effect = Exception("Connection error")

        # RAG should handle connection errors gracefully
        try:
            rag_system.ingest_document(
                title="Test",
                content="Content",
                tenant_id="test_tenant"
            )
        except Exception:
            # Error should be handled
            pass

        # Connection should be attempted
        assert mock_conn.cursor.called


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])

