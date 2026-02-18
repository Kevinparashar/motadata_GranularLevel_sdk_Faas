"""
CODEC Integration - High-Level Functions

Factory functions and convenience functions for codec operations.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from .codec_serializer import CodecSerializer

# ============================================================================
# Factory Functions
# ============================================================================


def create_codec_serializer(
    codec_type: str = "json",
    schema_registry: Optional[Any] = None,
    migration_manager: Optional[Any] = None,
) -> CodecSerializer:
    """
    Create and configure a codec serializer with default settings.

    Args:
        codec_type: Codec type ("json", "msgpack", "protobuf")
        schema_registry: Optional schema registry instance
        migration_manager: Optional migration manager instance

    Returns:
        Configured CodecSerializer instance

    Example:
        >>> codec = create_codec_serializer(codec_type="json")
        >>> envelope = codec.create_envelope("agent_message", "1.0", {"key": "value"})
    """
    return CodecSerializer(
        schema_registry=schema_registry,
        migration_manager=migration_manager,
        codec_type=codec_type,
    )


# ============================================================================
# Helper Functions for Component Integration
# ============================================================================


async def encode_agent_message(
    message: Any,
    codec: Optional[CodecSerializer] = None,
    schema_version: str = "1.0",
) -> bytes:
    """
    Encode an agent message to bytes.

    Args:
        message: AgentMessage instance or dictionary
        codec: CodecSerializer instance (creates default if not provided)
        schema_version: Schema version to use

    Returns:
        Encoded bytes

    Example:
        >>> from src.core.agno_agent_framework import AgentMessage
        >>> message = AgentMessage(from_agent="a1", to_agent="a2", content="Hello")
        >>> encoded = await encode_agent_message(message)
    """
    if codec is None:
        codec = create_codec_serializer()

    # Convert message to dictionary if it's a Pydantic model
    if hasattr(message, "model_dump"):
        raw_dict = message.model_dump()
        # Map AgentMessage fields to schema fields
        message_dict = {
            "message_id": raw_dict.get("message_id") or str(id(message)),
            "source_agent_id": raw_dict.get("from_agent", "") or raw_dict.get("source_agent_id", ""),
            "target_agent_id": raw_dict.get("to_agent", "") or raw_dict.get("target_agent_id", ""),
            "content": raw_dict.get("content", ""),
            "message_type": raw_dict.get("message_type", "text"),
            "timestamp": (
                raw_dict.get("timestamp").isoformat() 
                if raw_dict.get("timestamp") and hasattr(raw_dict.get("timestamp"), "isoformat")
                else datetime.now().isoformat()
            ),
            "metadata": raw_dict.get("metadata", {}),
        }
    elif hasattr(message, "dict"):
        raw_dict = message.dict()
        # Map AgentMessage fields to schema fields
        message_dict = {
            "message_id": raw_dict.get("message_id") or str(id(message)),
            "source_agent_id": raw_dict.get("from_agent", "") or raw_dict.get("source_agent_id", ""),
            "target_agent_id": raw_dict.get("to_agent", "") or raw_dict.get("target_agent_id", ""),
            "content": raw_dict.get("content", ""),
            "message_type": raw_dict.get("message_type", "text"),
            "timestamp": (
                raw_dict.get("timestamp").isoformat() 
                if raw_dict.get("timestamp") and hasattr(raw_dict.get("timestamp"), "isoformat")
                else datetime.now().isoformat()
            ),
            "metadata": raw_dict.get("metadata", {}),
        }
    elif isinstance(message, dict):
        # Map dictionary fields if needed
        message_dict = {
            "message_id": message.get("message_id") or message.get("id") or str(id(message)),
            "source_agent_id": message.get("from_agent", "") or message.get("source_agent_id", ""),
            "target_agent_id": message.get("to_agent", "") or message.get("target_agent_id", ""),
            "content": message.get("content", ""),
            "message_type": message.get("message_type", "text"),
            "timestamp": message.get("timestamp", datetime.now().isoformat()),
            "metadata": message.get("metadata", {}),
        }
    else:
        message_dict = {
            "message_id": getattr(message, "message_id", None) or str(id(message)),
            "source_agent_id": getattr(message, "from_agent", None) or getattr(message, "source_agent_id", ""),
            "target_agent_id": getattr(message, "to_agent", None) or getattr(message, "target_agent_id", ""),
            "content": getattr(message, "content", ""),
            "message_type": getattr(message, "message_type", "text"),
            "timestamp": getattr(message, "timestamp", datetime.now()).isoformat() if hasattr(getattr(message, "timestamp", None), "isoformat") else datetime.now().isoformat(),
            "metadata": getattr(message, "metadata", {}),
        }

    envelope = codec.create_envelope(
        message_type="agent_message",
        schema_version=schema_version,
        data=message_dict,
    )

    return await codec.encode(envelope)


async def decode_agent_message(
    payload: bytes,
    codec: Optional[CodecSerializer] = None,
    target_version: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Decode bytes to agent message dictionary.

    Args:
        payload: Encoded bytes
        codec: CodecSerializer instance (creates default if not provided)
        target_version: Target schema version (migrates if different)

    Returns:
        Decoded message dictionary

    Example:
        >>> decoded = await decode_agent_message(encoded_bytes)
        >>> message = AgentMessage(**decoded["data"])
    """
    if codec is None:
        codec = create_codec_serializer()

    envelope = await codec.decode(payload)

    # Migrate if needed
    if target_version and envelope.get("schema_version") != target_version:
        envelope = codec.migrate_envelope(envelope, target_version, "agent_message")

    # Validate schema
    codec.validate_schema(envelope, "agent_message")

    return envelope["data"]


async def encode_llm_request(
    request_id: str,
    prompt: str,
    model: str,
    tenant_id: str,
    parameters: Optional[Dict[str, Any]] = None,
    codec: Optional[CodecSerializer] = None,
    schema_version: str = "1.0",
) -> bytes:
    """
    Encode an LLM request to bytes.

    Args:
        request_id: Unique request identifier
        prompt: Prompt text
        model: Model name
        tenant_id: Tenant identifier
        parameters: Optional request parameters
        codec: CodecSerializer instance (creates default if not provided)
        schema_version: Schema version to use

    Returns:
        Encoded bytes
    """
    if codec is None:
        codec = create_codec_serializer()

    envelope = codec.create_envelope(
        message_type="llm_request",
        schema_version=schema_version,
        data={
            "request_id": request_id,
            "prompt": prompt,
            "model": model,
            "tenant_id": tenant_id,
            "parameters": parameters or {},
            "timestamp": datetime.now().isoformat(),
        },
    )

    return await codec.encode(envelope)


async def decode_llm_response(
    payload: bytes,
    codec: Optional[CodecSerializer] = None,
    target_version: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Decode bytes to LLM response dictionary.

    Args:
        payload: Encoded bytes
        codec: CodecSerializer instance (creates default if not provided)
        target_version: Target schema version (migrates if different)

    Returns:
        Decoded response dictionary
    """
    if codec is None:
        codec = create_codec_serializer()

    envelope = await codec.decode(payload)

    # Migrate if needed
    if target_version and envelope.get("schema_version") != target_version:
        envelope = codec.migrate_envelope(envelope, target_version, "llm_response")

    # Validate schema
    codec.validate_schema(envelope, "llm_response")

    return envelope["data"]


async def encode_rag_document(
    document_id: str,
    content: str,
    tenant_id: str,
    metadata: Optional[Dict[str, Any]] = None,
    chunks: Optional[list] = None,
    codec: Optional[CodecSerializer] = None,
    schema_version: str = "1.0",
) -> bytes:
    """
    Encode a RAG document to bytes.

    Args:
        document_id: Document identifier
        content: Document content
        tenant_id: Tenant identifier
        metadata: Optional document metadata
        chunks: Optional document chunks
        codec: CodecSerializer instance (creates default if not provided)
        schema_version: Schema version to use

    Returns:
        Encoded bytes
    """
    if codec is None:
        codec = create_codec_serializer()

    envelope = codec.create_envelope(
        message_type="rag_document",
        schema_version=schema_version,
        data={
            "document_id": document_id,
            "content": content,
            "metadata": metadata or {},
            "chunks": chunks or [],
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
        },
    )

    return await codec.encode(envelope)


async def decode_rag_query(
    payload: bytes,
    codec: Optional[CodecSerializer] = None,
    target_version: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Decode bytes to RAG query dictionary.

    Args:
        payload: Encoded bytes
        codec: CodecSerializer instance (creates default if not provided)
        target_version: Target schema version (migrates if different)

    Returns:
        Decoded query dictionary
    """
    if codec is None:
        codec = create_codec_serializer()

    envelope = await codec.decode(payload)

    # Migrate if needed
    if target_version and envelope.get("schema_version") != target_version:
        envelope = codec.migrate_envelope(envelope, target_version, "rag_query")

    # Validate schema
    codec.validate_schema(envelope, "rag_query")

    return envelope["data"]

