"""
LiteLLM Gateway

Unified gateway for multiple LLM providers with modular architecture.
"""

from .gateway import LiteLLMGateway, GatewayConfig, GenerateResponse, EmbedResponse
from .functions import (
    create_gateway,
    configure_gateway,
    generate_text,
    generate_text_async,
    stream_text,
    generate_embeddings,
    generate_embeddings_async,
    batch_generate,
)

__all__ = [
    # Core classes
    "LiteLLMGateway",
    "GatewayConfig",
    "GenerateResponse",
    "EmbedResponse",
    # Factory functions
    "create_gateway",
    "configure_gateway",
    # High-level convenience functions
    "generate_text",
    "generate_text_async",
    "stream_text",
    "generate_embeddings",
    "generate_embeddings_async",
    # Utility functions
    "batch_generate",
]
