"""
Trainer

Model training orchestration with hyperparameter management, validation, and checkpointing.
"""


import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from ...postgresql_database.connection import DatabaseConnection
from .exceptions import TrainingError
from .model_manager import ModelManager

logger = logging.getLogger(__name__)


class Trainer:
    """
    Orchestrates model training process.

    Handles training pipeline execution, hyperparameter management,
    cross-validation, metrics tracking, and checkpoint management.
    """

    def __init__(self, db: DatabaseConnection, tenant_id: Optional[str] = None):
        """
        Initialize trainer.
        
        Args:
            db (DatabaseConnection): Database connection/handle.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        """
        self.db = db
        self.tenant_id = tenant_id
        self.model_manager = ModelManager(db, tenant_id=tenant_id)

        logger.info(f"Trainer initialized for tenant: {tenant_id}")

    def train(
        self,
        model_id: str,
        model_type: str,
        training_data: Any,
        validation_data: Optional[Any] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Execute model training.
        
        Args:
            model_id (str): Input parameter for this operation.
            model_type (str): Input parameter for this operation.
            training_data (Any): Input parameter for this operation.
            validation_data (Optional[Any]): Input parameter for this operation.
            hyperparameters (Optional[Dict[str, Any]]): Input parameter for this operation.
            **kwargs (Any): Input parameter for this operation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        
        Raises:
            TrainingError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        try:
            logger.info(f"Starting training for {model_id}")

            # Import model creation based on type
            model = self._create_model(model_type, hyperparameters or {})

            # Train model
            if validation_data is not None:
                model.fit(training_data[0], training_data[1])
                val_metrics = self._evaluate(model, validation_data)
            else:
                model.fit(training_data[0], training_data[1])
                val_metrics = {}

            # Calculate training metrics
            train_metrics = self._evaluate(model, training_data)

            # Save model
            version = kwargs.get("version", "1.0.0")
            model_path = self.model_manager.save_model(model, model_id, version)

            # Register model
            self.model_manager.register_model(
                model_id=model_id,
                model_type=model_type,
                model_path=model_path,
                metadata={
                    "hyperparameters": hyperparameters or {},
                    "train_metrics": train_metrics,
                    "val_metrics": val_metrics,
                },
                version=version,
            )

            result = {
                "model_id": model_id,
                "version": version,
                "model_path": model_path,
                "metrics": {"train": train_metrics, "validation": val_metrics},
                "hyperparameters": hyperparameters or {},
            }

            logger.info(f"Training completed for {model_id}")
            return result

        except Exception as e:
            error_msg = f"Training failed for {model_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise TrainingError(
                error_msg,
                model_id=model_id,
                stage="training",
                hyperparameters=hyperparameters,
                original_error=e,
            )

    def validate(self, model: Any, validation_data: Any) -> Dict[str, Any]:
        """
        Validate a model.
        
        Args:
            model (Any): Model name or identifier to use.
            validation_data (Any): Input parameter for this operation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        return self._evaluate(model, validation_data)

    def save_checkpoint(
        self, model: Any, model_id: str, epoch: int, checkpoint_dir: Optional[str] = None
    ) -> str:
        """
        Save training checkpoint.
        
        Args:
            model (Any): Model name or identifier to use.
            model_id (str): Input parameter for this operation.
            epoch (int): Input parameter for this operation.
            checkpoint_dir (Optional[str]): Input parameter for this operation.
        
        Returns:
            str: Returned text value.
        """
        import joblib

        if checkpoint_dir is None:
            checkpoint_dir = f"./checkpoints/{model_id}"

        Path(checkpoint_dir).mkdir(parents=True, exist_ok=True)
        checkpoint_path = os.path.join(checkpoint_dir, f"checkpoint_epoch_{epoch}.joblib")
        joblib.dump(model, checkpoint_path)

        logger.info(f"Checkpoint saved: {checkpoint_path}")
        return checkpoint_path

    def load_checkpoint(self, checkpoint_path: str) -> Any:
        """
        Load training checkpoint.
        
        Args:
            checkpoint_path (str): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        """
        import joblib

        return joblib.load(checkpoint_path)

    def _create_model(self, model_type: str, hyperparameters: Dict[str, Any]) -> Any:
        """
        Create model instance based on type.
        
        Args:
            model_type (str): Input parameter for this operation.
            hyperparameters (Dict[str, Any]): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            ValueError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
        from sklearn.linear_model import LinearRegression, LogisticRegression
        from sklearn.svm import SVC, SVR

        # Provide sensible defaults for scikit-learn estimators
        # Users can override these via the hyperparameters argument
        rf_clf_defaults = {
            "random_state": 42,
            "n_estimators": 100,
            "min_samples_leaf": 1,
            "max_features": "sqrt",
        }
        rf_reg_defaults = {
            "random_state": 42,
            "n_estimators": 100,
            "min_samples_leaf": 1,
            "max_features": 1.0,
        }
        svc_defaults = {"C": 1.0, "kernel": "rbf", "gamma": "scale"}
        svr_defaults = {"C": 1.0, "kernel": "rbf", "gamma": "scale"}

        model_map = {
            "classification": RandomForestClassifier(  # noqa: S6709, S6973
                **{**rf_clf_defaults, **hyperparameters}
            ),
            "regression": RandomForestRegressor(  # noqa: S6709, S6973
                **{**rf_reg_defaults, **hyperparameters}
            ),
            "logistic_regression": LogisticRegression(**hyperparameters),
            "linear_regression": LinearRegression(**hyperparameters),
            "svm_classification": SVC(  # noqa: S6973
                **{**svc_defaults, **hyperparameters}
            ),
            "svm_regression": SVR(  # noqa: S6973
                **{**svr_defaults, **hyperparameters}
            ),
        }

        if model_type not in model_map:
            raise ValueError(f"Unknown model type: {model_type}")

        return model_map[model_type]

    def _evaluate(self, model: Any, data: Any) -> Dict[str, Any]:
        """
        Evaluate model on data.
        
        Args:
            model (Any): Model name or identifier to use.
            data (Any): Input parameter for this operation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        from sklearn.metrics import (
            accuracy_score,
            f1_score,
            mean_absolute_error,
            mean_squared_error,
            precision_score,
            r2_score,
            recall_score,
        )

        X, y = data
        y_pred = model.predict(X)

        # Determine if classification or regression
        if hasattr(model, "predict_proba"):
            # Classification
            return {
                "accuracy": float(accuracy_score(y, y_pred)),
                "precision": float(precision_score(y, y_pred, average="weighted", zero_division=0)),  # type: ignore[arg-type]
                "recall": float(recall_score(y, y_pred, average="weighted", zero_division=0)),  # type: ignore[arg-type]
                "f1": float(f1_score(y, y_pred, average="weighted", zero_division=0)),  # type: ignore[arg-type]
            }
        else:
            # Regression
            return {
                "mse": float(mean_squared_error(y, y_pred)),
                "mae": float(mean_absolute_error(y, y_pred)),
                "r2": float(r2_score(y, y_pred)),
            }
