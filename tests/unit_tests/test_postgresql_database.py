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
        mock_pool = MagicMock()
        mock_pool.close = AsyncMock()
        mock_conn = AsyncMock()
        
        # Set up async context manager for pool.acquire()
        # acquire() should return a context manager, not be async
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_pool.acquire = MagicMock(return_value=mock_context)
        
        mock_asyncpg_patcher = patch("src.core.postgresql_database.connection.asyncpg")
        mock_asyncpg = mock_asyncpg_patcher.start()
        mock_asyncpg.create_pool = AsyncMock(return_value=mock_pool)
        # Mock PostgresError for exception handling
        mock_asyncpg.PostgresError = Exception

        db = DatabaseConnection(config=db_config)
        yield db, mock_conn, mock_pool
        mock_asyncpg_patcher.stop()

    def test_initialization(self, db_config):
        """Test database initialization."""
        db = DatabaseConnection(config=db_config)
        assert db.config.host == "localhost"
        assert db.config.port == 5432
        assert db.config.database == "test_db"

    @pytest.mark.asyncio
    async def test_connect(self, mock_db):
        """Test database connection."""
        db, _, mock_pool = mock_db
        await db.connect()
        assert db.pool is not None
        assert db.pool == mock_pool

    @pytest.mark.asyncio
    async def test_execute_query(self, mock_db):
        """Test query execution."""
        db, mock_conn, _ = mock_db
        # Set up the pool first
        await db.connect()
        # Create a dict-like object that can be converted with dict()
        class MockRow:
            def __init__(self, data):
                self._data = data
            def __getitem__(self, key):
                return self._data[key]
            def keys(self):
                return self._data.keys()
            def __iter__(self):
                return iter(self._data)
        
        mock_conn.fetchrow = AsyncMock(return_value=MockRow({"id": 1, "name": "test"}))

        result = await db.execute_query("SELECT * FROM test WHERE id = $1", (1,), fetch_one=True)

        assert result["id"] == 1
        mock_conn.fetchrow.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_query_fetch_all(self, mock_db):
        """Test query execution with fetch_all."""
        db, mock_conn, _ = mock_db
        # Set up the pool first
        await db.connect()
        # Create dict-like objects that can be converted with dict()
        class MockRow:
            def __init__(self, data):
                self._data = data
            def __getitem__(self, key):
                return self._data[key]
            def keys(self):
                return self._data.keys()
            def __iter__(self):
                return iter(self._data)
        
        mock_conn.fetch = AsyncMock(return_value=[
            MockRow({"id": 1, "name": "test1"}),
            MockRow({"id": 2, "name": "test2"})
        ])

        results = await db.execute_query("SELECT * FROM test", fetch_all=True)

        assert len(results) == 2
        assert results[0]["id"] == 1

    @pytest.mark.asyncio
    async def test_disconnect(self, mock_db):
        """Test database disconnection."""
        db, _, mock_pool = mock_db
        # Set up the pool first
        await db.connect()
        await db.close()
        mock_pool.close.assert_called_once()


class TestVectorOperations:
    """Test VectorOperations."""

    @pytest.fixture
    def mock_db(self):
        """Mock database for vector operations."""
        mock_db = MagicMock()
        mock_db.execute_query = AsyncMock()
        mock_db.execute_transaction = AsyncMock()
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
        mock_db.execute_transaction.return_value = None

        vector_ops = VectorOperations(mock_db)
        embeddings_data = [(1, [0.1] * 1536, "model1"), (2, [0.2] * 1536, "model2")]

        await vector_ops.batch_insert_embeddings(embeddings_data)
        mock_db.execute_transaction.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
