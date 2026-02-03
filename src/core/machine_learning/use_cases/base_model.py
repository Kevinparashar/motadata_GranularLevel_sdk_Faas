"""
Base ML Model

Base class interface for all ML use case models.
When creating a new use case, inherit from this class.
"""


import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class BaseMLModel(ABC):
    """
    Base class for all ML use case models.

    All ITSM-specific ML models should inherit from this class
    and implement the required methods.
    """

    def __init__(self, model_id: str, tenant_id: Optional[str] = None, **kwargs):
        """
        Initialize base model.
        
        Args:
            model_id (str): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
            **kwargs (Any): Input parameter for this operation.
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
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Train the model.
        
        Args:
            training_data (Any): Input parameter for this operation.
            validation_data (Optional[Any]): Input parameter for this operation.
            hyperparameters (Optional[Dict[str, Any]]): Input parameter for this operation.
            **kwargs (Any): Input parameter for this operation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        pass

    @abstractmethod
    def predict(self, input_data: Any, **kwargs) -> Any:
        """
        Make predictions.
        
        Args:
            input_data (Any): Input parameter for this operation.
            **kwargs (Any): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        """
        pass

    @abstractmethod
    def evaluate(self, test_data: Any, **kwargs) -> Dict[str, Any]:
        """
        Evaluate model performance.
        
        Args:
            test_data (Any): Input parameter for this operation.
            **kwargs (Any): Input parameter for this operation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        pass

    @abstractmethod
    def save(self, filepath: str, **kwargs) -> str:
        """
        Save model to file.
        
        Args:
            filepath (str): Input parameter for this operation.
            **kwargs (Any): Input parameter for this operation.
        
        Returns:
            str: Returned text value.
        """
        pass

    @abstractmethod
    def load(self, filepath: str, **kwargs) -> None:
        """
        Load model from file.
        
        Args:
            filepath (str): Input parameter for this operation.
            **kwargs (Any): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        """
        pass

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model information.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        return {
            "model_id": self.model_id,
            "tenant_id": self.tenant_id,
            "is_trained": self.is_trained,
            "model_type": self.__class__.__name__,
        }
