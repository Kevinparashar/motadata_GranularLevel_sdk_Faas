"""
Unit tests for FaaS shared database utilities.
"""


from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.faas.shared.database import (
    DatabaseManager,
    _parse_database_url,
    get_database_connection,
)


class TestParseDatabaseUrl:
    """Test _parse_database_url function."""

    def test_parse_full_url(self):
        """Test parsing a full database URL."""
        url = "postgresql://user:password@localhost:5432/mydb"
        config = _parse_database_url(url)

        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "mydb"
        assert config.user == "user"
        assert config.password == "password"

    def test_parse_url_without_port(self):
        """Test parsing URL without explicit port."""
        url = "postgresql://user:pass@example.com/mydb"
        config = _parse_database_url(url)

        assert config.host == "example.com"
        assert config.port == 5432  # Default port
        assert config.database == "mydb"
        assert config.user == "user"
        assert config.password == "pass"

    def test_parse_url_without_password(self):
        """Test parsing URL without password."""
        url = "postgresql://user@localhost/mydb"
        config = _parse_database_url(url)

        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "mydb"
        assert config.user == "user"
        assert config.password == ""

    def test_parse_url_without_user(self):
        """Test parsing URL without username."""
        url = "postgresql://localhost:5432/mydb"
        config = _parse_database_url(url)

        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "mydb"
        assert config.user == "postgres"  # Default user
        assert config.password == ""

    def test_parse_url_without_database(self):
        """Test parsing URL without database name."""
        url = "postgresql://user:pass@localhost:5432"
        config = _parse_database_url(url)

        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "ai_app"  # Default database
        assert config.user == "user"
        assert config.password == "pass"

    def test_parse_url_without_hostname(self):
        """Test parsing URL without hostname."""
        url = "postgresql://user:pass@:5432/mydb"
        config = _parse_database_url(url)

        assert config.host == "localhost"  # Default host
        assert config.port == 5432
        assert config.database == "mydb"
        assert config.user == "user"
        assert config.password == "pass"

    def test_parse_url_with_special_characters_in_password(self):
        """Test parsing URL with special characters in password (URL-encoded)."""
        # URL-encode special characters: @ becomes %40, ! becomes %21, # becomes %23, $ becomes %24
        url = "postgresql://user:p%40ssw0rd%21%23%24@localhost:5432/mydb"
        config = _parse_database_url(url)

        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "mydb"
        assert config.user == "user"
        # Password is stored as-is from urlparse (not decoded)
        assert config.password == "p%40ssw0rd%21%23%24"

    def test_parse_url_with_path_leading_slash(self):
        """Test parsing URL with leading slash in path."""
        url = "postgresql://user:pass@localhost:5432//mydb"
        config = _parse_database_url(url)

        assert config.database == "mydb"  # Leading slash should be stripped


class TestDatabaseManager:
    """Test DatabaseManager class."""

    def test_init(self):
        """Test DatabaseManager initialization."""
        url = "postgresql://user:pass@localhost:5432/mydb"
        manager = DatabaseManager(url)

        assert manager.database_url == url
        assert manager._connection is None

    def test_get_connection_creates_new(self):
        """Test get_connection creates new connection when none exists."""
        url = "postgresql://user:pass@localhost:5432/mydb"
        manager = DatabaseManager(url)

        with patch("src.faas.shared.database.DatabaseConnection") as mock_db_conn:
            mock_connection = MagicMock()
            mock_db_conn.return_value = mock_connection

            connection = manager.get_connection()

            assert connection == mock_connection
            assert manager._connection == mock_connection
            mock_db_conn.assert_called_once()

    def test_get_connection_returns_existing(self):
        """Test get_connection returns existing connection."""
        url = "postgresql://user:pass@localhost:5432/mydb"
        manager = DatabaseManager(url)

        with patch("src.faas.shared.database.DatabaseConnection") as mock_db_conn:
            mock_connection = MagicMock()
            mock_db_conn.return_value = mock_connection

            # First call creates connection
            connection1 = manager.get_connection()
            # Second call returns existing
            connection2 = manager.get_connection()

            assert connection1 == connection2
            assert connection1 == mock_connection
            # DatabaseConnection should only be called once
            assert mock_db_conn.call_count == 1

    @pytest.mark.asyncio
    async def test_close_with_connection(self):
        """Test close when connection exists."""
        url = "postgresql://user:pass@localhost:5432/mydb"
        manager = DatabaseManager(url)

        mock_connection = AsyncMock()
        manager._connection = mock_connection

        await manager.close()

        mock_connection.close.assert_called_once()
        assert manager._connection is None

    @pytest.mark.asyncio
    async def test_close_without_connection(self):
        """Test close when no connection exists."""
        url = "postgresql://user:pass@localhost:5432/mydb"
        manager = DatabaseManager(url)

        # Should not raise an error
        await manager.close()

        assert manager._connection is None


class TestGetDatabaseConnection:
    """Test get_database_connection function."""

    def test_get_database_connection_with_url(self):
        """Test get_database_connection with explicit URL."""
        url = "postgresql://user:pass@localhost:5432/mydb"

        # Reset global state
        import src.faas.shared.database as db_module
        db_module._db_manager = None

        manager = get_database_connection(database_url=url)

        assert isinstance(manager, DatabaseManager)
        assert manager.database_url == url

    def test_get_database_connection_without_url_uses_config(self):
        """Test get_database_connection without URL uses config."""
        # Reset global state
        import src.faas.shared.database as db_module
        db_module._db_manager = None

        mock_config = MagicMock()
        mock_config.database_url = "postgresql://config:pass@host:5432/db"

        # Patch get_config at the config module level since it's imported inside the function
        with patch("src.faas.shared.config.get_config", return_value=mock_config):
            manager = get_database_connection()

            assert isinstance(manager, DatabaseManager)
            assert manager.database_url == mock_config.database_url

    def test_get_database_connection_returns_singleton(self):
        """Test get_database_connection returns same instance."""
        url = "postgresql://user:pass@localhost:5432/mydb"

        # Reset global state
        import src.faas.shared.database as db_module
        db_module._db_manager = None

        manager1 = get_database_connection(database_url=url)
        manager2 = get_database_connection(database_url=url)

        assert manager1 is manager2

    def test_get_database_connection_with_url_after_singleton_created(self):
        """Test get_database_connection ignores URL if singleton already exists."""
        url1 = "postgresql://user1:pass@localhost:5432/db1"
        url2 = "postgresql://user2:pass@localhost:5432/db2"

        # Reset global state
        import src.faas.shared.database as db_module
        db_module._db_manager = None

        manager1 = get_database_connection(database_url=url1)
        # Second call with different URL should return same manager
        manager2 = get_database_connection(database_url=url2)

        assert manager1 is manager2
        assert manager1.database_url == url1  # Original URL is preserved

