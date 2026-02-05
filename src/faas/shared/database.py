"""
Database connection utilities for FaaS services.
"""


from typing import Optional
from urllib.parse import urlparse

from ...core.postgresql_database import DatabaseConfig, DatabaseConnection


def _parse_database_url(database_url: str) -> DatabaseConfig:
    """
    Parse database URL and create DatabaseConfig.
    
    Args:
        database_url: PostgreSQL connection URL (e.g., postgresql://user:pass@host:port/dbname)
    
    Returns:
        DatabaseConfig instance
    """
    parsed = urlparse(database_url)
    
    # Extract port
    port = parsed.port or 5432
    
    # Extract password (may contain special characters)
    password = parsed.password or ""
    
    return DatabaseConfig(
        host=parsed.hostname or "localhost",
        port=port,
        database=parsed.path.lstrip("/") if parsed.path else "ai_app",
        user=parsed.username or "postgres",
        password=password,
    )


class DatabaseManager:
    """Database connection manager."""

    def __init__(self, database_url: str):
        """
        Initialize database manager.
        
        Args:
            database_url: PostgreSQL connection URL
        """
        self.database_url = database_url
        self._connection: Optional[DatabaseConnection] = None

    def get_connection(self) -> DatabaseConnection:
        """
        Get database connection (creates if not exists).
        
        Note: Connection pool is created lazily on first use via execute_query().
        This method only creates the DatabaseConnection instance.
        
        Returns:
            DatabaseConnection instance
        """
        if self._connection is None:
            config = _parse_database_url(self.database_url)
            self._connection = DatabaseConnection(config)
            # Connection pool will be created lazily on first async operation
            # via DatabaseConnection.execute_query() which calls connect() if needed
        return self._connection

    async def close(self):
        """
        Close database connection.
        
        Note: This should be called from an async context (e.g., FastAPI shutdown event).
        
        Returns:
            None: Result of the operation.
        """
        if self._connection:
            await self._connection.close()
            self._connection = None


_db_manager: Optional[DatabaseManager] = None


def get_database_connection(database_url: Optional[str] = None) -> DatabaseManager:
    """
    Get database connection manager.

    Args:
        database_url: Database connection URL (optional if config is loaded)

    Returns:
        DatabaseManager instance
    """
    global _db_manager

    if _db_manager is None:
        if database_url is None:
            from .config import get_config

            config = get_config()
            database_url = config.database_url

        _db_manager = DatabaseManager(database_url)

    return _db_manager
