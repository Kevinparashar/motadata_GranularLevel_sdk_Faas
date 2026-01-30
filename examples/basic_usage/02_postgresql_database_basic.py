"""
Basic PostgreSQL Database Example

Demonstrates how to use the PostgreSQL Database component
for database operations and vector storage.

Dependencies: Evaluation & Observability
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

load_dotenv(project_root / ".env")

from src.core.postgresql_database import DatabaseConfig, DatabaseConnection
from src.core.postgresql_database.vector_operations import VectorOperations


def main():
    """Demonstrate basic database operations."""

    # Initialize database connection
    db_config = DatabaseConfig(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        database=os.getenv("POSTGRES_DB", "motadata_sdk"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
    )

    db = DatabaseConnection(db_config)

    try:
        # Connect to database
        db.connect()
        print("✅ Connected to PostgreSQL database")

        # 1. Basic Query Operations
        print("\n=== Basic Query Operations ===")

        # Create a test table
        create_table_query = """
        CREATE TABLE IF NOT EXISTS test_table (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            value INTEGER
        );
        """
        db.execute_query(create_table_query)
        print("Created test table")

        # Insert data
        insert_query = "INSERT INTO test_table (name, value) VALUES (%s, %s) RETURNING id;"
        result = db.execute_query(insert_query, ("test_item", 42), fetch_one=True)
        print(f"Inserted record with ID: {result['id']}")

        # Query data
        select_query = "SELECT * FROM test_table WHERE name = %s;"
        results = db.execute_query(select_query, ("test_item",), fetch_all=True)
        print(f"Retrieved {len(results)} records")

        # 2. Vector Operations
        print("\n=== Vector Operations ===")

        vector_ops = VectorOperations(db)

        # Note: Assumes embeddings table already exists (created by RAG system)
        # If you need to create tables, use the database schema initialization
        print("Using existing embeddings table")

        # Insert an embedding
        test_embedding = [0.1] * 1536  # Mock embedding
        embedding_id = vector_ops.insert_embedding(
            document_id=1, embedding=test_embedding, model="text-embedding-3-small"
        )
        print(f"Inserted embedding with ID: {embedding_id}")

        # Similarity search
        query_embedding = [0.1] * 1536
        results = vector_ops.similarity_search(
            query_embedding=query_embedding, limit=5, threshold=0.7
        )
        print(f"Found {len(results)} similar vectors")

        # Cleanup
        db.execute_query("DROP TABLE IF EXISTS test_table;")
        print("\nCleaned up test table")
        print("Note: Embeddings table is managed by RAG system")

    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()
        print("✅ Database connection closed")

    print("\n✅ PostgreSQL database example completed successfully!")


if __name__ == "__main__":
    main()
