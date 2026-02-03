"""
Shared components for FaaS services.

This module contains common utilities, contracts, and middleware
used across all AI component services.
"""


from .agent_storage import AgentStorage
from .config import (
    ServiceConfig,
    get_config,
    load_config,
)
from .contracts import (
    ErrorResponse,
    ServiceRequest,
    ServiceResponse,
    StandardHeaders,
)
from .database import (
    DatabaseConnection,
    get_database_connection,
)
from .exceptions import (
    InternalServerError,
    NotFoundError,
    ServiceException,
    ValidationError,
)
from .http_client import (
    ServiceClientError,
    ServiceClientManager,
    ServiceHTTPClient,
    ServiceTimeoutError,
    ServiceUnavailableError,
    create_service_client,
)
from .middleware import (
    auth_middleware,
    error_handler,
    logging_middleware,
    setup_middleware,
)

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
