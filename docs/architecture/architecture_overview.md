# Architecture Overview - Simple Explanation

## What is This Document?

This document explains how data flows through the SDK in simple terms. No heavy theory - just practical understanding.

---

## High-Level Flow

```
User Request
    ↓
[Your Application Code]
    ↓
[SDK Components]
    ↓
[AI Services / Database]
    ↓
Response Back to User
```

---

## Component Flow (Step-by-Step)

### 1. Simple AI Text Generation

**What happens:**
1. Your code calls `gateway.generate_async("Hello")`
2. Gateway checks cache (if enabled) → if found, return cached response
3. Gateway checks rate limits → if exceeded, queue the request
4. Gateway calls LLM provider (OpenAI, Anthropic, etc.)
5. Gateway receives response, stores in cache (if enabled)
6. Gateway returns response to your code
7. Your code displays response to user

**Time:** ~1-3 seconds
**Cost:** ~$0.001-0.01 per request (depends on model)

---

### 2. Conversational Agent

**What happens:**
1. User sends message: "What's the weather?"
2. Agent receives message, loads conversation history from memory
3. Agent builds prompt with: system prompt + history + current message
4. Agent calls Gateway to get AI response
5. Agent stores conversation in memory
6. Agent returns response to user

**Components used:**
- Agent Framework (manages conversation)
- Gateway (calls AI)
- Memory System (stores history)

**Time:** ~2-4 seconds
**Cost:** ~$0.002-0.02 per message

---

### 3. Document Q&A (RAG)

**What happens:**
1. User asks: "What's in document X?"
2. RAG System converts question to embedding (vector)
3. RAG searches database for similar document chunks
4. RAG retrieves top 3-5 relevant chunks
5. RAG builds prompt: question + retrieved chunks
6. RAG calls Gateway to generate answer
7. RAG returns answer to user

**Components used:**
- RAG System (retrieval + generation)
- Gateway (embeddings + text generation)
- Database (stores documents + vectors)

**Time:** ~3-5 seconds
**Cost:** ~$0.003-0.03 per query

---

## Data Flow Diagrams

### Simple Request Flow

```
┌─────────────┐
│   Your App  │
└──────┬──────┘
       │
       │ 1. generate_async("Hello")
       ▼
┌─────────────┐
│   Gateway   │───┐
└──────┬──────┘   │
       │          │ 2. Check cache
       │          │    (if miss, continue)
       │          │
       │ 3. Call LLM Provider
       ▼          │
┌─────────────┐   │
│   OpenAI    │   │
│  /Anthropic │   │
└──────┬──────┘   │
       │          │
       │ 4. Response
       ▼          │
┌─────────────┐   │
│   Gateway   │◄──┘ 5. Store in cache
└──────┬──────┘
       │
       │ 6. Return response
       ▼
┌─────────────┐
│   Your App  │
└─────────────┘
```

### Agent Conversation Flow

```
┌─────────────┐
│    User     │
└──────┬──────┘
       │ "Hello"
       ▼
┌─────────────┐
│   Agent     │───┐
└──────┬──────┘   │
       │          │ 1. Load history
       │          │    from memory
       │          │
       │ 2. Build prompt
       ▼          │
┌─────────────┐   │
│   Gateway   │   │
└──────┬──────┘   │
       │          │
       │ 3. AI response
       ▼          │
┌─────────────┐   │
│   Agent     │◄──┘ 4. Save to memory
└──────┬──────┘
       │
       │ 5. Return response
       ▼
┌─────────────┐
│    User     │
└─────────────┘
```

### RAG Query Flow

```
┌─────────────┐
│    User     │
└──────┬──────┘
       │ "What is X?"
       ▼
┌─────────────┐
│  RAG System │
└──────┬──────┘
       │
       │ 1. Convert query to embedding
       ▼
┌─────────────┐
│   Gateway   │ (embedding)
└──────┬──────┘
       │
       │ 2. Vector search
       ▼
┌─────────────┐
│  Database   │ (pgvector)
└──────┬──────┘
       │
       │ 3. Retrieve top chunks
       ▼
┌─────────────┐
│  RAG System │
└──────┬──────┘
       │
       │ 4. Build prompt with chunks
       ▼
┌─────────────┐
│   Gateway   │ (text generation)
└──────┬──────┘
       │
       │ 5. Return answer
       ▼
┌─────────────┐
│    User     │
└─────────────┘
```

---

## Component Responsibilities

### Gateway
- **Does:** Calls AI services, manages rate limits, caches responses
- **Doesn't:** Store conversations, search documents, manage agents

### Agent Framework
- **Does:** Manages conversations, executes tasks, coordinates agents
- **Doesn't:** Generate embeddings, store documents, handle HTTP requests

### RAG System
- **Does:** Searches documents, generates context-aware answers
- **Doesn't:** Manage conversations, execute tasks, handle HTTP requests

### Cache
- **Does:** Stores responses temporarily, reduces costs
- **Doesn't:** Generate AI responses, store permanent data

### Database
- **Does:** Stores documents, vectors, metadata permanently
- **Doesn't:** Generate AI responses, manage conversations

---

## Common Patterns

### Pattern 1: Simple Chatbot
```
User → Agent → Gateway → AI Provider → Response
```

### Pattern 2: Document Q&A
```
User → RAG → Gateway (embedding) → Database → Gateway (generation) → Response
```

### Pattern 3: Cost-Optimized Chatbot
```
User → Agent → Cache → Gateway (if cache miss) → AI Provider → Cache → Response
```

### Pattern 4: Multi-Agent System
```
User → Agent A → Gateway
              → Agent B (delegation) → Gateway
              → Agent C (coordination) → Gateway
              → Combined Response
```

---

## Performance Characteristics

| Operation | Typical Time | Cost per Request |
|-----------|-------------|------------------|
| Simple AI call | 1-3 seconds | $0.001-0.01 |
| Agent conversation | 2-4 seconds | $0.002-0.02 |
| RAG query | 3-5 seconds | $0.003-0.03 |
| Cached response | <0.1 seconds | $0 (free) |

**Note:** Times and costs vary based on:
- Model used (GPT-4 is slower/expensive, GPT-3.5 is faster/cheaper)
- Query complexity
- Document size (for RAG)
- Network latency

---

## Error Handling Flow

```
Request
  ↓
Try Component Operation
  ↓
Success? → Return Result
  ↓
No → Check Error Type
  ↓
Retryable? → Retry (with backoff)
  ↓
No → Return Error to User
```

**Common Errors:**
- **Rate Limit:** SDK automatically queues and retries
- **Network Error:** SDK retries with exponential backoff
- **Invalid Input:** SDK returns clear error message
- **Provider Error:** SDK can fallback to another provider (if configured)

---

## Multi-Tenancy Flow

```
Request (with tenant_id)
  ↓
All Components Check tenant_id
  ↓
Data Isolation:
  - Cache keys include tenant_id
  - Database queries filter by tenant_id
  - Memory is isolated per tenant
  ↓
Response (tenant-specific)
```

**Key Point:** All components automatically handle tenant isolation. Just pass `tenant_id` in your requests.

---

## Summary

1. **Gateway** = Your connection to AI services
2. **Agent** = Manages conversations and tasks
3. **RAG** = Answers questions from documents
4. **Cache** = Saves money and speeds things up
5. **Database** = Stores your data permanently

**Simple Rule:**
- Need AI? → Use Gateway
- Need conversations? → Use Agent
- Need document Q&A? → Use RAG
- Want to save money? → Use Cache

For more details, see each component's README.

