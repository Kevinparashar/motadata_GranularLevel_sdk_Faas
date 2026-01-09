"""
MLOps Factory and Convenience Functions

High-level convenience functions for MLOps operations.
"""

from typing import Optional
from .mlops_pipeline import MLOpsPipeline
from .experiment_tracker import ExperimentTracker
from .model_versioning import ModelVersioning
from .model_deployment import ModelDeployment
from .model_monitoring import ModelMonitoring
from .drift_detection import DriftDetector
from ...postgresql_database.connection import DatabaseConnection


def create_mlops_pipeline(
    pipeline_id: str,
    tenant_id: Optional[str] = None
) -> MLOpsPipeline:
    """Create MLOps pipeline."""
    return MLOpsPipeline(pipeline_id=pipeline_id, tenant_id=tenant_id)


def create_experiment_tracker(
    tracking_uri: str = "./mlruns",
    tenant_id: Optional[str] = None
) -> ExperimentTracker:
    """Create experiment tracker."""
    return ExperimentTracker(tracking_uri=tracking_uri, tenant_id=tenant_id)


def create_model_versioning(
    db: DatabaseConnection,
    tenant_id: Optional[str] = None
) -> ModelVersioning:
    """Create model versioning manager."""
    return ModelVersioning(db=db, tenant_id=tenant_id)


def create_model_deployment(
    tenant_id: Optional[str] = None
) -> ModelDeployment:
    """Create model deployment manager."""
    return ModelDeployment(tenant_id=tenant_id)


def create_model_monitoring(
    tenant_id: Optional[str] = None
) -> ModelMonitoring:
    """Create model monitoring."""
    return ModelMonitoring(tenant_id=tenant_id)


def create_drift_detector(
    tenant_id: Optional[str] = None
) -> DriftDetector:
    """Create drift detector."""
    return DriftDetector(tenant_id=tenant_id)


