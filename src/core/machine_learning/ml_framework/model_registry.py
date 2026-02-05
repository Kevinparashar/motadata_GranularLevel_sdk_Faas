"""
Model Registry

Model versioning and registry management.
"""


import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

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

        # Note: _ensure_tables() is now async, so it should be called externally after __init__
        # await self._ensure_tables()  # Cannot await in __init__
        logger.info(f"ModelRegistry initialized for tenant: {tenant_id}")

    async def initialize(self) -> None:
        """
        Initialize ModelRegistry asynchronously (creates database tables).
        
        This should be called after __init__ to ensure database tables exist.
        
        Example:
            >>> registry = ModelRegistry(db, tenant_id="tenant_123")
            >>> await registry.initialize()
        
        Returns:
            None: Result of the operation.
        """
        await self._ensure_tables()

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
        import json

        full_metadata = {
            "metrics": metrics or {},
            "hyperparameters": hyperparameters or {},
            **(metadata or {}),
        }

        query = """
        INSERT INTO ml_model_versions (
            model_id, version, model_path, metrics, hyperparameters,
            metadata, tenant_id, created_at
        )
        VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6::jsonb, $7, $8)
        ON CONFLICT (model_id, version, tenant_id) DO UPDATE
        SET model_path = EXCLUDED.model_path,
            metrics = EXCLUDED.metrics,
            hyperparameters = EXCLUDED.hyperparameters,
            metadata = EXCLUDED.metadata,
            updated_at = $9
        RETURNING id;
        """

        now = datetime.now(timezone.utc)
        result = await self.db.execute_query(
            query,
            (
                model_id,
                version,
                model_path,
                json.dumps(metrics or {}),
                json.dumps(hyperparameters or {}),
                json.dumps(full_metadata),
                self.tenant_id,
                now,
                now,
            ),
            fetch_one=True,
        )

        logger.info(f"Model version registered: {model_id} v{version}")
        return str(result["id"])

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
        if version:
            query = """
            SELECT * FROM ml_model_versions
            WHERE model_id = $1 AND version = $2 AND tenant_id = $3;
            """
            params = (model_id, version, self.tenant_id)
        else:
            query = """
            SELECT * FROM ml_model_versions
            WHERE model_id = $1 AND tenant_id = $2
            ORDER BY created_at DESC
            LIMIT 1;
            """
            params = (model_id, self.tenant_id)

        result = await self.db.execute_query(query, params, fetch_one=True)
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
        v1 = await self.get_model_version(model_id, version1)
        v2 = await self.get_model_version(model_id, version2)

        if not v1 or not v2:
            raise ModelNotFoundError(
                f"One or both versions not found: {version1}, {version2}", model_id=model_id
            )

        return {
            "version1": v1,
            "version2": v2,
            "metrics_diff": self._compare_metrics(v1.get("metrics", {}), v2.get("metrics", {})),
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

    async def _ensure_tables(self) -> None:
        """
        Ensure required database tables exist asynchronously.
        
        Returns:
            None: Result of the operation.
        """
        query = """
        CREATE TABLE IF NOT EXISTS ml_model_versions (
            id SERIAL PRIMARY KEY,
            model_id VARCHAR(255) NOT NULL,
            version VARCHAR(50) NOT NULL,
            model_path TEXT NOT NULL,
            metrics JSONB,
            hyperparameters JSONB,
            metadata JSONB,
            environment VARCHAR(50) DEFAULT 'dev',
            tenant_id VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(model_id, version, tenant_id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_ml_versions_model ON ml_model_versions(model_id, tenant_id);
        CREATE INDEX IF NOT EXISTS idx_ml_versions_env ON ml_model_versions(environment);
        """

        await self.db.execute_query(query)
