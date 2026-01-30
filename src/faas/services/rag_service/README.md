# MOTADATA - RAG SERVICE

**FaaS implementation of the RAG System providing REST API endpoints for document ingestion, query processing, and vector search.**

## Overview

RAG Service is a FaaS implementation of the RAG (Retrieval-Augmented Generation) System component. It provides REST API endpoints for document ingestion, query processing, vector search, and document management.

## API Endpoints

### Document Management

- `POST /api/v1/rag/documents` - Ingest a new document
- `GET /api/v1/rag/documents/{document_id}` - Get document by ID
- `PUT /api/v1/rag/documents/{document_id}` - Update document
- `DELETE /api/v1/rag/documents/{document_id}` - Delete document
- `GET /api/v1/rag/documents` - List all documents

### Query Processing

- `POST /api/v1/rag/query` - Process a RAG query and generate response

**Request Body:**
```json
{
  "query": "What is machine learning?",
  "top_k": 5,
  "threshold": 0.7,
  "metadata_filters": {}
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "answer": "Machine learning is...",
    "documents": [...],
    "sources": [...],
    "confidence": 0.95
  }
}
```

### Vector Search

- `POST /api/v1/rag/search` - Perform vector similarity search

**Request Body:**
```json
{
  "query_text": "machine learning algorithms",
  "top_k": 10,
  "threshold": 0.6,
  "metadata_filters": {}
}
```

## Service Dependencies

- **Gateway Service**: For LLM generation and embedding generation
- **Cache Service**: For caching query results and embeddings
- **Database**: For document and embedding storage (PostgreSQL with pgvector)

## Stateless Architecture

The RAG Service is **stateless**:
- RAG system instances are created on-demand per request
- No in-memory caching of RAG systems
- All persistent state stored in database

## Usage

```python
from src.faas.services.rag_service import create_rag_service

# Create service
service = create_rag_service(
    service_name="rag-service",
    config_overrides={
        "gateway_service_url": "http://gateway-service:8080",
        "cache_service_url": "http://cache-service:8080",
    }
)

# Run service
# uvicorn service.app:app --host 0.0.0.0 --port 8080
```

## Integration with Other Services

### Using Gateway Service

```python
# RAG Service calls Gateway Service for embeddings and generation
from src.faas.shared import ServiceClientManager

client_manager = ServiceClientManager(config)
gateway_client = client_manager.get_client("gateway")

# Generate embeddings
response = await gateway_client.post(
    "/api/v1/gateway/embeddings",
    json_data={"texts": ["document text"], "model": "text-embedding-3-small"},
    headers=gateway_client.get_headers(tenant_id=tenant_id)
)
```

### Using NATS for Events

```python
# Publish document ingestion event
event = {
    "event_type": "rag.document.ingested",
    "document_id": document_id,
    "tenant_id": tenant_id,
}
await nats_client.publish(
    f"rag.events.{tenant_id}",
    codec_manager.encode(event)
)
```

## Configuration

```bash
SERVICE_NAME=rag-service
SERVICE_PORT=8080
GATEWAY_SERVICE_URL=http://gateway-service:8080
CACHE_SERVICE_URL=http://cache-service:8080
DATABASE_URL=postgresql://user:pass@localhost/db
ENABLE_NATS=true
ENABLE_OTEL=true
```

## Example Request

```bash
# Ingest a document
curl -X POST http://localhost:8080/api/v1/rag/documents \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant_123" \
  -d '{
    "title": "AI Guide",
    "content": "Artificial Intelligence is...",
    "source": "manual",
    "metadata": {"category": "tutorial"}
  }'

# Query documents
curl -X POST http://localhost:8080/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant_123" \
  -d '{
    "query": "What is AI?",
    "top_k": 5
  }'
```

