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
            text: Input text
            include_length: Include character length
            include_word_count: Include word count

        Returns:
            Dictionary of extracted features
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
            datetime_value: Datetime value
            include_hour: Include hour of day
            include_day_of_week: Include day of week

        Returns:
            Dictionary of extracted features
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
            data: Input DataFrame
            categorical_columns: List of categorical column names

        Returns:
            DataFrame with one-hot encoded features
        """
        if not _pandas_available:
            raise ImportError(
                "pandas is required for categorical feature extraction. "
                "Install it with: pip install pandas"
            )

        assert pd is not None
        return pd.get_dummies(data, columns=categorical_columns, prefix=categorical_columns)
