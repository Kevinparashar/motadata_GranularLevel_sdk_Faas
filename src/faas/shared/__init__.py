"""
Shared components for FaaS services.

This module contains common utilities, contracts, and middleware
used across all AI component services.
"""

from .contracts import (
    ServiceRequest,
    ServiceResponse,
    ErrorResponse,
    StandardHeaders,
)
from .middleware import (
    setup_middleware,
    auth_middleware,
    logging_middleware,
    error_handler,
)
from .database import (
    get_database_connection,
    DatabaseConnection,
)
from .config import (
    ServiceConfig,
    load_config,
    get_config,
)
from .exceptions import (
    ServiceException,
    ValidationError,
    NotFoundError,
    InternalServerError,
)
from .http_client import (
    ServiceHTTPClient,
    ServiceClientManager,
    create_service_client,
    ServiceClientError,
    ServiceUnavailableError,
    ServiceTimeoutError,
)
from .agent_storage import AgentStorage

__all__ = [
    # Contracts
    "ServiceRequest",
    "ServiceResponse",
    "ErrorResponse",
    "StandardHeaders",
    # Middleware
    "setup_middleware",
    "auth_middleware",
    "logging_middleware",
    "error_handler",
    # Database
    "get_database_connection",
    "DatabaseConnection",
    # Configuration
    "ServiceConfig",
    "load_config",
    "get_config",
    # HTTP Client
    "ServiceHTTPClient",
    "ServiceClientManager",
    "create_service_client",
    "ServiceClientError",
    "ServiceUnavailableError",
    "ServiceTimeoutError",
    # Agent Storage
    "AgentStorage",
    # Exceptions
    "ServiceException",
    "ValidationError",
    "NotFoundError",
    "InternalServerError",
]
