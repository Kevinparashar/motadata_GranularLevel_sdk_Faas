"""
PostgreSQL Database Integration

PostgreSQL database with pgvector extension for vector operations.
"""


from .connection import DatabaseConfig, DatabaseConnection
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
]
