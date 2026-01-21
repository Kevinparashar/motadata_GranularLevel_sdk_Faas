"""
Data Ingestion Service - FaaS implementation of Data Ingestion.

Provides REST API for file upload and multi-modal data processing.
"""

from .service import DataIngestionService, create_data_ingestion_service
from .models import (
    UploadFileRequest,
    ProcessFileRequest,
    FileResponse,
    ProcessingResponse,
)

__all__ = [
    "DataIngestionService",
    "create_data_ingestion_service",
    "UploadFileRequest",
    "ProcessFileRequest",
    "FileResponse",
    "ProcessingResponse",
]

