"""
Unit tests for FaaS Database utilities.
"""

import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Mock ml_service module before any imports to avoid numpy dependency
ml_service_mock = MagicMock()
ml_service_mock.MLService = MagicMock
ml_service_mock.create_ml_service = MagicMock
sys.modules['src.faas.services.ml_service'] = ml_service_mock

from src.faas.shared.database import (
    DatabaseManager,
    _parse_database_url,
    get_database_connection,
)


class TestParseDatabaseURL:
    """Test _parse_database_url function."""

    def test_parse_database_url_full(self):
        """Test parsing full database URL - covers lines 22-30."""
        # Password is part of URL parsing test, not a security issue in test code
        url = "postgresql://user:testpass@localhost:5432/testdb"  # noqa: S105
        config = _parse_database_url(url)
        
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "testdb"
        assert config.user == "user"
        assert config.password == "testpass"

    def test_parse_database_url_minimal(self):
        """Test parsing minimal database URL - covers default values."""
        url = "postgresql://localhost/dbname"
        config = _parse_database_url(url)
        
        assert config.host == "localhost"
        assert config.port == 5432  # Default port
        assert config.database == "dbname"
        assert config.user == "postgres"  # Default user
        assert config.password == ""  # Default password

    def test_parse_database_url_no_path(self):
        """Test parsing URL without path - covers line 33."""
        url = "postgresql://user:pass@host:5432"  # noqa: S105
        config = _parse_database_url(url)
        
        assert config.database == "ai_app"  # Default database
        assert config.host == "host"
        assert config.port == 5432

    def test_parse_database_url_no_port(self):
        """Test parsing URL without port - covers line 25."""
        url = "postgresql://user:pass@host/dbname"  # noqa: S105
        config = _parse_database_url(url)
        
        assert config.port == 5432  # Default port
        assert config.host == "host"

    def test_parse_database_url_no_password(self):
        """Test parsing URL without password - covers line 28."""
        # Password is not in URL, testing default behavior
        url = "postgresql://user@host:5432/dbname"  # noqa: S105, S2115
        config = _parse_database_url(url)
        
        assert config.password == ""  # Default password
        assert config.user == "user"

    def test_parse_database_url_no_username(self):
        """Test parsing URL without username - covers line 34."""
        url = "postgresql://host:5432/dbname"
        config = _parse_database_url(url)
        
        assert config.user == "postgres"  # Default user
        assert config.host == "host"


class TestDatabaseManager:
    """Test DatabaseManager class."""

    def test_initialization(self):
        """Test DatabaseManager initialization - covers lines 42-50."""
        url = "postgresql://user:pass@host:5432/dbname"  # noqa: S105
        manager = DatabaseManager(url)
        
        assert manager.database_url == url
        assert manager._connection is None

    def test_get_connection_first_call(self):
        """Test get_connection first call - covers lines 62-67."""
        url = "postgresql://user:pass@host:5432/dbname"  # noqa: S105
        manager = DatabaseManager(url)
        
        with patch("src.faas.shared.database.DatabaseConnection") as mock_db_conn:
            mock_connection = Mock()
            mock_db_conn.return_value = mock_connection
            
            connection = manager.get_connection()
            
            assert connection is not None
            assert manager._connection is not None
            mock_db_conn.assert_called_once()

    def test_get_connection_cached(self):
        """Test get_connection returns cached connection - covers line 67."""
        url = "postgresql://user:pass@host:5432/dbname"  # noqa: S105
        manager = DatabaseManager(url)
        
        with patch("src.faas.shared.database.DatabaseConnection") as mock_db_conn:
            mock_connection = Mock()
            mock_db_conn.return_value = mock_connection
            
            # First call
            connection1 = manager.get_connection()
            # Second call should return cached connection
            connection2 = manager.get_connection()
            
            assert connection1 is connection2
            assert mock_db_conn.call_count == 1  # Should only be called once

    @pytest.mark.asyncio
    async def test_close_with_connection(self):
        """Test close with existing connection - covers lines 78-80."""
        url = "postgresql://user:pass@host:5432/dbname"  # noqa: S105
        manager = DatabaseManager(url)
        
        # Create a mock connection
        mock_connection = Mock()
        mock_connection.close = AsyncMock()
        manager._connection = mock_connection
        
        await manager.close()
        
        mock_connection.close.assert_called_once()
        assert manager._connection is None

    @pytest.mark.asyncio
    async def test_close_without_connection(self):
        """Test close without existing connection - covers line 78."""
        url = "postgresql://user:pass@host:5432/dbname"  # noqa: S105
        manager = DatabaseManager(url)
        
        # Should not raise error when no connection exists
        await manager.close()
        
        assert manager._connection is None


class TestGetDatabaseConnection:
    """Test get_database_connection function."""

    def test_get_database_connection_with_url(self):
        """Test get_database_connection with URL - covers lines 98-105."""
        url = "postgresql://user:pass@host:5432/dbname"  # noqa: S105
        
        # Reset global state
        import src.faas.shared.database as db_module
        db_module._db_manager = None
        
        manager = get_database_connection(database_url=url)
        
        assert manager is not None
        assert isinstance(manager, DatabaseManager)
        assert manager.database_url == url

    def test_get_database_connection_without_url(self):
        """Test get_database_connection without URL - covers lines 99-103."""
        # Reset global state
        import src.faas.shared.database as db_module
        db_module._db_manager = None
        
        # Patch the config module import that happens inside the function
        with patch("src.faas.shared.config.get_config") as mock_get_config:
            mock_config = Mock()
            mock_config.database_url = "postgresql://default:pass@host:5432/db"  # noqa: S105
            mock_get_config.return_value = mock_config
            
            manager = get_database_connection(database_url=None)
            
            assert manager is not None
            assert isinstance(manager, DatabaseManager)
            mock_get_config.assert_called_once()

    def test_get_database_connection_cached(self):
        """Test get_database_connection returns cached manager - covers line 107."""
        url = "postgresql://user:pass@host:5432/dbname"  # noqa: S105
        
        # Reset global state
        import src.faas.shared.database as db_module
        db_module._db_manager = None
        
        # First call
        manager1 = get_database_connection(database_url=url)
        # Second call should return cached manager
        manager2 = get_database_connection(database_url=url)
        
        assert manager1 is manager2

    def test_get_database_connection_different_urls(self):
        """Test get_database_connection with different URLs - covers caching behavior."""
        url1 = "postgresql://user1:pass@host1:5432/db1"  # noqa: S105
        url2 = "postgresql://user2:pass@host2:5432/db2"  # noqa: S105
        
        # Reset global state
        import src.faas.shared.database as db_module
        db_module._db_manager = None
        
        # First call
        manager1 = get_database_connection(database_url=url1)
        # Second call with different URL should still return cached manager
        # (because caching is based on global state, not URL)
        manager2 = get_database_connection(database_url=url2)
        
        # The manager is cached globally, so it will be the same
        assert manager1 is manager2
        # But the URL in the manager is from the first call
        assert manager1.database_url == url1

