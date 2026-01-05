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

from src.core.litellm_gateway import LiteLLMGateway


def main():
    """Demonstrate basic gateway features."""
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  Warning: No API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env")
        print("Example will show structure but won't make actual API calls.")
        return
    
    # Initialize gateway
    provider = "openai" if os.getenv("OPENAI_API_KEY") else "anthropic"
    gateway = LiteLLMGateway(
        api_key=api_key,
        provider=provider
    )
    
    try:
        # 1. Text Generation
        print("=== Text Generation ===")
        
        response = gateway.generate(
            prompt="Explain quantum computing in one sentence.",
            model="gpt-4" if provider == "openai" else "claude-3-opus-20240229",
            max_tokens=100
        )
        
        print(f"Generated text: {response.text}")
        print(f"Model used: {response.model}")
        print(f"Tokens used: {response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}")
        
        # 2. Streaming Generation
        print("\n=== Streaming Generation ===")
        
        print("Streaming response:")
        for chunk in gateway.stream(
            prompt="Count from 1 to 5:",
            model="gpt-4" if provider == "openai" else "claude-3-opus-20240229",
            max_tokens=50
        ):
            if hasattr(chunk, 'choices') and chunk.choices:
                content = chunk.choices[0].delta.content
                if content:
                    print(content, end="", flush=True)
        print()  # New line after streaming
        
        # 3. Embeddings
        print("\n=== Embeddings ===")
        
        embedding_response = gateway.embed(
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
            response = gateway.generate(
                prompt="What's the weather in San Francisco?",
                model="gpt-4" if provider == "openai" else "claude-3-opus-20240229",
                functions=functions,
                function_call="auto"
            )
            print("Function calling response received")
        except Exception as e:
            print(f"Function calling (may not be supported): {type(e).__name__}")
        
        print("\n✅ LiteLLM Gateway example completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure you have a valid API key and internet connection.")


if __name__ == "__main__":
    main()

