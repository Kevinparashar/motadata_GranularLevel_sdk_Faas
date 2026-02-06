"""
Unit tests for Data Ingestion components.
"""


import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.core.data_ingestion.data_cleaner import DataCleaner
from src.core.data_ingestion.data_validator import DataValidator
from src.core.data_ingestion.exceptions import DataIngestionError
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
    with patch("src.core.data_ingestion.ingestion_service.create_rag_system"), \
         patch("src.core.data_ingestion.ingestion_service.create_cache"), \
         patch("src.core.data_ingestion.ingestion_service.create_multimodal_loader"):
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

