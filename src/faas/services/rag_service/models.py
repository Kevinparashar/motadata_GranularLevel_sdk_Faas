"""
Request/Response models for RAG Service.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class IngestDocumentRequest(BaseModel):
    """Request to ingest a document."""

    document_id: Optional[str] = Field(None, description="Document ID (generated if not provided)")
    title: str = Field(..., description="Document title")
    content: Optional[str] = Field(None, description="Document content")
    file_path: Optional[str] = Field(None, description="Path to document file")
    source: Optional[str] = Field(None, description="Document source")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Document metadata")
    chunk_size: Optional[int] = Field(1000, description="Chunk size for document processing")
    chunk_overlap: Optional[int] = Field(200, description="Chunk overlap")


class QueryRequest(BaseModel):
    """Request for RAG query."""

    query: str = Field(..., description="Query text")
    top_k: int = Field(default=5, ge=1, le=100, description="Number of documents to retrieve")
    threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Similarity threshold")
    metadata_filters: Optional[Dict[str, Any]] = Field(None, description="Metadata filters")
    enable_rewrite: bool = Field(default=True, description="Enable query rewriting")
    enable_hallucination_detection: bool = Field(
        default=False, description="Enable hallucination detection"
    )


class SearchRequest(BaseModel):
    """Request for vector search."""

    query_embedding: Optional[List[float]] = Field(None, description="Query embedding vector")
    query_text: Optional[str] = Field(
        None, description="Query text (will be embedded if query_embedding not provided)"
    )
    top_k: int = Field(default=5, ge=1, le=100, description="Number of results")
    threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Similarity threshold")
    metadata_filters: Optional[Dict[str, Any]] = Field(None, description="Metadata filters")


class UpdateDocumentRequest(BaseModel):
    """Request to update a document."""

    title: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    reprocess: bool = Field(default=False, description="Reprocess document (re-chunk and re-embed)")


class DocumentResponse(BaseModel):
    """Document response model."""

    document_id: str
    title: str
    source: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    chunk_count: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class QueryResponse(BaseModel):
    """Query response model."""

    answer: str
    documents: List[Dict[str, Any]] = Field(default_factory=list, description="Source documents")
    sources: List[str] = Field(default_factory=list, description="Document sources")
    confidence: Optional[float] = Field(None, description="Confidence score")
    hallucination_detected: Optional[bool] = Field(
        None, description="Whether hallucination was detected"
    )
    metadata: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    """Search response model."""

    documents: List[Dict[str, Any]] = Field(default_factory=list, description="Retrieved documents")
    scores: List[float] = Field(default_factory=list, description="Similarity scores")
    count: int = Field(0, description="Number of documents retrieved")
