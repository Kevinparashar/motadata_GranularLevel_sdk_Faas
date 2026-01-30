"""
ML Framework Factory and Convenience Functions

High-level convenience functions for common ML operations.
"""

# Standard library imports
from typing import Optional

# Local application/library specific imports
from ...cache_mechanism import CacheConfig, CacheMechanism
from ...postgresql_database.connection import DatabaseConnection
from .data_processor import DataProcessor
from .ml_system import MLSystem
from .model_manager import ModelManager
from .model_registry import ModelRegistry
from .predictor import Predictor
from .trainer import Trainer


def create_ml_system(
    db: DatabaseConnection,
    cache: Optional[CacheMechanism] = None,
    cache_config: Optional[CacheConfig] = None,
    max_memory_mb: int = 2048,
    tenant_id: Optional[str] = None,
) -> MLSystem:
    """
    Create and initialize ML system.

    Args:
        db: Database connection
        cache: Optional cache mechanism
        cache_config: Optional cache configuration
        max_memory_mb: Maximum memory for loaded models
        tenant_id: Optional tenant ID

    Returns:
        Initialized MLSystem instance
    """
    return MLSystem(
        db=db,
        cache=cache,
        cache_config=cache_config,
        max_memory_mb=max_memory_mb,
        tenant_id=tenant_id,
    )


def create_model_manager(
    db: DatabaseConnection, storage_path: str = "./models", tenant_id: Optional[str] = None
) -> ModelManager:
    """
    Create and initialize model manager.

    Args:
        db: Database connection
        storage_path: Base path for model storage
        tenant_id: Optional tenant ID

    Returns:
        Initialized ModelManager instance
    """
    return ModelManager(db=db, storage_path=storage_path, tenant_id=tenant_id)


def create_trainer(db: DatabaseConnection, tenant_id: Optional[str] = None) -> Trainer:
    """
    Create and initialize trainer.

    Args:
        db: Database connection
        tenant_id: Optional tenant ID

    Returns:
        Initialized Trainer instance
    """
    return Trainer(db=db, tenant_id=tenant_id)


def create_predictor(
    model_manager: ModelManager,
    cache: Optional[CacheMechanism] = None,
    tenant_id: Optional[str] = None,
) -> Predictor:
    """
    Create and initialize predictor.

    Args:
        model_manager: Model manager instance
        cache: Optional cache mechanism
        tenant_id: Optional tenant ID

    Returns:
        Initialized Predictor instance
    """
    return Predictor(model_manager=model_manager, cache=cache, tenant_id=tenant_id)


def create_data_processor(tenant_id: Optional[str] = None) -> DataProcessor:
    """
    Create and initialize data processor.

    Args:
        tenant_id: Optional tenant ID

    Returns:
        Initialized DataProcessor instance
    """
    return DataProcessor(tenant_id=tenant_id)


def create_model_registry(db: DatabaseConnection, tenant_id: Optional[str] = None) -> ModelRegistry:
    """
    Create and initialize model registry.

    Args:
        db: Database connection
        tenant_id: Optional tenant ID

    Returns:
        Initialized ModelRegistry instance
    """
    return ModelRegistry(db=db, tenant_id=tenant_id)
