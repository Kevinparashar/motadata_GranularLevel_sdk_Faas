"""
RAG Service - FaaS implementation of RAG System.

Provides REST API for document ingestion, query processing, document management,
and vector search operations.
"""

from .service import RAGService, create_rag_service
from .models import (
    IngestDocumentRequest,
    QueryRequest,
    SearchRequest,
    UpdateDocumentRequest,
    DocumentResponse,
    QueryResponse,
    SearchResponse,
)

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

