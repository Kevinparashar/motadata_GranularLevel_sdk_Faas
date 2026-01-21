"""
Data Ingestion - High-Level Functions
"""

from typing import Any, Dict, List, Optional

from .ingestion_service import DataIngestionService
from ..rag import RAGSystem
from ..cache_mechanism import CacheMechanism
from ..litellm_gateway import LiteLLMGateway
from ..postgresql_database.connection import DatabaseConnection


def create_ingestion_service(
    rag_system: Optional[RAGSystem] = None,
    cache: Optional[CacheMechanism] = None,
    gateway: Optional[LiteLLMGateway] = None,
    db: Optional[DatabaseConnection] = None,
    enable_validation: bool = True,
    enable_cleansing: bool = True,
    enable_auto_ingest: bool = True,
    enable_caching: bool = True,
    tenant_id: Optional[str] = None,
    **kwargs: Any
) -> DataIngestionService:
    """
    Create a data ingestion service.
    
    Args:
        rag_system: Optional RAG system
        cache: Optional cache mechanism
        gateway: Optional gateway (required if RAG not provided)
        db: Optional database (required if RAG not provided)
        enable_validation: Enable validation
        enable_cleansing: Enable cleansing
        enable_auto_ingest: Auto-ingest into RAG
        enable_caching: Enable caching
        tenant_id: Optional tenant ID
        **kwargs: Additional configuration
    
    Returns:
        DataIngestionService instance
    
    Example:
        >>> service = create_ingestion_service(rag=rag, cache=cache)
        >>> result = service.upload_and_process("document.pdf")
    """
    return DataIngestionService(
        rag_system=rag_system,
        cache=cache,
        gateway=gateway,
        db=db,
        enable_validation=enable_validation,
        enable_cleansing=enable_cleansing,
        enable_auto_ingest=enable_auto_ingest,
        enable_caching=enable_caching,
        tenant_id=tenant_id,
        **kwargs
    )


def upload_and_process(
    file_path: str,
    rag_system: Optional[RAGSystem] = None,
    cache: Optional[CacheMechanism] = None,
    gateway: Optional[LiteLLMGateway] = None,
    db: Optional[DatabaseConnection] = None,
    title: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    tenant_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to upload and process a file.
    
    Args:
        file_path: Path to file
        rag_system: Optional RAG system
        cache: Optional cache
        gateway: Optional gateway
        db: Optional database
        title: Optional title
        metadata: Optional metadata
        tenant_id: Optional tenant ID
    
    Returns:
        Processing result
    """
    service = create_ingestion_service(
        rag_system=rag_system,
        cache=cache,
        gateway=gateway,
        db=db,
        tenant_id=tenant_id
    )
    return service.upload_and_process(
        file_path=file_path,
        title=title,
        metadata=metadata
    )


async def upload_and_process_async(
    file_path: str,
    rag_system: Optional[RAGSystem] = None,
    cache: Optional[CacheMechanism] = None,
    gateway: Optional[LiteLLMGateway] = None,
    db: Optional[DatabaseConnection] = None,
    title: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    tenant_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Asynchronously upload and process a file.
    
    Args:
        file_path: Path to file
        rag_system: Optional RAG system
        cache: Optional cache
        gateway: Optional gateway
        db: Optional database
        title: Optional title
        metadata: Optional metadata
        tenant_id: Optional tenant ID
    
    Returns:
        Processing result
    """
    service = create_ingestion_service(
        rag_system=rag_system,
        cache=cache,
        gateway=gateway,
        db=db,
        tenant_id=tenant_id
    )
    return await service.upload_and_process_async(
        file_path=file_path,
        title=title,
        metadata=metadata
    )


def batch_upload_and_process(
    file_paths: List[str],
    rag_system: Optional[RAGSystem] = None,
    cache: Optional[CacheMechanism] = None,
    gateway: Optional[LiteLLMGateway] = None,
    db: Optional[DatabaseConnection] = None,
    titles: Optional[List[str]] = None,
    metadata_list: Optional[List[Dict[str, Any]]] = None,
    tenant_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Batch upload and process multiple files.
    
    Args:
        file_paths: List of file paths
        rag_system: Optional RAG system
        cache: Optional cache
        gateway: Optional gateway
        db: Optional database
        titles: Optional titles
        metadata_list: Optional metadata list
        tenant_id: Optional tenant ID
    
    Returns:
        List of processing results
    """
    service = create_ingestion_service(
        rag_system=rag_system,
        cache=cache,
        gateway=gateway,
        db=db,
        tenant_id=tenant_id
    )
    return service.batch_upload_and_process(
        file_paths=file_paths,
        titles=titles,
        metadata_list=metadata_list
    )

