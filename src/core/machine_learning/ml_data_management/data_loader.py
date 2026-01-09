"""
Data Loader

Loads data from various sources.
"""

from typing import Any, Optional
import logging
import pandas as pd

logger = logging.getLogger(__name__)


class DataLoader:
    """Loads data from various sources."""
    
    @staticmethod
    def load_from_csv(filepath: str) -> pd.DataFrame:
        """Load data from CSV file."""
        return pd.read_csv(filepath)
    
    @staticmethod
    def load_from_json(filepath: str) -> Any:
        """Load data from JSON file."""
        import json
        with open(filepath, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def load_from_database(
        db: Any,
        query: str,
        params: Optional[tuple] = None
    ) -> pd.DataFrame:
        """Load data from database."""
        return pd.read_sql_query(query, db, params=params)


