# RAG System

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

The **Cache Mechanism** (`src/core/cache_mechanism/`) can be used to cache:
- **Query Results**: Frequently asked questions can be cached to reduce LLM API calls
- **Embeddings**: Document embeddings can be cached to avoid regenerating them
- **Retrieved Documents**: Retrieved document sets can be cached for similar queries

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

## Key Components

### DocumentProcessor

The `DocumentProcessor` class handles document preprocessing:
- **Chunking Strategies**: Supports fixed-size, sentence-based, and paragraph-based chunking
- **Metadata Preservation**: Maintains document metadata throughout processing
- **Chunk Identification**: Generates unique identifiers for document chunks

### Retriever

The `Retriever` class performs document retrieval:
- **Query Embedding**: Converts text queries into vector embeddings using the gateway
- **Similarity Search**: Uses the database's vector operations to find similar documents
- **Result Filtering**: Applies metadata filters to refine search results

### RAGGenerator

The `RAGGenerator` class generates context-aware responses:
- **Context Building**: Constructs context strings from retrieved documents
- **Prompt Construction**: Builds prompts that include retrieved context
- **Response Generation**: Uses the gateway to generate responses based on context

### RAGSystem

The `RAGSystem` class integrates all components:
- **Document Ingestion**: Orchestrates the complete document ingestion pipeline
- **Query Processing**: Handles end-to-end query processing from retrieval to generation
- **Component Coordination**: Manages interactions between processor, retriever, and generator

## Document Ingestion Flow

1. **Document Input**: A document is provided with title, content, and optional metadata
2. **Document Storage**: The document is stored in the database
3. **Chunking**: The document processor splits the document into chunks
4. **Batch Embedding Generation**: All chunks are embedded in a single batch API call using the LiteLLM Gateway (optimized for performance)
5. **Batch Embedding Storage**: All embeddings are stored in the database with pgvector using batch insert

**Optimization**: The system now uses batch processing to embed all chunks in one API call instead of individual calls, significantly improving performance and reducing costs.

## Query Processing Flow

1. **Query Input**: A user query is received
2. **Query Embedding**: The query is converted to an embedding using the gateway
3. **Similarity Search**: The database performs similarity search to find relevant documents
4. **Context Building**: Retrieved documents are formatted into context
5. **Response Generation**: The gateway generates a response using the context and query
6. **Response Return**: The generated response is returned along with retrieved documents

## Error Handling

The RAG system implements error handling for:
- **Document Processing Errors**: Handles failures during chunking or embedding generation
- **Retrieval Errors**: Manages cases where no relevant documents are found
- **Generation Errors**: Handles LLM generation failures with appropriate fallbacks
- **Database Errors**: Catches and reports database operation failures

## Best Practices

1. **Chunk Size Optimization**: Choose appropriate chunk sizes based on document types and use cases
2. **Embedding Model Consistency**: Use the same embedding model for both ingestion and retrieval
3. **Metadata Management**: Maintain rich metadata for effective filtering and organization
4. **Similarity Threshold Tuning**: Adjust similarity thresholds to balance recall and precision
5. **Context Length Management**: Consider token limits when building context from retrieved documents
6. **Caching Strategy**: Implement caching for frequently accessed documents and queries
7. **Batch Processing**: Use `ingest_documents_batch()` or `ingest_documents_batch_async()` for ingesting multiple documents to leverage batch optimization
8. **Async Processing**: Use async methods (`ingest_document_async()`, `query_async()`) for better concurrency and throughput

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
