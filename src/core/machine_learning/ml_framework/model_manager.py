"""
Model Manager

Manages model lifecycle: create, update, delete, archive, and load models.
"""

from typing import Dict, Any, Optional, List
import logging
import os
from pathlib import Path
from datetime import datetime

from .exceptions import ModelNotFoundError, ModelLoadError, ModelSaveError
from ...postgresql_database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class ModelManager:
    """
    Manages model lifecycle and storage.
    
    Handles model registration, storage, loading, and metadata management
    with support for multiple storage backends and tenant isolation.
    """
    
    def __init__(
        self,
        db: DatabaseConnection,
        storage_path: str = "./models",
        tenant_id: Optional[str] = None
    ):
        """
        Initialize model manager.
        
        Args:
            db: Database connection for metadata
            storage_path: Base path for model storage
            tenant_id: Optional tenant ID for multi-tenant support
        """
        self.db = db
        self.tenant_id = tenant_id
        self.storage_path = Path(storage_path)
        if tenant_id:
            self.storage_path = self.storage_path / tenant_id
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._ensure_tables()
        logger.info(f"ModelManager initialized for tenant: {tenant_id}")
    
    def register_model(
        self,
        model_id: str,
        model_type: str,
        model_path: str,
        metadata: Optional[Dict[str, Any]] = None,
        version: str = "1.0.0"
    ) -> str:
        """
        Register a new model.
        
        Args:
            model_id: Unique model identifier
            model_type: Type of model (classification, regression, etc.)
            model_path: Path to model file
            metadata: Optional model metadata
            version: Model version
            
        Returns:
            Registered model ID
        """
        query = """
        INSERT INTO ml_models (model_id, model_type, model_path, metadata, version, tenant_id, created_at)
        VALUES (%s, %s, %s, %s::jsonb, %s, %s, %s)
        ON CONFLICT (model_id, version, tenant_id) DO UPDATE
        SET model_path = EXCLUDED.model_path,
            metadata = EXCLUDED.metadata,
            updated_at = %s
        RETURNING id;
        """
        
        import json
        metadata_json = json.dumps(metadata or {})
        now = datetime.utcnow()
        
        result = self.db.execute_query(
            query,
            (model_id, model_type, model_path, metadata_json, version, self.tenant_id, now, now),
            fetch_one=True
        )
        
        logger.info(f"Model registered: {model_id} v{version}")
        return str(result['id'])
    
    def get_model(
        self,
        model_id: str,
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get model information.
        
        Args:
            model_id: Model ID
            version: Optional version (uses latest if not specified)
            
        Returns:
            Model information dictionary
            
        Raises:
            ModelNotFoundError: If model not found
        """
        if version:
            query = """
            SELECT * FROM ml_models
            WHERE model_id = %s AND version = %s AND tenant_id = %s
            ORDER BY created_at DESC
            LIMIT 1;
            """
            params = (model_id, version, self.tenant_id)
        else:
            query = """
            SELECT * FROM ml_models
            WHERE model_id = %s AND tenant_id = %s
            ORDER BY created_at DESC
            LIMIT 1;
            """
            params = (model_id, self.tenant_id)
        
        result = self.db.execute_query(query, params, fetch_one=True)
        
        if not result:
            raise ModelNotFoundError(
                f"Model not found: {model_id}",
                model_id=model_id,
                version=version
            )
        
        return dict(result)
    
    def list_models(
        self,
        model_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List all models.
        
        Args:
            model_type: Optional filter by model type
            limit: Maximum number of results
            
        Returns:
            List of model information dictionaries
        """
        if model_type:
            query = """
            SELECT * FROM ml_models
            WHERE model_type = %s AND tenant_id = %s
            ORDER BY created_at DESC
            LIMIT %s;
            """
            params = (model_type, self.tenant_id, limit)
        else:
            query = """
            SELECT * FROM ml_models
            WHERE tenant_id = %s
            ORDER BY created_at DESC
            LIMIT %s;
            """
            params = (self.tenant_id, limit)
        
        results = self.db.execute_query(query, params)
        return [dict(row) for row in results]
    
    def update_model(
        self,
        model_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        version: Optional[str] = None
    ) -> None:
        """
        Update model metadata.
        
        Args:
            model_id: Model ID
            metadata: Updated metadata
            version: Optional version
        """
        import json
        metadata_json = json.dumps(metadata or {})
        now = datetime.utcnow()
        
        if version:
            query = """
            UPDATE ml_models
            SET metadata = %s::jsonb, updated_at = %s
            WHERE model_id = %s AND version = %s AND tenant_id = %s;
            """
            params = (metadata_json, now, model_id, version, self.tenant_id)
        else:
            query = """
            UPDATE ml_models
            SET metadata = %s::jsonb, updated_at = %s
            WHERE model_id = %s AND tenant_id = %s
            AND created_at = (SELECT MAX(created_at) FROM ml_models WHERE model_id = %s AND tenant_id = %s);
            """
            params = (metadata_json, now, model_id, self.tenant_id, model_id, self.tenant_id)
        
        self.db.execute_query(query, params)
        logger.info(f"Model updated: {model_id}")
    
    def delete_model(
        self,
        model_id: str,
        version: Optional[str] = None
    ) -> None:
        """
        Delete a model.
        
        Args:
            model_id: Model ID
            version: Optional version (deletes all versions if not specified)
        """
        if version:
            query = """
            DELETE FROM ml_models
            WHERE model_id = %s AND version = %s AND tenant_id = %s;
            """
            params = (model_id, version, self.tenant_id)
        else:
            query = """
            DELETE FROM ml_models
            WHERE model_id = %s AND tenant_id = %s;
            """
            params = (model_id, self.tenant_id)
        
        self.db.execute_query(query, params)
        logger.info(f"Model deleted: {model_id}")
    
    def archive_model(
        self,
        model_id: str,
        version: Optional[str] = None
    ) -> None:
        """
        Archive a model (soft delete).
        
        Args:
            model_id: Model ID
            version: Optional version
        """
        query = """
        UPDATE ml_models
        SET archived = true, updated_at = %s
        WHERE model_id = %s AND tenant_id = %s
        """
        params = [datetime.utcnow(), model_id, self.tenant_id]
        
        if version:
            query += " AND version = %s;"
            params.append(version)
        else:
            query += ";"
        
        self.db.execute_query(query, tuple(params))
        logger.info(f"Model archived: {model_id}")
    
    def load_model(
        self,
        model_id: str,
        version: Optional[str] = None
    ) -> Any:
        """
        Load model from storage.
        
        Args:
            model_id: Model ID
            version: Optional version
            
        Returns:
            Loaded model object
            
        Raises:
            ModelLoadError: If loading fails
        """
        try:
            model_info = self.get_model(model_id, version)
            model_path = model_info['model_path']
            
            # Load model using joblib (standard for scikit-learn)
            import joblib
            
            if not os.path.exists(model_path):
                raise ModelLoadError(
                    f"Model file not found: {model_path}",
                    model_id=model_id,
                    model_path=model_path,
                    version=version
                )
            
            model = joblib.load(model_path)
            logger.info(f"Model loaded: {model_id}")
            return model
            
        except ModelNotFoundError:
            raise
        except Exception as e:
            raise ModelLoadError(
                f"Failed to load model {model_id}: {str(e)}",
                model_id=model_id,
                version=version,
                original_error=e
            )
    
    def save_model(
        self,
        model: Any,
        model_id: str,
        version: str = "1.0.0"
    ) -> str:
        """
        Save model to storage.
        
        Args:
            model: Model object to save
            model_id: Model ID
            version: Model version
            
        Returns:
            Path to saved model file
            
        Raises:
            ModelSaveError: If saving fails
        """
        try:
            import joblib
            
            model_dir = self.storage_path / model_id
            model_dir.mkdir(parents=True, exist_ok=True)
            
            model_path = model_dir / f"model_v{version}.joblib"
            joblib.dump(model, model_path)
            
            logger.info(f"Model saved: {model_path}")
            return str(model_path)
            
        except Exception as e:
            raise ModelSaveError(
                f"Failed to save model {model_id}: {str(e)}",
                model_id=model_id,
                original_error=e
            )
    
    def _ensure_tables(self) -> None:
        """Ensure required database tables exist."""
        query = """
        CREATE TABLE IF NOT EXISTS ml_models (
            id SERIAL PRIMARY KEY,
            model_id VARCHAR(255) NOT NULL,
            model_type VARCHAR(100) NOT NULL,
            model_path TEXT NOT NULL,
            metadata JSONB,
            version VARCHAR(50) NOT NULL,
            tenant_id VARCHAR(255),
            archived BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(model_id, version, tenant_id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_ml_models_tenant ON ml_models(tenant_id);
        CREATE INDEX IF NOT EXISTS idx_ml_models_type ON ml_models(model_type);
        CREATE INDEX IF NOT EXISTS idx_ml_models_created ON ml_models(created_at DESC);
        """
        
        self.db.execute_query(query)


