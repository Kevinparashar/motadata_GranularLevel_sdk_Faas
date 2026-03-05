# AI Architecture — Diagrams and Flow

Diagrams and short flow explanations for the ITSM SaaS AI Engine (from AI_ARCHITECTURE.md).

---

## 1. Big picture: where AI lives

### Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    E N D   U S E R S                                    │
│                                                                                         │
│   ITSM Portal (agents, tickets, KB)  ·  Mobile App  ·  REST / API clients               │
└─────────────────────────────────────────────┬─────────────────────────────────────────┘
                                              │
                                              │  HTTPS  ·  JWT in Authorization header
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              A W S   A P I   G A T E W A Y                              │
│                                                                                         │
│   · Validate JWT signature and expiry                                                  │
│   · Extract tenant_id, user_id from claims  →  Inject X-Tenant-ID, X-User-ID          │
│   · Rate limiting (per tenant / per user)                                              │
│   · TLS termination  ·  Request validation  ·  Route to AI Engine                       │
└─────────────────────────────────────────────┬─────────────────────────────────────────┘
                                              │
                                              │  X-Tenant-ID  ·  X-User-ID  ·  X-Correlation-ID  ·  X-Request-ID
                                              ▼
╔═════════════════════════════════════════════════════════════════════════════════════════╗
║                                    A I   E N G I N E                                    ║
║                         (All AI services run here — multi-tenant, secure)                ║
╠═════════════════════════════════════════════════════════════════════════════════════════╣
║  LAYER 1 — REQUEST HANDLING                                                             ║
║  ┌─────────────────────────────────────────────────────────────────────────────────┐   ║
║  │  Auth Middleware      →  Validate X-Tenant-ID present (reject if missing)       │   ║
║  │  Logging Middleware   →  Log request/response, timing, tenant, correlation_id    │   ║
║  │  Error Handler        →  Map exceptions to standard JSON error response          │   ║
║  │  OTEL                 →  Start root trace span, set tenant in baggage           │   ║
║  └─────────────────────────────────────────────────────────────────────────────────┘   ║
║                                                                                         ║
║  LAYER 2 — ORCHESTRATION                                                                ║
║  ┌─────────────────────────────────────────────────────────────────────────────────┐   ║
║  │  Query Router        →  Classify intent (e.g. "summarize ticket", "chat", "RAG") │   ║
║  │  Service Selector    →  Map intent to target service + endpoint + payload        │   ║
║  │  Unified Cache       →  Check cache first (query / conversation / semantic)    │   ║
║  │  Service HTTP Client →  Call target service with retry + circuit breaker         │   ║
║  └─────────────────────────────────────────────────────────────────────────────────┘   ║
║                                                                                         ║
║  LAYER 3 — AI SERVICES (each is a stateless API)                                        ║
║  ┌────────────┬────────────┬────────────┬────────────┬────────────┬────────────┐       ║
║  │  Agent     │  RAG       │  ML        │  Cache     │  Prompt    │  Data      │       ║
║  │  Service   │  Service   │  Service   │  Service   │  Service   │  Ingestion │       ║
║  │            │            │            │            │            │  Service   │       ║
║  │  CRUD,     │  Ingest,   │  Train,    │  Get, Set,  │  Templates,│  Upload,   │       ║
║  │  execute,  │  query,    │  predict,  │  Invalidate│  render,   │  parse,    │       ║
║  │  chat,     │  search,   │  deploy,   │  (tenant-  │  context   │  auto-     │       ║
║  │  memory    │  manage    │  monitor   │   scoped)  │  window    │  pipeline  │       ║
║  └────────────┴────────────┴────────────┴────────────┴────────────┴────────────┘       ║
║  ┌────────────┬────────────┐                                                            ║
║  │  Prompt    │  LLMOps    │  + Validation (PII, guardrails)  ·  Feedback Loop        ║
║  │  Generator │  Service   │  + Observability (OTEL spans/metrics across all layers)   ║
║  │  Service   │  (log,     │                                                            ║
║  │  (agents/  │  cost,     │                                                            ║
║  │  tools     │  tokens,   │                                                            ║
║  │  from      │  metrics)  │                                                            ║
║  │  prompts)  │            │                                                            ║
║  └────────────┴────────────┘                                                            ║
║                                                                                         ║
║  LAYER 4 — CORE BUSINESS LOGIC (no direct DB; receives dependencies via injection)      ║
║  ┌─────────────────────────────────────────────────────────────────────────────────┐   ║
║  │  Agent Framework  ·  RAG System (Retriever, Generator, DocProcessor)            │   ║
║  │  Cache Mechanism  ·  Prompt Context Manager  ·  Validation & Guardrails         │   ║
║  │  LLMOps  ·  Feedback Loop  ·  Prompt Generator (AgentGen, ToolGen)               │   ║
║  │  ML Framework (Trainer, Predictor, MLOps pipeline)  ·  Data Ingestion pipeline   │   ║
║  └─────────────────────────────────────────────────────────────────────────────────┘   ║
║                                                                                         ║
║  LAYER 5 — DATA ACCESS (every query filtered by tenant_id)                              ║
║  ┌─────────────────────────────────────────────────────────────────────────────────┐   ║
║  │  AgentDAL · SessionDAL · MemoryDAL · DocumentDAL · EmbeddingDAL · PromptTemplateDAL│   ║
║  │  LLMOpsDAL · GatewayReqHistoryDAL · RAGQueryHistoryDAL · TenantCtxDAL · ...       │   ║
║  └─────────────────────────────────────────────────────────────────────────────────┘   ║
║                                                                                         ║
║  CROSS-CUTTING  │  OTEL (tracing, metrics, tenant in spans)  ·  CODEC (versioned msgs)  ║
║                 │  NATS (publish events: agent.created, rag.ingested, ticket.summarized)║
╚═════════════════╪═════════════════════════════════════════════════════════════════════╝
                  │
        ┌─────────┼─────────┬─────────────────────────┬─────────────────────────┐
        │         │         │                         │                         │
        ▼         ▼         ▼                         ▼                         ▼
┌───────────────┐ ┌───────────────────────────────┐ ┌─────────────────────────────────────┐
│  AI GATEWAY   │ │  D A T A B A S E              │ │  S O U R C E                         │
│  (LLM)        │ │                               │ │                                       │
│               │ │  PostgreSQL + pgvector       │ │  Dragonfly (distributed cache)       │
│  · One        │ │  · Tickets, conversations    │ │  · Response cache, embedding cache,  │
│    interface  │ │  · KB documents, versions     │ │    query cache (tenant-scoped keys)  │
│    to all     │ │  · Embeddings (vector store) │ │  OTEL Collector (traces, metrics)     │
│    LLM        │ │  · Prompts, agents, sessions │ │  NATS Server (event bus, pub/sub)      │
│    providers  │ │  · LLM ops log, audit tables │ │                                       │
│  · Rate       │ │  · All tables tenant-scoped  │ │                                       │
│    limit,     │ │  · Connection pool (asyncpg)│ │                                       │
│    retry,     │ │  · Vector indexes (IVFFlat, │ │                                       │
│    circuit    │ │    HNSW) for similarity      │ │                                       │
│    breaker    │ │                               │ │                                       │
│  · OpenAI,    │ │                               │ │                                       │
│    Anthropic, │ │                               │ │                                       │
│    Google,    │ │                               │ │                                       │
│    etc.       │ │                               │ │                                       │
└───────────────┘ └───────────────────────────────┘ └─────────────────────────────────────┘
```

### Flow explanation (big picture)

1. **Users** (ITSM Portal, mobile, REST clients) send **HTTPS** requests with **JWT**.  
2. **AWS API Gateway** validates JWT, extracts tenant/user, injects **X-Tenant-ID**, **X-User-ID**, **X-Correlation-ID**, **X-Request-ID**, and routes to the **AI Engine**.  
3. **AI Engine** processes the request in layers:  
   - **Layer 1** — Auth (reject if no tenant), logging, error mapping, OTEL root span.  
   - **Layer 2** — Query Router (intent), Service Selector (which service), Unified Cache (return if hit), then Service HTTP Client calls the chosen service.  
   - **Layer 3** — One of Agent, RAG, Prompt, Cache, ML, Data Ingestion, LLMOps, or Prompt Generator runs the request; each uses **Layer 4** (frameworks) and **Layer 5** (DALs).  
   - **Layer 4** — Agent Framework, RAG System, Prompt Context Manager, Validation, etc.; no direct DB; they receive DALs and gateway via injection.  
   - **Layer 5** — DALs talk only to the **Database** (PostgreSQL + pgvector); every query is tenant-scoped.  
4. **AI Gateway (LLM)** is called by the engine for generation/embeddings; it is the single interface to OpenAI, Anthropic, Google (rate limit, retry, circuit breaker).  
5. **Database** holds tickets, conversations, KB, embeddings, prompts, sessions, LLM ops log. **Source** is Dragonfly (cache), OTEL (traces/metrics), NATS (events).  
6. **Cross-cutting:** OTEL for tracing/metrics, CODEC for versioned messages, NATS for events (e.g. `ticket.summarized`).

**Data flow (summary):** Request → API Gateway → Engine (L1 → L2 → L3 → L4/L5 / Gateway) → Database or Source → response back. All steps are tenant-scoped and auditable.

---

## 2. Ticket summarization: end-to-end

**Scenario:** Support agent in ITSM portal clicks **Summarize ticket** for ticket TKT-5432.

### Diagram

```
┌─────────────┐     ┌──────────────────────────────────────────────────────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│   USER      │     │                    A I   E N G I N E                             │     │  AI GATEWAY     │     │  DATABASE /       │
│ (ITSM       │     │                                                                  │     │  (LLM)          │     │  SOURCE          │
│  Portal)    │     │                                                                  │     │                 │     │                  │
└──────┬──────┘     └──────────────────────────────────────────────────────────────────┘     └────────┬────────┘     └────────┬─────────┘
       │                                                                                              │                       │
       │  POST /summarize-ticket  │  Bearer JWT  │  Body: { ticket_id: "TKT-5432" }                  │                       │
       │─────────────────────────►│              │                                                    │                       │
       │                          │              │                                                    │                       │
       │                          │  STEP 1 — Middleware                                              │                       │
       │                          │  · Auth: validate X-Tenant-ID (e.g. tenant_acme)                │                       │
       │                          │  · Log: request path, tenant, correlation_id                      │                       │
       │                          │  · OTEL: start root span "ticket.summarize", set tenant baggage  │                       │
       │                          │              │                                                    │                       │
       │                          │  STEP 2 — Orchestrator                                            │                       │
       │                          │  · QueryRouter: "summarize ticket" → intent = AGENT_TASK         │                       │
       │                          │  · ServiceSelector: route to Agent Service /execute              │                       │
       │                          │  · Unified Cache: key = tenant_acme:summarize:TKT-5432           │                       │
       │                          │              │──────────────────────────────────────────────────────────────────────────►│  Check cache
       │                          │              │◄──────────────────────────────────────────────────────────────────────────│  Cache MISS
       │                          │              │                                                    │                       │
       │                          │  STEP 3 — Agent Service: get ticket data                          │                       │
       │                          │  · SessionDAL.get_messages(tenant_acme, ticket_id=TKT-5432)      │                       │
       │                          │              │──────────────────────────────────────────────────►│                       │  session_messages
       │                          │              │◄──────────────────────────────────────────────────│                       │  47 messages
       │                          │  · MemoryDAL.get_memory(tenant_acme, agent=summarizer)           │                       │
       │                          │              │──────────────────────────────────────────────────►│                       │  agent_memory
       │                          │              │◄──────────────────────────────────────────────────│                       │  prior context
       │                          │              │                                                    │                       │
       │                          │  STEP 4 — RAG Service: get relevant KB                            │                       │
       │                          │  · Retriever: query = "ticket TKT-5432 network issue summary"    │                       │
       │                          │  · Vector search (pgvector): similarity_search, top_k=5         │                       │
       │                          │              │──────────────────────────────────────────────────►│                       │  embeddings
       │                          │  · Keyword search (DocumentDAL): "network issue", tenant_acme   │                       │  documents
       │                          │              │──────────────────────────────────────────────────►│                       │
       │                          │              │◄──────────────────────────────────────────────────│                       │  5 relevant docs
       │                          │  · Merge + re-rank results  · OTEL: record retrieval metrics    │                       │
       │                          │              │                                                    │                       │
       │                          │  STEP 5 — Prompt assembly                                         │                       │
       │                          │  · PromptContextManager: get_template("ticket_summarization")    │                       │
       │                          │              │──────────────────────────────────────────────────►│                       │  prompt_templates
       │                          │              │◄──────────────────────────────────────────────────│                       │
       │                          │  · Assemble: [System] + [KB context] + [47 messages] + [Memory] + "Summarize..."        │
       │                          │  · ContextWindowManager: estimate tokens, truncate if needed     │                       │
       │                          │              │                                                    │                       │
       │                          │  STEP 6 — Call LLM                                                 │                       │
       │                          │  · gateway.generate_async(prompt=assembled, model="gpt-4")       │                       │
       │                          │              │──────────────────────────────────────────────────►│  Rate limit,         │
       │                          │              │                                                    │  dedup, circuit       │
       │                          │              │                                                    │  breaker → OpenAI     │
       │                          │              │◄──────────────────────────────────────────────────│  Summary text,       │
       │                          │              │                                                    │  tokens, cost         │
       │                          │              │                                                    │                       │
       │                          │  STEP 7 — Validate & log                                           │                       │
       │                          │  · ValidationManager: PII filter, secret detect, ITSM compliance │                       │
       │                          │  · LLMOps: log model, tokens_in, tokens_out, cost, tenant, latency│                       │
       │                          │              │──────────────────────────────────────────────────►│                       │  llm_operations
       │                          │              │                                                    │                       │
       │                          │  STEP 8 — Cache result & update memory                              │                       │
       │                          │  · CacheMechanism.set(tenant_acme:summarize:TKT-5432, summary, TTL)│                       │
       │                          │              │──────────────────────────────────────────────────►│  Dragonfly
       │                          │  · MemoryDAL.save(tenant_acme, summarizer_agent, context)         │                       │
       │                          │              │──────────────────────────────────────────────────►│  agent_memory
       │                          │              │                                                    │                       │
       │                          │  STEP 9 — Events & close-out                                       │                       │
       │                          │  · CODEC: encode event  · NATS: publish "ticket.summarized"        │                       │
       │                          │  · FeedbackLoop: register hook (agent can rate summary)           │                       │
       │                          │  · OTEL: end spans, export traces/metrics                         │                       │
       │                          │              │                                                    │                       │
       │  Response:               │              │                                                    │                       │
       │  { summary, tokens_used, │              │                                                    │                       │
       │    model, cached: false } │              │                                                    │                       │
       │◄─────────────────────────│              │                                                    │                       │
       │                          │              │                                                    │                       │
```

### Flow explanation (ticket summarization)

| Step | What happens | Who is used |
|------|----------------|-------------|
| **1** | Request hits engine. Middleware validates **X-Tenant-ID** (e.g. tenant_acme), logs path/tenant/correlation_id, starts OTEL span `ticket.summarize` and sets tenant in baggage. | Layer 1 |
| **2** | Orchestrator derives intent “summarize ticket”, selects Agent Service `/execute`, builds cache key `tenant_acme:summarize:TKT-5432` and checks cache (Dragonfly). On **cache miss**, proceeds. | Layer 2, Source (cache) |
| **3** | Agent Service loads ticket conversation and prior context: **SessionDAL** (47 messages), **MemoryDAL** (summarizer agent memory). All by tenant. | Layer 3/5, Database |
| **4** | RAG retrieves relevant KB: vector search (pgvector, top_k=5) and **DocumentDAL** keyword search for tenant; results merged and re-ranked. OTEL records retrieval metrics. | RAG, Layer 5, Database |
| **5** | **PromptContextManager** loads template `ticket_summarization` from DB, assembles prompt: system + KB context + 47 messages + memory + “Summarize…”. Context window manager truncates if over token limit. | Layer 4/5, Database |
| **6** | **AI Gateway** is called with assembled prompt and model (e.g. gpt-4). Gateway applies rate limit, dedup, circuit breaker, then calls provider (e.g. OpenAI); returns summary text, tokens, cost. | AI Gateway (LLM) |
| **7** | **ValidationManager** runs PII/secret/ITSM checks on the summary. **LLMOps** logs model, tokens, cost, tenant, latency to DB. | Layer 4, Layer 5 (LLMOpsDAL) |
| **8** | Summary is cached with key `tenant_acme:summarize:TKT-5432` (Dragonfly) and **MemoryDAL** saves updated context for the summarizer agent. | Cache, Layer 5, Source + Database |
| **9** | Event is encoded (CODEC), **NATS** publishes `ticket.summarized`. Feedback loop hook is registered. OTEL ends spans and exports traces/metrics. Response (summary, tokens_used, model, cached: false) is returned to the user. | Cross-cutting, User |

**End-to-end in one line:** Request → middleware (auth, log, trace) → orchestrator (intent, cache check) → load ticket + memory from DB → RAG retrieval from DB → load prompt template → call LLM Gateway → validate → log to DB → cache + update memory → publish event → return summary. All steps are tenant-scoped and auditable.

**Details:** Cache keys include tenant so one tenant never gets another’s summary. If the same ticket is summarized again before TTL, Step 2 returns the cached result and Steps 3–8 are skipped. New tickets (no/few messages) can be handled by checking message count after Step 3 and either returning “Insufficient conversation to summarize” or using a “new ticket” prompt template.
