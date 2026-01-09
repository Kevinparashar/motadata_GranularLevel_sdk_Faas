"""
Trainer

Model training orchestration with hyperparameter management, validation, and checkpointing.
"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import os
from pathlib import Path

from .exceptions import TrainingError
from .model_manager import ModelManager
from ...postgresql_database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class Trainer:
    """
    Orchestrates model training process.

    Handles training pipeline execution, hyperparameter management,
    cross-validation, metrics tracking, and checkpoint management.
    """

    def __init__(
        self,
        db: DatabaseConnection,
        tenant_id: Optional[str] = None
    ):
        """
        Initialize trainer.

        Args:
            db: Database connection
            tenant_id: Optional tenant ID
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
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute model training.

        Args:
            model_id: Unique model identifier
            model_type: Type of model (classification, regression, etc.)
            training_data: Training dataset
            validation_data: Optional validation dataset
            hyperparameters: Training hyperparameters
            **kwargs: Additional training parameters

        Returns:
            Dictionary with training results (metrics, model_path, version)

        Raises:
            TrainingError: If training fails
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
            version = kwargs.get('version', '1.0.0')
            model_path = self.model_manager.save_model(model, model_id, version)

            # Register model
            self.model_manager.register_model(
                model_id=model_id,
                model_type=model_type,
                model_path=model_path,
                metadata={
                    'hyperparameters': hyperparameters or {},
                    'train_metrics': train_metrics,
                    'val_metrics': val_metrics
                },
                version=version
            )

            result = {
                'model_id': model_id,
                'version': version,
                'model_path': model_path,
                'metrics': {
                    'train': train_metrics,
                    'validation': val_metrics
                },
                'hyperparameters': hyperparameters or {}
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
                original_error=e
            )

    def validate(
        self,
        model: Any,
        validation_data: Any
    ) -> Dict[str, Any]:
        """
        Validate a model.

        Args:
            model: Trained model
            validation_data: Validation dataset

        Returns:
            Validation metrics
        """
        return self._evaluate(model, validation_data)

    def save_checkpoint(
        self,
        model: Any,
        model_id: str,
        epoch: int,
        checkpoint_dir: Optional[str] = None
    ) -> str:
        """
        Save training checkpoint.

        Args:
            model: Model to save
            model_id: Model ID
            epoch: Current epoch
            checkpoint_dir: Optional checkpoint directory

        Returns:
            Path to checkpoint file
        """
        import joblib

        if checkpoint_dir is None:
            checkpoint_dir = f"./checkpoints/{model_id}"

        Path(checkpoint_dir).mkdir(parents=True, exist_ok=True)
        checkpoint_path = os.path.join(checkpoint_dir, f"checkpoint_epoch_{epoch}.joblib")
        joblib.dump(model, checkpoint_path)

        logger.info(f"Checkpoint saved: {checkpoint_path}")
        return checkpoint_path

    def load_checkpoint(
        self,
        checkpoint_path: str
    ) -> Any:
        """
        Load training checkpoint.

        Args:
            checkpoint_path: Path to checkpoint file

        Returns:
            Loaded model
        """
        import joblib
        return joblib.load(checkpoint_path)

    def _create_model(
        self,
        model_type: str,
        hyperparameters: Dict[str, Any]
    ) -> Any:
        """
        Create model instance based on type.

        Args:
            model_type: Type of model
            hyperparameters: Model hyperparameters

        Returns:
            Model instance
        """
        from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
        from sklearn.linear_model import LogisticRegression, LinearRegression
        from sklearn.svm import SVC, SVR

        model_map = {
            'classification': RandomForestClassifier(**hyperparameters),
            'regression': RandomForestRegressor(**hyperparameters),
            'logistic_regression': LogisticRegression(**hyperparameters),
            'linear_regression': LinearRegression(**hyperparameters),
            'svm_classification': SVC(**hyperparameters),
            'svm_regression': SVR(**hyperparameters),
        }

        if model_type not in model_map:
            raise ValueError(f"Unknown model type: {model_type}")

        return model_map[model_type]

    def _evaluate(
        self,
        model: Any,
        data: Any
    ) -> Dict[str, Any]:
        """
        Evaluate model on data.

        Args:
            model: Trained model
            data: Dataset (X, y) tuple

        Returns:
            Evaluation metrics
        """
        from sklearn.metrics import (
            accuracy_score, precision_score, recall_score, f1_score,
            mean_squared_error, mean_absolute_error, r2_score
        )

        X, y = data
        y_pred = model.predict(X)

        # Determine if classification or regression
        if hasattr(model, 'predict_proba'):
            # Classification
            return {
                'accuracy': float(accuracy_score(y, y_pred)),
                'precision': float(precision_score(y, y_pred, average='weighted', zero_division=0)),
                'recall': float(recall_score(y, y_pred, average='weighted', zero_division=0)),
                'f1': float(f1_score(y, y_pred, average='weighted', zero_division=0))
            }
        else:
            # Regression
            return {
                'mse': float(mean_squared_error(y, y_pred)),
                'mae': float(mean_absolute_error(y, y_pred)),
                'r2': float(r2_score(y, y_pred))
            }


