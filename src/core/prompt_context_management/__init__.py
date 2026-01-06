"""
Prompt Context Management

Manages prompts, templates, and context windows.
"""

from .prompt_manager import (
    PromptTemplate,
    PromptStore,
    ContextWindowManager,
    PromptContextManager,
)
from .functions import (
    create_prompt_manager,
    create_context_window_manager,
    render_prompt,
    add_template,
    build_context,
    truncate_to_fit,
    redact_sensitive,
    estimate_tokens,
    validate_prompt_length,
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

