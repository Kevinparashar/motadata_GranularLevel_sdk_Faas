"""
Data Cleaner

Cleanses and normalizes processed data.
"""

# Standard library imports
import re
from typing import Any, Dict, Optional


class DataCleaner:
    """
    Cleanses and normalizes data content.
    """

    def __init__(
        self,
        remove_extra_whitespace: bool = True,
        normalize_unicode: bool = True,
        remove_control_chars: bool = True,
        normalize_line_endings: bool = True,
    ):
        """
        Initialize cleaner.

        Args:
            remove_extra_whitespace: Remove extra whitespace
            normalize_unicode: Normalize unicode characters
            remove_control_chars: Remove control characters
            normalize_line_endings: Normalize line endings
        """
        self.remove_extra_whitespace = remove_extra_whitespace
        self.normalize_unicode = normalize_unicode
        self.remove_control_chars = remove_control_chars
        self.normalize_line_endings = normalize_line_endings

    def clean(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Clean content.

        Args:
            content: Content to clean
            metadata: Optional metadata

        Returns:
            Cleaned content
        """
        if not content:
            return content

        # Normalize line endings
        if self.normalize_line_endings:
            content = content.replace("\r\n", "\n").replace("\r", "\n")

        # Remove control characters
        if self.remove_control_chars:
            content = str(re.sub(r"[\x00-\x1f\x7f-\x9f]", "", content))

        # Normalize unicode
        if self.normalize_unicode:
            try:
                import unicodedata

                content = unicodedata.normalize("NFKD", content)
            except ImportError:
                pass  # Skip if unicodedata not available

        # Remove extra whitespace
        if self.remove_extra_whitespace:
            # Replace multiple spaces with single space
            content = str(re.sub(r" +", " ", content))
            # Replace multiple newlines with double newline
            content = str(re.sub(r"\n{3,}", "\n\n", content))
            # Strip leading/trailing whitespace
            content = content.strip()

        return content
