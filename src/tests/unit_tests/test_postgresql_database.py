"""
Unit Tests for PostgreSQL Database Component

Tests database operations and vector functionality.
"""

from unittest.mock import MagicMock, patch

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
        with patch("src.core.postgresql_database.connection.psycopg2.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn

            db = DatabaseConnection(config=db_config)
            db.connection_pool = mock_conn
            return db, mock_conn, mock_cursor

    def test_initialization(self, db_config):
        """Test database initialization."""
        db = DatabaseConnection(config=db_config)
        assert db.config.host == "localhost"
        assert db.config.port == 5432
        assert db.config.database == "test_db"

    def test_connect(self, mock_db):
        """Test database connection."""
        db, _, _ = mock_db
        db.connect()
        assert db.connection_pool is not None

    def test_execute_query(self, mock_db):
        """Test query execution."""
        db, _, mock_cursor = mock_db
        mock_cursor.fetchone.return_value = {"id": 1, "name": "test"}

        result = db.execute_query("SELECT * FROM test WHERE id = %s", (1,), fetch_one=True)

        assert result["id"] == 1
        mock_cursor.execute.assert_called_once()

    def test_execute_query_fetch_all(self, mock_db):
        """Test query execution with fetch_all."""
        db, _, mock_cursor = mock_db
        mock_cursor.fetchall.return_value = [{"id": 1, "name": "test1"}, {"id": 2, "name": "test2"}]

        results = db.execute_query("SELECT * FROM test", fetch_all=True)

        assert len(results) == 2
        assert results[0]["id"] == 1

    def test_disconnect(self, mock_db):
        """Test database disconnection."""
        db, mock_conn, _ = mock_db
        db.disconnect()
        mock_conn.close.assert_called_once()


class TestVectorOperations:
    """Test VectorOperations."""

    @pytest.fixture
    def mock_db(self):
        """Mock database for vector operations."""
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_db.cursor.return_value = mock_cursor
        return mock_db, mock_cursor

    def test_insert_embedding(self, mock_db):
        """Test embedding insertion."""
        mock_db_obj, mock_cursor = mock_db
        mock_cursor.fetchone.return_value = (1,)

        vector_ops = VectorOperations(mock_db_obj)
        embedding = [0.1] * 1536

        embedding_id = vector_ops.insert_embedding(
            document_id=1, embedding=embedding, model="text-embedding-3-small"
        )

        assert embedding_id == 1
        mock_cursor.execute.assert_called()

    def test_similarity_search(self, mock_db):
        """Test similarity search."""
        mock_db_obj, mock_cursor = mock_db
        mock_cursor.fetchall.return_value = [
            {"id": 1, "document_id": 1, "similarity": 0.95, "content": "test"}
        ]

        vector_ops = VectorOperations(mock_db_obj)
        query_embedding = [0.1] * 1536

        results = vector_ops.similarity_search(
            query_embedding=query_embedding, limit=5, threshold=0.7
        )

        assert len(results) == 1
        assert abs(results[0]["similarity"] - 0.95) < 0.001

    def test_batch_insert_embeddings(self, mock_db):
        """Test batch embedding insertion."""
        mock_db_obj, mock_cursor = mock_db

        vector_ops = VectorOperations(mock_db_obj)
        embeddings_data = [(1, [0.1] * 1536, "model1"), (2, [0.2] * 1536, "model2")]

        vector_ops.batch_insert_embeddings(embeddings_data)
        mock_cursor.executemany.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
