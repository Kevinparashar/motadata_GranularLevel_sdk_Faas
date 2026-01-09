"""
ML Framework Exception Hierarchy

Exceptions specific to the ML Framework component.
"""

from typing import Optional, Any
from ...exceptions import SDKError


class MLFrameworkError(SDKError):
    """Base exception for ML Framework-related errors."""
    pass


class TrainingError(MLFrameworkError):
    """
    Raised when model training fails.
    
    Attributes:
        model_id: ID of the model being trained
        stage: Training stage that failed
        hyperparameters: Hyperparameters used (if applicable)
    """
    
    def __init__(
        self,
        message: str,
        model_id: Optional[str] = None,
        stage: Optional[str] = None,
        hyperparameters: Optional[dict] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message, original_error)
        self.model_id = model_id
        self.stage = stage
        self.hyperparameters = hyperparameters


class PredictionError(MLFrameworkError):
    """
    Raised when model prediction fails.
    
    Attributes:
        model_id: ID of the model
        input_data: Input data that failed (if applicable)
        operation: Operation that failed (predict, predict_batch, etc.)
    """
    
    def __init__(
        self,
        message: str,
        model_id: Optional[str] = None,
        input_data: Optional[Any] = None,
        operation: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message, original_error)
        self.model_id = model_id
        self.input_data = input_data
        self.operation = operation


class ModelLoadError(MLFrameworkError):
    """
    Raised when model loading fails.
    
    Attributes:
        model_id: ID of the model
        model_path: Path to the model file
        version: Model version (if applicable)
    """
    
    def __init__(
        self,
        message: str,
        model_id: Optional[str] = None,
        model_path: Optional[str] = None,
        version: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message, original_error)
        self.model_id = model_id
        self.model_path = model_path
        self.version = version


class ModelSaveError(MLFrameworkError):
    """
    Raised when model saving fails.
    
    Attributes:
        model_id: ID of the model
        save_path: Path where model was being saved
    """
    
    def __init__(
        self,
        message: str,
        model_id: Optional[str] = None,
        save_path: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message, original_error)
        self.model_id = model_id
        self.save_path = save_path


class DataProcessingError(MLFrameworkError):
    """
    Raised when data processing fails.
    
    Attributes:
        operation: Processing operation that failed
        data_type: Type of data being processed
    """
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        data_type: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message, original_error)
        self.operation = operation
        self.data_type = data_type


class ModelNotFoundError(MLFrameworkError):
    """
    Raised when a model is not found.
    
    Attributes:
        model_id: ID of the model that was not found
        version: Model version (if applicable)
    """
    
    def __init__(
        self,
        message: str,
        model_id: Optional[str] = None,
        version: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message, original_error)
        self.model_id = model_id
        self.version = version


