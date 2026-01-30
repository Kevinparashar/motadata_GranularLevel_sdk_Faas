"""
ML System

Main ML system orchestrator providing unified interface for ML operations.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from ...cache_mechanism import CacheConfig, CacheMechanism
from ...postgresql_database.connection import DatabaseConnection
from .data_processor import DataProcessor
from .exceptions import ModelNotFoundError, PredictionError, TrainingError
from .model_manager import ModelManager
from .model_registry import ModelRegistry
from .predictor import Predictor
from .trainer import Trainer

logger = logging.getLogger(__name__)


class MLSystem:
    """
    Main ML system orchestrator.

    Provides unified interface for training, inference, and model management
    with multi-tenant support, memory management, and integration with
    existing SDK components.
    """

    def __init__(
        self,
        db: DatabaseConnection,
        cache: Optional[CacheMechanism] = None,
        cache_config: Optional[CacheConfig] = None,
        max_memory_mb: int = 2048,
        tenant_id: Optional[str] = None,
    ):
        """
        Initialize ML system.

        Args:
            db: Database connection for model metadata storage
            cache: Optional cache mechanism for predictions
            cache_config: Optional cache configuration
            max_memory_mb: Maximum memory limit for loaded models (MB)
            tenant_id: Optional tenant ID for multi-tenant support
        """
        self.db = db
        self.tenant_id = tenant_id
        self.max_memory_mb = max_memory_mb
        self.cache = cache or CacheMechanism(cache_config or CacheConfig())

        # Initialize components
        self.model_manager = ModelManager(db, tenant_id=tenant_id)
        self.trainer = Trainer(db, tenant_id=tenant_id)
        self.predictor = Predictor(
            model_manager=self.model_manager, cache=self.cache, tenant_id=tenant_id
        )
        self.data_processor = DataProcessor(tenant_id=tenant_id)
        self.model_registry = ModelRegistry(db, tenant_id=tenant_id)

        # Track loaded models in memory
        self._loaded_models: Dict[str, Any] = {}
        self._model_memory_usage: Dict[str, int] = {}  # MB

        logger.info(f"MLSystem initialized for tenant: {tenant_id}")

    def train_model(
        self,
        model_id: str,
        model_type: str,
        training_data: Any,
        hyperparameters: Optional[Dict[str, Any]] = None,
        validation_data: Optional[Any] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Train a new model.

        Args:
            model_id: Unique identifier for the model
            model_type: Type of model (e.g., 'classification', 'regression')
            training_data: Training dataset
            hyperparameters: Optional hyperparameters
            validation_data: Optional validation dataset
            **kwargs: Additional training parameters

        Returns:
            Dictionary with training results (metrics, model_path, etc.)

        Raises:
            TrainingError: If training fails
        """
        try:
            logger.info(f"Starting training for model: {model_id}")

            # Process training data
            processed_data = self.data_processor.preprocess(training_data, model_type=model_type)

            processed_val_data = None
            if validation_data:
                processed_val_data = self.data_processor.preprocess(
                    validation_data, model_type=model_type
                )

            # Train model
            training_result = self.trainer.train(
                model_id=model_id,
                model_type=model_type,
                training_data=processed_data,
                validation_data=processed_val_data,
                hyperparameters=hyperparameters or {},
                tenant_id=self.tenant_id,
                **kwargs,
            )

            # Register model
            model_path = training_result.get("model_path")
            if not model_path:
                raise TrainingError(
                    "Training result missing model_path",
                    model_id=model_id,
                    stage="model_registration"
                )
            
            self.model_registry.register_version(
                model_id=model_id,
                version=training_result.get("version", "1.0.0"),
                model_path=model_path,
                metrics=training_result.get("metrics", {}),
                hyperparameters=hyperparameters or {},
            )

            logger.info(f"Training completed for model: {model_id}")
            return training_result

        except Exception as e:
            error_msg = f"Training failed for model {model_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise TrainingError(
                error_msg, model_id=model_id, hyperparameters=hyperparameters, original_error=e
            )

    def predict(
        self, model_id: str, input_data: Any, version: Optional[str] = None, use_cache: bool = True
    ) -> Any:
        """
        Make a single prediction.

        Args:
            model_id: ID of the model
            input_data: Input data for prediction
            version: Optional model version (uses latest if not specified)
            use_cache: Whether to use prediction cache

        Returns:
            Prediction result

        Raises:
            PredictionError: If prediction fails
            ModelNotFoundError: If model is not found
        """
        try:
            # Check cache
            if use_cache:
                cache_key = f"ml_prediction:{self.tenant_id}:{model_id}:{hash(str(input_data))}"
                cached_result = self.cache.get(cache_key)
                if cached_result:
                    logger.debug(f"Cache hit for model: {model_id}")
                    return cached_result

            # Load model if not loaded
            if model_id not in self._loaded_models:
                self._load_model(model_id, version)

            # Preprocess input
            processed_input = self.data_processor.preprocess(input_data, is_training=False)

            # Make prediction
            result = self.predictor.predict(
                model=self._loaded_models[model_id], input_data=processed_input
            )

            # Postprocess result
            final_result = self.data_processor.postprocess(result)

            # Cache result
            if use_cache:
                self.cache.set(cache_key, final_result, ttl=3600)

            return final_result

        except ModelNotFoundError:
            raise
        except Exception as e:
            error_msg = f"Prediction failed for model {model_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise PredictionError(
                error_msg,
                model_id=model_id,
                input_data=input_data,
                operation="predict",
                original_error=e,
            )

    def predict_batch(
        self,
        model_id: str,
        input_batch: List[Any],
        version: Optional[str] = None,
        batch_size: int = 32,
    ) -> List[Any]:
        """
        Make batch predictions.

        Args:
            model_id: ID of the model
            input_batch: List of input data
            version: Optional model version
            batch_size: Batch size for processing

        Returns:
            List of prediction results
        """
        try:
            # Load model if not loaded
            if model_id not in self._loaded_models:
                self._load_model(model_id, version)

            results = []
            for i in range(0, len(input_batch), batch_size):
                batch = input_batch[i : i + batch_size]

                # Preprocess batch
                processed_batch = [
                    self.data_processor.preprocess(item, is_training=False) for item in batch
                ]

                # Make predictions
                batch_results = self.predictor.predict_batch(
                    model=self._loaded_models[model_id], input_batch=processed_batch
                )

                # Postprocess results
                processed_results = [
                    self.data_processor.postprocess(result) for result in batch_results
                ]

                results.extend(processed_results)

            return results

        except Exception as e:
            error_msg = f"Batch prediction failed for model {model_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise PredictionError(
                error_msg, model_id=model_id, operation="predict_batch", original_error=e
            )

    async def predict_async(
        self, model_id: str, input_data: Any, version: Optional[str] = None
    ) -> Any:
        """
        Make async prediction.

        Args:
            model_id: ID of the model
            input_data: Input data for prediction
            version: Optional model version

        Returns:
            Prediction result
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.predict, model_id, input_data, version)

    def load_model(self, model_id: str, version: Optional[str] = None) -> None:
        """
        Load model into memory.

        Args:
            model_id: ID of the model
            version: Optional model version

        Raises:
            ModelNotFoundError: If model is not found
        """
        self._load_model(model_id, version)

    def unload_model(self, model_id: str) -> None:
        """
        Unload model from memory.

        Args:
            model_id: ID of the model
        """
        if model_id in self._loaded_models:
            del self._loaded_models[model_id]
            if model_id in self._model_memory_usage:
                del self._model_memory_usage[model_id]
            logger.info(f"Model unloaded: {model_id}")

    def get_model_info(self, model_id: str, version: Optional[str] = None) -> Dict[str, Any]:
        """
        Get model metadata and information.

        Args:
            model_id: ID of the model
            version: Optional model version

        Returns:
            Dictionary with model information
        """
        result = self.model_registry.get_model_version(model_id, version)
        if result is None:
            raise ModelNotFoundError(f"Model not found: {model_id}", model_id=model_id, version=version)
        return result

    def _load_model(self, model_id: str, version: Optional[str] = None) -> None:
        """Internal method to load model with memory management."""
        # Check if already loaded
        if model_id in self._loaded_models:
            return

        # Check memory limits
        model_info = self.model_registry.get_model_version(model_id, version)
        if not model_info:
            raise ModelNotFoundError(
                f"Model not found: {model_id}", model_id=model_id, version=version
            )

        # Load model through model manager
        model = self.model_manager.load_model(model_id, version)

        # Track memory usage (simplified - actual implementation would measure)
        estimated_memory = 100  # MB (placeholder)
        current_memory = sum(self._model_memory_usage.values())

        if current_memory + estimated_memory > self.max_memory_mb:
            # Unload least recently used models
            logger.warning("Memory limit reached, unloading old models")
            # Simple strategy: unload first model
            if self._loaded_models:
                first_model = next(iter(self._loaded_models))
                self.unload_model(first_model)

        self._loaded_models[model_id] = model
        self._model_memory_usage[model_id] = estimated_memory
        logger.info(f"Model loaded: {model_id}")
