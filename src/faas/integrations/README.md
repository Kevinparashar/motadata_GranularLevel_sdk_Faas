# MOTADATA - INTEGRATION LAYER

**Standardized integrations for NATS, OpenTelemetry (OTEL), and CODEC across all FaaS services.**

## Overview

The integration layer provides standardized integrations for NATS, OpenTelemetry (OTEL), and CODEC across all FaaS services.

## NATS Integration

### Purpose
- Service-to-service messaging
- Event streaming
- Async communication

### Usage

```python
from src.faas.integrations import create_nats_client

# Create NATS client
nats_client = create_nats_client()

# Connect
await nats_client.connect()

# Publish message
await nats_client.publish(
    subject="gateway.generate.request",
    payload=codec_manager.encode({"prompt": "Hello"})
)

# Subscribe to messages
async def handle_message(msg):
    data = codec_manager.decode(msg.data)
    # Process message

await nats_client.subscribe(
    subject="gateway.generate.response",
    callback=handle_message
)
```

### Placeholder Status
Currently implemented as placeholder. Replace with actual NATS client when integration is complete.

## OpenTelemetry (OTEL) Integration

### Purpose
- Distributed tracing
- Metrics collection
- Logging correlation

### Usage

```python
from src.faas.integrations import create_otel_tracer

# Create tracer
tracer = create_otel_tracer(service_name="agent-service")

# Start span
with tracer.start_span("execute_task") as span:
    span.set_attribute("agent.id", agent_id)
    span.set_attribute("task.type", task_type)
    
    # Execute task
    result = await agent.execute_task(task)
    
    span.add_event("task.completed", {"result": "success"})
```

### Placeholder Status
Currently implemented as placeholder. Replace with actual OTEL SDK when integration is complete.

## CODEC Integration

### Purpose
- Message serialization/deserialization
- Efficient data encoding
- Support for multiple formats (JSON, MessagePack, Protobuf)

### Usage

```python
from src.faas.integrations import create_codec_manager

# Create codec manager
codec_manager = create_codec_manager(codec_type="json")

# Encode data
data = {"message": "Hello", "user_id": "user_123"}
encoded = codec_manager.encode(data)  # bytes

# Decode data
decoded = codec_manager.decode(encoded)  # dict
```

### Supported Formats
- **JSON**: Default, human-readable
- **MessagePack**: Compact binary format (placeholder)
- **Protobuf**: Efficient binary format (placeholder)

### Placeholder Status
JSON encoding/decoding is fully implemented. MessagePack and Protobuf are placeholders.

## Configuration

Enable integrations via environment variables:

```bash
# NATS
ENABLE_NATS=true
NATS_URL=nats://localhost:4222

# OTEL
ENABLE_OTEL=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# CODEC
ENABLE_CODEC=true
CODEC_TYPE=json  # or msgpack, protobuf
```

## Integration in Services

All services can use integrations:

```python
from src.faas.integrations import create_nats_client, create_otel_tracer, create_codec_manager

class MyService:
    def __init__(self, config):
        self.nats_client = create_nats_client() if config.enable_nats else None
        self.otel_tracer = create_otel_tracer(config.service_name) if config.enable_otel else None
        self.codec_manager = create_codec_manager()
```

## Next Steps

1. **NATS**: Implement actual NATS client using `nats-py` library
2. **OTEL**: Implement actual OTEL SDK integration
3. **CODEC**: Implement MessagePack and Protobuf codecs

