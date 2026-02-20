"""
CODEC Integration Module

Provides message encoding/decoding with schema versioning and validation
for type-safe, versioned communication between AI SDK components.
"""

from .bootstrap import bootstrap, register_all_migrations, register_all_schemas
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
    decode_agent_requirements,
    decode_llm_response,
    decode_prompt_template,
    decode_rag_query,
    decode_tool_requirements,
    encode_agent_message,
    encode_agent_requirements,
    encode_llm_request,
    encode_prompt_template,
    encode_rag_document,
    encode_tool_requirements,
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
    # Bootstrap functions
    "bootstrap",
    "register_all_schemas",
    "register_all_migrations",
    # Helper functions
    "encode_agent_message",
    "decode_agent_message",
    "encode_agent_requirements",
    "decode_agent_requirements",
    "encode_tool_requirements",
    "decode_tool_requirements",
    "encode_prompt_template",
    "decode_prompt_template",
    "encode_llm_request",
    "decode_llm_response",
    "encode_rag_document",
    "decode_rag_query",
]

