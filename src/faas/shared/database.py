"""
Database connection utilities for FaaS services.
"""

from typing import Any, Optional

from ..core.postgresql_database import DatabaseConnection, create_database_connection


class DatabaseManager:
    """Database connection manager."""

    def __init__(self, database_url: str):
        """
        Initialize database manager.

        Args:
            database_url: Database connection URL
        """
        self.database_url = database_url
        self._connection: Optional[DatabaseConnection] = None

    async def get_connection(self) -> DatabaseConnection:
        """
        Get database connection (creates if not exists).

        Returns:
            Database connection instance
        """
        if self._connection is None:
            self._connection = await create_database_connection(self.database_url)
        return self._connection

    async def close(self):
        """Close database connection."""
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

