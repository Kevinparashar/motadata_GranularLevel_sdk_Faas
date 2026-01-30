"""
Model Serialization

Utilities for saving and loading models.
"""

import logging
import pickle
from pathlib import Path
from typing import Any

import joblib

logger = logging.getLogger(__name__)


class ModelSerializer:
    """
    Utility class for model serialization.

    Handles saving and loading models in various formats.
    """

    @staticmethod
    def save_model(model: Any, filepath: str, format: str = "joblib") -> str:
        """
        Save model to file.

        Args:
            model: Model object to save
            filepath: Path to save file
            format: Serialization format (joblib, pickle)

        Returns:
            Path to saved file
        """
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        if format == "joblib":
            joblib.dump(model, filepath)
        elif format == "pickle":
            with open(filepath, "wb") as f:
                pickle.dump(model, f)
        else:
            raise ValueError(f"Unknown format: {format}")

        logger.info(f"Model saved: {filepath}")
        return filepath

    @staticmethod
    def load_model(filepath: str, format: str = "joblib") -> Any:
        """
        Load model from file.

        Args:
            filepath: Path to model file
            format: Serialization format (joblib, pickle)

        Returns:
            Loaded model object
        """
        if format == "joblib":
            return joblib.load(filepath)
        elif format == "pickle":
            with open(filepath, "rb") as f:
                return pickle.load(f)
        else:
            raise ValueError(f"Unknown format: {format}")
