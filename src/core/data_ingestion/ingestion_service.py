"""
Data Ingestion Service

Unified service for uploading, processing, and integrating data files
with all AI components (RAG, Agents, Cache, etc.).
"""


# Standard library imports
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..cache_mechanism import CacheMechanism, create_cache
from ..litellm_gateway import LiteLLMGateway
from ..postgresql_database.connection import DatabaseConnection

# Local application/library specific imports
from ..rag import RAGSystem, create_rag_system
from .data_cleaner import DataCleaner
from .data_validator import DataValidator
from .exceptions import DataIngestionError, ValidationError


class DataIngestionService:
    """
    Unified service for data ingestion and processing.

    Handles:
    - File upload and validation
    - Data processing and cleansing
    - Automatic integration with RAG, Agents, Cache
    - Multi-format support (text, PDF, audio, video, images, structured data)
    """

    def __init__(
        self,
        rag_system: Optional[RAGSystem] = None,
        cache: Optional[CacheMechanism] = None,
        gateway: Optional[LiteLLMGateway] = None,
        db: Optional[DatabaseConnection] = None,
        enable_validation: bool = True,
        enable_cleansing: bool = True,
        enable_auto_ingest: bool = True,
        enable_caching: bool = True,
        tenant_id: Optional[str] = None,
    ):
        """
        Initialize data ingestion service.
        
        Args:
            rag_system (Optional[RAGSystem]): Input parameter for this operation.
            cache (Optional[CacheMechanism]): Cache instance used to store and fetch cached results.
            gateway (Optional[LiteLLMGateway]): Gateway client used for LLM calls.
            db (Optional[DatabaseConnection]): Database connection/handle.
            enable_validation (bool): Flag to enable or disable validation.
            enable_cleansing (bool): Flag to enable or disable cleansing.
            enable_auto_ingest (bool): Flag to enable or disable auto ingest.
            enable_caching (bool): Flag to enable or disable caching.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        """
        self.rag_system = rag_system
        self.cache = cache
        self.gateway = gateway
        self.db = db
        self.enable_validation = enable_validation
        self.enable_cleansing = enable_cleansing
        self.enable_auto_ingest = enable_auto_ingest
        self.enable_caching = enable_caching
        self.tenant_id = tenant_id

        # Initialize RAG if not provided but gateway and db are
        if not self.rag_system and self.gateway and self.db:
            self.rag_system = create_rag_system(
                db=self.db, gateway=self.gateway, enable_multimodal=True
            )

        # Get gateway from RAG if not directly provided
        if not self.gateway and self.rag_system:
            self.gateway = self.rag_system.gateway

        # Initialize cache if not provided
        if not self.cache:
            self.cache = create_cache()

        # Initialize validators and cleaners
        self.validator = DataValidator() if enable_validation else None
        self.cleaner = DataCleaner() if enable_cleansing else None

        # Create multimodal loader
        from ..rag.multimodal_loader import create_multimodal_loader

        self.multimodal_loader = create_multimodal_loader(
            enable_audio_transcription=True,
            enable_video_transcription=True,
            enable_image_ocr=True,
            enable_image_description=True,
        )

    async def upload_and_process(
        self,
        file_path: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_ingest: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Upload and process a data file asynchronously.
        
        This is a one-stop method that:
                                                1. Validates the file
                                                2. Loads and processes content
                                                3. Cleanses the data
                                                4. Caches the result
                                                5. Ingests into RAG (if enabled)
        
                                                Example:
                                                    >>> service = create_ingestion_service(rag=rag, cache=cache)
                                                    >>> result = await service.upload_and_process("document.pdf")
                                                    >>> print(result["document_id"])  # RAG document ID
                                                    >>> print(result["content_preview"])  # Processed content preview
        
        Args:
            file_path (str): Path of the input file.
            title (Optional[str]): Input parameter for this operation.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
            auto_ingest (Optional[bool]): Input parameter for this operation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        
        Raises:
            DataIngestionError: Raised when this function detects an invalid state or when an underlying call fails.
            ValidationError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        path = Path(file_path)

        if not path.exists():
            raise DataIngestionError(
                message=f"File not found: {file_path}", file_path=str(file_path)
            )

        # Generate title if not provided
        if not title:
            title = path.stem

        # Validate file
        if self.validator:
            validation_result = await self.validator.validate_file(path)
            if not validation_result["valid"]:
                raise ValidationError(message=validation_result["error"], file_path=str(file_path))

        # Load and process content
        try:
            content, loaded_metadata = await self.multimodal_loader.load(str(path), gateway=self.gateway)
        except Exception as e:
            raise DataIngestionError(
                message=f"Error loading file: {str(e)}", file_path=str(file_path), original_error=e
            )

        # Merge metadata
        if metadata:
            loaded_metadata.update(metadata)
        metadata = loaded_metadata

        # Cleanse data if enabled
        if self.cleaner:
            content = await self.cleaner.clean(content, metadata)

        # Cache processed content
        cache_key = f"ingested:{path.name}:{path.stat().st_mtime}"
        if self.enable_caching:
            await self.cache.set(
                cache_key,
                {"content": content, "metadata": metadata},
                tenant_id=self.tenant_id,
                ttl=86400,  # 24 hours
            )

        # Auto-ingest into RAG if enabled
        document_id = None
        if (
            auto_ingest if auto_ingest is not None else self.enable_auto_ingest
        ) and self.rag_system:
            try:
                document_id = self.rag_system.ingest_document(
                    title=title,
                    content=content,
                    file_path=str(path),
                    tenant_id=self.tenant_id,
                    source=str(path),
                    metadata=metadata,
                )
            except Exception as e:
                raise DataIngestionError(
                    message=f"Error ingesting into RAG: {str(e)}",
                    file_path=str(file_path),
                    original_error=e,
                )

        return {
            "success": True,
            "file_path": str(path),
            "title": title,
            "document_id": document_id,
            "content_length": len(content),
            "content_preview": content[:500] + "..." if len(content) > 500 else content,
            "metadata": metadata,
            "cached": self.enable_caching,
            "ingested": document_id is not None,
        }

    async def upload_and_process_async(
        self,
        file_path: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_ingest: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Asynchronously upload and process a data file (alias for upload_and_process).
        
        Args:
            file_path (str): Path of the input file.
            title (Optional[str]): Input parameter for this operation.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
            auto_ingest (Optional[bool]): Input parameter for this operation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        # Delegate to the main async method
        return await self.upload_and_process(file_path, title, metadata, auto_ingest)

    async def batch_upload_and_process(
        self,
        file_paths: List[str],
        titles: Optional[List[str]] = None,
        metadata_list: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Batch upload and process multiple files asynchronously.
        
        Args:
            file_paths (List[str]): Input parameter for this operation.
            titles (Optional[List[str]]): Input parameter for this operation.
            metadata_list (Optional[List[Dict[str, Any]]]): Input parameter for this operation.
        
        Returns:
            List[Dict[str, Any]]: Dictionary result of the operation.
        """
        tasks = []
        for i, file_path in enumerate(file_paths):
            title = titles[i] if titles and i < len(titles) else None
            metadata = metadata_list[i] if metadata_list and i < len(metadata_list) else None

            tasks.append(
                self.upload_and_process(file_path=file_path, title=title, metadata=metadata)
            )

        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error dictionaries
        processed_results: List[Dict[str, Any]] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "file_path": file_paths[i],
                    "error": str(result)
                })
            elif isinstance(result, dict):
                processed_results.append(result)
            else:
                # Handle unexpected types
                processed_results.append({
                    "success": False,
                    "file_path": file_paths[i],
                    "error": f"Unexpected result type: {type(result)}"
                })
        
        return processed_results

    async def batch_upload_and_process_async(
        self,
        file_paths: List[str],
        titles: Optional[List[str]] = None,
        metadata_list: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Asynchronously batch upload and process multiple files (alias for batch_upload_and_process).
        
        Args:
            file_paths (List[str]): Input parameter for this operation.
            titles (Optional[List[str]]): Input parameter for this operation.
            metadata_list (Optional[List[Dict[str, Any]]]): Input parameter for this operation.
        
        Returns:
            List[Dict[str, Any]]: Dictionary result of the operation.
        """
        # Delegate to the main async method
        return await self.batch_upload_and_process(file_paths, titles, metadata_list)
