"""
Unit Tests for Embedding DAL

Tests database operations for vector embedding persistence.
Follows @cursorrules.md: Success ≥2, Edge ≥2, Failure ≥2
"""


import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.faas.shared.dal.embedding_dal import EmbeddingDAL


class TestEmbeddingDAL:
    """Test EmbeddingDAL class."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database connection."""
        db = MagicMock()
        db.execute_query = AsyncMock()
        db.execute_transaction = AsyncMock()
        return db

    @pytest.fixture
    def embedding_dal(self, mock_db):
        """Create an EmbeddingDAL instance."""
        return EmbeddingDAL(mock_db)

    @pytest.fixture
    def sample_embedding(self):
        """Create a sample embedding vector."""
        return [0.1, 0.2, 0.3, 0.4, 0.5]

    # Success Cases (≥2)
    @pytest.mark.asyncio
    async def test_insert_embedding_success(self, embedding_dal, mock_db, sample_embedding):
        """Test successfully inserting an embedding."""
        mock_db.execute_query.return_value = {"id": 123}

        result = await embedding_dal.insert_embedding(
            document_id=1,
            embedding=sample_embedding,
            model="text-embedding-3-small",
            tenant_id="tenant_456",
        )

        assert result == 123
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        assert "INSERT INTO embeddings" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_similarity_search_success(self, embedding_dal, mock_db, sample_embedding):
        """Test successfully performing similarity search."""
        mock_db.execute_query.return_value = [
            {
                "id": 1,
                "document_id": 10,
                "title": "Test Doc",
                "content": "Test content",
                "metadata": json.dumps({"key": "value"}),
                "source": "test_source",
                "similarity": 0.95,
            }
        ]

        result = await embedding_dal.similarity_search(
            query_embedding=sample_embedding,
            limit=10,
            threshold=0.7,
            model="text-embedding-3-small",
            tenant_id="tenant_456",
        )

        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["similarity"] == 0.95
        assert isinstance(result[0]["metadata"], dict)  # Should be parsed from JSON

    @pytest.mark.asyncio
    async def test_batch_insert_embeddings_success(
        self, embedding_dal, mock_db, sample_embedding
    ):
        """Test successfully batch inserting embeddings."""
        embeddings_data = [
            (1, sample_embedding, "model1"),
            (2, sample_embedding, "model2"),
        ]

        await embedding_dal.batch_insert_embeddings(
            embeddings_data=embeddings_data, tenant_id="tenant_456"
        )

        mock_db.execute_transaction.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_embedding_success(self, embedding_dal, mock_db):
        """Test successfully getting an embedding."""
        mock_db.execute_query.return_value = {
            "id": 123,
            "document_id": 10,
            "embedding": "[0.1,0.2,0.3]",
            "model": "text-embedding-3-small",
            "tenant_id": "tenant_456",
        }

        result = await embedding_dal.get_embedding(embedding_id=123, tenant_id="tenant_456")

        assert result is not None
        assert result["id"] == 123
        assert result["document_id"] == 10

    @pytest.mark.asyncio
    async def test_delete_embeddings_success(self, embedding_dal, mock_db):
        """Test successfully deleting embeddings."""
        mock_db.execute_query.return_value = 5  # 5 embeddings deleted

        result = await embedding_dal.delete_embeddings(
            document_id=10, tenant_id="tenant_456"
        )

        assert result == 5
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_embedding_success(self, embedding_dal, mock_db, sample_embedding):
        """Test successfully updating an embedding."""
        mock_db.execute_query.return_value = 1  # 1 row updated

        result = await embedding_dal.update_embedding(
            embedding_id=123, new_embedding=sample_embedding, tenant_id="tenant_456"
        )

        assert result is True
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_embeddings_by_document_success(self, embedding_dal, mock_db):
        """Test successfully getting embeddings by document."""
        mock_db.execute_query.return_value = [
            {"id": 1, "document_id": 10, "embedding": "[0.1,0.2]", "model": "model1"},
            {"id": 2, "document_id": 10, "embedding": "[0.3,0.4]", "model": "model2"},
        ]

        result = await embedding_dal.get_embeddings_by_document(
            document_id=10, tenant_id="tenant_456"
        )

        assert len(result) == 2
        assert all(r["document_id"] == 10 for r in result)

    @pytest.mark.asyncio
    async def test_embedding_exists_success(self, embedding_dal, mock_db):
        """Test successfully checking embedding existence."""
        mock_db.execute_query.return_value = {"1": 1}

        result = await embedding_dal.embedding_exists(embedding_id=123, tenant_id="tenant_456")

        assert result is True

    # Edge Cases (≥2)
    @pytest.mark.asyncio
    async def test_insert_embedding_without_tenant(self, embedding_dal, mock_db, sample_embedding):
        """Test inserting embedding without tenant_id."""
        mock_db.execute_query.return_value = {"id": 123}

        result = await embedding_dal.insert_embedding(
            document_id=1, embedding=sample_embedding, model="text-embedding-3-small"
        )

        assert result == 123
        call_args = mock_db.execute_query.call_args
        # tenant_id should not be in params
        params = call_args[1]["params"]
        assert len(params) == 3  # document_id, embedding, model

    @pytest.mark.asyncio
    async def test_similarity_search_without_filters(self, embedding_dal, mock_db, sample_embedding):
        """Test similarity search without model or tenant filters."""
        mock_db.execute_query.return_value = []

        result = await embedding_dal.similarity_search(
            query_embedding=sample_embedding, limit=10, threshold=0.7
        )

        assert result == []
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        # Should not have model or tenant_id filters
        assert "WHERE 1 - (e.embedding <=> $1::vector) >= $2" in query

    @pytest.mark.asyncio
    async def test_similarity_search_with_string_metadata(self, embedding_dal, mock_db, sample_embedding):
        """Test similarity search with string JSON metadata."""
        mock_db.execute_query.return_value = [
            {
                "id": 1,
                "document_id": 10,
                "title": "Test Doc",
                "content": "Test content",
                "metadata": '{"key": "value"}',  # String JSON
                "source": "test_source",
                "similarity": 0.95,
            }
        ]

        result = await embedding_dal.similarity_search(
            query_embedding=sample_embedding, limit=10
        )

        assert len(result) == 1
        assert isinstance(result[0]["metadata"], dict)  # Should be parsed

    @pytest.mark.asyncio
    async def test_get_embedding_not_found(self, embedding_dal, mock_db):
        """Test getting embedding that doesn't exist."""
        mock_db.execute_query.return_value = None

        result = await embedding_dal.get_embedding(embedding_id=999, tenant_id="tenant_456")

        assert result is None

    @pytest.mark.asyncio
    async def test_batch_insert_empty_list(self, embedding_dal, mock_db):
        """Test batch insert with empty list."""
        await embedding_dal.batch_insert_embeddings(embeddings_data=[], tenant_id="tenant_456")

        # Should not call execute_transaction for empty list
        mock_db.execute_transaction.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_embeddings_by_document_empty(self, embedding_dal, mock_db):
        """Test getting embeddings for document with none."""
        mock_db.execute_query.return_value = None

        result = await embedding_dal.get_embeddings_by_document(
            document_id=999, tenant_id="tenant_456"
        )

        assert result == []

    # Failure Cases (≥2)
    @pytest.mark.asyncio
    async def test_insert_embedding_database_error(self, embedding_dal, mock_db, sample_embedding):
        """Test handling database error during insert."""
        mock_db.execute_query.side_effect = Exception("Database connection failed")

        with pytest.raises(Exception, match="Database connection failed"):
            await embedding_dal.insert_embedding(
                document_id=1, embedding=sample_embedding, model="text-embedding-3-small"
            )

    @pytest.mark.asyncio
    async def test_similarity_search_database_error(self, embedding_dal, mock_db, sample_embedding):
        """Test handling database error during similarity search."""
        mock_db.execute_query.side_effect = Exception("Query execution failed")

        with pytest.raises(Exception, match="Query execution failed"):
            await embedding_dal.similarity_search(query_embedding=sample_embedding)

    @pytest.mark.asyncio
    async def test_delete_embeddings_database_error(self, embedding_dal, mock_db):
        """Test handling database error during delete."""
        mock_db.execute_query.side_effect = Exception("Delete operation failed")

        with pytest.raises(Exception, match="Delete operation failed"):
            await embedding_dal.delete_embeddings(document_id=10, tenant_id="tenant_456")

    @pytest.mark.asyncio
    async def test_update_embedding_not_found(self, embedding_dal, mock_db, sample_embedding):
        """Test updating embedding that doesn't exist."""
        mock_db.execute_query.return_value = 0  # 0 rows updated

        result = await embedding_dal.update_embedding(
            embedding_id=999, new_embedding=sample_embedding, tenant_id="tenant_456"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_embedding_exists_not_found(self, embedding_dal, mock_db):
        """Test checking existence of non-existent embedding."""
        mock_db.execute_query.return_value = None

        result = await embedding_dal.embedding_exists(embedding_id=999, tenant_id="tenant_456")

        assert result is False

