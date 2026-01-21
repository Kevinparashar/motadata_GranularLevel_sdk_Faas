"""
Request/Response models for Data Ingestion Service.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class UploadFileRequest(BaseModel):
    """Request to upload a file."""

    file_path: Optional[str] = Field(None, description="Path to file (for server-side upload)")
    title: Optional[str] = Field(None, description="File title")
    metadata: Optional[Dict[str, Any]] = Field(None, description="File metadata")
    auto_ingest: bool = Field(default=True, description="Auto-ingest into RAG system")


class ProcessFileRequest(BaseModel):
    """Request to process a file."""

    file_id: str = Field(..., description="File ID")
    process_type: Optional[str] = Field(None, description="Processing type")


class FileResponse(BaseModel):
    """File response model."""

    file_id: str
    file_name: str
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    status: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None


class ProcessingResponse(BaseModel):
    """Processing response model."""

    file_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None

