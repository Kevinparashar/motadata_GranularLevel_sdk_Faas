"""
Request/Response models for ML Service.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TrainModelRequest(BaseModel):
    """Request to train a model."""

    model_type: str = Field(..., description="Model type (e.g., 'classification', 'regression')")
    training_data: Dict[str, Any] = Field(..., description="Training data")
    hyperparameters: Optional[Dict[str, Any]] = Field(None, description="Model hyperparameters")
    validation_split: Optional[float] = Field(
        0.2, ge=0.0, le=1.0, description="Validation split ratio"
    )


class PredictRequest(BaseModel):
    """Request for model prediction."""

    model_id: str = Field(..., description="Model ID")
    features: Dict[str, Any] = Field(..., description="Input features")


class BatchPredictRequest(BaseModel):
    """Request for batch prediction."""

    model_id: str = Field(..., description="Model ID")
    features_list: List[Dict[str, Any]] = Field(..., description="List of input features")


class DeployModelRequest(BaseModel):
    """Request to deploy a model."""

    model_id: str = Field(..., description="Model ID")
    version: Optional[str] = Field(None, description="Model version")


class ModelResponse(BaseModel):
    """Model response model."""

    model_id: str
    model_type: str
    status: str
    version: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class TrainingResponse(BaseModel):
    """Training response model."""

    training_id: str
    model_id: str
    status: str
    metrics: Optional[Dict[str, Any]] = None
    progress: Optional[float] = Field(None, ge=0.0, le=1.0, description="Training progress")


class PredictionResponse(BaseModel):
    """Prediction response model."""

    prediction: Any
    confidence: Optional[float] = None
    model_id: str
    metadata: Optional[Dict[str, Any]] = None
