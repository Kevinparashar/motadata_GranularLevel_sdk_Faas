"""
Machine Learning Components

Comprehensive ML framework, MLOps pipeline, data management, and model serving
for ITSM domain SaaS platform.
"""

from .ml_framework import MLSystem, ModelManager, Trainer, Predictor
from .mlops import MLOpsPipeline, ExperimentTracker, ModelDeployment
from .ml_data_management import DataManager, FeatureStore
from .model_serving import ModelServer, BatchPredictor
from .ml_framework.functions import (
    create_ml_system,
    create_model_manager,
    create_trainer,
    create_predictor,
    create_data_processor,
    create_model_registry,
)
from .mlops.functions import (
    create_mlops_pipeline,
    create_experiment_tracker,
    create_model_versioning,
    create_model_deployment,
    create_model_monitoring,
    create_drift_detector,
)
from .ml_data_management.functions import (
    create_data_manager,
    create_data_loader,
    create_data_validator,
    create_feature_store,
    create_data_pipeline,
)
from .model_serving.functions import (
    create_model_server,
    create_batch_predictor,
    create_realtime_predictor,
)

__all__ = [
    # Core classes
    "MLSystem",
    "ModelManager",
    "Trainer",
    "Predictor",
    "MLOpsPipeline",
    "ExperimentTracker",
    "ModelDeployment",
    "DataManager",
    "FeatureStore",
    "ModelServer",
    "BatchPredictor",
    # ML Framework factory functions
    "create_ml_system",
    "create_model_manager",
    "create_trainer",
    "create_predictor",
    "create_data_processor",
    "create_model_registry",
    # MLOps factory functions
    "create_mlops_pipeline",
    "create_experiment_tracker",
    "create_model_versioning",
    "create_model_deployment",
    "create_model_monitoring",
    "create_drift_detector",
    # Data Management factory functions
    "create_data_manager",
    "create_data_loader",
    "create_data_validator",
    "create_feature_store",
    "create_data_pipeline",
    # Model Serving factory functions
    "create_model_server",
    "create_batch_predictor",
    "create_realtime_predictor",
]


