"""
Hello World Example - Get Started with the SDK in 5 Minutes

This is the simplest possible example to verify your SDK installation
and make your first AI call.

Prerequisites:
- Python 3.8+
- OpenAI API key (or other LLM provider key)
- Dependencies installed (pip install -r requirements.txt)

Expected Output:
- A greeting message from the AI
- Confirmation that the SDK is working correctly
- Token usage information
"""

import os
import asyncio

# Load environment variables from .env file (optional)
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except ImportError:
    # python-dotenv not installed, will use environment variables directly
    pass

# Import the gateway factory function
from src.core.litellm_gateway import create_gateway


async def main():
    """
    Simple Hello World example.

    This demonstrates:
    1. Creating a gateway connection
    2. Making a simple AI call
    3. Getting a response
    """

    print("🚀 Motadata AI SDK - Hello World Example\n")

    # Step 1: Get your API key from environment
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if not api_key:
        print("❌ Error: No API key found in environment variables")
        print("\nPlease set your API key:")
        print("  export OPENAI_API_KEY='your-api-key-here'")
        print("\nOr create a .env file with:")
        print("  OPENAI_API_KEY=your-api-key-here")
        return

    print("✅ API key found")
    print("📡 Creating gateway connection...\n")

    # Step 2: Create a gateway (this is your connection to AI services)
    # Using GPT-3.5-turbo for cost efficiency in Hello World example
    provider = "openai" if os.getenv("OPENAI_API_KEY") else ("anthropic" if os.getenv("ANTHROPIC_API_KEY") else "google")

    # Determine the default model based on provider
    default_model = "gpt-3.5-turbo" if provider == "openai" else ("claude-3-haiku-20240307" if provider == "anthropic" else "gemini-pro")

    # Create gateway with provider and API key
    # Note: create_gateway expects providers (list) and api_keys (dict)
    gateway = create_gateway(
        providers=[provider],
        default_model=default_model,
        api_keys={provider: api_key}
    )

    print("✅ Gateway created successfully")
    print("🤖 Sending request to AI...\n")

    # Step 3: Make your first AI call
    try:
        response = await gateway.generate_async(
            prompt="Say hello and introduce yourself in one sentence.",
            model=default_model
        )

        # Step 4: Display the response
        print("=" * 60)
        print("AI Response:")
        print("=" * 60)
        print(response.text)
        print("=" * 60)

        print(f"\n✅ Success! SDK is working correctly.")
        print(f"📊 Model used: {response.model}")

        if response.usage:
            print(f"💰 Tokens used: {response.usage.get('total_tokens', 'N/A')}")

        print("\n🎉 Congratulations! You've made your first AI call with the SDK.")
        print("\nNext steps:")
        print("  - Try examples/basic_usage/ for more examples")
        print("  - Read component READMEs to learn about Agents, RAG, etc.")
        print("  - Check docs/ for detailed guides")

    except (ConnectionError, TimeoutError) as e:
        print(f"❌ Network error: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check your internet connection")
        print("2. Verify the API endpoint is accessible")
    except ValueError as e:
        print(f"❌ Validation error: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check your API key format is correct")
        print("2. Verify all required parameters are provided")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check your API key is correct")
        print("2. Ensure you have internet connection")
        print("3. Verify your API key has credits/quota")
        print("4. Check the error message above for details")


if __name__ == "__main__":
    # Run the async function
    asyncio.run(main())

