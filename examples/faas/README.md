# MOTADATA - FAAS SERVICE EXAMPLES

**Examples demonstrating how to use each FaaS service for microservices deployment.**

This directory contains examples demonstrating how to use each FaaS service.

## Examples

### 1. Agent Service Example
**File**: `agent_service_example.py`

Demonstrates:
- Creating an agent
- Executing tasks with an agent
- Chatting with an agent
- Listing agents

**Usage**:
```bash
# Start Agent Service first
uvicorn src.faas.services.agent_service.service:app --host 0.0.0.0 --port 8083

# Run example
python examples/faas/agent_service_example.py
```

### 2. RAG Service Example
**File**: `rag_service_example.py`

Demonstrates:
- Ingesting documents
- Querying the RAG system
- Performing vector search

**Usage**:
```bash
# Start RAG Service first
uvicorn src.faas.services.rag_service.service:app --host 0.0.0.0 --port 8082

# Run example
python examples/faas/rag_service_example.py
```

### 3. Gateway Service Example
**File**: `gateway_service_example.py`

Demonstrates:
- Text generation
- Embedding generation
- Getting available providers

**Usage**:
```bash
# Start Gateway Service first
uvicorn src.faas.services.gateway_service.service:app --host 0.0.0.0 --port 8080

# Run example
python examples/faas/gateway_service_example.py
```

### 4. Complete Workflow Example
**File**: `complete_workflow_example.py`

Demonstrates:
- Complete workflow: Upload document → Ingest → Create agent → Query RAG → Agent responds

**Usage**:
```bash
# Start all services first
# Then run example
python examples/faas/complete_workflow_example.py
```

## Service URLs

Default service URLs (adjust based on your deployment):

- Gateway Service: `http://localhost:8080`
- Cache Service: `http://localhost:8081`
- RAG Service: `http://localhost:8082`
- Agent Service: `http://localhost:8083`
- ML Service: `http://localhost:8084`
- Prompt Service: `http://localhost:8085`
- Data Ingestion Service: `http://localhost:8086`
- Prompt Generator Service: `http://localhost:8087`
- LLMOps Service: `http://localhost:8088`

## Prerequisites

1. **Start Services**: Each service must be running before running examples
2. **Database**: PostgreSQL database must be running and accessible
3. **Redis** (optional): For caching
4. **API Keys**: LLM API keys must be configured

## Running Examples

### Start All Services

```bash
# Terminal 1: Gateway Service
uvicorn src.faas.services.gateway_service.service:app --host 0.0.0.0 --port 8080

# Terminal 2: Cache Service
uvicorn src.faas.services.cache_service.service:app --host 0.0.0.0 --port 8081

# Terminal 3: RAG Service
uvicorn src.faas.services.rag_service.service:app --host 0.0.0.0 --port 8082

# Terminal 4: Agent Service
uvicorn src.faas.services.agent_service.service:app --host 0.0.0.0 --port 8083
```

### Run Examples

```bash
# Agent Service example
python examples/faas/agent_service_example.py

# RAG Service example
python examples/faas/rag_service_example.py

# Gateway Service example
python examples/faas/gateway_service_example.py

# Complete workflow
python examples/faas/complete_workflow_example.py
```

## Expected Output

### Agent Service Example
```
Creating agent...
Create Agent Response: 201
Agent created: agent_abc123

Executing task...
Execute Task Response: 200
Task Result: {...}

Chatting with agent...
Chat Response: 200
Agent Response: Hello! How can I help you today?
```

### RAG Service Example
```
Ingesting document...
Ingest Document Response: 201
Document ingested: doc_xyz789

Querying RAG system...
Query Response: 200
Answer: Artificial Intelligence (AI) is...
Sources: 1 documents
```

## Troubleshooting

### Service Not Found
- Ensure service is running on the correct port
- Check service URL in example code

### Authentication Errors
- Ensure `X-Tenant-ID` header is provided
- Check API Gateway configuration

### Database Connection Errors
- Verify database is running
- Check `DATABASE_URL` environment variable

### LLM API Errors
- Verify API keys are configured
- Check Gateway Service logs

