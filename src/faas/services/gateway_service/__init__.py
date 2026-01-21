"""
Gateway Service - FaaS implementation of LiteLLM Gateway.

Provides unified LLM access via LiteLLM with rate limiting, caching, and provider management.
"""

from .service import GatewayService, create_gateway_service
from .models import (
    GenerateRequest,
    GenerateStreamRequest,
    EmbedRequest,
    GenerateResponse,
    EmbedResponse,
)

__all__ = [
    "GatewayService",
    "create_gateway_service",
    "GenerateRequest",
    "GenerateStreamRequest",
    "EmbedRequest",
    "GenerateResponse",
    "EmbedResponse",
]

