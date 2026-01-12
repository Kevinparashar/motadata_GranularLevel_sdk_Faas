"""
Data Management Factory and Convenience Functions

High-level convenience functions for data management operations.
"""

# Standard library imports
from typing import Optional

# Local application/library specific imports
from ...postgresql_database.connection import DatabaseConnection
from .data_loader import DataLoader
from .data_manager import DataManager
from .data_pipeline import DataPipeline
from .data_validator import DataValidator
from .feature_store import FeatureStore


def create_data_manager(
    db: DatabaseConnection,
    tenant_id: Optional[str] = None
) -> DataManager:
    """Create data manager."""
    return DataManager(db=db, tenant_id=tenant_id)


def create_data_loader() -> DataLoader:
    """Create data loader."""
    return DataLoader()


def create_data_validator() -> DataValidator:
    """Create data validator."""
    return DataValidator()


def create_feature_store(
    db: DatabaseConnection,
    tenant_id: Optional[str] = None
) -> FeatureStore:
    """Create feature store."""
    return FeatureStore(db=db, tenant_id=tenant_id)


def create_data_pipeline(
    pipeline_id: str,
    tenant_id: Optional[str] = None
) -> DataPipeline:
    """Create data pipeline."""
    return DataPipeline(pipeline_id=pipeline_id, tenant_id=tenant_id)


