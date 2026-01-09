"""
Model Factory

Factory for creating ML models based on type and configuration.
"""

from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ModelFactory:
    """
    Factory for creating ML models.
    
    Creates model instances based on model type and configuration.
    Supports scikit-learn models and can be extended for other frameworks.
    """
    
    @staticmethod
    def create_model(
        model_type: str,
        hyperparameters: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Create a model instance.
        
        Args:
            model_type: Type of model to create
            hyperparameters: Optional hyperparameters
            
        Returns:
            Model instance
            
        Raises:
            ValueError: If model type is not supported
        """
        hyperparameters = hyperparameters or {}
        
        # Classification models
        if model_type == "classification":
            from sklearn.ensemble import RandomForestClassifier
            return RandomForestClassifier(**hyperparameters)
        
        elif model_type == "logistic_regression":
            from sklearn.linear_model import LogisticRegression
            return LogisticRegression(**hyperparameters)
        
        elif model_type == "svm_classification":
            from sklearn.svm import SVC
            return SVC(**hyperparameters)
        
        # Regression models
        elif model_type == "regression":
            from sklearn.ensemble import RandomForestRegressor
            return RandomForestRegressor(**hyperparameters)
        
        elif model_type == "linear_regression":
            from sklearn.linear_model import LinearRegression
            return LinearRegression(**hyperparameters)
        
        elif model_type == "svm_regression":
            from sklearn.svm import SVR
            return SVR(**hyperparameters)
        
        # Clustering models
        elif model_type == "kmeans":
            from sklearn.cluster import KMeans
            return KMeans(**hyperparameters)
        
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
    
    @staticmethod
    def get_available_models() -> Dict[str, list]:
        """
        Get list of available model types.
        
        Returns:
            Dictionary with categories and available models
        """
        return {
            "classification": [
                "classification",
                "logistic_regression",
                "svm_classification"
            ],
            "regression": [
                "regression",
                "linear_regression",
                "svm_regression"
            ],
            "clustering": [
                "kmeans"
            ]
        }
    
    @staticmethod
    def create_model_wrapper(
        model_type: str,
        hyperparameters: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Create a model wrapped in BaseModelWrapper.
        
        Args:
            model_type: Type of model
            hyperparameters: Optional hyperparameters
            
        Returns:
            Wrapped model instance
        """
        from .base_model_wrapper import BaseModelWrapper
        
        model = ModelFactory.create_model(model_type, hyperparameters)
        return BaseModelWrapper(model, model_type)


