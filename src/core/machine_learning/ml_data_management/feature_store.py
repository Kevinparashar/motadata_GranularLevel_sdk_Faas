"""
Feature Store

Centralized feature storage and retrieval.
"""

from typing import Dict, Any, Optional, List
import logging

from ...postgresql_database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class FeatureStore:
    """
    Centralized feature store.
    
    Handles feature registration, versioning, and serving (online/offline).
    """
    
    def __init__(
        self,
        db: DatabaseConnection,
        tenant_id: Optional[str] = None
    ):
        """
        Initialize feature store.
        
        Args:
            db: Database connection
            tenant_id: Optional tenant ID
        """
        self.db = db
        self.tenant_id = tenant_id
        
        logger.info(f"FeatureStore initialized for tenant: {tenant_id}")
    
    def register_feature(
        self,
        feature_name: str,
        feature_data: Any,
        version: str = "1.0.0",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Register a feature.
        
        Args:
            feature_name: Name of feature
            feature_data: Feature data
            version: Feature version
            metadata: Optional metadata
            
        Returns:
            Feature ID
        """
        import json
        
        query = """
        INSERT INTO ml_features (feature_name, feature_data, version, metadata, tenant_id)
        VALUES (%s, %s::jsonb, %s, %s::jsonb, %s)
        RETURNING id;
        """
        
        result = self.db.execute_query(
            query,
            (
                feature_name,
                json.dumps(feature_data),
                version,
                json.dumps(metadata or {}),
                self.tenant_id
            ),
            fetch_one=True
        )
        
        logger.info(f"Feature registered: {feature_name}")
        return str(result['id'])
    
    def get_feature(
        self,
        feature_name: str,
        version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get feature.
        
        Args:
            feature_name: Feature name
            version: Optional version
            
        Returns:
            Feature data or None
        """
        if version:
            query = """
            SELECT * FROM ml_features
            WHERE feature_name = %s AND version = %s AND tenant_id = %s;
            """
            params = (feature_name, version, self.tenant_id)
        else:
            query = """
            SELECT * FROM ml_features
            WHERE feature_name = %s AND tenant_id = %s
            ORDER BY created_at DESC LIMIT 1;
            """
            params = (feature_name, self.tenant_id)
        
        result = self.db.execute_query(query, params, fetch_one=True)
        return dict(result) if result else None
    
    def list_features(self) -> List[Dict[str, Any]]:
        """List all features."""
        query = """
        SELECT DISTINCT feature_name, version FROM ml_features
        WHERE tenant_id = %s;
        """
        
        results = self.db.execute_query(query, (self.tenant_id,))
        return [dict(row) for row in results]


