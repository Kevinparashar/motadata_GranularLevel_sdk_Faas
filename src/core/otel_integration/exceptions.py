"""
OTEL Integration Exceptions

Custom exceptions for OpenTelemetry integration operations.
"""

from typing import Optional

from src.core.exceptions import SDKError


class OTELError(SDKError):
    """Base exception for OTEL integration errors."""

    def __init__(
        self,
        message: str,
        component: str = "otel_integration",
        original_error: Optional[Exception] = None,
    ):
        """
        Initialize OTEL error.
        
        Args:
            message: Error message
            component: Component name
            original_error: Original exception that caused this error
        """
        super().__init__(message, original_error=original_error)
        self.message = message
        self.component = component
        self.original_error = original_error


class OTELTracingError(OTELError):
    """Exception raised when tracing operations fail."""
    
    def __init__(
        self,
        message: str,
        span_name: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        """
        Initialize tracing error.
        
        Args:
            message: Error message
            span_name: Name of the span that failed
            original_error: Original exception that caused this error
        """
        super().__init__(message, component="otel_tracing", original_error=original_error)
        self.span_name = span_name


class OTELMetricsError(OTELError):
    """Exception raised when metrics operations fail."""
    
    def __init__(
        self,
        message: str,
        metric_name: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        """
        Initialize metrics error.
        
        Args:
            message: Error message
            metric_name: Name of the metric that failed
            original_error: Original exception that caused this error
        """
        super().__init__(message, component="otel_metrics", original_error=original_error)
        self.metric_name = metric_name


class OTELContextError(OTELError):
    """Exception raised when trace context operations fail."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        """
        Initialize context error.
        
        Args:
            message: Error message
            operation: Operation that failed (inject/extract)
            original_error: Original exception that caused this error
        """
        super().__init__(message, component="otel_context", original_error=original_error)
        self.operation = operation

