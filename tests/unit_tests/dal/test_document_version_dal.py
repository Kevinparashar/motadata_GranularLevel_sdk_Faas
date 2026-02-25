"""
Unit Tests for Document Version DAL

Tests database operations for document version persistence.
Follows @cursorrules.md: Success ≥2, Edge ≥2, Failure ≥2
"""


import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.faas.shared.dal.document_version_dal import DocumentVersionDAL


class TestDocumentVersionDAL:
    """Test DocumentVersionDAL class."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database connection."""
        db = MagicMock()
        db.execute_query = AsyncMock()
        return db

    @pytest.fixture
    def document_version_dal(self, mock_db):
        """Create a DocumentVersionDAL instance."""
        return DocumentVersionDAL(mock_db)

    # Success Cases (≥2)
    @pytest.mark.asyncio
    async def test_create_version_success(self, document_version_dal, mock_db):
        """Test successfully creating a document version."""
        # Mock max version query
        mock_db.execute_query.side_effect = [
            {"max_version": 2},  # Current max version
            {"id": "version_record_123", "created_at": datetime.now()},  # Insert result
        ]

        result = await document_version_dal.create_version(
            document_id="doc_123",
            content="Test content",
            tenant_id="tenant_456",
            metadata={"key": "value"},
        )

        assert result["version"] == 3  # Next version
        assert result["document_id"] == "doc_123"
        assert "content_hash" in result
        assert len(mock_db.execute_query.call_args_list) == 2

    @pytest.mark.asyncio
    async def test_get_versions_success(self, document_version_dal, mock_db):
        """Test successfully getting all versions."""
        mock_db.execute_query.return_value = [
            {
                "version": 1,
                "content_hash": "hash1",
                "created_at": datetime.now(),
                "metadata": json.dumps({"key": "value"}),
            },
            {
                "version": 2,
                "content_hash": "hash2",
                "created_at": datetime.now(),
                "metadata": json.dumps({"key2": "value2"}),
            },
        ]

        result = await document_version_dal.get_versions("doc_123", "tenant_456")

        assert len(result) == 2
        assert result[0]["version"] == 1
        assert isinstance(result[0]["metadata"], dict)

    @pytest.mark.asyncio
    async def test_get_version_success(self, document_version_dal, mock_db):
        """Test successfully getting a specific version."""
        mock_db.execute_query.return_value = {
            "version": 2,
            "content_hash": "hash2",
            "content": "Test content",
            "created_at": datetime.now(),
            "metadata": json.dumps({"key": "value"}),
        }

        result = await document_version_dal.get_version("doc_123", 2, "tenant_456")

        assert result is not None
        assert result["version"] == 2
        assert isinstance(result["metadata"], dict)

    @pytest.mark.asyncio
    async def test_get_latest_version_success(self, document_version_dal, mock_db):
        """Test successfully getting the latest version."""
        mock_db.execute_query.return_value = {
            "version": 5,
            "content_hash": "hash5",
            "content": "Latest content",
            "created_at": datetime.now(),
            "metadata": json.dumps({"key": "value"}),
        }

        result = await document_version_dal.get_latest_version("doc_123", "tenant_456")

        assert result is not None
        assert result["version"] == 5
        call_args = mock_db.execute_query.call_args
        assert "ORDER BY version DESC" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_delete_version_success(self, document_version_dal, mock_db):
        """Test successfully deleting a version."""
        mock_db.execute_query.return_value = 1  # 1 row deleted

        result = await document_version_dal.delete_version("doc_123", 2, "tenant_456")

        assert result is True
        mock_db.execute_query.assert_called_once()

    # Edge Cases (≥2)
    @pytest.mark.asyncio
    async def test_create_version_first_version(self, document_version_dal, mock_db):
        """Test creating first version (no existing versions)."""
        mock_db.execute_query.side_effect = [
            {"max_version": None},  # No existing versions
            {"id": "version_record_123", "created_at": datetime.now()},
        ]

        result = await document_version_dal.create_version(
            document_id="doc_123",
            content="Test content",
            tenant_id="tenant_456",
        )

        assert result["version"] == 1  # First version

    @pytest.mark.asyncio
    async def test_get_versions_with_string_metadata(self, document_version_dal, mock_db):
        """Test getting versions with string JSON metadata."""
        mock_db.execute_query.return_value = [
            {
                "version": 1,
                "content_hash": "hash1",
                "created_at": datetime.now(),
                "metadata": '{"key": "value"}',  # String JSON
            },
        ]

        result = await document_version_dal.get_versions("doc_123", "tenant_456")

        assert len(result) == 1
        assert isinstance(result[0]["metadata"], dict)

    @pytest.mark.asyncio
    async def test_get_versions_empty_result(self, document_version_dal, mock_db):
        """Test getting versions with empty result."""
        mock_db.execute_query.return_value = None

        result = await document_version_dal.get_versions("doc_123", "tenant_456")

        assert result == []

    @pytest.mark.asyncio
    async def test_create_version_without_tenant(self, document_version_dal, mock_db):
        """Test creating version without tenant_id."""
        mock_db.execute_query.side_effect = [
            {"max_version": 1},
            {"id": "version_record_123", "created_at": datetime.now()},
        ]

        result = await document_version_dal.create_version(
            document_id="doc_123",
            content="Test content",
        )

        assert result["version"] == 2
        # Check that tenant_id is handled correctly
        insert_call = mock_db.execute_query.call_args_list[1]
        assert "tenant_id" in insert_call[0][0] or "NULL" in insert_call[0][0]

    @pytest.mark.asyncio
    async def test_delete_version_not_found(self, document_version_dal, mock_db):
        """Test deleting non-existent version."""
        mock_db.execute_query.return_value = 0  # 0 rows deleted

        result = await document_version_dal.delete_version("doc_123", 999, "tenant_456")

        assert result is False

    # Failure Cases (≥2)
    @pytest.mark.asyncio
    async def test_get_version_not_found(self, document_version_dal, mock_db):
        """Test getting non-existent version."""
        mock_db.execute_query.return_value = None

        result = await document_version_dal.get_version("doc_123", 999, "tenant_456")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_latest_version_not_found(self, document_version_dal, mock_db):
        """Test getting latest version when none exist."""
        mock_db.execute_query.return_value = None

        result = await document_version_dal.get_latest_version("doc_123", "tenant_456")

        assert result is None

    @pytest.mark.asyncio
    async def test_create_version_database_error(self, document_version_dal, mock_db):
        """Test creating version with database error."""
        mock_db.execute_query.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            await document_version_dal.create_version(
                document_id="doc_123",
                content="Test content",
                tenant_id="tenant_456",
            )

