"""
Base ML Model

Base class interface for all ML use case models.
When creating a new use case, inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class BaseMLModel(ABC):
    """
    Base class for all ML use case models.
    
    All ITSM-specific ML models should inherit from this class
    and implement the required methods.
    """
    
    def __init__(
        self,
        model_id: str,
        tenant_id: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize base model.
        
        Args:
            model_id: Unique model identifier
            tenant_id: Optional tenant ID
            **kwargs: Additional model-specific parameters
        """
        self.model_id = model_id
        self.tenant_id = tenant_id
        self.model = None
        self.is_trained = False
        
        logger.info(f"BaseMLModel initialized: {model_id}")
    
    @abstractmethod
    def train(
        self,
        training_data: Any,
        validation_data: Optional[Any] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Train the model.
        
        Args:
            training_data: Training dataset
            validation_data: Optional validation dataset
            hyperparameters: Training hyperparameters
            **kwargs: Additional training parameters
            
        Returns:
            Dictionary with training results (metrics, etc.)
        """
        pass
    
    @abstractmethod
    def predict(
        self,
        input_data: Any,
        **kwargs
    ) -> Any:
        """
        Make predictions.
        
        Args:
            input_data: Input data for prediction
            **kwargs: Additional prediction parameters
            
        Returns:
            Prediction results
        """
        pass
    
    @abstractmethod
    def evaluate(
        self,
        test_data: Any,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Evaluate model performance.
        
        Args:
            test_data: Test dataset
            **kwargs: Additional evaluation parameters
            
        Returns:
            Dictionary with evaluation metrics
        """
        pass
    
    @abstractmethod
    def save(
        self,
        filepath: str,
        **kwargs
    ) -> str:
        """
        Save model to file.
        
        Args:
            filepath: Path to save model
            **kwargs: Additional save parameters
            
        Returns:
            Path to saved model file
        """
        pass
    
    @abstractmethod
    def load(
        self,
        filepath: str,
        **kwargs
    ) -> None:
        """
        Load model from file.
        
        Args:
            filepath: Path to model file
            **kwargs: Additional load parameters
        """
        pass
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model information.
        
        Returns:
            Dictionary with model metadata
        """
        return {
            'model_id': self.model_id,
            'tenant_id': self.tenant_id,
            'is_trained': self.is_trained,
            'model_type': self.__class__.__name__
        }


