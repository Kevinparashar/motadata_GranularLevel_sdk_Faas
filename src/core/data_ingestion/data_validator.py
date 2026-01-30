"""
Data Validator

Validates uploaded files for format, size, and content.
"""

# Standard library imports
import mimetypes
from pathlib import Path
from typing import Any, Dict, List, Optional

# Local application/library specific imports


class DataValidator:
    """
    Validates data files before processing.
    """

    # Format constants
    JSON_EXT = ".json"

    # Supported formats
    SUPPORTED_TEXT = [".txt", ".md", ".markdown", ".html", JSON_EXT]
    SUPPORTED_DOCUMENTS = [".pdf", ".doc", ".docx", ".rtf"]
    SUPPORTED_AUDIO = [".mp3", ".wav", ".m4a", ".ogg", ".flac"]
    SUPPORTED_VIDEO = [".mp4", ".avi", ".mov", ".mkv", ".webm"]
    SUPPORTED_IMAGES = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
    SUPPORTED_STRUCTURED = [".csv", JSON_EXT, ".xml", ".xlsx", ".xls"]

    SUPPORTED_FORMATS = (
        SUPPORTED_TEXT
        + SUPPORTED_DOCUMENTS
        + SUPPORTED_AUDIO
        + SUPPORTED_VIDEO
        + SUPPORTED_IMAGES
        + SUPPORTED_STRUCTURED
    )

    # Size limits (in bytes)
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB
    MAX_TEXT_SIZE = 100 * 1024 * 1024  # 100 MB

    def __init__(
        self, max_file_size: Optional[int] = None, allowed_formats: Optional[List[str]] = None
    ):
        """
        Initialize validator.

        Args:
            max_file_size: Maximum file size in bytes
            allowed_formats: List of allowed formats (None = all supported)
        """
        self.file_size_limit = max_file_size or self.MAX_FILE_SIZE
        self.allowed_formats = allowed_formats or self.SUPPORTED_FORMATS

    def validate_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Validate a file.

        Args:
            file_path: Path to file

        Returns:
            Dictionary with validation result
        """
        if not file_path.exists():
            return {"valid": False, "error": f"File not found: {file_path}"}

        # Check file size
        file_size = file_path.stat().st_size
        if file_size > self.file_size_limit:
            return {
                "valid": False,
                "error": f"File too large: {file_size} bytes (max: {self.file_size_limit})",
            }

        # Check format
        suffix = file_path.suffix.lower()
        if suffix not in self.allowed_formats:
            return {
                "valid": False,
                "error": f"Unsupported format: {suffix}. Supported: {', '.join(self.allowed_formats)}",
            }

        # Check MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            # Additional validation based on MIME type
            if not self._is_valid_mime_type(mime_type, suffix):
                return {"valid": False, "error": f"MIME type mismatch: {mime_type} for {suffix}"}

        return {"valid": True, "file_size": file_size, "format": suffix, "mime_type": mime_type}

    def _is_valid_mime_type(self, mime_type: str, suffix: str) -> bool:
        """Check if MIME type matches file extension."""
        # Basic validation - can be enhanced
        mime_map = {
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".mp4": "video/mp4",
            ".jpg": "image/jpeg",
            ".png": "image/png",
        }

        expected_mime = mime_map.get(suffix)
        if expected_mime:
            return mime_type.startswith(expected_mime.split("/")[0])

        return True  # Allow if not in map

    def validate_content(self, content: str, format: str) -> Dict[str, Any]:
        """
        Validate content structure.

        Args:
            content: Content to validate
            format: File format

        Returns:
            Validation result
        """
        if len(content) > self.MAX_TEXT_SIZE:
            return {"valid": False, "error": f"Content too large: {len(content)} bytes"}

        # Format-specific validation
        if format == self.JSON_EXT:
            try:
                import json

                json.loads(content)
            except json.JSONDecodeError as e:
                return {"valid": False, "error": f"Invalid JSON: {str(e)}"}

        return {"valid": True}
