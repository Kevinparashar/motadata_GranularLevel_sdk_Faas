"""
MLOps Exception Hierarchy

Exceptions specific to the MLOps component.
"""

from typing import Optional
from ...exceptions import SDKError


class MLOpsError(SDKError):
    """Base exception for MLOps-related errors."""
    pass


class ExperimentError(MLOpsError):
    """Raised when experiment tracking fails."""
    pass


class DeploymentError(MLOpsError):
    """Raised when model deployment fails."""
    pass


class MonitoringError(MLOpsError):
    """Raised when model monitoring fails."""
    pass


class DriftDetectionError(MLOpsError):
    """Raised when drift detection fails."""
    pass


