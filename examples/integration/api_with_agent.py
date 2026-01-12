"""
API with Agent Integration Example

Demonstrates how to expose Agent functionality via REST API.
"""

# Standard library imports
import os
import sys
from pathlib import Path

# Third-party imports
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

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
from src.core.agno_agent_framework import Agent, AgentManager
from src.core.litellm_gateway import LiteLLMGateway


# Request/Response Models
class AgentTaskRequest(BaseModel):
    """Request model for agent task execution."""
    task_type: str
    parameters: dict
    priority: int = 0


class AgentTaskResponse(BaseModel):
    """Response model for agent task execution."""
    task_id: str
    status: str
    result: dict


# Initialize components
api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
provider = "openai" if os.getenv("OPENAI_API_KEY") else "anthropic"

if api_key:
    gateway = LiteLLMGateway(api_key=api_key, provider=provider)
    agent_manager = AgentManager()
    
    # Create default agent
    default_agent = Agent(
        agent_id="api-agent-001",
        name="API Agent",
        description="Agent exposed via API",
        gateway=gateway,
        llm_model="gpt-4" if provider == "openai" else "claude-3-opus-20240229"
    )
    agent_manager.register_agent(default_agent)

# Create FastAPI app
app = FastAPI(title="Agent API", version="1.0.0")


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy"}


@app.post("/agent/task", response_model=AgentTaskResponse)
async def execute_agent_task(request: AgentTaskRequest):
    """Execute an agent task."""
    if not api_key:
        raise HTTPException(status_code=500, detail="API key not configured")
    
    agent = agent_manager.get_agent("api-agent-001")
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Add task
    task_id = agent.add_task(
        task_type=request.task_type,
        parameters=request.parameters,
        priority=request.priority
    )
    
    # Execute task
    import asyncio
    task = agent.task_queue[-1]  # Get the task we just added
    result = await agent.execute_task(task)
    
    return AgentTaskResponse(
        task_id=task_id,
        status=result.get("status", "completed"),
        result=result
    )


@app.get("/agent/status")
async def get_agent_status():
    """Get agent status."""
    if not api_key:
        raise HTTPException(status_code=500, detail="API key not configured")
    
    agent = agent_manager.get_agent("api-agent-001")
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent.get_status()


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Agent API server...")
    print("📖 API Docs: http://localhost:8001/docs")
    uvicorn.run(app, host="0.0.0.0", port=8001)

