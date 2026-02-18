"""
Feature Store

Centralized feature storage and retrieval.
"""


import logging
from typing import Any, Dict, List, Optional

from ...postgresql_database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class FeatureStore:
    """
    Centralized feature store.

    Handles feature registration, versioning, and serving (online/offline).
    """

    def __init__(self, db: DatabaseConnection, tenant_id: Optional[str] = None):
        """
        Initialize feature store.
        
        Args:
            db (DatabaseConnection): Database connection/handle.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        """
        self.db = db
        self.tenant_id = tenant_id

        logger.info(f"FeatureStore initialized for tenant: {tenant_id}")

    async def register_feature(
        self,
        feature_name: str,
        feature_data: Any,
        version: str = "1.0.0",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Register a feature asynchronously.
        
        Args:
            feature_name (str): Input parameter for this operation.
            feature_data (Any): Input parameter for this operation.
            version (str): Input parameter for this operation.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
        
        Returns:
            str: Returned text value.
        """
        import json

        query = """
        INSERT INTO ml_features (feature_name, feature_data, version, metadata, tenant_id)
        VALUES ($1, $2::jsonb, $3, $4::jsonb, $5)
        RETURNING id;
        """

        result = await self.db.execute_query(
            query,
            (
                feature_name,
                json.dumps(feature_data),
                version,
                json.dumps(metadata or {}),
                self.tenant_id,
            ),
            fetch_one=True,
        )

        logger.info(f"Feature registered: {feature_name}")
        return str(result["id"])

    async def get_feature(
        self, feature_name: str, version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get feature asynchronously.
        
        Args:
            feature_name (str): Input parameter for this operation.
            version (Optional[str]): Input parameter for this operation.
        
        Returns:
            Optional[Dict[str, Any]]: Dictionary result of the operation.
        """
        if version:
            query = """
            SELECT * FROM ml_features
            WHERE feature_name = $1 AND version = $2 AND tenant_id = $3;
            """
            params = (feature_name, version, self.tenant_id)
        else:
            query = """
            SELECT * FROM ml_features
            WHERE feature_name = $1 AND tenant_id = $2
            ORDER BY created_at DESC LIMIT 1;
            """
            params = (feature_name, self.tenant_id)

        result = await self.db.execute_query(query, params, fetch_one=True)
        return dict(result) if result else None

    async def list_features(self) -> List[Dict[str, Any]]:
        """
        List all features asynchronously.
        
        Returns:
            List[Dict[str, Any]]: Dictionary result of the operation.
        """
        query = """
        SELECT DISTINCT feature_name, version FROM ml_features
        WHERE tenant_id = $1;
        """

        results = await self.db.execute_query(query, (self.tenant_id,))
        return [dict(row) for row in results]
