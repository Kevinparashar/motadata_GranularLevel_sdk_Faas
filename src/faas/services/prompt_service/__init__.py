"""
Prompt Service - FaaS implementation of Prompt Context Management.

Provides REST API for prompt template management and context building.
"""


from .models import (
    BuildContextRequest,
    ContextResponse,
    CreateTemplateRequest,
    RenderedPromptResponse,
    RenderPromptRequest,
    TemplateResponse,
    UpdateTemplateRequest,
)
from .service import PromptService, create_prompt_service

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
