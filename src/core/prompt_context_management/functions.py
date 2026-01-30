"""
Prompt Context Management - High-Level Functions

Factory functions, convenience functions, and utilities for prompt management.
"""

from typing import Any, Dict, List, Optional

from .prompt_manager import ContextWindowManager, PromptContextManager

# ============================================================================
# Factory Functions
# ============================================================================


def create_prompt_manager(max_tokens: int = 4000, safety_margin: int = 200) -> PromptContextManager:
    """
    Create and configure a PromptContextManager with default settings.

    Args:
        max_tokens: Maximum tokens in context window
        safety_margin: Safety margin for token estimation

    Returns:
        Configured PromptContextManager instance

    Example:
        >>> manager = create_prompt_manager(max_tokens=8000)
    """
    return PromptContextManager(max_tokens=max_tokens, safety_margin=safety_margin)


def create_context_window_manager(
    max_tokens: int = 4000, safety_margin: int = 200
) -> ContextWindowManager:
    """
    Create a ContextWindowManager with specified settings.

    Args:
        max_tokens: Maximum tokens
        safety_margin: Safety margin

    Returns:
        ContextWindowManager instance

    Example:
        >>> window = create_context_window_manager(max_tokens=8000)
    """
    return ContextWindowManager(max_tokens=max_tokens, safety_margin=safety_margin)


# ============================================================================
# High-Level Convenience Functions
# ============================================================================


def render_prompt(
    manager: PromptContextManager,
    template_name: str,
    variables: Dict[str, Any],
    version: Optional[str] = None,
) -> str:
    """
    Render a prompt template with variables (high-level convenience).

    Args:
        manager: PromptContextManager instance
        template_name: Name of template
        variables: Variables to substitute
        version: Optional template version

    Returns:
        Rendered prompt string

    Example:
        >>> prompt = render_prompt(
        ...     manager,
        ...     "analysis_template",
        ...     {"text": "Analyze this", "model": "gpt-4"}
        ... )
    """
    return manager.render(template_name=template_name, variables=variables, version=version)


def add_template(
    manager: PromptContextManager,
    name: str,
    version: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Add a prompt template (high-level convenience).

    Args:
        manager: PromptContextManager instance
        name: Template name
        version: Template version
        content: Template content
        metadata: Optional metadata

    Example:
        >>> add_template(
        ...     manager,
        ...     "greeting",
        ...     "1.0",
        ...     "Hello {name}, welcome to {service}!"
        ... )
    """
    manager.add_template(name=name, version=version, content=content, metadata=metadata)


def build_context(
    manager: PromptContextManager, new_message: str, include_history: bool = True
) -> str:
    """
    Build context from history and new message (high-level convenience).

    Args:
        manager: PromptContextManager instance
        new_message: New message to add
        include_history: Whether to include history

    Returns:
        Built context string

    Example:
        >>> context = build_context(manager, "What is AI?", include_history=True)
    """
    if include_history:
        return manager.build_context_with_history(new_message)
    else:
        return manager.window.build_context([new_message])


def truncate_to_fit(
    manager: PromptContextManager, prompt: str, max_tokens: Optional[int] = None
) -> str:
    """
    Truncate prompt to fit within token limits (high-level convenience).

    Args:
        manager: PromptContextManager instance
        prompt: Prompt to truncate
        max_tokens: Optional max tokens (uses manager default if not provided)

    Returns:
        Truncated prompt

    Example:
        >>> truncated = truncate_to_fit(manager, long_prompt, max_tokens=2000)
    """
    return manager.truncate_prompt(prompt, max_tokens=max_tokens)


def redact_sensitive(
    manager: PromptContextManager, text: str, patterns: Optional[List[str]] = None
) -> str:
    """
    Redact sensitive information from text (high-level convenience).

    Args:
        manager: PromptContextManager instance
        text: Text to redact
        patterns: Optional custom patterns

    Returns:
        Redacted text

    Example:
        >>> safe_text = redact_sensitive(manager, "API key: sk-1234567890")
    """
    return manager.strip_sensitive(text, patterns=patterns)


# ============================================================================
# Utility Functions
# ============================================================================


def estimate_tokens(manager: PromptContextManager, text: str) -> int:
    """
    Estimate token count for text (utility function).

    Args:
        manager: PromptContextManager instance
        text: Text to estimate

    Returns:
        Estimated token count

    Example:
        >>> tokens = estimate_tokens(manager, "Hello world")
    """
    return manager.window.estimate_tokens(text)


def validate_prompt_length(
    manager: PromptContextManager, prompt: str, max_tokens: Optional[int] = None
) -> Dict[str, Any]:
    """
    Validate if prompt fits within token limits (utility function).

    Args:
        manager: PromptContextManager instance
        prompt: Prompt to validate
        max_tokens: Optional max tokens

    Returns:
        Dictionary with validation results

    Example:
        >>> result = validate_prompt_length(manager, prompt)
        >>> if not result["fits"]:
        ...     print(f"Prompt too long: {result['tokens']} tokens")
    """
    max_tokens = max_tokens or manager.window.max_tokens
    tokens = estimate_tokens(manager, prompt)
    fits = tokens <= (max_tokens - manager.window.safety_margin)

    return {
        "fits": fits,
        "tokens": tokens,
        "max_tokens": max_tokens,
        "safety_margin": manager.window.safety_margin,
        "available_tokens": max_tokens - manager.window.safety_margin,
    }


__all__ = [
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
