# SDK Workflows

## Visual Workflow Representation

This document provides a comprehensive visual and textual representation of the entire SDK workflow, detailing how components interact with each other.

## High-Level Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Request                             │
│                    (Query, Task, or API Call)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              API Backend Services (src/core/)                    │
│    (Request Validation & Routing - Unified Query Endpoint)      │
│              (Auto-routing: Agent/RAG/Both)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
    ┌───────────────────┐    ┌───────────────────┐
    │  Agent Framework  │    │   RAG System      │
    │  (src/core/)      │    │  (src/core/)      │
    │  + Memory         │    │  + Memory         │
    └─────────┬─────────┘    └─────────┬─────────┘
              │                        │
              │                        │
    ┌─────────▼─────────┐    ┌─────────▼─────────┐
    │  LiteLLM Gateway │    │  Vector Database  │
    │  (src/core/)     │    │  (src/core/)      │
    │  + Cache         │    │                   │
    └─────────┬─────────┘    └─────────┬─────────┘
              │                        │
              └────────────┬───────────┘
                           │
                           ▼
              ┌──────────────────────┐
              │  PostgreSQL Database │
              │  (src/core/)         │
              └──────────────────────┘
                           │
                           ▼
    ┌──────────────────────────────────────┐
    │  Connectivity Clients (root/)       │
    │  Pool Implementation (root/)        │
    │  Governance Framework (root/)        │
    └──────────────────────────────────────┘
```

## Component Interaction Workflows

### 1. RAG Query Workflow

```
User Query
    │
    ▼
API Backend Services (Validate Request)
    │
    ▼
RAG System (src/core/rag/)
    │
    ├─→ Agent Memory (Retrieve Conversation Context, if enabled)
    │   ├─→ Episodic Memory (Previous queries/answers)
    │   └─→ Semantic Memory (User preferences, patterns)
    │
    ├─→ Query Rewriting (Optional: Expand abbreviations, normalize)
    │
    ├─→ Cache Mechanism (Check Cache for Query Results)
    │
    ├─→ Prompt Context Management (Build Prompt with Memory Context)
    │
    ├─→ LiteLLM Gateway (Generate Query Embedding)
    │   └─→ Gateway Cache (Check cache before API call)
    │
    ├─→ Retriever
    │   ├─→ Vector Database (Similarity Search)
    │   ├─→ Keyword Search (Optional: Hybrid retrieval)
    │   └─→ Metadata Filtering (Filter by metadata)
    │
    ├─→ PostgreSQL Database (Retrieve Documents with Metadata)
    │
    ├─→ Context Building (Assemble retrieved documents + memory context)
    │
    ├─→ LiteLLM Gateway (Generate Response with Context)
    │   └─→ Gateway Cache (Store response in cache)
    │
    ├─→ Agent Memory (Store Query-Answer Pair in Episodic Memory)
    │
    ├─→ Cache Mechanism (Store Query Result)
    │
    └─→ Evaluation & Observability (Log & Trace)
    │
    ▼
Response to User
```

### 2. Agent Task Execution Workflow

```
Agent Task
    │
    ▼
Agent Framework
    │
    ├─→ Agent Manager (Route to Agent)
    │
    ├─→ Agent (Execute Task)
    │
    ├─→ LiteLLM Gateway (LLM Reasoning)
    │   └─→ Gateway Cache (Check cache before API call, store after)
    │
    ├─→ RAG System (Knowledge Retrieval, if needed)
    │   └─→ RAG Memory (Retrieve conversation context)
    │
    ├─→ Database (Store Results)
    │
    └─→ Evaluation & Observability (Track Execution)
    │
    ▼
Task Result
```

### 3. Document Ingestion Workflow

```
Document Input
    │
    ▼
RAG System
    │
    ├─→ Document Processor
    │   │
    │   ├─→ Load Document (Multiple formats: text, HTML, JSON)
    │   │
    │   ├─→ Preprocessing Pipeline
    │   │   ├─→ Text Normalization
    │   │   ├─→ Whitespace Cleaning
    │   │   └─→ Unicode Normalization
    │   │
    │   ├─→ Metadata Extraction
    │   │   ├─→ Title Extraction
    │   │   ├─→ Date Extraction
    │   │   ├─→ Tag/Keyword Extraction
    │   │   ├─→ Language Detection
    │   │   └─→ File Metadata (name, size, extension)
    │   │
    │   ├─→ Metadata Validation (Schema-based)
    │   │
    │   ├─→ Chunking (Multiple strategies: fixed, sentence, paragraph, semantic)
    │   │
    │   ├─→ Chunk Validation
    │   │   ├─→ Size Validation (min/max)
    │   │   └─→ Content Quality Checks
    │   │
    │   └─→ Metadata Enrichment (Document → Chunk metadata)
    │
    ├─→ LiteLLM Gateway (Batch Generate Embeddings)
    │
    ├─→ PostgreSQL Database (Store Document with Metadata)
    │
    ├─→ Vector Database (Store Embeddings)
    │
    └─→ Cache Mechanism (Invalidate Cache)
    │
    ▼
Document Stored
```

### 4. Multi-Agent Coordination Workflow

```
Complex Task
    │
    ▼
Coordination Agent
    │
    ├─→ Task Decomposition
    │
    ├─→ Agent Selection
    │
    ├─→ Task Distribution
    │       │
    │       ├─→ Agent 1 (Sub-task 1)
    │       ├─→ Agent 2 (Sub-task 2)
    │       └─→ Agent 3 (Sub-task 3)
    │
    ├─→ Result Aggregation
    │
    └─→ Final Result
    │
    ▼
Completed Task
```

## Data Flow Workflows

### Request Flow

```
1. User Request
   ↓
2. API Backend (Validate & Route)
   ↓
   ├─→ Unified Query Endpoint (Auto-routing: Agent/RAG/Both)
   └─→ Component-Specific Endpoints (Direct routing)
   ↓
3. Component Selection (Agent/RAG/Other)
   ↓
4. Component Processing
   ├─→ Memory Retrieval (if enabled)
   ├─→ Cache Check (Gateway cache, RAG cache)
   └─→ Context Building
   ↓
5. Gateway/Database Operations
   ├─→ Gateway Cache (Check before API call, store after)
   └─→ Database Queries
   ↓
6. Response Generation
   ├─→ Memory Storage (Store query-answer pairs)
   └─→ Cache Storage (Store results)
   ↓
7. Observability Logging
   ↓
8. Response to User
```

### Error Handling Flow

```
Operation
    │
    ├─→ Success → Continue
    │
    └─→ Error
         │
         ├─→ Retry Logic
         │   │
         │   ├─→ Success → Continue
         │   └─→ Failure → Fallback
         │
         └─→ Fallback Mechanism
             │
             ├─→ Alternative Provider
             ├─→ Cached Response
             └─→ Error Response
```

## Connection Management Workflow

```
Connection Request
    │
    ▼
Pool Implementation (root/pool_implementation/)
    │
    ├─→ Check Available Connection
    │   │
    │   ├─→ Available → Return Connection
    │   │
    │   └─→ Not Available
    │       │
    │       ├─→ Create New (if under max)
    │       │
    │       └─→ Wait for Release
    │
    ▼
Connection Usage
    │
    ▼
Connection Release
    │
    ▼
Return to Pool
```

## Caching Workflow

```
Request
    │
    ▼
Cache Check (Multiple Levels)
    │
    ├─→ Gateway Cache (LLM Response Cache)
    │   ├─→ Cache Hit → Return Cached Response (No API call)
    │   └─→ Cache Miss → Continue to LLM API call
    │
    ├─→ RAG Cache (Query Result Cache)
    │   ├─→ Cache Hit → Return Cached Result
    │   └─→ Cache Miss → Continue to RAG Processing
    │
    └─→ Memory Cache (Conversation Context)
        ├─→ Cache Hit → Use Cached Context
        └─→ Cache Miss → Build New Context
    │
    ▼
Execute Operation (if cache miss)
    │
    ▼
Store in Cache (Multiple Levels)
    ├─→ Gateway Cache (Store LLM response)
    ├─→ RAG Cache (Store query result)
    └─→ Memory Cache (Store conversation context)
    │
    ▼
Return Result
```

## Observability Workflow

```
Operation Start
    │
    ▼
Start Trace
    │
    ├─→ Log Operation Start
    │
    ├─→ Record Metrics
    │
    └─→ Track Context
         │
         ▼
    Operation Execution
         │
         ├─→ Log Events
         ├─→ Update Metrics
         └─→ Propagate Trace
         │
         ▼
    Operation Complete
         │
         ├─→ End Trace
         ├─→ Final Metrics
         └─→ Log Completion
```

## Integration Points

### Between Components

1. **Gateway ↔ Agents**: Agents use gateway for LLM operations (both in src/core/)
   - Gateway cache automatically checks/stores responses
2. **Gateway ↔ RAG**: RAG uses gateway for embeddings and generation (both in src/core/)
   - Gateway cache automatically checks/stores responses
3. **RAG ↔ Database**: RAG stores/retrieves documents and embeddings (both in src/core/)
4. **RAG ↔ Memory**: RAG integrates with Agent Memory for conversation context (both in src/core/)
   - Memory retrieval before query processing
   - Memory storage after query completion
5. **Agents ↔ Database**: Agents store tasks and results (both in src/core/)
6. **Cache ↔ All**: All components can use cache (src/core/)
   - Gateway cache: Automatic LLM response caching
   - RAG cache: Query result caching
   - Memory cache: Conversation context caching
7. **API Backend ↔ Agent/RAG**: Unified query endpoint orchestrates both (src/core/)
   - Automatic routing based on query type
   - Dual processing support (both Agent and RAG)
8. **Observability ↔ All**: All operations are traced and logged (src/core/)
9. **Pool ↔ Database**: Database uses pool for connections (root/ ↔ src/core/)
10. **Connectivity ↔ All**: All components use connectivity clients (root/ ↔ src/core/)
11. **Governance ↔ All**: Governance framework applies to all components (root/)

### External Services

1. **LLM Providers**: Via LiteLLM Gateway
2. **PostgreSQL**: Direct database connections
3. **Redis**: For caching (optional)
4. **Message Queues**: For async operations (optional)

## Workflow Best Practices

1. **Error Handling**: Implement at every step
2. **Retry Logic**: For transient failures
3. **Fallback Mechanisms**: Alternative paths on failure
4. **Monitoring**: Track all workflow steps
5. **Optimization**: Cache frequently accessed data
6. **Scalability**: Design for horizontal scaling

## Examples and Tests

### Working Examples

See `examples/` directory for working code examples demonstrating these workflows:

- **Basic Usage**: `examples/basic_usage/` - Examples for each component showing individual workflows
- **Integration**: `examples/integration/` - Examples showing multi-component workflows
- **End-to-End**: `examples/end_to_end/` - Complete workflow examples

### Test Suites

See `src/tests/` directory for comprehensive tests validating these workflows:

- **Unit Tests**: `src/tests/unit_tests/` - Component-specific workflow tests
- **Integration Tests**: `src/tests/integration_tests/` - Multi-component workflow tests

For detailed examples and test documentation, see:
- `examples/README.md` - Examples documentation
- `src/tests/unit_tests/README.md` - Unit tests documentation
- `src/tests/integration_tests/README.md` - Integration tests documentation

