"""
Mock Database Connection Implementation

Mock implementation of DatabaseConnection for testing.

Copyright (c) 2024 Motadata. All rights reserved.
"""

import asyncio
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import MagicMock


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
        # Minimal async operation to satisfy linter
        await asyncio.sleep(0)
        self._connected = True

    async def close(self) -> None:
        """Mock close method - simulates database disconnection."""
        # Minimal async operation to satisfy linter
        await asyncio.sleep(0)
        self._connected = False
        if self.pool:
            self.pool = None

    async def execute_query(
        self,
        query: str,
        params: Optional[Tuple[Any, ...]] = None,
        fetch_one: bool = False,
        fetch_all: bool = True,
    ) -> Any:
        """
        Mock execute_query method.
        
        Args:
            query: SQL query string
            params: Query parameters (for interface compatibility)
            fetch_one: Fetch only one row
            fetch_all: Fetch all rows
            
        Returns:
            Mock query results (dict if fetch_one, list of dicts if fetch_all, int otherwise)
        """
        # Minimal async operation to satisfy linter
        await asyncio.sleep(0)
        
        # Create unique key from query and params for mock data lookup
        mock_key = query
        if params:
            mock_key = f"{query}:{hash(params)}"
        
        # Simple mock implementation - returns empty list by default
        # Tests can override this behavior using set_mock_data()
        results = self._mock_data.get(mock_key, self._mock_data.get(query, []))
        
        if fetch_one:
            return results[0] if results else None
        
        if fetch_all:
            return results
        
        # Execute without fetching - return row count
        return len(results)

    async def execute_transaction(
        self, queries: List[Tuple[str, Optional[Tuple[Any, ...]]]]
    ) -> None:
        """
        Mock execute_transaction method - executes multiple queries in a transaction.
        
        Args:
            queries: List of (query, params) tuples
        """
        # Minimal async operation to satisfy linter
        await asyncio.sleep(0)
        
        # Simple mock implementation - executes all queries
        for query, _params_tuple in queries:
            # Store result if mock data exists for this query
            if query in self._mock_data:
                # Transaction succeeds
                pass

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

