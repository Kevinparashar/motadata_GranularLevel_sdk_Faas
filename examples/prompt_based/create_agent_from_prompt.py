"""
Example: Create Agent from Natural Language Prompt

Demonstrates how to create an AI agent using a natural language description.
"""

import asyncio
import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.core.agno_agent_framework import AgentTask
from src.core.litellm_gateway import create_gateway
from src.core.prompt_based_generator import create_agent_from_prompt


async def main():
    """Main example function."""
    print("🚀 Prompt-Based Agent Creation Example\n")

    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: Please set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env file")
        return

    # Create gateway
    print("📡 Creating LiteLLM Gateway...")
    gateway = create_gateway(api_key=api_key, provider="openai", default_model="gpt-4")
    print("✅ Gateway created\n")

    # Create agent from natural language prompt
    print("🤖 Creating agent from prompt...")
    print(
        "Prompt: Create a customer support agent that categorizes tickets and suggests solutions\n"
    )

    try:
        agent = await create_agent_from_prompt(
            prompt="""
            Create a customer support agent with the following capabilities:
            1. Categorize support tickets by type (technical, billing, general)
            2. Suggest solutions based on ticket history and knowledge base
            3. Escalate to human agents when needed
            4. Track ticket resolution time
            5. Provide friendly and helpful responses
            """,
            gateway=gateway,
            tenant_id="example_tenant",
            user_id="example_user",
        )

        print("✅ Agent created successfully!")
        print(f"   Agent ID: {agent.agent_id}")
        print(f"   Name: {agent.name}")
        print(f"   Description: {agent.description}")
        print(f"   Capabilities: {[cap.name for cap in agent.capabilities]}\n")

        # Use the agent
        print("💬 Testing agent with a sample task...")
        task = AgentTask(
            task_id="test_task_1",
            task_type="categorize_ticket",
            parameters={
                "ticket_text": "I can't log into my account. I've tried resetting my password but it's not working.",
                "customer_tier": "gold",
            },
        )

        response = await agent.execute_task(task, tenant_id="example_tenant")
        print("✅ Agent response received")
        print(f"   Response: {response}\n")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
