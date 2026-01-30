"""
Experiment Tracker

Tracks ML experiments with MLflow integration.
"""

# Standard library imports
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ExperimentTracker:
    """
    Tracks ML experiments.

    Provides experiment logging, comparison, and search capabilities
    with MLflow integration.
    """

    def __init__(self, tracking_uri: str = "./mlruns", tenant_id: Optional[str] = None):
        """
        Initialize experiment tracker.

        Args:
            tracking_uri: MLflow tracking URI
            tenant_id: Optional tenant ID
        """
        self.tracking_uri = tracking_uri
        self.tenant_id = tenant_id
        self._mlflow_available = self._check_mlflow()

        logger.info(f"ExperimentTracker initialized for tenant: {tenant_id}")

    def create_experiment(self, experiment_name: str, tags: Optional[Dict[str, str]] = None) -> str:
        """
        Create new experiment.

        Args:
            experiment_name: Name of experiment
            tags: Optional tags

        Returns:
            Experiment ID
        """
        if self._mlflow_available:
            import mlflow  # type: ignore[import-not-found]

            mlflow.set_tracking_uri(self.tracking_uri)
            experiment_id: str = mlflow.create_experiment(experiment_name, tags=tags or {})
            return experiment_id
        else:
            logger.warning("MLflow not available, using local tracking")
            return f"exp_{experiment_name}_{datetime.now().timestamp()}"

    def log_params(self, params: Dict[str, Any]) -> None:
        """Log hyperparameters."""
        if self._mlflow_available:
            import mlflow  # type: ignore[import-not-found]

            mlflow.log_params(params)
        logger.debug(f"Logged parameters: {params}")

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None) -> None:
        """Log metrics."""
        if self._mlflow_available:
            import mlflow  # type: ignore[import-not-found]

            mlflow.log_metrics(metrics, step=step)
        logger.debug(f"Logged metrics: {metrics}")

    def log_artifacts(self, artifacts: Dict[str, str]) -> None:
        """Log artifacts (models, plots, etc.)."""
        if self._mlflow_available:
            import mlflow  # type: ignore[import-not-found]

            for name, path in artifacts.items():
                mlflow.log_artifact(path, name)
        logger.debug(f"Logged artifacts: {artifacts}")

    def search_experiments(
        self, filter_string: Optional[str] = None, max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search experiments.

        Args:
            filter_string: Optional filter string
            max_results: Maximum results

        Returns:
            List of experiment information
        """
        if self._mlflow_available:
            from mlflow.tracking import MlflowClient  # type: ignore[import-not-found]

            client = MlflowClient(tracking_uri=self.tracking_uri)
            experiments = client.search_experiments(
                filter_string=filter_string, max_results=max_results
            )
            return [{"experiment_id": exp.experiment_id, "name": exp.name} for exp in experiments]
        else:
            return []

    def _check_mlflow(self) -> bool:
        """Check if MLflow is available."""
        try:
            import mlflow  # type: ignore[import-not-found]  # noqa: F401

            return True
        except ImportError:
            return False
