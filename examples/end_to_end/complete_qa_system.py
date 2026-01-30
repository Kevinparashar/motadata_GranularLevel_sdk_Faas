"""
Complete Q&A System Example

End-to-end example demonstrating a complete question-answering system
using RAG, Agents, and API Backend.
"""

# Standard library imports
import os
import sys
from pathlib import Path

# Third-party imports
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

if load_dotenv:
    load_dotenv(project_root / ".env")

from src.core.agno_agent_framework import Agent, AgentManager
from src.core.cache_mechanism import CacheConfig, CacheMechanism
from src.core.litellm_gateway import create_gateway
from src.core.postgresql_database import DatabaseConfig, DatabaseConnection

# Local application/library specific imports
from src.core.rag import RAGSystem


def main():
    """Run complete Q&A system."""

    print("=" * 60)
    print("Complete Q&A System - End-to-End Example")
    print("=" * 60)

    # Check prerequisites
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: No API key found. Set OPENAI_API_KEY in .env")
        return

    provider = "openai" if os.getenv("OPENAI_API_KEY") else "anthropic"
    default_model = "gpt-3.5-turbo" if provider == "openai" else "claude-3-haiku-20240307"

    # 1. Initialize Cache
    print("\n[1/6] Initializing Cache...")
    cache_config = CacheConfig(backend="memory", default_ttl=3600, max_size=2048)
    cache = CacheMechanism(cache_config)
    print("✅ Cache initialized")

    # 2. Initialize Database
    print("[2/6] Initializing Database...")
    db_config = DatabaseConfig(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        database=os.getenv("POSTGRES_DB", "motadata_sdk"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
    )

    db = DatabaseConnection(db_config)
    db.connect()
    print("✅ Database connected")

    # 3. Initialize Gateway
    print("[3/6] Initializing LiteLLM Gateway...")
    gateway = create_gateway(
        providers=[provider], default_model=default_model, api_keys={provider: api_key}
    )
    print("✅ Gateway initialized")

    # 4. Initialize RAG System
    print("[4/6] Initializing RAG System...")
    rag = RAGSystem(
        db=db,
        gateway=gateway,
        embedding_model=(
            "text-embedding-3-small" if provider == "openai" else "text-embedding-ada-002"
        ),
        generation_model=default_model,
    )
    print("✅ RAG system initialized")

    # 5. Ingest Knowledge Base
    print("[5/6] Ingesting Knowledge Base...")
    knowledge_base = [
        {
            "title": "SDK Overview",
            "content": """
            The Motadata Python AI SDK is a comprehensive, modular SDK for building AI-powered applications.
            It provides unified interfaces for LLM operations, agent frameworks, RAG systems, and database operations.
            The SDK is designed with modularity and swappability in mind, allowing easy replacement of components.
            """,
        },
        {
            "title": "Agent Framework",
            "content": """
            The Agent Framework enables creation of autonomous AI agents with session management, memory systems,
            tools, and plugins. Agents can execute tasks, communicate with each other, and coordinate complex workflows.
            The framework supports multiple agent frameworks including Agno and LangChain.
            """,
        },
        {
            "title": "RAG System",
            "content": """
            The RAG (Retrieval-Augmented Generation) system provides document ingestion, vector-based retrieval,
            and context-aware response generation. It uses PostgreSQL with pgvector for efficient similarity search
            and supports multiple embedding models.
            """,
        },
        {
            "title": "Observability",
            "content": """
            The Observability component provides distributed tracing, structured logging, and metrics collection
            using OpenTelemetry. It integrates with all SDK components for comprehensive monitoring.
            """,
        },
    ]

    document_ids = []
    for doc in knowledge_base:
        doc_id = rag.ingest_document(
            title=doc["title"],
            content=doc["content"],
            source="knowledge_base",
            metadata={"category": "sdk_documentation"},
        )
        document_ids.append(doc_id)
        print(f"  ✅ Ingested: {doc['title']}")

    print(f"✅ Ingested {len(document_ids)} documents")

    # 6. Create Q&A Agent
    print("[6/6] Creating Q&A Agent...")
    agent = Agent(
        agent_id="qa-agent-001",
        name="Q&A Assistant",
        description="An intelligent assistant that answers questions using RAG",
        gateway=gateway,
        llm_model=default_model,
    )

    agent_manager = AgentManager()
    agent_manager.register_agent(agent)
    print("✅ Agent created and registered")

    # 8. Interactive Q&A Loop
    print("\n" + "=" * 60)
    print("Interactive Q&A System")
    print("=" * 60)
    print("Type 'quit' to exit\n")

    questions = [
        "What is the SDK?",
        "How does the Agent Framework work?",
        "What is RAG?",
        "How does observability work?",
    ]

    for question in questions:
        print(f"\n❓ Question: {question}")

        # Check cache first
        cache_key = f"qa:{hash(question)}"
        cached_answer = cache.get(cache_key)

        if cached_answer:
            print("💾 Using cached answer")
            print(f"✅ Answer: {cached_answer['answer']}")
            continue

        # Query RAG system
        result = rag.query(query=question, top_k=2, threshold=0.7, max_tokens=300)

        # Cache the result
        cache.set(cache_key, result, ttl=3600)

        # Display answer
        print(f"✅ Answer: {result['answer']}")
        print(
            f"📚 Sources: {', '.join([doc.get('title', 'Unknown') for doc in result['retrieved_documents']])}"
        )

    # 9. System Statistics
    print("\n" + "=" * 60)
    print("System Statistics")
    print("=" * 60)

    # Get agent status
    agent_status = agent.get_status()
    print(f"Agent status: {agent_status['status']}")
    print(f"Agent capabilities: {len(agent_status.get('capabilities', []))}")

    # Cleanup
    print("\n[Cleanup] Closing connections...")
    db.close()
    print("✅ Q&A System shutdown complete")

    print("\n✅ Complete Q&A system example finished successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
