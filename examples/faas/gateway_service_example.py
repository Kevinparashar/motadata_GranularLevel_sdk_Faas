"""
Example: Using Gateway Service

Demonstrates how to interact with Gateway Service for LLM access.
"""

import asyncio

import httpx


async def main():
    """Example usage of Gateway Service."""
    base_url = "http://localhost:8080"  # Gateway Service URL
    tenant_id = "tenant_123"
    headers = {
        "X-Tenant-ID": tenant_id,
        "X-User-ID": "user_456",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        # 1. Generate text
        print("Generating text...")
        generate_response = await client.post(
            f"{base_url}/api/v1/gateway/generate",
            json={
                "prompt": "Explain artificial intelligence in one sentence.",
                "model": "gpt-4",
                "max_tokens": 100,
                "temperature": 0.7,
            },
            headers=headers,
        )
        print(f"Generate Response: {generate_response.status_code}")
        if generate_response.status_code == 200:
            generate_data = generate_response.json()
            print(f"Generated Text: {generate_data['data']['text']}")
            print(f"Model Used: {generate_data['data']['model']}")
            print(f"Tokens Used: {generate_data['data']['usage']}")

        # 2. Generate embeddings
        print("\nGenerating embeddings...")
        embed_response = await client.post(
            f"{base_url}/api/v1/gateway/embeddings",
            json={
                "texts": [
                    "Artificial intelligence is the future",
                    "Machine learning enables AI",
                ],
                "model": "text-embedding-3-small",
            },
            headers=headers,
        )
        print(f"Embed Response: {embed_response.status_code}")
        if embed_response.status_code == 200:
            embed_data = embed_response.json()
            print(f"Generated {len(embed_data['data']['embeddings'])} embeddings")
            print(f"Embedding dimension: {len(embed_data['data']['embeddings'][0])}")

        # 3. Get available providers
        print("\nGetting available providers...")
        providers_response = await client.get(
            f"{base_url}/api/v1/gateway/providers",
            headers=headers,
        )
        print(f"Providers Response: {providers_response.status_code}")
        if providers_response.status_code == 200:
            providers_data = providers_response.json()
            print(f"Available Providers: {providers_data['data']['providers']}")


if __name__ == "__main__":
    asyncio.run(main())
