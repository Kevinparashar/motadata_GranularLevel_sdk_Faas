# OpenTelemetry (OTEL) Implementation Structure for motadata-python-ai-sdk

## Project Structure with OTEL Integration Points

    /project-root
    │
    ├── /src
    │   ├── /faas
    │   │   ├── /integrations
    │   │   │   ├── otel.py                    # OTEL bootstrap (provider/exporter/tracer)
    │   │   │   └── nats.py                    # Context propagation (inject/extract)
    │   │   │
    │   │   ├── /shared
    │   │   │   ├── middleware.py              # Trace context + request correlation
    │   │   │   ├── http_client.py             # Outbound HTTP spans
    │   │   │   └── database.py                # DB instrumentation hook
    │   │   │
    │   │   └── /services
    │   │       ├── /agent_service/service.py
    │   │       ├── /rag_service/service.py
    │   │       ├── /cache_service/service.py
    │   │       ├── /llmops_service/service.py
    │   │       ├── /data_ingestion_service/service.py
    │   │       ├── /prompt_service/service.py
    │   │       ├── /prompt_generator_service/service.py
    │   │       ├── /gateway_service/service.py
    │   │       └── /ml_service/service.py
    │   │
    │   └── /core
    │       ├── /agno_agent_framework
    │       │   ├── agent.py                   # agent.run lifecycle span
    │       │   ├── orchestration.py           # plan -> tool_exec -> finalize spans
    │       │   ├── tools.py                   # tool execution boundary
    │       │   ├── memory.py                  # memory retrieval boundary
    │       │   └── session.py
    │       │
    │       ├── /rag
    │       │   ├── rag_system.py              # rag.run span
    │       │   ├── retriever.py               # retrieval stage span
    │       │   ├── document_processor.py      # processing stage span
    │       │   ├── multimodal_loader.py       # loading stage span
    │       │   ├── generator.py               # generation stage span
    │       │   └── hallucination_detector.py  # guardrail/verification span
    │       │
    │       ├── /litellm_gateway
    │       │   ├── gateway.py                 # llm.call boundary span
    │       │   ├── rate_limiter.py
    │       │   └── kv_cache.py
    │       │
    │       ├── /postgresql_database
    │       │   ├── connection.py              # DB connection boundary
    │       │   ├── vector_operations.py
    │       │   └── vector_index_manager.py
    │       │
    │       ├── /cache_mechanism
    │       │   ├── cache.py                   # cache get/set/invalidate spans
    │       │   └── cache_enhancements.py
    │       │
    │       ├── /data_ingestion
    │       │   ├── ingestion_service.py       # ingest pipeline span
    │       │   ├── data_cleaner.py
    │       │   └── data_validator.py
    │       │
    │       └── /llmops
    │           └── llmops.py
    │
    ├── /tests
    │   └── (OTEL validation only in integration tests if required)
    │
    └── /docs
        └── OTEL-Implementation.md

------------------------------------------------------------------------

## Implementation Guidelines

### Where OTEL MUST exist

-   Service entrypoints
-   HTTP client boundaries
-   Database connections
-   Cache boundaries
-   LLM gateway calls
-   Agent orchestration stages
-   RAG pipeline stages
-   Messaging boundaries (NATS)

### Where OTEL MUST NOT exist

-   Utility functions
-   Constants
-   Exceptions
-   DTOs / models
-   Small helper methods

------------------------------------------------------------------------

## Span Strategy

### Agents

-   agent.run
-   agent.plan
-   agent.tool_exec
-   agent.memory
-   agent.finalize

### RAG

-   rag.run
-   rag.retrieve
-   rag.process
-   rag.generate
-   rag.verify

### LLM Gateway

-   llm.call (with provider + model attributes)

### Data Ingestion

-   ingest.run
-   ingest.clean
-   ingest.validate
-   ingest.store

------------------------------------------------------------------------

## Observability Principle

Instrument boundaries and orchestration layers --- not every function.\
Focus on high-value spans that provide actionable diagnostics.
