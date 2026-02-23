"""
Unit Tests for PostgreSQL Database Component

Tests database operations and vector functionality.
"""


import asyncio
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

    @pytest.mark.asyncio
    async def test_connect_postgres_error(self, db_config):
        """Test connect with PostgresError."""
        with patch("src.core.postgresql_database.connection.asyncpg") as mock_asyncpg:
            mock_asyncpg.create_pool = AsyncMock(side_effect=Exception("Postgres error"))
            mock_asyncpg.PostgresError = Exception
            
            db = DatabaseConnection(config=db_config)
            with pytest.raises(ConnectionError, match="Failed to create connection pool"):
                await db.connect()

    @pytest.mark.asyncio
    async def test_close_no_pool(self, db_config):
        """Test close when pool is None."""
        db = DatabaseConnection(config=db_config)
        # Should not raise error
        await db.close()
        assert db.pool is None

    @pytest.mark.asyncio
    async def test_get_connection(self, mock_db):
        """Test get_connection context manager."""
        db, mock_conn, _ = mock_db
        await db.connect()
        
        async with db.get_connection() as conn:
            assert conn == mock_conn

    @pytest.mark.asyncio
    async def test_get_connection_auto_connect(self, mock_db):
        """Test get_connection auto-connects if pool is None."""
        db, mock_conn, _ = mock_db
        db.pool = None  # Ensure pool is None
        
        async with db.get_connection() as conn:
            assert conn == mock_conn

    def test_convert_placeholders(self, db_config):
        """Test placeholder conversion."""
        db = DatabaseConnection(config=db_config)
        
        # Test with %s placeholders
        query = "SELECT * FROM test WHERE id = %s AND name = %s"
        result = db._convert_placeholders(query, 2)
        assert result == "SELECT * FROM test WHERE id = $1 AND name = $2"
        
        # Test with no placeholders
        query2 = "SELECT * FROM test"
        result2 = db._convert_placeholders(query2, 0)
        assert result2 == query2
        
        # Test with $1 format (already converted)
        query3 = "SELECT * FROM test WHERE id = $1"
        result3 = db._convert_placeholders(query3, 1)
        assert result3 == query3

    @pytest.mark.asyncio
    async def test_execute_query_no_fetch(self, mock_db):
        """Test execute_query with fetch_all=False."""
        db, mock_conn, _ = mock_db
        await db.connect()
        
        mock_conn.execute = AsyncMock(return_value="INSERT 0 5")
        
        result = await db.execute_query("INSERT INTO test VALUES ($1)", (1,), fetch_all=False)
        
        assert result == 5
        mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_query_no_fetch_empty_result(self, mock_db):
        """Test execute_query with fetch_all=False and empty result."""
        db, mock_conn, _ = mock_db
        await db.connect()
        
        mock_conn.execute = AsyncMock(return_value="")
        
        result = await db.execute_query("INSERT INTO test VALUES ($1)", (1,), fetch_all=False)
        
        assert result == 0

    @pytest.mark.asyncio
    async def test_execute_query_fetch_one_none(self, mock_db):
        """Test execute_query with fetch_one=True and None result."""
        db, mock_conn, _ = mock_db
        await db.connect()
        
        mock_conn.fetchrow = AsyncMock(return_value=None)
        
        result = await db.execute_query("SELECT * FROM test WHERE id = $1", (999,), fetch_one=True)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_execute_query_with_placeholder_conversion(self, mock_db):
        """Test execute_query with %s placeholder conversion."""
        db, mock_conn, _ = mock_db
        await db.connect()
        
        class MockRow:
            def __init__(self, data):
                self._data = data
            def __getitem__(self, key):
                return self._data[key]
            def keys(self):
                return self._data.keys()
            def __iter__(self):
                return iter(self._data)
        
        mock_conn.fetchrow = AsyncMock(return_value=MockRow({"id": 1}))
        
        result = await db.execute_query("SELECT * FROM test WHERE id = %s", (1,), fetch_one=True)
        
        assert result["id"] == 1
        # Verify placeholder was converted
        call_args = mock_conn.fetchrow.call_args[0]
        assert "$1" in call_args[0]

    @pytest.mark.asyncio
    async def test_execute_query_auto_connect(self, mock_db):
        """Test execute_query auto-connects if pool is None."""
        db, mock_conn, _ = mock_db
        db.pool = None
        
        class MockRow:
            def __init__(self, data):
                self._data = data
            def __getitem__(self, key):
                return self._data[key]
            def keys(self):
                return self._data.keys()
            def __iter__(self):
                return iter(self._data)
        
        mock_conn.fetchrow = AsyncMock(return_value=MockRow({"id": 1}))
        
        result = await db.execute_query("SELECT * FROM test WHERE id = $1", (1,), fetch_one=True)
        
        assert result["id"] == 1

    @pytest.mark.asyncio
    async def test_execute_transaction(self, mock_db):
        """Test execute_transaction."""
        db, mock_conn, _ = mock_db
        await db.connect()
        
        # Mock transaction context manager
        mock_transaction = MagicMock()
        mock_transaction.__aenter__ = AsyncMock(return_value=None)
        mock_transaction.__aexit__ = AsyncMock(return_value=None)
        mock_conn.transaction = MagicMock(return_value=mock_transaction)
        mock_conn.execute = AsyncMock()
        
        queries = [
            ("INSERT INTO test VALUES ($1)", (1,)),
            ("UPDATE test SET name = $1", ("test",)),
        ]
        
        await db.execute_transaction(queries)
        
        assert mock_conn.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_transaction_with_placeholders(self, mock_db):
        """Test execute_transaction with %s placeholders."""
        db, mock_conn, _ = mock_db
        await db.connect()
        
        mock_transaction = MagicMock()
        mock_transaction.__aenter__ = AsyncMock(return_value=None)
        mock_transaction.__aexit__ = AsyncMock(return_value=None)
        mock_conn.transaction = MagicMock(return_value=mock_transaction)
        mock_conn.execute = AsyncMock()
        
        queries = [
            ("INSERT INTO test VALUES (%s)", (1,)),
        ]
        
        await db.execute_transaction(queries)
        
        # Verify placeholder was converted
        call_args = mock_conn.execute.call_args[0]
        assert "$1" in call_args[0]

    @pytest.mark.asyncio
    async def test_execute_transaction_no_params(self, mock_db):
        """Test execute_transaction with queries without params."""
        db, mock_conn, _ = mock_db
        await db.connect()
        
        mock_transaction = MagicMock()
        mock_transaction.__aenter__ = AsyncMock(return_value=None)
        mock_transaction.__aexit__ = AsyncMock(return_value=None)
        mock_conn.transaction = MagicMock(return_value=mock_transaction)
        mock_conn.execute = AsyncMock()
        
        queries = [
            ("CREATE TABLE test (id INT)", None),
        ]
        
        await db.execute_transaction(queries)
        
        mock_conn.execute.assert_called_once_with("CREATE TABLE test (id INT)")

    @pytest.mark.asyncio
    async def test_execute_transaction_auto_connect(self, mock_db):
        """Test execute_transaction auto-connects if pool is None."""
        db, mock_conn, _ = mock_db
        db.pool = None
        
        mock_transaction = MagicMock()
        mock_transaction.__aenter__ = AsyncMock(return_value=None)
        mock_transaction.__aexit__ = AsyncMock(return_value=None)
        mock_conn.transaction = MagicMock(return_value=mock_transaction)
        mock_conn.execute = AsyncMock()
        
        queries = [("SELECT 1", None)]
        
        await db.execute_transaction(queries)
        
        mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_connection_success(self, mock_db):
        """Test check_connection success."""
        db, mock_conn, _ = mock_db
        await db.connect()
        
        mock_conn.fetchval = AsyncMock(return_value=1)
        
        result = await db.check_connection()
        
        assert result is True

    @pytest.mark.asyncio
    async def test_check_connection_auto_connect(self, mock_db):
        """Test check_connection auto-connects if pool is None."""
        db, mock_conn, _ = mock_db
        db.pool = None
        
        mock_conn.fetchval = AsyncMock(return_value=1)
        
        result = await db.check_connection()
        
        assert result is True

    @pytest.mark.asyncio
    async def test_check_connection_postgres_error(self, mock_db):
        """Test check_connection with PostgresError."""
        db, mock_conn, _ = mock_db
        await db.connect()
        
        mock_conn.fetchval = AsyncMock(side_effect=Exception("Postgres error"))
        
        result = await db.check_connection()
        
        assert result is False

    @pytest.mark.asyncio
    async def test_check_connection_connection_error(self, mock_db):
        """Test check_connection with ConnectionError."""
        db, _, _ = mock_db
        db.pool = None
        
        with patch("src.core.postgresql_database.connection.asyncpg") as mock_asyncpg:
            mock_asyncpg.create_pool = AsyncMock(side_effect=ConnectionError("Connection failed"))
            mock_asyncpg.PostgresError = Exception
            
            result = await db.check_connection()
            
            assert result is False

    @pytest.mark.asyncio
    async def test_check_connection_unexpected_error(self, mock_db):
        """Test check_connection with unexpected error."""
        db, mock_conn, _ = mock_db
        await db.connect()
        
        mock_conn.fetchval = AsyncMock(side_effect=KeyError("Unexpected error"))
        
        result = await db.check_connection()
        
        assert result is False

    def test_database_config_from_env(self, monkeypatch):
        """Test DatabaseConfig.from_env()."""
        from src.core.postgresql_database import DatabaseConfig
        
        monkeypatch.setenv("DB_HOST", "test_host")
        monkeypatch.setenv("DB_PORT", "5433")
        monkeypatch.setenv("DB_NAME", "test_db")
        monkeypatch.setenv("DB_USER", "test_user")
        monkeypatch.setenv("DB_PASSWORD", "test_pass")
        monkeypatch.setenv("DB_MIN_CONNECTIONS", "2")
        monkeypatch.setenv("DB_MAX_CONNECTIONS", "20")
        
        config = DatabaseConfig.from_env()
        
        assert config.host == "test_host"
        assert config.port == 5433
        assert config.database == "test_db"
        assert config.user == "test_user"
        assert config.password == "test_pass"
        assert config.min_connections == 2
        assert config.max_connections == 20

    def test_database_config_from_env_defaults(self, monkeypatch):
        """Test DatabaseConfig.from_env() with defaults."""
        from src.core.postgresql_database import DatabaseConfig
        
        # Clear all env vars
        monkeypatch.delenv("DB_HOST", raising=False)
        monkeypatch.delenv("DB_PORT", raising=False)
        monkeypatch.delenv("DB_NAME", raising=False)
        monkeypatch.delenv("DB_USER", raising=False)
        monkeypatch.delenv("DB_PASSWORD", raising=False)
        monkeypatch.delenv("DB_MIN_CONNECTIONS", raising=False)
        monkeypatch.delenv("DB_MAX_CONNECTIONS", raising=False)
        
        config = DatabaseConfig.from_env()
        
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "ai_app"
        assert config.user == "postgres"
        assert config.password == ""
        assert config.min_connections == 1
        assert config.max_connections == 10

    def test_execute_query_sync(self, mock_db):
        """Test execute_query_sync."""
        db, mock_conn, _ = mock_db
        
        class MockRow:
            def __init__(self, data):
                self._data = data
            def __getitem__(self, key):
                return self._data[key]
            def keys(self):
                return self._data.keys()
            def __iter__(self):
                return iter(self._data)
        
        mock_conn.fetchrow = AsyncMock(return_value=MockRow({"id": 1}))
        
        result = db.execute_query_sync("SELECT * FROM test WHERE id = $1", (1,), fetch_one=True)
        
        assert result["id"] == 1

    def test_get_or_create_event_loop_new_loop(self, db_config):
        """Test _get_or_create_event_loop creates new loop."""
        db = DatabaseConnection(config=db_config)
        
        # Clear any existing event loop
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_closed():
                loop.close()
        except RuntimeError:
            pass
        
        loop = db._get_or_create_event_loop()
        
        assert loop is not None
        assert isinstance(loop, asyncio.AbstractEventLoop)

    def test_get_or_create_event_loop_existing_loop(self, db_config):
        """Test _get_or_create_event_loop with existing loop."""
        db = DatabaseConnection(config=db_config)
        
        # Create a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result_loop = db._get_or_create_event_loop()
            assert result_loop == loop
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    def test_get_or_create_event_loop_closed_loop(self, db_config):
        """Test _get_or_create_event_loop with closed loop."""
        db = DatabaseConnection(config=db_config)
        
        # Create and close a loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.close()
        
        result_loop = db._get_or_create_event_loop()
        
        assert result_loop is not None
        assert not result_loop.is_closed()

    @pytest.mark.asyncio
    async def test_get_or_create_event_loop_in_async_context(self, db_config):
        """Test _get_or_create_event_loop raises error in async context."""
        db = DatabaseConnection(config=db_config)
        
        with pytest.raises(RuntimeError, match="Cannot use sync methods from async context"):
            db._get_or_create_event_loop()


class TestVectorOperations:
    """Test VectorOperations."""

    @pytest.fixture
    def mock_db(self):
        """Mock database for vector operations."""
        mock_db = MagicMock()
        mock_db.execute_query = AsyncMock()
        mock_db.execute_transaction = AsyncMock()
        return mock_db

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
    def mock_db_connection(self, db_config):
        """Mock database connection for DatabaseConnection tests."""
        mock_pool = MagicMock()
        mock_pool.close = AsyncMock()
        mock_conn = AsyncMock()
        
        # Set up async context manager for pool.acquire()
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_pool.acquire = MagicMock(return_value=mock_context)
        
        mock_asyncpg_patcher = patch("src.core.postgresql_database.connection.asyncpg")
        mock_asyncpg = mock_asyncpg_patcher.start()
        mock_asyncpg.create_pool = AsyncMock(return_value=mock_pool)
        mock_asyncpg.PostgresError = Exception

        db = DatabaseConnection(config=db_config)
        yield db, mock_conn, mock_pool
        mock_asyncpg_patcher.stop()

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

    @pytest.mark.asyncio
    async def test_batch_insert_embeddings_empty(self, mock_db):
        """Test batch_insert_embeddings with empty list."""
        vector_ops = VectorOperations(mock_db)

        await vector_ops.batch_insert_embeddings([])
        mock_db.execute_transaction.assert_not_called()

    @pytest.mark.asyncio
    async def test_similarity_search_with_model_and_tenant(self, mock_db):
        """Test similarity_search with model and tenant_id."""
        mock_db.execute_query.return_value = [
            {"id": 1, "document_id": 1, "similarity": 0.95, "content": "test"}
        ]

        vector_ops = VectorOperations(mock_db)
        query_embedding = [0.1] * 1536

        results = await vector_ops.similarity_search(
            query_embedding=query_embedding,
            limit=5,
            threshold=0.7,
            model="text-embedding-3-small",
            tenant_id="tenant-1",
        )

        assert len(results) == 1
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_similarity_search_with_model_only(self, mock_db):
        """Test similarity_search with model only."""
        mock_db.execute_query.return_value = [
            {"id": 1, "document_id": 1, "similarity": 0.95, "content": "test"}
        ]

        vector_ops = VectorOperations(mock_db)
        query_embedding = [0.1] * 1536

        results = await vector_ops.similarity_search(
            query_embedding=query_embedding,
            limit=5,
            threshold=0.7,
            model="text-embedding-3-small",
        )

        assert len(results) == 1
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_similarity_search_with_tenant_only(self, mock_db):
        """Test similarity_search with tenant_id only."""
        mock_db.execute_query.return_value = [
            {"id": 1, "document_id": 1, "similarity": 0.95, "content": "test"}
        ]

        vector_ops = VectorOperations(mock_db)
        query_embedding = [0.1] * 1536

        results = await vector_ops.similarity_search(
            query_embedding=query_embedding,
            limit=5,
            threshold=0.7,
            tenant_id="tenant-1",
        )

        assert len(results) == 1
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_embedding(self, mock_db):
        """Test get_embedding."""
        mock_db.execute_query.return_value = {
            "id": 1,
            "document_id": 1,
            "embedding": "[0.1,0.2,0.3]",
            "model": "text-embedding-3-small",
        }

        vector_ops = VectorOperations(mock_db)
        result = await vector_ops.get_embedding(1)

        assert result is not None
        assert result["id"] == 1
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_embedding_not_found(self, mock_db):
        """Test get_embedding when not found."""
        mock_db.execute_query.return_value = None

        vector_ops = VectorOperations(mock_db)
        result = await vector_ops.get_embedding(999)

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_embeddings(self, mock_db):
        """Test delete_embeddings."""
        mock_db.execute_query.return_value = 5  # 5 rows deleted

        vector_ops = VectorOperations(mock_db)
        result = await vector_ops.delete_embeddings(document_id=1)

        assert result == 5
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_embedding_success(self, mock_db):
        """Test update_embedding success."""
        mock_db.execute_query.return_value = 1  # 1 row updated

        vector_ops = VectorOperations(mock_db)
        new_embedding = [0.5] * 1536

        result = await vector_ops.update_embedding(embedding_id=1, new_embedding=new_embedding)

        assert result is True
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_embedding_not_found(self, mock_db):
        """Test update_embedding when embedding not found."""
        mock_db.execute_query.return_value = 0  # 0 rows updated

        vector_ops = VectorOperations(mock_db)
        new_embedding = [0.5] * 1536

        result = await vector_ops.update_embedding(embedding_id=999, new_embedding=new_embedding)

        assert result is False


    @pytest.mark.asyncio
    async def test_connect_postgres_error(self, db_config):
        """Test connect with PostgresError."""
        with patch("src.core.postgresql_database.connection.asyncpg") as mock_asyncpg:
            mock_asyncpg.create_pool = AsyncMock(side_effect=Exception("Postgres error"))
            mock_asyncpg.PostgresError = Exception
            
            db = DatabaseConnection(config=db_config)
            with pytest.raises(ConnectionError, match="Failed to create connection pool"):
                await db.connect()

    @pytest.mark.asyncio
    async def test_close_no_pool(self, db_config):
        """Test close when pool is None."""
        db = DatabaseConnection(config=db_config)
        # Should not raise error
        await db.close()
        assert db.pool is None

    @pytest.mark.asyncio
    async def test_get_connection(self, mock_db_connection):
        """Test get_connection context manager."""
        db, mock_conn, _ = mock_db_connection
        await db.connect()
        
        async with db.get_connection() as conn:
            assert conn == mock_conn

    @pytest.mark.asyncio
    async def test_get_connection_auto_connect(self, mock_db_connection):
        """Test get_connection auto-connects if pool is None."""
        db, mock_conn, _ = mock_db_connection
        db.pool = None  # Ensure pool is None
        
        async with db.get_connection() as conn:
            assert conn == mock_conn

    def test_convert_placeholders(self, db_config):
        """Test placeholder conversion."""
        db = DatabaseConnection(config=db_config)
        
        # Test with %s placeholders
        query = "SELECT * FROM test WHERE id = %s AND name = %s"
        result = db._convert_placeholders(query, 2)
        assert result == "SELECT * FROM test WHERE id = $1 AND name = $2"
        
        # Test with no placeholders
        query2 = "SELECT * FROM test"
        result2 = db._convert_placeholders(query2, 0)
        assert result2 == query2
        
        # Test with $1 format (already converted)
        query3 = "SELECT * FROM test WHERE id = $1"
        result3 = db._convert_placeholders(query3, 1)
        assert result3 == query3

    @pytest.mark.asyncio
    async def test_execute_query_no_fetch(self, mock_db_connection):
        """Test execute_query with fetch_all=False."""
        db, mock_conn, _ = mock_db_connection
        await db.connect()
        
        mock_conn.execute = AsyncMock(return_value="INSERT 0 5")
        
        result = await db.execute_query("INSERT INTO test VALUES ($1)", (1,), fetch_all=False)
        
        assert result == 5
        mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_query_no_fetch_empty_result(self, mock_db_connection):
        """Test execute_query with fetch_all=False and empty result."""
        db, mock_conn, _ = mock_db_connection
        await db.connect()
        
        mock_conn.execute = AsyncMock(return_value="")
        
        result = await db.execute_query("INSERT INTO test VALUES ($1)", (1,), fetch_all=False)
        
        assert result == 0

    @pytest.mark.asyncio
    async def test_execute_query_fetch_one_none(self, mock_db_connection):
        """Test execute_query with fetch_one=True and None result."""
        db, mock_conn, _ = mock_db_connection
        await db.connect()
        
        mock_conn.fetchrow = AsyncMock(return_value=None)
        
        result = await db.execute_query("SELECT * FROM test WHERE id = $1", (999,), fetch_one=True)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_execute_query_with_placeholder_conversion(self, mock_db_connection):
        """Test execute_query with %s placeholder conversion."""
        db, mock_conn, _ = mock_db_connection
        await db.connect()
        
        class MockRow:
            def __init__(self, data):
                self._data = data
            def __getitem__(self, key):
                return self._data[key]
            def keys(self):
                return self._data.keys()
            def __iter__(self):
                return iter(self._data)
        
        mock_conn.fetchrow = AsyncMock(return_value=MockRow({"id": 1}))
        
        result = await db.execute_query("SELECT * FROM test WHERE id = %s", (1,), fetch_one=True)
        
        assert result["id"] == 1
        # Verify placeholder was converted
        call_args = mock_conn.fetchrow.call_args[0]
        assert "$1" in call_args[0]

    @pytest.mark.asyncio
    async def test_execute_query_auto_connect(self, mock_db_connection):
        """Test execute_query auto-connects if pool is None."""
        db, mock_conn, _ = mock_db_connection
        db.pool = None
        
        class MockRow:
            def __init__(self, data):
                self._data = data
            def __getitem__(self, key):
                return self._data[key]
            def keys(self):
                return self._data.keys()
            def __iter__(self):
                return iter(self._data)
        
        mock_conn.fetchrow = AsyncMock(return_value=MockRow({"id": 1}))
        
        result = await db.execute_query("SELECT * FROM test WHERE id = $1", (1,), fetch_one=True)
        
        assert result["id"] == 1

    @pytest.mark.asyncio
    async def test_execute_transaction(self, mock_db_connection):
        """Test execute_transaction."""
        db, mock_conn, _ = mock_db_connection
        await db.connect()
        
        # Mock transaction context manager
        mock_transaction = MagicMock()
        mock_transaction.__aenter__ = AsyncMock(return_value=None)
        mock_transaction.__aexit__ = AsyncMock(return_value=None)
        mock_conn.transaction = MagicMock(return_value=mock_transaction)
        mock_conn.execute = AsyncMock()
        
        queries = [
            ("INSERT INTO test VALUES ($1)", (1,)),
            ("UPDATE test SET name = $1", ("test",)),
        ]
        
        await db.execute_transaction(queries)
        
        assert mock_conn.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_transaction_with_placeholders(self, mock_db_connection):
        """Test execute_transaction with %s placeholders."""
        db, mock_conn, _ = mock_db_connection
        await db.connect()
        
        mock_transaction = MagicMock()
        mock_transaction.__aenter__ = AsyncMock(return_value=None)
        mock_transaction.__aexit__ = AsyncMock(return_value=None)
        mock_conn.transaction = MagicMock(return_value=mock_transaction)
        mock_conn.execute = AsyncMock()
        
        queries = [
            ("INSERT INTO test VALUES (%s)", (1,)),
        ]
        
        await db.execute_transaction(queries)
        
        # Verify placeholder was converted
        call_args = mock_conn.execute.call_args[0]
        assert "$1" in call_args[0]

    @pytest.mark.asyncio
    async def test_execute_transaction_no_params(self, mock_db_connection):
        """Test execute_transaction with queries without params."""
        db, mock_conn, _ = mock_db_connection
        await db.connect()
        
        mock_transaction = MagicMock()
        mock_transaction.__aenter__ = AsyncMock(return_value=None)
        mock_transaction.__aexit__ = AsyncMock(return_value=None)
        mock_conn.transaction = MagicMock(return_value=mock_transaction)
        mock_conn.execute = AsyncMock()
        
        queries = [
            ("CREATE TABLE test (id INT)", None),
        ]
        
        await db.execute_transaction(queries)
        
        mock_conn.execute.assert_called_once_with("CREATE TABLE test (id INT)")

    @pytest.mark.asyncio
    async def test_execute_transaction_auto_connect(self, mock_db_connection):
        """Test execute_transaction auto-connects if pool is None."""
        db, mock_conn, _ = mock_db_connection
        db.pool = None
        
        mock_transaction = MagicMock()
        mock_transaction.__aenter__ = AsyncMock(return_value=None)
        mock_transaction.__aexit__ = AsyncMock(return_value=None)
        mock_conn.transaction = MagicMock(return_value=mock_transaction)
        mock_conn.execute = AsyncMock()
        
        queries = [("SELECT 1", None)]
        
        await db.execute_transaction(queries)
        
        mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_connection_success(self, mock_db_connection):
        """Test check_connection success."""
        db, mock_conn, _ = mock_db_connection
        await db.connect()
        
        mock_conn.fetchval = AsyncMock(return_value=1)
        
        result = await db.check_connection()
        
        assert result is True

    @pytest.mark.asyncio
    async def test_check_connection_auto_connect(self, mock_db_connection):
        """Test check_connection auto-connects if pool is None."""
        db, mock_conn, _ = mock_db_connection
        db.pool = None
        
        mock_conn.fetchval = AsyncMock(return_value=1)
        
        result = await db.check_connection()
        
        assert result is True

    @pytest.mark.asyncio
    async def test_check_connection_postgres_error(self, mock_db_connection):
        """Test check_connection with PostgresError."""
        db, mock_conn, _ = mock_db_connection
        await db.connect()
        
        mock_conn.fetchval = AsyncMock(side_effect=Exception("Postgres error"))
        
        result = await db.check_connection()
        
        assert result is False

    @pytest.mark.asyncio
    async def test_check_connection_connection_error(self, mock_db_connection):
        """Test check_connection with ConnectionError."""
        db, _, _ = mock_db_connection
        db.pool = None
        
        with patch("src.core.postgresql_database.connection.asyncpg") as mock_asyncpg:
            mock_asyncpg.create_pool = AsyncMock(side_effect=ConnectionError("Connection failed"))
            mock_asyncpg.PostgresError = Exception
            
            result = await db.check_connection()
            
            assert result is False

    @pytest.mark.asyncio
    async def test_check_connection_unexpected_error(self, mock_db_connection):
        """Test check_connection with unexpected error."""
        db, mock_conn, _ = mock_db_connection
        await db.connect()
        
        mock_conn.fetchval = AsyncMock(side_effect=KeyError("Unexpected error"))
        
        result = await db.check_connection()
        
        assert result is False

    def test_database_config_from_env(self, monkeypatch):
        """Test DatabaseConfig.from_env()."""
        from src.core.postgresql_database import DatabaseConfig
        
        monkeypatch.setenv("DB_HOST", "test_host")
        monkeypatch.setenv("DB_PORT", "5433")
        monkeypatch.setenv("DB_NAME", "test_db")
        monkeypatch.setenv("DB_USER", "test_user")
        monkeypatch.setenv("DB_PASSWORD", "test_pass")
        monkeypatch.setenv("DB_MIN_CONNECTIONS", "2")
        monkeypatch.setenv("DB_MAX_CONNECTIONS", "20")
        
        config = DatabaseConfig.from_env()
        
        assert config.host == "test_host"
        assert config.port == 5433
        assert config.database == "test_db"
        assert config.user == "test_user"
        assert config.password == "test_pass"
        assert config.min_connections == 2
        assert config.max_connections == 20

    def test_database_config_from_env_defaults(self, monkeypatch):
        """Test DatabaseConfig.from_env() with defaults."""
        from src.core.postgresql_database import DatabaseConfig
        
        # Clear all env vars
        monkeypatch.delenv("DB_HOST", raising=False)
        monkeypatch.delenv("DB_PORT", raising=False)
        monkeypatch.delenv("DB_NAME", raising=False)
        monkeypatch.delenv("DB_USER", raising=False)
        monkeypatch.delenv("DB_PASSWORD", raising=False)
        monkeypatch.delenv("DB_MIN_CONNECTIONS", raising=False)
        monkeypatch.delenv("DB_MAX_CONNECTIONS", raising=False)
        
        config = DatabaseConfig.from_env()
        
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "ai_app"
        assert config.user == "postgres"
        assert config.password == ""
        assert config.min_connections == 1
        assert config.max_connections == 10

    def test_execute_query_sync(self, mock_db_connection):
        """Test execute_query_sync."""
        db, mock_conn, _ = mock_db_connection
        
        class MockRow:
            def __init__(self, data):
                self._data = data
            def __getitem__(self, key):
                return self._data[key]
            def keys(self):
                return self._data.keys()
            def __iter__(self):
                return iter(self._data)
        
        mock_conn.fetchrow = AsyncMock(return_value=MockRow({"id": 1}))
        
        result = db.execute_query_sync("SELECT * FROM test WHERE id = $1", (1,), fetch_one=True)
        
        assert result["id"] == 1

    def test_get_or_create_event_loop_new_loop(self, db_config):
        """Test _get_or_create_event_loop creates new loop."""
        db = DatabaseConnection(config=db_config)
        
        # Clear any existing event loop
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_closed():
                loop.close()
        except RuntimeError:
            pass
        
        loop = db._get_or_create_event_loop()
        
        assert loop is not None
        assert isinstance(loop, asyncio.AbstractEventLoop)

    def test_get_or_create_event_loop_existing_loop(self, db_config):
        """Test _get_or_create_event_loop with existing loop."""
        db = DatabaseConnection(config=db_config)
        
        # Create a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result_loop = db._get_or_create_event_loop()
            assert result_loop == loop
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    def test_get_or_create_event_loop_closed_loop(self, db_config):
        """Test _get_or_create_event_loop with closed loop."""
        db = DatabaseConnection(config=db_config)
        
        # Create and close a loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.close()
        
        result_loop = db._get_or_create_event_loop()
        
        assert result_loop is not None
        assert not result_loop.is_closed()

    @pytest.mark.asyncio
    async def test_get_or_create_event_loop_in_async_context(self, db_config):
        """Test _get_or_create_event_loop raises error in async context."""
        db = DatabaseConnection(config=db_config)
        
        with pytest.raises(RuntimeError, match="Cannot use sync methods from async context"):
            db._get_or_create_event_loop()


class TestVectorIndexManager:
    """Test VectorIndexManager."""

    @pytest.fixture
    def mock_db(self):
        """Mock database for vector index manager."""
        mock_db = MagicMock()
        mock_db.execute_query = AsyncMock()
        return mock_db

    @pytest.fixture
    def index_manager(self, mock_db):
        """Vector index manager fixture."""
        from src.core.postgresql_database.vector_index_manager import VectorIndexManager
        return VectorIndexManager(mock_db)

    def test_database_error_init(self):
        """Test DatabaseError initialization."""
        from src.core.postgresql_database.vector_index_manager import DatabaseError

        error = DatabaseError("Test error", operation="test_op", original_error=ValueError("original"))
        assert error.message == "Test error"
        assert error.operation == "test_op"
        assert error.original_error is not None
        assert str(error) == "Test error"

    def test_vector_index_error_init(self):
        """Test VectorIndexError initialization."""
        from src.core.postgresql_database.vector_index_manager import VectorIndexError

        error = VectorIndexError("Test error", index_name="test_idx", original_error=ValueError("original"))
        assert error.message == "Test error"
        assert error.index_name == "test_idx"
        assert error.original_error is not None
        assert str(error) == "Test error"

    def test_index_type_enum(self):
        """Test IndexType enum."""
        from src.core.postgresql_database.vector_index_manager import IndexType

        assert IndexType.IVFFLAT == "ivfflat"
        assert IndexType.HNSW == "hnsw"

    def test_index_distance_enum(self):
        """Test IndexDistance enum."""
        from src.core.postgresql_database.vector_index_manager import IndexDistance

        assert IndexDistance.COSINE == "cosine"
        assert IndexDistance.L2 == "l2"
        assert IndexDistance.INNER_PRODUCT == "inner_product"

    def test_vector_index_manager_init(self, mock_db):
        """Test VectorIndexManager initialization."""
        from src.core.postgresql_database.vector_index_manager import VectorIndexManager

        manager = VectorIndexManager(mock_db)
        assert manager.db == mock_db

    def test_get_distance_opclass_cosine(self, index_manager):
        """Test _get_distance_opclass with COSINE."""
        from src.core.postgresql_database.vector_index_manager import IndexDistance

        result = index_manager._get_distance_opclass(IndexDistance.COSINE)
        assert result == "vector_cosine_ops"

    def test_get_distance_opclass_l2(self, index_manager):
        """Test _get_distance_opclass with L2."""
        from src.core.postgresql_database.vector_index_manager import IndexDistance

        result = index_manager._get_distance_opclass(IndexDistance.L2)
        assert result == "vector_l2_ops"

    def test_get_distance_opclass_inner_product(self, index_manager):
        """Test _get_distance_opclass with INNER_PRODUCT."""
        from src.core.postgresql_database.vector_index_manager import IndexDistance

        result = index_manager._get_distance_opclass(IndexDistance.INNER_PRODUCT)
        assert result == "vector_ip_ops"

    def test_build_ivfflat_query(self, index_manager):
        """Test _build_ivfflat_query."""
        query = index_manager._build_ivfflat_query(
            "test_idx", "test_table", "test_col", "vector_cosine_ops", 100
        )
        assert "CREATE INDEX IF NOT EXISTS test_idx" in query
        assert "ON test_table USING ivfflat" in query
        assert "lists = 100" in query

    def test_build_hnsw_query(self, index_manager):
        """Test _build_hnsw_query."""
        query = index_manager._build_hnsw_query(
            "test_idx", "test_table", "test_col", "vector_cosine_ops", 16, 64
        )
        assert "CREATE INDEX IF NOT EXISTS test_idx" in query
        assert "ON test_table USING hnsw" in query
        assert "m = 16" in query
        assert "ef_construction = 64" in query

    @pytest.mark.asyncio
    async def test_create_index_already_exists(self, index_manager, mock_db):
        """Test create_index when index already exists."""
        from src.core.postgresql_database.vector_index_manager import IndexType, IndexDistance

        mock_db.execute_query.return_value = {"exists": True}
        index_manager.index_exists = AsyncMock(return_value=True)

        result = await index_manager.create_index(
            table_name="test_table",
            column_name="test_col",
            index_type=IndexType.IVFFLAT,
            distance=IndexDistance.COSINE,
        )

        assert result is not None
        mock_db.execute_query.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_index_ivfflat_with_lists(self, index_manager, mock_db):
        """Test create_index with IVFFlat and provided lists."""
        from src.core.postgresql_database.vector_index_manager import IndexType, IndexDistance

        index_manager.index_exists = AsyncMock(return_value=False)
        mock_db.execute_query.return_value = None

        result = await index_manager.create_index(
            table_name="test_table",
            column_name="test_col",
            index_type=IndexType.IVFFLAT,
            distance=IndexDistance.COSINE,
            lists=200,
        )

        assert result is not None
        mock_db.execute_query.assert_called()

    @pytest.mark.asyncio
    async def test_create_index_ivfflat_calculate_lists(self, index_manager, mock_db):
        """Test create_index with IVFFlat and calculated lists."""
        from src.core.postgresql_database.vector_index_manager import IndexType, IndexDistance

        index_manager.index_exists = AsyncMock(return_value=False)
        index_manager._get_table_row_count = AsyncMock(return_value=10000)
        mock_db.execute_query.return_value = None

        result = await index_manager.create_index(
            table_name="test_table",
            column_name="test_col",
            index_type=IndexType.IVFFLAT,
            distance=IndexDistance.COSINE,
        )

        assert result is not None
        mock_db.execute_query.assert_called()

    @pytest.mark.asyncio
    async def test_create_index_hnsw_with_params(self, index_manager, mock_db):
        """Test create_index with HNSW and provided parameters."""
        from src.core.postgresql_database.vector_index_manager import IndexType, IndexDistance

        index_manager.index_exists = AsyncMock(return_value=False)
        mock_db.execute_query.return_value = None

        result = await index_manager.create_index(
            table_name="test_table",
            column_name="test_col",
            index_type=IndexType.HNSW,
            distance=IndexDistance.L2,
            m=32,
            ef_construction=128,
        )

        assert result is not None
        mock_db.execute_query.assert_called()

    @pytest.mark.asyncio
    async def test_create_index_hnsw_defaults(self, index_manager, mock_db):
        """Test create_index with HNSW and default parameters."""
        from src.core.postgresql_database.vector_index_manager import IndexType, IndexDistance

        index_manager.index_exists = AsyncMock(return_value=False)
        mock_db.execute_query.return_value = None

        result = await index_manager.create_index(
            table_name="test_table",
            column_name="test_col",
            index_type=IndexType.HNSW,
            distance=IndexDistance.INNER_PRODUCT,
        )

        assert result is not None
        mock_db.execute_query.assert_called()

    @pytest.mark.asyncio
    async def test_create_index_with_tenant_id(self, index_manager, mock_db):
        """Test create_index with tenant_id."""
        from src.core.postgresql_database.vector_index_manager import IndexType, IndexDistance
        from unittest.mock import AsyncMock

        # Mock IndexDAL methods
        index_manager.index_dal.index_exists = AsyncMock(return_value=False)
        index_manager.index_dal.get_table_row_count = AsyncMock(return_value=1000)
        index_manager.index_dal.create_index = AsyncMock(return_value=True)

        result = await index_manager.create_index(
            table_name="test_table",
            column_name="test_col",
            index_type=IndexType.IVFFLAT,
            distance=IndexDistance.COSINE,
            tenant_id="tenant-1",
        )

        assert result is not None
        assert "tenant-1" in result

    @pytest.mark.asyncio
    async def test_create_index_error(self, index_manager, mock_db):
        """Test create_index with error."""
        from src.core.postgresql_database.vector_index_manager import (
            DatabaseError,
            IndexType,
            IndexDistance,
        )

        index_manager.index_exists = AsyncMock(return_value=False)
        # Provide lists to avoid calling _get_table_row_count
        mock_db.execute_query.side_effect = Exception("Database error")

        with pytest.raises(DatabaseError):
            await index_manager.create_index(
                table_name="test_table",
                column_name="test_col",
                index_type=IndexType.IVFFLAT,
                distance=IndexDistance.COSINE,
                lists=100,  # Provide lists to avoid row count query
            )

    @pytest.mark.asyncio
    async def test_index_exists_true(self, index_manager, mock_db):
        """Test index_exists returns True."""
        mock_db.execute_query.return_value = {"exists": True}

        result = await index_manager.index_exists("test_idx")

        assert result is True

    @pytest.mark.asyncio
    async def test_index_exists_false(self, index_manager, mock_db):
        """Test index_exists returns False."""
        mock_db.execute_query.return_value = None  # IndexDAL returns None if not found

        result = await index_manager.index_exists("test_idx")

        assert result is False

    @pytest.mark.asyncio
    async def test_index_exists_none_result(self, index_manager, mock_db):
        """Test index_exists with None result."""
        mock_db.execute_query.return_value = None

        result = await index_manager.index_exists("test_idx")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_index_info(self, index_manager, mock_db):
        """Test get_index_info."""
        mock_db.execute_query.return_value = {
            "indexname": "test_idx",
            "tablename": "test_table",
            "indexdef": "CREATE INDEX...",
            "index_size": "1 MB",
            "is_valid": True,
            "is_ready": True,
        }

        result = await index_manager.get_index_info("test_idx")

        assert result is not None
        assert result["indexname"] == "test_idx"

    @pytest.mark.asyncio
    async def test_get_index_info_none(self, index_manager, mock_db):
        """Test get_index_info returns None."""
        mock_db.execute_query.return_value = None

        result = await index_manager.get_index_info("test_idx")

        assert result is None

    @pytest.mark.asyncio
    async def test_list_indexes_with_table(self, index_manager, mock_db):
        """Test list_indexes with table name."""
        # Mock IndexDAL's list_indexes to return vector indexes
        from unittest.mock import AsyncMock
        index_manager.index_dal.list_indexes = AsyncMock(return_value=[
            {"indexname": "idx1", "tablename": "test_table", "indexdef": "CREATE INDEX idx1 USING ivfflat", "index_size": "1 MB"}
        ])

        result = await index_manager.list_indexes(table_name="test_table")

        assert len(result) == 1
        assert result[0]["indexname"] == "idx1"

    @pytest.mark.asyncio
    async def test_list_indexes_without_table(self, index_manager, mock_db):
        """Test list_indexes without table name."""
        # Mock IndexDAL's list_indexes to return vector indexes
        from unittest.mock import AsyncMock
        index_manager.index_dal.list_indexes = AsyncMock(return_value=[
            {"indexname": "idx1", "tablename": "table1", "indexdef": "CREATE INDEX idx1 USING ivfflat", "index_size": "1 MB"},
            {"indexname": "idx2", "tablename": "table2", "indexdef": "CREATE INDEX idx2 USING hnsw", "index_size": "2 MB"},
        ])

        result = await index_manager.list_indexes()

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_indexes_empty(self, index_manager, mock_db):
        """Test list_indexes with empty result."""
        mock_db.execute_query.return_value = None

        result = await index_manager.list_indexes()

        assert result == []

    @pytest.mark.asyncio
    async def test_reindex_success(self, index_manager, mock_db):
        """Test reindex success."""
        index_manager.index_exists = AsyncMock(return_value=True)
        mock_db.execute_query.return_value = None

        result = await index_manager.reindex("test_idx", concurrently=False)

        assert result is True
        mock_db.execute_query.assert_called()

    @pytest.mark.asyncio
    async def test_reindex_concurrent(self, index_manager, mock_db):
        """Test reindex with concurrently=True."""
        index_manager.index_exists = AsyncMock(return_value=True)
        mock_db.execute_query.return_value = None

        result = await index_manager.reindex("test_idx", concurrently=True)

        assert result is True
        # Verify CONCURRENTLY is in the query
        call_args = mock_db.execute_query.call_args[0]
        assert "CONCURRENTLY" in call_args[0]

    @pytest.mark.asyncio
    async def test_reindex_not_exists(self, index_manager):
        """Test reindex when index doesn't exist."""
        from src.core.postgresql_database.vector_index_manager import VectorIndexError

        index_manager.index_exists = AsyncMock(return_value=False)

        with pytest.raises(VectorIndexError):
            await index_manager.reindex("test_idx")

    @pytest.mark.asyncio
    async def test_reindex_error(self, index_manager, mock_db):
        """Test reindex with error."""
        from src.core.postgresql_database.vector_index_manager import VectorIndexError

        index_manager.index_exists = AsyncMock(return_value=True)
        mock_db.execute_query.side_effect = Exception("Database error")

        with pytest.raises(VectorIndexError):
            await index_manager.reindex("test_idx")

    @pytest.mark.asyncio
    async def test_reindex_table(self, index_manager, mock_db):
        """Test reindex_table."""
        index_manager.list_indexes = AsyncMock(
            return_value=[
                {"indexname": "idx1"},
                {"indexname": "idx2"},
            ]
        )
        index_manager.reindex = AsyncMock(return_value=True)

        result = await index_manager.reindex_table("test_table", concurrently=False)

        assert len(result) == 2
        assert index_manager.reindex.call_count == 2

    @pytest.mark.asyncio
    async def test_reindex_table_with_failure(self, index_manager, mock_db):
        """Test reindex_table with some failures."""
        index_manager.list_indexes = AsyncMock(
            return_value=[
                {"indexname": "idx1"},
                {"indexname": "idx2"},
            ]
        )
        index_manager.reindex = AsyncMock(side_effect=[True, Exception("Error")])

        result = await index_manager.reindex_table("test_table")

        assert len(result) == 1
        assert result[0] == "idx1"

    @pytest.mark.asyncio
    async def test_drop_index_exists(self, index_manager, mock_db):
        """Test drop_index when index exists."""
        index_manager.index_exists = AsyncMock(return_value=True)
        mock_db.execute_query.return_value = None

        result = await index_manager.drop_index("test_idx", if_exists=True)

        assert result == "test_idx"
        mock_db.execute_query.assert_called()

    @pytest.mark.asyncio
    async def test_drop_index_not_exists_if_exists_true(self, index_manager):
        """Test drop_index when index doesn't exist and if_exists=True."""
        index_manager.index_exists = AsyncMock(return_value=False)

        result = await index_manager.drop_index("test_idx", if_exists=True)

        assert result is None

    @pytest.mark.asyncio
    async def test_drop_index_not_exists_if_exists_false(self, index_manager, mock_db):
        """Test drop_index when index doesn't exist and if_exists=False."""
        index_manager.index_exists = AsyncMock(return_value=False)
        mock_db.execute_query.return_value = None

        result = await index_manager.drop_index("test_idx", if_exists=False)

        assert result == "test_idx"
        mock_db.execute_query.assert_called()

    @pytest.mark.asyncio
    async def test_drop_index_error(self, index_manager, mock_db):
        """Test drop_index with error."""
        from src.core.postgresql_database.vector_index_manager import DatabaseError

        index_manager.index_exists = AsyncMock(return_value=True)
        mock_db.execute_query.side_effect = Exception("Database error")

        with pytest.raises(DatabaseError):
            await index_manager.drop_index("test_idx")

    @pytest.mark.asyncio
    async def test_auto_reindex_on_embedding_change_with_index_type(self, index_manager):
        """Test auto_reindex_on_embedding_change with specific index type."""
        from src.core.postgresql_database.vector_index_manager import IndexType

        index_manager.index_exists = AsyncMock(return_value=True)
        index_manager.reindex = AsyncMock(return_value=True)

        result = await index_manager.auto_reindex_on_embedding_change(
            table_name="test_table",
            column_name="test_col",
            index_type=IndexType.IVFFLAT,
        )

        assert result is True
        index_manager.reindex.assert_called_once()

    @pytest.mark.asyncio
    async def test_auto_reindex_on_embedding_change_index_not_exists(self, index_manager):
        """Test auto_reindex_on_embedding_change when index doesn't exist."""
        from src.core.postgresql_database.vector_index_manager import IndexType

        index_manager.index_exists = AsyncMock(return_value=False)

        result = await index_manager.auto_reindex_on_embedding_change(
            table_name="test_table",
            column_name="test_col",
            index_type=IndexType.IVFFLAT,
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_auto_reindex_on_embedding_change_all_indexes(self, index_manager):
        """Test auto_reindex_on_embedding_change without index type."""
        index_manager.reindex_table = AsyncMock(return_value=["idx1", "idx2"])

        result = await index_manager.auto_reindex_on_embedding_change(
            table_name="test_table",
            column_name="test_col",
        )

        assert result is True
        index_manager.reindex_table.assert_called_once_with("test_table", concurrently=True)

    @pytest.mark.asyncio
    async def test_auto_reindex_on_embedding_change_no_indexes(self, index_manager):
        """Test auto_reindex_on_embedding_change with no indexes."""
        index_manager.reindex_table = AsyncMock(return_value=[])

        result = await index_manager.auto_reindex_on_embedding_change(
            table_name="test_table",
            column_name="test_col",
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_get_index_statistics_exists(self, index_manager, mock_db):
        """Test get_index_statistics when index exists."""
        index_manager.index_exists = AsyncMock(return_value=True)
        mock_db.execute_query.side_effect = [
            {"oid": 12345},  # First call for OID
            {"size": "1 MB", "num_scans": 100, "tuples_returned": 1000, "tuples_fetched": 500},
        ]

        result = await index_manager.get_index_statistics("test_idx")

        assert result is not None
        assert result["size"] == "1 MB"

    @pytest.mark.asyncio
    async def test_get_index_statistics_not_exists(self, index_manager):
        """Test get_index_statistics when index doesn't exist."""
        index_manager.index_exists = AsyncMock(return_value=False)

        result = await index_manager.get_index_statistics("test_idx")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_index_statistics_no_oid(self, index_manager, mock_db):
        """Test get_index_statistics when OID not found."""
        index_manager.index_exists = AsyncMock(return_value=True)
        mock_db.execute_query.return_value = None

        result = await index_manager.get_index_statistics("test_idx")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_index_statistics_empty_oid(self, index_manager, mock_db):
        """Test get_index_statistics when OID is empty."""
        index_manager.index_exists = AsyncMock(return_value=True)
        mock_db.execute_query.return_value = {}

        result = await index_manager.get_index_statistics("test_idx")

        assert result is None

    def test_get_index_name_basic(self, index_manager):
        """Test _get_index_name without tenant_id."""
        from src.core.postgresql_database.vector_index_manager import IndexType

        result = index_manager._get_index_name("test_table", "test_col", IndexType.IVFFLAT)
        assert "test_table" in result
        assert "test_col" in result
        assert "ivfflat" in result

    def test_get_index_name_with_tenant_id(self, index_manager):
        """Test _get_index_name with tenant_id."""
        from src.core.postgresql_database.vector_index_manager import IndexType

        result = index_manager._get_index_name(
            "test_table", "test_col", IndexType.HNSW, tenant_id="tenant-1"
        )
        assert "tenant-1" in result

    @pytest.mark.asyncio
    async def test_get_table_row_count_without_tenant(self, index_manager, mock_db):
        """Test _get_table_row_count without tenant_id."""
        mock_db.execute_query.return_value = {"count": 1000}

        result = await index_manager._get_table_row_count("test_table")

        assert result == 1000

    @pytest.mark.asyncio
    async def test_get_table_row_count_with_tenant(self, index_manager, mock_db):
        """Test _get_table_row_count with tenant_id."""
        mock_db.execute_query.return_value = {"count": 500}

        result = await index_manager._get_table_row_count("test_table", tenant_id="tenant-1")

        assert result == 500

    @pytest.mark.asyncio
    async def test_get_table_row_count_none_result(self, index_manager, mock_db):
        """Test _get_table_row_count with None result."""
        mock_db.execute_query.return_value = None

        result = await index_manager._get_table_row_count("test_table")

        assert result == 0

    @pytest.mark.asyncio
    async def test_get_table_row_count_no_count_key(self, index_manager, mock_db):
        """Test _get_table_row_count without count key."""
        mock_db.execute_query.return_value = {}

        result = await index_manager._get_table_row_count("test_table")

        assert result == 0

    def test_create_vector_index_manager(self, mock_db):
        """Test create_vector_index_manager factory function."""
        from src.core.postgresql_database.vector_index_manager import (
            VectorIndexManager,
            create_vector_index_manager,
        )

        manager = create_vector_index_manager(mock_db)

        assert isinstance(manager, VectorIndexManager)
        assert manager.db == mock_db


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
