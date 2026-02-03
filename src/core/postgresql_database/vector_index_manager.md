# MOTADATA - VECTOR INDEX MANAGER DOCUMENTATION

This document explains the **Vector Index Manager** used by the PostgreSQL + pgvector layer.

## What it does

The vector index manager helps you:

- create vector indexes (for faster similarity search)
- choose an index type (example: IVFFlat, HNSW)
- reindex when needed
- manage index configuration in a consistent way

## Where the code is

- Implementation: `src/core/postgresql_database/vector_index_manager.py`
- Used by: `src/core/rag/rag_system.py` and `src/core/postgresql_database/vector_operations.py`

## When you need this

You should look at index management when:

- similarity search becomes slow as data grows
- you change embedding dimension or model behaviour
- you want better latency in production


