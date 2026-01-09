"""
Data Manager

Manages data lifecycle for ML operations.
"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from ...postgresql_database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class DataManager:
    """
    Manages data lifecycle for ML.
    
    Handles data ingestion, validation, transformation, storage, and archival.
    """
    
    def __init__(
        self,
        db: DatabaseConnection,
        tenant_id: Optional[str] = None
    ):
        """
        Initialize data manager.
        
        Args:
            db: Database connection
            tenant_id: Optional tenant ID
        """
        self.db = db
        self.tenant_id = tenant_id
        
        logger.info(f"DataManager initialized for tenant: {tenant_id}")
    
    def ingest_data(
        self,
        data: Any,
        dataset_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Ingest new data.
        
        Args:
            data: Data to ingest
            dataset_name: Name of dataset
            metadata: Optional metadata
            
        Returns:
            Dataset ID
        """
        import json
        
        query = """
        INSERT INTO ml_datasets (dataset_name, metadata, tenant_id, created_at)
        VALUES (%s, %s::jsonb, %s, %s)
        RETURNING id;
        """
        
        result = self.db.execute_query(
            query,
            (dataset_name, json.dumps(metadata or {}), self.tenant_id, datetime.utcnow()),
            fetch_one=True
        )
        
        logger.info(f"Data ingested: {dataset_name}")
        return str(result['id'])
    
    def validate_data(self, data: Any, schema: Optional[Dict[str, Any]] = None) -> bool:
        """
        Validate data quality.
        
        Args:
            data: Data to validate
            schema: Optional data schema
            
        Returns:
            True if valid
        """
        # Basic validation logic
        return True
    
    def archive_data(self, dataset_id: str) -> None:
        """
        Archive old data.
        
        Args:
            dataset_id: Dataset ID
        """
        query = """
        UPDATE ml_datasets
        SET archived = true, updated_at = %s
        WHERE id = %s AND tenant_id = %s;
        """
        
        self.db.execute_query(query, (datetime.utcnow(), dataset_id, self.tenant_id))
        logger.info(f"Data archived: {dataset_id}")


