"""
Unit Tests for Document DAL

Tests database operations for document persistence.
Follows @cursorrules.md: Success ≥2, Edge ≥2, Failure ≥2
"""


import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.faas.shared.dal.document_dal import DocumentDAL


class TestDocumentDAL:
    """Test DocumentDAL class."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database connection."""
        db = MagicMock()
        db.execute_query = AsyncMock()
        return db

    @pytest.fixture
    def document_dal(self, mock_db):
        """Create a DocumentDAL instance."""
        return DocumentDAL(mock_db)

    # Success Cases (≥2)
    @pytest.mark.asyncio
    async def test_save_document_success(self, document_dal, mock_db):
        """Test successfully saving a document."""
        mock_db.execute_query.return_value = {"id": "doc_123"}

        result = await document_dal.save_document(
            title="Test Document",
            content="Test content",
            source="test_source",
            metadata={"key": "value"},
            tenant_id="tenant_456",
        )

        assert result == "doc_123"
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        assert "INSERT INTO documents" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_load_document_success(self, document_dal, mock_db):
        """Test successfully loading a document."""
        mock_db.execute_query.return_value = {
            "id": "doc_123",
            "title": "Test Document",
            "content": "Test content",
            "source": "test_source",
            "metadata": json.dumps({"key": "value"}),
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        result = await document_dal.load_document("doc_123", "tenant_456")

        assert result is not None
        assert result["id"] == "doc_123"
        assert result["title"] == "Test Document"
        assert isinstance(result["metadata"], dict)

    @pytest.mark.asyncio
    async def test_list_documents_success(self, document_dal, mock_db):
        """Test successfully listing documents."""
        mock_db.execute_query.return_value = [
            {"id": "doc_1", "title": "Doc 1"},
            {"id": "doc_2", "title": "Doc 2"},
        ]

        result = await document_dal.list_documents("tenant_456", limit=10, offset=0)

        assert len(result) == 2
        assert result[0]["id"] == "doc_1"

    @pytest.mark.asyncio
    async def test_update_document_success(self, document_dal, mock_db):
        """Test successfully updating a document."""
        mock_db.execute_query.return_value = 1  # 1 row updated

        result = await document_dal.update_document(
            "doc_123",
            title="Updated Title",
            content="Updated content",
            metadata={"new": "data"},
            tenant_id="tenant_456",
        )

        assert result is True
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_document_success(self, document_dal, mock_db):
        """Test successfully deleting a document."""
        mock_db.execute_query.return_value = 1  # 1 row deleted

        result = await document_dal.delete_document("doc_123", "tenant_456")

        assert result is True
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_document_exists_success(self, document_dal, mock_db):
        """Test successfully checking document existence."""
        mock_db.execute_query.return_value = {"1": 1}

        result = await document_dal.document_exists("doc_123", "tenant_456")

        assert result is True

    # Edge Cases (≥2)
    @pytest.mark.asyncio
    async def test_save_document_without_tenant(self, document_dal, mock_db):
        """Test saving document without tenant_id."""
        mock_db.execute_query.return_value = {"id": "doc_123"}

        result = await document_dal.save_document(
            title="Test Document",
            content="Test content",
        )

        assert result == "doc_123"
        call_args = mock_db.execute_query.call_args
        assert call_args[1]["params"][-1] is None  # tenant_id is None

    @pytest.mark.asyncio
    async def test_load_document_with_string_metadata(self, document_dal, mock_db):
        """Test loading document with string JSON metadata."""
        mock_db.execute_query.return_value = {
            "id": "doc_123",
            "title": "Test Document",
            "content": "Test content",
            "source": "test_source",
            "metadata": '{"key": "value"}',  # String JSON
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        result = await document_dal.load_document("doc_123", "tenant_456")

        assert result is not None
        assert isinstance(result["metadata"], dict)

    @pytest.mark.asyncio
    async def test_list_documents_empty_result(self, document_dal, mock_db):
        """Test listing documents with empty result."""
        mock_db.execute_query.return_value = None

        result = await document_dal.list_documents("tenant_456")

        assert result == []

    @pytest.mark.asyncio
    async def test_update_document_no_changes(self, document_dal, mock_db):
        """Test updating document with no changes."""
        result = await document_dal.update_document("doc_123")

        assert result is False
        mock_db.execute_query.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_document_not_found(self, document_dal, mock_db):
        """Test deleting non-existent document."""
        mock_db.execute_query.return_value = 0  # 0 rows deleted

        result = await document_dal.delete_document("nonexistent", "tenant_456")

        assert result is False

    @pytest.mark.asyncio
    async def test_document_exists_not_found(self, document_dal, mock_db):
        """Test checking existence of non-existent document."""
        mock_db.execute_query.return_value = None

        result = await document_dal.document_exists("nonexistent", "tenant_456")

        assert result is False

    # Failure Cases (≥2)
    @pytest.mark.asyncio
    async def test_load_document_not_found(self, document_dal, mock_db):
        """Test loading non-existent document."""
        mock_db.execute_query.return_value = None

        result = await document_dal.load_document("nonexistent", "tenant_456")

        assert result is None

    @pytest.mark.asyncio
    async def test_save_document_database_error(self, document_dal, mock_db):
        """Test saving document with database error."""
        mock_db.execute_query.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            await document_dal.save_document(
                title="Test Document",
                content="Test content",
            )

