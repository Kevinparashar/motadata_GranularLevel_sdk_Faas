# MOTADATA - CORE COMPONENTS INTEGRATION STORY

This document explains **how the main SDK components work together** in a typical SaaS flow.

## What this story covers

- How a request flows through **Gateway → Agents → RAG → Cache → Observability**
- Where **tenant isolation** is applied (`tenant_id`)
- Where to look in the code when you are debugging or extending the SDK

## The common end-to-end flow

### 1) User request comes in

Your application (or FaaS service) receives a request, and extracts:

- `tenant_id` (mandatory for multi-tenant isolation)
- `user_id` (optional, for audit/personalization)
- input payload (prompt / document / query / task)

### 2) Gateway does the LLM work

The **LiteLLM Gateway** is the main entry point for model calls:

- text generation
- embeddings
- optional streaming

It is also the right place for:

- rate limiting
- caching (when enabled)
- LLMOps logging (when enabled)

### 3) Cache reduces latency and cost

The **Cache Mechanism** stores frequently repeated outputs (like embeddings or model responses).

- cache hits reduce response time
- cache hits reduce LLM cost (no repeat API call)

### 4) RAG adds knowledge context

The **RAG System** is used when you need answers from documents:

- ingest documents
- chunk + embed
- retrieve top matches
- generate final answer using retrieved context

### 5) Agents orchestrate tasks and tools

The **Agent Framework** is used when you need orchestration:

- tool usage
- multi-step workflows
- memory (conversation context)

### 6) Observability helps in production

Observability (OTEL + logs + metrics) helps you answer:

- why a request failed
- where time was spent
- how much LLM cost was incurred

## Code pointers

- Core SDK code: `src/core/`
- FaaS services: `src/faas/services/`
- Integrations (NATS/OTEL/CODEC): `src/faas/integrations/` and `src/integrations/`


