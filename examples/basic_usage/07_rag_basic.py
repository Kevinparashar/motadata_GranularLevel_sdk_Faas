"""
Basic RAG Example

Demonstrates how to use the RAG component
for document ingestion, retrieval, and generation.

Dependencies: PostgreSQL Database, LiteLLM Gateway
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

load_dotenv(project_root / ".env")

from src.core.rag import RAGSystem
from src.core.postgresql_database import DatabaseConnection, DatabaseConfig
from src.core.litellm_gateway import create_gateway


def main():
    """Demonstrate basic RAG operations."""
    
    # Check prerequisites
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  Warning: No API key found. Set OPENAI_API_KEY in .env")
        return
    
    # Initialize dependencies
    provider = "openai" if os.getenv("OPENAI_API_KEY") else "anthropic"
    default_model = "gpt-3.5-turbo" if provider == "openai" else "claude-3-haiku-20240307"
    gateway = create_gateway(
        providers=[provider],
        default_model=default_model,
        api_keys={provider: api_key}
    )
    
    db_config = DatabaseConfig(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        database=os.getenv("POSTGRES_DB", "motadata_sdk"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "")
    )
    
    db = DatabaseConnection(db_config)
    
    try:
        # Connect to database
        db.connect()
        print("✅ Connected to database")
        
        # Initialize RAG system
        rag = RAGSystem(
            db=db,
            gateway=gateway,
            embedding_model="text-embedding-3-small" if provider == "openai" else "text-embedding-ada-002",
            generation_model=default_model
        )
        
        # 1. Document Ingestion
        print("\n=== Document Ingestion ===")
        
        documents = [
            {
                "title": "Python Basics",
                "content": """
                Python is a high-level programming language known for its simplicity and readability.
                It supports multiple programming paradigms including procedural, object-oriented, and functional programming.
                Python has a large standard library and an active community.
                """,
                "source": "internal_knowledge_base"
            },
            {
                "title": "Machine Learning",
                "content": """
                Machine Learning is a subset of artificial intelligence that enables systems to learn
                from data without being explicitly programmed. Common approaches include supervised learning,
                unsupervised learning, and reinforcement learning.
                """,
                "source": "internal_knowledge_base"
            }
        ]
        
        document_ids = []
        for doc in documents:
            doc_id = rag.ingest_document(
                title=doc["title"],
                content=doc["content"],
                source=doc["source"],
                metadata={"category": "technical"}
            )
            document_ids.append(doc_id)
            print(f"Ingested document: {doc['title']} (ID: {doc_id})")
        
        # 2. Query RAG System
        print("\n=== Querying RAG System ===")
        
        query = "What is Python?"
        print(f"Query: {query}")
        
        result = rag.query(
            query=query,
            top_k=2,
            threshold=0.7,
            max_tokens=200
        )
        
        print(f"\nAnswer: {result['answer']}")
        print(f"\nRetrieved {result['num_documents']} documents:")
        for i, doc in enumerate(result['retrieved_documents'], 1):
            print(f"  {i}. {doc.get('title', 'Unknown')} (similarity: {doc.get('similarity', 0):.3f})")
        
        # 3. Async Query
        print("\n=== Async Query ===")
        
        import asyncio
        
        async def async_query():
            result = await rag.query_async(
                query="What is machine learning?",
                top_k=1,
                threshold=0.7
            )
            return result
        
        async_result = asyncio.run(async_query())
        print(f"Async answer: {async_result['answer'][:100]}...")
        
        # 4. Multiple Queries
        print("\n=== Multiple Queries ===")
        
        queries = [
            "What programming paradigms does Python support?",
            "What are the types of machine learning?"
        ]
        
        for q in queries:
            result = rag.query(q, top_k=1, threshold=0.7, max_tokens=150)
            print(f"\nQ: {q}")
            print(f"A: {result['answer'][:100]}...")
        
        # Cleanup
        print("\n=== Cleanup ===")
        for doc_id in document_ids:
            # In production, you'd have a delete method
            print(f"Would delete document: {doc_id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        print("\n✅ Database connection closed")
    
    print("\n✅ RAG example completed successfully!")


if __name__ == "__main__":
    main()

