"""
Unit Tests for Index DAL

Tests database operations for vector index management.
Follows @cursorrules.md: Success ≥2, Edge ≥2, Failure ≥2
"""


from unittest.mock import AsyncMock, MagicMock

import pytest

from src.faas.shared.dal.index_dal import IndexDAL


class TestIndexDAL:
    """Test IndexDAL class."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database connection."""
        db = MagicMock()
        db.execute_query = AsyncMock()
        return db

    @pytest.fixture
    def index_dal(self, mock_db):
        """Create an IndexDAL instance."""
        return IndexDAL(mock_db)

    # Success Cases (≥2)
    @pytest.mark.asyncio
    async def test_create_index_ivfflat_success(self, index_dal, mock_db):
        """Test successfully creating an IVFFlat index."""
        mock_db.execute_query.return_value = None  # CREATE INDEX returns None

        result = await index_dal.create_index(
            index_name="test_index",
            table_name="embeddings",
            column_name="embedding",
            index_type="ivfflat",
            distance_metric="cosine",
            lists=100,
        )

        assert result is True
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "CREATE INDEX IF NOT EXISTS" in query
        assert "ivfflat" in query.lower()
        assert "vector_cosine_ops" in query

    @pytest.mark.asyncio
    async def test_create_index_hnsw_success(self, index_dal, mock_db):
        """Test successfully creating an HNSW index."""
        mock_db.execute_query.return_value = None

        result = await index_dal.create_index(
            index_name="test_hnsw_index",
            table_name="embeddings",
            column_name="embedding",
            index_type="hnsw",
            distance_metric="l2",
            m=16,
            ef_construction=64,
        )

        assert result is True
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "hnsw" in query.lower()
        assert "vector_l2_ops" in query
        assert "m = 16" in query
        assert "ef_construction = 64" in query

    @pytest.mark.asyncio
    async def test_drop_index_success(self, index_dal, mock_db):
        """Test successfully dropping an index."""
        mock_db.execute_query.return_value = None

        result = await index_dal.drop_index("test_index")

        assert result is True
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "DROP INDEX IF EXISTS" in query

    @pytest.mark.asyncio
    async def test_index_exists_success(self, index_dal, mock_db):
        """Test successfully checking index existence."""
        mock_db.execute_query.return_value = {"1": 1}

        result = await index_dal.index_exists("test_index")

        assert result is True
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "SELECT 1 FROM pg_indexes" in query

    @pytest.mark.asyncio
    async def test_get_table_row_count_success(self, index_dal, mock_db):
        """Test successfully getting table row count."""
        mock_db.execute_query.return_value = {"count": 1000}

        result = await index_dal.get_table_row_count("embeddings", tenant_id="tenant_456")

        assert result == 1000
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "COUNT(*)" in query

    @pytest.mark.asyncio
    async def test_list_indexes_success(self, index_dal, mock_db):
        """Test successfully listing indexes."""
        mock_db.execute_query.return_value = [
            {
                "indexname": "test_index",
                "tablename": "embeddings",
                "indexdef": "CREATE INDEX test_index ON embeddings USING ivfflat",
            },
            {
                "indexname": "test_index2",
                "tablename": "embeddings",
                "indexdef": "CREATE INDEX test_index2 ON embeddings USING hnsw",
            },
        ]

        result = await index_dal.list_indexes()

        assert len(result) == 2
        assert result[0]["indexname"] == "test_index"

    @pytest.mark.asyncio
    async def test_reindex_success(self, index_dal, mock_db):
        """Test successfully reindexing."""
        mock_db.execute_query.return_value = None

        result = await index_dal.reindex("test_index")

        assert result is True
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "REINDEX INDEX" in query

    @pytest.mark.asyncio
    async def test_get_index_info_success(self, index_dal, mock_db):
        """Test successfully getting index information."""
        mock_db.execute_query.return_value = {
            "indexname": "test_index",
            "tablename": "embeddings",
            "indexdef": "CREATE INDEX test_index ON embeddings USING ivfflat",
        }

        result = await index_dal.get_index_info("test_index")

        assert result is not None
        assert result["indexname"] == "test_index"

    # Edge Cases (≥2)
    @pytest.mark.asyncio
    async def test_create_index_with_defaults(self, index_dal, mock_db):
        """Test creating index with default parameters."""
        mock_db.execute_query.return_value = None

        result = await index_dal.create_index(
            index_name="test_index",
            table_name="embeddings",
            column_name="embedding",
            index_type="ivfflat",
        )

        assert result is True
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        # Should use default lists=100
        assert "lists = 100" in query

    @pytest.mark.asyncio
    async def test_get_table_row_count_without_tenant(self, index_dal, mock_db):
        """Test getting row count without tenant filter."""
        mock_db.execute_query.return_value = {"count": 500}

        result = await index_dal.get_table_row_count("embeddings")

        assert result == 500
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "WHERE tenant_id" not in query

    @pytest.mark.asyncio
    async def test_list_indexes_with_table_filter(self, index_dal, mock_db):
        """Test listing indexes filtered by table."""
        mock_db.execute_query.return_value = [
            {
                "indexname": "test_index",
                "tablename": "embeddings",
                "indexdef": "CREATE INDEX test_index",
            }
        ]

        result = await index_dal.list_indexes(table_name="embeddings")

        assert len(result) == 1
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "WHERE tablename = $1" in query

    @pytest.mark.asyncio
    async def test_index_exists_not_found(self, index_dal, mock_db):
        """Test checking existence of non-existent index."""
        mock_db.execute_query.return_value = None

        result = await index_dal.index_exists("non_existent_index")

        assert result is False

    @pytest.mark.asyncio
    async def test_list_indexes_empty(self, index_dal, mock_db):
        """Test listing indexes when none exist."""
        mock_db.execute_query.return_value = None

        result = await index_dal.list_indexes()

        assert result == []

    @pytest.mark.asyncio
    async def test_get_index_info_not_found(self, index_dal, mock_db):
        """Test getting info for non-existent index."""
        mock_db.execute_query.return_value = None

        result = await index_dal.get_index_info("non_existent_index")

        assert result is None

    # Failure Cases (≥2)
    @pytest.mark.asyncio
    async def test_create_index_invalid_table_name(self, index_dal, mock_db):
        """Test creating index with invalid table name."""
        with pytest.raises(ValueError, match="Invalid table name"):
            await index_dal.create_index(
                index_name="test_index",
                table_name="embeddings; DROP TABLE",  # SQL injection attempt
                column_name="embedding",
                index_type="ivfflat",
            )

    @pytest.mark.asyncio
    async def test_create_index_invalid_column_name(self, index_dal, mock_db):
        """Test creating index with invalid column name."""
        with pytest.raises(ValueError, match="Invalid column name"):
            await index_dal.create_index(
                index_name="test_index",
                table_name="embeddings",
                column_name="embedding; DROP TABLE",  # SQL injection attempt
                index_type="ivfflat",
            )

    @pytest.mark.asyncio
    async def test_create_index_invalid_index_name(self, index_dal, mock_db):
        """Test creating index with invalid index name."""
        with pytest.raises(ValueError, match="Invalid index name"):
            await index_dal.create_index(
                index_name="test_index; DROP TABLE",  # SQL injection attempt
                table_name="embeddings",
                column_name="embedding",
                index_type="ivfflat",
            )

    @pytest.mark.asyncio
    async def test_create_index_unsupported_type(self, index_dal, mock_db):
        """Test creating index with unsupported type."""
        with pytest.raises(ValueError, match="Unsupported index type"):
            await index_dal.create_index(
                index_name="test_index",
                table_name="embeddings",
                column_name="embedding",
                index_type="unsupported_type",
            )

    @pytest.mark.asyncio
    async def test_create_index_database_error(self, index_dal, mock_db):
        """Test handling database error during index creation."""
        mock_db.execute_query.side_effect = Exception("Database connection failed")

        result = await index_dal.create_index(
            index_name="test_index",
            table_name="embeddings",
            column_name="embedding",
            index_type="ivfflat",
        )

        assert result is False  # Should return False on error

    @pytest.mark.asyncio
    async def test_drop_index_database_error(self, index_dal, mock_db):
        """Test handling database error during index drop."""
        mock_db.execute_query.side_effect = Exception("Drop operation failed")

        result = await index_dal.drop_index("test_index")

        assert result is False  # Should return False on error

    @pytest.mark.asyncio
    async def test_reindex_database_error(self, index_dal, mock_db):
        """Test handling database error during reindex."""
        mock_db.execute_query.side_effect = Exception("Reindex operation failed")

        result = await index_dal.reindex("test_index")

        assert result is False  # Should return False on error

    @pytest.mark.asyncio
    async def test_get_table_row_count_invalid_table(self, index_dal, mock_db):
        """Test getting row count with invalid table name."""
        with pytest.raises(ValueError, match="Invalid table name"):
            await index_dal.get_table_row_count("embeddings; DROP TABLE")

    @pytest.mark.asyncio
    async def test_drop_index_invalid_name(self, index_dal, mock_db):
        """Test dropping index with invalid name."""
        with pytest.raises(ValueError, match="Invalid index name"):
            await index_dal.drop_index("test_index; DROP TABLE")

    @pytest.mark.asyncio
    async def test_reindex_invalid_name(self, index_dal, mock_db):
        """Test reindexing with invalid index name."""
        with pytest.raises(ValueError, match="Invalid index name"):
            await index_dal.reindex("test_index; DROP TABLE")

