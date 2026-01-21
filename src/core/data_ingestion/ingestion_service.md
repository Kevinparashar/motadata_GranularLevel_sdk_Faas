# Data Ingestion Service Documentation

## Overview

The `ingestion_service.py` file contains the core `DataIngestionService` class implementation, which provides a unified interface for ingesting and processing data from various sources and formats. The service automatically handles multi-modal data processing, validation, cleaning, and integration with RAG systems.

**Primary Functionality:**
- Multi-modal data ingestion (text, PDF, audio, video, images)
- Automatic format detection and processing
- Data validation and cleaning
- Integration with RAG system for automatic indexing
- Batch processing capabilities
- Tenant-scoped data isolation
- Metadata extraction and management
- Error handling and recovery

## Code Explanation

### Class Structure

#### `DataIngestionService` (Class)
Main data ingestion service class.

**Core Attributes:**
- `gateway`: LiteLLM Gateway for multi-modal processing
- `rag_system`: Optional RAG system for automatic indexing
- `validator`: DataValidator for validation
- `cleaner`: DataCleaner for data cleaning
- `cache`: Optional cache mechanism

**Configuration:**
- `auto_index_to_rag`: Automatically index ingested data to RAG (default: True)
- `enable_validation`: Enable data validation (default: True)
- `enable_cleaning`: Enable data cleaning (default: True)
- `tenant_id`: Optional tenant ID for multi-tenant isolation

### Key Methods

#### `ingest(data_source, data_type=None, **kwargs) -> Dict[str, Any]`
Ingests data from various sources.

**Parameters:**
- `data_source`: Data source (file path, URL, or content string)
- `data_type`: Optional data type hint (auto-detected if not provided)
- `tenant_id`: Optional tenant ID
- `metadata`: Optional metadata dictionary
- `auto_index`: Automatically index to RAG (default: True)
- `**kwargs`: Additional ingestion parameters

**Supported Sources:**
- **File Paths**: Local file paths
- **URLs**: HTTP/HTTPS URLs
- **Content Strings**: Direct text content
- **File Objects**: Python file objects

**Supported Formats:**
- **Text**: .txt, .md, .html, .json, .csv
- **Documents**: .pdf, .doc, .docx, .xls, .xlsx
- **Audio**: .mp3, .wav, .m4a, .ogg (with transcription)
- **Video**: .mp4, .avi, .mov, .mkv (with transcription and frame extraction)
- **Images**: .jpg, .png, .gif, .bmp (with OCR and description)

**Process:**
1. Detects data type and format
2. Loads data from source
3. Validates data (if enabled)
4. Cleans data (if enabled)
5. Processes multi-modal content (transcription, OCR, etc.)
6. Extracts metadata
7. Indexes to RAG (if enabled)
8. Returns ingestion result

**Returns:** Dictionary with:
- `ingestion_id`: Unique ingestion ID
- `data_type`: Detected data type
- `status`: Ingestion status
- `metadata`: Extracted metadata
- `rag_document_id`: RAG document ID (if indexed)

#### `async def ingest_async(data_source, data_type=None, **kwargs) -> Dict[str, Any]`
Asynchronous data ingestion (recommended for production).

**Parameters:** Same as `ingest()`

**Returns:** Dictionary with ingestion results

#### `ingest_batch(data_sources, **kwargs) -> List[Dict[str, Any]]`
Batch data ingestion.

**Parameters:**
- `data_sources`: List of data sources (file paths, URLs, or content)
- `tenant_id`: Optional tenant ID for all sources
- `**kwargs`: Additional parameters

**Returns:** List of ingestion result dictionaries

#### `async def ingest_batch_async(data_sources, **kwargs) -> List[Dict[str, Any]]`
Asynchronous batch ingestion.

**Parameters:** Same as `ingest_batch()`

**Returns:** List of ingestion result dictionaries

#### `validate(data, data_type=None) -> Dict[str, Any]`
Validates data before ingestion.

**Parameters:**
- `data`: Data to validate
- `data_type`: Optional data type hint

**Returns:** Dictionary with validation results:
- `valid`: Boolean indicating validity
- `errors`: List of validation errors
- `warnings`: List of warnings

#### `clean(data, data_type=None) -> str`
Cleans data before ingestion.

**Parameters:**
- `data`: Data to clean
- `data_type`: Optional data type hint

**Returns:** Cleaned data string

## Usage Instructions

### Basic Service Creation

```python
from src.core.data_ingestion import DataIngestionService
from src.core.litellm_gateway import create_gateway

# Create gateway
gateway = create_gateway(api_keys={'openai': 'your-api-key'}, default_model='gpt-4')

# Create ingestion service
service = DataIngestionService(
    gateway=gateway,
    auto_index_to_rag=True,
    enable_validation=True,
    enable_cleaning=True
)
```

### Ingesting Text Content

```python
# Ingest text directly
result = service.ingest(
    data_source="This is sample text content...",
    data_type="text",
    tenant_id="tenant_123",
    metadata={"category": "documentation"}
)

print(f"Ingested: {result['ingestion_id']}")
print(f"RAG Document ID: {result.get('rag_document_id')}")
```

### Ingesting from File

```python
# Ingest from file path
result = await service.ingest_async(
    data_source="/path/to/document.pdf",
    tenant_id="tenant_123"
)

# Auto-detects format and processes accordingly
print(f"Data Type: {result['data_type']}")
print(f"Status: {result['status']}")
```

### Ingesting from URL

```python
# Ingest from URL
result = await service.ingest_async(
    data_source="https://example.com/document.pdf",
    tenant_id="tenant_123"
)
```

### Multi-Modal Ingestion

```python
# Ingest image with OCR
result = await service.ingest_async(
    data_source="/path/to/image.png",
    tenant_id="tenant_123"
)
# Automatically performs OCR and generates description

# Ingest audio with transcription
result = await service.ingest_async(
    data_source="/path/to/audio.mp3",
    tenant_id="tenant_123"
)
# Automatically transcribes audio

# Ingest video
result = await service.ingest_async(
    data_source="/path/to/video.mp4",
    tenant_id="tenant_123"
)
# Automatically extracts frames and transcribes audio
```

### Batch Ingestion

```python
# Batch ingest multiple files
data_sources = [
    "/path/to/doc1.pdf",
    "/path/to/doc2.docx",
    "/path/to/image.jpg",
    "https://example.com/document.txt"
]

results = await service.ingest_batch_async(
    data_sources=data_sources,
    tenant_id="tenant_123"
)

for result in results:
    print(f"Ingested: {result['ingestion_id']}, Status: {result['status']}")
```

### With RAG Integration

```python
from src.core.rag import create_rag_system
from src.core.postgresql_database import create_database_connection

# Create RAG system
db = create_database_connection("postgresql://user:pass@localhost/db")
rag = create_rag_system(db=db, gateway=gateway)

# Create ingestion service with RAG
service = DataIngestionService(
    gateway=gateway,
    rag_system=rag,
    auto_index_to_rag=True  # Automatically indexes to RAG
)

# Ingest and automatically index
result = await service.ingest_async(
    data_source="/path/to/document.pdf",
    tenant_id="tenant_123"
)

# Document is now searchable in RAG
rag_result = await rag.query_async("What is in the document?", tenant_id="tenant_123")
```

### Validation and Cleaning

```python
# Validate data before ingestion
validation = service.validate(
    data="Sample content...",
    data_type="text"
)

if validation['valid']:
    # Clean data
    cleaned = service.clean(
        data="Sample content...",
        data_type="text"
    )
    
    # Ingest cleaned data
    result = await service.ingest_async(cleaned, tenant_id="tenant_123")
else:
    print(f"Validation errors: {validation['errors']}")
```

### Prerequisites

1. **Python 3.10+**: Required for type hints and async/await
2. **Dependencies**: Install via `pip install -r requirements.txt`
   - `litellm`: For LLM operations (multi-modal processing)
   - `pydantic`: For data validation
   - Optional: `Pillow`, `opencv-python`, `pydub` for multi-modal support
3. **API Keys**: LLM provider API keys for multi-modal processing
4. **RAG System** (optional): For automatic indexing

## Connection to Other Components

### LiteLLM Gateway
Uses `LiteLLMGateway` from `src/core/litellm_gateway/gateway.py`:
- Generates image descriptions
- Transcribes audio/video
- Processes multi-modal content

**Integration Point:** `service.gateway` attribute

### RAG System
Integrates with `RAGSystem` from `src/core/rag/rag_system.py`:
- Automatically indexes ingested data
- Makes data searchable via RAG queries

**Integration Point:** `service.rag_system` attribute

### Data Validator
Uses `DataValidator` from `src/core/data_ingestion/data_validator.py`:
- Validates data before ingestion
- Checks format and content quality

**Integration Point:** `service.validator` attribute

### Data Cleaner
Uses `DataCleaner` from `src/core/data_ingestion/data_cleaner.py`:
- Cleans data before ingestion
- Normalizes content

**Integration Point:** `service.cleaner` attribute

### Cache Mechanism
Uses `CacheMechanism` from `src/core/cache_mechanism/`:
- Caches processed content
- Improves performance

**Integration Point:** `service.cache` attribute

### Where Used
- **Data Ingestion Functions** (`src/core/data_ingestion/functions.py`): Factory functions create service instances
- **FaaS Data Ingestion Service** (`src/faas/services/data_ingestion_service/`): REST API wrapper
- **API Backend Services** (`src/core/api_backend_services/`): HTTP endpoints
- **Examples**: All data ingestion examples use this class

## Best Practices

### 1. Use Async Methods
Always prefer async methods for production:
```python
# Good: Async for better performance
result = await service.ingest_async(data_source="...")

# Bad: Synchronous blocks event loop
result = service.ingest(data_source="...")
```

### 2. Enable Validation
Always enable validation for data quality:
```python
# Good: Validation enabled
service = DataIngestionService(
    gateway=gateway,
    enable_validation=True
)

# Bad: No validation (may ingest invalid data)
service = DataIngestionService(gateway=gateway, enable_validation=False)
```

### 3. Use Tenant IDs
Always provide tenant_id for multi-tenant applications:
```python
# Good: Tenant-scoped operations
result = await service.ingest_async(
    data_source="...",
    tenant_id="tenant_123"
)

# Bad: Missing tenant_id in multi-tenant system
result = await service.ingest_async(data_source="...")
```

### 4. Use Batch Processing
Use batch processing for multiple files:
```python
# Good: Batch processing
results = await service.ingest_batch_async(data_sources)

# Bad: Sequential processing
results = []
for source in data_sources:
    result = await service.ingest_async(source)
    results.append(result)
```

### 5. Integrate with RAG
Enable automatic RAG indexing:
```python
# Good: Auto-index to RAG
service = DataIngestionService(
    gateway=gateway,
    rag_system=rag,
    auto_index_to_rag=True
)

# Bad: Manual indexing (more steps)
service = DataIngestionService(gateway=gateway)
result = await service.ingest_async("...")
# Then manually index to RAG...
```

### 6. Provide Metadata
Always provide meaningful metadata:
```python
# Good: Rich metadata
result = await service.ingest_async(
    data_source="...",
    metadata={
        "category": "documentation",
        "author": "John Doe",
        "date": "2024-01-01",
        "tags": ["AI", "ML"]
    }
)

# Bad: No metadata (harder to manage)
result = await service.ingest_async(data_source="...")
```

### 7. Handle Errors
Always handle errors appropriately:
```python
# Good: Error handling
try:
    result = await service.ingest_async(data_source="...")
except Exception as e:
    logger.error(f"Ingestion failed: {e}")
    # Handle error

# Bad: No error handling
result = await service.ingest_async(data_source="...")  # May crash
```

### 8. Validate Before Ingestion
Validate data before ingestion:
```python
# Good: Validate first
validation = service.validate(data="...")
if validation['valid']:
    result = await service.ingest_async(data="...")
else:
    # Handle validation errors
    print(f"Errors: {validation['errors']}")

# Bad: Ingest without validation
result = await service.ingest_async(data="...")  # May fail
```

## Additional Resources

### Documentation
- **[Data Ingestion README](README.md)** - Complete data ingestion guide
- **[Data Ingestion Functions Documentation](functions.md)** - Factory and convenience functions
- **[Data Ingestion Troubleshooting](../../../docs/troubleshooting/data_ingestion_troubleshooting.md)** - Common issues

### Related Components
- **[Data Validator](data_validator.py)** - Data validation
- **[Data Cleaner](data_cleaner.py)** - Data cleaning
- **[RAG System](../../rag/README.md)** - RAG integration
- **[LiteLLM Gateway](../../litellm_gateway/README.md)** - Multi-modal processing

### External Resources
- **[Multi-Modal Processing Guide](../../../docs/components/multimodal_data_processing.md)** - Format support details
- **[File Format Support](https://docs.python.org/3/library/mimetypes.html)** - MIME type detection
- **[OCR Libraries](https://github.com/tesseract-ocr/tesseract)** - OCR documentation

### Examples
- **[Basic Ingestion Example](../../../../examples/basic_usage/)** - Simple ingestion
- **[Multi-Modal Ingestion Example](../../../../examples/)** - Multi-modal processing
- **[Batch Ingestion Example](../../../../examples/)** - Batch processing

