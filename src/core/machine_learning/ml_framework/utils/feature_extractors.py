"""
Feature Extractors

Utilities for extracting features from raw data.
"""


import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

try:
    import pandas as pd  # type: ignore[import-untyped]

    _pandas_available = True
except ImportError:
    _pandas_available = False
    pd = None


class FeatureExtractor:
    """
    Utility class for feature extraction.

    Provides common feature extraction methods for ITSM domain data.
    """

    @staticmethod
    def extract_text_features(
        text: str, include_length: bool = True, include_word_count: bool = True
    ) -> Dict[str, float]:
        """
        Extract basic features from text.
        
        Args:
            text (str): Input parameter for this operation.
            include_length (bool): Input parameter for this operation.
            include_word_count (bool): Input parameter for this operation.
        
        Returns:
            Dict[str, float]: Dictionary result of the operation.
        """
        features = {}

        if include_length:
            features["char_length"] = len(text)

        if include_word_count:
            features["word_count"] = len(text.split())

        return features

    @staticmethod
    def extract_datetime_features(
        datetime_value: Any, include_hour: bool = True, include_day_of_week: bool = True
    ) -> Dict[str, float]:
        """
        Extract features from datetime.
        
        Args:
            datetime_value (Any): Input parameter for this operation.
            include_hour (bool): Input parameter for this operation.
            include_day_of_week (bool): Input parameter for this operation.
        
        Returns:
            Dict[str, float]: Dictionary result of the operation.
        
        Raises:
            ImportError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        if not _pandas_available:
            raise ImportError(
                "pandas is required for datetime feature extraction. "
                "Install it with: pip install pandas"
            )

        assert pd is not None
        features = {}
        dt = pd.to_datetime(datetime_value)

        if include_hour:
            features["hour"] = dt.hour

        if include_day_of_week:
            features["day_of_week"] = dt.dayofweek

        features["month"] = dt.month
        features["year"] = dt.year

        return features

    @staticmethod
    def extract_categorical_features(data: Any, categorical_columns: List[str]) -> Any:
        """
        Extract features from categorical columns (one-hot encoding).
        
        Args:
            data (Any): Input parameter for this operation.
            categorical_columns (List[str]): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            ImportError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        if not _pandas_available:
            raise ImportError(
                "pandas is required for categorical feature extraction. "
                "Install it with: pip install pandas"
            )

        assert pd is not None
        return pd.get_dummies(data, columns=categorical_columns, prefix=categorical_columns)
