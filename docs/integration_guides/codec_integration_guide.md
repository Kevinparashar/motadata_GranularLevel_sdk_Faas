# CODEC Integration Guide

## Overview

This guide explains how to integrate CODEC message encoding/decoding with AI SDK components.

## Prerequisites

- Core SDK CODEC envelope and schema management (versioned dependency)
- Schema definitions registered
- Version migration utilities available

## Integration Points

### Message Encoding

#### Creating an Envelope

```python
# Create envelope
envelope = codec.create_envelope(
    message_type="agent_message",
    schema_version="1.0",
    data={
        "message_id": message_id,
        "content": content,
        "timestamp": timestamp.isoformat()
    }
)

# Encode to bytes
encoded = codec.encode(envelope)
```

### Message Decoding

#### Decoding with Validation

```python
# Decode from bytes
envelope = codec.decode(payload)

# Validate schema version
if envelope["schema_version"] != "1.0":
    # Handle version migration
    envelope = codec.migrate_envelope(envelope, target_version="1.0")

# Validate schema
codec.validate_schema(envelope, schema_name="agent_message")

# Extract data
data = envelope["data"]
```

### Agent Message Encoding

```python
# Encode agent message
def encode_agent_message(message: AgentMessage) -> bytes:
    envelope = codec.create_envelope(
        message_type="agent_message",
        schema_version="1.0",
        data={
            "message_id": message.message_id,
            "source_agent_id": message.source_agent_id,
            "target_agent_id": message.target_agent_id,
            "content": message.content,
            "message_type": message.message_type,
            "timestamp": message.timestamp.isoformat(),
            "metadata": message.metadata
        }
    )
    return codec.encode(envelope)
```

### Gateway Request/Response Encoding

```python
# Encode LLM request
request_envelope = codec.create_envelope(
    message_type="llm_request",
    schema_version="1.0",
    data={
        "request_id": request_id,
        "prompt": prompt,
        "model": model,
        "tenant_id": tenant_id,
        "timestamp": datetime.now().isoformat()
    }
)
encoded_request = codec.encode(request_envelope)

# Decode LLM response
response_envelope = codec.decode(encoded_response)
response_data = response_envelope["data"]
```

### RAG Document Encoding

```python
# Encode document
document_envelope = codec.create_envelope(
    message_type="rag_document",
    schema_version="1.0",
    data={
        "document_id": document_id,
        "content": content,
        "metadata": metadata,
        "chunks": [chunk.to_dict() for chunk in chunks],
        "tenant_id": tenant_id,
        "timestamp": datetime.now().isoformat()
    }
)
encoded_document = codec.encode(document_envelope)
```

## Schema Versioning

### Version Migration

```python
# Check version
if envelope["schema_version"] != current_version:
    # Migrate to current version
    migrated = codec.migrate_envelope(
        envelope,
        target_version=current_version
    )
```

### Schema Validation

```python
# Validate against schema
is_valid = codec.validate_schema(
    envelope,
    schema_name="agent_message"
)

if not is_valid:
    raise ValueError("Invalid schema")
```

## Performance Targets

- Agent message serialization: < 1ms P95
- RAG payload encoding: < 2ms P95
- Schema validation: < 0.5ms P95

## See Also

- [CORE_COMPONENTS_INTEGRATION_STORY.md](../../CORE_COMPONENTS_INTEGRATION_STORY.md)
- Core SDK CODEC documentation

