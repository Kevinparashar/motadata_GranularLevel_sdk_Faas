"""
Mock Database Connection Implementation

Mock implementation of DatabaseConnection for testing.
"""

from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock


class MockDatabaseConnection:
    """
    Mock implementation of DatabaseConnection for testing.
    
    Provides a mock database connection that can be used in tests
    without requiring an actual PostgreSQL database.
    """

    def __init__(self, config: Optional[Any] = None):
        """
        Initialize mock database connection.
        
        Args:
            config: Optional database configuration (not used in mock)
        """
        self.config = config
        self.pool = MagicMock()
        self._mock_data: Dict[str, List[Dict[str, Any]]] = {}
        self._connected = False

    async def connect(self) -> None:
        """Mock connect method - simulates database connection."""
        self._connected = True

    async def disconnect(self) -> None:
        """Mock disconnect method - simulates database disconnection."""
        self._connected = False

    async def execute_query(
        self,
        query: str,
        parameters: Optional[tuple] = None,
        tenant_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Mock execute_query method.
        
        Args:
            query: SQL query string
            parameters: Query parameters
            tenant_id: Optional tenant ID
            
        Returns:
            Mock query results
        """
        # Simple mock implementation - returns empty list by default
        # Tests can override this behavior
        return self._mock_data.get(query, [])

    async def execute_update(
        self,
        query: str,
        parameters: Optional[tuple] = None,
        tenant_id: Optional[str] = None,
    ) -> int:
        """
        Mock execute_update method.
        
        Args:
            query: SQL update query
            parameters: Query parameters
            tenant_id: Optional tenant ID
            
        Returns:
            Number of affected rows (mock)
        """
        return 1  # Mock: always returns 1 affected row

    def set_mock_data(self, query: str, data: List[Dict[str, Any]]) -> None:
        """
        Set mock data for a specific query.
        
        Args:
            query: Query string to mock
            data: Mock data to return
        """
        self._mock_data[query] = data

    def clear_mock_data(self) -> None:
        """Clear all mock data."""
        self._mock_data.clear()


__all__ = ["MockDatabaseConnection"]

