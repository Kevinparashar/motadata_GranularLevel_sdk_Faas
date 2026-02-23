"""
Model Data Access Layer (DAL)

Provides database abstraction for ML model persistence.
Tables are assumed to exist (managed by migrations/DAL).
"""


import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.core.postgresql_database import DatabaseConnection 

logger = logging.getLogger(__name__)


class ModelDAL:
    """
    Data Access Layer for ML model persistence.

    Handles all database operations for ML models.
    Tables are assumed to exist (managed by migrations/DAL).
    """

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize Model DAL.

        Args:
            db_connection: Database connection instance.
        """
        self.db = db_connection

    async def register_model(
        self,
        model_id: str,
        model_type: str,
        model_path: str,
        version: str,
        tenant_id: Optional[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Register a new model.

        Args:
            model_id: Model identifier.
            model_type: Model type.
            model_path: Path to model file.
            version: Model version.
            tenant_id: Tenant identifier for tenant isolation.
            metadata: Optional model metadata.

        Returns:
            str: Model record ID.
        """
        query = """
        INSERT INTO ml_models (model_id, model_type, model_path, metadata, version, tenant_id, created_at)
        VALUES ($1, $2, $3, $4::jsonb, $5, $6, $7)
        ON CONFLICT (model_id, version, tenant_id) DO UPDATE
        SET model_path = EXCLUDED.model_path,
            metadata = EXCLUDED.metadata,
            updated_at = $8
        RETURNING id;
        """

        metadata_json = json.dumps(metadata or {})
        now = datetime.now(timezone.utc)

        result = await self.db.execute_query(
            query,
            params=(model_id, model_type, model_path, metadata_json, version, tenant_id, now, now),
            fetch_one=True,
        )

        return str(result["id"])

    async def get_model(
        self, model_id: str, version: Optional[str] = None, tenant_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get model information.

        Args:
            model_id: Model identifier.
            version: Optional model version.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            Optional[Dict[str, Any]]: Model data if found, else None.
        """
        query = """
        SELECT * FROM ml_models
        WHERE model_id = $1
        """
        params: List[Any] = [model_id]

        if version:
            query += " AND version = $" + str(len(params) + 1)
            params.append(version)

        if tenant_id:
            query += " AND tenant_id = $" + str(len(params) + 1)
            params.append(tenant_id)

        query += " ORDER BY created_at DESC LIMIT 1"

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_one=True,
        )

        if not result:
            return None

        # Parse JSON metadata
        model = dict(result)
        if model.get("metadata"):
            model["metadata"] = (
                json.loads(model["metadata"])
                if isinstance(model["metadata"], str)
                else model["metadata"]
            )

        return model

    async def list_models(
        self,
        tenant_id: Optional[str] = None,
        model_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List models.

        Args:
            tenant_id: Tenant identifier for tenant isolation.
            model_type: Optional filter by model type.
            limit: Maximum number of models to return.
            offset: Number of models to skip.

        Returns:
            List[Dict[str, Any]]: List of model dictionaries.
        """
        query = """
        SELECT * FROM ml_models
        WHERE 1=1
        """
        params: List[Any] = []

        if tenant_id:
            query += f" AND tenant_id = ${len(params) + 1}"
            params.append(tenant_id)

        if model_type:
            query += f" AND model_type = ${len(params) + 1}"
            params.append(model_type)

        query += f" ORDER BY created_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
        params.extend([limit, offset])

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        # Parse JSON metadata for each model
        if results:
            for model in results:
                if model.get("metadata"):
                    model["metadata"] = (
                        json.loads(model["metadata"])
                        if isinstance(model["metadata"], str)
                        else model["metadata"]
                    )

        return results if results else []

    async def delete_model(
        self, model_id: str, version: Optional[str] = None, tenant_id: Optional[str] = None
    ) -> bool:
        """
        Delete model from database.

        Args:
            model_id: Model identifier.
            version: Optional model version.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            bool: True if deleted, False if not found.
        """
        query = """
        DELETE FROM ml_models
        WHERE model_id = $1
        """
        params: List[Any] = [model_id]

        if version:
            query += f" AND version = ${len(params) + 1}"
            params.append(version)

        if tenant_id:
            query += f" AND tenant_id = ${len(params) + 1}"
            params.append(tenant_id)

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=False,
        )

        return result > 0

    async def archive_model(
        self, model_id: str, version: Optional[str] = None, tenant_id: Optional[str] = None
    ) -> bool:
        """
        Archive model (mark as archived).

        Args:
            model_id: Model identifier.
            version: Optional model version.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            bool: True if archived, False if not found.
        """
        query = """
        UPDATE ml_models
        SET archived = TRUE, updated_at = CURRENT_TIMESTAMP
        WHERE model_id = $1
        """
        params: List[Any] = [model_id]

        if version:
            query += f" AND version = ${len(params) + 1}"
            params.append(version)

        if tenant_id:
            query += f" AND tenant_id = ${len(params) + 1}"
            params.append(tenant_id)

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=False,
        )

        return result > 0

    async def model_exists(
        self, model_id: str, version: Optional[str] = None, tenant_id: Optional[str] = None
    ) -> bool:
        """
        Check if model exists.

        Args:
            model_id: Model identifier.
            version: Optional model version.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            bool: True if exists, False otherwise.
        """
        query = """
        SELECT 1 FROM ml_models
        WHERE model_id = $1
        """
        params: List[Any] = [model_id]

        if version:
            query += f" AND version = ${len(params) + 1}"
            params.append(version)

        if tenant_id:
            query += f" AND tenant_id = ${len(params) + 1}"
            params.append(tenant_id)

        query += " LIMIT 1"

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_one=True,
        )

        return result is not None

