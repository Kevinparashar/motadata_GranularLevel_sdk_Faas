"""
Base Model Wrapper

Base wrapper class for integrating ML models (scikit-learn, etc.) with the ML framework.
"""

from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class BaseModelWrapper:
    """
    Base wrapper for ML models.
    
    Provides a common interface for different ML model types
    (scikit-learn, XGBoost, etc.) to integrate with the ML framework.
    This is a framework-level component, not a use case model.
    """
    
    def __init__(
        self,
        model: Any,
        model_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize model wrapper.
        
        Args:
            model: The underlying ML model (scikit-learn, etc.)
            model_type: Type of model (classification, regression, etc.)
            metadata: Optional model metadata
        """
        self.model = model
        self.model_type = model_type
        self.metadata = metadata or {}
        
        logger.debug(f"BaseModelWrapper initialized for {model_type}")
    
    def fit(self, X: Any, y: Any, **kwargs) -> 'BaseModelWrapper':
        """
        Train the model.
        
        Args:
            X: Training features
            y: Training labels
            **kwargs: Additional training parameters
            
        Returns:
            Self for method chaining
        """
        self.model.fit(X, y, **kwargs)
        return self
    
    def predict(self, X: Any) -> Any:
        """
        Make predictions.
        
        Args:
            X: Input features
            
        Returns:
            Predictions
        """
        return self.model.predict(X)
    
    def predict_proba(self, X: Any) -> Any:
        """
        Get prediction probabilities (for classification models).
        
        Args:
            X: Input features
            
        Returns:
            Prediction probabilities or None if not supported
        """
        if hasattr(self.model, 'predict_proba'):
            return self.model.predict_proba(X)
        return None
    
    def score(self, X: Any, y: Any) -> float:
        """
        Score the model.
        
        Args:
            X: Test features
            y: Test labels
            
        Returns:
            Model score
        """
        if hasattr(self.model, 'score'):
            return float(self.model.score(X, y))
        return 0.0
    
    def get_params(self) -> Dict[str, Any]:
        """
        Get model parameters.
        
        Returns:
            Model parameters
        """
        if hasattr(self.model, 'get_params'):
            return self.model.get_params()
        return {}
    
    def set_params(self, **params) -> 'BaseModelWrapper':
        """
        Set model parameters.
        
        Args:
            **params: Parameters to set
            
        Returns:
            Self for method chaining
        """
        if hasattr(self.model, 'set_params'):
            self.model.set_params(**params)
        return self
    
    def get_model(self) -> Any:
        """
        Get the underlying model.
        
        Returns:
            The wrapped model
        """
        return self.model


