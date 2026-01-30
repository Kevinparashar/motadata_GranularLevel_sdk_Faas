"""
Example: Using RAG Service

Demonstrates how to interact with RAG Service for document ingestion and querying.
"""

import asyncio

import httpx


async def main():
    """Example usage of RAG Service."""
    base_url = "http://localhost:8082"  # RAG Service URL
    tenant_id = "tenant_123"
    headers = {
        "X-Tenant-ID": tenant_id,
        "X-User-ID": "user_456",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        # 1. Ingest a document
        print("Ingesting document...")
        ingest_response = await client.post(
            f"{base_url}/api/v1/rag/documents",
            json={
                "title": "AI Documentation",
                "content": """
                Artificial Intelligence (AI) is the simulation of human intelligence
                in machines that are programmed to think and learn like humans.
                AI can be categorized into narrow AI and general AI.
                """,
                "source": "internal_docs",
                "metadata": {"category": "technology", "author": "AI Team"},
            },
            headers=headers,
        )
        print(f"Ingest Document Response: {ingest_response.status_code}")
        if ingest_response.status_code == 201:
            ingest_data = ingest_response.json()
            document_id = ingest_data["data"]["document_id"]
            print(f"Document ingested: {document_id}")

            # 2. Query the RAG system
            print("\nQuerying RAG system...")
            query_response = await client.post(
                f"{base_url}/api/v1/rag/query",
                json={
                    "query": "What is artificial intelligence?",
                    "top_k": 3,
                    "enable_rewrite": True,
                },
                headers=headers,
            )
            print(f"Query Response: {query_response.status_code}")
            if query_response.status_code == 200:
                query_data = query_response.json()
                print(f"Answer: {query_data['data']['answer']}")
                print(f"Sources: {len(query_data['data']['documents'])} documents")

            # 3. Perform vector search
            print("\nPerforming vector search...")
            search_response = await client.post(
                f"{base_url}/api/v1/rag/search",
                json={
                    "query_text": "machine learning",
                    "top_k": 5,
                    "threshold": 0.7,
                },
                headers=headers,
            )
            print(f"Search Response: {search_response.status_code}")
            if search_response.status_code == 200:
                search_data = search_response.json()
                print(f"Found {search_data['data']['count']} documents")


if __name__ == "__main__":
    asyncio.run(main())
