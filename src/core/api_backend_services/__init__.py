"""
API Backend Services

API services, endpoints, and backend integration.
"""

from .functions import (
    add_api_versioning,
    add_endpoint,
    add_health_check,
    configure_api_app,
    create_agent_endpoints,
    create_api_app,
    create_api_router,
    create_gateway_endpoints,
    create_rag_endpoints,
    create_unified_query_endpoint,
    register_router,
)

__all__ = [
    # Factory functions
    "create_api_app",
    "create_api_router",
    "configure_api_app",
    # High-level convenience functions
    "register_router",
    "add_endpoint",
    "create_rag_endpoints",
    "create_agent_endpoints",
    "create_gateway_endpoints",
    "create_unified_query_endpoint",
    # Utility functions
    "add_health_check",
    "add_api_versioning",
]
