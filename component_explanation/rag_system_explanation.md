# RAG System - Comprehensive Component Explanation

## Overview

The RAG (Retrieval-Augmented Generation) System is a comprehensive solution for building context-aware AI applications. It combines document retrieval with LLM generation to provide accurate, contextually relevant responses based on a knowledge base of documents.

## Table of Contents

1. [Document Processing](#document-processing)
2. [Document Retrieval](#document-retrieval)
3. [Response Generation](#response-generation)
4. [Memory Integration](#memory-integration)
5. [Exception Handling](#exception-handling)
6. [Functions](#functions)
7. [Workflow](#workflow)
8. [Customization](#customization)

---

## Document Processing

### Functionality

Document processing handles the ingestion and preparation of documents for retrieval:
- **Document Loading**: Loads documents from various sources (text, HTML, JSON)
- **Preprocessing**: Normalizes text, cleans content, handles encoding
- **Chunking**: Splits documents into manageable chunks using multiple strategies
- **Metadata Extraction**: Automatically extracts metadata (title, dates, tags, language)
- **Metadata Validation**: Validates metadata against schemas
- **Embedding Generation**: Generates vector embeddings for chunks

### Code Examples

#### Document Ingestion

```python
from src.core.rag import create_rag_system
from src.core.postgresql_database import DatabaseConnection
from src.core.litellm_gateway import LiteLLMGateway

# Initialize dependencies
db = DatabaseConnection(...)
gateway = LiteLLMGateway(...)

# Create RAG system
rag = create_rag_system(
    db=db,
    gateway=gateway,
    embedding_model="text-embedding-3-small",
    generation_model="gpt-4"
)

# Ingest document
document_id = rag.ingest_document(
    title="AI Guide",
    content="Artificial Intelligence is...",
    tenant_id="tenant_123",
    source="https://example.com/ai-guide",
    metadata={
        "author": "John Doe",
        "category": "tutorial",
        "tags": ["ai", "ml", "tutorial"]
    }
)
```

#### Document Processing with Custom Configuration

```python
from src.core.rag import create_document_processor

# Create document processor with custom configuration
processor = create_document_processor(
    chunk_size=1000,              # Characters per chunk
    chunk_overlap=200,            # Overlap between chunks
    chunking_strategy="semantic",  # Strategy: fixed, sentence, paragraph, semantic
    min_chunk_size=100,           # Minimum chunk size
    max_chunk_size=2000,          # Maximum chunk size
    enable_preprocessing=True,    # Enable text preprocessing
    enable_metadata_extraction=True  # Enable automatic metadata extraction
)

# Process document
chunks = processor.chunk_document(
    content=document_content,
    document_id="doc_123",
    metadata={"title": "Document Title"}
)
```

---

## Document Retrieval

### Functionality

Document retrieval finds relevant documents for queries:
- **Query Embedding**: Converts queries into vector embeddings
- **Vector Search**: Performs similarity search using embeddings
- **Hybrid Retrieval**: Combines vector and keyword search
- **Result Filtering**: Applies metadata filters
- **Relevance Scoring**: Scores and ranks retrieved documents

### Code Examples

#### Basic Retrieval

```python
# Retrieve documents
retrieved_docs = rag.retriever.retrieve(
    query="What is artificial intelligence?",
    tenant_id="tenant_123",
    top_k=5,
    threshold=0.7,
    filters={"category": "tutorial"}
)

for doc in retrieved_docs:
    print(f"Title: {doc['title']}")
    print(f"Similarity: {doc['similarity']}")
    print(f"Content: {doc['content'][:100]}...")
```

#### Hybrid Retrieval

```python
# Hybrid retrieval (vector + keyword)
retrieved_docs = rag.retriever.retrieve_hybrid(
    query="machine learning algorithms",
    tenant_id="tenant_123",
    top_k=10,
    threshold=0.6,
    vector_weight=0.7,  # 70% weight for vector search
    keyword_weight=0.3  # 30% weight for keyword search
)
```

---

## Response Generation

### Functionality

Response generation creates context-aware answers:
- **Context Building**: Constructs context from retrieved documents
- **Prompt Construction**: Builds prompts with context and query
- **LLM Generation**: Generates responses using the gateway
- **Response Formatting**: Formats responses for consumption

### Code Examples

#### Generate Response

```python
# Generate response with retrieved context
answer = rag.generator.generate(
    query="What is AI?",
    context_documents=retrieved_docs,
    max_tokens=1000,
    temperature=0.7
)

print(answer)
```

#### Complete RAG Query

```python
# Complete RAG query (retrieval + generation)
result = rag.query(
    query="What is machine learning?",
    tenant_id="tenant_123",
    top_k=5,
    threshold=0.7,
    max_tokens=1000,
    use_query_rewriting=True,
    retrieval_strategy="hybrid"
)

print(f"Answer: {result['answer']}")
print(f"Retrieved {result['num_documents']} documents")
```

---

## Memory Integration

### Functionality

The RAG system integrates with **Agent Memory** to provide conversation context:

- **Conversation History**: Retrieves previous queries and answers for context
- **User Preferences**: Remembers user-specific preferences and patterns
- **Context Enhancement**: Enhances query context with relevant memories
- **Query-Answer Storage**: Stores query-answer pairs in episodic memory
- **Automatic Context Building**: Automatically builds context from memory before query processing

### Code Examples

#### RAG with Memory Enabled

```python
from src.core.rag import create_rag_system

# Create RAG with memory enabled (default)
rag = create_rag_system(
    db=db,
    gateway=gateway,
    enable_memory=True,  # Enable conversation memory
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

#### Memory-Enhanced Query Processing

When memory is enabled, the query process includes:

1. **Memory Retrieval**: Retrieves relevant episodic and semantic memories
2. **Context Building**: Builds conversation context from memories
3. **Query Enhancement**: Enhances query with conversation context
4. **Response Generation**: Generates response with enhanced context
5. **Memory Storage**: Stores query-answer pair in episodic memory

```python
# First query
result1 = rag.query(
    query="What is machine learning?",
    user_id="user123",
    conversation_id="conv456",
    tenant_id="tenant1"
)

# Second query - memory provides context
result2 = rag.query(
    query="Can you explain it in simpler terms?",
    user_id="user123",
    conversation_id="conv456",  # Same conversation
    tenant_id="tenant1"
)
# Memory automatically includes context from first query
```

---

## Exception Handling

### Exception Hierarchy

The RAG system uses a structured exception hierarchy:

```
SDKError (Base)
└── RAGError
    ├── RetrievalError
    ├── GenerationError
    ├── EmbeddingError
    ├── DocumentProcessingError
    ├── ChunkingError
    └── ValidationError
```

### Code Examples

```python
from src.core.rag.exceptions import (
    RetrievalError,
    GenerationError,
    EmbeddingError,
    DocumentProcessingError
)

try:
    result = rag.query("What is AI?", tenant_id="tenant_123")
except RetrievalError as e:
    print(f"Retrieval failed: {e.message}")
    print(f"Query: {e.query}")
except GenerationError as e:
    print(f"Generation failed: {e.message}")
    print(f"Context: {e.context}")
except EmbeddingError as e:
    print(f"Embedding failed: {e.message}")
    print(f"Model: {e.model}")
except DocumentProcessingError as e:
    print(f"Document processing failed: {e.message}")
    print(f"Document ID: {e.document_id}")
```

---

## Functions

### Factory Functions

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
    chunk_size=1000,
    chunk_overlap=200,
    chunking_strategy="semantic"
)
```

### Convenience Functions

```python
from src.core.rag import (
    quick_rag_query,
    ingest_document_simple,
    batch_ingest_documents
)

# Quick RAG query
result = quick_rag_query(
    rag,
    "What is AI?",
    tenant_id="tenant_123",
    top_k=5
)

# Simple document ingestion
doc_id = ingest_document_simple(
    rag,
    "AI Guide",
    "Content...",
    tenant_id="tenant_123"
)

# Batch ingestion
doc_ids = batch_ingest_documents(
    rag,
    documents=[
        {"title": "Doc 1", "content": "..."},
        {"title": "Doc 2", "content": "..."}
    ],
    tenant_id="tenant_123"
)
```

---

## Workflow

### Component Placement in SDK Architecture

The RAG System is positioned in the **Application Layer** and integrates with multiple infrastructure components:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SDK ARCHITECTURE OVERVIEW                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              RAG SYSTEM (Application Layer)               │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │  Document    │  │  Retriever   │  │  Generator   │  │   │
│  │  │  Processor   │  │              │  │              │  │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │   │
│  │         │                 │                  │          │   │
│  │         └─────────────────┼──────────────────┘          │   │
│  │                           │                             │   │
│  │                    ┌──────▼───────┐                     │   │
│  │                    │  RAGSystem   │                     │   │
│  │                    │  (Orchestrator)                     │   │
│  │                    └──────┬───────┘                     │   │
│  └───────────────────────────┼─────────────────────────────┘   │
│                              │                                   │
┌───────────────────────────────┼───────────────────────────────────┐
│                               │                                   │
│  ┌────────────────────────────▼──────────────────────────────┐   │
│  │              INFRASTRUCTURE LAYER                          │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │   │
│  │  │LiteLLM       │  │  PostgreSQL  │  │    Cache     │   │   │
│  │  │Gateway       │  │  Database    │  │  Mechanism   │   │   │
│  │  │              │  │              │  │              │   │   │
│  │  │ - embed()    │  │ - Vector     │  │ - Query      │   │   │
│  │  │ - generate() │  │   Search     │  │   Caching    │   │   │
│  │  │              │  │ - Document   │  │ - Result     │   │   │
│  │  │              │  │   Storage    │  │   Caching    │   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
```

### Document Ingestion Workflow

The following diagram shows the complete flow of document ingestion:

```
┌─────────────────────────────────────────────────────────────────┐
│              DOCUMENT INGESTION WORKFLOW                         │
└─────────────────────────────────────────────────────────────────┘

    [Document Input]
           │
           │ Parameters:
           │ - title: str
           │ - content: str
           │ - tenant_id: Optional[str]
           │ - source: Optional[str]
           │ - metadata: Optional[Dict]
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 1: Document Storage                                │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ rag.ingest_document(title, content, tenant_id)   │  │
    │  │                                                   │  │
    │  │ Code Flow:                                       │  │
    │  │ 1. Validate input parameters                     │  │
    │  │ 2. Insert document into database:                │  │
    │  │    INSERT INTO documents (                        │  │
    │  │        title, content, metadata,                  │  │
    │  │        source, tenant_id                          │  │
    │  │    ) VALUES (...)                                │  │
    │  │ 3. Get document_id from database                 │  │
    │  │                                                   │  │
    │  │ Database Fields:                                  │  │
    │  │ - id: UUID (auto-generated)                      │  │
    │  │ - title: str                                     │  │
    │  │ - content: text                                  │  │
    │  │ - metadata: jsonb                                │  │
    │  │ - source: str (optional)                         │  │
    │  │ - tenant_id: str (for isolation)                 │  │
    │  │ - created_at: timestamp                          │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 2: Document Preprocessing                         │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ processor.chunk_document(content, document_id)    │  │
    │  │                                                   │  │
    │  │ Preprocessing Steps:                              │  │
    │  │ 1. Text normalization                             │  │
    │  │    - Normalize whitespace                         │  │
    │  │    - Remove control characters                    │  │
    │  │    - Handle unicode                               │  │
    │  │ 2. Content cleaning                               │  │
    │  │    - Remove artifacts                             │  │
    │  │    - Normalize formatting                         │  │
    │  │ 3. Encoding handling                              │  │
    │  │    - Detect encoding                              │  │
    │  │    - Convert to UTF-8                            │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 3: Metadata Extraction                             │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ if enable_metadata_extraction:                     │  │
    │  │     metadata = extract_metadata(content)          │  │
    │  │                                                   │  │
    │  │ Extracted Metadata:                                │  │
    │  │ - title: str (from content or file)              │  │
    │  │ - dates: List[str] (various formats)              │  │
    │  │ - tags: List[str] (hashtags, keywords)           │  │
    │  │ - language: str (detected language)               │  │
    │  │ - file_info: Dict (name, size, extension)        │  │
    │  │                                                   │  │
    │  │ Metadata Validation:                               │  │
    │  │ - Schema validation (if schema provided)         │  │
    │  │ - Type checking                                   │  │
    │  │ - Required field validation                      │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 4: Document Chunking                               │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ chunks = processor.chunk_document(                │  │
    │  │     content=preprocessed_content,                  │  │
    │  │     document_id=document_id,                       │  │
    │  │     metadata=enriched_metadata                     │  │
    │  │ )                                                 │  │
    │  │                                                   │  │
    │  │ Chunking Strategies:                               │  │
    │  │ 1. Fixed: Fixed-size chunks with overlap         │  │
    │  │    - chunk_size: int (default: 1000)             │  │
    │  │    - chunk_overlap: int (default: 200)           │  │
    │  │                                                   │  │
    │  │ 2. Sentence: Chunks by sentences                 │  │
    │  │    - Preserves sentence boundaries                │  │
    │  │    - Better for narrative text                   │  │
    │  │                                                   │  │
    │  │ 3. Paragraph: Chunks by paragraphs                │  │
    │  │    - Preserves paragraph structure                │  │
    │  │    - Handles large paragraphs intelligently      │  │
    │  │                                                   │  │
    │  │ 4. Semantic: Chunks by semantic boundaries       │  │
    │  │    - Chunks by headers and sections              │  │
    │  │    - Better for structured documents            │  │
    │  │                                                   │  │
    │  │ Chunk Validation:                                  │  │
    │  │ - Size validation (min_chunk_size, max_chunk_size)│
    │  │ - Content validation (non-empty, meaningful)     │  │
    │  │ - Quality checks                                  │  │
    │  │                                                   │  │
    │  │ Chunk Metadata:                                    │  │
    │  │ - chunk_id: str (unique identifier)              │  │
    │  │ - chunk_index: int (position in document)        │  │
    │  │ - token_count: int (estimated tokens)            │  │
    │  │ - Document-level metadata (inherited)            │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 5: Batch Embedding Generation                     │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ chunk_texts = [chunk.content for chunk in chunks] │  │
    │  │                                                   │  │
    │  │ try:                                              │  │
    │  │     # Single batch API call                       │  │
    │  │     embedding_response = gateway.embed(            │  │
    │  │         texts=chunk_texts,                        │  │
    │  │         model=embedding_model                      │  │
    │  │     )                                             │  │
    │  │     embeddings = embedding_response.embeddings    │  │
    │  │ except Exception:                                 │  │
    │  │     # Fallback to individual processing           │  │
    │  │     embeddings = []                               │  │
    │  │     for chunk in chunks:                          │  │
    │  │         embedding = gateway.embed([chunk.content])│
    │  │         embeddings.append(embedding)              │  │
    │  │                                                   │  │
    │  │ Embedding Parameters:                              │  │
    │  │ - texts: List[str] (chunk contents)              │  │
    │  │ - model: str (embedding model name)              │  │
    │  │ - tenant_id: Optional[str] (for tracking)       │  │
    │  │                                                   │  │
    │  │ Embedding Response:                               │  │
    │  │ - embeddings: List[List[float]] (vectors)       │  │
    │  │ - model: str (model used)                        │  │
    │  │ - usage: Dict (token usage)                      │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 6: Embedding Storage                              │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ embeddings_data = []                              │  │
    │  │ for i, embedding in enumerate(embeddings):        │  │
    │  │     embeddings_data.append((                      │  │
    │  │         document_id,                              │  │
    │  │         embedding,                                │  │
    │  │         embedding_model                           │  │
    │  │     ))                                            │  │
    │  │                                                   │  │
    │  │ # Batch insert embeddings                         │  │
    │  │ vector_ops.batch_insert_embeddings(              │  │
    │  │     embeddings_data                               │  │
    │  │ )                                                 │  │
    │  │                                                   │  │
    │  │ Database Storage:                                 │  │
    │  │ - embeddings table:                              │  │
    │  │   - id: UUID                                     │  │
    │  │   - document_id: UUID (FK to documents)         │  │
    │  │   - chunk_id: str                                │  │
    │  │   - embedding: vector (pgvector)                 │  │
    │  │   - model: str                                   │  │
    │  │   - tenant_id: str (for isolation)              │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    [Return document_id]
```

### Query Processing Workflow

The following diagram shows the complete flow of query processing:

```
┌─────────────────────────────────────────────────────────────────┐
│              QUERY PROCESSING WORKFLOW                           │
└─────────────────────────────────────────────────────────────────┘

    [User Query]
           │
           │ Parameters:
           │ - query: str
           │ - tenant_id: Optional[str]
           │ - top_k: int
           │ - threshold: float
           │ - max_tokens: int
           │ - use_query_rewriting: bool
           │ - retrieval_strategy: str
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 1: Query Rewriting (Optional)                      │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ if use_query_rewriting:                            │  │
    │  │     rewritten_query = rag._rewrite_query(query)    │  │
    │  │                                                   │  │
    │  │ Rewriting Steps:                                   │  │
    │  │ 1. Expand abbreviations:                          │  │
    │  │    "AI" → "artificial intelligence"               │  │
    │  │    "ML" → "machine learning"                      │  │
    │  │ 2. Normalize terms                                │  │
    │  │ 3. Remove extra whitespace                        │  │
    │  │                                                   │  │
    │  │ Benefits:                                          │  │
    │  │ - Better retrieval quality                        │  │
    │  │ - Improved semantic matching                      │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 2: Cache Check                                    │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ cache_key = f"rag:query:{tenant_id}:{query}:..." │  │
    │  │ cached_result = cache.get(cache_key)              │  │
    │  │ if cached_result:                                  │  │
    │  │     return cached_result  # Early return          │  │
    │  │                                                   │  │
    │  │ Cache Key Components:                              │  │
    │  │ - tenant_id (for isolation)                       │  │
    │  │ - query (rewritten if applicable)                │  │
    │  │ - top_k                                           │  │
    │  │ - threshold                                       │  │
    │  │ - max_tokens                                      │  │
    │  │ - retrieval_strategy                              │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 3: Query Embedding                                 │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ query_embedding = retriever._get_embedding(query) │  │
    │  │                                                   │  │
    │  │ Code Flow:                                       │  │
    │  │ 1. Call gateway.embed() with query text          │  │
    │  │ 2. Get embedding vector from response           │  │
    │  │ 3. Return embedding as List[float]              │  │
    │  │                                                   │  │
    │  │ Embedding Parameters:                             │  │
    │  │ - texts: List[str] (query text)                 │  │
    │  │ - model: str (embedding model)                  │  │
    │  │ - tenant_id: Optional[str]                      │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 4: Document Retrieval                              │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ if retrieval_strategy == "hybrid":                │  │
    │  │     docs = retriever.retrieve_hybrid(...)         │  │
    │  │ else:                                             │  │
    │  │     docs = retriever.retrieve(...)                │  │
    │  │                                                   │  │
    │  │ Vector Search:                                     │  │
    │  │ 1. similarity_search(query_embedding)            │  │
    │  │ 2. Filter by tenant_id (if provided)            │  │
    │  │ 3. Apply similarity threshold                    │  │
    │  │ 4. Return top_k results                          │  │
    │  │                                                   │  │
    │  │ Hybrid Search:                                    │  │
    │  │ 1. Vector search (semantic similarity)          │  │
    │  │ 2. Keyword search (text matching)                │  │
    │  │ 3. Combine results with weighted scoring        │  │
    │  │ 4. Return top_k results                          │  │
    │  │                                                   │  │
    │  │ Retrieved Document Structure:                     │  │
    │  │ - id: str (document ID)                          │  │
    │  │ - title: str                                     │  │
    │  │ - content: str (chunk content)                  │  │
    │  │ - similarity: float (0.0-1.0)                    │  │
    │  │ - metadata: Dict                                │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 5: Context Building                                │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ context = generator._build_context(documents)     │  │
    │  │                                                   │  │
    │  │ Context Format:                                   │  │
    │  │ [Document 1: Title (Similarity: 0.95)]           │  │
    │  │ Content...                                        │  │
    │  │ ---                                               │  │
    │  │ [Document 2: Title (Similarity: 0.87)]           │  │
    │  │ Content...                                        │  │
    │  │                                                   │  │
    │  │ Context Building:                                 │  │
    │  │ 1. Iterate through retrieved documents           │  │
    │  │ 2. Format each document with title and similarity│
    │  │ 3. Join documents with separator                 │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 6: Prompt Construction                            │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ prompt = generator._build_prompt(query, context) │  │
    │  │                                                   │  │
    │  │ Prompt Template:                                  │  │
    │  │ "Based on the following context, please answer   │  │
    │  │  the question.                                    │  │
    │  │                                                   │  │
    │  │  Context:                                          │  │
    │  │  {context}                                         │  │
    │  │                                                   │  │
    │  │  Question: {query}                                │  │
    │  │                                                   │  │
    │  │  Answer:"                                          │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 7: LLM Generation                                 │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ response = gateway.generate_async(                │  │
    │  │     prompt=prompt,                                │  │
    │  │     model=generation_model,                        │  │
    │  │     max_tokens=max_tokens,                         │  │
    │  │     temperature=0.7,                               │  │
    │  │     tenant_id=tenant_id                            │  │
    │  │ )                                                 │  │
    │  │                                                   │  │
    │  │ answer = response.text                            │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────┐
    │  STEP 8: Result Caching                                │
    │  ┌───────────────────────────────────────────────────┐  │
    │  │ result = {                                        │  │
    │  │     "answer": answer,                             │  │
    │  │     "retrieved_documents": documents,             │  │
    │  │     "num_documents": len(documents),              │  │
    │  │     "query_used": rewritten_query,                │  │
    │  │     "original_query": original_query               │  │
    │  │ }                                                 │  │
    │  │                                                   │  │
    │  │ cache.set(cache_key, result, ttl=300)             │  │
    │  │                                                   │  │
    │  │ Cache TTL: 300 seconds (5 minutes)               │  │
    │  └───────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
           │
           ▼
    [Return Result Dictionary]
```

### Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│              COMPONENT INTERACTION FLOW                          │
└─────────────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │  RAGSystem   │
                    │ (Orchestrator)│
                    └──────┬───────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│Document       │  │  Retriever    │  │  Generator    │
│Processor      │  │               │  │               │
│               │  │ Functions:    │  │ Functions:    │
│ Functions:    │  │ - retrieve()  │  │ - generate() │
│ - chunk()     │  │ - retrieve_   │  │ - generate_  │
│ - preprocess()│  │   hybrid()    │  │   async()    │
│ - extract_    │  │ - _get_       │  │ - _build_    │
│   metadata()  │  │   embedding() │  │   context()  │
└───────┬───────┘  └───────┬───────┘  └───────┬───────┘
        │                  │                  │
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│LiteLLM Gateway│  │  PostgreSQL   │  │    Cache      │
│               │  │  Database     │  │  Mechanism    │
│ Functions:    │  │               │  │               │
│ - embed()     │  │ Functions:    │  │ Functions:    │
│ - generate()  │  │ - similarity_ │  │ - get()      │
│               │  │   search()    │  │ - set()      │
│               │  │ - batch_      │  │ - delete()   │
│               │  │   insert_     │  │              │
│               │  │   embeddings()│  │              │
└───────────────┘  └───────────────┘  └───────────────┘
```

### Parameter Details

#### ingest_document Parameters

```python
def ingest_document(
    self,
    title: str,                    # Document title
                                  # Required, non-empty string
                                  # Used for display and search

    content: str,                  # Document content
                                  # Required, non-empty string
                                  # Can be plain text, HTML, or JSON

    tenant_id: Optional[str] = None,  # Tenant identifier
                                  # Used for:
                                  #   - Document isolation
                                  #   - Embedding filtering
                                  #   - Query filtering
                                  #   - Cache isolation

    source: Optional[str] = None,  # Document source
                                  # Examples:
                                  #   - URL: "https://example.com/doc"
                                  #   - File path: "/path/to/file.txt"
                                  #   - Database ID: "db:12345"

    metadata: Optional[Dict[str, Any]] = None  # Document metadata
                                  # Common keys:
                                  #   - "author": str
                                  #   - "category": str
                                  #   - "tags": List[str]
                                  #   - "language": str
                                  #   - "created_at": str
                                  #   - "updated_at": str
                                  #   - Custom fields allowed
) -> str  # Returns document_id (UUID string)
```

#### query Parameters

```python
def query(
    self,
    query: str,                    # User query text
                                  # Required, non-empty string
                                  # Can include natural language

    tenant_id: Optional[str] = None,  # Tenant identifier
                                  # Filters documents by tenant
                                  # Ensures tenant isolation

    top_k: int = 5,               # Number of documents to retrieve
                                  # Range: 1 - 100
                                  # Higher = more context, slower

    threshold: float = 0.7,       # Minimum similarity threshold
                                  # Range: 0.0 - 1.0
                                  # Higher = stricter matching
                                  # Lower = more results

    max_tokens: int = 1000,       # Maximum tokens in response
                                  # Range: 100 - 4000
                                  # Limits response length

    use_query_rewriting: bool = True,  # Enable query rewriting
                                  # Expands abbreviations
                                  # Normalizes terms
                                  # Improves retrieval quality

    retrieval_strategy: str = "vector"  # Retrieval strategy
                                  # Values:
                                  #   - "vector": Vector search only
                                  #   - "hybrid": Vector + keyword
                                  #   - "keyword": Keyword search only
) -> Dict[str, Any]  # Returns result dictionary
```

#### Result Dictionary Structure

```python
{
    "answer": str,                 # Generated answer text
                                  # None if generation failed

    "retrieved_documents": List[Dict],  # Retrieved documents
                                  # Each dict contains:
                                  #   - "id": str
                                  #   - "title": str
                                  #   - "content": str
                                  #   - "similarity": float
                                  #   - "metadata": Dict

    "num_documents": int,         # Number of retrieved documents
                                  # 0 if no documents found

    "query_used": str,            # Query used for retrieval
                                  # Rewritten if rewriting enabled

    "original_query": str         # Original user query
                                  # Used for display
}
```

---

## Customization

### Configuration

```python
# Custom RAG system configuration
rag = create_rag_system(
    db=db,
    gateway=gateway,
    embedding_model="text-embedding-ada-002",  # Custom embedding model
    generation_model="gpt-4-turbo",            # Custom generation model
    cache=custom_cache,                        # Custom cache instance
    cache_config=CacheConfig(                  # Custom cache config
        default_ttl=600,                      # 10 minutes
        namespace="rag_cache"
    )
)
```

### Custom Document Processor

```python
# Custom document processor
processor = create_document_processor(
    chunk_size=2000,              # Larger chunks
    chunk_overlap=400,            # More overlap
    chunking_strategy="semantic",  # Semantic chunking
    min_chunk_size=200,           # Larger minimum
    max_chunk_size=4000,          # Larger maximum
    enable_preprocessing=True,
    enable_metadata_extraction=True,
    metadata_schema=CustomSchema()  # Custom schema
)
```

### Custom Retrieval Strategy

```python
# Custom hybrid retrieval weights
retrieved_docs = rag.retriever.retrieve_hybrid(
    query="custom query",
    tenant_id="tenant_123",
    top_k=10,
    threshold=0.6,
    vector_weight=0.8,  # 80% weight for vector
    keyword_weight=0.2  # 20% weight for keyword
)
```

---

## Best Practices

1. **Chunk Size**: Choose appropriate chunk sizes (500-2000 chars) based on document type
2. **Chunking Strategy**: Use semantic chunking for structured docs, sentence for narrative
3. **Embedding Model**: Use consistent embedding model for ingestion and retrieval
4. **Metadata**: Leverage metadata for better filtering and organization
5. **Query Rewriting**: Enable query rewriting for better retrieval quality
6. **Hybrid Retrieval**: Use hybrid retrieval for diverse query types
7. **Caching**: Enable caching for frequently asked questions
8. **Tenant Isolation**: Always provide tenant_id for multi-tenant deployments
9. **Error Handling**: Implement comprehensive error handling
10. **Monitoring**: Monitor retrieval quality and generation performance

---

## Additional Resources

- **Component README**: `src/core/rag/README.md`
- **Function Documentation**: `src/core/rag/functions.py`
- **Examples**: `examples/basic_usage/09_rag_basic.py`
- **Integration Examples**: `examples/integration/agent_with_rag.py`

