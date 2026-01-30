"""
RAG (Retrieval-Augmented Generation)

RAG system for context-aware LLM responses.
"""

from .document_processor import DocumentChunk, DocumentProcessor
from .functions import (
    batch_ingest_documents,
    batch_ingest_documents_async,
    batch_process_documents,
    create_document_processor,
    create_rag_system,
    delete_document_simple,
    ingest_document_simple,
    ingest_document_simple_async,
    quick_rag_query,
    quick_rag_query_async,
    update_document_simple,
)
from .generator import RAGGenerator
from .hallucination_detector import (
    HallucinationDetector,
    HallucinationResult,
    create_hallucination_detector,
)
from .multimodal_loader import MultiModalLoader, create_multimodal_loader
from .rag_system import RAGSystem
from .retriever import Retriever

__all__ = [
    # Core classes
    "RAGSystem",
    "DocumentProcessor",
    "DocumentChunk",
    "Retriever",
    "RAGGenerator",
    "MultiModalLoader",
    # Hallucination Detection
    "HallucinationDetector",
    "create_hallucination_detector",
    "HallucinationResult",
    # Factory functions
    "create_rag_system",
    "create_document_processor",
    "create_multimodal_loader",
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
