"""
ML Service - FaaS implementation of ML Framework.

Provides REST API for model training, inference, and model management.
"""

from .service import MLService, create_ml_service
from .models import (
    TrainModelRequest,
    PredictRequest,
    BatchPredictRequest,
    DeployModelRequest,
    ModelResponse,
    TrainingResponse,
    PredictionResponse,
)

__all__ = [
    "MLService",
    "create_ml_service",
    "TrainModelRequest",
    "PredictRequest",
    "BatchPredictRequest",
    "DeployModelRequest",
    "ModelResponse",
    "TrainingResponse",
    "PredictionResponse",
]

