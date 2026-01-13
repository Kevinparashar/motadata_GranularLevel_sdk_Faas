# OTEL Integration

## Overview

This module provides integration between the AI SDK components and the OpenTelemetry observability system from the Core SDK.

## Purpose

OTEL integration enables:
- Distributed tracing across AI components
- Metrics collection for performance monitoring
- Structured logging
- Cost and token usage tracking
- Error tracking and monitoring

## Integration Points

### All AI Components
- Distributed tracing for all operations
- Metrics collection for performance
- Error tracking and logging

### LiteLLM Gateway
- LLM call tracing
- Token usage and cost metrics
- Provider health monitoring

### RAG System
- Query latency tracking
- Retrieval performance metrics
- Document ingestion monitoring

### Agent Framework
- Task execution tracing
- Memory operation metrics
- Tool execution tracking

## Usage

See the integration guide: `docs/integration_guides/otel_integration_guide.md`

## Dependencies

- Core SDK OTEL bootstrap and propagation (versioned dependency)

