"""
Motadata AI SDK - Function as a Service (FaaS) Architecture

This package provides the FaaS implementation of the Motadata AI SDK,
where each AI component is transformed into an independent, scalable service.

Architecture:
- Services: Each AI component as an independent service (Agent, RAG, Gateway, ML, Cache, Prompt, Data Ingestion)
- Integrations: NATS (messaging), OTEL (observability), CODEC (serialization)
- Shared Components: Common utilities, contracts, middleware, database connections

Services communicate via:
- Direct HTTP calls (synchronous)
- NATS message bus (asynchronous)
- Shared state (PostgreSQL, Redis)
"""

__version__ = "0.1.0"

# Import from shared components
try:
    from .shared.contracts import (
        ServiceRequest,
        ServiceResponse,
        ErrorResponse,
        StandardHeaders,
    )
    from .shared.config import ServiceConfig, load_config
    from .shared.exceptions import (
        ServiceException,
        ValidationError,
        NotFoundError,
        InternalServerError,
    )
except ImportError:
    # Fallback if shared components not available
    ServiceRequest = None
    ServiceResponse = None
    ErrorResponse = None
    StandardHeaders = None
    ServiceConfig = None
    load_config = None
    ServiceException = None
    ValidationError = None
    NotFoundError = None
    InternalServerError = None

# Import from integrations
try:
    from .integrations import (
        create_nats_client,
        create_otel_tracer,
        create_codec_manager,
    )
except ImportError:
    create_nats_client = None
    create_otel_tracer = None
    create_codec_manager = None

__all__ = [
    # Contracts
    "ServiceRequest",
    "ServiceResponse",
    "ErrorResponse",
    "StandardHeaders",
    # Configuration
    "ServiceConfig",
    "load_config",
    # Exceptions
    "ServiceException",
    "ValidationError",
    "NotFoundError",
    "InternalServerError",
    # Integrations
    "create_nats_client",
    "create_otel_tracer",
    "create_codec_manager",
]

