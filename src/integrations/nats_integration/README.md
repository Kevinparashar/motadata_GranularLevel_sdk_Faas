# MOTADATA - NATS INTEGRATION

**Integration module providing asynchronous messaging capabilities between AI SDK components and the NATS messaging system.**

## Overview

This module provides integration between the AI SDK components and the NATS messaging system from the Core SDK.

## Purpose

NATS integration enables:
- Asynchronous messaging between AI components
- Agent-to-agent communication
- RAG document processing queues
- LLM request queuing
- Event-driven workflows

## Integration Points

### Agent Framework
- Agent-to-agent messaging via `ai.agent.message.{tenant_id}`
- Task distribution via `ai.agent.tasks.{tenant_id}`
- Memory updates via `ai.agent.memory.{tenant_id}`

### LiteLLM Gateway
- Request queuing via `ai.gateway.requests.{tenant_id}`
- Response delivery via `ai.gateway.responses.{tenant_id}`

### RAG System
- Document ingestion via `ai.rag.ingest.{tenant_id}`
- Query processing via `ai.rag.queries.{tenant_id}`

## Usage

See the integration guide: `docs/integration_guides/nats_integration_guide.md`

## Dependencies

- Core SDK NATS wrapper (versioned dependency)

