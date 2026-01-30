"""
Basic Data Ingestion Example

Demonstrates how to use the Data Ingestion Service
for simple file upload and automatic processing.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

load_dotenv(project_root / ".env")

from src.core.cache_mechanism import create_cache
from src.core.data_ingestion import create_ingestion_service
from src.core.litellm_gateway import create_gateway
from src.core.postgresql_database import DatabaseConfig, DatabaseConnection
from src.core.rag import create_rag_system


def main():
    """Demonstrate basic data ingestion features."""

    print("=== Data Ingestion Service Example ===\n")

    # 1. Setup components
    print("1. Setting up components...")

    # Database
    db_config = DatabaseConfig(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        database=os.getenv("POSTGRES_DB", "motadata_sdk"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
    )
    db = DatabaseConnection(db_config)
    db.connect()

    # Gateway
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY not found. Set it in .env file.")
        return

    gateway = create_gateway(api_keys={"openai": api_key})

    # RAG System
    rag = create_rag_system(db, gateway, enable_multimodal=True)

    # Cache
    cache = create_cache()

    print("✅ Components setup complete\n")

    # 2. Create ingestion service
    print("2. Creating ingestion service...")
    service = create_ingestion_service(
        rag_system=rag,
        cache=cache,
        enable_validation=True,
        enable_cleansing=True,
        enable_auto_ingest=True,
        enable_caching=True,
    )
    print("✅ Ingestion service created\n")

    # 3. Upload and process a file (example with text file)
    print("3. Uploading and processing file...")

    # Create a sample text file for demonstration
    sample_file = project_root / "sample_document.txt"
    sample_file.write_text(
        """
    This is a sample document for demonstration.
    
    It contains multiple paragraphs of text that will be processed
    by the data ingestion service.
    
    The service will:
    - Validate the file
    - Process the content
    - Cleanse the data
    - Cache the result
    - Ingest into RAG system
    """
    )

    try:
        result = service.upload_and_process(
            file_path=str(sample_file),
            title="Sample Document",
            metadata={"source": "example", "type": "demo"},
        )

        print("✅ File processed successfully!")
        print(f"   - Document ID: {result['document_id']}")
        print(f"   - Content length: {result['content_length']} characters")
        print(f"   - Cached: {result['cached']}")
        print(f"   - Ingested: {result['ingested']}")
        print(f"   - Preview: {result['content_preview'][:100]}...\n")

        # 4. Query the ingested content
        print("4. Querying ingested content...")
        query_result = rag.query("What does the sample document contain?", top_k=3)
        if query_result and query_result.get("answer"):
            docs = query_result.get("retrieved_documents", [])
            print(f"✅ Found {len(docs)} relevant documents")
            print(f"   Answer: {query_result['answer'][:100]}...\n")

    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}\n")

    finally:
        # Cleanup
        if sample_file.exists():
            sample_file.unlink()

    # 5. Batch processing example
    print("5. Batch processing example...")
    print("   (Would process multiple files in one call)")
    print("   service.batch_upload_and_process(['file1.pdf', 'file2.mp3', 'file3.jpg'])\n")

    print("✅ Data ingestion example completed!")


if __name__ == "__main__":
    main()
