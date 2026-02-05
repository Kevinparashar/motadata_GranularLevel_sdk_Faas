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
            remove_extra_whitespace (bool): Input parameter for this operation.
            normalize_unicode (bool): Input parameter for this operation.
            remove_control_chars (bool): Input parameter for this operation.
            normalize_line_endings (bool): Input parameter for this operation.
        """
        self.remove_extra_whitespace = remove_extra_whitespace
        self.normalize_unicode = normalize_unicode
        self.remove_control_chars = remove_control_chars
        self.normalize_line_endings = normalize_line_endings

    async def clean(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Clean content asynchronously.
        
        Args:
            content (str): Content text.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
        
        Returns:
            str: Returned text value.
        """
        import asyncio
        
        if not content:
            return content

        # Run CPU-intensive operations in thread pool to prevent blocking
        def _clean_sync() -> str:
            result = content
            
            # Normalize line endings
            if self.normalize_line_endings:
                result = result.replace("\r\n", "\n").replace("\r", "\n")

            # Remove control characters
            if self.remove_control_chars:
                result = str(re.sub(r"[\x00-\x1f\x7f-\x9f]", "", result))

            # Normalize unicode
            if self.normalize_unicode:
                try:
                    import unicodedata
                    result = unicodedata.normalize("NFKD", result)
                except ImportError:
                    pass  # Skip if unicodedata not available

            # Remove extra whitespace
            if self.remove_extra_whitespace:
                # Replace multiple spaces with single space
                result = str(re.sub(r" +", " ", result))
                # Replace multiple newlines with double newline
                result = str(re.sub(r"\n{3,}", "\n\n", result))
                # Strip leading/trailing whitespace
                result = result.strip()

            return result
        
        # Run in thread pool to avoid blocking the event loop
        return await asyncio.to_thread(_clean_sync)
