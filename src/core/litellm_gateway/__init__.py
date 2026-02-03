"""
LiteLLM Gateway

Unified gateway for multiple LLM providers with modular architecture.
"""


from .functions import (
    batch_generate,
    configure_gateway,
    create_gateway,
    generate_embeddings,
    generate_embeddings_async,
    generate_text,
    generate_text_async,
    stream_text,
)
from .gateway import EmbedResponse, GatewayConfig, GenerateResponse, LiteLLMGateway
from .kv_cache import KVCacheEntry, KVCacheManager, create_kv_cache_manager

__all__ = [
    # Core classes
    "LiteLLMGateway",
    "GatewayConfig",
    "GenerateResponse",
    "EmbedResponse",
    # KV Cache
    "KVCacheManager",
    "create_kv_cache_manager",
    "KVCacheEntry",
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
