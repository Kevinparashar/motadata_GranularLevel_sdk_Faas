"""
Example: Create Tool from Natural Language Prompt

Demonstrates how to create a tool using a natural language description.
"""

import asyncio
import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.core.litellm_gateway import create_gateway
from src.core.prompt_based_generator import create_tool_from_prompt


async def main():
    """Main example function."""
    print("🚀 Prompt-Based Tool Creation Example\n")

    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: Please set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env file")
        return

    # Create gateway
    print("📡 Creating LiteLLM Gateway...")
    gateway = create_gateway(api_key=api_key, provider="openai", default_model="gpt-4")
    print("✅ Gateway created\n")

    # Create tool from natural language prompt
    print("🔧 Creating tool from prompt...")
    print("Prompt: Create a tool that calculates ticket priority\n")

    try:
        tool = await create_tool_from_prompt(
            prompt="""
            Create a tool that calculates the priority of a support ticket.
            
            Inputs:
            - urgency: integer from 1-5 (1=low, 5=critical)
            - impact: integer from 1-5 (1=low, 5=high)
            - customer_tier: string (bronze, silver, gold, platinum)
            
            Output: Priority score from 1-5 where:
            - 1 = Low priority
            - 2 = Medium priority
            - 3 = High priority
            - 4 = Urgent
            - 5 = Critical
            
            Formula: (urgency * 0.4) + (impact * 0.4) + (tier_multiplier * 0.2)
            Tier multipliers: bronze=1.0, silver=1.2, gold=1.5, platinum=2.0
            """,
            gateway=gateway,
            tenant_id="example_tenant",
            user_id="example_user",
        )

        print("✅ Tool created successfully!")
        print(f"   Tool ID: {tool.tool_id}")
        print(f"   Name: {tool.name}")
        print(f"   Description: {tool.description}")
        print(f"   Parameters: {[p.name for p in tool.parameters]}\n")

        # Use the tool
        print("🧪 Testing tool with sample inputs...")
        result1 = tool.execute(urgency=4, impact=5, customer_tier="platinum")
        print(f"   Test 1 (urgent, high impact, platinum): Priority = {result1}")

        result2 = tool.execute(urgency=2, impact=2, customer_tier="bronze")
        print(f"   Test 2 (low urgency, low impact, bronze): Priority = {result2}\n")

        print("✅ Tool working correctly!")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
