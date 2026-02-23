# Orchestrator Service

**AI Entry Point with Intelligent Routing and Unified Caching**

## Overview

The Orchestrator Service provides a single entry point for all AI operations in the FaaS architecture. It intelligently routes user queries to the appropriate service based on intent analysis and provides unified caching across all AI features.

## Features

- **Intelligent Query Routing**: Automatically analyzes query intent and routes to the appropriate service (Agent, RAG, Gateway, etc.)
- **Unified Caching**: Caches responses across all AI features at the entry point, reducing costs and improving performance
- **Intent Analysis**: Uses LLM-based intent classification with pattern matching fallback
- **Service Selection**: Maps intents to service endpoints with automatic fallback
- **Cache Management**: Provides cache invalidation and management capabilities

## Architecture

```
User Query
    ↓
Orchestrator Service
    ↓
Query Router (Intent Analysis)
    ↓
Service Selector (Route Selection)
    ↓
Cache Check
    ↓
Service Call (Agent/RAG/Gateway/etc.)
    ↓
Cache Store
    ↓
Response
```

## API Endpoints

### POST `/api/v1/orchestrate`

Orchestrate a query - automatically routes to appropriate service.

**Request:**
```json
{
  "query": "Hello, how are you?",
  "context": {
    "agent_id": "agent_123",
    "session_id": "session_456"
  },
  "intent": "agent_chat",  // Optional, overrides analysis
  "cache_enabled": true,
  "stream": false
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "message": "Hello! I'm doing well, thank you."
  },
  "intent": "agent_chat",
  "service": "agent",
  "endpoint": "/api/v1/agents/agent_123/chat",
  "cached": false,
  "correlation_id": "corr_789",
  "request_id": "req_abc123"
}
```

### POST `/api/v1/intent/analyze`

Analyze query intent only (no routing).

**Request:**
```json
{
  "query": "Search documents about AI",
  "context": {
    "top_k": 5
  }
}
```

**Response:**
```json
{
  "intent": "rag_query",
  "confidence": 0.95,
  "reasoning": "Query contains document search keywords",
  "suggested_service": "rag",
  "suggested_endpoint": "/api/v1/rag/query"
}
```

### POST `/api/v1/cache/invalidate`

Invalidate cache entries.

**Request:**
```json
{
  "feature": "agent_chat",
  "tenant_id": "tenant_123",
  "pattern": "orchestrator:agent_chat:*"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Cache invalidated successfully"
}
```

## Query Intents

The orchestrator supports the following intents:

- `agent_chat`: Chat with an AI agent
- `agent_task`: Execute agent task
- `rag_query`: Query documents/knowledge base
- `direct_llm`: Direct LLM generation
- `document_ingestion`: Upload/ingest documents
- `prompt_generation`: Create agent/tool from prompt
- `ml_prediction`: ML model prediction
- `unknown`: Unknown intent (fallback to gateway)

## Caching Strategy

The orchestrator uses different caching strategies per feature:

- **Conversation Strategy**: For agent chat (includes session context)
- **Query Strategy**: For RAG queries, direct LLM, etc. (exact query match)
- **No Cache**: For document ingestion (always fresh)

Cache TTLs:
- Agent Chat: 5 minutes
- Agent Task: 10 minutes
- RAG Query: 1 hour
- Direct LLM: 30 minutes
- Prompt Generation: 24 hours
- ML Prediction: 30 minutes

## Configuration

Set the following environment variables:

```bash
ORCHESTRATOR_SERVICE_URL=http://orchestrator-service:8080
GATEWAY_SERVICE_URL=http://gateway-service:8080
AGENT_SERVICE_URL=http://agent-service:8080
RAG_SERVICE_URL=http://rag-service:8080
# ... other service URLs
DATABASE_URL=postgresql://user:pass@localhost/db
DRAGONFLY_URL=redis://localhost:6379
OPENAI_API_KEY=sk-...
```

## Usage Example

```python
from src.faas.services.orchestrator_service import OrchestratorService
from src.faas.shared.config import load_config

# Load configuration
config = load_config("orchestrator-service")

# Create service
service = OrchestratorService(
    config=config,
    db_connection=db,
)

# Service is ready to handle requests via FastAPI
```

## Benefits

1. **User Experience**: Users don't need to know which service to call
2. **Cost Optimization**: Unified caching reduces LLM API costs
3. **Performance**: Faster responses for cached queries
4. **Flexibility**: Easy to add new services without frontend changes
5. **SaaS Ready**: Natural language interface for users

