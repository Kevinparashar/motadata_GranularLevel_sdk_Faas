"""
Basic LiteLLM Gateway Example

Demonstrates how to use the LiteLLM Gateway component
for unified LLM operations across multiple providers.

Dependencies: Evaluation & Observability, Cache (optional)
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

load_dotenv(project_root / ".env")

from src.core.litellm_gateway import create_gateway


async def main():
    """Demonstrate basic gateway features."""
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  Warning: No API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env")
        print("Example will show structure but won't make actual API calls.")
        return
    
    # Initialize gateway
    provider = "openai" if os.getenv("OPENAI_API_KEY") else "anthropic"
    default_model = "gpt-3.5-turbo" if provider == "openai" else "claude-3-haiku-20240307"
    gateway = create_gateway(
        providers=[provider],
        default_model=default_model,
        api_keys={provider: api_key}
    )
    
    try:
        # 1. Text Generation
        print("=== Text Generation ===")
        
        response = await gateway.generate_async(
            prompt="Explain quantum computing in one sentence.",
            model=default_model,
            max_tokens=100
        )
        
        print(f"Generated text: {response.text}")
        print(f"Model used: {response.model}")
        print(f"Tokens used: {response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}")
        
        # 2. Streaming Generation
        print("\n=== Streaming Generation ===")
        
        print("Streaming response:")
        async for chunk in gateway.stream_async(
            prompt="Count from 1 to 5:",
            model=default_model,
            max_tokens=50
        ):
            if hasattr(chunk, 'choices') and chunk.choices:
                content = chunk.choices[0].delta.content
                if content:
                    print(content, end="", flush=True)
        print()  # New line after streaming
        
        # 3. Embeddings
        print("\n=== Embeddings ===")
        
        embedding_response = await gateway.embed_async(
            texts=["Hello, world!", "This is a test."],
            model="text-embedding-3-small" if provider == "openai" else "text-embedding-ada-002"
        )
        
        if embedding_response.embeddings:
            print(f"Generated {len(embedding_response.embeddings)} embeddings")
            print(f"Embedding dimension: {len(embedding_response.embeddings[0])}")
        
        # 4. Function Calling (if supported)
        print("\n=== Function Calling ===")
        
        functions = [
            {
                "name": "get_weather",
                "description": "Get the current weather",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "The city and state"}
                    },
                    "required": ["location"]
                }
            }
        ]
        
        try:
            response = await gateway.generate_async(
                prompt="What's the weather in San Francisco?",
                model=default_model,
                functions=functions,
                function_call="auto"
            )
            print("Function calling response received")
        except Exception as e:
            print(f"Function calling (may not be supported): {type(e).__name__}")
        
        print("\n✅ LiteLLM Gateway example completed successfully!")
        
    except (ConnectionError, TimeoutError) as e:
        print(f"❌ Network error: {e}")
        print("Make sure you have a valid API key and internet connection.")
    except ValueError as e:
        print(f"❌ Validation error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure you have a valid API key and internet connection.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

