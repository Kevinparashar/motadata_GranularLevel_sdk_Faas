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
        codec_type: Codec type ("json" only - other types are not supported)
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


async def encode_agent_requirements(
    requirements: Any,
    codec: Optional[CodecSerializer] = None,
    schema_version: str = "1.0",
) -> bytes:
    """
    Encode AgentRequirements to bytes.

    Args:
        requirements: AgentRequirements instance or dictionary
        codec: CodecSerializer instance (creates default if not provided)
        schema_version: Schema version to use

    Returns:
        Encoded bytes

    Example:
        >>> from src.core.prompt_based_generator.prompt_interpreter import AgentRequirements
        >>> requirements = AgentRequirements(name="test", description="test", ...)
        >>> encoded = await encode_agent_requirements(requirements)
    """
    if codec is None:
        codec = create_codec_serializer()

    # Convert requirements to dictionary if it's a Pydantic model
    if hasattr(requirements, "model_dump"):
        requirements_dict = requirements.model_dump()
    elif hasattr(requirements, "dict"):
        requirements_dict = requirements.dict()
    elif isinstance(requirements, dict):
        requirements_dict = requirements
    else:
        requirements_dict = {
            "name": getattr(requirements, "name", ""),
            "description": getattr(requirements, "description", ""),
            "capabilities": getattr(requirements, "capabilities", []),
            "system_prompt": getattr(requirements, "system_prompt", ""),
            "required_tools": getattr(requirements, "required_tools", []),
            "memory_config": getattr(requirements, "memory_config", {}),
            "max_context_tokens": getattr(requirements, "max_context_tokens", 4000),
            "enable_tool_calling": getattr(requirements, "enable_tool_calling", True),
            "metadata": getattr(requirements, "metadata", {}),
        }

    envelope = codec.create_envelope(
        message_type="agent_requirements",
        schema_version=schema_version,
        data=requirements_dict,
    )

    return await codec.encode(envelope)


async def decode_agent_requirements(
    payload: bytes,
    codec: Optional[CodecSerializer] = None,
    target_version: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Decode bytes to AgentRequirements dictionary.

    Args:
        payload: Encoded bytes
        codec: CodecSerializer instance (creates default if not provided)
        target_version: Target schema version (migrates if different)

    Returns:
        Decoded requirements dictionary

    Example:
        >>> decoded = await decode_agent_requirements(encoded_bytes)
        >>> requirements = AgentRequirements(**decoded)
    """
    if codec is None:
        codec = create_codec_serializer()

    envelope = await codec.decode(payload)

    # Migrate if needed
    if target_version and envelope.get("schema_version") != target_version:
        envelope = codec.migrate_envelope(envelope, target_version, "agent_requirements")

    # Validate schema
    codec.validate_schema(envelope, "agent_requirements")

    return envelope["data"]


async def encode_tool_requirements(
    requirements: Any,
    codec: Optional[CodecSerializer] = None,
    schema_version: str = "1.0",
) -> bytes:
    """
    Encode ToolRequirements to bytes.

    Args:
        requirements: ToolRequirements instance or dictionary
        codec: CodecSerializer instance (creates default if not provided)
        schema_version: Schema version to use

    Returns:
        Encoded bytes

    Example:
        >>> from src.core.prompt_based_generator.prompt_interpreter import ToolRequirements
        >>> requirements = ToolRequirements(name="test", description="test", ...)
        >>> encoded = await encode_tool_requirements(requirements)
    """
    if codec is None:
        codec = create_codec_serializer()

    # Convert requirements to dictionary if it's a Pydantic model
    if hasattr(requirements, "model_dump"):
        requirements_dict = requirements.model_dump()
    elif hasattr(requirements, "dict"):
        requirements_dict = requirements.dict()
    elif isinstance(requirements, dict):
        requirements_dict = requirements
    else:
        requirements_dict = {
            "name": getattr(requirements, "name", ""),
            "description": getattr(requirements, "description", ""),
            "function_name": getattr(requirements, "function_name", ""),
            "parameters": getattr(requirements, "parameters", []),
            "return_type": getattr(requirements, "return_type", "Any"),
            "code_template": getattr(requirements, "code_template", None),
            "metadata": getattr(requirements, "metadata", {}),
        }

    envelope = codec.create_envelope(
        message_type="tool_requirements",
        schema_version=schema_version,
        data=requirements_dict,
    )

    return await codec.encode(envelope)


async def decode_tool_requirements(
    payload: bytes,
    codec: Optional[CodecSerializer] = None,
    target_version: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Decode bytes to ToolRequirements dictionary.

    Args:
        payload: Encoded bytes
        codec: CodecSerializer instance (creates default if not provided)
        target_version: Target schema version (migrates if different)

    Returns:
        Decoded requirements dictionary

    Example:
        >>> decoded = await decode_tool_requirements(encoded_bytes)
        >>> requirements = ToolRequirements(**decoded)
    """
    if codec is None:
        codec = create_codec_serializer()

    envelope = await codec.decode(payload)

    # Migrate if needed
    if target_version and envelope.get("schema_version") != target_version:
        envelope = codec.migrate_envelope(envelope, target_version, "tool_requirements")

    # Validate schema
    codec.validate_schema(envelope, "tool_requirements")

    return envelope["data"]


async def encode_prompt_template(
    template: Any,
    codec: Optional[CodecSerializer] = None,
    schema_version: str = "1.0",
) -> bytes:
    """
    Encode PromptTemplate to bytes.

    Args:
        template: PromptTemplate instance or dictionary
        codec: CodecSerializer instance (creates default if not provided)
        schema_version: Schema version to use

    Returns:
        Encoded bytes

    Example:
        >>> from src.core.prompt_context_management.prompt_manager import PromptTemplate
        >>> template = PromptTemplate(name="test", version="1.0", content="Hello {name}")
        >>> encoded = await encode_prompt_template(template)
    """
    if codec is None:
        codec = create_codec_serializer()

    # Convert template to dictionary
    if hasattr(template, "__dict__"):
        # For dataclass instances
        template_dict = {
            "name": template.name,
            "version": template.version,
            "content": template.content,
            "tenant_id": getattr(template, "tenant_id", None),
            "metadata": getattr(template, "metadata", {}),
        }
    elif isinstance(template, dict):
        template_dict = template
    else:
        template_dict = {
            "name": getattr(template, "name", ""),
            "version": getattr(template, "version", ""),
            "content": getattr(template, "content", ""),
            "tenant_id": getattr(template, "tenant_id", None),
            "metadata": getattr(template, "metadata", {}),
        }

    envelope = codec.create_envelope(
        message_type="prompt_template",
        schema_version=schema_version,
        data=template_dict,
    )

    return await codec.encode(envelope)


async def decode_prompt_template(
    payload: bytes,
    codec: Optional[CodecSerializer] = None,
    target_version: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Decode bytes to PromptTemplate dictionary.

    Args:
        payload: Encoded bytes
        codec: CodecSerializer instance (creates default if not provided)
        target_version: Target schema version (migrates if different)

    Returns:
        Decoded template dictionary

    Example:
        >>> decoded = await decode_prompt_template(encoded_bytes)
        >>> template = PromptTemplate(**decoded)
    """
    if codec is None:
        codec = create_codec_serializer()

    envelope = await codec.decode(payload)

    # Migrate if needed
    if target_version and envelope.get("schema_version") != target_version:
        envelope = codec.migrate_envelope(envelope, target_version, "prompt_template")

    # Validate schema
    codec.validate_schema(envelope, "prompt_template")

    return envelope["data"]

