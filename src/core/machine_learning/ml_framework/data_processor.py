"""
Data Processor

Data preprocessing and feature engineering for ML models.
"""

from typing import Any, Optional, Dict, Tuple
import logging
import pandas as pd
import numpy as np

from .exceptions import DataProcessingError

logger = logging.getLogger(__name__)


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
            tenant_id: Optional tenant ID
        """
        self.tenant_id = tenant_id
        self._scalers = {}
        self._encoders = {}
        
        logger.info(f"DataProcessor initialized for tenant: {tenant_id}")
    
    def preprocess(
        self,
        data: Any,
        model_type: Optional[str] = None,
        is_training: bool = True
    ) -> Any:
        """
        Preprocess data for model training or inference.
        
        Args:
            data: Raw input data
            model_type: Optional model type for type-specific processing
            is_training: Whether this is training data (affects scaling fit)
            
        Returns:
            Preprocessed data
        """
        try:
            # Handle different input types
            if isinstance(data, pd.DataFrame):
                processed = self._preprocess_dataframe(data, is_training)
            elif isinstance(data, (list, tuple)) and len(data) == 2:
                # (X, y) tuple
                X, y = data
                processed_X = self.preprocess(X, model_type, is_training)
                processed = (processed_X, y)
            elif isinstance(data, np.ndarray):
                processed = self._preprocess_array(data, is_training)
            else:
                # Try to convert to numpy array
                processed = np.array(data)
            
            logger.debug("Data preprocessing completed")
            return processed
            
        except Exception as e:
            error_msg = f"Data preprocessing failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise DataProcessingError(
                error_msg,
                operation="preprocess",
                original_error=e
            )
    
    def extract_features(
        self,
        data: Any,
        feature_config: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Extract features from raw data.
        
        Args:
            data: Raw input data
            feature_config: Optional feature extraction configuration
            
        Returns:
            Extracted features
        """
        try:
            if isinstance(data, pd.DataFrame):
                return self._extract_features_dataframe(data, feature_config)
            else:
                return data
        except Exception as e:
            error_msg = f"Feature extraction failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise DataProcessingError(
                error_msg,
                operation="extract_features",
                original_error=e
            )
    
    def transform_features(
        self,
        features: Any,
        transform_type: str = "standard"
    ) -> Any:
        """
        Transform features (scaling, normalization, etc.).
        
        Args:
            features: Input features
            transform_type: Type of transformation (standard, minmax, etc.)
            
        Returns:
            Transformed features
        """
        try:
            from sklearn.preprocessing import StandardScaler, MinMaxScaler
            
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
            raise DataProcessingError(
                error_msg,
                operation="transform_features",
                original_error=e
            )
    
    def split_data(
        self,
        X: Any,
        y: Any,
        test_size: float = 0.2,
        val_size: Optional[float] = None,
        random_state: int = 42
    ) -> Tuple[Any, ...]:
        """
        Split data into train/validation/test sets.
        
        Args:
            X: Features
            y: Labels
            test_size: Proportion of test set
            val_size: Optional proportion of validation set
            random_state: Random seed
            
        Returns:
            Tuple of (X_train, X_val, X_test, y_train, y_val, y_test) or
            (X_train, X_test, y_train, y_test) if val_size is None
        """
        try:
            from sklearn.model_selection import train_test_split
            
            # First split: train+val vs test
            X_train_val, X_test, y_train_val, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state
            )
            
            if val_size:
                # Second split: train vs val
                val_size_adjusted = val_size / (1 - test_size)
                X_train, X_val, y_train, y_val = train_test_split(
                    X_train_val, y_train_val,
                    test_size=val_size_adjusted,
                    random_state=random_state
                )
                return (X_train, X_val, X_test, y_train, y_val, y_test)
            else:
                return (X_train_val, X_test, y_train_val, y_test)
                
        except Exception as e:
            error_msg = f"Data splitting failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise DataProcessingError(
                error_msg,
                operation="split_data",
                original_error=e
            )
    
    def postprocess(
        self,
        predictions: Any
    ) -> Any:
        """
        Postprocess model predictions.
        
        Args:
            predictions: Raw model predictions
            
        Returns:
            Postprocessed predictions
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
    
    def _preprocess_dataframe(
        self,
        df: pd.DataFrame,
        is_training: bool
    ) -> pd.DataFrame:
        """Preprocess pandas DataFrame."""
        # Handle missing values
        df = df.fillna(df.mean() if is_training else 0)
        
        # Remove duplicates
        df = df.drop_duplicates()
        
        return df
    
    def _preprocess_array(
        self,
        arr: np.ndarray,
        is_training: bool
    ) -> np.ndarray:
        """Preprocess numpy array."""
        # Handle NaN values
        if np.isnan(arr).any():
            arr = np.nan_to_num(arr, nan=0.0)
        
        return arr
    
    def _extract_features_dataframe(
        self,
        df: pd.DataFrame,
        feature_config: Optional[Dict[str, Any]]
    ) -> pd.DataFrame:
        """Extract features from DataFrame."""
        # Basic feature extraction
        # Can be extended based on feature_config
        return df


