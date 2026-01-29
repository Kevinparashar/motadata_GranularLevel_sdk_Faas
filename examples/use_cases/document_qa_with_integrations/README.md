# Motadata Document Q&A Use Case with NATS, OTEL, and CODEC Integration

## Overview

This use case demonstrates a complete Document Q&A system using RAG, Agent Framework, and LiteLLM Gateway, with full integration of NATS, OTEL, and CODEC core components.

## Architecture

```
User Query
    │
    ▼
API Endpoint (Unified Query)
    │
    ├─→ OTEL: Start trace
    │
    ▼
RAG System
    │
    ├─→ NATS: Publish query to queue
    ├─→ CODEC: Encode query message
    ├─→ OTEL: Trace query processing
    │
    ▼
Document Retrieval
    │
    ├─→ NATS: Request embeddings via Gateway
    ├─→ CODEC: Encode/Decode embedding requests
    │
    ▼
Response Generation
    │
    ├─→ NATS: Request LLM generation
    ├─→ CODEC: Encode/Decode LLM requests
    ├─→ OTEL: Track tokens and costs
    │
    ▼
Return Response
    │
    ├─→ CODEC: Encode response
    ├─→ OTEL: End trace, record metrics
```

## Components Used

- **RAG System**: Document retrieval and context building
- **LiteLLM Gateway**: Embedding generation and LLM calls
- **Agent Framework**: Optional orchestration
- **NATS**: Asynchronous messaging and queuing
- **OTEL**: Distributed tracing and metrics
- **CODEC**: Message serialization

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
export NATS_URL=nats://localhost:4222
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export POSTGRES_HOST=localhost
export POSTGRES_DB=motadata_sdk
```

3. Run the example:
```bash
python main.py
```

## Integration Points

### NATS Topics Used
- `ai.rag.queries.{tenant_id}` - Query queue
- `ai.rag.results.{tenant_id}` - Results delivery
- `ai.gateway.requests.{tenant_id}` - LLM requests
- `ai.gateway.responses.{tenant_id}` - LLM responses

### OTEL Spans
- `use_case.document_qa` - Root trace
- `rag.query.process` - Query processing
- `rag.embedding.generate` - Embedding generation
- `rag.vector.search` - Vector search
- `rag.response.generate` - Response generation

### CODEC Schemas
- `rag_query` - Query encoding
- `rag_result` - Result encoding
- `llm_request` - LLM request encoding
- `llm_response` - LLM response encoding

## See Also

- [CORE_COMPONENTS_INTEGRATION_STORY.md](../../../CORE_COMPONENTS_INTEGRATION_STORY.md)
- [Integration Guides](../../../docs/integration_guides/)

