# AI Architecture — ITSM SaaS Platform

## AI architecture for the ITSM SaaS platform: high-level flow, where the AI Engine sits, and how we’re set up for multi-tenant, audit, and resilience.

---

## Slide 1 — What we’re building for

- **Multi-tenant** — Every request and every query is scoped by tenant. No customer ever sees another customer’s data.
- **Audit and compliance** — Every AI operation is logged with tenant, cost, and a correlation ID so we can trace and audit.
- **Cost control** — We track tokens and cost per tenant and per operation for governance and billing.
- **Knowledge base** — Our RAG can consume KB in multiple formats: text, JSON, CSV. The engine handles parsing and search.
- **Resilience** — Retries, circuit breakers, and caching so we degrade gracefully when something fails.
- **Observability** — Tracing and metrics across the flow for support and operations.

---

## Slide 2 — The big picture: where AI lives

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

**Where the AI Gateway is:** The **AI Gateway** is the first box below the AI Engine, labeled **LLM / AI GATEWAY**. It sits outside the engine: the engine calls it for every text generation and embedding request. It is the single interface to OpenAI, Anthropic, Google, etc., with rate limit, retry, and circuit breaker.

**Data Access Layer (DAL) — what it is, where it sits, and how it works**

- **What it is:** A **DAL** (Data Access Layer) is a thin layer that talks **only** to the database. It has **no business logic**: it takes identifiers and filters in, runs SQL (or DB APIs), and returns **domain objects or lists** (e.g. sessions, messages, documents, memories). Every DAL method that reads or writes data is **tenant-scoped** (e.g. `tenant_id` is required or applied in the query).
- **Where it sits in the flow:** DALs are **Layer 5** in the AI Engine (see diagram: “LAYER 5 — DATA ACCESS”). They sit **between** the services (Layer 3) / core logic (Layer 4) and the **Database**. So: **User → API Gateway → Engine (Middleware → Orchestrator → Agent/RAG/Prompt Service) → DAL → Database**. The Agent Service, RAG Service, Prompt Service, etc. **call** the DAL; the DAL **never** calls the LLM or other services.
- **Input → output (typical pattern):**
  - **Input:** Always includes **tenant_id** (for isolation). Plus one or more of: **entity id** (e.g. `session_id`, `document_id`, `agent_id`), **filters** (e.g. `memory_type`, keywords, limit/offset), or **payload to write** (e.g. session, memory item, document).
  - **Output:** **Reads:** domain objects (e.g. `AgentSession`, `MemoryItem`) or lists of them, or dicts/lists for documents; **writes:** `None` (success) or an id (e.g. document id). DALs do **not** return HTTP responses; they return data to the service that called them.

**DALs used in the ticket-summarization flow (Slide 7) — example inputs and outputs:**

| DAL | Where it’s used in the flow | Typical input | Typical output |
|-----|-----------------------------|---------------|-----------------|
| **SessionDAL** | Step 3 — “get ticket data” (conversation for the ticket) | `tenant_id`, `session_id` (or in ITSM mapping: ticket_id → session) | `AgentSession` (includes `messages: List[SessionMessage]`). Empty list if no messages (e.g. new ticket). |
| **MemoryDAL** | Step 3 — prior context for summarizer agent; Step 8 — save updated context | **Load:** `tenant_id`, `agent_id`, optional `memory_type`. **Save:** `tenant_id`, `MemoryItem` | **Load:** `List[MemoryItem]`. **Save:** `None`. |
| **DocumentDAL** | Step 4 — RAG keyword search (plus vector search via EmbeddingDAL / retriever) | `tenant_id`, `keywords: List[str]`, `limit` | `List[Dict]` (documents with title, content, metadata, etc.). Empty list if no matches. |
| **PromptTemplateDAL** | Step 5 — “get template” for prompt assembly | `tenant_id`, template name (e.g. `ticket_summarization`), optional version | Template content (or None if not found; then app can use FallbackTemplateManager). |
| **EmbeddingDAL** | Step 4 — RAG vector search (similarity_search) | `tenant_id`, query embedding, `top_k`, optional filters | List of nearest document chunks / ids (used with DocumentDAL to get full docs). |
| **LLMOpsDAL** | Step 7 — log model, tokens, cost, tenant | `tenant_id`, operation metadata (model, tokens_in, tokens_out, cost, latency, etc.) | Write-only; no return used by flow. |

So in the diagram: **Step 3** and **Step 8** use SessionDAL and MemoryDAL (read/write **Database**); **Step 4** uses DocumentDAL and EmbeddingDAL; **Step 5** uses PromptTemplateDAL; **Step 7** uses LLMOpsDAL. All of these live in **Layer 5** and are invoked by the Agent Service and RAG Service (Layer 3/4).

---

## Layers in detail (with examples)

Each layer has a single responsibility. Requests flow **down** from Layer 1 → 2 → 3; Layer 3 and 4 call Layer 5 and the AI Gateway as needed.

---

### Layer 1 — Request handling

**Purpose:** Run first on every incoming request: secure it, log it, start tracing, and normalize errors. No business logic; no call to DAL or LLM.

| Component | What it does | Example |
|-----------|----------------|--------|
| **Auth Middleware** | Reads headers (e.g. `X-Tenant-ID`, `Authorization`). Validates that tenant is present and allowed. Rejects with 401/403 if missing or invalid. | Request with `X-Tenant-ID: tenant_acme` → pass. Request with no `X-Tenant-ID` → 401 "Tenant required". |
| **Logging Middleware** | Logs method, path, tenant, correlation_id, user_id, and later status code and duration. | `POST /summarize-ticket tenant=tenant_acme correlation_id=abc-123 → 200 340ms`. |
| **Error Handler** | Catches unhandled exceptions (e.g. from Layer 2 or 3). Maps them to a standard JSON body and HTTP status. | `ValueError("Invalid ticket_id")` → `{ "error": "invalid_request", "detail": "Invalid ticket_id" }` with 400. |
| **OTEL** | Starts root trace span (e.g. `ticket.summarize`). Puts tenant_id (and optionally correlation_id) in baggage so every downstream span can tag traces by tenant. | Span `ticket.summarize` created; child spans (orchestrator, agent, RAG, gateway) all inherit tenant in attributes. |

**Example flow:** `POST /summarize-ticket` with body `{ "ticket_id": "TKT-5432" }` and header `X-Tenant-ID: tenant_acme` → Auth allows → Logging records request → OTEL starts span → request is passed to Layer 2.

---

### Layer 2 — Orchestration

**Purpose:** Decide **what** to do (intent) and **where** to send the request (which service + endpoint). Optionally serve from cache. Call the target service over HTTP with retries and circuit breaker.

| Component | What it does | Example |
|-----------|----------------|--------|
| **Query Router** | Classifies the request into an intent (e.g. by path, body, or a small classifier). No LLM required for this step in the basic design. | `POST /summarize-ticket` + body `{ "ticket_id": "TKT-5432" }` → intent = `AGENT_TASK` or `summarize_ticket`. |
| **Service Selector** | Maps intent to a target service and endpoint. | Intent `summarize_ticket` → Agent Service, `POST /execute` with payload `{ "task_type": "summarize", "ticket_id": "TKT-5432" }`. |
| **Unified Cache** | Before calling the service, builds a cache key (e.g. tenant + operation + entity id). Checks Dragonfly (or other cache). On hit, returns cached response and skips Layer 3/4/5 and LLM. | Key `tenant_acme:summarize:TKT-5432` → cache hit → return cached summary and `cached: true`; no Agent/RAG/LLM call. |
| **Service HTTP Client** | Calls the selected service (e.g. Agent Service) with retry and circuit breaker. Returns response or propagates error. | `POST http://agent-service/execute` with retry 2 times; if service is down, circuit opens and returns 503 after fast-fail. |

**Example flow:** Query Router says "summarize_ticket" → Service Selector says "Agent Service /execute" → Cache get `tenant_acme:summarize:TKT-5432` → miss → Service Client calls Agent Service → response flows back.

---

### Layer 3 — AI services

**Purpose:** Stateless HTTP APIs that implement one capability each (agents, RAG, prompts, cache, ML, ingestion, LLMOps). They use **Layer 4** (core logic) and **Layer 5** (DALs) and the **AI Gateway** (LLM) to do the work.

| Service | Responsibility | Example |
|---------|-----------------|--------|
| **Agent Service** | CRUD for agents; execute tasks (e.g. summarize, analyze); chat with session; load/save memory. Uses Agent Framework (Layer 4), SessionDAL, MemoryDAL (Layer 5), and LLM Gateway. | `POST /execute` with `{ "task_type": "summarize", "ticket_id": "TKT-5432" }` → load session/memory via DALs → build prompt → call gateway → validate → return summary. |
| **RAG Service** | Ingest documents (parse, chunk, embed, store); query (vector + keyword search, merge, re-rank); return context or generated answer. Uses RAG System (Layer 4), DocumentDAL, EmbeddingDAL (Layer 5), and optionally LLM Gateway for answer generation. | `POST /query` with `{ "query": "network outage resolution", "tenant_id": "tenant_acme" }` → DocumentDAL + EmbeddingDAL for retrieval → optional LLM call with context → return answer or chunks. |
| **Prompt Service** | Store and version prompt templates; render with variables; context window management. Uses Prompt Context Manager (Layer 4), PromptTemplateDAL (Layer 5). Does not call LLM. | `GET /templates/ticket_summarization?version=1.0` → PromptTemplateDAL load → return template. Render: `POST /render` with `{ "template": "ticket_summarization", "variables": { "messages": "..." } }` → return assembled prompt text. |
| **Cache Service** | Get/Set/Invalidate by key; keys are tenant-scoped. Talks to Dragonfly (or similar). Used by Layer 2 (unified cache) and by services that want to cache embeddings or responses. | `GET /cache/tenant_acme:summarize:TKT-5432` → return value or 404. `SET` with TTL for caching summarization result. |
| **ML Service** | Train models (e.g. ticket classifier, SLA predictor); run predictions; deploy and monitor. Uses ML Framework (Layer 4) and possibly DALs for features/labels. | `POST /predict` with ticket features → return priority or SLA risk score. |
| **Data Ingestion Service** | Upload files (PDF, CSV, JSON); parse and normalize; optionally use LLM for extraction; pipeline into KB or training data. Uses Data Ingestion pipeline (Layer 4), DocumentDAL, EmbeddingDAL (Layer 5). | `POST /ingest` with file + tenant_id → parse → chunk → embed → DocumentDAL.save, EmbeddingDAL.upsert. |
| **Prompt Generator Service** | Create agents or tools from natural-language prompts (e.g. "An agent that summarizes tickets"). Uses Prompt Generator (AgentGen, ToolGen) and LLM Gateway. | User says "Create an agent that escalates high-priority tickets" → LLM generates config/schema → agent or tool definition stored. |
| **LLMOps Service** | Log every LLM call: model, tenant, tokens_in, tokens_out, cost, latency. Expose metrics and dashboards. Uses LLMOpsDAL (Layer 5). | After each gateway call, Agent Service (or gateway wrapper) sends log to LLMOps Service → LLMOpsDAL.insert → available for billing and audit. |

**Example (ticket summarization):** Orchestrator calls **Agent Service** `/execute`. Agent Service uses **SessionDAL** to get messages, **MemoryDAL** to get prior context, **RAG** (or RAG Service) for KB context, **Prompt Service** (or in-process Prompt Context Manager) for template, then **AI Gateway** for LLM call, then **MemoryDAL** and **Cache** to save result.

---

### Layer 4 — Core business logic

**Purpose:** Reusable libraries/frameworks that contain the actual AI and business logic. **No direct DB or HTTP** — they receive DALs, gateway, and config via dependency injection. Layer 3 services are the ones that call Layer 4 and pass these dependencies.

| Component | What it does | Example |
|-----------|----------------|--------|
| **Agent Framework** | Agents, tasks, sessions, tool-calling loop. Given a task (e.g. "summarize"), builds prompt from context, calls LLM (via injected gateway), handles tools, returns result. | `execute_task(agent, "summarize", { "ticket_id": "TKT-5432" })` → uses session/memory from DALs, builds prompt, calls gateway.generate_async(), returns summary. |
| **RAG System** | Retriever (vector + keyword), document processor (chunk, normalize), generator (optional LLM). Given a query and tenant, returns relevant chunks or full answer. | Retriever.similarity_search(embedding, top_k=5) + DocumentDAL.keyword_search() → merge and re-rank → Generator.generate(query, context) → answer. |
| **Prompt Context Manager** | Load template by name/version (via store/DAL), render with variables, apply context window (truncate by tokens). | get_template("ticket_summarization"); render({ "messages": messages_text, "kb_context": kb_text }); truncate to 8k tokens. |
| **Cache Mechanism** | Key-value with TTL; tenant-scoped keys; optional fallback or multi-tier. Used by Layer 2 and by services. | get("tenant_acme:summarize:TKT-5432") → miss; after LLM response, set(key, summary, ttl=3600). |
| **Validation & Guardrails** | PII detection/redaction, policy checks, output format validation. Applied to LLM output before returning to client. | validate(summary) → strip PII, check no secrets, ensure ITSM-safe → return cleaned text or errors. |
| **LLMOps** | Interface to record model, tokens, cost, tenant, latency. Implemented by writing to LLMOpsDAL or sending to LLMOps Service. | record(tenant_id, model, tokens_in, tokens_out, cost_usd, latency_ms). |
| **Feedback Loop** | Register hooks for ratings or corrections; store and optionally feed back into prompts or fine-tuning. | User rates summary "thumbs down" → store with ticket_id and correlation_id for later analysis. |
| **Prompt Generator (AgentGen, ToolGen)** | Take natural-language description; call LLM to produce agent config or tool schema. | "Agent that summarizes tickets" → LLM returns JSON config for agent + tools. |
| **ML Framework** | Trainer, Predictor, MLOps pipeline for training and serving models (classification, regression). | Trainer.train(features, labels); Predictor.predict(features) → priority score. |
| **Data Ingestion pipeline** | Parse file → normalize → chunk → embed → store. Orchestrates steps; uses Document processor and DALs. | PDF → extract text → chunk by size/overlap → embed each chunk → DocumentDAL.save, EmbeddingDAL.upsert. |

**Example:** Agent Service receives "summarize TKT-5432". It uses **Agent Framework** to run the task. The framework uses **Prompt Context Manager** (template + render + truncate), **RAG System** (retrieve KB), and injected **gateway** for the LLM call. After the call, **Validation** runs on the summary, **LLMOps** records the call, **Cache Mechanism** and **MemoryDAL** persist the result.

---

### Layer 5 — Data access

**Purpose:** Single place that talks to the **Database** (PostgreSQL + pgvector). Each DAL is scoped to one entity (sessions, documents, memories, prompts, etc.). Every method is tenant-scoped. No business logic; only CRUD and queries.

| Concept | Detail | Example |
|---------|--------|--------|
| **Who calls Layer 5** | Layer 3 services and Layer 4 components that receive DALs as dependencies. | Agent Service calls SessionDAL.load_session(session_id, tenant_id); RAG Service calls DocumentDAL.keyword_search(tenant_id, keywords, limit). |
| **Input** | Always tenant_id plus entity id(s), filters, or write payload. | MemoryDAL.load_memories(agent_id="summarizer", tenant_id="tenant_acme", memory_type=MemoryType.CONTEXT). |
| **Output** | Domain objects or lists (e.g. AgentSession, List[MemoryItem], List[dict] for documents). Writes return None or id. | SessionDAL.load_session() → AgentSession(messages=[...]); DocumentDAL.keyword_search() → [{ "id", "title", "content", "metadata" }, ...]. |
| **Tenant isolation** | Every SELECT/INSERT/UPDATE/DELETE includes tenant_id (or equivalent) so one tenant never sees another’s data. | SELECT * FROM agent_sessions WHERE session_id = $1 AND tenant_id = $2. |

See the **DAL table** earlier in this document for the ticket-summarization flow: SessionDAL, MemoryDAL, DocumentDAL, PromptTemplateDAL, EmbeddingDAL, LLMOpsDAL with their typical inputs and outputs.

---

### Cross-cutting: OTEL, CODEC, NATS

**Purpose:** Observability, versioned messaging, and events that span multiple layers and services.

| Component | What it does | Example |
|-----------|----------------|--------|
| **OTEL** | Tracing (spans) and metrics across the engine. Layer 1 starts the root span and sets tenant in baggage; each layer and service can create child spans and record metrics. | Root span `ticket.summarize` → child spans `orchestrator.route`, `agent.execute`, `rag.retrieve`, `gateway.generate`; all tagged with tenant_acme. Metrics: llm_calls_total, rag_retrieval_latency_seconds. |
| **CODEC** | Encode/decode events and messages with a versioned schema so that producers and consumers can evolve without breaking each other. | Encode event `{ "type": "ticket.summarized", "ticket_id": "TKT-5432", "tenant_id": "tenant_acme" }` with schema v2 → bytes; subscriber decodes with same schema. |
| **NATS** | Publish domain events so other systems (e.g. ITSM workflow, analytics) can react without being called synchronously. | After summarization: publish("ticket.summarized", payload) → downstream subscriber updates ticket record or triggers notification. |

---

## Slide 3 — Common questions

| Question | Answer |
|----------|--------|
| Why one central AI Engine? | Easier to secure, monitor, and scale. All AI logic and tenant isolation live in one place. |
| How do we enforce tenant isolation? | Tenant ID is required on every request and on every database query. It’s built into the data layer. |
| What if the LLM is down? | Circuit breakers and retries. We also cache prior results so repeat requests don’t always need the LLM. |
| Can we audit AI actions? | Yes. Every LLM call, RAG query, and key operation is logged with tenant and correlation ID. |

---

## Slide 4 — Where the LLM / AI Gateway is used

All LLM calls go through a single **LLM / AI Gateway**. Nothing in the engine talks directly to OpenAI or Anthropic.

- **Agent Service** — Every agent task, chat, and reasoning call.
- **RAG Service** — Generating answers from retrieved context and generating embeddings for search.
- **Gateway Service** — Exposes the gateway as a REST API (generate, embed, stream) for other services or clients.
- **Prompt Generator Service** — Creating agents and tools from natural-language prompts.
- **Data Ingestion** — Optional LLM use when ingesting files into the KB.

---

## Slide 5 — What happens when we call the AI Gateway

1. **Check cache** — Same prompt + model + tenant → return cached response if valid.
2. **Rate limit** — Token bucket, per tenant.
3. **Deduplication** — Identical in-flight requests share one LLM call.
4. **Circuit breaker** — If this model or provider is failing repeatedly, we fail fast and don’t hammer it.
5. **Call LLM** — Via a router: primary model, or fallback list if we’ve configured it.
6. **Validate** — PII, policy, guardrails on the response.
7. **Log** — Tokens, cost, model, tenant, latency (LLMOps).
8. **Cache** — Store result for future identical requests.
9. **Return** — Text or embeddings back to the caller.

---

## Slide 6 — How we choose the model

- **Different model per feature** — The caller passes the model on each call. We can use, for example, GPT-4 for summarization and a smaller model for chat. We decide that in our wiring or config; the gateway doesn’t choose by feature name.
- **When a model is down** — We can configure a **model list** and **fallbacks**. The router then automatically tries the next model if the primary fails. We also have a circuit breaker so we don’t keep hitting a failed provider.

---

## Slide 7 — Example: ticket summarization (end to end)

**Scenario:** Support agent in ITSM portal clicks **Summarize ticket** for ticket TKT-5432.

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
       │                          │              │──────────────────────────────────────────────────►│                       │  Dragonfly
       │                          │  · MemoryDAL.save(tenant_acme, summarizer_agent, context)         │                       │
       │                          │              │──────────────────────────────────────────────────►│                       │  agent_memory
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

**Flow summary:** Request → middleware (auth, log, trace) → orchestrator (intent, cache check) → load ticket + memory from DB → RAG retrieval (vector + keyword) from DB → load prompt template from DB → call LLM Gateway → validate → log to DB → cache result in Dragonfly → update memory in DB → publish event → return summary. All steps tenant-scoped and auditable.

**Edge cases and fallbacks (including “new ticket” / missing data):**

| Scenario | Behavior | Where it’s handled |
|----------|----------|--------------------|
| **New ticket — no or few messages** | Orchestrator or Agent Service can check message count after Step 3. If below a threshold (e.g. 0–1 messages), either: (a) skip LLM call and return a fixed response (e.g. “Insufficient conversation to summarize”), or (b) use a dedicated “new ticket” / minimal-data prompt template so the LLM returns a short placeholder. | **AI Engine / app** (orchestrator or agent service logic). SDK’s **FallbackTemplateManager** can be used with a condition (e.g. “use `ticket_summarization_new_ticket` when message count &lt; 2”) so the right template is chosen before Step 5. |
| **Empty RAG / no KB results** | Step 4 can return an empty or small list. Prompt assembly (Step 5) still runs with empty or minimal KB context; LLM is called with “no relevant articles” so it can still produce a summary from ticket messages only. | **AI Engine** (RAG returns empty list; prompt template should tolerate empty KB section). |
| **Prompt template not found** | If the primary template (e.g. `ticket_summarization`) is missing, use **FallbackTemplateManager** (or default fallback template) so a valid template is always passed to Step 5 — avoids failing the request. | **SDK** (`FallbackTemplateManager.get_template_with_fallback` in prompt context management). |
| **LLM provider / model down** | Gateway uses **model fallbacks** (e.g. `fallbacks: ["gpt-4", "gpt-3.5-turbo", "claude-3"]`). If the primary model fails, the next model in the list is tried so the request can still complete. | **SDK** (LiteLLM gateway `fallbacks` config and routing). |

So: **model fallback** (provider down) and **template fallback** (template missing) are handled in the **existing SDK**. **Data fallback** (new ticket / no or minimal ticket data) is handled in the **AI Engine** — e.g. early check after loading ticket/session and either returning a safe response or choosing a “new ticket” template; the SDK supports this via conditional fallback templates and by not requiring non-empty messages for the gateway call.

---

## Slide 8 — Summary: what we have today

| Topic | What we have |
|-------|----------------------|
| **Place of AI** | One **AI Engine**; all AI services run inside it. |
| **User access** | Users → AWS API Gateway (auth, tenant) → AI Engine. |
| **Data** | **Database** for tickets, conversations, KB, embeddings (PostgreSQL + pgvector). **Source** for cache, events, traces. |
| **LLM** | One **LLM / AI Gateway** to OpenAI, Anthropic, Google, etc.; rate limit, retry, circuit breaker. |
| **ITSM SaaS** | Multi-tenant, tenant-scoped data, audit logs, cost per tenant, KB in multiple formats. |

---

## Closing — Validation

1. Does this high-level flow work for our ITSM SaaS use cases? (Tickets, KB, multi-tenant, and the AI features we’re planning.)
2. Is one AI Engine with clear boundaries to gateway, DB, and source acceptable? Or do you see a need to split things differently?
3. Any must-haves for compliance or ITSM? (e.g. extra audit, data residency, or changes to how we use the LLM gateway.)
