"""
RAG (Retrieval-Augmented Generation)

RAG system for context-aware LLM responses.
"""

from .rag_system import RAGSystem
from .document_processor import DocumentProcessor, DocumentChunk
from .retriever import Retriever
from .generator import RAGGenerator
from .functions import (
    create_rag_system,
    create_document_processor,
    quick_rag_query,
    quick_rag_query_async,
    ingest_document_simple,
    ingest_document_simple_async,
    batch_ingest_documents,
    batch_ingest_documents_async,
    update_document_simple,
    delete_document_simple,
    batch_process_documents,
)

__all__ = [
    # Core classes
    "RAGSystem",
    "DocumentProcessor",
    "DocumentChunk",
    "Retriever",
    "RAGGenerator",
    # Factory functions
    "create_rag_system",
    "create_document_processor",
    # High-level convenience functions
    "quick_rag_query",
    "quick_rag_query_async",
    "ingest_document_simple",
    "ingest_document_simple_async",
    "batch_ingest_documents",
    "batch_ingest_documents_async",
    "update_document_simple",
    "delete_document_simple",
    # Utility functions
    "batch_process_documents",
]
