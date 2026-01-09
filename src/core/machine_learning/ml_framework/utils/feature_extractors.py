"""
Feature Extractors

Utilities for extracting features from raw data.
"""

from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """
    Utility class for feature extraction.
    
    Provides common feature extraction methods for ITSM domain data.
    """
    
    @staticmethod
    def extract_text_features(
        text: str,
        include_length: bool = True,
        include_word_count: bool = True
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
            features['char_length'] = len(text)
        
        if include_word_count:
            features['word_count'] = len(text.split())
        
        return features
    
    @staticmethod
    def extract_datetime_features(
        datetime_value: Any,
        include_hour: bool = True,
        include_day_of_week: bool = True
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
        import pandas as pd
        
        features = {}
        dt = pd.to_datetime(datetime_value)
        
        if include_hour:
            features['hour'] = dt.hour
        
        if include_day_of_week:
            features['day_of_week'] = dt.dayofweek
        
        features['month'] = dt.month
        features['year'] = dt.year
        
        return features
    
    @staticmethod
    def extract_categorical_features(
        data: pd.DataFrame,
        categorical_columns: List[str]
    ) -> pd.DataFrame:
        """
        Extract features from categorical columns (one-hot encoding).
        
        Args:
            data: Input DataFrame
            categorical_columns: List of categorical column names
            
        Returns:
            DataFrame with one-hot encoded features
        """
        return pd.get_dummies(data, columns=categorical_columns, prefix=categorical_columns)


