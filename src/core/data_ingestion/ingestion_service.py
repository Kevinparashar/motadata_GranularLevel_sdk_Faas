"""
Data Ingestion Service

Unified service for uploading, processing, and integrating data files
with all AI components (RAG, Agents, Cache, etc.).
"""

# Standard library imports
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

# Local application/library specific imports
from ..rag import RAGSystem, create_rag_system
from ..rag.multimodal_loader import create_multimodal_loader
from ..cache_mechanism import CacheMechanism, create_cache_mechanism
from ..litellm_gateway import LiteLLMGateway
from ..postgresql_database.connection import DatabaseConnection
from .data_validator import DataValidator
from .data_cleaner import DataCleaner
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
        tenant_id: Optional[str] = None
    ):
        """
        Initialize data ingestion service.
        
        Args:
            rag_system: Optional RAG system for document ingestion
            cache: Optional cache mechanism for processed data
            gateway: Optional gateway (required if RAG not provided)
            db: Optional database (required if RAG not provided)
            enable_validation: Enable data validation
            enable_cleansing: Enable data cleansing
            enable_auto_ingest: Automatically ingest into RAG
            enable_caching: Cache processed data
            tenant_id: Optional tenant ID for multi-tenancy
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
                db=self.db,
                gateway=self.gateway,
                enable_multimodal=True
            )
        
        # Get gateway from RAG if not directly provided
        if not self.gateway and self.rag_system:
            self.gateway = self.rag_system.gateway
        
        # Initialize cache if not provided
        if not self.cache:
            self.cache = create_cache_mechanism()
        
        # Initialize validators and cleaners
        self.validator = DataValidator() if enable_validation else None
        self.cleaner = DataCleaner() if enable_cleansing else None
        
        # Create multimodal loader
        from ..rag.multimodal_loader import create_multimodal_loader
        self.multimodal_loader = create_multimodal_loader(
            enable_audio_transcription=True,
            enable_video_transcription=True,
            enable_image_ocr=True,
            enable_image_description=True
        )
    
    def upload_and_process(
        self,
        file_path: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_ingest: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Upload and process a data file.
        
        This is a one-stop method that:
        1. Validates the file
        2. Loads and processes content
        3. Cleanses the data
        4. Caches the result
        5. Ingests into RAG (if enabled)
        
        Args:
            file_path: Path to file
            title: Optional document title (defaults to filename)
            metadata: Optional metadata
            auto_ingest: Override auto-ingest setting
        
        Returns:
            Dictionary with processing results
        
        Example:
            >>> service = create_ingestion_service(rag=rag, cache=cache)
            >>> result = service.upload_and_process("document.pdf")
            >>> print(result["document_id"])  # RAG document ID
            >>> print(result["content_preview"])  # Processed content preview
        """
        path = Path(file_path)
        
        if not path.exists():
            raise DataIngestionError(
                message=f"File not found: {file_path}",
                file_path=str(file_path)
            )
        
        # Generate title if not provided
        if not title:
            title = path.stem
        
        # Validate file
        if self.validator:
            validation_result = self.validator.validate_file(path)
            if not validation_result["valid"]:
                raise ValidationError(
                    message=validation_result["error"],
                    file_path=str(file_path)
                )
        
        # Load and process content
        try:
            content, loaded_metadata = self.multimodal_loader.load(str(path), gateway=self.gateway)
        except Exception as e:
            raise DataIngestionError(
                message=f"Error loading file: {str(e)}",
                file_path=str(file_path),
                original_error=e
            )
        
        # Merge metadata
        if metadata:
            loaded_metadata.update(metadata)
        metadata = loaded_metadata
        
        # Cleanse data if enabled
        if self.cleaner:
            content = self.cleaner.clean(content, metadata)
        
        # Cache processed content
        cache_key = f"ingested:{path.name}:{path.stat().st_mtime}"
        if self.enable_caching:
            self.cache.set(
                cache_key,
                {"content": content, "metadata": metadata},
                tenant_id=self.tenant_id,
                ttl=86400  # 24 hours
            )
        
        # Auto-ingest into RAG if enabled
        document_id = None
        if (auto_ingest if auto_ingest is not None else self.enable_auto_ingest) and self.rag_system:
            try:
                document_id = self.rag_system.ingest_document(
                    title=title,
                    content=content,
                    file_path=str(path),
                    tenant_id=self.tenant_id,
                    source=str(path),
                    metadata=metadata
                )
            except Exception as e:
                raise DataIngestionError(
                    message=f"Error ingesting into RAG: {str(e)}",
                    file_path=str(file_path),
                    original_error=e
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
            "ingested": document_id is not None
        }
    
    async def upload_and_process_async(
        self,
        file_path: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_ingest: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Asynchronously upload and process a data file.
        
        Args:
            file_path: Path to file
            title: Optional document title
            metadata: Optional metadata
            auto_ingest: Override auto-ingest setting
        
        Returns:
            Dictionary with processing results
        """
        # Run synchronous processing in executor
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.upload_and_process,
            file_path,
            title,
            metadata,
            auto_ingest
        )
    
    def batch_upload_and_process(
        self,
        file_paths: List[str],
        titles: Optional[List[str]] = None,
        metadata_list: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Batch upload and process multiple files.
        
        Args:
            file_paths: List of file paths
            titles: Optional list of titles
            metadata_list: Optional list of metadata dicts
        
        Returns:
            List of processing results
        """
        results = []
        for i, file_path in enumerate(file_paths):
            try:
                title = titles[i] if titles and i < len(titles) else None
                metadata = metadata_list[i] if metadata_list and i < len(metadata_list) else None
                
                result = self.upload_and_process(
                    file_path=file_path,
                    title=title,
                    metadata=metadata
                )
                results.append(result)
            except Exception as e:
                results.append({
                    "success": False,
                    "file_path": file_path,
                    "error": str(e)
                })
        
        return results
    
    async def batch_upload_and_process_async(
        self,
        file_paths: List[str],
        titles: Optional[List[str]] = None,
        metadata_list: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Asynchronously batch upload and process multiple files.
        
        Args:
            file_paths: List of file paths
            titles: Optional list of titles
            metadata_list: Optional list of metadata dicts
        
        Returns:
            List of processing results
        """
        tasks = []
        for i, file_path in enumerate(file_paths):
            title = titles[i] if titles and i < len(titles) else None
            metadata = metadata_list[i] if metadata_list and i < len(metadata_list) else None
            
            tasks.append(
                self.upload_and_process_async(
                    file_path=file_path,
                    title=title,
                    metadata=metadata
                )
            )
        
        return await asyncio.gather(*tasks, return_exceptions=True)

