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


def create_data_manager(db: DatabaseConnection, tenant_id: Optional[str] = None) -> DataManager:
    """
    Create data manager.
    
    Args:
        db (DatabaseConnection): Database connection/handle.
        tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
    
    Returns:
        DataManager: Result of the operation.
    """
    return DataManager(db=db, tenant_id=tenant_id)


def create_data_loader() -> DataLoader:
    """
    Create data loader.
    
    Returns:
        DataLoader: Result of the operation.
    """
    return DataLoader()


def create_data_validator() -> DataValidator:
    """
    Create data validator.
    
    Returns:
        DataValidator: Result of the operation.
    """
    return DataValidator()


def create_feature_store(db: DatabaseConnection, tenant_id: Optional[str] = None) -> FeatureStore:
    """
    Create feature store.
    
    Args:
        db (DatabaseConnection): Database connection/handle.
        tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
    
    Returns:
        FeatureStore: Result of the operation.
    """
    return FeatureStore(db=db, tenant_id=tenant_id)


def create_data_pipeline(pipeline_id: str, tenant_id: Optional[str] = None) -> DataPipeline:
    """
    Create data pipeline.
    
    Args:
        pipeline_id (str): Input parameter for this operation.
        tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
    
    Returns:
        DataPipeline: Result of the operation.
    """
    return DataPipeline(pipeline_id=pipeline_id, tenant_id=tenant_id)
