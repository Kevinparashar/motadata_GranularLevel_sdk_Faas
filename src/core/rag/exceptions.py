"""
RAG System Exception Hierarchy

Exceptions specific to the RAG (Retrieval-Augmented Generation) system.
"""

from typing import Any, Optional

from ..exceptions import SDKError


class RAGError(SDKError):
    """Base exception for RAG-related errors."""

    pass


class RetrievalError(RAGError):
    """
    Raised when document retrieval or vector search fails.

    Attributes:
        query: Query that failed
        document_id: ID of the document (if applicable)
        operation: Operation that failed (retrieve, search, etc.)
    """

    def __init__(
        self,
        message: str,
        query: Optional[str] = None,
        document_id: Optional[str] = None,
        operation: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message, original_error)
        self.query = query
        self.document_id = document_id
        self.operation = operation


class GenerationError(RAGError):
    """
    Raised when LLM-based generation fails (RAG answer synthesis).

    Attributes:
        query: Query that was being processed
        context: Context used for generation (if applicable)
        operation: Operation that failed
    """

    def __init__(
        self,
        message: str,
        query: Optional[str] = None,
        context: Optional[str] = None,
        operation: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message, original_error)
        self.query = query
        self.context = context
        self.operation = operation


class EmbeddingError(RAGError):
    """
    Raised when embedding generation fails.

    Attributes:
        text: Text that failed to embed
        model: Embedding model used (if applicable)
    """

    def __init__(
        self,
        message: str,
        text: Optional[str] = None,
        model: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message, original_error)
        self.text = text
        self.model = model


class DocumentProcessingError(RAGError):
    """
    Raised when document processing fails (loading, parsing, chunking).

    Attributes:
        document_id: ID of the document
        file_path: Path to the document file
        operation: Operation that failed (load, parse, chunk, etc.)
    """

    def __init__(
        self,
        message: str,
        document_id: Optional[str] = None,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message, original_error)
        self.document_id = document_id
        self.file_path = file_path
        self.operation = operation


class ChunkingError(RAGError):
    """
    Raised when document chunking fails.

    Attributes:
        document_id: ID of the document
        chunking_strategy: Chunking strategy used
    """

    def __init__(
        self,
        message: str,
        document_id: Optional[str] = None,
        chunking_strategy: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message, original_error)
        self.document_id = document_id
        self.chunking_strategy = chunking_strategy


class ValidationError(RAGError):
    """
    Raised when validation fails (e.g., empty content, invalid format).

    Attributes:
        field: Field that failed validation
        value: Value that failed validation
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message, original_error)
        self.field = field
        self.value = value
