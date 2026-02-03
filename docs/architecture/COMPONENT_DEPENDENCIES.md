# MOTADATA - COMPONENT DEPENDENCIES

This document gives a quick view of which SDK components depend on which other components.

## Dependency rules (simple)

- **Gateway** is the common dependency for all LLM calls.
- **RAG** depends on **Database** (vector storage) and **Gateway** (embeddings/generation).
- **Agents** can depend on **Gateway**, and optionally **RAG** and **Cache**.
- **Cache** is optional and can be plugged into most components.
- **Observability** can wrap all components.

## Practical dependency matrix

| Component | Depends on | Optional dependencies |
|----------|------------|-----------------------|
| LiteLLM Gateway | Provider credentials | Cache, LLMOps, rate limiter |
| PostgreSQL Database | Postgres instance | pgvector indexes |
| Cache Mechanism | (none) | Dragonfly/Redis backend |
| RAG System | Database, Gateway | Cache, Memory, Hallucination detector |
| Agent Framework | (none) | Gateway, Memory, Tools, RAG |
| Data Ingestion | (none) | RAG, Cache, Gateway, Database |
| FaaS Services | Core SDK components | NATS, OTEL, CODEC |


