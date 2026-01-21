"""
Request/Response models for Gateway Service.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """Request for text generation."""

    prompt: str = Field(..., description="Generation prompt")
    model: Optional[str] = Field(None, description="Model to use (overrides default)")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Generation temperature")
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="Top-p sampling")
    frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0, description="Frequency penalty")
    presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0, description="Presence penalty")
    stop: Optional[List[str]] = Field(None, description="Stop sequences")
    stream: bool = Field(default=False, description="Enable streaming response")


class GenerateStreamRequest(BaseModel):
    """Request for streaming text generation."""

    prompt: str = Field(..., description="Generation prompt")
    model: Optional[str] = Field(None, description="Model to use")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Generation temperature")


class EmbedRequest(BaseModel):
    """Request for embedding generation."""

    texts: List[str] = Field(..., description="Texts to embed")
    model: Optional[str] = Field(None, description="Embedding model to use (overrides default)")


class GenerateResponse(BaseModel):
    """Text generation response model."""

    text: str = Field(..., description="Generated text")
    model: str = Field(..., description="Model used")
    usage: Optional[Dict[str, Any]] = Field(None, description="Token usage information")
    finish_reason: Optional[str] = Field(None, description="Finish reason")
    raw_response: Optional[Dict[str, Any]] = Field(None, description="Raw LLM response")


class EmbedResponse(BaseModel):
    """Embedding response model."""

    embeddings: List[List[float]] = Field(..., description="Embedding vectors")
    model: str = Field(..., description="Model used")
    usage: Optional[Dict[str, Any]] = Field(None, description="Token usage information")

