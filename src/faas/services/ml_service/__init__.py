"""
ML Service - FaaS implementation of ML Framework.

Provides REST API for model training, inference, and model management.
"""

from .models import (
    BatchPredictRequest,
    DeployModelRequest,
    ModelResponse,
    PredictionResponse,
    PredictRequest,
    TrainingResponse,
    TrainModelRequest,
)
from .service import MLService, create_ml_service

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
