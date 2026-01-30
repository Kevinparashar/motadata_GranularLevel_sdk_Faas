"""
Request/Response models for Agent Service.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CreateAgentRequest(BaseModel):
    """Request to create an agent."""

    agent_id: Optional[str] = Field(None, description="Agent ID (generated if not provided)")
    name: str = Field(..., description="Agent name")
    description: Optional[str] = Field(None, description="Agent description")
    llm_model: Optional[str] = Field(None, description="LLM model to use")
    llm_provider: Optional[str] = Field(None, description="LLM provider")
    system_prompt: Optional[str] = Field(None, description="System prompt")
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")
    memory_config: Optional[Dict[str, Any]] = Field(None, description="Memory configuration")
    tool_ids: List[str] = Field(default_factory=list, description="Tool IDs to attach")


class UpdateAgentRequest(BaseModel):
    """Request to update an agent."""

    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    capabilities: Optional[List[str]] = None
    memory_config: Optional[Dict[str, Any]] = None


class ExecuteTaskRequest(BaseModel):
    """Request to execute an agent task."""

    task_type: str = Field(..., description="Task type")
    parameters: Dict[str, Any] = Field(..., description="Task parameters")
    priority: int = Field(default=0, description="Task priority")


class ChatRequest(BaseModel):
    """Request for chat interaction."""

    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session ID (creates new if not provided)")
    stream: bool = Field(default=False, description="Enable streaming response")


class AgentResponse(BaseModel):
    """Agent response model."""

    agent_id: str
    name: str
    description: Optional[str] = None
    status: str
    capabilities: List[str] = Field(default_factory=list)
    created_at: str
    updated_at: str


class TaskResponse(BaseModel):
    """Task execution response model."""

    task_id: str
    agent_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model."""

    session_id: str
    agent_id: str
    message: str
    metadata: Optional[Dict[str, Any]] = None
