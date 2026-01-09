"""
Model Serving Exception Hierarchy

Exceptions specific to the Model Serving component.
"""

from typing import Optional
from ...exceptions import SDKError


class ModelServingError(SDKError):
    """Base exception for model serving errors."""
    pass


class ServerError(ModelServingError):
    """Raised when server operations fail."""
    pass


class BatchJobError(ModelServingError):
    """Raised when batch job operations fail."""
    pass


class InferenceError(ModelServingError):
    """Raised when inference fails."""
    pass


