"""
Example: Complete Workflow - Agent Using RAG

Demonstrates a complete workflow where an Agent uses RAG to answer questions.
"""

import asyncio
from pathlib import Path

import httpx

# Constants
EXAMPLE_DOC_FILENAME = "example_document.txt"
EXAMPLE_DOC_CONTENT = """
Motadata AI SDK provides comprehensive AI capabilities including:
- Agent Framework for autonomous AI agents
- RAG System for document-based Q&A
- LiteLLM Gateway for unified LLM access
- ML Framework for machine learning operations
"""


def _prepare_example_document() -> Path:
    """Prepare example document for upload (synchronous helper)."""
    doc_path = Path(EXAMPLE_DOC_FILENAME)
    doc_path.write_text(EXAMPLE_DOC_CONTENT)
    return doc_path


async def complete_workflow():
    """
    Complete workflow example:
    1. Upload document to Data Ingestion Service
    2. Document is automatically ingested into RAG
    3. Create an agent
    4. Agent uses RAG to answer questions
    """
    tenant_id = "tenant_123"
    headers = {
        "X-Tenant-ID": tenant_id,
        "X-User-ID": "user_456",
        "Content-Type": "application/json",
    }

    # Prepare document before async operations
    doc_path = _prepare_example_document()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Upload document via Data Ingestion Service
        print("Step 1: Uploading document...")
        
        # Upload the document (read file content before async context)
        file_content = doc_path.read_bytes()
        upload_response = await client.post(
            "http://localhost:8086/api/v1/ingestion/upload",
            files={"file": (EXAMPLE_DOC_FILENAME, file_content)},
            data={"title": "SDK Documentation", "auto_ingest": "true"},
            headers={"X-Tenant-ID": tenant_id},
        )
        print(f"Upload Response: {upload_response.status_code}")

        # Step 2: Wait for ingestion to complete (in production, use async/events)
        await asyncio.sleep(2)

        # Step 3: Create an agent
        print("\nStep 2: Creating agent...")
        agent_response = await client.post(
            "http://localhost:8083/api/v1/agents",
            json={
                "name": "Document Q&A Agent",
                "description": "Answers questions about SDK documentation",
                "llm_model": "gpt-4",
                "system_prompt": "You are a helpful assistant that answers questions using provided documents.",
            },
            headers=headers,
        )
        if agent_response.status_code == 201:
            agent_id = agent_response.json()["data"]["agent_id"]
            print(f"Agent created: {agent_id}")

            # Step 4: Agent queries RAG system (via internal service call)
            # In production, this would be handled internally
            print("\nStep 3: Agent querying RAG system...")
            rag_query_response = await client.post(
                "http://localhost:8082/api/v1/rag/query",
                json={
                    "query": "What capabilities does the Motadata AI SDK provide?",
                    "top_k": 3,
                },
                headers=headers,
            )
            if rag_query_response.status_code == 200:
                rag_data = rag_query_response.json()
                answer = rag_data["data"]["answer"]
                print(f"RAG Answer: {answer}")

                # Step 5: Agent uses RAG answer to respond
                print("\nStep 4: Agent responding to user...")
                agent_chat_response = await client.post(
                    f"http://localhost:8083/api/v1/agents/{agent_id}/chat",
                    json={
                        "message": "What capabilities does the Motadata AI SDK provide?",
                    },
                    headers=headers,
                )
                if agent_chat_response.status_code == 200:
                    chat_data = agent_chat_response.json()
                    print(f"Agent Response: {chat_data['data']['message']}")


if __name__ == "__main__":
    asyncio.run(complete_workflow())
