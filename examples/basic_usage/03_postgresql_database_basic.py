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

from src.core.postgresql_database import PostgreSQLDatabase
from src.core.postgresql_database.vector_operations import VectorOperations


def main():
    """Demonstrate basic database operations."""
    
    # Initialize database connection
    db_config = {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", 5432)),
        "database": os.getenv("POSTGRES_DB", "motadata_sdk"),
        "user": os.getenv("POSTGRES_USER", "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD", "")
    }
    
    db = PostgreSQLDatabase(**db_config)
    
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
        
        # Create vector table if not exists
        vector_ops.create_vector_table("test_vectors", dimension=1536)
        print("Created vector table")
        
        # Store an embedding
        test_embedding = [0.1] * 1536  # Mock embedding
        embedding_id = vector_ops.store_embedding(
            document_id=1,
            embedding=test_embedding,
            model="text-embedding-3-small"
        )
        print(f"Stored embedding with ID: {embedding_id}")
        
        # Similarity search
        query_embedding = [0.1] * 1536
        results = vector_ops.similarity_search(
            query_embedding=query_embedding,
            limit=5,
            threshold=0.7
        )
        print(f"Found {len(results)} similar vectors")
        
        # Cleanup
        db.execute_query("DROP TABLE IF EXISTS test_table;")
        db.execute_query("DROP TABLE IF EXISTS test_vectors;")
        print("\nCleaned up test tables")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        db.disconnect()
        print("✅ Database connection closed")
    
    print("\n✅ PostgreSQL database example completed successfully!")


if __name__ == "__main__":
    main()

