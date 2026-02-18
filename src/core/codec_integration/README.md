# MOTADATA - CODEC INTEGRATION

**Message encoding/decoding with schema versioning and validation for type-safe communication between AI SDK components.**

## Overview

The CODEC Integration module provides message serialization/deserialization with schema versioning, validation, and migration support. It enables type-safe, versioned communication between AI SDK components through NATS or other messaging systems.

## Features

- **Schema Management**: Register and validate message schemas
- **Version Migration**: Automatic schema version migration for backward compatibility
- **Multiple Codec Types**: Support for JSON (with msgpack/protobuf planned)
- **Type Safety**: Schema validation ensures data structure integrity
- **Component Integration**: Helper functions for Agent, Gateway, and RAG components

## Quick Start

```python
from src.core.codec_integration import create_codec_serializer, encode_agent_message

# Create codec serializer
codec = create_codec_serializer(codec_type="json")

# Create envelope
envelope = codec.create_envelope(
    message_type="agent_message",
    schema_version="1.0",
    data={"message_id": "msg_123", "content": "Hello"}
)

# Encode to bytes
encoded = await codec.encode(envelope)

# Decode from bytes
decoded = await codec.decode(encoded)
```

## Component Integration

### Agent Framework

```python
from src.core.codec_integration import encode_agent_message, decode_agent_message
from src.core.agno_agent_framework import AgentMessage

# Encode agent message
message = AgentMessage(from_agent="a1", to_agent="a2", content="Hello")
encoded = await encode_agent_message(message)

# Decode agent message
decoded = await decode_agent_message(encoded)
```

### LiteLLM Gateway

```python
from src.core.codec_integration import encode_llm_request, decode_llm_response

# Encode LLM request
encoded = await encode_llm_request(
    request_id="req_123",
    prompt="Hello",
    model="gpt-4",
    tenant_id="tenant_123"
)

# Decode LLM response
decoded = await decode_llm_response(encoded)
```

### RAG System

```python
from src.core.codec_integration import encode_rag_document, decode_rag_query

# Encode RAG document
encoded = await encode_rag_document(
    document_id="doc_123",
    content="Document content",
    tenant_id="tenant_123"
)

# Decode RAG query
decoded = await decode_rag_query(encoded)
```

## Schema Management

### Registering Schemas

```python
codec.register_schema(
    schema_name="custom_message",
    version="1.0",
    schema_definition={
        "type": "object",
        "required": ["field1", "field2"],
        "properties": {
            "field1": {"type": "string"},
            "field2": {"type": "number"}
        }
    },
    is_default=True
)
```

### Schema Validation

```python
# Validate envelope
is_valid = codec.validate_schema(envelope, schema_name="agent_message")
```

## Version Migration

### Registering Migrations

```python
def migrate_v09_to_v10(old_envelope: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate from v0.9 to v1.0."""
    old_data = old_envelope["data"]
    return {
        "schema_version": "1.0",
        "message_type": "agent_message",
        "data": {
            "message_id": old_data["id"],
            "content": old_data["text"],
            # ... transform other fields
        }
    }

codec.register_migration(
    schema_name="agent_message",
    from_version="0.9",
    to_version="1.0",
    migration_function=migrate_v09_to_v10
)
```

### Automatic Migration

```python
# Decode with automatic migration
envelope = await codec.decode(payload)
if envelope["schema_version"] != "1.0":
    envelope = codec.migrate_envelope(envelope, target_version="1.0")
```

## Error Handling

```python
from src.core.codec_integration.exceptions import (
    CodecEncodingError,
    CodecDecodingError,
    SchemaValidationError,
    MigrationError
)

try:
    encoded = await codec.encode(envelope)
except CodecEncodingError as e:
    print(f"Encoding failed: {e.message}")
    print(f"Message type: {e.message_type}")
```

## See Also

- [CODEC Integration Guide](../../docs/integration_guides/codec_integration_guide.md)
- [CODEC Integration Explanation](../../docs/components/codec_integration_explanation.md)

