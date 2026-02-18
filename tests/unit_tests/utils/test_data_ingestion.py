"""
Unit tests for Data Ingestion components.
"""


import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.data_ingestion.data_cleaner import DataCleaner
from src.core.data_ingestion.data_validator import DataValidator
from src.core.data_ingestion.exceptions import DataIngestionError, ValidationError
from src.core.data_ingestion.functions import (
    batch_upload_and_process,
    batch_upload_and_process_async,
    create_ingestion_service,
    upload_and_process,
    upload_and_process_async,
)
from src.core.data_ingestion.ingestion_service import DataIngestionService


@pytest.fixture
def data_validator():
    """Create DataValidator instance."""
    return DataValidator()


@pytest.fixture
def data_cleaner():
    """Create DataCleaner instance."""
    return DataCleaner()


@pytest.fixture
def ingestion_service():
    """Create DataIngestionService instance."""
    with patch("src.core.rag.create_rag_system"), \
         patch("src.core.cache_mechanism.create_cache"), \
         patch("src.core.rag.multimodal_loader.create_multimodal_loader"):
        service = DataIngestionService(
            rag_system=None,
            cache=None,
            gateway=None,
            db=None,
            enable_validation=True,
            enable_cleansing=True,
            tenant_id="tenant_123",
        )
        return service


@pytest.mark.asyncio
async def test_data_validator_validate_file_valid(data_validator):
    """Test validate_file with valid file."""
    # Create temporary file asynchronously
    def _create_temp_file():
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test content")
            return Path(f.name)
    
    file_path = await asyncio.to_thread(_create_temp_file)
    
    try:
        result = await data_validator.validate_file(file_path)
        
        assert result["valid"] is True
        assert "file_size" in result
        assert result["format"] == ".txt"
    finally:
        await asyncio.to_thread(file_path.unlink)


@pytest.mark.asyncio
async def test_data_validator_validate_file_not_found(data_validator):
    """Test validate_file with non-existent file."""
    file_path = Path("/nonexistent/file.txt")
    
    result = await data_validator.validate_file(file_path)
    
    assert result["valid"] is False
    assert "error" in result
    assert "not found" in result["error"].lower()


@pytest.mark.asyncio
async def test_data_validator_validate_file_too_large(data_validator):
    """Test validate_file with file too large."""
    # Create temporary file larger than limit
    # Use a smaller size for testing (1KB + 1 byte)
    test_size = 1024 + 1
    
    def _create_temp_file():
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("x" * test_size)
            return Path(f.name)
    
    file_path = await asyncio.to_thread(_create_temp_file)
    
    try:
        # Create validator with smaller limit for testing
        validator = DataValidator(max_file_size=1024)  # 1KB limit
        result = await validator.validate_file(file_path)
        
        assert result["valid"] is False
        assert "too large" in result["error"].lower()
    finally:
        await asyncio.to_thread(file_path.unlink)


@pytest.mark.asyncio
async def test_data_validator_validate_file_unsupported_format(data_validator):
    """Test validate_file with unsupported format."""
    # Create temporary file with unsupported extension
    def _create_temp_file():
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xyz", delete=False) as f:
            f.write("Test content")
            return Path(f.name)
    
    file_path = await asyncio.to_thread(_create_temp_file)
    
    try:
        result = await data_validator.validate_file(file_path)
        
        assert result["valid"] is False
        assert "unsupported" in result["error"].lower()
    finally:
        await asyncio.to_thread(file_path.unlink)


@pytest.mark.asyncio
async def test_data_validator_validate_content_valid(data_validator):
    """Test validate_content with valid content."""
    result = await data_validator.validate_content("Test content", ".txt")
    
    assert result["valid"] is True


@pytest.mark.asyncio
async def test_data_validator_validate_content_json_valid(data_validator):
    """Test validate_content with valid JSON."""
    json_content = '{"key": "value"}'
    result = await data_validator.validate_content(json_content, ".json")
    
    assert result["valid"] is True


@pytest.mark.asyncio
async def test_data_validator_validate_content_json_invalid(data_validator):
    """Test validate_content with invalid JSON."""
    invalid_json = '{"key": "value"'
    result = await data_validator.validate_content(invalid_json, ".json")
    
    assert result["valid"] is False
    assert "json" in result["error"].lower()


@pytest.mark.asyncio
async def test_data_cleaner_clean_basic(data_cleaner):
    """Test clean with basic content."""
    content = "  Hello   World  \n\n\n"
    result = await data_cleaner.clean(content)
    
    assert "Hello World" in result
    assert result.strip() == result


@pytest.mark.asyncio
async def test_data_cleaner_clean_remove_control_chars(data_cleaner):
    """Test clean removes control characters."""
    content = "Hello\x00World\x1fTest"
    result = await data_cleaner.clean(content)
    
    assert "\x00" not in result
    assert "\x1f" not in result


@pytest.mark.asyncio
async def test_data_cleaner_clean_normalize_line_endings(data_cleaner):
    """Test clean normalizes line endings."""
    content = "Line1\r\nLine2\rLine3\n"
    result = await data_cleaner.clean(content)
    
    assert "\r" not in result


@pytest.mark.asyncio
async def test_data_cleaner_clean_empty(data_cleaner):
    """Test clean with empty content."""
    result = await data_cleaner.clean("")
    
    assert result == ""


@pytest.mark.asyncio
async def test_data_cleaner_clean_multiple_whitespace(data_cleaner):
    """Test clean removes multiple whitespace."""
    content = "Hello    World     Test"
    result = await data_cleaner.clean(content)
    
    assert "  " not in result  # No double spaces


@pytest.mark.asyncio
async def test_data_cleaner_clean_multiple_newlines(data_cleaner):
    """Test clean normalizes multiple newlines."""
    content = "Line1\n\n\n\nLine2"
    result = await data_cleaner.clean(content)
    
    # Should have at most double newlines
    assert "\n\n\n" not in result


@pytest.mark.asyncio
async def test_ingestion_service_initialization(ingestion_service):
    """Test DataIngestionService initialization."""
    assert ingestion_service is not None
    assert ingestion_service.tenant_id == "tenant_123"
    assert ingestion_service.enable_validation is True
    assert ingestion_service.enable_cleansing is True


@pytest.mark.asyncio
async def test_ingestion_service_upload_and_process_file_not_found(ingestion_service):
    """Test upload_and_process with non-existent file."""
    with pytest.raises(DataIngestionError):
        await ingestion_service.upload_and_process(
            file_path="/nonexistent/file.txt",
            title="Test",
        )


@pytest.mark.asyncio
async def test_ingestion_service_upload_and_process_valid(ingestion_service):
    """Test upload_and_process with valid file."""
    # Create temporary file asynchronously
    def _create_temp_file():
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test content")
            return f.name
    
    file_path = await asyncio.to_thread(_create_temp_file)
    
    try:
        with patch.object(ingestion_service.validator, "validate_file", new_callable=AsyncMock) as mock_validate, \
             patch.object(ingestion_service.multimodal_loader, "load", new_callable=AsyncMock) as mock_load, \
             patch.object(ingestion_service.cleaner, "clean", new_callable=AsyncMock) as mock_clean, \
             patch.object(ingestion_service.cache, "set", new_callable=AsyncMock) as mock_cache_set:
            
            mock_validate.return_value = {"valid": True, "file_size": 100, "format": ".txt"}
            mock_load.return_value = ("Test content", {})  # Returns tuple (content, metadata)
            mock_clean.return_value = "Test content"
            mock_cache_set.return_value = None
            
            result = await ingestion_service.upload_and_process(
                file_path=file_path,
                title="Test Document",
            )
            
            assert "content_preview" in result or "document_id" in result
            mock_validate.assert_called_once()
            mock_load.assert_called_once()
            mock_clean.assert_called_once()
    finally:
        await asyncio.to_thread(Path(file_path).unlink)


@pytest.mark.asyncio
async def test_data_validator_custom_limits():
    """Test DataValidator with custom limits."""
    validator = DataValidator(max_file_size=1000, allowed_formats=[".txt"])
    
    assert validator.file_size_limit == 1000
    assert validator.allowed_formats == [".txt"]


@pytest.mark.asyncio
async def test_data_cleaner_custom_options():
    """Test DataCleaner with custom options."""
    cleaner = DataCleaner(
        remove_extra_whitespace=False,
        normalize_unicode=False,
        remove_control_chars=False,
        normalize_line_endings=False,
    )
    
    content = "  Hello   World  \n\n\n"
    result = await cleaner.clean(content)
    
    # Should not modify content with all options disabled
    assert result == content


@pytest.mark.asyncio
async def test_ingestion_service_init_with_gateway_and_db():
    """Test DataIngestionService initialization with gateway and db (creates RAG)."""
    mock_gateway = MagicMock()
    mock_db = MagicMock()
    
    with patch("src.core.data_ingestion.ingestion_service.create_rag_system") as mock_create_rag, \
         patch("src.core.cache_mechanism.create_cache") as mock_create_cache, \
         patch("src.core.rag.multimodal_loader.create_multimodal_loader") as mock_create_loader:
        
        mock_rag = MagicMock()
        mock_create_rag.return_value = mock_rag
        mock_cache = MagicMock()
        mock_create_cache.return_value = mock_cache
        mock_loader = MagicMock()
        mock_create_loader.return_value = mock_loader
        
        service = DataIngestionService(
            gateway=mock_gateway,
            db=mock_db,
            enable_validation=True,
            enable_cleansing=True,
        )
        
        assert service.rag_system == mock_rag
        assert service.gateway == mock_gateway
        mock_create_rag.assert_called_once()


@pytest.mark.asyncio
async def test_ingestion_service_init_gateway_from_rag():
    """Test DataIngestionService gets gateway from RAG system."""
    mock_rag = MagicMock()
    mock_gateway = MagicMock()
    mock_rag.gateway = mock_gateway
    
    with patch("src.core.cache_mechanism.create_cache") as mock_create_cache, \
         patch("src.core.rag.multimodal_loader.create_multimodal_loader") as mock_create_loader:
        
        mock_cache = MagicMock()
        mock_create_cache.return_value = mock_cache
        mock_loader = MagicMock()
        mock_create_loader.return_value = mock_loader
        
        service = DataIngestionService(
            rag_system=mock_rag,
            gateway=None,
        )
        
        assert service.gateway == mock_gateway


@pytest.mark.asyncio
async def test_ingestion_service_upload_and_process_generate_title(ingestion_service):
    """Test upload_and_process generates title from filename."""
    def _create_temp_file():
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test content")
            return f.name
    
    file_path = await asyncio.to_thread(_create_temp_file)
    
    try:
        with patch.object(ingestion_service.validator, "validate_file", new_callable=AsyncMock) as mock_validate, \
             patch.object(ingestion_service.multimodal_loader, "load", new_callable=AsyncMock) as mock_load, \
             patch.object(ingestion_service.cleaner, "clean", new_callable=AsyncMock) as mock_clean, \
             patch.object(ingestion_service.cache, "set", new_callable=AsyncMock) as mock_cache_set:
            
            mock_validate.return_value = {"valid": True, "file_size": 100, "format": ".txt"}
            mock_load.return_value = ("Test content", {})
            mock_clean.return_value = "Test content"
            mock_cache_set.return_value = None
            
            result = await ingestion_service.upload_and_process(
                file_path=file_path,
                title=None,  # Should be generated from filename
            )
            
            assert result["title"] == Path(file_path).stem
    finally:
        await asyncio.to_thread(Path(file_path).unlink)


@pytest.mark.asyncio
async def test_ingestion_service_upload_and_process_validation_error(ingestion_service):
    """Test upload_and_process with validation error."""
    def _create_temp_file():
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test content")
            return f.name
    
    file_path = await asyncio.to_thread(_create_temp_file)
    
    try:
        with patch.object(ingestion_service.validator, "validate_file", new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = {"valid": False, "error": "File too large"}
            
            with pytest.raises(ValidationError, match="File too large"):
                await ingestion_service.upload_and_process(
                    file_path=file_path,
                    title="Test",
                )
    finally:
        await asyncio.to_thread(Path(file_path).unlink)


@pytest.mark.asyncio
async def test_ingestion_service_upload_and_process_load_error(ingestion_service):
    """Test upload_and_process with file loading error."""
    def _create_temp_file():
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test content")
            return f.name
    
    file_path = await asyncio.to_thread(_create_temp_file)
    
    try:
        with patch.object(ingestion_service.validator, "validate_file", new_callable=AsyncMock) as mock_validate, \
             patch.object(ingestion_service.multimodal_loader, "load", new_callable=AsyncMock) as mock_load:
            
            mock_validate.return_value = {"valid": True, "file_size": 100, "format": ".txt"}
            mock_load.side_effect = ValueError("Load error")
            
            with pytest.raises(DataIngestionError, match="Error loading file"):
                await ingestion_service.upload_and_process(
                    file_path=file_path,
                    title="Test",
                )
    finally:
        await asyncio.to_thread(Path(file_path).unlink)


@pytest.mark.asyncio
async def test_ingestion_service_upload_and_process_merge_metadata(ingestion_service):
    """Test upload_and_process merges metadata."""
    def _create_temp_file():
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test content")
            return f.name
    
    file_path = await asyncio.to_thread(_create_temp_file)
    
    try:
        with patch.object(ingestion_service.validator, "validate_file", new_callable=AsyncMock) as mock_validate, \
             patch.object(ingestion_service.multimodal_loader, "load", new_callable=AsyncMock) as mock_load, \
             patch.object(ingestion_service.cleaner, "clean", new_callable=AsyncMock) as mock_clean, \
             patch.object(ingestion_service.cache, "set", new_callable=AsyncMock) as mock_cache_set:
            
            mock_validate.return_value = {"valid": True, "file_size": 100, "format": ".txt"}
            mock_load.return_value = ("Test content", {"type": "text", "size": 100})
            mock_clean.return_value = "Test content"
            mock_cache_set.return_value = None
            
            result = await ingestion_service.upload_and_process(
                file_path=file_path,
                title="Test",
                metadata={"custom": "value"},
            )
            
            assert result["metadata"]["type"] == "text"
            assert result["metadata"]["custom"] == "value"
    finally:
        await asyncio.to_thread(Path(file_path).unlink)


@pytest.mark.asyncio
async def test_ingestion_service_upload_and_process_with_rag_ingestion(ingestion_service):
    """Test upload_and_process with RAG ingestion enabled."""
    mock_rag = MagicMock()
    mock_rag.ingest_document = MagicMock(return_value="doc-123")
    ingestion_service.rag_system = mock_rag
    
    def _create_temp_file():
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test content")
            return f.name
    
    file_path = await asyncio.to_thread(_create_temp_file)
    
    try:
        with patch.object(ingestion_service.validator, "validate_file", new_callable=AsyncMock) as mock_validate, \
             patch.object(ingestion_service.multimodal_loader, "load", new_callable=AsyncMock) as mock_load, \
             patch.object(ingestion_service.cleaner, "clean", new_callable=AsyncMock) as mock_clean, \
             patch.object(ingestion_service.cache, "set", new_callable=AsyncMock) as mock_cache_set:
            
            mock_validate.return_value = {"valid": True, "file_size": 100, "format": ".txt"}
            mock_load.return_value = ("Test content", {})
            mock_clean.return_value = "Test content"
            mock_cache_set.return_value = None
            
            result = await ingestion_service.upload_and_process(
                file_path=file_path,
                title="Test",
                auto_ingest=True,
            )
            
            assert result["document_id"] == "doc-123"
            assert result["ingested"] is True
            mock_rag.ingest_document.assert_called_once()
    finally:
        await asyncio.to_thread(Path(file_path).unlink)


@pytest.mark.asyncio
async def test_ingestion_service_upload_and_process_rag_ingestion_error(ingestion_service):
    """Test upload_and_process with RAG ingestion error."""
    mock_rag = MagicMock()
    mock_rag.ingest_document = MagicMock(side_effect=ValueError("RAG error"))
    ingestion_service.rag_system = mock_rag
    
    def _create_temp_file():
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test content")
            return f.name
    
    file_path = await asyncio.to_thread(_create_temp_file)
    
    try:
        with patch.object(ingestion_service.validator, "validate_file", new_callable=AsyncMock) as mock_validate, \
             patch.object(ingestion_service.multimodal_loader, "load", new_callable=AsyncMock) as mock_load, \
             patch.object(ingestion_service.cleaner, "clean", new_callable=AsyncMock) as mock_clean, \
             patch.object(ingestion_service.cache, "set", new_callable=AsyncMock) as mock_cache_set:
            
            mock_validate.return_value = {"valid": True, "file_size": 100, "format": ".txt"}
            mock_load.return_value = ("Test content", {})
            mock_clean.return_value = "Test content"
            mock_cache_set.return_value = None
            
            with pytest.raises(DataIngestionError, match="Error ingesting into RAG"):
                await ingestion_service.upload_and_process(
                    file_path=file_path,
                    title="Test",
                    auto_ingest=True,
                )
    finally:
        await asyncio.to_thread(Path(file_path).unlink)


@pytest.mark.asyncio
async def test_ingestion_service_upload_and_process_no_caching(ingestion_service):
    """Test upload_and_process with caching disabled."""
    ingestion_service.enable_caching = False
    
    def _create_temp_file():
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test content")
            return f.name
    
    file_path = await asyncio.to_thread(_create_temp_file)
    
    try:
        with patch.object(ingestion_service.validator, "validate_file", new_callable=AsyncMock) as mock_validate, \
             patch.object(ingestion_service.multimodal_loader, "load", new_callable=AsyncMock) as mock_load, \
             patch.object(ingestion_service.cleaner, "clean", new_callable=AsyncMock) as mock_clean, \
             patch.object(ingestion_service.cache, "set", new_callable=AsyncMock) as mock_cache_set:
            
            mock_validate.return_value = {"valid": True, "file_size": 100, "format": ".txt"}
            mock_load.return_value = ("Test content", {})
            mock_clean.return_value = "Test content"
            
            result = await ingestion_service.upload_and_process(
                file_path=file_path,
                title="Test",
            )
            
            assert result["cached"] is False
            mock_cache_set.assert_not_called()
    finally:
        await asyncio.to_thread(Path(file_path).unlink)


@pytest.mark.asyncio
async def test_ingestion_service_upload_and_process_no_cleansing(ingestion_service):
    """Test upload_and_process with cleansing disabled."""
    ingestion_service.cleaner = None
    
    def _create_temp_file():
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test content")
            return f.name
    
    file_path = await asyncio.to_thread(_create_temp_file)
    
    try:
        with patch.object(ingestion_service.validator, "validate_file", new_callable=AsyncMock) as mock_validate, \
             patch.object(ingestion_service.multimodal_loader, "load", new_callable=AsyncMock) as mock_load, \
             patch.object(ingestion_service.cache, "set", new_callable=AsyncMock) as mock_cache_set:
            
            mock_validate.return_value = {"valid": True, "file_size": 100, "format": ".txt"}
            mock_load.return_value = ("Test content", {})
            mock_cache_set.return_value = None
            
            result = await ingestion_service.upload_and_process(
                file_path=file_path,
                title="Test",
            )
            
            assert "content_preview" in result
    finally:
        await asyncio.to_thread(Path(file_path).unlink)


@pytest.mark.asyncio
async def test_ingestion_service_upload_and_process_async(ingestion_service):
    """Test upload_and_process_async (alias method)."""
    def _create_temp_file():
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test content")
            return f.name
    
    file_path = await asyncio.to_thread(_create_temp_file)
    
    try:
        with patch.object(ingestion_service.validator, "validate_file", new_callable=AsyncMock) as mock_validate, \
             patch.object(ingestion_service.multimodal_loader, "load", new_callable=AsyncMock) as mock_load, \
             patch.object(ingestion_service.cleaner, "clean", new_callable=AsyncMock) as mock_clean, \
             patch.object(ingestion_service.cache, "set", new_callable=AsyncMock) as mock_cache_set:
            
            mock_validate.return_value = {"valid": True, "file_size": 100, "format": ".txt"}
            mock_load.return_value = ("Test content", {})
            mock_clean.return_value = "Test content"
            mock_cache_set.return_value = None
            
            result = await ingestion_service.upload_and_process_async(
                file_path=file_path,
                title="Test",
            )
            
            assert "success" in result
            assert result["success"] is True
    finally:
        await asyncio.to_thread(Path(file_path).unlink)


@pytest.mark.asyncio
async def test_ingestion_service_batch_upload_and_process(ingestion_service):
    """Test batch_upload_and_process."""
    def _create_temp_files():
        files = []
        for i in range(2):
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                f.write(f"Test content {i}")
                files.append(f.name)
        return files
    
    file_paths = await asyncio.to_thread(_create_temp_files)
    
    try:
        with patch.object(ingestion_service.validator, "validate_file", new_callable=AsyncMock) as mock_validate, \
             patch.object(ingestion_service.multimodal_loader, "load", new_callable=AsyncMock) as mock_load, \
             patch.object(ingestion_service.cleaner, "clean", new_callable=AsyncMock) as mock_clean, \
             patch.object(ingestion_service.cache, "set", new_callable=AsyncMock) as mock_cache_set:
            
            mock_validate.return_value = {"valid": True, "file_size": 100, "format": ".txt"}
            mock_load.return_value = ("Test content", {})
            mock_clean.return_value = "Test content"
            mock_cache_set.return_value = None
            
            results = await ingestion_service.batch_upload_and_process(
                file_paths=file_paths,
                titles=["File 1", "File 2"],
            )
            
            assert len(results) == 2
            assert all(r["success"] for r in results)
    finally:
        for file_path in file_paths:
            await asyncio.to_thread(Path(file_path).unlink)


@pytest.mark.asyncio
async def test_ingestion_service_batch_upload_with_errors(ingestion_service):
    """Test batch_upload_and_process with some files failing."""
    def _create_temp_file():
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test content")
            return f.name
    
    file_path = await asyncio.to_thread(_create_temp_file)
    
    try:
        # Mock upload_and_process to raise error for second file
        original_method = ingestion_service.upload_and_process
        
        async def mock_upload(*args, **kwargs):
            if "nonexistent" in str(kwargs.get("file_path", "")):
                raise DataIngestionError(message="File not found", file_path="/nonexistent/file.txt")
            return await original_method(*args, **kwargs)
        
        ingestion_service.upload_and_process = mock_upload
        
        with patch.object(ingestion_service.validator, "validate_file", new_callable=AsyncMock) as mock_validate, \
             patch.object(ingestion_service.multimodal_loader, "load", new_callable=AsyncMock) as mock_load, \
             patch.object(ingestion_service.cleaner, "clean", new_callable=AsyncMock) as mock_clean, \
             patch.object(ingestion_service.cache, "set", new_callable=AsyncMock) as mock_cache_set:
            
            mock_validate.return_value = {"valid": True, "file_size": 100, "format": ".txt"}
            mock_load.return_value = ("Test content", {})
            mock_clean.return_value = "Test content"
            mock_cache_set.return_value = None
            
            results = await ingestion_service.batch_upload_and_process(
                file_paths=[file_path, "/nonexistent/file.txt"],
            )
            
            assert len(results) == 2
            assert results[0]["success"] is True
            assert results[1]["success"] is False
            assert "error" in results[1]
    finally:
        await asyncio.to_thread(Path(file_path).unlink)


@pytest.mark.asyncio
async def test_ingestion_service_batch_upload_unexpected_type(ingestion_service):
    """Test batch_upload_and_process handles unexpected result types."""
    def _create_temp_file():
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test content")
            return f.name
    
    file_path = await asyncio.to_thread(_create_temp_file)
    
    try:
        # Mock upload_and_process to return unexpected type
        original_method = ingestion_service.upload_and_process
        
        async def mock_upload(*args, **kwargs):
            if "unexpected" in str(kwargs.get("file_path", "")):
                return "unexpected_string"  # Not a dict
            return await original_method(*args, **kwargs)
        
        ingestion_service.upload_and_process = mock_upload
        
        with patch.object(ingestion_service.validator, "validate_file", new_callable=AsyncMock) as mock_validate, \
             patch.object(ingestion_service.multimodal_loader, "load", new_callable=AsyncMock) as mock_load, \
             patch.object(ingestion_service.cleaner, "clean", new_callable=AsyncMock) as mock_clean, \
             patch.object(ingestion_service.cache, "set", new_callable=AsyncMock) as mock_cache_set:
            
            mock_validate.return_value = {"valid": True, "file_size": 100, "format": ".txt"}
            mock_load.return_value = ("Test content", {})
            mock_clean.return_value = "Test content"
            mock_cache_set.return_value = None
            
            # Create a file path that will trigger unexpected type
            unexpected_path = file_path.replace(".txt", "_unexpected.txt")
            
            results = await ingestion_service.batch_upload_and_process(
                file_paths=[file_path, unexpected_path],
            )
            
            assert len(results) == 2
            assert results[0]["success"] is True
            assert results[1]["success"] is False
            assert "Unexpected result type" in results[1]["error"]
    finally:
        await asyncio.to_thread(Path(file_path).unlink)


@pytest.mark.asyncio
async def test_ingestion_service_batch_upload_and_process_async(ingestion_service):
    """Test batch_upload_and_process_async (alias method)."""
    def _create_temp_file():
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test content")
            return f.name
    
    file_path = await asyncio.to_thread(_create_temp_file)
    
    try:
        with patch.object(ingestion_service.validator, "validate_file", new_callable=AsyncMock) as mock_validate, \
             patch.object(ingestion_service.multimodal_loader, "load", new_callable=AsyncMock) as mock_load, \
             patch.object(ingestion_service.cleaner, "clean", new_callable=AsyncMock) as mock_clean, \
             patch.object(ingestion_service.cache, "set", new_callable=AsyncMock) as mock_cache_set:
            
            mock_validate.return_value = {"valid": True, "file_size": 100, "format": ".txt"}
            mock_load.return_value = ("Test content", {})
            mock_clean.return_value = "Test content"
            mock_cache_set.return_value = None
            
            results = await ingestion_service.batch_upload_and_process_async(
                file_paths=[file_path],
            )
            
            assert len(results) == 1
            assert results[0]["success"] is True
    finally:
        await asyncio.to_thread(Path(file_path).unlink)


@pytest.mark.asyncio
async def test_ingestion_service_upload_and_process_auto_ingest_override(ingestion_service):
    """Test upload_and_process with auto_ingest parameter override."""
    mock_rag = MagicMock()
    mock_rag.ingest_document = MagicMock(return_value="doc-123")
    ingestion_service.rag_system = mock_rag
    ingestion_service.enable_auto_ingest = False  # Disabled by default
    
    def _create_temp_file():
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test content")
            return f.name
    
    file_path = await asyncio.to_thread(_create_temp_file)
    
    try:
        with patch.object(ingestion_service.validator, "validate_file", new_callable=AsyncMock) as mock_validate, \
             patch.object(ingestion_service.multimodal_loader, "load", new_callable=AsyncMock) as mock_load, \
             patch.object(ingestion_service.cleaner, "clean", new_callable=AsyncMock) as mock_clean, \
             patch.object(ingestion_service.cache, "set", new_callable=AsyncMock) as mock_cache_set:
            
            mock_validate.return_value = {"valid": True, "file_size": 100, "format": ".txt"}
            mock_load.return_value = ("Test content", {})
            mock_clean.return_value = "Test content"
            mock_cache_set.return_value = None
            
            # Override with auto_ingest=True
            result = await ingestion_service.upload_and_process(
                file_path=file_path,
                title="Test",
                auto_ingest=True,  # Override default
            )
            
            assert result["document_id"] == "doc-123"
            mock_rag.ingest_document.assert_called_once()
    finally:
        await asyncio.to_thread(Path(file_path).unlink)


@pytest.mark.asyncio
async def test_ingestion_service_upload_and_process_auto_ingest_false(ingestion_service):
    """Test upload_and_process with auto_ingest=False."""
    mock_rag = MagicMock()
    ingestion_service.rag_system = mock_rag
    ingestion_service.enable_auto_ingest = True  # Enabled by default
    
    def _create_temp_file():
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test content")
            return f.name
    
    file_path = await asyncio.to_thread(_create_temp_file)
    
    try:
        with patch.object(ingestion_service.validator, "validate_file", new_callable=AsyncMock) as mock_validate, \
             patch.object(ingestion_service.multimodal_loader, "load", new_callable=AsyncMock) as mock_load, \
             patch.object(ingestion_service.cleaner, "clean", new_callable=AsyncMock) as mock_clean, \
             patch.object(ingestion_service.cache, "set", new_callable=AsyncMock) as mock_cache_set:
            
            mock_validate.return_value = {"valid": True, "file_size": 100, "format": ".txt"}
            mock_load.return_value = ("Test content", {})
            mock_clean.return_value = "Test content"
            mock_cache_set.return_value = None
            
            # Override with auto_ingest=False
            result = await ingestion_service.upload_and_process(
                file_path=file_path,
                title="Test",
                auto_ingest=False,  # Override default
            )
            
            assert result["document_id"] is None
            assert result["ingested"] is False
            mock_rag.ingest_document.assert_not_called()
    finally:
        await asyncio.to_thread(Path(file_path).unlink)


@pytest.mark.asyncio
async def test_ingestion_service_batch_upload_with_metadata_list(ingestion_service):
    """Test batch_upload_and_process with metadata_list."""
    def _create_temp_file():
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test content")
            return f.name
    
    file_path = await asyncio.to_thread(_create_temp_file)
    
    try:
        with patch.object(ingestion_service.validator, "validate_file", new_callable=AsyncMock) as mock_validate, \
             patch.object(ingestion_service.multimodal_loader, "load", new_callable=AsyncMock) as mock_load, \
             patch.object(ingestion_service.cleaner, "clean", new_callable=AsyncMock) as mock_clean, \
             patch.object(ingestion_service.cache, "set", new_callable=AsyncMock) as mock_cache_set:
            
            mock_validate.return_value = {"valid": True, "file_size": 100, "format": ".txt"}
            mock_load.return_value = ("Test content", {"type": "text"})
            mock_clean.return_value = "Test content"
            mock_cache_set.return_value = None
            
            results = await ingestion_service.batch_upload_and_process(
                file_paths=[file_path],
                metadata_list=[{"custom": "value"}],
            )
            
            assert len(results) == 1
            assert results[0]["metadata"]["type"] == "text"
            assert results[0]["metadata"]["custom"] == "value"
    finally:
        await asyncio.to_thread(Path(file_path).unlink)


class TestDataIngestionFunctions:
    """Tests for data_ingestion/functions.py convenience functions."""

    @pytest.mark.asyncio
    async def test_create_ingestion_service_basic(self):
        """Test create_ingestion_service with basic parameters."""
        with patch("src.core.data_ingestion.functions.DataIngestionService") as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service

            service = create_ingestion_service()

            assert service == mock_service
            mock_service_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_ingestion_service_with_all_params(self):
        """Test create_ingestion_service with all parameters."""
        mock_rag = MagicMock()
        mock_cache = MagicMock()
        mock_gateway = MagicMock()
        mock_db = MagicMock()

        with patch("src.core.data_ingestion.functions.DataIngestionService") as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service

            service = create_ingestion_service(
                rag_system=mock_rag,
                cache=mock_cache,
                gateway=mock_gateway,
                db=mock_db,
                enable_validation=False,
                enable_cleansing=False,
                enable_auto_ingest=False,
                enable_caching=False,
                tenant_id="tenant-1",
                custom_param="value",
            )

            assert service == mock_service
            mock_service_class.assert_called_once_with(
                rag_system=mock_rag,
                cache=mock_cache,
                gateway=mock_gateway,
                db=mock_db,
                enable_validation=False,
                enable_cleansing=False,
                enable_auto_ingest=False,
                enable_caching=False,
                tenant_id="tenant-1",
                custom_param="value",
            )

    @pytest.mark.asyncio
    async def test_upload_and_process(self):
        """Test upload_and_process convenience function."""
        mock_rag = MagicMock()
        mock_cache = MagicMock()

        with patch("src.core.data_ingestion.functions.create_ingestion_service") as mock_create:
            mock_service = MagicMock()
            mock_service.upload_and_process = AsyncMock(return_value={"success": True, "document_id": "doc-123"})
            mock_create.return_value = mock_service

            result = await upload_and_process(
                file_path="test.txt",
                rag_system=mock_rag,
                cache=mock_cache,
                title="Test Document",
                metadata={"key": "value"},
                tenant_id="tenant-1",
            )

            assert result["success"] is True
            assert result["document_id"] == "doc-123"
            mock_create.assert_called_once_with(
                rag_system=mock_rag,
                cache=mock_cache,
                gateway=None,
                db=None,
                tenant_id="tenant-1",
            )
            mock_service.upload_and_process.assert_called_once_with(
                file_path="test.txt",
                title="Test Document",
                metadata={"key": "value"},
            )

    @pytest.mark.asyncio
    async def test_upload_and_process_async(self):
        """Test upload_and_process_async alias function."""
        mock_rag = MagicMock()
        mock_cache = MagicMock()

        with patch("src.core.data_ingestion.functions.upload_and_process") as mock_upload:
            mock_upload.return_value = {"success": True, "document_id": "doc-123"}

            result = await upload_and_process_async(
                file_path="test.txt",
                rag_system=mock_rag,
                cache=mock_cache,
                title="Test Document",
                metadata={"key": "value"},
                tenant_id="tenant-1",
            )

            assert result["success"] is True
            mock_upload.assert_called_once_with(
                "test.txt",
                mock_rag,
                mock_cache,
                None,
                None,
                "Test Document",
                {"key": "value"},
                "tenant-1",
            )

    @pytest.mark.asyncio
    async def test_batch_upload_and_process(self):
        """Test batch_upload_and_process convenience function."""
        mock_rag = MagicMock()
        mock_cache = MagicMock()

        with patch("src.core.data_ingestion.functions.create_ingestion_service") as mock_create:
            mock_service = MagicMock()
            mock_service.batch_upload_and_process = AsyncMock(
                return_value=[
                    {"success": True, "document_id": "doc-1"},
                    {"success": True, "document_id": "doc-2"},
                ]
            )
            mock_create.return_value = mock_service

            result = await batch_upload_and_process(
                file_paths=["test1.txt", "test2.txt"],
                rag_system=mock_rag,
                cache=mock_cache,
                titles=["Title 1", "Title 2"],
                metadata_list=[{"key1": "value1"}, {"key2": "value2"}],
                tenant_id="tenant-1",
            )

            assert len(result) == 2
            assert result[0]["success"] is True
            assert result[1]["success"] is True
            mock_create.assert_called_once_with(
                rag_system=mock_rag,
                cache=mock_cache,
                gateway=None,
                db=None,
                tenant_id="tenant-1",
            )
            mock_service.batch_upload_and_process.assert_called_once_with(
                file_paths=["test1.txt", "test2.txt"],
                titles=["Title 1", "Title 2"],
                metadata_list=[{"key1": "value1"}, {"key2": "value2"}],
            )

    @pytest.mark.asyncio
    async def test_batch_upload_and_process_async(self):
        """Test batch_upload_and_process_async alias function."""
        mock_rag = MagicMock()
        mock_cache = MagicMock()

        with patch("src.core.data_ingestion.functions.batch_upload_and_process") as mock_batch:
            mock_batch.return_value = [
                {"success": True, "document_id": "doc-1"},
                {"success": True, "document_id": "doc-2"},
            ]

            result = await batch_upload_and_process_async(
                file_paths=["test1.txt", "test2.txt"],
                rag_system=mock_rag,
                cache=mock_cache,
                titles=["Title 1", "Title 2"],
                metadata_list=[{"key1": "value1"}, {"key2": "value2"}],
                tenant_id="tenant-1",
            )

            assert len(result) == 2
            mock_batch.assert_called_once_with(
                ["test1.txt", "test2.txt"],
                mock_rag,
                mock_cache,
                None,
                None,
                ["Title 1", "Title 2"],
                [{"key1": "value1"}, {"key2": "value2"}],
                "tenant-1",
            )

