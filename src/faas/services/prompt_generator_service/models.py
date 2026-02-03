"""
Request/Response models for Prompt Generator Service.
"""


from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CreateAgentFromPromptRequest(BaseModel):
    """Request to create an agent from a prompt."""

    prompt: str = Field(..., description="Natural language description of the agent")
    agent_id: Optional[str] = Field(None, description="Agent ID (generated if not provided)")
    llm_model: Optional[str] = Field(None, description="LLM model to use for generation")
    llm_provider: Optional[str] = Field(None, description="LLM provider")
    cache_enabled: bool = Field(default=True, description="Enable caching of interpretations")
    additional_config: Optional[Dict[str, Any]] = Field(
        None, description="Additional agent configuration"
    )


class CreateToolFromPromptRequest(BaseModel):
    """Request to create a tool from a prompt."""

    prompt: str = Field(..., description="Natural language description of the tool")
    tool_id: Optional[str] = Field(None, description="Tool ID (generated if not provided)")
    llm_model: Optional[str] = Field(None, description="LLM model to use for generation")
    llm_provider: Optional[str] = Field(None, description="LLM provider")
    cache_enabled: bool = Field(default=True, description="Enable caching of interpretations")
    additional_config: Optional[Dict[str, Any]] = Field(
        None, description="Additional tool configuration"
    )


class RateAgentRequest(BaseModel):
    """Request to rate an agent."""

    agent_id: str = Field(..., description="Agent ID")
    rating: int = Field(..., ge=1, le=5, description="Rating (1-5)")
    feedback: Optional[str] = Field(None, description="Optional feedback text")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class RateToolRequest(BaseModel):
    """Request to rate a tool."""

    tool_id: str = Field(..., description="Tool ID")
    rating: int = Field(..., ge=1, le=5, description="Rating (1-5)")
    feedback: Optional[str] = Field(None, description="Optional feedback text")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class GrantPermissionRequest(BaseModel):
    """Request to grant permission."""

    resource_type: str = Field(..., description="Resource type (agent or tool)")
    resource_id: str = Field(..., description="Resource ID")
    user_id: str = Field(..., description="User ID")
    permission: str = Field(..., description="Permission type (read, write, execute)")


class AgentGenerationResponse(BaseModel):
    """Response for agent generation."""

    agent_id: str
    name: str
    description: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)
    system_prompt: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    created_at: str


class ToolGenerationResponse(BaseModel):
    """Response for tool generation."""

    tool_id: str
    name: str
    description: Optional[str] = None
    code: str
    parameters: List[Dict[str, Any]] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)
    created_at: str


class FeedbackResponse(BaseModel):
    """Response for feedback submission."""

    feedback_id: str
    resource_type: str
    resource_id: str
    rating: int
    feedback: Optional[str] = None
    submitted_at: str


class FeedbackStatsResponse(BaseModel):
    """Response for feedback statistics."""

    resource_id: str
    resource_type: str
    total_ratings: int
    average_rating: float
    rating_distribution: Dict[int, int] = Field(default_factory=dict)
    total_feedback: int
