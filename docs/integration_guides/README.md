# Integration Guides

This directory contains integration guides for core platform components (NATS, OTEL, CODEC) with the AI SDK.

## Available Guides

1. **[NATS Integration Guide](nats_integration_guide.md)**
   - NATS messaging integration
   - Pub/Sub topics and channels
   - Integration patterns for each AI component

2. **[OTEL Integration Guide](otel_integration_guide.md)**
   - OpenTelemetry observability integration
   - Distributed tracing
   - Metrics collection
   - Logging integration

3. **[CODEC Integration Guide](codec_integration_guide.md)**
   - Message encoding/decoding
   - Schema versioning
   - Validation patterns

## Related Documentation

- [CORE_COMPONENTS_INTEGRATION_STORY.md](../components/CORE_COMPONENTS_INTEGRATION_STORY.md) - Complete integration story and architecture
- Component-specific README files in `src/core/` directories
- [FaaS Integrations](../src/faas/integrations/README.md) - NATS, OTEL, CODEC for FaaS services
- [FaaS Implementation Guide](../architecture/FAAS_IMPLEMENTATION_GUIDE.md) - FaaS architecture with integrations

