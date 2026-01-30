"""
Basic Agent Example

Demonstrates how to use the Agent Framework component
for creating and managing AI agents.

Dependencies: LiteLLM Gateway, Evaluation & Observability
"""

# Standard library imports
import asyncio
import os
import sys
from pathlib import Path

# Third-party imports
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

if load_dotenv:
    load_dotenv(project_root / ".env")

# Local application/library specific imports
from src.core.agno_agent_framework import Agent, AgentManager
from src.core.agno_agent_framework.memory import AgentMemory, MemoryType
from src.core.agno_agent_framework.session import SessionManager
from src.core.agno_agent_framework.tools import ToolRegistry
from src.core.litellm_gateway import create_gateway


def demo_session_management(agent):
    """Demonstrate session management."""
    print("\n=== Session Management ===")
    
    session_manager = SessionManager()
    session = session_manager.create_session(agent_id=agent.agent_id, max_history=100)
    
    print(f"Created session: {session.session_id}")
    print(f"Session agent: {session.agent_id}")
    
    # Add messages to session
    session.add_message("user", "Hello, agent!")
    session.add_message("assistant", "Hello! How can I help you?")
    
    print(f"Session messages: {len(session.messages)}")


def demo_memory_management(agent):
    """Demonstrate memory management."""
    print("\n=== Memory Management ===")
    
    memory = AgentMemory(agent_id=agent.agent_id)
    
    # Store short-term memory
    memory.store(
        content="User prefers concise answers", memory_type=MemoryType.SHORT_TERM, importance=0.7
    )
    
    # Store long-term memory
    memory.store(
        content="User is a software developer", memory_type=MemoryType.LONG_TERM, importance=0.9
    )
    
    # Retrieve memories
    memories = memory.retrieve(query="user preferences", limit=5)
    print(f"Retrieved {len(memories)} memories")


def demo_tool_management():
    """Demonstrate tool management."""
    print("\n=== Tool Management ===")
    
    def calculator_tool(a: float, b: float, operation: str) -> float:
        """Simple calculator tool."""
        if operation == "add":
            return a + b
        elif operation == "multiply":
            return a * b
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    # Register tool using function registration (auto-detects parameters)
    tool_registry = ToolRegistry()
    tool_registry.register_function(
        tool_id="calc-001",
        name="calculator",
        description="Perform basic calculations",
        function=calculator_tool,
    )
    
    print("Registered tool: calculator")
    
    # Execute tool
    tool = tool_registry.get_tool_by_name("calculator")
    if tool:
        result = tool.execute(a=5, b=3, operation="add")
        print(f"Tool result: 5 + 3 = {result}")


async def demo_task_execution(agent, default_model):
    """Demonstrate task execution."""
    print("\n=== Task Execution ===")
    
    task_id = agent.add_task(
        task_type="llm_query",
        parameters={"prompt": "Explain what AI is in one sentence.", "model": default_model},
        priority=1,
    )
    
    print(f"Added task: {task_id}")
    
    # Execute task
    if agent.task_queue:
        task = agent.task_queue[0]
        try:
            result = await agent.execute_task(task)
            print(f"Task completed: {result.get('status')}")
            if "result" in result:
                print(f"Result: {result['result'][:100]}...")
        except (ConnectionError, TimeoutError) as e:
            print(f"Network error during task execution: {type(e).__name__}")
        except ValueError as e:
            print(f"Validation error during task execution: {type(e).__name__}")
        except Exception as e:
            print(f"Task execution error: {type(e).__name__}")


def demo_agent_manager(agent):
    """Demonstrate agent manager."""
    print("\n=== Agent Manager ===")
    
    manager = AgentManager()
    manager.register_agent(agent)
    
    # Get agent status
    status = agent.get_status()
    print(f"Agent status: {status['status']}")
    print(f"Capabilities: {status['capabilities']}")
    
    # List all agents
    agent_ids = manager.list_agents()
    print(f"Registered agents: {agent_ids}")


async def main():
    """Demonstrate basic agent features."""

    # Initialize gateway for agent
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  Warning: No API key found. Set OPENAI_API_KEY in .env")
        print("Example will show structure but won't make actual API calls.")
        return

    provider = "openai" if os.getenv("OPENAI_API_KEY") else "anthropic"
    default_model = "gpt-3.5-turbo" if provider == "openai" else "claude-3-haiku-20240307"
    gateway = create_gateway(
        providers=[provider], default_model=default_model, api_keys={provider: api_key}
    )

    # 1. Create an Agent
    print("=== Creating Agent ===")

    agent = Agent(
        agent_id="agent-001",
        name="Assistant Agent",
        description="A helpful AI assistant",
        gateway=gateway,
        llm_model=default_model,
    )

    # Add capabilities
    agent.add_capability(
        name="text_generation",
        description="Generate text responses",
        parameters={"max_tokens": 1000},
    )

    print(f"Created agent: {agent.name} (ID: {agent.agent_id})")
    print(f"Capabilities: {[cap.name for cap in agent.capabilities]}")

    # Run demonstrations
    demo_session_management(agent)
    demo_memory_management(agent)
    demo_tool_management()
    await demo_task_execution(agent, default_model)
    demo_agent_manager(agent)

    print("\n✅ Agent example completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
