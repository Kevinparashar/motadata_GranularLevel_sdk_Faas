# Vector Database

## Overview

The Vector Database component provides specialized vector operations using PostgreSQL's pgvector extension. It enables efficient storage, indexing, and similarity search of high-dimensional vectors (embeddings) that are essential for RAG systems, semantic search, and other embedding-based applications.

## Purpose and Functionality

This component extends the PostgreSQL Database component with vector-specific capabilities. It provides:
- **Vector Storage**: Efficient storage of high-dimensional embedding vectors
- **Similarity Search**: Fast similarity search using cosine distance, L2 distance, or inner product
- **Indexing Support**: Support for IVFFlat and HNSW indexes for optimal performance
- **Metadata Integration**: Combines vector search with metadata filtering

The component leverages pgvector's native vector data type and operators to provide efficient vector operations that would be difficult to implement with standard SQL.

## Connection to Other Components

### Integration with RAG System

The **RAG System** (`src/core/rag/`) is the primary consumer of vector database operations. The RAG system uses this component for:
1. **Embedding Storage**: When documents are ingested, their embeddings are stored using the vector database's storage methods
2. **Similarity Search**: The RAG retriever uses the vector database's similarity search to find relevant documents for queries
3. **Result Ranking**: Search results are ranked by similarity scores provided by the vector database

The RAG system's retriever component directly calls the vector database's similarity search methods to find relevant documents.

### Integration with PostgreSQL Database

The **PostgreSQL Database** (`src/core/postgresql_database/`) provides the underlying database infrastructure. The vector database component extends the database connection with vector-specific operations. It uses the database connection for executing vector queries and managing vector data.

### Integration with LiteLLM Gateway

The **LiteLLM Gateway** (`src/core/litellm_gateway/`) is used indirectly through the RAG system. When embeddings need to be generated for storage or queries, the gateway is used, and those embeddings are then stored or searched using the vector database. The gateway doesn't directly interact with the vector database, but the data flow connects them.

### Integration with Evaluation & Observability

The **Evaluation & Observability** component (`src/core/evaluation_observability/`) can monitor vector database operations:
- **Search Performance**: Tracks similarity search query times
- **Index Performance**: Monitors index usage and effectiveness
- **Storage Metrics**: Tracks vector storage and retrieval patterns

This monitoring helps optimize vector database performance.

## Libraries Utilized

- **pgvector**: PostgreSQL extension that provides the `vector` data type and similarity operators. It enables efficient vector storage and search directly in PostgreSQL.
- **psycopg2**: Used for executing vector queries and managing database connections.

## Key Features

### Vector Storage

The component provides efficient vector storage:
- **Native Vector Type**: Uses pgvector's native `vector` data type
- **Batch Operations**: Supports batch insertion of vectors for performance
- **Metadata Association**: Associates vectors with document metadata

### Similarity Search

Similarity search capabilities include:
- **Cosine Similarity**: Measures angle between vectors, best for normalized embeddings
- **L2 Distance**: Euclidean distance, measures straight-line distance
- **Inner Product**: Dot product, useful for certain embedding types
- **Threshold Filtering**: Filters results by similarity threshold
- **Limit Control**: Limits number of results returned

### Indexing

Index support for performance:
- **IVFFlat Index**: Fast approximate search, good for datasets up to ~1M vectors
- **HNSW Index**: Hierarchical Navigable Small World, very fast for high-dimensional data, good for larger datasets
- **Index Tuning**: Configurable parameters for optimal performance

## Distance Metrics

### Cosine Distance

Best for normalized embeddings, measures the angle between vectors. This is the most commonly used metric for text embeddings as it focuses on direction rather than magnitude.

### L2 Distance

Euclidean distance, measures straight-line distance between vectors. Useful when vector magnitudes are meaningful.

### Inner Product

Dot product of vectors. Useful for certain types of embeddings where inner product is more meaningful than distance.

## Index Types

### IVFFlat Index

Fast approximate search using inverted file index with flat compression. Good for smaller to medium-sized datasets. Requires careful tuning of the `lists` parameter based on dataset size.

### HNSW Index

Hierarchical Navigable Small World graph-based index. Very fast for high-dimensional data and large datasets. Requires tuning of `m` (connections per layer) and `ef_construction` (candidate list size) parameters.

## Performance Considerations

### Index Selection

- **Small Datasets (< 1M vectors)**: IVFFlat index is typically sufficient
- **Large Datasets (> 1M vectors)**: HNSW index provides better performance
- **Exact Search**: For exact search, no index may be needed for small datasets

### Query Optimization

- **Appropriate Limits**: Use reasonable limits to avoid returning too many results
- **Threshold Filtering**: Use similarity thresholds to filter low-quality results
- **Metadata Filtering**: Combine vector search with metadata filters when possible

### Batch Operations

Batch operations are significantly faster than individual operations:
- **Batch Insertion**: Insert multiple vectors in a single operation
- **Reduced Overhead**: Minimizes database round-trips and transaction overhead

## Error Handling

The component handles:
- **Vector Dimension Mismatches**: Validates vector dimensions match expected sizes
- **Index Errors**: Handles index creation and usage errors
- **Query Errors**: Catches and reports query execution errors
- **Connection Errors**: Manages database connection failures

## Best Practices

1. **Index Selection**: Choose the appropriate index type based on dataset size
2. **Vector Normalization**: Normalize embeddings for cosine similarity
3. **Parameter Tuning**: Tune index parameters based on data characteristics
4. **Performance Monitoring**: Monitor query latency and optimize as needed
5. **Batch Operations**: Use batch operations for better performance
6. **Dimension Consistency**: Maintain consistent embedding dimensions
7. **Threshold Tuning**: Adjust similarity thresholds based on use case requirements
