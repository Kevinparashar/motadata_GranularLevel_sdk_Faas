"""
Integration layer for FaaS services.

Provides integrations for:
- NATS: Message bus for service-to-service communication
- OTEL: OpenTelemetry for observability
- CODEC: Message serialization/deserialization
"""

from .codec import CodecManager, create_codec_manager
from .nats import NATSClient, create_nats_client
from .otel import OTELTracer, create_otel_tracer

__all__ = [
    # NATS
    "NATSClient",
    "create_nats_client",
    # OTEL
    "OTELTracer",
    "create_otel_tracer",
    # CODEC
    "CodecManager",
    "create_codec_manager",
]
