"""
Unit Tests for PostgreSQL Database Component

Tests database operations and vector functionality.
"""


from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.postgresql_database import DatabaseConnection
from src.core.postgresql_database.vector_operations import VectorOperations


class TestDatabaseConnection:
    """Test DatabaseConnection."""

    @pytest.fixture
    def db_config(self):
        """Database configuration fixture."""
        from src.core.postgresql_database import DatabaseConfig
        return DatabaseConfig(
            host="localhost",
            port=5432,
            database="test_db",
            user="test_user",
            password="test_password",
        )

    @pytest.fixture
    def mock_db(self, db_config):
        """Mock database connection."""
        with patch("src.core.postgresql_database.connection.asyncpg") as mock_asyncpg:
            mock_pool = AsyncMock()
            mock_conn = AsyncMock()
            mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
            mock_pool.acquire.return_value.__aexit__.return_value = None
            mock_asyncpg.create_pool.return_value = mock_pool

            db = DatabaseConnection(config=db_config)
            return db, mock_conn, mock_pool

    def test_initialization(self, db_config):
        """Test database initialization."""
        db = DatabaseConnection(config=db_config)
        assert db.config.host == "localhost"
        assert db.config.port == 5432
        assert db.config.database == "test_db"

    @pytest.mark.asyncio
    async def test_connect(self, mock_db):
        """Test database connection."""
        db, _, _ = mock_db
        await db.connect()
        assert db._connection is not None

    @pytest.mark.asyncio
    async def test_execute_query(self, mock_db):
        """Test query execution."""
        db, mock_conn, _ = mock_db
        mock_conn.fetchrow.return_value = {"id": 1, "name": "test"}

        result = await db.execute_query("SELECT * FROM test WHERE id = $1", (1,), fetch_one=True)

        assert result["id"] == 1
        mock_conn.fetchrow.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_query_fetch_all(self, mock_db):
        """Test query execution with fetch_all."""
        db, mock_conn, _ = mock_db
        mock_conn.fetch.return_value = [{"id": 1, "name": "test1"}, {"id": 2, "name": "test2"}]

        results = await db.execute_query("SELECT * FROM test", fetch_all=True)

        assert len(results) == 2
        assert results[0]["id"] == 1

    @pytest.mark.asyncio
    async def test_disconnect(self, mock_db):
        """Test database disconnection."""
        db, _, mock_pool = mock_db
        await db.close()
        mock_pool.close.assert_called_once()


class TestVectorOperations:
    """Test VectorOperations."""

    @pytest.fixture
    def mock_db(self):
        """Mock database for vector operations."""
        mock_db = MagicMock()
        mock_db.execute_query = AsyncMock()
        return mock_db

    @pytest.mark.asyncio
    async def test_insert_embedding(self, mock_db):
        """Test embedding insertion."""
        mock_db.execute_query.return_value = {"id": 1}

        vector_ops = VectorOperations(mock_db)
        embedding = [0.1] * 1536

        embedding_id = await vector_ops.insert_embedding(
            document_id=1, embedding=embedding, model="text-embedding-3-small"
        )

        assert embedding_id == 1
        mock_db.execute_query.assert_called()

    @pytest.mark.asyncio
    async def test_similarity_search(self, mock_db):
        """Test similarity search."""
        mock_db.execute_query.return_value = [
            {"id": 1, "document_id": 1, "similarity": 0.95, "content": "test"}
        ]

        vector_ops = VectorOperations(mock_db)
        query_embedding = [0.1] * 1536

        results = await vector_ops.similarity_search(
            query_embedding=query_embedding, limit=5, threshold=0.7
        )

        assert len(results) == 1
        assert abs(results[0]["similarity"] - 0.95) < 0.001

    @pytest.mark.asyncio
    async def test_batch_insert_embeddings(self, mock_db):
        """Test batch embedding insertion."""
        mock_db.execute_query.return_value = None

        vector_ops = VectorOperations(mock_db)
        embeddings_data = [(1, [0.1] * 1536, "model1"), (2, [0.2] * 1536, "model2")]

        await vector_ops.batch_insert_embeddings(embeddings_data)
        mock_db.execute_query.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
