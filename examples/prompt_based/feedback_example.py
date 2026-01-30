"""
Example: Feedback Collection for Agents and Tools

Demonstrates how to collect and view feedback for generated agents and tools.
"""

import asyncio
import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.core.litellm_gateway import create_gateway
from src.core.prompt_based_generator import (
    create_agent_from_prompt,
    create_tool_from_prompt,
    get_agent_feedback_stats,
    get_tool_feedback_stats,
    rate_agent,
    rate_tool,
)


async def main():
    """Main example function."""
    print("🚀 Feedback Collection Example\n")

    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: Please set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env file")
        return

    # Create gateway
    print("📡 Creating LiteLLM Gateway...")
    gateway = create_gateway(api_key=api_key, provider="openai", default_model="gpt-4")
    print("✅ Gateway created\n")

    tenant_id = "example_tenant"
    user_id = "example_user"

    try:
        # Create an agent
        print("🤖 Creating agent...")
        agent = await create_agent_from_prompt(
            prompt="Create a helpful assistant that answers questions",
            gateway=gateway,
            tenant_id=tenant_id,
            user_id=user_id,
        )
        print(f"✅ Agent created: {agent.agent_id}\n")

        # Create a tool
        print("🔧 Creating tool...")
        tool = await create_tool_from_prompt(
            prompt="Create a tool that adds two numbers",
            gateway=gateway,
            tenant_id=tenant_id,
            user_id=user_id,
        )
        print(f"✅ Tool created: {tool.tool_id}\n")

        # Collect feedback for agent
        print("⭐ Collecting feedback for agent...")
        rate_agent(
            agent_id=agent.agent_id,
            rating=5,
            user_id=user_id,
            tenant_id=tenant_id,
            feedback_text="Very helpful and responsive!",
        )
        rate_agent(
            agent_id=agent.agent_id,
            rating=4,
            user_id="user_2",
            tenant_id=tenant_id,
            feedback_text="Good, but could be faster",
        )
        print("✅ Feedback collected\n")

        # Collect feedback for tool
        print("⭐ Collecting feedback for tool...")
        rate_tool(
            tool_id=tool.tool_id,
            rating=5,
            user_id=user_id,
            tenant_id=tenant_id,
            feedback_text="Works perfectly!",
        )
        rate_tool(
            tool_id=tool.tool_id,
            rating=4,
            user_id="user_2",
            tenant_id=tenant_id,
            feedback_text="Accurate results",
        )
        print("✅ Feedback collected\n")

        # Get feedback statistics
        print("📊 Agent Feedback Statistics:")
        agent_stats = get_agent_feedback_stats(agent.agent_id, tenant_id=tenant_id)
        print(f"   Total feedback: {agent_stats['total_feedback']}")
        print(f"   Average rating: {agent_stats['average_rating']}")
        print(f"   Average effectiveness: {agent_stats['average_effectiveness']}")
        print(f"   Ratings distribution: {agent_stats['ratings_distribution']}\n")

        print("📊 Tool Feedback Statistics:")
        tool_stats = get_tool_feedback_stats(tool.tool_id, tenant_id=tenant_id)
        print(f"   Total feedback: {tool_stats['total_feedback']}")
        print(f"   Average rating: {tool_stats['average_rating']}")
        print(f"   Average performance: {tool_stats['average_performance']}")
        print(f"   Ratings distribution: {tool_stats['ratings_distribution']}\n")

        print("✅ Feedback example completed!")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
