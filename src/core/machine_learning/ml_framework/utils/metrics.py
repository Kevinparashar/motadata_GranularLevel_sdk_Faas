"""
Metrics Calculator

Utilities for calculating ML metrics.
"""

import logging
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """
    Utility class for calculating ML metrics.

    Provides methods for classification and regression metrics.
    """

    @staticmethod
    def calculate_classification_metrics(
        y_true: Any, y_pred: Any, average: str = "weighted"
    ) -> Dict[str, float]:
        """
        Calculate classification metrics.

        Args:
            y_true: True labels
            y_pred: Predicted labels
            average: Averaging strategy for multi-class

        Returns:
            Dictionary of metrics
        """
        return {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision": float(precision_score(y_true, y_pred, average=average, zero_division=0)),  # type: ignore[arg-type]
            "recall": float(recall_score(y_true, y_pred, average=average, zero_division=0)),  # type: ignore[arg-type]
            "f1": float(f1_score(y_true, y_pred, average=average, zero_division=0)),  # type: ignore[arg-type]
        }

    @staticmethod
    def calculate_regression_metrics(y_true: Any, y_pred: Any) -> Dict[str, float]:
        """
        Calculate regression metrics.

        Args:
            y_true: True values
            y_pred: Predicted values

        Returns:
            Dictionary of metrics
        """
        return {
            "mse": float(mean_squared_error(y_true, y_pred)),
            "mae": float(mean_absolute_error(y_true, y_pred)),
            "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
            "r2": float(r2_score(y_true, y_pred)),
        }

    @staticmethod
    def get_confusion_matrix(y_true: Any, y_pred: Any) -> np.ndarray:
        """
        Get confusion matrix.

        Args:
            y_true: True labels
            y_pred: Predicted labels

        Returns:
            Confusion matrix
        """
        return confusion_matrix(y_true, y_pred)

    @staticmethod
    def get_classification_report(
        y_true: Any, y_pred: Any, target_names: Optional[List[str]] = None
    ) -> str:
        """
        Get classification report.

        Args:
            y_true: True labels
            y_pred: Predicted labels
            target_names: Optional class names

        Returns:
            Classification report string
        """
        result = classification_report(y_true, y_pred, target_names=target_names, output_dict=False)
        return str(result)
