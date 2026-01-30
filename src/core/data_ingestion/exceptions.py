"""
Data Ingestion Exceptions
"""

from typing import Optional

from ..exceptions import SDKError


class DataIngestionError(SDKError):
    """Base exception for data ingestion errors."""

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.file_path = file_path
        self.original_error = original_error


class ValidationError(DataIngestionError):
    """Exception for validation errors."""

    pass
