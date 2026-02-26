"""
Unit Tests for Database Setup

Tests database initialization and setup functions.
"""


from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.postgresql_database import DatabaseConnection, DatabaseConfig
from src.core.postgresql_database.setup import (
    create_pgvector_extension,
    verify_pgvector_extension,
    create_embeddings_table,
    create_documents_table,
    verify_tables_exist,
    setup_vector_indexes,
    verify_setup,
    setup_database,
)


class TestSetupFunctions:
    """Test database setup functions."""

    @pytest.fixture
    def db_config(self):
        """Database configuration fixture."""
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
    async def test_create_pgvector_extension_success(self, mock_db):
        """Test create_pgvector_extension success."""
        db, _, _ = mock_db
        db.create_pgvector_extension = AsyncMock(return_value=True)
        
        result = await create_pgvector_extension(db)
        
        assert result is True
        db.create_pgvector_extension.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_pgvector_extension_failure(self, mock_db):
        """Test create_pgvector_extension failure."""
        db, _, _ = mock_db
        db.create_pgvector_extension = AsyncMock(return_value=False)
        
        result = await create_pgvector_extension(db)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_create_pgvector_extension_exception(self, mock_db):
        """Test create_pgvector_extension with exception."""
        db, _, _ = mock_db
        db.create_pgvector_extension = AsyncMock(side_effect=Exception("DB error"))
        
        result = await create_pgvector_extension(db)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_create_pgvector_extension_with_otel(self, mock_db):
        """Test create_pgvector_extension with OTEL integration."""
        db, _, _ = mock_db
        db.create_pgvector_extension = AsyncMock(return_value=True)
        
        # Mock OTEL tracer
        mock_tracer = MagicMock()
        mock_trace = MagicMock()
        mock_trace.set_attribute = MagicMock()
        mock_tracer.start_trace = MagicMock(return_value=mock_trace)
        mock_trace.__enter__ = MagicMock(return_value=mock_trace)
        mock_trace.__exit__ = MagicMock(return_value=None)
        
        with patch("src.core.otel_integration.create_otel_tracer", return_value=mock_tracer):
            result = await create_pgvector_extension(db)
            
            assert result is True
            mock_trace.set_attribute.assert_called()

    @pytest.mark.asyncio
    async def test_verify_pgvector_extension_success(self, mock_db):
        """Test verify_pgvector_extension success."""
        db, _, _ = mock_db
        db.verify_pgvector_extension = AsyncMock(return_value=True)
        
        result = await verify_pgvector_extension(db)
        
        assert result is True
        db.verify_pgvector_extension.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_pgvector_extension_failure(self, mock_db):
        """Test verify_pgvector_extension failure."""
        db, _, _ = mock_db
        db.verify_pgvector_extension = AsyncMock(return_value=False)
        
        result = await verify_pgvector_extension(db)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_pgvector_extension_exception(self, mock_db):
        """Test verify_pgvector_extension with exception."""
        db, _, _ = mock_db
        db.verify_pgvector_extension = AsyncMock(side_effect=Exception("DB error"))
        
        result = await verify_pgvector_extension(db)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_create_embeddings_table_success(self, mock_db):
        """Test create_embeddings_table success."""
        db, _, _ = mock_db
        db.execute_query = AsyncMock(return_value=None)
        
        result = await create_embeddings_table(db, dimension=1536)
        
        assert result is True
        db.execute_query.assert_called_once()
        # Verify vector dimension in query
        call_args = db.execute_query.call_args[0]
        assert "vector(1536)" in call_args[0]

    @pytest.mark.asyncio
    async def test_create_embeddings_table_custom_dimension(self, mock_db):
        """Test create_embeddings_table with custom dimension."""
        db, _, _ = mock_db
        db.execute_query = AsyncMock(return_value=None)
        
        result = await create_embeddings_table(db, dimension=768)
        
        assert result is True
        call_args = db.execute_query.call_args[0]
        assert "vector(768)" in call_args[0]

    @pytest.mark.asyncio
    async def test_create_embeddings_table_exception(self, mock_db):
        """Test create_embeddings_table with exception."""
        db, _, _ = mock_db
        db.execute_query = AsyncMock(side_effect=Exception("DB error"))
        
        result = await create_embeddings_table(db)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_create_embeddings_table_with_otel(self, mock_db):
        """Test create_embeddings_table with OTEL integration."""
        db, _, _ = mock_db
        db.execute_query = AsyncMock(return_value=None)
        
        # Mock OTEL tracer
        mock_tracer = MagicMock()
        mock_trace = MagicMock()
        mock_trace.set_attribute = MagicMock()
        mock_tracer.start_trace = MagicMock(return_value=mock_trace)
        mock_trace.__enter__ = MagicMock(return_value=mock_trace)
        mock_trace.__exit__ = MagicMock(return_value=None)
        
        with patch("src.core.otel_integration.create_otel_tracer", return_value=mock_tracer):
            result = await create_embeddings_table(db)
            
            assert result is True
            mock_trace.set_attribute.assert_called()

    @pytest.mark.asyncio
    async def test_create_documents_table_success(self, mock_db):
        """Test create_documents_table success."""
        db, _, _ = mock_db
        db.execute_query = AsyncMock(return_value=None)
        
        result = await create_documents_table(db)
        
        assert result is True
        db.execute_query.assert_called_once()
        # Verify table structure in query
        call_args = db.execute_query.call_args[0]
        assert "CREATE TABLE IF NOT EXISTS documents" in call_args[0]
        assert "JSONB" in call_args[0]

    @pytest.mark.asyncio
    async def test_create_documents_table_exception(self, mock_db):
        """Test create_documents_table with exception."""
        db, _, _ = mock_db
        db.execute_query = AsyncMock(side_effect=Exception("DB error"))
        
        result = await create_documents_table(db)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_tables_exist_both_exist(self, mock_db):
        """Test verify_tables_exist when both tables exist."""
        db, _, _ = mock_db
        db.execute_query = AsyncMock(return_value=[
            {"table_name": "embeddings"},
            {"table_name": "documents"},
        ])
        
        result = await verify_tables_exist(db)
        
        assert result["embeddings"] is True
        assert result["documents"] is True

    @pytest.mark.asyncio
    async def test_verify_tables_exist_none_exist(self, mock_db):
        """Test verify_tables_exist when no tables exist."""
        db, _, _ = mock_db
        db.execute_query = AsyncMock(return_value=[])
        
        result = await verify_tables_exist(db)
        
        assert result["embeddings"] is False
        assert result["documents"] is False

    @pytest.mark.asyncio
    async def test_verify_tables_exist_partial(self, mock_db):
        """Test verify_tables_exist when only one table exists."""
        db, _, _ = mock_db
        db.execute_query = AsyncMock(return_value=[
            {"table_name": "embeddings"},
        ])
        
        result = await verify_tables_exist(db)
        
        assert result["embeddings"] is True
        assert result["documents"] is False

    @pytest.mark.asyncio
    async def test_verify_tables_exist_exception(self, mock_db):
        """Test verify_tables_exist with exception."""
        db, _, _ = mock_db
        db.execute_query = AsyncMock(side_effect=Exception("DB error"))
        
        result = await verify_tables_exist(db)
        
        assert result["embeddings"] is False
        assert result["documents"] is False

    @pytest.mark.asyncio
    async def test_setup_vector_indexes_ivfflat(self, mock_db):
        """Test setup_vector_indexes with ivfflat."""
        db, _, _ = mock_db
        
        # Mock VectorIndexManager
        mock_index_manager = MagicMock()
        mock_index_manager.create_index = AsyncMock(return_value="idx_embeddings_embedding_ivfflat")
        
        with patch("src.core.postgresql_database.vector_index_manager.VectorIndexManager") as mock_manager_class:
            mock_manager_class.return_value = mock_index_manager
            result = await setup_vector_indexes(db, index_type="ivfflat")
            
            assert result is True
            mock_index_manager.create_index.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_vector_indexes_hnsw(self, mock_db):
        """Test setup_vector_indexes with hnsw."""
        db, _, _ = mock_db
        
        # Mock VectorIndexManager
        mock_index_manager = MagicMock()
        mock_index_manager.create_index = AsyncMock(return_value="idx_embeddings_embedding_hnsw")
        
        with patch("src.core.postgresql_database.vector_index_manager.VectorIndexManager") as mock_manager_class:
            mock_manager_class.return_value = mock_index_manager
            result = await setup_vector_indexes(db, index_type="hnsw")
            
            assert result is True
            mock_index_manager.create_index.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_vector_indexes_exception(self, mock_db):
        """Test setup_vector_indexes with exception."""
        db, _, _ = mock_db
        
        # Mock VectorIndexManager to raise exception in create_index
        mock_index_manager = MagicMock()
        mock_index_manager.create_index = AsyncMock(side_effect=Exception("Error"))
        
        with patch("src.core.postgresql_database.vector_index_manager.VectorIndexManager") as mock_manager_class:
            mock_manager_class.return_value = mock_index_manager
            result = await setup_vector_indexes(db)
            
            assert result is False

    @pytest.mark.asyncio
    async def test_verify_setup_complete(self, mock_db):
        """Test verify_setup with complete setup."""
        db, _, _ = mock_db
        db.check_connection = AsyncMock(return_value=True)
        db.verify_pgvector_extension = AsyncMock(return_value=True)
        db.execute_query = AsyncMock(side_effect=[
            [{"table_name": "embeddings"}, {"table_name": "documents"}],  # verify_tables_exist
            [{"indexname": "idx_embeddings_embedding_ivfflat"}],  # check indexes
        ])
        
        result = await verify_setup(db)
        
        assert result["connection"] is True
        assert result["pgvector_extension"] is True
        assert result["tables"]["embeddings"] is True
        assert result["tables"]["documents"] is True
        assert result["indexes"]["embeddings_embedding"] is True

    @pytest.mark.asyncio
    async def test_verify_setup_connection_failure(self, mock_db):
        """Test verify_setup with connection failure."""
        db, _, _ = mock_db
        db.check_connection = AsyncMock(return_value=False)
        
        result = await verify_setup(db)
        
        assert result["connection"] is False
        assert result["pgvector_extension"] is False

    @pytest.mark.asyncio
    async def test_verify_setup_no_indexes(self, mock_db):
        """Test verify_setup when no indexes exist."""
        db, _, _ = mock_db
        db.check_connection = AsyncMock(return_value=True)
        db.verify_pgvector_extension = AsyncMock(return_value=True)
        db.execute_query = AsyncMock(side_effect=[
            [{"table_name": "embeddings"}, {"table_name": "documents"}],  # verify_tables_exist
            [],  # check indexes - no indexes
        ])
        
        result = await verify_setup(db)
        
        assert result["indexes"]["embeddings_embedding"] is False

    @pytest.mark.asyncio
    async def test_verify_setup_index_check_exception(self, mock_db):
        """Test verify_setup when index check fails."""
        db, _, _ = mock_db
        db.check_connection = AsyncMock(return_value=True)
        db.verify_pgvector_extension = AsyncMock(return_value=True)
        db.execute_query = AsyncMock(side_effect=[
            [{"table_name": "embeddings"}, {"table_name": "documents"}],  # verify_tables_exist
            Exception("Index check error"),  # check indexes - exception
        ])
        
        result = await verify_setup(db)
        
        assert "error" in result["indexes"]

    @pytest.mark.asyncio
    async def test_setup_database_complete(self, mock_db):
        """Test setup_database with complete setup."""
        db, _, _ = mock_db
        db.check_connection = AsyncMock(return_value=True)
        db.create_pgvector_extension = AsyncMock(return_value=True)
        db.execute_query = AsyncMock(return_value=None)
        
        # Mock VectorIndexManager
        mock_index_manager = MagicMock()
        mock_index_manager.create_index = AsyncMock(return_value="idx_embeddings_embedding_ivfflat")
        
        with patch("src.core.postgresql_database.vector_index_manager.VectorIndexManager") as mock_manager_class:
            mock_manager_class.return_value = mock_index_manager
            result = await setup_database(db)
            
            assert result["connection"] is True
            assert result["pgvector_extension"] is True
            assert result["embeddings_table"] is True
            assert result["documents_table"] is True
            assert result["vector_indexes"] is True

    @pytest.mark.asyncio
    async def test_setup_database_verify_only(self, mock_db):
        """Test setup_database with verify_only mode."""
        db, _, _ = mock_db
        db.check_connection = AsyncMock(return_value=True)
        db.verify_pgvector_extension = AsyncMock(return_value=True)
        db.execute_query = AsyncMock(side_effect=[
            [{"table_name": "embeddings"}, {"table_name": "documents"}],  # verify_tables_exist
            [{"count": 1}],  # check indexes
        ])
        
        config = {
            "create_extension": False,
            "create_tables": False,
            "create_indexes": False,
        }
        
        result = await setup_database(db, config=config)
        
        assert result["connection"] is True
        assert result["pgvector_extension"] is True
        assert result["embeddings_table"] is True
        assert result["documents_table"] is True
        # Indexes should be verified, not created
        assert "vector_indexes" in result

    @pytest.mark.asyncio
    async def test_setup_database_connection_failure(self, mock_db):
        """Test setup_database with connection failure."""
        db, _, _ = mock_db
        db.check_connection = AsyncMock(return_value=False)
        
        result = await setup_database(db)
        
        assert result["connection"] is False
        assert result["pgvector_extension"] is False

    @pytest.mark.asyncio
    async def test_setup_database_extension_missing(self, mock_db):
        """Test setup_database when extension is missing."""
        db, _, _ = mock_db
        db.check_connection = AsyncMock(return_value=True)
        db.create_pgvector_extension = AsyncMock(return_value=False)
        
        result = await setup_database(db)
        
        assert result["connection"] is True
        assert result["pgvector_extension"] is False
        # Should not proceed with table creation
        assert result["embeddings_table"] is False

    @pytest.mark.asyncio
    async def test_setup_database_custom_config(self, mock_db):
        """Test setup_database with custom configuration."""
        db, _, _ = mock_db
        db.check_connection = AsyncMock(return_value=True)
        db.create_pgvector_extension = AsyncMock(return_value=True)
        db.execute_query = AsyncMock(return_value=None)
        
        # Mock VectorIndexManager
        mock_index_manager = MagicMock()
        mock_index_manager.create_index = AsyncMock(return_value="idx_embeddings_embedding_hnsw")
        
        config = {
            "dimension": 768,
            "index_type": "hnsw",
        }
        
        with patch("src.core.postgresql_database.vector_index_manager.VectorIndexManager") as mock_manager_class:
            mock_manager_class.return_value = mock_index_manager
            result = await setup_database(db, config=config)
            
            assert result["vector_indexes"] is True
            # Verify custom dimension was used
            call_args = db.execute_query.call_args_list
            embeddings_call = [c for c in call_args if "vector(768)" in str(c)][0]
            assert embeddings_call is not None

    @pytest.mark.asyncio
    async def test_setup_database_exception(self, mock_db):
        """Test setup_database with exception."""
        db, _, _ = mock_db
        db.check_connection = AsyncMock(side_effect=Exception("Setup error"))
        
        result = await setup_database(db)
        
        assert result.get("error") is True
        assert "message" in result

    @pytest.mark.asyncio
    async def test_setup_database_with_otel(self, mock_db):
        """Test setup_database with OTEL integration."""
        db, _, _ = mock_db
        db.check_connection = AsyncMock(return_value=True)
        db.create_pgvector_extension = AsyncMock(return_value=True)
        db.execute_query = AsyncMock(return_value=None)
        
        # Mock OTEL tracer
        mock_tracer = MagicMock()
        mock_trace = MagicMock()
        mock_trace.set_attribute = MagicMock()
        mock_tracer.start_trace = MagicMock(return_value=mock_trace)
        mock_trace.__enter__ = MagicMock(return_value=mock_trace)
        mock_trace.__exit__ = MagicMock(return_value=None)
        
        # Mock VectorIndexManager
        mock_index_manager = MagicMock()
        mock_index_manager.create_index = AsyncMock(return_value="idx_embeddings_embedding_ivfflat")
        
        with patch("src.core.otel_integration.create_otel_tracer", return_value=mock_tracer):
            with patch("src.core.postgresql_database.vector_index_manager.VectorIndexManager") as mock_manager_class:
                mock_manager_class.return_value = mock_index_manager
                result = await setup_database(db)
                
                assert result["connection"] is True
                mock_trace.set_attribute.assert_called()

    @pytest.mark.asyncio
    async def test_verify_tables_exist_with_otel(self, mock_db):
        """Test verify_tables_exist with OTEL integration."""
        db, _, _ = mock_db
        db.execute_query = AsyncMock(return_value=[
            {"table_name": "embeddings"},
            {"table_name": "documents"},
        ])
        
        # Mock OTEL tracer
        mock_tracer = MagicMock()
        mock_trace = MagicMock()
        mock_trace.set_attribute = MagicMock()
        mock_tracer.start_trace = MagicMock(return_value=mock_trace)
        mock_trace.__enter__ = MagicMock(return_value=mock_trace)
        mock_trace.__exit__ = MagicMock(return_value=None)
        
        with patch("src.core.otel_integration.create_otel_tracer", return_value=mock_tracer):
            result = await verify_tables_exist(db)
            
            assert result["embeddings"] is True
            assert result["documents"] is True
            mock_trace.set_attribute.assert_called()

    @pytest.mark.asyncio
    async def test_verify_setup_with_otel(self, mock_db):
        """Test verify_setup with OTEL integration."""
        db, _, _ = mock_db
        db.check_connection = AsyncMock(return_value=True)
        db.verify_pgvector_extension = AsyncMock(return_value=True)
        db.execute_query = AsyncMock(side_effect=[
            [{"table_name": "embeddings"}, {"table_name": "documents"}],
            [{"indexname": "idx_embeddings_embedding_ivfflat"}],
        ])
        
        # Mock OTEL tracer
        mock_tracer = MagicMock()
        mock_trace = MagicMock()
        mock_trace.set_attribute = MagicMock()
        mock_tracer.start_trace = MagicMock(return_value=mock_trace)
        mock_trace.__enter__ = MagicMock(return_value=mock_trace)
        mock_trace.__exit__ = MagicMock(return_value=None)
        
        with patch("src.core.otel_integration.create_otel_tracer", return_value=mock_tracer):
            result = await verify_setup(db)
            
            assert result["connection"] is True
            mock_trace.set_attribute.assert_called()

    @pytest.mark.asyncio
    async def test_setup_vector_indexes_with_otel(self, mock_db):
        """Test setup_vector_indexes with OTEL integration."""
        db, _, _ = mock_db
        
        # Mock VectorIndexManager
        mock_index_manager = MagicMock()
        mock_index_manager.create_index = AsyncMock(return_value="idx_embeddings_embedding_ivfflat")
        
        # Mock OTEL tracer
        mock_tracer = MagicMock()
        mock_trace = MagicMock()
        mock_trace.set_attribute = MagicMock()
        mock_tracer.start_trace = MagicMock(return_value=mock_trace)
        mock_trace.__enter__ = MagicMock(return_value=mock_trace)
        mock_trace.__exit__ = MagicMock(return_value=None)
        
        with patch("src.core.otel_integration.create_otel_tracer", return_value=mock_tracer):
            with patch("src.core.postgresql_database.vector_index_manager.VectorIndexManager") as mock_manager_class:
                mock_manager_class.return_value = mock_index_manager
                result = await setup_vector_indexes(db)
                
                assert result is True
                mock_trace.set_attribute.assert_called()

    @pytest.mark.asyncio
    async def test_create_documents_table_with_otel(self, mock_db):
        """Test create_documents_table with OTEL integration."""
        db, _, _ = mock_db
        db.execute_query = AsyncMock(return_value=None)
        
        # Mock OTEL tracer
        mock_tracer = MagicMock()
        mock_trace = MagicMock()
        mock_trace.set_attribute = MagicMock()
        mock_tracer.start_trace = MagicMock(return_value=mock_trace)
        mock_trace.__enter__ = MagicMock(return_value=mock_trace)
        mock_trace.__exit__ = MagicMock(return_value=None)
        
        with patch("src.core.otel_integration.create_otel_tracer", return_value=mock_tracer):
            result = await create_documents_table(db)
            
            assert result is True
            mock_trace.set_attribute.assert_called()

    @pytest.mark.asyncio
    async def test_verify_pgvector_extension_with_otel(self, mock_db):
        """Test verify_pgvector_extension with OTEL integration."""
        db, _, _ = mock_db
        db.verify_pgvector_extension = AsyncMock(return_value=True)
        
        # Mock OTEL tracer
        mock_tracer = MagicMock()
        mock_trace = MagicMock()
        mock_trace.set_attribute = MagicMock()
        mock_tracer.start_trace = MagicMock(return_value=mock_trace)
        mock_trace.__enter__ = MagicMock(return_value=mock_trace)
        mock_trace.__exit__ = MagicMock(return_value=None)
        
        with patch("src.core.otel_integration.create_otel_tracer", return_value=mock_tracer):
            result = await verify_pgvector_extension(db)
            
            assert result is True
            mock_trace.set_attribute.assert_called()

    @pytest.mark.asyncio
    async def test_setup_database_no_indexes_when_table_missing(self, mock_db):
        """Test setup_database skips indexes when embeddings table is missing."""
        db, _, _ = mock_db
        db.check_connection = AsyncMock(return_value=True)
        db.create_pgvector_extension = AsyncMock(return_value=True)
        db.execute_query = AsyncMock(side_effect=[
            None,  # create_embeddings_table - fails
            None,  # create_documents_table
            [{"table_name": "documents"}],  # verify_tables_exist - embeddings missing
        ])
        
        # Mock create_embeddings_table to return False
        with patch("src.core.postgresql_database.setup.create_embeddings_table", return_value=False):
            result = await setup_database(db)
            
            assert result["embeddings_table"] is False
            # Indexes should not be created if embeddings table is missing
            assert result["vector_indexes"] is False

