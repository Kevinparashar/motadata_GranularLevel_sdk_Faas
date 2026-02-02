"""
Unit Tests for Prompt Context Management Functions

Tests factory functions, convenience functions, and utilities for prompt context management.
"""

import pytest

from src.core.prompt_context_management.functions import (  # Factory functions; High-level convenience functions; Utility functions
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
from src.core.prompt_context_management.prompt_manager import (
    ContextWindowManager,
    PromptContextManager,
)


class TestFactoryFunctions:
    """Test factory functions for prompt manager creation."""

    def test_create_prompt_manager(self):
        """Test create_prompt_manager factory function."""
        manager = create_prompt_manager(max_tokens=8000, safety_margin=200)

        assert isinstance(manager, PromptContextManager)
        assert manager.window.max_tokens == 8000
        assert manager.window.safety_margin == 200

    def test_create_prompt_manager_defaults(self):
        """Test create_prompt_manager with default parameters."""
        manager = create_prompt_manager()

        assert isinstance(manager, PromptContextManager)
        assert manager.window.max_tokens == 4000
        assert manager.window.safety_margin == 200

    def test_create_context_window_manager(self):
        """Test create_context_window_manager factory function."""
        window_manager = create_context_window_manager(max_tokens=8000, safety_margin=200)

        assert isinstance(window_manager, ContextWindowManager)
        assert window_manager.max_tokens == 8000
        assert window_manager.safety_margin == 200

    def test_create_context_window_manager_defaults(self):
        """Test create_context_window_manager with default parameters."""
        window_manager = create_context_window_manager()

        assert isinstance(window_manager, ContextWindowManager)
        assert window_manager.max_tokens == 4000
        assert window_manager.safety_margin == 200


class TestConvenienceFunctions:
    """Test high-level convenience functions."""

    @pytest.fixture
    def prompt_manager(self):
        """Create a prompt manager for testing."""
        manager = create_prompt_manager(max_tokens=4000)
        # Add a test template
        manager.add_template(
            name="test_template",
            version="1.0",
            content="Hello {name}, you are {age} years old.",
        )
        return manager

    def test_render_prompt(self, prompt_manager):
        """Test render_prompt convenience function."""
        variables = {"name": "John", "age": "30"}

        result = render_prompt(
            manager=prompt_manager, template_name="test_template", variables=variables
        )

        assert "John" in result
        assert "30" in result
        assert "Hello" in result

    def test_render_prompt_with_version(self, prompt_manager):
        """Test render_prompt with version parameter."""
        variables = {"name": "John", "age": "30"}

        result = render_prompt(
            manager=prompt_manager,
            template_name="test_template",
            variables=variables,
            version="1.0",
        )

        assert "John" in result

    def test_add_template(self, prompt_manager):
        """Test add_template convenience function."""
        add_template(
            manager=prompt_manager,
            name="new_template",
            version="1.0",
            content="Template: {variable}",
            metadata={"description": "New template"},
        )

        # Verify template was added
        result = render_prompt(
            manager=prompt_manager, template_name="new_template", variables={"variable": "value"}
        )

        assert "value" in result

    def test_build_context(self, prompt_manager):
        """Test build_context convenience function."""
        # Add history to manager
        prompt_manager.history = ["Hello", "Hi there!"]

        context = build_context(
            manager=prompt_manager, new_message="What is AI?", include_history=True
        )

        assert "What is AI?" in context
        assert "Hello" in context or "Hi there!" in context

    def test_build_context_no_history(self, prompt_manager):
        """Test build_context without history."""
        context = build_context(
            manager=prompt_manager, new_message="What is AI?", include_history=False
        )

        assert "What is AI?" in context

    def test_truncate_to_fit(self, prompt_manager):
        """Test truncate_to_fit convenience function."""
        long_text = "A" * 10000  # Very long text

        truncated = truncate_to_fit(manager=prompt_manager, prompt=long_text, max_tokens=100)

        assert len(truncated) < len(long_text)
        assert len(truncated) > 0

    def test_truncate_to_fit_short_text(self, prompt_manager):
        """Test truncate_to_fit with text that fits."""
        short_text = "Short text"

        truncated = truncate_to_fit(manager=prompt_manager, prompt=short_text, max_tokens=100)

        assert truncated == short_text

    def test_redact_sensitive(self, prompt_manager):
        """Test redact_sensitive convenience function."""
        text = "My email is john@example.com and phone is 123-456-7890"

        redacted = redact_sensitive(manager=prompt_manager, text=text)

        # Should redact sensitive information
        assert "john@example.com" not in redacted or "[REDACTED]" in redacted
        assert "123-456-7890" not in redacted or "[REDACTED]" in redacted


class TestUtilityFunctions:
    """Test utility functions."""

    @pytest.fixture
    def prompt_manager(self):
        """Create a prompt manager for testing."""
        return create_prompt_manager(max_tokens=4000)

    def test_estimate_tokens(self, prompt_manager):
        """Test estimate_tokens utility function."""
        text = "This is a test sentence with multiple words."

        token_count = estimate_tokens(prompt_manager, text)

        assert isinstance(token_count, int)
        assert token_count > 0

    def test_estimate_tokens_empty(self, prompt_manager):
        """Test estimate_tokens with empty text."""
        token_count = estimate_tokens(prompt_manager, "")

        assert token_count == 0

    def test_estimate_tokens_long_text(self, prompt_manager):
        """Test estimate_tokens with long text."""
        long_text = "Word " * 1000

        token_count = estimate_tokens(prompt_manager, long_text)

        assert token_count > 0
        assert isinstance(token_count, int)

    def test_validate_prompt_length(self, prompt_manager):
        """Test validate_prompt_length utility function."""
        text = "Short text"
        max_tokens = 100

        result = validate_prompt_length(prompt_manager, text, max_tokens)

        assert result["fits"] is True

    def test_validate_prompt_length_too_long(self, prompt_manager):
        """Test validate_prompt_length with text that's too long."""
        long_text = "Word " * 10000
        max_tokens = 100

        result = validate_prompt_length(prompt_manager, long_text, max_tokens)

        assert result["fits"] is False

    def test_validate_prompt_length_exact(self, prompt_manager):
        """Test validate_prompt_length with text at exact limit."""
        # Create text that's approximately at the limit
        text = "Word " * 50  # Approximate 50 tokens
        max_tokens = 50

        result = validate_prompt_length(prompt_manager, text, max_tokens)

        # Should be valid (with some margin)
        assert isinstance(result, dict)
        assert "fits" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
