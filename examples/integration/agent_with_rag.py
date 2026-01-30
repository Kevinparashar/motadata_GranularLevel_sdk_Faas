"""
Agent with RAG Integration Example

Demonstrates how to integrate Agent Framework with RAG system
to create an agent that can answer questions using retrieved context.
"""

import asyncio

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

# Local application/library specific imports
from src.core.agno_agent_framework import Agent
from src.core.litellm_gateway import create_gateway
from src.core.postgresql_database import DatabaseConfig, DatabaseConnection
from src.core.rag import RAGSystem


async def main():
    """Demonstrate agent-RAG integration."""

    # Check prerequisites
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  Warning: No API key found. Set OPENAI_API_KEY in .env")
        return

    provider = "openai" if os.getenv("OPENAI_API_KEY") else "anthropic"
    default_model = "gpt-3.5-turbo" if provider == "openai" else "claude-3-haiku-20240307"

    # Initialize components
    gateway = create_gateway(
        providers=[provider], default_model=default_model, api_keys={provider: api_key}
    )

    db_config = DatabaseConfig(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        database=os.getenv("POSTGRES_DB", "motadata_sdk"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
    )

    db = DatabaseConnection(db_config)
    db.connect()

    # Initialize RAG system
    rag = RAGSystem(
        db=db,
        gateway=gateway,
        embedding_model=(
            "text-embedding-3-small" if provider == "openai" else "text-embedding-ada-002"
        ),
        generation_model=default_model,
    )

    # Ingest sample documents
    print("=== Ingesting Documents ===")
    documents = [
        {
            "title": "SDK Architecture",
            "content": "The SDK follows a modular architecture with swappable components. Each component implements interfaces for easy replacement.",
        },
        {
            "title": "Agent Framework",
            "content": "Agents can execute tasks, manage sessions, store memories, and use tools. They communicate with each other and integrate with RAG systems.",
        },
    ]

    for doc in documents:
        rag.ingest_document(
            title=doc["title"], content=doc["content"], source="knowledge_base"
        )
        print(f"Ingested: {doc['title']}")

    # Create agent with RAG integration
    print("\n=== Creating RAG-Enabled Agent ===")

    agent = Agent(
        agent_id="rag-agent-001",
        name="RAG Assistant",
        description="An agent that uses RAG to answer questions",
        gateway=gateway,
        llm_model=default_model,
    )

    # Add RAG capability
    def rag_query_tool(query: str) -> dict:
        """Tool for querying RAG system."""
        result = rag.query(query=query, top_k=3, threshold=0.7)
        return {
            "answer": result["answer"],
            "sources": [doc.get("title", "Unknown") for doc in result["retrieved_documents"]],
        }

    # Register RAG tool with agent
    from src.core.agno_agent_framework.tools import Tool, ToolParameter, ToolRegistry

    rag_tool = Tool(
        tool_id="rag-query-001",
        name="rag_query",
        description="Query the RAG system for information",
        function=rag_query_tool,
        parameters=[
            ToolParameter(
                name="query",
                type="string",
                description="The question to ask",
                required=True,
            )
        ],
    )

    tool_registry = ToolRegistry()
    tool_registry.register_tool(rag_tool)

    # Execute agent task with RAG
    print("\n=== Agent Task with RAG ===")

    agent.add_task(
        task_type="rag_query",
        parameters={"query": "What is the SDK architecture?", "use_rag": True},
        priority=1,
    )

    # Custom task execution that uses RAG
    async def execute_rag_task(agent, task):
        """Execute task using RAG."""
        query = task.parameters.get("query", "")

        # Use RAG to get context
        rag_result = rag.query(query=query, top_k=2, threshold=0.7)

        # Use LLM to generate answer with context
        context = "\n".join(
            [
                f"- {doc.get('title', 'Unknown')}: {doc.get('content', '')[:200]}"
                for doc in rag_result["retrieved_documents"]
            ]
        )

        prompt = f"""
Based on the following context, answer the question.

Context:
{context}

Question: {query}

Answer:
        """.strip()

        response = await gateway.generate_async(
            prompt=prompt, model=agent.llm_model or default_model, max_tokens=300
        )

        return {
            "status": "completed",
            "answer": response.text,
            "sources": [doc.get("title") for doc in rag_result["retrieved_documents"]],
        }

    # Execute task
    task = agent.task_queue[0]
    result = await execute_rag_task(agent, task)

    print(f"Question: {task.parameters['query']}")
    print(f"Answer: {result['answer']}")
    print(f"Sources: {', '.join(result['sources'])}")

    # Cleanup
    db.close()
    print("\n✅ Agent-RAG integration example completed!")


if __name__ == "__main__":
    asyncio.run(main())
