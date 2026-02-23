"""
Model Manager

Manages model lifecycle: create, update, delete, archive, and load models.
"""


from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from ...faas.shared.dal.model_dal import ModelDAL  # type: ignore[import-untyped]

from ...postgresql_database.connection import DatabaseConnection
from .exceptions import ModelLoadError, ModelNotFoundError, ModelSaveError

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
        tenant_id: Optional[str] = None,
        model_dal: Optional[Any] = None,
    ):
        """
        Initialize model manager.
        
        Args:
            db: Database connection/handle.
            storage_path: Storage path for model files.
            tenant_id: Tenant identifier used for tenant isolation.
            model_dal: Optional ModelDAL instance for database persistence.
        """
        self.db = db
        self.tenant_id = tenant_id
        # Initialize ModelDAL if not provided
        if model_dal is None:
            from ...faas.shared.dal.model_dal import ModelDAL  # type: ignore[import-untyped]
            self.model_dal = ModelDAL(db)
        else:
            self.model_dal = model_dal
        self.storage_path = Path(storage_path)
        if tenant_id:
            self.storage_path = self.storage_path / tenant_id
        self.storage_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"ModelManager initialized for tenant: {tenant_id}")

    async def initialize(self) -> None:
        """
        Initialize ModelManager asynchronously.
        
        This method is kept for backward compatibility but no longer creates tables.
        Tables are assumed to exist (managed by migrations/DAL).
        
        Example:
            >>> model_manager = ModelManager(db, storage_path="./models")
            >>> await model_manager.initialize()
        
        Returns:
            None: Result of the operation.
        """
        # Tables are assumed to exist (managed by migrations/DAL)
        pass

    async def register_model(
        self,
        model_id: str,
        model_type: str,
        model_path: str,
        metadata: Optional[Dict[str, Any]] = None,
        version: str = "1.0.0",
    ) -> str:
        """
        Register a new model asynchronously.
        
        Args:
            model_id (str): Input parameter for this operation.
            model_type (str): Input parameter for this operation.
            model_path (str): Input parameter for this operation.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
            version (str): Input parameter for this operation.
        
        Returns:
            str: Returned text value.
        """
        # Use DAL to register model
        model_record_id = await self.model_dal.register_model(
            model_id=model_id,
            model_type=model_type,
            model_path=model_path,
            version=version,
            tenant_id=self.tenant_id,
            metadata=metadata,
        )

        logger.info(f"Model registered: {model_id} v{version}")
        return model_record_id

    async def get_model(self, model_id: str, version: Optional[str] = None) -> Dict[str, Any]:
        """
        Get model information asynchronously.
        
        Args:
            model_id (str): Input parameter for this operation.
            version (Optional[str]): Input parameter for this operation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        
        Raises:
            ModelNotFoundError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        # Use DAL to get model
        result = await self.model_dal.get_model(model_id, version, self.tenant_id)

        if not result:
            raise ModelNotFoundError(
                f"Model not found: {model_id}", model_id=model_id, version=version
            )

        return result

    async def list_models(
        self, model_type: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List all models asynchronously.
        
        Args:
            model_type (Optional[str]): Input parameter for this operation.
            limit (int): Input parameter for this operation.
        
        Returns:
            List[Dict[str, Any]]: Dictionary result of the operation.
        """
        # Use DAL to list models
        results = await self.model_dal.list_models(
            tenant_id=self.tenant_id, model_type=model_type, limit=limit, offset=0
        )
        return [dict(row) for row in results]

    async def update_model(
        self,
        model_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        version: Optional[str] = None,
    ) -> None:
        """
        Update model metadata asynchronously.
        
        Args:
            model_id (str): Input parameter for this operation.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
            version (Optional[str]): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        """
        import json

        metadata_json = json.dumps(metadata or {})
        now = datetime.now(timezone.utc)

        if version:
            query = """
            UPDATE ml_models
            SET metadata = $1::jsonb, updated_at = $2
            WHERE model_id = $3 AND version = $4 AND tenant_id = $5;
            """
            params = (metadata_json, now, model_id, version, self.tenant_id)
        else:
            query = """
            UPDATE ml_models
            SET metadata = $1::jsonb, updated_at = $2
            WHERE model_id = $3 AND tenant_id = $4
            AND created_at = (SELECT MAX(created_at) FROM ml_models WHERE model_id = $5 AND tenant_id = $6);
            """
            params = (metadata_json, now, model_id, self.tenant_id, model_id, self.tenant_id)

        await self.db.execute_query(query, params)
        logger.info(f"Model updated: {model_id}")

    async def delete_model(self, model_id: str, version: Optional[str] = None) -> None:
        """
        Delete a model asynchronously.
        
        Args:
            model_id (str): Input parameter for this operation.
            version (Optional[str]): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        """
        # Use DAL to delete model
        await self.model_dal.delete_model(model_id, version, self.tenant_id)
        logger.info(f"Model deleted: {model_id}")

    async def archive_model(self, model_id: str, version: Optional[str] = None) -> None:
        """
        Archive a model (soft delete) asynchronously.
        
        Args:
            model_id (str): Input parameter for this operation.
            version (Optional[str]): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        """
        # Use DAL to archive model
        await self.model_dal.archive_model(model_id, version, self.tenant_id)
        logger.info(f"Model archived: {model_id}")

    async def load_model(self, model_id: str, version: Optional[str] = None) -> Any:
        """
        Load model from storage asynchronously.
        
        Args:
            model_id (str): Input parameter for this operation.
            version (Optional[str]): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            ModelLoadError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        import asyncio
        
        try:
            model_info = await self.get_model(model_id, version)
            model_path = model_info["model_path"]

            # Load model using joblib (standard for scikit-learn)
            import joblib

            def _load_sync() -> Any:
                if not os.path.exists(model_path):
                    raise ModelLoadError(
                        f"Model file not found: {model_path}",
                        model_id=model_id,
                        model_path=model_path,
                        version=version,
                    )
                return joblib.load(model_path)

            # Run file I/O in thread pool to avoid blocking
            model = await asyncio.to_thread(_load_sync)
            logger.info(f"Model loaded: {model_id}")
            return model

        except ModelNotFoundError:
            raise
        except Exception as e:
            raise ModelLoadError(
                f"Failed to load model {model_id}: {str(e)}",
                model_id=model_id,
                version=version,
                original_error=e,
            )

    async def save_model(self, model: Any, model_id: str, version: str = "1.0.0") -> str:
        """
        Save model to storage asynchronously.
        
        Args:
            model (Any): Model name or identifier to use.
            model_id (str): Input parameter for this operation.
            version (str): Input parameter for this operation.
        
        Returns:
            str: Returned text value.
        
        Raises:
            ModelSaveError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        import asyncio
        
        try:
            import joblib

            model_dir = self.storage_path / model_id
            model_dir.mkdir(parents=True, exist_ok=True)

            model_path = model_dir / f"model_v{version}.joblib"
            
            def _save_sync() -> None:
                joblib.dump(model, model_path)
            
            # Run file I/O in thread pool to avoid blocking
            await asyncio.to_thread(_save_sync)

            logger.info(f"Model saved: {model_path}")
            return str(model_path)

        except Exception as e:
            raise ModelSaveError(
                f"Failed to save model {model_id}: {str(e)}", model_id=model_id, original_error=e
            )
