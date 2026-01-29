# Motadata Data Ingestion Service

## Overview

Data Ingestion Service is a FaaS implementation of the Data Ingestion component. It provides REST API endpoints for file upload, multi-modal data processing, and automatic ingestion into RAG systems.

## API Endpoints

### File Upload

- `POST /api/v1/ingestion/upload` - Upload and process a file

**Request:**
- `file`: File to upload (multipart/form-data)
- `title`: Optional title for the document
- `metadata`: Optional JSON metadata
- `auto_ingest`: Whether to automatically ingest into RAG (default: true)

**Response:**
```json
{
  "success": true,
  "message": "File uploaded and processed successfully",
  "data": {
    "file_id": "file_abc123",
    "status": "completed",
    "rag_document_id": "doc_xyz789"
  }
}
```

### File Processing

- `POST /api/v1/ingestion/files/{file_id}/process` - Process an already uploaded file

**Request Body:**
```json
{
  "file_path": "/path/to/file.pdf",
  "title": "Document Title",
  "metadata": {"category": "tutorial"},
  "auto_ingest": true
}
```

### File Status

- `GET /api/v1/ingestion/files/{file_id}` - Get file processing status

**Response:**
```json
{
  "success": true,
  "data": {
    "file_id": "file_abc123",
    "status": "completed",
    "progress": 100,
    "message": "Processing complete",
    "rag_document_id": "doc_xyz789"
  }
}
```

## Service Dependencies

- **RAG Service**: For automatic document ingestion (if `auto_ingest=true`)
- **Database**: For file metadata and processing status

## Stateless Architecture

The Data Ingestion Service is **stateless**:
- Ingestion service instances are created on-demand per request
- No in-memory caching of ingestion services
- All file metadata and status stored in database

## Usage

```python
from src.faas.services.data_ingestion_service import create_data_ingestion_service

# Create service
service = create_data_ingestion_service(
    service_name="data-ingestion-service",
    config_overrides={
        "rag_service_url": "http://rag-service:8080",
        "database_url": "postgresql://user:pass@localhost/db",
    }
)

# Run service
# uvicorn service.app:app --host 0.0.0.0 --port 8080
```

## Integration with Other Services

### Using RAG Service

```python
# Data Ingestion Service calls RAG Service for auto-ingestion
from src.faas.shared import ServiceClientManager

client_manager = ServiceClientManager(config)
rag_client = client_manager.get_client("rag")

# Ingest document into RAG
response = await rag_client.post(
    "/api/v1/rag/documents",
    json_data={
        "title": "Document Title",
        "content": "Document content...",
        "source": "data_ingestion"
    },
    headers=rag_client.get_headers(tenant_id=tenant_id)
)
```

### Using NATS for Events

```python
# Publish file processing completion event
event = {
    "event_type": "ingestion.file.processed",
    "file_id": file_id,
    "tenant_id": tenant_id,
}
await nats_client.publish(
    f"ingestion.events.{tenant_id}",
    codec_manager.encode(event)
)
```

## Configuration

```bash
SERVICE_NAME=data-ingestion-service
SERVICE_PORT=8080
RAG_SERVICE_URL=http://rag-service:8080
DATABASE_URL=postgresql://user:pass@localhost/db
ENABLE_NATS=true
ENABLE_OTEL=true
```

## Example Request

```bash
# Upload a file
curl -X POST http://localhost:8080/api/v1/ingestion/upload \
  -H "X-Tenant-ID: tenant_123" \
  -F "file=@document.pdf" \
  -F "title=My Document" \
  -F "auto_ingest=true"

# Check file status
curl -X GET http://localhost:8080/api/v1/ingestion/files/file_abc123 \
  -H "X-Tenant-ID: tenant_123"
```

## Supported File Formats

- **Text**: `.txt`, `.md`, `.rst`
- **Documents**: `.pdf`, `.docx`, `.doc`
- **Images**: `.jpg`, `.png`, `.gif` (with OCR)
- **Audio**: `.mp3`, `.wav` (with transcription)
- **Video**: `.mp4`, `.avi` (with transcription)
- **Structured Data**: `.json`, `.csv`, `.xlsx`

## Features

- **Multi-Modal Support**: Process text, images, audio, video
- **Automatic Format Detection**: Detect file type and process accordingly
- **Auto-Ingestion**: Automatically ingest processed files into RAG
- **Metadata Extraction**: Extract metadata from files
- **Progress Tracking**: Track file processing progress
- **Validation**: Validate file formats and content

