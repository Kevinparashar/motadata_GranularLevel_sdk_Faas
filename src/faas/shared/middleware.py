"""
Common middleware for FaaS services.

Provides authentication, logging, error handling, and observability.
"""

import logging
import time
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .contracts import ErrorResponse
from .exceptions import ServiceException

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response."""
        start_time = time.time()

        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "tenant_id": request.headers.get("X-Tenant-ID"),
                "correlation_id": request.headers.get("X-Correlation-ID"),
            },
        )

        # Process request
        response = await call_next(request)

        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Response: {response.status_code} - {process_time:.3f}s",
            extra={
                "status_code": response.status_code,
                "process_time": process_time,
                "tenant_id": request.headers.get("X-Tenant-ID"),
                "correlation_id": request.headers.get("X-Correlation-ID"),
            },
        )

        # Add process time header
        response.headers["X-Process-Time"] = str(process_time)

        return response


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for authentication validation."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate authentication headers."""
        # Extract tenant_id from header (set by API Gateway)
        tenant_id = request.headers.get("X-Tenant-ID")

        if not tenant_id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "success": False,
                    "error": {
                        "code": "MISSING_TENANT_ID",
                        "message": "X-Tenant-ID header is required",
                    },
                },
            )

        # Continue with request
        response = await call_next(request)
        return response


async def error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global error handler for all services.

    Args:
        request: FastAPI request object
        exc: Exception that was raised

    Returns:
        JSON error response
    """
    correlation_id = request.headers.get("X-Correlation-ID", "unknown")
    request_id = request.headers.get("X-Request-ID", "unknown")

    if isinstance(exc, ServiceException):
        status_code = exc.status_code
        error_code = exc.error_code
        error_message = exc.message
        error_details = exc.details
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_code = "INTERNAL_SERVER_ERROR"
        error_message = "An unexpected error occurred"
        error_details = {"type": type(exc).__name__, "message": str(exc)}

    logger.error(
        f"Error: {error_code} - {error_message}",
        exc_info=exc,
        extra={
            "correlation_id": correlation_id,
            "request_id": request_id,
            "error_code": error_code,
            "status_code": status_code,
        },
    )

    error_response = ErrorResponse(
        success=False,
        error={
            "code": error_code,
            "message": error_message,
            "details": error_details,
        },
        correlation_id=correlation_id,
        request_id=request_id,
    )

    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(),
    )


def setup_middleware(app):
    """
    Setup common middleware for FastAPI app.

    Args:
        app: FastAPI application instance
    """
    # Add logging middleware
    app.add_middleware(LoggingMiddleware)

    # Add auth middleware
    app.add_middleware(AuthMiddleware)

    # Add error handler
    app.add_exception_handler(Exception, error_handler)

    logger.info("Middleware setup completed")


def auth_middleware(request: Request) -> str:
    """
    Extract and validate tenant_id from request.

    Args:
        request: FastAPI request object

    Returns:
        Tenant ID

    Raises:
        ServiceException: If tenant_id is missing
    """
    tenant_id = request.headers.get("X-Tenant-ID")
    if not tenant_id:
        from .exceptions import ValidationError

        raise ValidationError("X-Tenant-ID header is required")

    return tenant_id


def logging_middleware(func: Callable) -> Callable:
    """
    Decorator for function-level logging.

    Args:
        func: Function to wrap

    Returns:
        Wrapped function with logging
    """
    import functools

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger.info(f"Executing {func.__name__}")
        try:
            result = await func(*args, **kwargs)
            logger.info(f"Completed {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            raise

    return wrapper
