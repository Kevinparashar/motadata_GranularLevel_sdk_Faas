"""
Data Processor

Data preprocessing and feature engineering for ML models.
"""


import logging
from typing import Any, Dict, Optional, Tuple

import numpy as np

from .exceptions import DataProcessingError

logger = logging.getLogger(__name__)

try:
    import pandas as pd  # type: ignore[import-untyped]

    _pandas_available = True
except ImportError:
    _pandas_available = False
    pd = None


class DataProcessor:
    """
    Handles data preprocessing and feature engineering.

    Provides data cleaning, normalization, feature extraction,
    transformation, and data splitting capabilities.
    """

    def __init__(self, tenant_id: Optional[str] = None):
        """
        Initialize data processor.
        
        Args:
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        """
        self.tenant_id = tenant_id
        self._scalers = {}
        self._encoders = {}

        logger.info(f"DataProcessor initialized for tenant: {tenant_id}")

    def preprocess(
        self, data: Any, model_type: Optional[str] = None, is_training: bool = True
    ) -> Any:
        """
        Preprocess data for model training or inference.
        
        Args:
            data (Any): Input parameter for this operation.
            model_type (Optional[str]): Input parameter for this operation.
            is_training (bool): Flag to indicate whether training is true.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            DataProcessingError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        try:
            # Handle different input types
            if _pandas_available and pd is not None and isinstance(data, pd.DataFrame):
                processed = self._preprocess_dataframe(data, is_training)
            elif isinstance(data, (list, tuple)) and len(data) == 2:
                # (X, y) tuple - X, y are standard ML conventions
                X, y = data  # noqa: N806
                processed_X = self.preprocess(X, model_type, is_training)  # noqa: N806, S117
                processed = (processed_X, y)
            elif isinstance(data, np.ndarray):
                processed = self._preprocess_array(data)
            else:
                # Try to convert to numpy array
                processed = np.array(data)

            logger.debug("Data preprocessing completed")
            return processed

        except Exception as e:
            error_msg = f"Data preprocessing failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise DataProcessingError(error_msg, operation="preprocess", original_error=e)

    def extract_features(self, data: Any, feature_config: Optional[Dict[str, Any]] = None) -> Any:
        """
        Extract features from raw data.
        
        Args:
            data (Any): Input parameter for this operation.
            feature_config (Optional[Dict[str, Any]]): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            DataProcessingError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        try:
            if _pandas_available and pd is not None and isinstance(data, pd.DataFrame):
                return self._extract_features_dataframe(data, feature_config)
            else:
                return data
        except Exception as e:
            error_msg = f"Feature extraction failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise DataProcessingError(error_msg, operation="extract_features", original_error=e)

    def transform_features(self, features: Any, transform_type: str = "standard") -> Any:
        """
        Transform features (scaling, normalization, etc.).
        
        Args:
            features (Any): Input parameter for this operation.
            transform_type (str): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            DataProcessingError: Raised when this function detects an invalid state or when an underlying call fails.
            ValueError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        try:
            from sklearn.preprocessing import MinMaxScaler, StandardScaler

            if transform_type == "standard":
                scaler = StandardScaler()
            elif transform_type == "minmax":
                scaler = MinMaxScaler()
            else:
                raise ValueError(f"Unknown transform type: {transform_type}")

            transformed = scaler.fit_transform(features)
            return transformed

        except Exception as e:
            error_msg = f"Feature transformation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise DataProcessingError(error_msg, operation="transform_features", original_error=e)

    def split_data(
        self,
        X: Any,
        y: Any,
        test_size: float = 0.2,
        val_size: Optional[float] = None,
        random_state: int = 42,
    ) -> Tuple[Any, ...]:
        """
        Split data into train/validation/test sets.
        
        Args:
            X (Any): Input parameter for this operation.
            y (Any): Input parameter for this operation.
            test_size (float): Input parameter for this operation.
            val_size (Optional[float]): Input parameter for this operation.
            random_state (int): Input parameter for this operation.
        
        Returns:
            Tuple[Any, ...]: Result of the operation.
        
        Raises:
            DataProcessingError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        try:
            from sklearn.model_selection import train_test_split

            # First split: train+val vs test (X, y naming follows ML conventions)
            X_train_val, X_test, y_train_val, y_test = train_test_split(  # noqa: N806, S117
                X, y, test_size=test_size, random_state=random_state
            )

            if val_size:
                # Second split: train vs val
                val_size_adjusted = val_size / (1 - test_size)
                X_train, X_val, y_train, y_val = train_test_split(  # noqa: N806, S117
                    X_train_val, y_train_val, test_size=val_size_adjusted, random_state=random_state
                )
                return (X_train, X_val, X_test, y_train, y_val, y_test)
            else:
                return (X_train_val, X_test, y_train_val, y_test)

        except Exception as e:
            error_msg = f"Data splitting failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise DataProcessingError(error_msg, operation="split_data", original_error=e)

    def postprocess(self, predictions: Any) -> Any:
        """
        Postprocess model predictions.
        
        Args:
            predictions (Any): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        """
        try:
            # Convert numpy arrays to lists for JSON serialization
            if isinstance(predictions, np.ndarray):
                return predictions.tolist()
            elif isinstance(predictions, (list, tuple)):
                return [self.postprocess(item) for item in predictions]
            else:
                return predictions
        except Exception as e:
            logger.warning(f"Postprocessing warning: {str(e)}")
            return predictions

    def _preprocess_dataframe(self, df: Any, is_training: bool) -> Any:
        """
        Preprocess pandas DataFrame.
        
        Args:
            df (Any): Input parameter for this operation.
            is_training (bool): Flag to indicate whether training is true.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            ImportError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        if not _pandas_available or pd is None:
            raise ImportError(
                "pandas is required for DataFrame preprocessing. "
                "Install it with: pip install pandas"
            )
        # Handle missing values
        df = df.fillna(df.mean() if is_training else 0)

        # Remove duplicates
        df = df.drop_duplicates()

        return df

    def _preprocess_array(self, arr: np.ndarray) -> np.ndarray:
        """
        Preprocess numpy array.
        
        Args:
            arr (np.ndarray): Input parameter for this operation.
        
        Returns:
            np.ndarray: Result of the operation.
        """
        # Handle NaN values
        if np.isnan(arr).any():
            arr = np.nan_to_num(arr, nan=0.0)

        return arr

    def _extract_features_dataframe(
        self, df: Any, feature_config: Optional[Dict[str, Any]]
    ) -> Any:
        """
        Extract features from DataFrame.
        
        Args:
            df (Any): Input parameter for this operation.
            feature_config (Optional[Dict[str, Any]]): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            ImportError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        if not _pandas_available or pd is None:
            raise ImportError(
                "pandas is required for DataFrame feature extraction. "
                "Install it with: pip install pandas"
            )
        # Basic feature extraction
        # Can be extended based on feature_config
        return df
