"""
Base Model Wrapper

Base wrapper class for integrating ML models (scikit-learn, etc.) with the ML framework.
"""


import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class BaseModelWrapper:
    """
    Base wrapper for ML models.

    Provides a common interface for different ML model types
    (scikit-learn, XGBoost, etc.) to integrate with the ML framework.
    This is a framework-level component, not a use case model.
    """

    def __init__(self, model: Any, model_type: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize model wrapper.
        
        Args:
            model (Any): Model name or identifier to use.
            model_type (str): Input parameter for this operation.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
        """
        self.model = model
        self.model_type = model_type
        self.metadata = metadata or {}

        logger.debug(f"BaseModelWrapper initialized for {model_type}")

    def fit(self, X: Any, y: Any, **kwargs) -> "BaseModelWrapper":
        """
        Train the model.
        
        Args:
            X (Any): Input parameter for this operation.
            y (Any): Input parameter for this operation.
            **kwargs (Any): Input parameter for this operation.
        
        Returns:
            'BaseModelWrapper': Builder instance (returned for call chaining).
        """
        self.model.fit(X, y, **kwargs)
        return self

    def predict(self, X: Any) -> Any:
        """
        Make predictions.
        
        Args:
            X (Any): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        """
        return self.model.predict(X)

    def predict_proba(self, X: Any) -> Any:
        """
        Get prediction probabilities (for classification models).
        
        Args:
            X (Any): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        """
        if hasattr(self.model, "predict_proba"):
            return self.model.predict_proba(X)
        return None

    def score(self, X: Any, y: Any) -> float:
        """
        Score the model.
        
        Args:
            X (Any): Input parameter for this operation.
            y (Any): Input parameter for this operation.
        
        Returns:
            float: Result of the operation.
        """
        if hasattr(self.model, "score"):
            return float(self.model.score(X, y))
        return 0.0

    def get_params(self) -> Dict[str, Any]:
        """
        Get model parameters.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        if hasattr(self.model, "get_params"):
            params = self.model.get_params()
            return dict(params) if params is not None else {}
        return {}

    def set_params(self, **params) -> "BaseModelWrapper":
        """
        Set model parameters.
        
        Args:
            **params (Any): Input parameter for this operation.
        
        Returns:
            'BaseModelWrapper': Builder instance (returned for call chaining).
        """
        if hasattr(self.model, "set_params"):
            self.model.set_params(**params)
        return self

    def get_model(self) -> Any:
        """
        Get the underlying model.
        
        Returns:
            Any: Result of the operation.
        """
        return self.model
