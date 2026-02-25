"""
Model Registry

Model versioning and registry management.
"""


from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from ...faas.shared.dal.model_version_dal import ModelVersionDAL  # type: ignore[import-untyped]

from ...postgresql_database.connection import DatabaseConnection
from .exceptions import ModelNotFoundError

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Manages model versioning and registry.

    Handles model version management, metadata storage, lineage tracking,
    and model comparison.
    """

    def __init__(self, db: DatabaseConnection, tenant_id: Optional[str] = None):
        """
        Initialize model registry.
        
        Args:
            db (DatabaseConnection): Database connection/handle.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        """
        self.db = db
        self.tenant_id = tenant_id
        # Initialize ModelVersionDAL
        from ...faas.shared.dal.model_version_dal import ModelVersionDAL  # type: ignore[import-untyped]
        self.model_version_dal = ModelVersionDAL(db)

        logger.info(f"ModelRegistry initialized for tenant: {tenant_id}")

    async def initialize(self) -> None:
        """
        Initialize ModelRegistry asynchronously.
        
        This method is kept for backward compatibility but no longer creates tables.
        Tables are assumed to exist (managed by migrations/DAL).
        
        Example:
            >>> registry = ModelRegistry(db, tenant_id="tenant_123")
            >>> await registry.initialize()
        
        Returns:
            None: Result of the operation.
        """
        # Tables are assumed to exist (managed by migrations/DAL)
        pass

    async def register_version(
        self,
        model_id: str,
        version: str,
        model_path: str,
        metrics: Optional[Dict[str, Any]] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Register a new model version asynchronously.
        
        Args:
            model_id (str): Input parameter for this operation.
            version (str): Input parameter for this operation.
            model_path (str): Input parameter for this operation.
            metrics (Optional[Dict[str, Any]]): Input parameter for this operation.
            hyperparameters (Optional[Dict[str, Any]]): Input parameter for this operation.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
        
        Returns:
            str: Returned text value.
        """
        # Use DAL to register version
        version_record_id = await self.model_version_dal.register_version(
            model_id=model_id,
            version=version,
            model_path=model_path,
            tenant_id=self.tenant_id,
            metrics=metrics,
            hyperparameters=hyperparameters,
            metadata=metadata,
        )

        logger.info(f"Model version registered: {model_id} v{version}")
        return version_record_id

    async def get_model_version(
        self, model_id: str, version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get specific model version asynchronously.
        
        Args:
            model_id (str): Input parameter for this operation.
            version (Optional[str]): Input parameter for this operation.
        
        Returns:
            Optional[Dict[str, Any]]: Dictionary result of the operation.
        """
        # Use DAL to get version
        result = await self.model_version_dal.get_version(model_id, version or "latest", self.tenant_id)
        
        # If version is None, get latest
        if not result and version is None:
            versions = await self.model_version_dal.list_versions(
                model_id, self.tenant_id, limit=1, offset=0
            )
            result = versions[0] if versions else None
        return dict(result) if result else None

    async def list_versions(self, model_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List all versions of a model asynchronously.
        
        Args:
            model_id (str): Input parameter for this operation.
            limit (int): Input parameter for this operation.
        
        Returns:
            List[Dict[str, Any]]: Dictionary result of the operation.
        """
        query = """
        SELECT * FROM ml_model_versions
        WHERE model_id = $1 AND tenant_id = $2
        ORDER BY created_at DESC
        LIMIT $3;
        """

        results = await self.db.execute_query(query, (model_id, self.tenant_id, limit))
        return [dict(row) for row in results]

    async def promote_version(self, model_id: str, version: str, environment: str) -> None:
        """
        Promote model version to environment (dev, staging, prod) asynchronously.
        
        Args:
            model_id (str): Input parameter for this operation.
            version (str): Input parameter for this operation.
            environment (str): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        """
        query = """
        UPDATE ml_model_versions
        SET environment = $1, updated_at = $2
        WHERE model_id = $3 AND version = $4 AND tenant_id = $5;
        """

        await self.db.execute_query(
            query, (environment, datetime.now(timezone.utc), model_id, version, self.tenant_id)
        )

        logger.info(f"Model version promoted: {model_id} v{version} to {environment}")

    async def compare_versions(self, model_id: str, version1: str, version2: str) -> Dict[str, Any]:
        """
        Compare two model versions asynchronously.
        
        Args:
            model_id (str): Input parameter for this operation.
            version1 (str): Input parameter for this operation.
            version2 (str): Input parameter for this operation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        
        Raises:
            ModelNotFoundError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        # Use DAL to compare versions
        diff = await self.model_version_dal.compare_versions(
            model_id, version1, version2, self.tenant_id
        )

        if "error" in diff:
            raise ModelNotFoundError(
                f"One or both versions not found: {version1}, {version2}", model_id=model_id
            )

        v1 = await self.get_model_version(model_id, version1)
        v2 = await self.get_model_version(model_id, version2)

        return {
            "version1": v1,
            "version2": v2,
            "metrics_diff": diff.get("metrics", {}),
            "hyperparameters_diff": diff.get("hyperparameters", {}),
        }

    async def get_lineage(self, model_id: str, version: Optional[str] = None) -> Dict[str, Any]:
        """
        Get model lineage (training data, parent models, etc.) asynchronously.
        
        Args:
            model_id (str): Input parameter for this operation.
            version (Optional[str]): Input parameter for this operation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        version_info = await self.get_model_version(model_id, version)
        if not version_info:
            return {}

        return {
            "model_id": model_id,
            "version": version_info.get("version"),
            "created_at": version_info.get("created_at"),
            "hyperparameters": version_info.get("hyperparameters", {}),
            "metrics": version_info.get("metrics", {}),
        }

    def _compare_metrics(
        self, metrics1: Dict[str, Any], metrics2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare metrics between two versions.
        
        Args:
            metrics1 (Dict[str, Any]): Input parameter for this operation.
            metrics2 (Dict[str, Any]): Input parameter for this operation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        diff = {}
        all_keys = set(metrics1.keys()) | set(metrics2.keys())

        for key in all_keys:
            val1 = metrics1.get(key)
            val2 = metrics2.get(key)

            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                diff[key] = {"version1": val1, "version2": val2, "difference": val2 - val1}

        return diff
