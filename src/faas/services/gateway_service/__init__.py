"""
Gateway Service - FaaS implementation of LiteLLM Gateway.

Provides unified LLM access via LiteLLM with rate limiting, caching, and provider management.
"""


from .models import (
    EmbedRequest,
    EmbedResponse,
    GenerateRequest,
    GenerateResponse,
    GenerateStreamRequest,
)
from .service import GatewayService, create_gateway_service

__all__ = [
    "GatewayService",
    "create_gateway_service",
    "GenerateRequest",
    "GenerateStreamRequest",
    "EmbedRequest",
    "GenerateResponse",
    "EmbedResponse",
]
