"""
Core SDK Exception Hierarchy

Base exception class for all SDK errors.
"""

from typing import Optional


class SDKError(Exception):
    """
    Base exception class for all SDK errors.

    This enables platform-wide catching and uniform error handling.
    All SDK-specific exceptions should inherit from this class.

    Attributes:
        message: Human-readable error message
        original_error: Original exception that caused this error (if any)
    """

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        """
        Initialize SDK error.

        Args:
            message: Error message
            original_error: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.original_error = original_error

    def __str__(self) -> str:
        """Return string representation of error."""
        if self.original_error:
            return f"{self.message} (Original: {str(self.original_error)})"
        return self.message
