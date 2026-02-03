"""
MLOps Factory and Convenience Functions

High-level convenience functions for MLOps operations.
"""


# Standard library imports
from typing import Optional

# Local application/library specific imports
from ...postgresql_database.connection import DatabaseConnection
from .drift_detection import DriftDetector
from .experiment_tracker import ExperimentTracker
from .mlops_pipeline import MLOpsPipeline
from .model_deployment import ModelDeployment
from .model_monitoring import ModelMonitoring
from .model_versioning import ModelVersioning


def create_mlops_pipeline(pipeline_id: str, tenant_id: Optional[str] = None) -> MLOpsPipeline:
    """
    Create MLOps pipeline.
    
    Args:
        pipeline_id (str): Input parameter for this operation.
        tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
    
    Returns:
        MLOpsPipeline: Result of the operation.
    """
    return MLOpsPipeline(pipeline_id=pipeline_id, tenant_id=tenant_id)


def create_experiment_tracker(
    tracking_uri: str = "./mlruns", tenant_id: Optional[str] = None
) -> ExperimentTracker:
    """
    Create experiment tracker.
    
    Args:
        tracking_uri (str): Input parameter for this operation.
        tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
    
    Returns:
        ExperimentTracker: Result of the operation.
    """
    return ExperimentTracker(tracking_uri=tracking_uri, tenant_id=tenant_id)


def create_model_versioning(
    db: DatabaseConnection, tenant_id: Optional[str] = None
) -> ModelVersioning:
    """
    Create model versioning manager.
    
    Args:
        db (DatabaseConnection): Database connection/handle.
        tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
    
    Returns:
        ModelVersioning: Result of the operation.
    """
    return ModelVersioning(db=db, tenant_id=tenant_id)


def create_model_deployment(tenant_id: Optional[str] = None) -> ModelDeployment:
    """
    Create model deployment manager.
    
    Args:
        tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
    
    Returns:
        ModelDeployment: Result of the operation.
    """
    return ModelDeployment(tenant_id=tenant_id)


def create_model_monitoring(tenant_id: Optional[str] = None) -> ModelMonitoring:
    """
    Create model monitoring.
    
    Args:
        tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
    
    Returns:
        ModelMonitoring: Result of the operation.
    """
    return ModelMonitoring(tenant_id=tenant_id)


def create_drift_detector(tenant_id: Optional[str] = None) -> DriftDetector:
    """
    Create drift detector.
    
    Args:
        tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
    
    Returns:
        DriftDetector: Result of the operation.
    """
    return DriftDetector(tenant_id=tenant_id)
