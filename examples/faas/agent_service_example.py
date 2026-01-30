"""
Example: Using Agent Service

Demonstrates how to interact with Agent Service via HTTP API.
"""

import asyncio

import httpx


async def main():
    """Example usage of Agent Service."""
    base_url = "http://localhost:8083"  # Agent Service URL
    tenant_id = "tenant_123"
    headers = {
        "X-Tenant-ID": tenant_id,
        "X-User-ID": "user_456",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        # 1. Create an agent
        print("Creating agent...")
        create_response = await client.post(
            f"{base_url}/api/v1/agents",
            json={
                "name": "Customer Support Agent",
                "description": "Helps customers with support tickets",
                "llm_model": "gpt-4",
                "system_prompt": "You are a helpful customer support agent.",
                "capabilities": ["ticket_handling", "problem_solving"],
            },
            headers=headers,
        )
        print(f"Create Agent Response: {create_response.status_code}")
        if create_response.status_code == 201:
            agent_data = create_response.json()
            agent_id = agent_data["data"]["agent_id"]
            print(f"Agent created: {agent_id}")

            # 2. Execute a task
            print("\nExecuting task...")
            task_response = await client.post(
                f"{base_url}/api/v1/agents/{agent_id}/execute",
                json={
                    "task_type": "llm_query",
                    "parameters": {
                        "prompt": "What is customer support?",
                    },
                    "priority": 1,
                },
                headers=headers,
            )
            print(f"Execute Task Response: {task_response.status_code}")
            if task_response.status_code == 200:
                task_data = task_response.json()
                print(f"Task Result: {task_data['data']}")

            # 3. Chat with agent
            print("\nChatting with agent...")
            chat_response = await client.post(
                f"{base_url}/api/v1/agents/{agent_id}/chat",
                json={
                    "message": "Hello, I need help with my account",
                },
                headers=headers,
            )
            print(f"Chat Response: {chat_response.status_code}")
            if chat_response.status_code == 200:
                chat_data = chat_response.json()
                print(f"Agent Response: {chat_data['data']['message']}")

            # 4. List agents
            print("\nListing agents...")
            list_response = await client.get(
                f"{base_url}/api/v1/agents",
                headers=headers,
            )
            print(f"List Agents Response: {list_response.status_code}")
            if list_response.status_code == 200:
                list_data = list_response.json()
                print(f"Total agents: {list_data['data']['total']}")


if __name__ == "__main__":
    asyncio.run(main())
