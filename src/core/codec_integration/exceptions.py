"""
CODEC Integration Exception Hierarchy

Exceptions specific to CODEC serialization, schema validation, and version migration.
"""

from typing import Optional

from ..exceptions import SDKError


class CodecError(SDKError):
    """Base exception for CODEC-related errors."""

    pass


class CodecEncodingError(CodecError):
    """
    Raised when encoding fails.

    Attributes:
        message_type: Type of message that failed to encode
        data: Data that failed to encode (may be truncated for large payloads)
    """

    def __init__(
        self,
        message: str,
        message_type: Optional[str] = None,
        data: Optional[dict] = None,
        original_error: Optional[Exception] = None,
    ):
        """
        Initialize encoding error.
        
        Args:
            message (str): Input parameter for this operation.
            message_type (Optional[str]): Input parameter for this operation.
            data (Optional[dict]): Input parameter for this operation.
            original_error (Optional[Exception]): Input parameter for this operation.
        """
        super().__init__(message, original_error)
        self.message_type = message_type
        self.data = data


class CodecDecodingError(CodecError):
    """
    Raised when decoding fails.

    Attributes:
        payload: Payload that failed to decode (may be truncated)
        schema_version: Schema version of the payload (if detected)
    """

    def __init__(
        self,
        message: str,
        payload: Optional[bytes] = None,
        schema_version: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        """
        Initialize decoding error.
        
        Args:
            message (str): Input parameter for this operation.
            payload (Optional[bytes]): Input parameter for this operation.
            schema_version (Optional[str]): Input parameter for this operation.
            original_error (Optional[Exception]): Input parameter for this operation.
        """
        super().__init__(message, original_error)
        self.payload = payload
        self.schema_version = schema_version


class SchemaValidationError(CodecError):
    """
    Raised when schema validation fails.

    Attributes:
        schema_name: Name of the schema that failed validation
        validation_errors: List of validation error messages
    """

    def __init__(
        self,
        message: str,
        schema_name: Optional[str] = None,
        validation_errors: Optional[list] = None,
        original_error: Optional[Exception] = None,
    ):
        """
        Initialize schema validation error.
        
        Args:
            message (str): Input parameter for this operation.
            schema_name (Optional[str]): Input parameter for this operation.
            validation_errors (Optional[list]): Input parameter for this operation.
            original_error (Optional[Exception]): Input parameter for this operation.
        """
        super().__init__(message, original_error)
        self.schema_name = schema_name
        self.validation_errors = validation_errors or []


class SchemaVersionError(CodecError):
    """
    Raised when schema version is invalid or unsupported.

    Attributes:
        schema_name: Name of the schema
        version: Version that caused the error
        supported_versions: List of supported versions
    """

    def __init__(
        self,
        message: str,
        schema_name: Optional[str] = None,
        version: Optional[str] = None,
        supported_versions: Optional[list] = None,
        original_error: Optional[Exception] = None,
    ):
        """
        Initialize schema version error.
        
        Args:
            message (str): Input parameter for this operation.
            schema_name (Optional[str]): Input parameter for this operation.
            version (Optional[str]): Input parameter for this operation.
            supported_versions (Optional[list]): Input parameter for this operation.
            original_error (Optional[Exception]): Input parameter for this operation.
        """
        super().__init__(message, original_error)
        self.schema_name = schema_name
        self.version = version
        self.supported_versions = supported_versions or []


class MigrationError(CodecError):
    """
    Raised when schema migration fails.

    Attributes:
        schema_name: Name of the schema
        from_version: Source version
        to_version: Target version
    """

    def __init__(
        self,
        message: str,
        schema_name: Optional[str] = None,
        from_version: Optional[str] = None,
        to_version: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        """
        Initialize migration error.
        
        Args:
            message (str): Input parameter for this operation.
            schema_name (Optional[str]): Input parameter for this operation.
            from_version (Optional[str]): Input parameter for this operation.
            to_version (Optional[str]): Input parameter for this operation.
            original_error (Optional[Exception]): Input parameter for this operation.
        """
        super().__init__(message, original_error)
        self.schema_name = schema_name
        self.from_version = from_version
        self.to_version = to_version

