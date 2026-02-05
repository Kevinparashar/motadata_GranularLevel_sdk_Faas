"""
Data Loader

Loads data from various sources.
"""


import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    import pandas as pd  # type: ignore[import-untyped]

    _pandas_available = True
except ImportError:
    _pandas_available = False
    pd = None


class DataLoader:
    """Loads data from various sources."""

    @staticmethod
    async def load_from_csv(filepath: str) -> Any:
        """
        Load data from CSV file asynchronously.
        
        Args:
            filepath (str): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            ImportError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        import asyncio
        
        if not _pandas_available:
            raise ImportError(
                "pandas is required for CSV loading. "
                "Install it with: pip install pandas"
            )
        assert pd is not None
        
        # Run pandas I/O in thread pool to avoid blocking
        return await asyncio.to_thread(pd.read_csv, filepath)

    @staticmethod
    async def load_from_json(filepath: str) -> Any:
        """
        Load data from JSON file asynchronously.
        
        Args:
            filepath (str): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        """
        import asyncio
        import json

        def _load_sync() -> Any:
            with open(filepath, "r") as f:
                return json.load(f)
        
        # Run file I/O in thread pool to avoid blocking
        return await asyncio.to_thread(_load_sync)

    @staticmethod
    async def load_from_database(db: Any, query: str, params: Optional[tuple] = None) -> Any:
        """
        Load data from database asynchronously.
        
        Args:
            db (Any): Database connection/handle (should be async DatabaseConnection).
            query (str): Input parameter for this operation.
            params (Optional[tuple]): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            ImportError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        import asyncio
        
        if not _pandas_available:
            raise ImportError(
                "pandas is required for database loading. "
                "Install it with: pip install pandas"
            )
        assert pd is not None
        
        # If db is async DatabaseConnection, use async query
        if hasattr(db, 'execute_query') and asyncio.iscoroutinefunction(db.execute_query):
            result = await db.execute_query(query, params, fetch_all=True)
            # Convert result to DataFrame
            return await asyncio.to_thread(pd.DataFrame, result)
        else:
            # Fallback for sync database connections
            return await asyncio.to_thread(pd.read_sql_query, query, db, params=params)
