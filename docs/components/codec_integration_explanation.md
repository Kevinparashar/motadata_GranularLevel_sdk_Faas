# CODEC Integration - Comprehensive Component Explanation

## Overview

The CODEC Integration component provides message encoding/decoding with schema versioning and validation, ensuring type-safe, versioned communication between AI SDK components through the CODEC serialization system from the Core SDK.

## Table of Contents

1. [CODEC Integration Overview](#codec-integration-overview)
2. [Integration Points](#integration-points)
3. [Message Encoding](#message-encoding)
4. [Message Decoding](#message-decoding)
5. [Schema Management](#schema-management)
6. [Versioning and Migration](#versioning-and-migration)
7. [Agent Framework Integration](#agent-framework-integration)
8. [LiteLLM Gateway Integration](#litellm-gateway-integration)
9. [RAG System Integration](#rag-system-integration)
10. [Validation](#validation)
11. [Workflow](#workflow)
12. [Customization](#customization)

---

## CODEC Integration Overview

### Purpose

CODEC integration enables:
- **Type-Safe Serialization**: Ensure data structure integrity
- **Schema Versioning**: Handle schema evolution gracefully
- **Message Validation**: Validate messages before processing
- **Backward Compatibility**: Support multiple schema versions
- **Performance**: Efficient encoding/decoding

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AI SDK Components                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Agent      │  │   Gateway    │  │     RAG      │     │
│  │  Framework   │  │              │  │   System     │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                  │              │
│         └─────────────────┼──────────────────┘              │
│                           │                                  │
│         ┌─────────────────┴──────────────────┐             │
│         │     CODEC Integration Layer         │             │
│         │  ┌──────────────────────────────┐   │             │
│         │  │  CODEC Serializer             │   │             │
│         │  │  Schema Manager               │   │             │
│         │  │  Version Migrator             │   │             │
│         │  │  (from Core SDK)              │   │             │
│         │  └──────────────────────────────┘   │             │
│         └─────────────────┬──────────────────┘             │
│                           │                                  │
└───────────────────────────┼──────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Schema Registry                                  │
│  (Core SDK - Schema definitions and versions)                │
└─────────────────────────────────────────────────────────────┘
```

---

## Integration Points

### Component Integration Matrix

| Component | Encoding | Decoding | Schemas Used |
|-----------|----------|----------|-------------|
| **Agent Framework** | Agent messages, tasks, memory items | Agent messages, task results | `agent_message`, `agent_task`, `memory_item` |
| **LiteLLM Gateway** | LLM requests, embedding requests | LLM responses, embedding responses | `llm_request`, `llm_response`, `embedding_request` |
| **RAG System** | Documents, queries | Query results, document status | `rag_document`, `rag_query`, `rag_result` |
| **LLMOps** | Operation logs | Operation queries | `llm_operation` |
| **MLOps** | Training jobs, predictions | Job status, prediction results | `ml_training_job`, `ml_prediction` |

---

## Message Encoding

### Creating an Envelope

```python
from src.integrations.codec_integration import CodecSerializer

codec = CodecSerializer()

# Create envelope
envelope = codec.create_envelope(
    message_type="agent_message",
    schema_version="1.0",
    data={
        "message_id": "msg_123",
        "source_agent_id": "agent_123",
        "target_agent_id": "agent_456",
        "content": "Test message",
        "message_type": "text",
        "timestamp": datetime.now().isoformat(),
        "metadata": {}
    }
)
```

### Encoding to Bytes

```python
# Encode envelope to bytes
encoded = codec.encode(envelope)

# Result: bytes ready for NATS transmission
assert isinstance(encoded, bytes)
```

### Complete Encoding Example

```python
def encode_agent_message(message: AgentMessage) -> bytes:
    """Encode agent message with CODEC."""
    # Create envelope
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
    
    # Encode to bytes
    return codec.encode(envelope)
```

---

## Message Decoding

### Decoding from Bytes

```python
# Decode bytes to envelope
envelope = codec.decode(payload)

# Extract data
data = envelope["data"]
```

### Decoding with Validation

```python
def decode_agent_message(payload: bytes) -> AgentMessage:
    """Decode agent message with validation."""
    # Decode envelope
    envelope = codec.decode(payload)
    
    # Check schema version
    if envelope["schema_version"] != "1.0":
        # Migrate to current version
        envelope = codec.migrate_envelope(envelope, target_version="1.0")
    
    # Validate schema
    is_valid = codec.validate_schema(envelope, schema_name="agent_message")
    if not is_valid:
        raise ValueError("Invalid schema")
    
    # Extract data
    data = envelope["data"]
    
    # Reconstruct object
    return AgentMessage(
        message_id=data["message_id"],
        source_agent_id=data["source_agent_id"],
        target_agent_id=data["target_agent_id"],
        content=data["content"],
        message_type=data["message_type"],
        timestamp=datetime.fromisoformat(data["timestamp"]),
        metadata=data["metadata"]
    )
```

---

## Schema Management

### Schema Definitions

#### Agent Message Schema (v1.0)

```json
{
  "schema_version": "1.0",
  "message_type": "agent_message",
  "data": {
    "message_id": "string",
    "source_agent_id": "string",
    "target_agent_id": "string",
    "content": "string",
    "message_type": "string",
    "timestamp": "datetime",
    "metadata": {}
  }
}
```

#### LLM Request Schema (v1.0)

```json
{
  "schema_version": "1.0",
  "message_type": "llm_request",
  "data": {
    "request_id": "string",
    "prompt": "string",
    "model": "string",
    "tenant_id": "string",
    "parameters": {
      "temperature": "float",
      "max_tokens": "integer"
    },
    "timestamp": "datetime"
  }
}
```

#### RAG Document Schema (v1.0)

```json
{
  "schema_version": "1.0",
  "message_type": "rag_document",
  "data": {
    "document_id": "string",
    "content": "string",
    "metadata": {},
    "chunks": [
      {
        "chunk_id": "string",
        "content": "string",
        "embedding": "array<float>",
        "metadata": {}
      }
    ],
    "tenant_id": "string",
    "timestamp": "datetime"
  }
}
```

### Schema Registration

```python
# Register schema (typically done at initialization)
codec.register_schema(
    schema_name="agent_message",
    version="1.0",
    schema_definition={
        "type": "object",
        "properties": {
            "message_id": {"type": "string"},
            "content": {"type": "string"},
            # ... more properties
        },
        "required": ["message_id", "content"]
    }
)
```

---

## Versioning and Migration

### Version Migration

```python
# Check version
if envelope["schema_version"] != current_version:
    # Migrate to current version
    migrated = codec.migrate_envelope(
        envelope,
        target_version=current_version
    )
    
    # Use migrated envelope
    envelope = migrated
```

### Migration Strategies

```python
# Migration function (defined in Core SDK)
def migrate_agent_message_v09_to_v10(old_envelope):
    """Migrate agent message from v0.9 to v1.0."""
    old_data = old_envelope["data"]
    
    # Transform data
    new_data = {
        "message_id": old_data["id"],  # Field renamed
        "source_agent_id": old_data["from"],
        "target_agent_id": old_data["to"],
        "content": old_data["text"],
        "message_type": old_data.get("type", "text"),
        "timestamp": old_data["time"],
        "metadata": old_data.get("meta", {})
    }
    
    return {
        "schema_version": "1.0",
        "message_type": "agent_message",
        "data": new_data
    }
```

---

## Agent Framework Integration

### Encoding Agent Messages

```python
async def send_message(self, target_agent_id: str, content: str):
    """Send message with CODEC encoding."""
    message = AgentMessage(
        message_id=str(uuid.uuid4()),
        source_agent_id=self.agent_id,
        target_agent_id=target_agent_id,
        content=content,
        message_type="text"
    )
    
    # Encode message
    encoded = codec.encode(codec.create_envelope(
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
    ))
    
    # Publish via NATS
    await nats_client.publish(
        subject=f"ai.agent.message.{self.tenant_id}",
        payload=encoded
    )
```

### Decoding Agent Messages

```python
async def receive_message(self, payload: bytes):
    """Receive and decode message."""
    # Decode envelope
    envelope = codec.decode(payload)
    
    # Validate and migrate if needed
    if envelope["schema_version"] != "1.0":
        envelope = codec.migrate_envelope(envelope, target_version="1.0")
    
    # Validate schema
    codec.validate_schema(envelope, schema_name="agent_message")
    
    # Extract data
    data = envelope["data"]
    
    # Reconstruct message
    message = AgentMessage(
        message_id=data["message_id"],
        source_agent_id=data["source_agent_id"],
        target_agent_id=data["target_agent_id"],
        content=data["content"],
        message_type=data["message_type"],
        timestamp=datetime.fromisoformat(data["timestamp"]),
        metadata=data["metadata"]
    )
    
    return message
```

---

## LiteLLM Gateway Integration

### Encoding LLM Requests

```python
async def generate_async(self, prompt: str, model: str, tenant_id: str):
    """Generate with CODEC encoding."""
    request_id = str(uuid.uuid4())
    
    # Create request envelope
    request_envelope = codec.create_envelope(
        message_type="llm_request",
        schema_version="1.0",
        data={
            "request_id": request_id,
            "prompt": prompt,
            "model": model,
            "tenant_id": tenant_id,
            "parameters": {
                "temperature": 0.7,
                "max_tokens": 1000
            },
            "timestamp": datetime.now().isoformat()
        }
    )
    
    # Encode
    encoded = codec.encode(request_envelope)
    
    # Publish via NATS
    await nats_client.publish(
        subject=f"ai.gateway.requests.{tenant_id}",
        payload=encoded
    )
```

### Decoding LLM Responses

```python
async def receive_response(self, payload: bytes):
    """Receive and decode LLM response."""
    # Decode envelope
    envelope = codec.decode(payload)
    
    # Validate schema
    codec.validate_schema(envelope, schema_name="llm_response")
    
    # Extract data
    data = envelope["data"]
    
    # Create response object
    response = GenerateResponse(
        text=data["response"],
        prompt_tokens=data["tokens"]["prompt"],
        completion_tokens=data["tokens"]["completion"],
        total_tokens=data["tokens"]["total"],
        cost=data["cost"],
        model=data["model"]
    )
    
    return response
```

---

## RAG System Integration

### Encoding Documents

```python
async def ingest_document_async(self, document: Document):
    """Ingest document with CODEC encoding."""
    # Process document into chunks
    chunks = await self.processor.process(document)
    
    # Create document envelope
    document_envelope = codec.create_envelope(
        message_type="rag_document",
        schema_version="1.0",
        data={
            "document_id": document.document_id,
            "content": document.content,
            "metadata": document.metadata,
            "chunks": [
                {
                    "chunk_id": chunk.chunk_id,
                    "content": chunk.content,
                    "embedding": chunk.embedding.tolist(),
                    "metadata": chunk.metadata
                }
                for chunk in chunks
            ],
            "tenant_id": document.tenant_id,
            "timestamp": datetime.now().isoformat()
        }
    )
    
    # Encode
    encoded = codec.encode(document_envelope)
    
    # Publish via NATS
    await nats_client.publish(
        subject=f"ai.rag.ingest.{document.tenant_id}",
        payload=encoded
    )
```

### Encoding Queries

```python
async def query_async(self, query: str, tenant_id: str):
    """Query with CODEC encoding."""
    query_id = str(uuid.uuid4())
    
    # Create query envelope
    query_envelope = codec.create_envelope(
        message_type="rag_query",
        schema_version="1.0",
        data={
            "query_id": query_id,
            "query": query,
            "tenant_id": tenant_id,
            "parameters": {
                "top_k": 5,
                "similarity_threshold": 0.7
            },
            "timestamp": datetime.now().isoformat()
        }
    )
    
    # Encode
    encoded = codec.encode(query_envelope)
    
    # Publish via NATS
    await nats_client.publish(
        subject=f"ai.rag.queries.{tenant_id}",
        payload=encoded
    )
```

---

## Validation

### Schema Validation

```python
# Validate envelope against schema
is_valid = codec.validate_schema(envelope, schema_name="agent_message")

if not is_valid:
    raise ValueError("Invalid schema")
```

### Validation with Error Details

```python
# Validate and get errors
validation_result = codec.validate_schema_detailed(
    envelope,
    schema_name="agent_message"
)

if not validation_result.is_valid:
    for error in validation_result.errors:
        print(f"Validation error: {error.field} - {error.message}")
```

### Required Fields Validation

```python
# Check required fields
required_fields = ["message_id", "content", "timestamp"]
for field in required_fields:
    if field not in envelope["data"]:
        raise ValueError(f"Missing required field: {field}")
```

---

## Workflow

### Complete Encoding/Decoding Flow

```
1. Component creates message object
   │
   ├─→ CODEC: Create envelope
   │
   ▼
2. CODEC: Encode to bytes
   │
   ├─→ Schema validation
   │
   ▼
3. NATS: Transmit bytes
   │
   ▼
4. Receiver receives bytes
   │
   ├─→ CODEC: Decode envelope
   │
   ├─→ Version check
   │   │
   │   ├─→ If version mismatch: Migrate
   │
   ├─→ Schema validation
   │
   ▼
5. Extract data from envelope
   │
   ▼
6. Reconstruct object
   │
   ▼
7. Process message
```

---

## Customization

### Custom Schema Definitions

```python
# Define custom schema
custom_schema = {
    "type": "object",
    "properties": {
        "custom_field": {"type": "string"},
        "custom_number": {"type": "number"}
    },
    "required": ["custom_field"]
}

codec.register_schema(
    schema_name="custom_message",
    version="1.0",
    schema_definition=custom_schema
)
```

### Custom Migration Functions

```python
# Register custom migration
codec.register_migration(
    from_version="0.9",
    to_version="1.0",
    message_type="agent_message",
    migration_function=migrate_v09_to_v10
)
```

---

## Best Practices

1. **Always use envelopes** for message structure
2. **Validate schemas** before encoding/decoding
3. **Handle version migration** gracefully
4. **Use meaningful schema versions** (semantic versioning)
5. **Document schema changes** when updating versions
6. **Test migrations** thoroughly before deployment
7. **Monitor validation failures** for schema issues
8. **Use type hints** in Python code for better validation

---

## See Also

- [CORE_COMPONENTS_INTEGRATION_STORY.md](../../CORE_COMPONENTS_INTEGRATION_STORY.md)
- [CODEC Integration Guide](../../docs/integration_guides/codec_integration_guide.md)
- Core SDK CODEC documentation

