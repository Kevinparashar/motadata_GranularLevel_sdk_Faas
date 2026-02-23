"""
Model Version Data Access Layer (DAL)

Provides database abstraction for ML model version persistence.
Tables are assumed to exist (managed by migrations/DAL).
"""


import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.core.postgresql_database import DatabaseConnection  

logger = logging.getLogger(__name__)


class ModelVersionDAL:
    """
    Data Access Layer for ML model version persistence.

    Handles all database operations for ML model versions.
    Tables are assumed to exist (managed by migrations/DAL).
    """

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize Model Version DAL.

        Args:
            db_connection: Database connection instance.
        """
        self.db = db_connection

    async def register_version(
        self,
        model_id: str,
        version: str,
        model_path: str,
        tenant_id: Optional[str],
        metrics: Optional[Dict[str, Any]] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        environment: str = "dev",
    ) -> str:
        """
        Register a new model version.

        Args:
            model_id: Model identifier.
            version: Version string.
            model_path: Path to model file.
            tenant_id: Tenant identifier for tenant isolation.
            metrics: Optional model metrics.
            hyperparameters: Optional hyperparameters.
            metadata: Optional additional metadata.
            environment: Environment name (default: "dev").

        Returns:
            str: Version record ID.
        """
        full_metadata = {
            "metrics": metrics or {},
            "hyperparameters": hyperparameters or {},
            **(metadata or {}),
        }

        query = """
        INSERT INTO ml_model_versions (
            model_id, version, model_path, metrics, hyperparameters,
            metadata, environment, tenant_id, created_at
        )
        VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6::jsonb, $7, $8, $9)
        ON CONFLICT (model_id, version, tenant_id) DO UPDATE
        SET model_path = EXCLUDED.model_path,
            metrics = EXCLUDED.metrics,
            hyperparameters = EXCLUDED.hyperparameters,
            metadata = EXCLUDED.metadata,
            environment = EXCLUDED.environment,
            updated_at = $10
        RETURNING id;
        """

        now = datetime.now(timezone.utc)
        result = await self.db.execute_query(
            query,
            params=(
                model_id,
                version,
                model_path,
                json.dumps(metrics or {}),
                json.dumps(hyperparameters or {}),
                json.dumps(full_metadata),
                environment,
                tenant_id,
                now,
                now,
            ),
            fetch_one=True,
        )

        return str(result["id"])

    async def get_version(
        self, model_id: str, version: str, tenant_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get model version information.

        Args:
            model_id: Model identifier.
            version: Version string.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            Optional[Dict[str, Any]]: Version data if found, else None.
        """
        query = """
        SELECT * FROM ml_model_versions
        WHERE model_id = $1 AND version = $2
        """
        params: List[Any] = [model_id, version]

        if tenant_id:
            query += " AND tenant_id = $3"
            params.append(tenant_id)

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_one=True,
        )

        if not result:
            return None

        # Parse JSON fields
        version_data = dict(result)
        for field in ["metrics", "hyperparameters", "metadata"]:
            if version_data.get(field):
                version_data[field] = (
                    json.loads(version_data[field])
                    if isinstance(version_data[field], str)
                    else version_data[field]
                )

        return version_data

    async def list_versions(
        self,
        model_id: str,
        tenant_id: Optional[str] = None,
        environment: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List versions for a model.

        Args:
            model_id: Model identifier.
            tenant_id: Tenant identifier for tenant isolation.
            environment: Optional filter by environment.
            limit: Maximum number of versions to return.
            offset: Number of versions to skip.

        Returns:
            List[Dict[str, Any]]: List of version dictionaries.
        """
        query = """
        SELECT * FROM ml_model_versions
        WHERE model_id = $1
        """
        params: List[Any] = [model_id]

        if tenant_id:
            query += f" AND tenant_id = ${len(params) + 1}"
            params.append(tenant_id)

        if environment:
            query += f" AND environment = ${len(params) + 1}"
            params.append(environment)

        query += f" ORDER BY created_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
        params.extend([limit, offset])

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        # Parse JSON fields for each version
        if results:
            for version_data in results:
                for field in ["metrics", "hyperparameters", "metadata"]:
                    if version_data.get(field):
                        version_data[field] = (
                            json.loads(version_data[field])
                            if isinstance(version_data[field], str)
                            else version_data[field]
                        )

        return results if results else []

    async def delete_version(
        self, model_id: str, version: str, tenant_id: Optional[str] = None
    ) -> bool:
        """
        Delete model version from database.

        Args:
            model_id: Model identifier.
            version: Version string.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            bool: True if deleted, False if not found.
        """
        query = """
        DELETE FROM ml_model_versions
        WHERE model_id = $1 AND version = $2
        """
        params: List[Any] = [model_id, version]

        if tenant_id:
            query += " AND tenant_id = $3"
            params.append(tenant_id)

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=False,
        )

        return result > 0

    async def compare_versions(
        self,
        model_id: str,
        version1: str,
        version2: str,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compare two model versions.

        Args:
            model_id: Model identifier.
            version1: First version string.
            version2: Second version string.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            Dict[str, Any]: Comparison results.
        """
        v1 = await self.get_version(model_id, version1, tenant_id)
        v2 = await self.get_version(model_id, version2, tenant_id)

        if not v1 or not v2:
            return {"error": "One or both versions not found"}

        diff: Dict[str, Any] = {}

        # Compare metrics
        if v1.get("metrics") and v2.get("metrics"):
            metrics_diff = {}
            all_keys = set(v1["metrics"].keys()) | set(v2["metrics"].keys())
            for key in all_keys:
                val1 = v1["metrics"].get(key)
                val2 = v2["metrics"].get(key)
                if val1 != val2:
                    metrics_diff[key] = {"version1": val1, "version2": val2}
            if metrics_diff:
                diff["metrics"] = metrics_diff

        # Compare hyperparameters
        if v1.get("hyperparameters") and v2.get("hyperparameters"):
            hyperparams_diff = {}
            all_keys = set(v1["hyperparameters"].keys()) | set(v2["hyperparameters"].keys())
            for key in all_keys:
                val1 = v1["hyperparameters"].get(key)
                val2 = v2["hyperparameters"].get(key)
                if val1 != val2:
                    hyperparams_diff[key] = {"version1": val1, "version2": val2}
            if hyperparams_diff:
                diff["hyperparameters"] = hyperparams_diff

        return diff

