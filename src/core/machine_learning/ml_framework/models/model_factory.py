"""
Model Factory

Factory for creating ML models based on type and configuration.
"""


# Standard library imports
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ModelFactory:
    """
    Factory for creating ML models.

    Creates model instances based on model type and configuration.
    Supports scikit-learn models and can be extended for other frameworks.
    """

    @staticmethod
    def create_model(model_type: str, hyperparameters: Optional[Dict[str, Any]] = None) -> Any:
        """
        Create a model instance.
        
        Args:
            model_type (str): Input parameter for this operation.
            hyperparameters (Optional[Dict[str, Any]]): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            ValueError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        hyperparameters = hyperparameters or {}

        # Classification models
        if model_type == "classification":
            from sklearn.ensemble import RandomForestClassifier

            defaults = {
                "random_state": 42,
                "min_samples_leaf": 1,
                "max_features": "sqrt",
                "n_estimators": 100,
            }
            params = {**defaults, **hyperparameters}
            return RandomForestClassifier(**params)  # noqa: S6709, S6973

        elif model_type == "logistic_regression":
            from sklearn.linear_model import LogisticRegression

            defaults = {"random_state": 42, "max_iter": 1000}
            params = {**defaults, **hyperparameters}
            return LogisticRegression(**params)  # noqa: S6709

        elif model_type == "svm_classification":
            from sklearn.svm import SVC

            defaults = {"C": 1.0, "kernel": "rbf", "gamma": "scale", "random_state": 42}
            params = {**defaults, **hyperparameters}
            return SVC(**params)  # noqa: S6709, S6973

        # Regression models
        elif model_type == "regression":
            from sklearn.ensemble import RandomForestRegressor

            defaults = {
                "random_state": 42,
                "min_samples_leaf": 1,
                "max_features": 1.0,
                "n_estimators": 100,
            }
            params = {**defaults, **hyperparameters}
            return RandomForestRegressor(**params)  # noqa: S6709, S6973

        elif model_type == "linear_regression":
            from sklearn.linear_model import LinearRegression

            return LinearRegression(**hyperparameters)

        elif model_type == "svm_regression":
            from sklearn.svm import SVR

            defaults = {"C": 1.0, "kernel": "rbf", "gamma": "scale"}
            params = {**defaults, **hyperparameters}
            return SVR(**params)  # noqa: S6973

        # Clustering models
        elif model_type == "kmeans":
            from sklearn.cluster import KMeans

            defaults = {"random_state": 42, "n_clusters": 8}
            params = {**defaults, **hyperparameters}
            return KMeans(**params)  # noqa: S6709

        else:
            raise ValueError(f"Unsupported model type: {model_type}")

    @staticmethod
    def get_available_models() -> Dict[str, list]:
        """
        Get list of available model types.
        
        Returns:
            Dict[str, list]: Dictionary result of the operation.
        """
        return {
            "classification": ["classification", "logistic_regression", "svm_classification"],
            "regression": ["regression", "linear_regression", "svm_regression"],
            "clustering": ["kmeans"],
        }

    @staticmethod
    def create_model_wrapper(
        model_type: str, hyperparameters: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Create a model wrapped in BaseModelWrapper.
        
        Args:
            model_type (str): Input parameter for this operation.
            hyperparameters (Optional[Dict[str, Any]]): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        """
        from .base_model_wrapper import BaseModelWrapper

        model = ModelFactory.create_model(model_type, hyperparameters)
        return BaseModelWrapper(model, model_type)
