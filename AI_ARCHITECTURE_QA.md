# AI Architecture — Questions & Answers

**Purpose:** Questions that a department head or AI/architecture reviewer might ask based on the AI Architecture document, with answers drawn from the same document. Use this for prep before a review or presentation.

---

## Strategy & scope

**Q1. Why do we have one central AI Engine instead of multiple AI services per product?**

**A.** One central AI Engine makes it easier to secure, monitor, and scale. All AI logic and tenant isolation live in one place. We get a single boundary for auth, logging, tracing, cost control, and compliance instead of duplicating them across many services.

---

**Q2. Does this architecture work for our ITSM SaaS use cases (tickets, KB, multi-tenant, planned AI features)?**

**A.** Yes. The document is built around ITSM: ticket summarization is the main end-to-end example. The flow supports tickets, conversations, KB (RAG), multi-tenancy, agents, chat, RAG query, ML (e.g. classification, SLA prediction), prompt management, and data ingestion. The same engine can support additional AI features by adding or extending Layer 3 services and Layer 4 logic.

---

**Q3. Where does the AI Gateway sit, and why is it separate from the AI Engine?**

**A.** The AI Gateway is the first box below the AI Engine in the diagram—the single interface to all LLM providers (OpenAI, Anthropic, Google, etc.). It sits “outside” the engine in the sense that the engine *calls* it for every text generation and embedding request. Keeping it as one gateway gives us one place for rate limiting, retries, circuit breaker, caching, and logging of LLM usage.

---

## Security & multi-tenancy

**Q4. How do we enforce tenant isolation so one customer never sees another’s data?**

**A.** Tenant ID is required on every request (e.g. `X-Tenant-ID` from the API Gateway) and on every database query. It’s enforced in Layer 1 (auth middleware rejects missing tenant) and built into the data layer: every DAL method is tenant-scoped (e.g. `WHERE tenant_id = $2`). So all reads and writes are filtered by tenant.

---

**Q5. What happens if a request arrives without a tenant ID?**

**A.** The Auth Middleware in Layer 1 validates that `X-Tenant-ID` is present (and allowed). If it’s missing or invalid, the request is rejected with 401/403 before any business logic or data access runs.

---

**Q6. Who can call the AI Engine, and how are they authenticated?**

**A.** Users (ITSM Portal, mobile app, REST clients) send HTTPS requests with JWT in the Authorization header. The AWS API Gateway validates JWT signature and expiry, extracts `tenant_id` and `user_id` from claims, and injects `X-Tenant-ID`, `X-User-ID`, and optionally `X-Correlation-ID`, `X-Request-ID` into the request to the AI Engine. The engine trusts these headers after gateway validation.

---

## Layers & flow

**Q7. What is the request flow from user to response?**

**A.** User → AWS API Gateway (auth, tenant injection) → AI Engine → Layer 1 (auth, logging, OTEL, error handling) → Layer 2 (Query Router → Service Selector → Unified Cache → Service HTTP Client) → Layer 3 (e.g. Agent Service, RAG Service) → Layer 4 (Agent Framework, RAG System, Prompt Context Manager, etc.) and Layer 5 (DALs) and AI Gateway as needed → Database / Dragonfly / LLM → response back up the stack.

---

**Q8. What is the role of each layer (1–5)?**

**A.**  
- **Layer 1 — Request handling:** Auth, logging, error mapping, OTEL root span. No business logic.  
- **Layer 2 — Orchestration:** Decide intent, map to service/endpoint, check cache, call target service with retry/circuit breaker.  
- **Layer 3 — AI services:** Stateless APIs (Agent, RAG, Prompt, Cache, ML, Data Ingestion, LLMOps, etc.) that implement one capability each; they use Layer 4, Layer 5, and the AI Gateway.  
- **Layer 4 — Core business logic:** Reusable frameworks (Agent Framework, RAG System, Prompt Context Manager, Validation, etc.) with no direct DB or HTTP; they receive DALs and gateway via injection.  
- **Layer 5 — Data access:** DALs that only talk to the database; tenant-scoped CRUD and queries, no business logic.

---

**Q9. What is a DAL, and where does it sit in the flow?**

**A.** A DAL (Data Access Layer) is a thin layer that talks only to the database. It takes identifiers and filters (and always `tenant_id`), runs SQL/DB APIs, and returns domain objects or lists. It has no business logic. DALs sit in Layer 5, between Layer 3/4 services and the Database. Services call DALs; DALs never call the LLM or other services.

---

**Q10. Which components call the LLM (AI Gateway)?**

**A.** Agent Service (every agent task, chat, reasoning), RAG Service (answer generation and optionally embeddings), Gateway Service (REST API for generate/embed/stream), Prompt Generator Service (creating agents/tools from prompts), and Data Ingestion (optional LLM when ingesting into KB). Nothing in the engine talks directly to OpenAI or Anthropic—all calls go through the single AI Gateway.

---

## Resilience & fallbacks

**Q11. What if the LLM or a provider is down?**

**A.** We use circuit breakers and retries at the gateway and at the Service HTTP Client (Layer 2). We also configure a model list and fallbacks (e.g. `fallbacks: ["gpt-4", "gpt-3.5-turbo", "claude-3"]`); the router tries the next model if the primary fails. Caching (Unified Cache, gateway cache) means repeat requests may be served without calling the LLM.

---

**Q12. How do we handle a “new ticket” with no or very few messages?**

**A.** This is a data-availability fallback. After Step 3 (load ticket/session), the orchestrator or Agent Service can check message count. If below a threshold (e.g. 0–1 messages), we either (a) skip the LLM and return a fixed response (e.g. “Insufficient conversation to summarize”), or (b) use a dedicated “new ticket” prompt template so the LLM returns a short placeholder. The SDK’s FallbackTemplateManager can choose the template with a condition (e.g. use `ticket_summarization_new_ticket` when message count < 2).

---

**Q13. What if RAG returns no KB results?**

**A.** Step 4 can return an empty list. Prompt assembly (Step 5) still runs with empty or minimal KB context; we call the LLM with “no relevant articles” so it can still produce a summary from ticket messages only. The prompt template should tolerate an empty KB section.

---

**Q14. What if a prompt template is missing?**

**A.** We use FallbackTemplateManager (or a default fallback template). If the primary template (e.g. `ticket_summarization`) is not found, the SDK’s `get_template_with_fallback` returns a configured fallback so a valid template is always passed to prompt assembly—avoiding request failure.

---

## Cost & audit

**Q15. How do we control and track cost per tenant?**

**A.** We track tokens and cost per tenant and per operation. Every LLM call is logged via LLMOps (model, tokens_in, tokens_out, cost, tenant, latency) and persisted (e.g. LLMOpsDAL). This supports governance, billing, and cost alerts per tenant.

---

**Q16. Can we audit AI actions?**

**A.** Yes. Every LLM call, RAG query, and key operation is logged with tenant and correlation ID. Layer 1 logs request/response and timing; LLMOps logs model, tokens, cost; OTEL provides traces across the flow. So we can trace a request from API Gateway through orchestrator, service, DAL, and gateway.

---

**Q17. What is logged for a typical “summarize ticket” request?**

**A.** Middleware logs method, path, tenant, correlation_id, duration, status. LLMOps logs model, tokens_in, tokens_out, cost, tenant, latency for the gateway call. OTEL records a root span (e.g. `ticket.summarize`) and child spans (orchestrator, agent, RAG, gateway), all tagged with tenant. Optionally, RAG and agent actions are logged for audit.

---

## Observability & events

**Q18. How do we trace a request across the engine?**

**A.** OTEL starts a root trace span in Layer 1 (e.g. `ticket.summarize`) and puts tenant_id (and optionally correlation_id) in baggage. Each layer and service can create child spans. So we get one trace from middleware → orchestrator → Agent Service → DAL / RAG / gateway, all with the same trace ID and tenant tags.

---

**Q19. What are NATS and CODEC used for?**

**A.** **NATS** is the event bus: we publish domain events (e.g. `ticket.summarized`, `agent.created`, `rag.ingested`) so other systems (ITSM workflow, analytics) can react asynchronously without being called synchronously. **CODEC** is for versioned encode/decode of those events so producers and consumers can evolve schemas without breaking each other.

---

## Data & RAG

**Q20. What formats does the KB (RAG) support?**

**A.** The RAG can consume KB in multiple formats: text, JSON, CSV. The engine (Data Ingestion pipeline, document processor) handles parsing and normalization before chunking, embedding, and storing in the database (DocumentDAL, EmbeddingDAL).

---

**Q21. How does RAG retrieval work in the ticket flow?**

**A.** In Step 4 we do vector search (e.g. pgvector similarity_search, top_k=5) and keyword search (DocumentDAL.keyword_search with tenant and keywords). Results are merged and re-ranked. The assembled context is passed to prompt assembly (Step 5) and optionally to the LLM for answer generation.

---

**Q22. Where is data stored (database vs cache vs external)?**

**A.** **Database (PostgreSQL + pgvector):** Tickets, conversations, KB documents, embeddings, prompts, agents, sessions, LLM ops log, audit tables—all tenant-scoped. **Source (Dragonfly):** Response cache, embedding cache, query cache with tenant-scoped keys. **OTEL Collector** and **NATS** are used for traces/metrics and events. The AI Engine does not store tenant data in external third-party systems beyond the configured DB and cache.

---

## Model selection & gateway

**Q23. How do we choose which LLM model to use for a given feature?**

**A.** The caller passes the model on each call (e.g. `gateway.generate_async(..., model="gpt-4")`). We decide per feature in wiring or config (e.g. GPT-4 for summarization, a smaller model for chat). The gateway does not choose by feature name—it just routes to the requested model and applies fallbacks if that model fails.

---

**Q24. What happens when we call the AI Gateway (step by step)?**

**A.** (1) Check cache—same prompt + model + tenant → return cached response if valid. (2) Rate limit (token bucket, per tenant). (3) Deduplication—identical in-flight requests share one LLM call. (4) Circuit breaker—if the model/provider is failing repeatedly, fail fast. (5) Call LLM via router (primary or next fallback). (6) Validate—PII, policy, guardrails on response. (7) Log—tokens, cost, model, tenant, latency (LLMOps). (8) Cache result for future identical requests. (9) Return text or embeddings to the caller.

---

## Compliance & ITSM

**Q25. Are there any must-haves for compliance or ITSM we should call out?**

**A.** The document calls out: multi-tenant isolation, audit (tenant + correlation ID on operations), cost tracking per tenant, and validation (PII, guardrails) on LLM output. Specific must-haves (e.g. data residency, extra audit fields, retention) should be confirmed with compliance and ITSM stakeholders; the architecture supports adding them (e.g. more fields in LLMOps, tenant metadata in DALs, NATS/CODEC for audit events).

---

**Q26. How do we handle PII and sensitive data in LLM output?**

**A.** Validation and guardrails (Layer 4) run on LLM output before returning to the client. This includes PII detection/redaction and policy checks so we don’t expose secrets or non-ITSM-safe content. The exact rules can be configured per tenant or globally.

---

## Summary & validation

**Q27. What do we have today, in one sentence per area?**

**A.** **Place of AI:** One AI Engine; all AI services run inside it. **User access:** Users → AWS API Gateway (auth, tenant) → AI Engine. **Data:** Database (PostgreSQL + pgvector) for tickets, conversations, KB, embeddings; Source for cache (Dragonfly), events (NATS), traces (OTEL). **LLM:** One AI Gateway to OpenAI, Anthropic, Google, etc., with rate limit, retry, circuit breaker. **ITSM SaaS:** Multi-tenant, tenant-scoped data, audit logs, cost per tenant, KB in multiple formats.

---

**Q28. Is one AI Engine with clear boundaries to gateway, DB, and source acceptable, or should we split differently?**

**A.** The document proposes one engine with clear boundaries. Splitting would be acceptable if there are strong reasons (e.g. separate scaling, regulatory isolation). The current design keeps security, observability, and tenant isolation in one place and is presented as the recommended approach unless compliance or scale demands otherwise.

---

**Q29. What are the main edge cases and where are they handled?**

**A.** (1) **New ticket / no messages:** Engine or orchestrator checks after loading ticket; return fixed message or use “new ticket” template; SDK supports conditional fallback templates. (2) **Empty RAG:** Engine; prompt tolerates empty KB context. (3) **Template not found:** SDK FallbackTemplateManager. (4) **LLM/provider down:** SDK gateway fallbacks and circuit breaker.

---

**Q30. How does the ticket summarization flow end to end (high level)?**

**A.** Request → middleware (auth, log, trace) → orchestrator (intent, cache check) → load ticket + memory from DB (SessionDAL, MemoryDAL) → RAG retrieval (vector + keyword) from DB → load prompt template → call LLM Gateway → validate → log to DB (LLMOps) → cache result in Dragonfly → update memory in DB → publish event (NATS) → return summary. All steps are tenant-scoped and auditable.
