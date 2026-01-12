"""
Basic Connectivity Example

Demonstrates how to use the Connectivity component
for managing HTTP and WebSocket connections.

Dependencies: Pool Implementation, Evaluation & Observability
"""

# Standard library imports
import asyncio
import os
import sys
from pathlib import Path

# Third-party imports
try:
    from dotenv import load_dotenv  # type: ignore
except ImportError:
    load_dotenv = None

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

if load_dotenv:
    load_dotenv(project_root / ".env")

# Local application/library specific imports
from connectivity_clients import ClientManager, HTTPClient, WebSocketClient


async def main():
    """Demonstrate basic connectivity features."""
    
    # 1. HTTP Client Example
    print("=== HTTP Client Example ===")
    
    http_client = HTTPClient(
        base_url="https://api.example.com",
        timeout=30,
        retry_count=3
    )
    
    # Make GET request
    try:
        response = await http_client.get("/endpoint", params={"key": "value"})
        print(f"GET Response status: {response.status_code}")
    except (ConnectionError, TimeoutError) as e:
        print(f"GET request (expected to fail in example): {type(e).__name__}")
    except Exception as e:
        print(f"GET request (expected to fail in example): {type(e).__name__}")
    
    # Make POST request
    try:
        response = await http_client.post(
            "/endpoint",
            json={"data": "test"},
            headers={"Content-Type": "application/json"}
        )
        print(f"POST Response status: {response.status_code}")
    except (ConnectionError, TimeoutError) as e:
        print(f"POST request (expected to fail in example): {type(e).__name__}")
    except Exception as e:
        print(f"POST request (expected to fail in example): {type(e).__name__}")
    
    # 2. WebSocket Client Example
    print("\n=== WebSocket Client Example ===")
    
    ws_client = WebSocketClient(
        url="wss://api.example.com/ws",
        reconnect=True,
        reconnect_interval=5
    )
    
    # Connect (in real scenario)
    # await ws_client.connect()
    # await ws_client.send({"message": "Hello"})
    # message = await ws_client.receive()
    # await ws_client.close()
    
    print("WebSocket client configured (connection skipped in example)")
    
    # 3. Client Manager Example
    print("\n=== Client Manager Example ===")
    
    manager = ClientManager()
    
    # Register clients
    manager.register_client("http", http_client)
    manager.register_client("websocket", ws_client)
    
    # Get client
    client = manager.get_client("http")
    print(f"Retrieved client: {type(client).__name__}")
    
    # Health check
    health_status = await manager.check_health()
    print(f"Health status: {health_status}")
    
    # Cleanup
    await http_client.close()
    await ws_client.close()
    
    print("\n✅ Connectivity example completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())

