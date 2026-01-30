# MOTADATA - DATA INGESTION FUNCTIONS

**Documentation of high-level factory functions, convenience functions, and utilities for the Data Ingestion Service.**

## Overview

The `functions.py` file provides high-level factory functions, convenience functions, and utilities for the Data Ingestion Service. These functions simplify data ingestion service creation, configuration, and common operations, making it easier for developers to ingest data from various sources and formats.

**Primary Functionality:**
- Factory functions for creating ingestion services with different configurations
- Convenience functions for common ingestion operations
- Quick ingestion functions for simple use cases
- Batch processing utilities for handling multiple data sources
- Integration helpers for RAG system

## Code Explanation

### Function Categories

The file is organized into several categories:

#### 1. Factory Functions
Factory functions create and configure ingestion services:

- **`create_ingestion_service()`**: Create ingestion service with simplified configuration
- **`create_ingestion_service_with_rag()`**: Create ingestion service with RAG integration

#### 2. Convenience Functions
High-level functions for common operations:

- **`ingest_data()`**: Simplified data ingestion
- **`ingest_data_async()`**: Async data ingestion
- **`ingest_file()`**: File ingestion convenience function
- **`ingest_file_async()`**: Async file ingestion
- **`ingest_url()`**: URL ingestion convenience function
- **`ingest_url_async()`**: Async URL ingestion
- **`quick_ingest()`**: Quick ingestion for simple use cases
- **`quick_ingest_async()`**: Async quick ingestion

#### 3. Batch Processing Functions
Utilities for batch operations:

- **`ingest_batch()`**: Batch data ingestion
- **`ingest_batch_async()`**: Async batch ingestion

### Key Functions

#### `create_ingestion_service(gateway, **kwargs) -> DataIngestionService`
Creates a data ingestion service instance.

**Parameters:**
- `gateway`: LiteLLM Gateway instance (required)
- `rag_system`: Optional RAG system for automatic indexing
- `auto_index_to_rag`: Automatically index to RAG (default: True)
- `enable_validation`: Enable data validation (default: True)
- `enable_cleaning`: Enable data cleaning (default: True)
- `cache`: Optional cache mechanism
- `**kwargs`: Additional configuration

**Returns:** Configured `DataIngestionService` instance

**Example:**
```python
from src.core.data_ingestion import create_ingestion_service
from src.core.litellm_gateway import create_gateway

gateway = create_gateway(api_keys={'openai': 'key'}, default_model='gpt-4')

service = create_ingestion_service(
    gateway=gateway,
    auto_index_to_rag=True,
    enable_validation=True
)
```

#### `async def quick_ingest_async(service, data_source, **kwargs) -> Dict[str, Any]`
Quick ingestion function for simple use cases.

**Parameters:**
- `service`: DataIngestionService instance
- `data_source`: Data source (file path, URL, or content)
- `tenant_id`: Optional tenant ID
- `metadata`: Optional metadata
- `**kwargs`: Additional parameters

**Returns:** Dictionary with ingestion results

**Example:**
```python
result = await quick_ingest_async(
    service,
    data_source="/path/to/document.pdf",
    tenant_id="tenant_123"
)
```

#### `async def ingest_file_async(service, file_path, **kwargs) -> Dict[str, Any]`
File ingestion convenience function.

**Parameters:**
- `service`: DataIngestionService instance
- `file_path`: Path to file
- `tenant_id`: Optional tenant ID
- `metadata`: Optional metadata
- `**kwargs`: Additional parameters

**Returns:** Dictionary with ingestion results

#### `async def ingest_url_async(service, url, **kwargs) -> Dict[str, Any]`
URL ingestion convenience function.

**Parameters:**
- `service`: DataIngestionService instance
- `url`: URL to fetch data from
- `tenant_id`: Optional tenant ID
- `metadata`: Optional metadata
- `**kwargs`: Additional parameters

**Returns:** Dictionary with ingestion results

#### `async def ingest_batch_async(service, data_sources, **kwargs) -> List[Dict[str, Any]]`
Batch data ingestion.

**Parameters:**
- `service`: DataIngestionService instance
- `data_sources`: List of data sources
- `tenant_id`: Optional tenant ID for all sources
- `**kwargs`: Additional parameters

**Returns:** List of ingestion result dictionaries

## Usage Instructions

### Basic Service Creation

```python
from src.core.data_ingestion import create_ingestion_service
from src.core.litellm_gateway import create_gateway

gateway = create_gateway(api_keys={'openai': 'key'}, default_model='gpt-4')

service = create_ingestion_service(
    gateway=gateway,
    auto_index_to_rag=True
)
```

### Quick Ingestion

```python
from src.core.data_ingestion import create_ingestion_service, quick_ingest_async

service = create_ingestion_service(gateway=gateway)

# Quick ingest from file
result = await quick_ingest_async(
    service,
    data_source="/path/to/document.pdf",
    tenant_id="tenant_123"
)

print(f"Ingested: {result['ingestion_id']}")
```

### File Ingestion

```python
from src.core.data_ingestion import create_ingestion_service, ingest_file_async

service = create_ingestion_service(gateway=gateway)

# Ingest file
result = await ingest_file_async(
    service,
    file_path="/path/to/document.pdf",
    tenant_id="tenant_123",
    metadata={"category": "documentation"}
)
```

### URL Ingestion

```python
from src.core.data_ingestion import create_ingestion_service, ingest_url_async

service = create_ingestion_service(gateway=gateway)

# Ingest from URL
result = await ingest_url_async(
    service,
    url="https://example.com/document.pdf",
    tenant_id="tenant_123"
)
```

### Batch Ingestion

```python
from src.core.data_ingestion import create_ingestion_service, ingest_batch_async

service = create_ingestion_service(gateway=gateway)

data_sources = [
    "/path/to/doc1.pdf",
    "/path/to/doc2.docx",
    "https://example.com/doc3.txt"
]

results = await ingest_batch_async(
    service,
    data_sources=data_sources,
    tenant_id="tenant_123"
)

for result in results:
    print(f"Status: {result['status']}")
```

### With RAG Integration

```python
from src.core.data_ingestion import create_ingestion_service_with_rag
from src.core.rag import create_rag_system
from src.core.postgresql_database import create_database_connection

gateway = create_gateway(api_keys={'openai': 'key'}, default_model='gpt-4')
db = create_database_connection("postgresql://user:pass@localhost/db")
rag = create_rag_system(db=db, gateway=gateway)

# Create service with RAG
service = create_ingestion_service_with_rag(
    gateway=gateway,
    rag_system=rag,
    auto_index_to_rag=True
)

# Ingest and automatically index
result = await quick_ingest_async(
    service,
    data_source="/path/to/document.pdf",
    tenant_id="tenant_123"
)

# Document is now searchable in RAG
```

### Prerequisites

1. **Python 3.10+**: Required for type hints and async/await
2. **Dependencies**: Install via `pip install -r requirements.txt`
   - `litellm`: For LLM operations
   - `pydantic`: For data validation
   - Optional: Multi-modal libraries
3. **API Keys**: LLM provider API keys
4. **RAG System** (optional): For automatic indexing

## Connection to Other Components

### Data Ingestion Service
These functions create and use `DataIngestionService` instances from `ingestion_service.py`:
- All factory functions return `DataIngestionService` instances
- Convenience functions use service methods internally

**Integration Point:** Functions wrap `DataIngestionService` class instantiation and methods

### LiteLLM Gateway
Uses `LiteLLMGateway` from `src/core/litellm_gateway/gateway.py`:
- Required parameter for service creation
- Handles multi-modal processing

**Integration Point:** `gateway` parameter in factory functions

### RAG System
Integrates with `RAGSystem` from `src/core/rag/rag_system.py`:
- Optional parameter for automatic indexing
- Makes ingested data searchable

**Integration Point:** `rag_system` parameter in factory functions

### Where Used
- **Examples**: All data ingestion examples use these functions
- **API Backend Services**: HTTP endpoints use these functions
- **FaaS Data Ingestion Service**: REST API wrapper uses these functions
- **User Applications**: Primary interface for data ingestion

## Best Practices

### 1. Use Factory Functions
Always use factory functions instead of directly instantiating `DataIngestionService`:
```python
# Good: Use factory function
service = create_ingestion_service(gateway=gateway)

# Bad: Direct instantiation
from src.core.data_ingestion.ingestion_service import DataIngestionService
service = DataIngestionService(gateway=gateway, ...)
```

### 2. Use Async Functions
Always prefer async functions for production:
```python
# Good: Async for better performance
result = await quick_ingest_async(service, data_source="...")

# Bad: Synchronous blocks event loop
result = quick_ingest(service, data_source="...")
```

### 3. Provide Tenant IDs
Always provide tenant_id for multi-tenant applications:
```python
# Good: Tenant-scoped operations
result = await quick_ingest_async(service, data_source="...", tenant_id="tenant_123")

# Bad: Missing tenant_id
result = await quick_ingest_async(service, data_source="...")
```

### 4. Use Batch Processing
Use batch processing for multiple files:
```python
# Good: Batch processing
results = await ingest_batch_async(service, data_sources)

# Bad: Sequential processing
results = []
for source in data_sources:
    result = await quick_ingest_async(service, source)
    results.append(result)
```

### 5. Integrate with RAG
Enable automatic RAG indexing:
```python
# Good: Auto-index to RAG
service = create_ingestion_service_with_rag(gateway=gateway, rag_system=rag)

# Bad: Manual indexing
service = create_ingestion_service(gateway=gateway)
# Then manually index...
```

### 6. Handle Errors
Always handle errors appropriately:
```python
# Good: Error handling
try:
    result = await quick_ingest_async(service, data_source="...")
except Exception as e:
    logger.error(f"Ingestion failed: {e}")
    # Handle error

# Bad: No error handling
result = await quick_ingest_async(service, data_source="...")  # May crash
```

## Additional Resources

### Documentation
- **[Data Ingestion Service Documentation](ingestion_service.md)** - Core service class
- **[Data Ingestion README](README.md)** - Complete guide
- **[Data Ingestion Troubleshooting](../../../docs/troubleshooting/data_ingestion_troubleshooting.md)** - Common issues

### Related Components
- **[Data Ingestion Service](ingestion_service.py)** - Core service implementation
- **[Data Validator](data_validator.py)** - Validation
- **[Data Cleaner](data_cleaner.py)** - Cleaning

### External Resources
- **[Multi-Modal Processing Guide](../../../docs/components/multimodal_data_processing.md)** - Format support
- **[File Format Support](https://docs.python.org/3/library/mimetypes.html)** - MIME types

### Examples
- **[Basic Ingestion Example](../../../../examples/basic_usage/)** - Simple usage
- **[Multi-Modal Example](../../../../examples/)** - Multi-modal processing
- **[Batch Ingestion Example](../../../../examples/)** - Batch processing

