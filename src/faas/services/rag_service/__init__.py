"""
RAG Service - FaaS implementation of RAG System.

Provides REST API for document ingestion, query processing, document management,
and vector search operations.
"""

from .models import (
    DocumentResponse,
    IngestDocumentRequest,
    QueryRequest,
    QueryResponse,
    SearchRequest,
    SearchResponse,
    UpdateDocumentRequest,
)
from .service import RAGService, create_rag_service

__all__ = [
    "RAGService",
    "create_rag_service",
    "IngestDocumentRequest",
    "QueryRequest",
    "SearchRequest",
    "UpdateDocumentRequest",
    "DocumentResponse",
    "QueryResponse",
    "SearchResponse",
]
