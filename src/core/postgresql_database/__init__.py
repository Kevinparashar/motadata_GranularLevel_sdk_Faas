"""
PostgreSQL Database Integration

PostgreSQL database with pgvector extension for vector operations.
"""


from .connection import DatabaseConfig, DatabaseConnection
from .setup import (
    create_documents_table,
    create_embeddings_table,
    create_pgvector_extension,
    setup_database,
    setup_vector_indexes,
    verify_pgvector_extension,
    verify_setup,
    verify_tables_exist,
)
from .vector_index_manager import (
    IndexDistance,
    IndexType,
    VectorIndexManager,
    create_vector_index_manager,
)

__all__ = [
    "DatabaseConnection",
    "DatabaseConfig",
    "VectorIndexManager",
    "create_vector_index_manager",
    "IndexType",
    "IndexDistance",
    # Setup functions
    "setup_database",
    "create_pgvector_extension",
    "verify_pgvector_extension",
    "create_embeddings_table",
    "create_documents_table",
    "verify_tables_exist",
    "setup_vector_indexes",
    "verify_setup",
]
