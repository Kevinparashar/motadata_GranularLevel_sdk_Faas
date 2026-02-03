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
    def load_from_csv(filepath: str) -> Any:
        """
        Load data from CSV file.
        
        Args:
            filepath (str): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            ImportError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        if not _pandas_available:
            raise ImportError(
                "pandas is required for CSV loading. "
                "Install it with: pip install pandas"
            )
        assert pd is not None
        return pd.read_csv(filepath)

    @staticmethod
    def load_from_json(filepath: str) -> Any:
        """
        Load data from JSON file.
        
        Args:
            filepath (str): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        """
        import json

        with open(filepath, "r") as f:
            return json.load(f)

    @staticmethod
    def load_from_database(db: Any, query: str, params: Optional[tuple] = None) -> Any:
        """
        Load data from database.
        
        Args:
            db (Any): Database connection/handle.
            query (str): Input parameter for this operation.
            params (Optional[tuple]): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            ImportError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        if not _pandas_available:
            raise ImportError(
                "pandas is required for database loading. "
                "Install it with: pip install pandas"
            )
        assert pd is not None
        return pd.read_sql_query(query, db, params=params)
