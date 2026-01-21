"""
Data Ingestion Service

Unified interface for uploading and processing data files with automatic
integration into RAG, Agents, Cache, and other AI components.
"""

from .ingestion_service import DataIngestionService
from .functions import (
    create_ingestion_service,
    upload_and_process,
    upload_and_process_async,
    batch_upload_and_process,
)

__all__ = [
    # Core classes
    "DataIngestionService",
    # Factory functions
    "create_ingestion_service",
    # High-level convenience functions
    "upload_and_process",
    "upload_and_process_async",
    "batch_upload_and_process",
]

