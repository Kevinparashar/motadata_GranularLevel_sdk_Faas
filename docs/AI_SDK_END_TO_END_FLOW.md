# AI SDK End-to-End Flow: From Development to Runtime Execution (NATS + OTEL + CODEC + AI Components)

## Executive Summary

The AI SDK provides enterprise-grade AI capabilities (agent orchestration, RAG retrieval, LLM gateway, prompt management) integrated with three foundational platform components: **NATS** for asynchronous messaging, **OpenTelemetry (OTEL)** for distributed observability, and **CODEC** for schema-versioned message serialization. This integration enables deterministic, reviewable, and production-ready AI workflows where incoming events trigger intelligent processing pipelines that enrich and route data through validated, observable, and recoverable execution paths. The SDK operates as a message-driven system where all AI operations are instrumented, traced, and validated at each stage, ensuring compliance with platform standards while delivering scalable AI enrichment capabilities.

---

## Actors and Runtime Components

### Development-Time Actors
- **Developer**: Builds use cases using SDK primitives (Agent Framework, RAG System, LiteLLM Gateway, Prompt Management)
- **CI/CD Pipeline**: Validates code, runs tests, packages artifacts, enforces contract compliance

### Runtime Components
- **AI SDK Runtime**: Executes use case handlers, orchestrates AI components, manages state
- **NATS Broker**: Message broker for pub/sub and request/reply patterns, handles routing and delivery
- **Upstream Producer Service**: Publishes events to NATS subjects (e.g., `ai.incident.triage.request.{tenant_id}`)
- **Downstream Consumer Service**: Consumes enriched events from NATS subjects (e.g., `ai.incident.triage.response.{tenant_id}`)
- **OTEL Collector**: Receives traces, metrics, and logs from SDK runtime, forwards to backends (Jaeger, Prometheus, etc.)
- **Vector DB (PostgreSQL with pgvector)**: Stores document embeddings for RAG retrieval
- **LLM Provider (via LiteLLM Gateway)**: Provides LLM inference (OpenAI, Anthropic, etc.)

---

## End-to-End Flow: AI Incident Triage / AI Enrichment Pipeline

### Use Case Overview
**Input**: Incident event arrives via NATS with incident details (title, description, priority, affected user)  
**Output**: Enriched incident event published back with AI-generated analysis (category prediction, suggested resolution, risk assessment)

### Success Path Flow
1. Upstream service publishes incident event to `ai.incident.triage.request.{tenant_id}`
2. AI SDK runtime subscribes and receives message
3. CODEC decodes and validates message schema
4. OTEL extracts trace context and creates root span
5. Agent Framework orchestrates triage workflow
6. RAG System retrieves relevant knowledge base articles
7. LiteLLM Gateway generates AI analysis
8. Prompt Management applies guardrails and formatting
9. CODEC encodes enriched response with schema version
10. NATS publishes to `ai.incident.triage.response.{tenant_id}`
11. Downstream service consumes enriched event

### Failure Path Flow
1. Message decode failure → Publish to `ai.incident.triage.failed.{tenant_id}` with error details
2. LLM timeout → Retry with circuit breaker, then publish failure event
3. Vector DB failure → Fallback to keyword search, log error, continue
4. Agent failure → Publish partial result with error metadata, route to DLQ

---

## Stage-by-Stage Breakdown

### Stage 1: Developer Builds Use Case Using SDK Primitives

**Trigger**: Developer creates new use case handler file

**Components Used**:
- `src/core/agno_agent_framework/` - Agent orchestration
- `src/core/rag/` - Knowledge retrieval
- `src/core/litellm_gateway/` - LLM calls
- `src/core/prompt_context_management/` - Prompt templates
- `src/integrations/nats_integration/` - NATS client wrapper
- `src/integrations/otel_integration/` - OTEL tracer/metrics wrapper
- `src/integrations/codec_integration/` - CODEC serializer wrapper

**What is Produced**:
- Use case handler class (e.g., `IncidentTriageHandler`)
- Agent task definitions
- RAG query logic
- Prompt templates
- Error handling logic

**Mandatory Metadata**:
- `tenant_id` - Extracted from NATS subject or message headers
- `correlation_id` - Generated or extracted from incoming message
- `schema_version` - Defined in CODEC schema registry
- `trace_context` - Extracted from NATS headers (W3C Trace Context)

**Validations**:
- CODEC schema validation: Message structure matches registered schema
- NATS header validation: Required headers present (tenant_id, correlation_id, traceparent)
- OTEL propagation validation: Trace context properly formatted

**Logs/Metrics/Traces**:
- Log: `INFO: Use case handler initialized: IncidentTriageHandler`
- Metric: `sdk.use_case.handler.created` (counter)
- Trace: Not applicable (development stage)

---

### Stage 2: Packaging/Release Inside AI SDK Repo

**Trigger**: CI/CD pipeline executes on merge to main branch

**Components Used**:
- Test suite: `src/tests/unit_tests/`, `src/tests/integration_tests/`
- Benchmark suite: `src/tests/benchmarks/`
- Contract validation: CODEC schema registry validation
- Package builder: Python package creation

**What is Produced**:
- Validated Python package artifact
- Test results report
- Benchmark results report
- Schema registry snapshot
- Documentation artifacts

**Mandatory Metadata**:
- Package version (semantic versioning)
- Schema registry version
- Dependency versions (NATS wrapper, OTEL wrapper, CODEC wrapper)

**Validations**:
- Unit tests pass (codec helpers, wrapper usage, span helpers)
- Integration tests pass (Docker NATS end-to-end)
- Contract fixture decode tests pass (all registered schemas)
- OTEL propagation tests pass (trace context round-trip)
- Benchmark smoke tests pass (codec latency < 1ms P95, publish/consume throughput > 100 msg/sec)

**Logs/Metrics/Traces**:
- Log: `INFO: Package build successful: ai-sdk v1.2.3`
- Metric: `sdk.build.duration` (histogram), `sdk.build.success` (counter)
- Trace: Build pipeline trace (optional)

---

### Stage 3: Runtime Message Ingestion (NATS Subscribe)

**Trigger**: Upstream service publishes event to `ai.incident.triage.request.{tenant_id}`

**Components Used**:
- `src/integrations/nats_integration/` - NATS client wrapper
- NATS broker (external)

**What is Consumed**:
- Raw NATS message with headers and payload bytes

**Mandatory Metadata**:
- `tenant_id` - Extracted from NATS subject pattern `ai.incident.triage.request.{tenant_id}`
- `correlation_id` - From NATS headers (`X-Correlation-ID`)
- `traceparent` - From NATS headers (W3C Trace Context format: `00-{trace_id}-{span_id}-{flags}`)
- `timestamp` - Message publish timestamp from NATS headers

**Validations**:
- NATS subject validation: Subject matches expected pattern `ai.{component}.{operation}.{tenant_id}`
- NATS header validation: Required headers present and non-empty
- Tenant isolation: Subscription queue group ensures tenant isolation

**Logs/Metrics/Traces**:
- Log: `INFO: Message received: subject=ai.incident.triage.request.tenant_123, correlation_id=corr_456`
- Metric: `nats.messages.received` (counter, labels: tenant_id, subject)
- Metric: `nats.message.size` (histogram, bytes)
- Trace: Root span created with name `nats.consume`, attributes: `nats.subject`, `nats.tenant_id`, `nats.correlation_id`

---

### Stage 4: CODEC Decode + Validation

**Trigger**: Raw message payload received from NATS

**Components Used**:
- `src/integrations/codec_integration/` - CODEC serializer wrapper

**What is Consumed**:
- Encoded message payload (bytes)

**What is Produced**:
- Decoded message envelope (dict) with structure:
  ```python
  {
    "message_type": "incident_triage_request",
    "spec_version": "1.0",
    "tenant_id": "tenant_123",
    "correlation_id": "corr_456",
    "timestamp": "2024-01-15T10:30:00Z",
    "payload": {
      "incident_id": "INC-12345",
      "title": "Server outage",
      "description": "Production server unresponsive",
      "priority": "high",
      "affected_user": "user@example.com"
    }
  }
  ```

**Mandatory Metadata**:
- `message_type` - Must match registered schema name
- `spec_version` - Schema version (e.g., "1.0")
- `tenant_id` - Must match NATS subject tenant_id
- `correlation_id` - Must match NATS header correlation_id
- `timestamp` - ISO 8601 format

**Validations**:
- CODEC schema validation: Envelope structure matches schema registry definition
- Schema version check: Version exists in registry, migration path available if needed
- Field validation: Required fields present, types correct, constraints satisfied
- Tenant ID consistency: Envelope tenant_id matches NATS subject tenant_id

**Logs/Metrics/Traces**:
- Log: `INFO: Message decoded: message_type=incident_triage_request, spec_version=1.0, correlation_id=corr_456`
- Log: `ERROR: Decode failed: schema_validation_error, correlation_id=corr_456` (on failure)
- Metric: `codec.decode.attempts` (counter)
- Metric: `codec.decode.success` (counter)
- Metric: `codec.decode.duration` (histogram, milliseconds)
- Metric: `codec.decode.failures` (counter, labels: error_type)
- Trace: Child span `codec.decode` with attributes: `codec.message_type`, `codec.spec_version`, `codec.decode.success`

---

### Stage 5: OTEL Trace Extraction and Span Creation

**Trigger**: Decoded message envelope available

**Components Used**:
- `src/integrations/otel_integration/` - OTEL tracer wrapper

**What is Consumed**:
- Trace context from NATS headers (`traceparent`)
- Decoded message metadata

**What is Produced**:
- OTEL trace context object
- Root span for message processing
- Span attributes and events

**Mandatory Metadata**:
- `trace_id` - Extracted from `traceparent` header or generated if missing
- `span_id` - Extracted from `traceparent` or generated for root span
- `parent_span_id` - From `traceparent` if present
- `correlation_id` - From message envelope (for log correlation)

**Validations**:
- OTEL propagation validation: `traceparent` header format valid (W3C Trace Context)
- Trace context extraction: Successfully extracts or generates trace context
- Span creation: Root span created with proper parent context

**Logs/Metrics/Traces**:
- Log: `INFO: Trace context extracted: trace_id=abc123, span_id=def456, correlation_id=corr_456`
- Metric: `otel.traces.started` (counter)
- Metric: `otel.trace.context.extracted` (counter, labels: source=nats_header)
- Trace: Root span `ai.incident.triage.process` with attributes:
  - `tenant_id`: "tenant_123"
  - `correlation_id`: "corr_456"
  - `message_type`: "incident_triage_request"
  - `incident_id`: "INC-12345"

---

### Stage 6: Agent Orchestration Step

**Trigger**: Decoded message and trace context available

**Components Used**:
- `src/core/agno_agent_framework/` - Agent Framework
- `src/integrations/nats_integration/` - NATS for agent-to-agent messaging (if multi-agent)
- `src/integrations/otel_integration/` - OTEL for agent tracing

**What is Consumed**:
- Decoded message payload (incident details)
- Agent task definition
- Agent memory (if available)

**What is Produced**:
- Agent task execution plan
- Agent reasoning output
- Agent memory updates (if applicable)
- Intermediate results for next stages

**Mandatory Metadata**:
- `tenant_id` - From message envelope
- `correlation_id` - From message envelope
- `trace_id` - From OTEL trace context
- `agent_id` - Agent instance identifier
- `task_id` - Generated task identifier

**Validations**:
- Agent task validation: Task definition valid, required parameters present
- Agent memory validation: Memory access authorized for tenant
- Agent health check: Agent instance healthy before task execution

**Logs/Metrics/Traces**:
- Log: `INFO: Agent task started: agent_id=agent_triage_001, task_id=task_789, correlation_id=corr_456`
- Metric: `agent.tasks.started` (counter, labels: agent_id, tenant_id)
- Metric: `agent.task.duration` (histogram, seconds)
- Metric: `agent.memory.operations` (counter, labels: operation_type)
- Trace: Child span `agent.task.execute` with attributes:
  - `agent.id`: "agent_triage_001"
  - `agent.task.id`: "task_789"
  - `agent.task.type`: "incident_triage"
  - `agent.memory.used`: true/false

---

### Stage 7: RAG Retrieval Step

**Trigger**: Agent determines knowledge retrieval needed

**Components Used**:
- `src/core/rag/` - RAG System
- `src/core/postgresql_database/` - Vector database
- `src/integrations/otel_integration/` - OTEL for RAG tracing

**What is Consumed**:
- Query text (from incident description or agent-generated query)
- Tenant context
- Retrieval parameters (top_k, similarity_threshold)

**What is Produced**:
- Retrieved document chunks with embeddings
- Relevance scores
- Source metadata

**Mandatory Metadata**:
- `tenant_id` - From message envelope
- `correlation_id` - From message envelope
- `trace_id` - From OTEL trace context
- `query_id` - Generated query identifier

**Validations**:
- RAG query validation: Query text non-empty, parameters within bounds
- Vector DB connection: Database connection healthy
- Tenant isolation: Vector search scoped to tenant_id

**Logs/Metrics/Traces**:
- Log: `INFO: RAG query executed: query_id=query_101, tenant_id=tenant_123, results_count=5, correlation_id=corr_456`
- Metric: `rag.queries.executed` (counter, labels: tenant_id)
- Metric: `rag.query.duration` (histogram, seconds)
- Metric: `rag.retrieval.results_count` (histogram)
- Metric: `rag.vector.search.duration` (histogram, milliseconds)
- Trace: Child span `rag.query` with child spans:
  - `rag.embedding.generate` (attributes: `embedding.model`, `embedding.dimensions`)
  - `rag.vector.search` (attributes: `results.count`, `similarity.threshold`)
  - `rag.context.build` (attributes: `context.length`, `chunks.count`)

---

### Stage 8: LiteLLM Call Step

**Trigger**: Agent or RAG determines LLM generation needed

**Components Used**:
- `src/core/litellm_gateway/` - LiteLLM Gateway
- `src/core/cache_mechanism/` - Cache for LLM responses
- `src/integrations/otel_integration/` - OTEL for LLM tracing

**What is Consumed**:
- Prompt text (from prompt management or agent)
- Model name (e.g., "gpt-4", "claude-3-opus")
- Generation parameters (temperature, max_tokens)

**What is Produced**:
- LLM-generated text response
- Token usage metadata (prompt_tokens, completion_tokens, total_tokens)
- Cost metadata (USD)
- Cached response (if cache hit)

**Mandatory Metadata**:
- `tenant_id` - From message envelope
- `correlation_id` - From message envelope
- `trace_id` - From OTEL trace context
- `request_id` - Generated LLM request identifier
- `model` - LLM model name

**Validations**:
- LLM request validation: Prompt non-empty, model supported, parameters valid
- Rate limiting: Request within rate limits for tenant/model
- Circuit breaker: Provider healthy (not in open state)

**Logs/Metrics/Traces**:
- Log: `INFO: LLM request: request_id=req_202, model=gpt-4, tenant_id=tenant_123, correlation_id=corr_456`
- Log: `INFO: LLM response: request_id=req_202, tokens=150, cost=0.01, duration=2.5s, correlation_id=corr_456`
- Metric: `llm.requests.queued` (counter, labels: model, tenant_id)
- Metric: `llm.requests.completed` (counter, labels: model, status)
- Metric: `llm.request.duration` (histogram, seconds, labels: model)
- Metric: `llm.tokens.used` (histogram, labels: token_type)
- Metric: `llm.cost` (histogram, USD, labels: model)
- Metric: `llm.cache.hit_rate` (gauge, percentage)
- Trace: Child span `llm.generate` with attributes:
  - `llm.model`: "gpt-4"
  - `llm.provider`: "openai"
  - `llm.tokens.prompt`: 100
  - `llm.tokens.completion`: 50
  - `llm.tokens.total`: 150
  - `llm.cost.usd`: 0.01
  - `llm.cache.hit`: false

---

### Stage 9: Post-Processing/Guardrails Step

**Trigger**: LLM response received

**Components Used**:
- `src/core/prompt_context_management/` - Prompt Management
- `src/core/validation/` - Validation and guardrails
- `src/integrations/otel_integration/` - OTEL for validation tracing

**What is Consumed**:
- LLM-generated text
- Validation rules
- Formatting templates

**What is Produced**:
- Validated and formatted response
- Validation metadata (passed/failed rules)
- Formatted output (JSON, structured text)

**Mandatory Metadata**:
- `tenant_id` - From message envelope
- `correlation_id` - From message envelope
- `trace_id` - From OTEL trace context
- `validation_status` - Pass/fail
- `validation_rules_applied` - List of rules checked

**Validations**:
- Content validation: Response meets quality thresholds
- Guardrail validation: Response passes policy checks (toxicity, PII, compliance)
- Format validation: Response matches expected output format
- Token limit validation: Response within token limits

**Logs/Metrics/Traces**:
- Log: `INFO: Validation passed: correlation_id=corr_456, rules_applied=3`
- Log: `WARN: Validation failed: correlation_id=corr_456, rule=toxicity_check, reason=high_score`
- Metric: `validation.checks.executed` (counter, labels: rule_type)
- Metric: `validation.passed` (counter)
- Metric: `validation.failed` (counter, labels: rule_type, reason)
- Trace: Child span `validation.check` with attributes:
  - `validation.rules.applied`: ["toxicity", "pii", "compliance"]
  - `validation.status`: "passed"
  - `validation.duration`: 0.05

---

### Stage 10: CODEC Encode + Schema Version Stamping

**Trigger**: Validated response ready for publishing

**Components Used**:
- `src/integrations/codec_integration/` - CODEC serializer wrapper

**What is Consumed**:
- Response data (enriched incident analysis)
- Schema version (from registry)

**What is Produced**:
- Encoded message envelope (bytes) with structure:
  ```python
  {
    "message_type": "incident_triage_response",
    "spec_version": "1.0",
    "tenant_id": "tenant_123",
    "correlation_id": "corr_456",
    "timestamp": "2024-01-15T10:30:15Z",
    "payload": {
      "incident_id": "INC-12345",
      "ai_analysis": {
        "predicted_category": "infrastructure",
        "suggested_resolution": "Check server health metrics",
        "risk_assessment": "high",
        "confidence_score": 0.92
      },
      "knowledge_sources": ["KB-001", "KB-045"],
      "processing_metadata": {
        "agent_id": "agent_triage_001",
        "llm_model": "gpt-4",
        "tokens_used": 150,
        "processing_duration": 3.2
      }
    }
  }
  ```

**Mandatory Metadata**:
- `message_type` - Response message type (must match schema)
- `spec_version` - Schema version (from registry, e.g., "1.0")
- `tenant_id` - From original request (must match)
- `correlation_id` - From original request (must match)
- `timestamp` - Current timestamp (ISO 8601)

**Validations**:
- CODEC schema validation: Response structure matches schema registry definition
- Schema version check: Version exists in registry
- Field validation: Required fields present, types correct
- Correlation ID consistency: Matches original request correlation_id

**Logs/Metrics/Traces**:
- Log: `INFO: Message encoded: message_type=incident_triage_response, spec_version=1.0, correlation_id=corr_456`
- Metric: `codec.encode.attempts` (counter)
- Metric: `codec.encode.success` (counter)
- Metric: `codec.encode.duration` (histogram, milliseconds)
- Metric: `codec.encode.failures` (counter, labels: error_type)
- Trace: Child span `codec.encode` with attributes:
  - `codec.message_type`: "incident_triage_response"
  - `codec.spec_version`: "1.0"
  - `codec.encode.success`: true

---

### Stage 11: NATS Publish of Output Event

**Trigger**: Encoded message envelope ready

**Components Used**:
- `src/integrations/nats_integration/` - NATS client wrapper
- NATS broker (external)

**What is Consumed**:
- Encoded message envelope (bytes)
- NATS subject pattern
- NATS headers

**What is Produced**:
- Published NATS message to `ai.incident.triage.response.{tenant_id}`
- NATS publish acknowledgment

**Mandatory Metadata**:
- NATS subject: `ai.incident.triage.response.{tenant_id}` (tenant_id from envelope)
- NATS headers:
  - `X-Correlation-ID`: From envelope correlation_id
  - `traceparent`: W3C Trace Context (from OTEL trace)
  - `X-Message-Type`: From envelope message_type
  - `X-Schema-Version`: From envelope spec_version

**Validations**:
- NATS subject validation: Subject matches expected pattern
- NATS header validation: Required headers present
- Tenant isolation: Subject includes tenant_id

**Logs/Metrics/Traces**:
- Log: `INFO: Message published: subject=ai.incident.triage.response.tenant_123, correlation_id=corr_456`
- Metric: `nats.messages.published` (counter, labels: tenant_id, subject)
- Metric: `nats.publish.duration` (histogram, milliseconds)
- Metric: `nats.publish.failures` (counter, labels: error_type)
- Trace: Child span `nats.publish` with attributes:
  - `nats.subject`: "ai.incident.triage.response.tenant_123"
  - `nats.tenant_id`: "tenant_123"
  - `nats.correlation_id`: "corr_456"

---

### Stage 12: Downstream Consumption Expectations (Contract Compliance)

**Trigger**: Downstream service subscribes to response subject

**Components Used**:
- Downstream consumer service (external)
- NATS broker (external)

**What is Consumed**:
- Published message from AI SDK
- Message envelope (decoded by downstream service)

**Contract Compliance Requirements**:
- **Message Structure**: Envelope matches schema registry definition
- **Schema Version**: Version is supported by downstream service
- **Required Fields**: All mandatory fields present and non-null
- **Field Types**: Field types match schema definition
- **Tenant Isolation**: Message tenant_id matches subscription tenant_id
- **Correlation ID**: Correlation ID present for request-response matching
- **Timestamp**: Timestamp present and valid ISO 8601 format

**Backward Compatibility**:
- **Schema Evolution**: New schema versions must be backward compatible (additive changes only)
- **Version Support**: Downstream services support multiple schema versions (e.g., 1.0, 1.1)
- **Migration Path**: Schema registry provides migration functions for version upgrades

**Logs/Metrics/Traces**:
- (Downstream service logs/metrics, not AI SDK responsibility)
- AI SDK ensures contract compliance through validation gates

---

## Message Contract Model

### Envelope Format (Conceptual)

```json
{
  "message_type": "string",           // e.g., "incident_triage_request"
  "spec_version": "string",           // e.g., "1.0" (schema version)
  "tenant_id": "string",              // Tenant identifier
  "correlation_id": "string",         // Request correlation ID
  "timestamp": "string",               // ISO 8601 timestamp
  "payload": {                        // Message-specific payload
    // ... payload fields ...
  },
  "error": {                          // Present only on errors
    "error_code": "string",
    "error_message": "string",
    "error_details": {}
  }
}
```

### Schema Version Evolution

**Backward Compatible Changes**:
- Adding new optional fields
- Adding new enum values (if enum is not closed)
- Widening field types (e.g., int → float)

**Breaking Changes** (require new version):
- Removing fields
- Renaming fields
- Narrowing field types
- Changing required fields to optional (or vice versa)

**Version Migration**:
- CODEC registry maintains migration functions for each version transition
- Automatic migration applied during decode if version mismatch detected
- Migration functions are tested and validated in contract fixture tests

---

## Observability Model (OTEL)

### Trace Structure

```
Root Span: nats.consume
├─ Attributes:
│  ├─ nats.subject: "ai.incident.triage.request.tenant_123"
│  ├─ nats.tenant_id: "tenant_123"
│  ├─ nats.correlation_id: "corr_456"
│  └─ message_type: "incident_triage_request"
│
├─ Child Span: codec.decode
│  ├─ Attributes:
│  │  ├─ codec.message_type: "incident_triage_request"
│  │  ├─ codec.spec_version: "1.0"
│  │  └─ codec.decode.success: true
│  │
├─ Child Span: ai.incident.triage.process
│  ├─ Attributes:
│  │  ├─ tenant_id: "tenant_123"
│  │  ├─ correlation_id: "corr_456"
│  │  └─ incident_id: "INC-12345"
│  │
│  ├─ Child Span: agent.task.execute
│  │  ├─ Attributes:
│  │  │  ├─ agent.id: "agent_triage_001"
│  │  │  ├─ agent.task.id: "task_789"
│  │  │  └─ agent.task.type: "incident_triage"
│  │  │
│  ├─ Child Span: rag.query
│  │  ├─ Attributes:
│  │  │  ├─ rag.tenant_id: "tenant_123"
│  │  │  └─ rag.query.length: 50
│  │  │
│  │  ├─ Child Span: rag.embedding.generate
│  │  │  ├─ Attributes:
│  │  │  │  ├─ embedding.model: "text-embedding-3-small"
│  │  │  │  └─ embedding.dimensions: 1536
│  │  │  │
│  │  ├─ Child Span: rag.vector.search
│  │  │  ├─ Attributes:
│  │  │  │  ├─ results.count: 5
│  │  │  │  └─ similarity.threshold: 0.7
│  │  │  │
│  ├─ Child Span: llm.generate
│  │  ├─ Attributes:
│  │  │  ├─ llm.model: "gpt-4"
│  │  │  ├─ llm.provider: "openai"
│  │  │  ├─ llm.tokens.prompt: 100
│  │  │  ├─ llm.tokens.completion: 50
│  │  │  ├─ llm.tokens.total: 150
│  │  │  ├─ llm.cost.usd: 0.01
│  │  │  └─ llm.cache.hit: false
│  │  │
│  ├─ Child Span: validation.check
│  │  ├─ Attributes:
│  │  │  ├─ validation.rules.applied: ["toxicity", "pii", "compliance"]
│  │  │  └─ validation.status: "passed"
│  │  │
│  ├─ Child Span: codec.encode
│  │  ├─ Attributes:
│  │  │  ├─ codec.message_type: "incident_triage_response"
│  │  │  └─ codec.spec_version: "1.0"
│  │  │
│  └─ Child Span: nats.publish
    ├─ Attributes:
       ├─ nats.subject: "ai.incident.triage.response.tenant_123"
       └─ nats.correlation_id: "corr_456"
```

### Correlation ID and Trace ID Usage

- **Correlation ID**: Used for log correlation across services. Present in all logs and trace attributes.
- **Trace ID**: Used for distributed tracing across services. Extracted from/propagated via NATS headers.
- **Debugging**: Query logs by correlation_id or traces by trace_id to see full request flow across AI SDK and downstream services.

---

## Error Handling + DLQ Story

### Error Scenarios and Handling

#### 1. Decode/Schema Failure

**Error**: CODEC decode fails or schema validation fails

**Handling**:
1. Log error with correlation_id and error details
2. Emit metric: `codec.decode.failures` (counter, labels: error_type)
3. Create error span with error status
4. Publish to DLQ subject: `ai.incident.triage.failed.{tenant_id}` with error envelope:
   ```json
   {
     "message_type": "incident_triage_failed",
     "spec_version": "1.0",
     "tenant_id": "tenant_123",
     "correlation_id": "corr_456",
     "timestamp": "2024-01-15T10:30:00Z",
     "error": {
       "error_code": "DECODE_FAILED",
       "error_message": "Schema validation failed: missing required field 'incident_id'",
       "error_details": {
         "original_subject": "ai.incident.triage.request.tenant_123",
         "schema_version": "1.0",
         "validation_errors": ["missing_field: incident_id"]
       }
     }
   }
   ```

#### 2. Timeout from LLM

**Error**: LiteLLM Gateway timeout (e.g., 30 seconds exceeded)

**Handling**:
1. Log warning with correlation_id and timeout duration
2. Emit metric: `llm.requests.timeout` (counter, labels: model)
3. Update trace span with error status
4. Circuit breaker: Check if provider should be marked as unhealthy
5. Retry logic: If retries available, retry with exponential backoff
6. If all retries exhausted, publish to DLQ: `ai.incident.triage.failed.{tenant_id}` with error envelope:
   ```json
   {
     "message_type": "incident_triage_failed",
     "error": {
       "error_code": "LLM_TIMEOUT",
       "error_message": "LLM request timed out after 30 seconds",
       "error_details": {
         "model": "gpt-4",
         "timeout_seconds": 30,
         "retry_count": 3
       }
     }
   }
   ```

#### 3. Vector DB Failure

**Error**: PostgreSQL connection failure or query timeout

**Handling**:
1. Log error with correlation_id and database error details
2. Emit metric: `rag.database.errors` (counter, labels: error_type)
3. Fallback strategy: Attempt keyword search (if available)
4. If fallback fails, continue with empty RAG results (agent can proceed without knowledge)
5. Update trace span with warning (not error, as fallback succeeded)
6. No DLQ routing (non-fatal error, processing continues)

#### 4. Agent Failure

**Error**: Agent task execution fails (exception, invalid state)

**Handling**:
1. Log error with correlation_id, agent_id, and error details
2. Emit metric: `agent.tasks.failed` (counter, labels: agent_id, error_type)
3. Update trace span with error status
4. Publish partial result (if available) or failure event to DLQ: `ai.incident.triage.failed.{tenant_id}` with error envelope:
   ```json
   {
     "message_type": "incident_triage_failed",
     "error": {
       "error_code": "AGENT_FAILED",
       "error_message": "Agent task execution failed: Invalid agent state",
       "error_details": {
         "agent_id": "agent_triage_001",
         "task_id": "task_789",
         "error_type": "InvalidStateError"
       }
     }
   }
   ```

### DLQ Routing

**DLQ Subject Pattern**: `ai.{component}.{operation}.failed.{tenant_id}`

**DLQ Message Structure**: Same envelope format with `error` field populated

**DLQ Consumer**: Separate service/process subscribes to DLQ subjects for:
- Error analysis and alerting
- Retry logic (if applicable)
- Dead letter archival

---

## Validation Gates Inside AI SDK Repo

### Automated Checks (Week-by-Week Progress Validation)

#### 1. Unit Tests

**Location**: `src/tests/unit_tests/`

**Coverage**:
- CODEC helpers: Encode/decode functions, schema validation, version migration
- Wrapper usage: NATS client wrapper, OTEL tracer wrapper, CODEC serializer wrapper
- Span helpers: Trace context extraction, span creation, attribute setting

**Validation Criteria**:
- All unit tests pass (100% pass rate)
- Code coverage > 80% for integration modules
- Test execution time < 30 seconds

#### 2. Integration Tests (Docker NATS End-to-End)

**Location**: `src/tests/integration_tests/test_nats_integration.py`, `test_otel_integration.py`, `test_codec_integration.py`

**Coverage**:
- NATS pub/sub with real NATS broker (Docker container)
- OTEL trace propagation through NATS messages
- CODEC encode/decode round-trip with schema validation
- Multi-tenant isolation (multiple tenants, separate subjects)
- Error scenarios (connection failures, timeouts, invalid messages)

**Validation Criteria**:
- All integration tests pass (100% pass rate)
- Tests run against real NATS broker (not mocks)
- Test execution time < 5 minutes

#### 3. Contract Fixture Decode Tests

**Location**: `src/tests/integration_tests/test_codec_integration.py`

**Coverage**:
- All registered schemas in schema registry
- All schema versions (current and previous)
- Backward compatibility (old messages decode with new code)
- Forward compatibility (new messages decode with migration)

**Validation Criteria**:
- All contract fixtures decode successfully
- Schema version migration functions tested
- No breaking changes detected

#### 4. OTEL Propagation Tests

**Location**: `src/tests/integration_tests/test_otel_integration.py`

**Coverage**:
- Trace context extraction from NATS headers
- Trace context injection into NATS headers
- Trace propagation across components (Agent → RAG → Gateway)
- Trace export to OTEL collector

**Validation Criteria**:
- Trace context round-trip successful (extract → process → inject)
- Traces visible in OTEL collector/backend
- Trace attributes correctly set

#### 5. Benchmark Smoke Tests

**Location**: `src/tests/benchmarks/benchmark_nats_performance.py`, `benchmark_codec_serialization.py`

**Coverage**:
- CODEC latency: Encode/decode operations < 1ms P95
- NATS publish/consume throughput: > 100 msg/sec
- OTEL overhead: < 5% tracing overhead, < 2% metrics overhead

**Validation Criteria**:
- Performance targets met (assertions in benchmark tests)
- Benchmark results logged and tracked
- Performance regressions detected and flagged

---

## Sequence Diagram

```
Upstream Service          NATS Broker          AI SDK Runtime          Vector DB          LLM Provider
     |                        |                       |                    |                    |
     |--[1] Publish Event---->|                       |                    |                    |
     |   (ai.incident.triage  |                       |                    |                    |
     |    .request.tenant_123)|                       |                    |                    |
     |                        |                       |                    |                    |
     |                        |--[2] Message---------->|                    |                    |
     |                        |   (headers + payload) |                    |                    |
     |                        |                       |                    |                    |
     |                        |                       |--[3] CODEC Decode   |                    |
     |                        |                       |   + Validation     |                    |
     |                        |                       |                    |                    |
     |                        |                       |--[4] OTEL Extract  |                    |
     |                        |                       |   Trace Context    |                    |
     |                        |                       |   + Create Span    |                    |
     |                        |                       |                    |                    |
     |                        |                       |--[5] Agent Execute|                    |
     |                        |                       |   Task             |                    |
     |                        |                       |                    |                    |
     |                        |                       |--[6] RAG Query---->|                    |
     |                        |                       |   (vector search)  |                    |
     |                        |                       |<--[7] Results------|                    |
     |                        |                       |                    |                    |
     |                        |                       |--[8] LLM Generate----------------->|
     |                        |                       |   (prompt + context)                 |
     |                        |                       |<--[9] Response---------------------|
     |                        |                       |   (text + tokens)                   |
     |                        |                       |                    |                    |
     |                        |                       |--[10] Validate +   |                    |
     |                        |                       |    Format          |                    |
     |                        |                       |                    |                    |
     |                        |                       |--[11] CODEC Encode |                    |
     |                        |                       |   + Schema Version |                    |
     |                        |                       |                    |                    |
     |                        |<--[12] Publish--------|                    |                    |
     |                        |   (ai.incident.triage |                    |                    |
     |                        |    .response.tenant_  |                    |                    |
     |                        |    123)               |                    |                    |
     |                        |                       |                    |                    |
Downstream Service          |                       |                    |                    |
     |<--[13] Consume---------|                       |                    |                    |
     |   (enriched event)     |                       |                    |                    |
```

**Error Path (Example: LLM Timeout)**:
```
     |                        |                       |                    |                    |
     |                        |                       |--[8] LLM Generate----------------->|
     |                        |                       |   (timeout after 30s)              |
     |                        |                       |<--[ERROR] Timeout------------------|
     |                        |                       |                    |                    |
     |                        |                       |--[RETRY] LLM Generate------------->|
     |                        |                       |   (exponential backoff)            |
     |                        |                       |<--[ERROR] Timeout------------------|
     |                        |                       |                    |                    |
     |                        |                       |--[DLQ] Publish Failure------------>|
     |                        |<--[Publish]-----------|                    |                    |
     |                        |   (ai.incident.triage |                    |                    |
     |                        |    .failed.tenant_123)|                    |                    |
```

---

## Conclusion

The AI SDK operates as a deterministic, observable, and contract-compliant message-driven system where NATS provides reliable messaging, OTEL provides distributed observability, and CODEC provides schema-versioned serialization. Each stage of the execution pipeline is validated, traced, and monitored, ensuring that AI capabilities are delivered with enterprise-grade reliability and debuggability. Weekly validation gates prove continuous progress through automated testing, benchmarking, and contract compliance verification.

