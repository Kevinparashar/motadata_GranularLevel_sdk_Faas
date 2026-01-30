"""
Request/Response models for Prompt Service.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CreateTemplateRequest(BaseModel):
    """Request to create a prompt template."""

    template_id: Optional[str] = Field(None, description="Template ID (generated if not provided)")
    name: str = Field(..., description="Template name")
    content: str = Field(..., description="Template content")
    version: Optional[str] = Field(None, description="Template version")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Template metadata")


class UpdateTemplateRequest(BaseModel):
    """Request to update a prompt template."""

    name: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class RenderPromptRequest(BaseModel):
    """Request to render a prompt template."""

    template_name: str = Field(..., description="Template name")
    variables: Dict[str, Any] = Field(..., description="Variables to substitute")
    version: Optional[str] = Field(None, description="Template version")


class BuildContextRequest(BaseModel):
    """Request to build context."""

    messages: List[Dict[str, Any]] = Field(..., description="Messages to include in context")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens in context")
    system_prompt: Optional[str] = Field(None, description="System prompt")


class TemplateResponse(BaseModel):
    """Template response model."""

    template_id: str
    name: str
    content: str
    version: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RenderedPromptResponse(BaseModel):
    """Rendered prompt response model."""

    rendered_prompt: str
    template_name: str
    variables_used: Dict[str, Any]
    token_count: Optional[int] = None


class ContextResponse(BaseModel):
    """Context response model."""

    context: str
    token_count: int
    messages_included: int
    truncated: bool = Field(False, description="Whether context was truncated")
