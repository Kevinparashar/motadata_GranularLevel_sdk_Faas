"""
Common exceptions for FaaS services.
"""


from typing import Any, Dict, Optional


class ServiceException(Exception):
    """Base exception for all service errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "SERVICE_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize service exception.
        
        Args:
            message (str): Input parameter for this operation.
            status_code (int): Input parameter for this operation.
            error_code (str): Input parameter for this operation.
            details (Optional[Dict[str, Any]]): Input parameter for this operation.
        """
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(ServiceException):
    """Exception for validation errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize validation error.
        
        Args:
            message (str): Input parameter for this operation.
            details (Optional[Dict[str, Any]]): Input parameter for this operation.
        """
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class NotFoundError(ServiceException):
    """Exception for resource not found errors."""

    def __init__(self, resource_type: str, resource_id: str):
        """
        Initialize not found error.
        
        Args:
            resource_type (str): Input parameter for this operation.
            resource_id (str): Input parameter for this operation.
        """
        super().__init__(
            message=f"{resource_type} with id '{resource_id}' not found",
            status_code=404,
            error_code="NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


class InternalServerError(ServiceException):
    """Exception for internal server errors."""

    def __init__(
        self,
        message: str = "An internal server error occurred",
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize internal server error.
        
        Args:
            message (str): Input parameter for this operation.
            details (Optional[Dict[str, Any]]): Input parameter for this operation.
        """
        super().__init__(
            message=message,
            status_code=500,
            error_code="INTERNAL_SERVER_ERROR",
            details=details,
        )


class DependencyError(ServiceException):
    """Exception for dependency service errors."""

    def __init__(self, service_name: str, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize dependency error.
        
        Args:
            service_name (str): Input parameter for this operation.
            message (str): Input parameter for this operation.
            details (Optional[Dict[str, Any]]): Input parameter for this operation.
        """
        super().__init__(
            message=f"Dependency service '{service_name}' error: {message}",
            status_code=502,
            error_code="DEPENDENCY_ERROR",
            details={"service_name": service_name, **(details or {})},
        )
