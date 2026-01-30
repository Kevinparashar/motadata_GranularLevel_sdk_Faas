"""
Document Q&A Use Case with NATS, OTEL, and CODEC Integration

Complete example showing how NATS, OTEL, and CODEC integrate
with RAG System, LiteLLM Gateway, and Agent Framework.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# TODO: SDK-INTEG-001 - Import when integrations are implemented  # noqa: FIX002, S1135
# from src.integrations.nats_integration import NATSClient
# from src.integrations.otel_integration import OTELTracer, OTELMetrics
# from src.integrations.codec_integration import CodecSerializer

from src.core.litellm_gateway import create_gateway
from src.core.postgresql_database.connection import DatabaseConfig, DatabaseConnection
from src.core.rag import create_rag_system


async def main():
    """Run Document Q&A use case with integrations."""

    print("=" * 60)
    print("Document Q&A Use Case with NATS, OTEL, CODEC Integration")
    print("=" * 60)
    print()

    # TODO: SDK-INTEG-002 - Initialize integrations when available  # noqa: FIX002, S1135
    # nats_client = NATSClient(url=os.getenv("NATS_URL", "nats://localhost:4222"))
    # otel_tracer = OTELTracer(service_name="document_qa")
    # otel_metrics = OTELMetrics()
    # codec = CodecSerializer()

    # Initialize AI components
    db_config = DatabaseConfig(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "motadata_sdk"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    )

    db = DatabaseConnection(config=db_config)

    gateway = create_gateway(
        providers=["openai"],
        default_model="gpt-4",
        api_keys={"openai": os.getenv("OPENAI_API_KEY", "")},
    )

    rag = create_rag_system(
        db=db, gateway=gateway, embedding_model="text-embedding-3-small", generation_model="gpt-4"
    )

    print("✅ Components initialized")
    print()

    # Example query
    query = "What is the refund policy?"
    tenant_id = "tenant_123"

    print(f"Query: {query}")
    print()

    # TODO: SDK-INTEG-003 - Implement full integration flow when NATS, OTEL, CODEC are available  # noqa: FIX002, S1135
    # For now, use direct RAG query
    print("Processing query (direct RAG call - integrations will be added)...")
    response = await rag.query_async(query, tenant_id=tenant_id)

    print()
    print("Response:")
    print(response.get("answer", "No answer available"))
    print()
    sources = response.get("retrieved_documents", [])
    print(f"Sources: {len(sources)} documents")

    # Cleanup
    db.close()
    print()
    print("✅ Use case completed")


if __name__ == "__main__":
    asyncio.run(main())
