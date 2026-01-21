"""
PostgreSQL Database Integration

PostgreSQL database with pgvector extension for vector operations.
"""

from .connection import DatabaseConnection, DatabaseConfig
from .vector_index_manager import (
    VectorIndexManager,
    create_vector_index_manager,
    IndexType,
    IndexDistance
)

__all__ = [
    "DatabaseConnection",
    "DatabaseConfig",
    "VectorIndexManager",
    "create_vector_index_manager",
    "IndexType",
    "IndexDistance",
]
