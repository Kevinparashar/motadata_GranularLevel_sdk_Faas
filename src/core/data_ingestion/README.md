# Motadata Data Ingestion Service

## When to Use This Component

**✅ Use Data Ingestion Service when:**
- You want a simple one-line file upload that automatically works with all AI components
- You need automatic file processing, validation, and cleansing
- You want files automatically ingested into RAG, cached, and available to agents
- You're building a system where users upload files and everything "just works"
- You need batch processing of multiple files
- You want asynchronous processing for better performance

**❌ Don't use Data Ingestion Service when:**
- You need fine-grained control over each processing step
- You're processing files programmatically with custom logic
- You don't need automatic RAG ingestion
- You're working with streaming data

**Simple Example:**
```python
from src.core.data_ingestion import upload_and_process
from src.core.rag import create_rag_system
from src.core.cache_mechanism import create_cache_mechanism

# Setup
rag = create_rag_system(db, gateway)
cache = create_cache_mechanism()

# One-line upload - everything happens automatically!
result = upload_and_process(
    "document.pdf",
    rag_system=rag,
    cache=cache
)

# File is now:
# - Validated and processed
# - Cached for fast access
# - Ingested into RAG (searchable)
# - Available to agents
print(f"Document ID: {result['document_id']}")
```

---

## Overview

The Data Ingestion Service provides a unified, simple interface for uploading and processing data files. It automatically handles:

1. **File Validation**: Format, size, and content validation
2. **Data Processing**: Multi-modal loading (text, PDF, audio, video, images)
3. **Data Cleansing**: Normalization and quality improvement
4. **Automatic Integration**: 
   - Ingests into RAG system (for search)
   - Caches processed content (for performance)
   - Makes available to agents (for AI operations)

## Key Features

### One-Line Upload
Simply provide a file path - everything else is automatic:
```python
result = upload_and_process("myfile.pdf", rag_system=rag, cache=cache)
```

### Automatic Processing
- Detects file format automatically
- Processes content based on format
- Extracts metadata
- Cleanses and normalizes data

### Multi-Format Support
- **Text**: `.txt`, `.md`, `.html`, `.json`
- **Documents**: `.pdf`, `.doc`, `.docx`
- **Audio**: `.mp3`, `.wav`, `.m4a`, `.ogg` (with transcription)
- **Video**: `.mp4`, `.avi`, `.mov`, `.mkv` (with transcription)
- **Images**: `.jpg`, `.png`, `.gif`, `.bmp` (with OCR)
- **Structured**: `.csv`, `.json`, `.xml`, `.xlsx`

### Automatic Integration
- **RAG Integration**: Automatically ingests into RAG for search
- **Caching**: Caches processed content for fast access
- **Agent Ready**: Processed content available to agents immediately

### Asynchronous Processing
```python
result = await upload_and_process_async("file.pdf", rag_system=rag)
```

### Batch Processing
```python
results = batch_upload_and_process(
    ["file1.pdf", "file2.mp3", "file3.jpg"],
    rag_system=rag,
    cache=cache
)
```

---

## Usage Examples

### Basic Usage

```python
from src.core.data_ingestion import create_ingestion_service
from src.core.rag import create_rag_system
from src.core.cache_mechanism import create_cache_mechanism

# Setup components
rag = create_rag_system(db, gateway)
cache = create_cache_mechanism()

# Create ingestion service
service = create_ingestion_service(
    rag_system=rag,
    cache=cache
)

# Upload and process
result = service.upload_and_process("document.pdf")
print(f"Document ID: {result['document_id']}")
print(f"Content length: {result['content_length']}")
```

### With Custom Configuration

```python
service = create_ingestion_service(
    rag_system=rag,
    cache=cache,
    enable_validation=True,      # Validate files
    enable_cleansing=True,        # Clean data
    enable_auto_ingest=True,      # Auto-ingest into RAG
    enable_caching=True,          # Cache results
    tenant_id="tenant_123"        # Multi-tenant support
)
```

### Asynchronous Processing

```python
import asyncio

async def process_files():
    service = create_ingestion_service(rag_system=rag, cache=cache)
    
    # Process multiple files asynchronously
    results = await service.batch_upload_and_process_async([
        "file1.pdf",
        "file2.mp3",
        "file3.jpg"
    ])
    
    for result in results:
        print(f"Processed: {result['file_path']}")

asyncio.run(process_files())
```

### Without Auto-Ingest

```python
# Process file but don't ingest into RAG
result = service.upload_and_process(
    "document.pdf",
    auto_ingest=False  # Just process and cache
)

# Manually ingest later if needed
if result["success"]:
    rag.ingest_document(
        title=result["title"],
        content=result["content_preview"],
        metadata=result["metadata"]
    )
```

---

## Integration with AI Components

### RAG Integration

Files are automatically ingested into RAG:
```python
# Upload file
result = upload_and_process("manual.pdf", rag_system=rag)

# File is now searchable in RAG
answers = await rag.query("What is the installation process?")
```

### Agent Integration

Agents can immediately use processed content:
```python
from src.core.agno_agent_framework import create_agent

# Upload file
upload_and_process("data.csv", rag_system=rag, cache=cache)

# Agent can query RAG for the uploaded content
agent = create_agent("analyst", "Data Analyst", gateway)
response = await agent.execute_task(
    "Analyze the data from the uploaded CSV file"
)
```

### Cache Integration

Processed content is automatically cached:
```python
# First upload - processes and caches
result1 = upload_and_process("large_document.pdf", cache=cache)

# Second access - uses cache (fast!)
result2 = upload_and_process("large_document.pdf", cache=cache)
```

---

## Data Processing Pipeline

```
File Upload
    ↓
Validation (format, size, content)
    ↓
Multi-Modal Loading (format-specific processing)
    ↓
Data Cleansing (normalization, quality improvement)
    ↓
Caching (store for fast access)
    ↓
RAG Ingestion (make searchable)
    ↓
Ready for Agents & Queries
```

---

## Configuration Options

### Service Configuration

```python
create_ingestion_service(
    rag_system=rag,              # RAG system for ingestion
    cache=cache,                 # Cache for processed data
    gateway=gateway,             # Gateway (if RAG not provided)
    db=db,                       # Database (if RAG not provided)
    enable_validation=True,      # Enable file validation
    enable_cleansing=True,        # Enable data cleansing
    enable_auto_ingest=True,      # Auto-ingest into RAG
    enable_caching=True,          # Cache processed content
    tenant_id="tenant_123"       # Multi-tenant support
)
```

### Validation Options

```python
from src.core.data_ingestion import DataValidator

validator = DataValidator(
    max_file_size=100 * 1024 * 1024,  # 100 MB
    allowed_formats=[".pdf", ".docx", ".txt"]  # Specific formats
)
```

### Cleansing Options

```python
from src.core.data_ingestion import DataCleaner

cleaner = DataCleaner(
    remove_extra_whitespace=True,
    normalize_unicode=True,
    remove_control_chars=True,
    normalize_line_endings=True
)
```

---

## Error Handling

```python
from src.core.data_ingestion.exceptions import DataIngestionError, ValidationError

try:
    result = upload_and_process("file.pdf", rag_system=rag)
except ValidationError as e:
    print(f"Validation failed: {e.message}")
except DataIngestionError as e:
    print(f"Processing failed: {e.message}")
    print(f"File: {e.file_path}")
```

---

## Best Practices

1. **Use Auto-Ingest**: Let the service handle RAG ingestion automatically
2. **Enable Caching**: Cache improves performance for repeated access
3. **Batch Processing**: Use batch methods for multiple files
4. **Async for Large Files**: Use async methods for large files or many files
5. **Validation**: Keep validation enabled for data quality
6. **Metadata**: Provide metadata for better organization
7. **Tenant Isolation**: Use tenant_id for multi-tenant applications

---

## Related Documentation

- **[Multi-Modal Data Processing](../components/multimodal_data_processing.md)** - Format support details
- **[RAG System](../rag/README.md)** - RAG integration
- **[Cache Mechanism](../cache_mechanism/README.md)** - Caching details
- **[Agent Framework](../agno_agent_framework/README.md)** - Agent integration

