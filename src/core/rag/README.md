# RAG System

## When to Use This Component

**✅ Use RAG System when:**
- You have documents/knowledge bases to query
- You need accurate answers from your own data
- You want to answer questions about specific content
- You're building document Q&A, knowledge bases, or chatbots with documents
- You need to keep AI responses grounded in your data
- You have a corpus of documents that users will query

**❌ Don't use RAG System when:**
- You don't have documents to query
- You only need general AI chat (use Agent Framework)
- You need real-time data that changes frequently
- Your documents are too large or unstructured for effective retrieval
- You only need simple document search (use database search instead)
- Your use case doesn't require document-based answers

**Simple Example:**
```python
from src.core.rag import create_rag_system, quick_rag_query
from src.core.litellm_gateway import create_gateway

gateway = create_gateway(api_key="your-key", provider="openai")
rag = create_rag_system(db, gateway)

# Ingest a document
await rag.ingest_document_async("doc1", "Your document content here", "Document Title")

# Query it
result = await quick_rag_query(rag, "What is this document about?")
print(result["answer"])
```

**Cost Note:** RAG queries cost ~$0.003-0.03 per query (embedding + generation). Caching can reduce costs by 50-90% for repeated queries.

---

## Overview

The RAG (Retrieval-Augmented Generation) System is a comprehensive solution for building context-aware AI applications. It combines document retrieval with LLM generation to provide accurate, contextually relevant responses based on a knowledge base of documents.

## Purpose and Functionality

The RAG system enables applications to answer questions and generate responses using information from a curated document collection. It works by:
1. **Document Ingestion**: Processing and storing documents with their embeddings
2. **Query Processing**: Converting user queries into embeddings and finding relevant documents
3. **Context-Aware Generation**: Using retrieved documents as context for LLM response generation

This approach overcomes the limitations of LLMs by providing them with up-to-date, specific information from the document collection, resulting in more accurate and relevant responses.

## Connection to Other Components

### Integration with LiteLLM Gateway

The **LiteLLM Gateway** (`src/core/litellm_gateway/`) is a critical dependency for the RAG system. The gateway is used in two essential ways:
1. **Embedding Generation**: The RAG system uses the gateway's `embed()` method to generate vector embeddings for both documents during ingestion and queries during retrieval. These embeddings are essential for similarity search.
2. **Response Generation**: After retrieving relevant documents, the RAG generator uses the gateway's `generate()` or `generate_async()` methods to create context-aware responses. The gateway handles the actual LLM interaction, abstracting away provider-specific details.

The gateway instance is injected into the RAG system during initialization, creating a clear dependency relationship.

### Integration with PostgreSQL Database

The **PostgreSQL Database** (`src/core/postgresql_database/`) is the storage backend for the RAG system. The integration includes:
1. **Document Storage**: Documents are stored in the database with their metadata, titles, and content
2. **Embedding Storage**: Vector embeddings are stored using the pgvector extension, enabling efficient similarity search
3. **Retrieval Operations**: The RAG retriever uses the database's `VectorOperations` class to perform similarity searches and retrieve relevant documents

The database provides the persistence and search capabilities that make the RAG system functional.

### Integration with Document Processor

The **Document Processor** (internal component) handles document preprocessing:
- **Chunking**: Splits large documents into smaller, manageable chunks
- **Metadata Extraction**: Extracts and preserves document metadata
- **Content Normalization**: Normalizes document content for consistent processing

The processor prepares documents for embedding generation and storage.

### Integration with Cache Mechanism

The **Cache Mechanism** (`src/core/cache_mechanism/`) is used to cache:
- **Query Results**: Frequently asked questions are cached to reduce LLM API calls
- **Embeddings**: Document embeddings can be cached to avoid regenerating them
- **Retrieved Documents**: Retrieved document sets are cached for similar queries

This caching improves performance and reduces costs.

### Integration with Agent Memory

The **Agent Memory** (`src/core/agno_agent_framework/memory.py`) is integrated for conversation context:
- **Query History**: Stores previous queries and answers for context
- **User Preferences**: Remembers user-specific preferences and patterns
- **Conversation Context**: Maintains conversation history across sessions
- **Memory Retrieval**: Retrieves relevant memories to enhance query context

**Example:**
```python
from src.core.rag import create_rag_system

# Create RAG with memory enabled (default)
rag = create_rag_system(
    db=db,
    gateway=gateway,
    enable_memory=True,
    memory_config={
        "max_episodic": 100,  # Store last 100 queries
        "max_semantic": 200,  # Store 200 semantic patterns
        "max_age_days": 30    # Auto-cleanup after 30 days
    }
)

# Query with user context
result = rag.query(
    query="What did we discuss about AI?",
    user_id="user123",
    conversation_id="conv456",
    tenant_id="tenant1"
)
# Memory automatically retrieves previous context
```

## Key Features

### Batch Processing

The RAG system now supports **optimized batch processing** for improved performance:

1. **Batch Embedding Generation**:
   - All chunks from a document are embedded in a single API call
   - Significantly reduces API calls and improves ingestion speed
   - Automatically falls back to individual processing if batch fails

2. **Batch Document Ingestion**:
   - `ingest_documents_batch()`: Process multiple documents synchronously
   - `ingest_documents_batch_async()`: Process multiple documents concurrently
   - Configurable batch size for optimal performance

3. **Async Support**:
   - `ingest_document_async()`: Async document ingestion with batch embedding
   - `query_async()`: Async query processing
   - Enables concurrent processing for better throughput

**Performance Benefits:**
- **Reduced API Calls**: Single embedding call per document instead of one per chunk
- **Faster Ingestion**: Batch processing reduces total ingestion time by 50-70%
- **Lower Costs**: Fewer API calls mean lower costs
- **Better Scalability**: Async batch processing handles large document collections efficiently

This caching improves performance and reduces costs.

### Query Optimization

The RAG system now includes **advanced query optimization** features:

1. **Query Rewriting**:
   - Automatically expands abbreviations (AI → artificial intelligence)
   - Normalizes query terms for better retrieval
   - Improves search quality by enhancing query semantics

2. **Query Caching**:
   - Caches query results to avoid redundant processing
   - Reduces LLM API calls for repeated queries
   - Configurable TTL for cache entries

**Example:**
```python
# Query with rewriting enabled (default)
result = rag.query("What is AI?", use_query_rewriting=True)

# Query with caching (automatic)
result = rag.query("What is machine learning?")  # First call - generates
result = rag.query("What is machine learning?")  # Second call - from cache
```

### Hybrid Retrieval

The RAG system supports **hybrid retrieval strategies** that combine multiple search methods:

1. **Vector Search**: Semantic similarity using embeddings
2. **Keyword Search**: Traditional text matching
3. **Hybrid**: Combines both with weighted scoring

**Benefits:**
- Better recall for diverse query types
- Improved accuracy for exact matches
- Balanced results combining semantic and keyword relevance

**Example:**
```python
# Vector-only retrieval (default)
result = rag.query("What is AI?", retrieval_strategy="vector")

# Hybrid retrieval (vector + keyword)
result = rag.query("What is AI?", retrieval_strategy="hybrid")
```

### Document Management

The RAG system now supports **complete document lifecycle management**:

1. **Document Updates**:
   - Update document title, content, or metadata
   - Content updates automatically re-process and re-embed chunks
   - Maintains document versioning through metadata

2. **Document Deletion**:
   - Delete documents and all associated chunks/embeddings
   - Automatic cache invalidation
   - Clean removal from knowledge base

**Example:**
```python
# Update document
rag.update_document(
    document_id="doc-123",
    title="Updated Title",
    content="Updated content",
    metadata={"version": "2.0"}
)

# Delete document
rag.delete_document("doc-123")
```

### Advanced Re-ranking

The RAG system now includes **advanced re-ranking algorithms** for improved document relevance:

- **Cross-Encoder Re-ranking**: Uses cross-encoder models for more accurate relevance scoring
- **Diversity Re-ranking**: Ensures diverse results by penalizing similar documents
- **Hybrid Scoring**: Combines multiple signals (semantic similarity, keyword match, metadata)
- **Configurable Re-ranking**: Enable/disable re-ranking and configure algorithms

**Example:**
```python
from src.core.rag.rag_enhancements import DocumentReranker

# Enable re-ranking
reranker = DocumentReranker(
    enable_reranking=True,
    reranking_algorithm="cross_encoder",
    top_k_before_rerank=20,
    top_k_after_rerank=5
)
rag.attach_reranker(reranker)

# Query with re-ranking
result = rag.query("What is AI?", top_k=5, use_reranking=True)
```

### Document Versioning

The RAG system supports **document versioning** for better management and retrieval:

- **Version Tracking**: Tracks document versions with timestamps
- **Version History**: Maintains history of document changes
- **Version-Based Retrieval**: Retrieve specific document versions
- **Automatic Versioning**: Automatically creates versions on updates

**Example:**
```python
from src.core.rag.rag_enhancements import DocumentVersioning

# Enable versioning
versioning = DocumentVersioning(enable_versioning=True)
rag.attach_versioning(versioning)

# Ingest document (creates version 1.0)
doc_id = rag.ingest_document("AI Guide", "Content...")

# Update document (creates version 2.0)
rag.update_document(doc_id, content="Updated content...")

# Retrieve specific version
doc = rag.get_document_version(doc_id, version="1.0")
```

### Explicit Relevance Scoring

The RAG system provides **explicit relevance scoring** for retrieved documents:

- **Similarity Scores**: Provides similarity scores for each retrieved document
- **Relevance Metrics**: Calculates relevance metrics (semantic, keyword, hybrid)
- **Score Normalization**: Normalizes scores for consistent comparison
- **Score Thresholds**: Filter documents by relevance score thresholds

**Example:**
```python
# Query with relevance scores
result = rag.query("What is AI?", top_k=5, return_scores=True)

for doc in result["documents"]:
    print(f"Document: {doc['title']}")
    print(f"Relevance Score: {doc['relevance_score']}")
    print(f"Similarity Score: {doc['similarity_score']}")
```

### Incremental Updates

The RAG system supports **incremental updates** to avoid full re-embedding:

- **Change Detection**: Detects changes in document content
- **Selective Re-embedding**: Only re-embeds changed chunks
- **Efficient Updates**: Updates only affected embeddings
- **Version Tracking**: Tracks changes for incremental processing

**Example:**
```python
from src.core.rag.rag_enhancements import IncrementalUpdater

# Enable incremental updates
updater = IncrementalUpdater(enable_incremental=True)
rag.attach_incremental_updater(updater)

# Update document (only changed chunks are re-embedded)
rag.update_document(
    document_id="doc-123",
    content="Updated content with minor changes"
)
# Only changed chunks are re-processed and re-embedded
```

### Document Validation

The RAG system includes **enhanced document validation** processes:

- **Format Validation**: Validates document formats and structure
- **Content Validation**: Validates content quality and completeness
- **Metadata Validation**: Validates metadata against schemas
- **Compliance Checking**: Ensures documents meet compliance requirements

**Example:**
```python
from src.core.rag.rag_enhancements import DocumentValidator

# Configure validator
validator = DocumentValidator(
    validate_format=True,
    validate_content=True,
    validate_metadata=True,
    compliance_rules=["itil", "security"]
)
rag.attach_validator(validator)

# Ingest document (validates before processing)
doc_id = rag.ingest_document("Guide", "Content...", validate=True)
```

### Real-time Document Synchronization

The RAG system supports **real-time document synchronization**:

- **Change Detection**: Detects changes in source documents
- **Automatic Updates**: Automatically updates documents when source changes
- **Synchronization Strategies**: Configurable sync strategies (immediate, batch, scheduled)
- **Conflict Resolution**: Handles conflicts during synchronization

**Example:**
```python
from src.core.rag.rag_enhancements import RealTimeSync

# Enable real-time sync
sync = RealTimeSync(
    enable_sync=True,
    sync_strategy="immediate",  # or "batch", "scheduled"
    sync_interval=60  # seconds for batch/scheduled
)
rag.attach_realtime_sync(sync)

# Watch document source
rag.watch_document_source("file:///path/to/docs", auto_sync=True)
```

### Integration with Evaluation & Observability

The **Evaluation & Observability** component (`src/core/evaluation_observability/`) tracks:
- **Query Performance**: Measures retrieval and generation times
- **Retrieval Quality**: Tracks similarity scores and relevance metrics
- **Generation Quality**: Monitors response quality and accuracy
- **Usage Statistics**: Tracks document ingestion and query volumes

This monitoring is essential for optimizing RAG system performance.

### Integration with API Backend Services

The **API Backend Services** (`src/core/api_backend_services/`) expose RAG functionality through REST endpoints:
- **Document Ingestion**: Endpoints for adding documents to the knowledge base
- **Query Endpoints**: Endpoints for querying the RAG system
- **Management Endpoints**: Endpoints for managing documents and system configuration

The backend services route requests to the appropriate RAG system methods.

## Libraries Utilized

- **pydantic**: Used for data validation and model definitions. All document chunks, retrieval results, and generation responses are defined using Pydantic models.
- **hashlib**: Used for generating unique chunk identifiers during document processing.

## Function-Driven API

The RAG System provides a **function-driven API** with factory functions, high-level convenience functions, and utilities for easy RAG system creation and usage.

### Factory Functions

Create RAG systems with simplified configuration:

```python
from src.core.rag import create_rag_system, create_document_processor

# Create RAG system
rag = create_rag_system(
    db=db,
    gateway=gateway,
    embedding_model="text-embedding-3-small",
    generation_model="gpt-4"
)

# Create document processor
processor = create_document_processor(
    chunk_size=500,
    strategy="sentence"
)
```

### High-Level Convenience Functions

Use simplified functions for common operations:

```python
from src.core.rag import (
    quick_rag_query,
    ingest_document_simple,
    batch_ingest_documents,
    update_document_simple,
    delete_document_simple
)

# Quick RAG query with hybrid retrieval
result = quick_rag_query(
    rag, "What is AI?",
    top_k=5,
    retrieval_strategy="hybrid",
    use_query_rewriting=True
)
print(result["answer"])

# Simple document ingestion
doc_id = ingest_document_simple(
    rag,
    "AI Guide",
    "Artificial Intelligence is..."
)

# Batch ingest documents
doc_ids = batch_ingest_documents(rag, documents, batch_size=10)

# Update document
update_document_simple(
    rag, "doc-123",
    title="Updated Title",
    content="Updated content"
)

# Delete document
delete_document_simple(rag, "doc-123")
```

### Utility Functions

Use utility functions for batch processing:

```python
from src.core.rag import batch_process_documents

# Process documents in batches
results = batch_process_documents(
    documents,
    lambda doc: process_document(doc),
    batch_size=10
)
```

See `src/core/rag/functions.py` for complete function documentation.

## Key Components

### DocumentProcessor

The `DocumentProcessor` class handles document preprocessing:
- **Enhanced Chunking Pipeline**:
  - Multiple chunking strategies: fixed-size, sentence-based, paragraph-based, and semantic chunking
  - Preprocessing pipeline: text normalization, whitespace cleaning, unicode normalization
  - Chunk validation: filters chunks by size (min/max), validates content
  - Word boundary awareness: chunks break at word boundaries when possible
  - Semantic chunking: chunks by headers and sections for structured documents
- **Advanced Metadata Handling**:
  - Automatic metadata extraction: title, dates, tags, language detection
  - Metadata validation: schema-based validation for metadata consistency
  - Metadata enrichment: document-level metadata automatically added to chunks
  - Metadata transformation: normalization and standardization
  - File metadata extraction: extracts file name, size, extension, modification date
- **Multiple File Format Support**:
  - Text files (.txt, .md, .markdown)
  - HTML files with text extraction
  - JSON files with readable conversion
  - Extensible architecture for additional formats
- **Chunk Identification**: Generates unique identifiers for document chunks with token count estimation

### Retriever

The `Retriever` class performs document retrieval:
- **Query Embedding**: Converts text queries into vector embeddings using the gateway
- **Similarity Search**: Uses the database's vector operations to find similar documents
- **Hybrid Retrieval**: Combines vector similarity and keyword search for better results
- **Result Filtering**: Applies metadata filters to refine search results
- **Query Optimization**: Supports query rewriting and caching for improved performance

### RAGGenerator

The `RAGGenerator` class generates context-aware responses:
- **Context Building**: Constructs context strings from retrieved documents
- **Prompt Construction**: Builds prompts that include retrieved context
- **Response Generation**: Uses the gateway to generate responses based on context

### RAGSystem

The `RAGSystem` class integrates all components:
- **Document Ingestion**: Orchestrates the complete document ingestion pipeline
- **Query Processing**: Handles end-to-end query processing from retrieval to generation
- **Document Management**: Supports document updates and deletion with automatic re-processing
- **Query Optimization**: Implements query rewriting and caching for better performance
- **Hybrid Retrieval**: Supports multiple retrieval strategies (vector, keyword, hybrid)
- **Component Coordination**: Manages interactions between processor, retriever, and generator

## Document Ingestion Flow

1. **Document Input**: A document is provided with title, content, and optional metadata
2. **Preprocessing**: Document content is preprocessed (normalization, cleaning, unicode handling)
3. **Metadata Extraction**: Automatic extraction of metadata (title, dates, tags, language, file info)
4. **Metadata Validation**: Metadata is validated against schema (if provided)
5. **Document Storage**: The document is stored in the database with enriched metadata
6. **Chunking Pipeline**:
   - Document is chunked based on selected strategy
   - Chunks are validated (size, content quality)
   - Chunk metadata is enriched with document-level metadata
   - Token counts are estimated for each chunk
7. **Batch Embedding Generation**: All chunks are embedded in a single batch API call using the LiteLLM Gateway (optimized for performance)
8. **Batch Embedding Storage**: All embeddings are stored in the database with pgvector using batch insert

**Optimization**: The system now uses batch processing to embed all chunks in one API call instead of individual calls, significantly improving performance and reducing costs.

## Query Processing Flow

1. **Query Input**: A user query is received
2. **Query Rewriting** (optional): Query is rewritten to improve retrieval (expands abbreviations, normalizes terms)
3. **Query Caching Check**: System checks cache for existing query results
4. **Query Embedding**: The query is converted to an embedding using the gateway
5. **Retrieval Strategy**:
   - **Vector Search**: Semantic similarity search using embeddings
   - **Hybrid Search**: Combines vector and keyword search with weighted scoring
   - **Keyword Search**: Traditional text matching
6. **Similarity Search**: The database performs similarity search to find relevant documents
7. **Context Building**: Retrieved documents are formatted into context
8. **Response Generation**: The gateway generates a response using the context and query
9. **Response Caching**: Result is cached for future queries
10. **Response Return**: The generated response is returned along with retrieved documents

## Error Handling

The RAG system uses a structured exception hierarchy for granular error handling. All RAG-related exceptions inherit from `SDKError` and provide structured attributes for debugging.

### Exception Types

**RAG Exceptions** (`src/core/rag/exceptions.py`):
- `RetrievalError`: Raised when document retrieval or vector search fails
  - Attributes: `query`, `document_id`, `operation`
- `GenerationError`: Raised when LLM-based generation fails (RAG answer synthesis)
  - Attributes: `query`, `context`, `operation`
- `EmbeddingError`: Raised when embedding generation fails
  - Attributes: `text`, `model`
- `DocumentProcessingError`: Raised when document processing fails (loading, parsing, chunking)
  - Attributes: `document_id`, `file_path`, `operation`
- `ChunkingError`: Raised when document chunking fails
  - Attributes: `document_id`, `chunking_strategy`
- `ValidationError`: Raised when validation fails (e.g., empty content, invalid format)
  - Attributes: `field`, `value`

### Usage Examples

```python
from src.core.rag.exceptions import (
    RetrievalError,
    GenerationError,
    EmbeddingError,
    DocumentProcessingError
)

try:
    results = retriever.retrieve(query, top_k=5)
except RetrievalError as e:
    logger.error(f"Retrieval failed for query '{e.query}': {e.message}")
    # Handle retrieval failure
except EmbeddingError as e:
    logger.error(f"Embedding generation failed: {e.message}")
    # Handle embedding failure
except DocumentProcessingError as e:
    logger.error(f"Document processing failed for {e.file_path}: {e.message}")
    # Handle document processing failure
```

### Error Handling Levels

The RAG system implements error handling for:
- **Document Processing Errors**: Wrapped in `DocumentProcessingError` or `ChunkingError`
- **Retrieval Errors**: Wrapped in `RetrievalError` with query context
- **Generation Errors**: Wrapped in `GenerationError` with query and context
- **Embedding Errors**: Wrapped in `EmbeddingError` with text and model information
- **Validation Errors**: Wrapped in `ValidationError` with field and value information
- **Database Errors**: Caught and reported with appropriate context

## Enhanced Chunking Pipeline

The RAG system now includes a comprehensive chunking pipeline with advanced features:

### Preprocessing Steps

1. **Text Normalization**: Normalizes whitespace, removes control characters, handles unicode
2. **Content Cleaning**: Removes artifacts and normalizes formatting
3. **Encoding Handling**: Properly handles various text encodings

### Chunking Strategies

- **Fixed**: Fixed-size chunks with word boundary awareness
- **Sentence**: Chunks by sentences, preserving sentence boundaries
- **Paragraph**: Chunks by paragraphs, handling large paragraphs intelligently
- **Semantic**: Chunks by semantic boundaries (headers, sections) for structured documents

### Chunk Validation

- **Size Validation**: Filters chunks that are too small or too large
- **Content Validation**: Ensures chunks contain meaningful content
- **Quality Checks**: Validates chunk quality before embedding

### Metadata Handling

The system provides comprehensive metadata management:

1. **Automatic Extraction**:
   - Title extraction from content or file
   - Date extraction from various formats
   - Tag/keyword extraction (hashtags)
   - Language detection
   - File metadata (name, size, extension, modification date)

2. **Metadata Validation**:
   - Schema-based validation
   - Type checking
   - Required field validation

3. **Metadata Enrichment**:
   - Document-level metadata automatically added to chunks
   - Chunk-specific metadata (index, position, token count)
   - Merged metadata from multiple sources

4. **Metadata Schema**:
   - Define custom metadata schemas
   - Validate metadata against schemas
   - Ensure consistency across documents

### File Format Support

- **Text Files**: `.txt`, `.md`, `.markdown`
- **HTML Files**: Extracts text content from HTML
- **JSON Files**: Converts JSON to readable text format
- **Extensible**: Architecture supports adding more formats

**Example:**
```python
from src.core.rag import create_document_processor

# Create processor with enhanced features
processor = create_document_processor(
    chunk_size=1000,
    chunk_overlap=200,
    chunking_strategy="semantic",  # Use semantic chunking
    min_chunk_size=100,  # Filter chunks smaller than 100 chars
    max_chunk_size=2000,  # Split chunks larger than 2000 chars
    enable_preprocessing=True,  # Enable text preprocessing
    enable_metadata_extraction=True  # Enable automatic metadata extraction
)

# Process document with metadata extraction
content, metadata = processor.load_document("document.txt")
chunks = processor.chunk_document(content, "doc_123", metadata)
```

## Best Practices

1. **Chunk Size Optimization**: Choose appropriate chunk sizes based on document types and use cases
2. **Chunking Strategy**: Use semantic chunking for structured documents (markdown, HTML), sentence chunking for narrative text
3. **Embedding Model Consistency**: Use the same embedding model for both ingestion and retrieval
4. **Metadata Management**: Leverage automatic metadata extraction and maintain rich metadata for effective filtering and organization
5. **Preprocessing**: Enable preprocessing for cleaner, more consistent chunks
6. **Chunk Validation**: Set appropriate min/max chunk sizes to filter low-quality chunks
7. **Similarity Threshold Tuning**: Adjust similarity thresholds to balance recall and precision
8. **Context Length Management**: Consider token limits when building context from retrieved documents
9. **Caching Strategy**: Implement caching for frequently accessed documents and queries
10. **Batch Processing**: Use `ingest_documents_batch()` or `ingest_documents_batch_async()` for ingesting multiple documents to leverage batch optimization
11. **Async Processing**: Use async methods (`ingest_document_async()`, `query_async()`) for better concurrency and throughput
12. **Re-ranking**: Enable re-ranking for improved relevance, especially for top-k retrieval
13. **Document Versioning**: Use versioning for documents that change frequently to track history
14. **Incremental Updates**: Use incremental updates for large documents to avoid full re-embedding
15. **Document Validation**: Enable validation to ensure document quality and compliance
16. **Real-time Sync**: Use real-time synchronization for documents that change frequently
17. **Relevance Scoring**: Use relevance scores to filter and rank retrieved documents

## Examples and Tests

### Working Examples

See the following examples for RAG system usage:

- **Basic RAG Example**: `examples/basic_usage/09_rag_basic.py` - Basic RAG operations including document ingestion and querying
- **Agent with RAG**: `examples/integration/agent_with_rag.py` - Integration example showing agent using RAG for context
- **Complete Q&A System**: `examples/end_to_end/complete_qa_system.py` - End-to-end example with RAG system

### Tests

- **Unit Tests**: `src/tests/unit_tests/test_rag.py` - Comprehensive unit tests for RAG components
- **Integration Tests**: `src/tests/integration_tests/test_agent_rag_integration.py` - Agent-RAG integration tests

For more examples and test documentation, see:
- `examples/README.md` - Complete examples documentation
- `src/tests/unit_tests/README.md` - Unit tests documentation
