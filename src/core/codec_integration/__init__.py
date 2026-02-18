"""
CODEC Integration Module

Provides message encoding/decoding with schema versioning and validation
for type-safe, versioned communication between AI SDK components.
"""

from .codec_serializer import CodecSerializer
from .exceptions import (
    CodecDecodingError,
    CodecEncodingError,
    CodecError,
    MigrationError,
    SchemaValidationError,
    SchemaVersionError,
)
from .functions import (
    create_codec_serializer,
    decode_agent_message,
    decode_llm_response,
    decode_rag_query,
    encode_agent_message,
    encode_llm_request,
    encode_rag_document,
)

__all__ = [
    # Core classes
    "CodecSerializer",
    # Exceptions
    "CodecError",
    "CodecEncodingError",
    "CodecDecodingError",
    "SchemaValidationError",
    "SchemaVersionError",
    "MigrationError",
    # Factory functions
    "create_codec_serializer",
    # Helper functions
    "encode_agent_message",
    "decode_agent_message",
    "encode_llm_request",
    "decode_llm_response",
    "encode_rag_document",
    "decode_rag_query",
]

