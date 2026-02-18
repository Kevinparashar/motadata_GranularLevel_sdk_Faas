"""
Unit Tests for RAG Exceptions

Tests exception classes in the RAG module.
"""


from src.core.rag.exceptions import (
    ChunkingError,
    DocumentProcessingError,
    EmbeddingError,
    GenerationError,
    RAGError,
    RetrievalError,
    ValidationError,
)


class TestRAGError:
    """Test RAGError base exception."""

    def test_rag_error_basic(self):
        """Test RAGError with basic message."""
        error = RAGError("Test error message")

        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_rag_error_with_original_error(self):
        """Test RAGError with original error."""
        original = ValueError("Original error")
        error = RAGError("Test error message", original_error=original)

        # SDKError includes original error in string representation
        assert "Test error message" in str(error)
        assert error.original_error == original
        assert error.message == "Test error message"


class TestRetrievalError:
    """Test RetrievalError exception."""

    def test_retrieval_error_basic(self):
        """Test RetrievalError with basic message."""
        error = RetrievalError("Retrieval failed")

        assert str(error) == "Retrieval failed"
        assert error.query is None
        assert error.document_id is None
        assert error.operation is None

    def test_retrieval_error_with_all_params(self):
        """Test RetrievalError with all parameters to cover lines 51-54."""
        original = ValueError("Original error")
        error = RetrievalError(
            message="Retrieval failed",
            query="test query",
            document_id="doc-123",
            operation="search",
            original_error=original,
        )

        assert "Retrieval failed" in str(error)
        assert error.message == "Retrieval failed"
        assert error.query == "test query"
        assert error.document_id == "doc-123"
        assert error.operation == "search"
        assert error.original_error == original

    def test_retrieval_error_with_query(self):
        """Test RetrievalError with query parameter."""
        error = RetrievalError("Retrieval failed", query="test query")

        assert error.query == "test query"

    def test_retrieval_error_with_document_id(self):
        """Test RetrievalError with document_id parameter."""
        error = RetrievalError("Retrieval failed", document_id="doc-123")

        assert error.document_id == "doc-123"

    def test_retrieval_error_with_operation(self):
        """Test RetrievalError with operation parameter."""
        error = RetrievalError("Retrieval failed", operation="search")

        assert error.operation == "search"


class TestGenerationError:
    """Test GenerationError exception."""

    def test_generation_error_basic(self):
        """Test GenerationError with basic message."""
        error = GenerationError("Generation failed")

        assert str(error) == "Generation failed"
        assert error.query is None
        assert error.context is None
        assert error.operation is None

    def test_generation_error_with_all_params(self):
        """Test GenerationError with all parameters to cover lines 85-88."""
        original = ValueError("Original error")
        error = GenerationError(
            message="Generation failed",
            query="test query",
            context="test context",
            operation="generate",
            original_error=original,
        )

        assert "Generation failed" in str(error)
        assert error.message == "Generation failed"
        assert error.query == "test query"
        assert error.context == "test context"
        assert error.operation == "generate"
        assert error.original_error == original

    def test_generation_error_with_query(self):
        """Test GenerationError with query parameter."""
        error = GenerationError("Generation failed", query="test query")

        assert error.query == "test query"

    def test_generation_error_with_context(self):
        """Test GenerationError with context parameter."""
        error = GenerationError("Generation failed", context="test context")

        assert error.context == "test context"

    def test_generation_error_with_operation(self):
        """Test GenerationError with operation parameter."""
        error = GenerationError("Generation failed", operation="generate")

        assert error.operation == "generate"


class TestEmbeddingError:
    """Test EmbeddingError exception."""

    def test_embedding_error_basic(self):
        """Test EmbeddingError with basic message."""
        error = EmbeddingError("Embedding failed")

        assert str(error) == "Embedding failed"
        assert error.text is None
        assert error.model is None

    def test_embedding_error_with_all_params(self):
        """Test EmbeddingError with all parameters."""
        original = ValueError("Original error")
        error = EmbeddingError(
            message="Embedding failed",
            text="test text",
            model="text-embedding-3-small",
            original_error=original,
        )

        assert "Embedding failed" in str(error)
        assert error.message == "Embedding failed"
        assert error.text == "test text"
        assert error.model == "text-embedding-3-small"
        assert error.original_error == original

    def test_embedding_error_with_text(self):
        """Test EmbeddingError with text parameter."""
        error = EmbeddingError("Embedding failed", text="test text")

        assert error.text == "test text"

    def test_embedding_error_with_model(self):
        """Test EmbeddingError with model parameter."""
        error = EmbeddingError("Embedding failed", model="text-embedding-3-small")

        assert error.model == "text-embedding-3-small"


class TestDocumentProcessingError:
    """Test DocumentProcessingError exception."""

    def test_document_processing_error_basic(self):
        """Test DocumentProcessingError with basic message."""
        error = DocumentProcessingError("Processing failed")

        assert str(error) == "Processing failed"
        assert error.document_id is None
        assert error.file_path is None
        assert error.operation is None

    def test_document_processing_error_with_all_params(self):
        """Test DocumentProcessingError with all parameters."""
        original = ValueError("Original error")
        error = DocumentProcessingError(
            message="Processing failed",
            document_id="doc-123",
            file_path="/path/to/file.pdf",
            operation="load",
            original_error=original,
        )

        assert "Processing failed" in str(error)
        assert error.message == "Processing failed"
        assert error.document_id == "doc-123"
        assert error.file_path == "/path/to/file.pdf"
        assert error.operation == "load"
        assert error.original_error == original

    def test_document_processing_error_with_document_id(self):
        """Test DocumentProcessingError with document_id parameter."""
        error = DocumentProcessingError("Processing failed", document_id="doc-123")

        assert error.document_id == "doc-123"

    def test_document_processing_error_with_file_path(self):
        """Test DocumentProcessingError with file_path parameter."""
        error = DocumentProcessingError("Processing failed", file_path="/path/to/file.pdf")

        assert error.file_path == "/path/to/file.pdf"

    def test_document_processing_error_with_operation(self):
        """Test DocumentProcessingError with operation parameter."""
        error = DocumentProcessingError("Processing failed", operation="load")

        assert error.operation == "load"


class TestChunkingError:
    """Test ChunkingError exception."""

    def test_chunking_error_basic(self):
        """Test ChunkingError with basic message."""
        error = ChunkingError("Chunking failed")

        assert str(error) == "Chunking failed"
        assert error.document_id is None
        assert error.chunking_strategy is None

    def test_chunking_error_with_all_params(self):
        """Test ChunkingError with all parameters."""
        original = ValueError("Original error")
        error = ChunkingError(
            message="Chunking failed",
            document_id="doc-123",
            chunking_strategy="semantic",
            original_error=original,
        )

        assert "Chunking failed" in str(error)
        assert error.message == "Chunking failed"
        assert error.document_id == "doc-123"
        assert error.chunking_strategy == "semantic"
        assert error.original_error == original

    def test_chunking_error_with_document_id(self):
        """Test ChunkingError with document_id parameter."""
        error = ChunkingError("Chunking failed", document_id="doc-123")

        assert error.document_id == "doc-123"

    def test_chunking_error_with_chunking_strategy(self):
        """Test ChunkingError with chunking_strategy parameter."""
        error = ChunkingError("Chunking failed", chunking_strategy="semantic")

        assert error.chunking_strategy == "semantic"


class TestValidationError:
    """Test ValidationError exception."""

    def test_validation_error_basic(self):
        """Test ValidationError with basic message."""
        error = ValidationError("Validation failed")

        assert str(error) == "Validation failed"
        assert error.field is None
        assert error.value is None

    def test_validation_error_with_all_params(self):
        """Test ValidationError with all parameters."""
        original = ValueError("Original error")
        error = ValidationError(
            message="Validation failed",
            field="content",
            value="",
            original_error=original,
        )

        assert "Validation failed" in str(error)
        assert error.message == "Validation failed"
        assert error.field == "content"
        assert error.value == ""
        assert error.original_error == original

    def test_validation_error_with_field(self):
        """Test ValidationError with field parameter."""
        error = ValidationError("Validation failed", field="content")

        assert error.field == "content"

    def test_validation_error_with_value(self):
        """Test ValidationError with value parameter."""
        error = ValidationError("Validation failed", value="")

        assert error.value == ""

    def test_validation_error_with_complex_value(self):
        """Test ValidationError with complex value."""
        complex_value = {"key": "value", "list": [1, 2, 3]}
        error = ValidationError("Validation failed", value=complex_value)

        assert error.value == complex_value

