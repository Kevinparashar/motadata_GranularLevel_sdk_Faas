"""
Prompt Context Management

Manages prompts, templates, and context windows.
"""

from .functions import (
    add_template,
    build_context,
    create_context_window_manager,
    create_prompt_manager,
    estimate_tokens,
    redact_sensitive,
    render_prompt,
    truncate_to_fit,
    validate_prompt_length,
)
from .prompt_manager import (
    ContextWindowManager,
    PromptContextManager,
    PromptStore,
    PromptTemplate,
)

__all__ = [
    # Core classes
    "PromptTemplate",
    "PromptStore",
    "ContextWindowManager",
    "PromptContextManager",
    # Factory functions
    "create_prompt_manager",
    "create_context_window_manager",
    # High-level convenience functions
    "render_prompt",
    "add_template",
    "build_context",
    "truncate_to_fit",
    "redact_sensitive",
    # Utility functions
    "estimate_tokens",
    "validate_prompt_length",
]
