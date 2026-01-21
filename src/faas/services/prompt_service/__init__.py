"""
Prompt Service - FaaS implementation of Prompt Context Management.

Provides REST API for prompt template management and context building.
"""

from .service import PromptService, create_prompt_service
from .models import (
    CreateTemplateRequest,
    UpdateTemplateRequest,
    RenderPromptRequest,
    BuildContextRequest,
    TemplateResponse,
    RenderedPromptResponse,
    ContextResponse,
)

__all__ = [
    "PromptService",
    "create_prompt_service",
    "CreateTemplateRequest",
    "UpdateTemplateRequest",
    "RenderPromptRequest",
    "BuildContextRequest",
    "TemplateResponse",
    "RenderedPromptResponse",
    "ContextResponse",
]

