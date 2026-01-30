"""
Unit Tests for LiteLLM Gateway Functions

Tests factory functions, convenience functions, and utilities for LiteLLM Gateway.
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.core.litellm_gateway import GatewayConfig, LiteLLMGateway
from src.core.litellm_gateway.functions import (  # Factory functions; High-level convenience functions; Utility functions
    batch_generate,
    configure_gateway,
    create_gateway,
    generate_embeddings,
    generate_embeddings_async,
    generate_text,
    generate_text_async,
    stream_text,
)


class TestFactoryFunctions:
    """Test factory functions for gateway creation."""

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_create_gateway(self):
        """Test create_gateway factory function."""
        gateway = create_gateway(
            providers=["openai"], default_model="gpt-4", timeout=60.0, max_retries=3
        )

        assert isinstance(gateway, LiteLLMGateway)
        assert gateway.config is not None

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "ANTHROPIC_API_KEY": "test-key-2"})
    def test_create_gateway_multiple_providers(self):
        """Test create_gateway with multiple providers."""
        gateway = create_gateway(
            providers=["openai", "anthropic"],
            default_model="gpt-4",
            api_keys={"openai": "sk-test", "anthropic": "sk-test-2"},
        )

        assert isinstance(gateway, LiteLLMGateway)

    def test_create_gateway_with_api_keys(self):
        """Test create_gateway with explicit API keys."""
        gateway = create_gateway(
            providers=["openai"], default_model="gpt-4", api_keys={"openai": "sk-test-key"}
        )

        assert isinstance(gateway, LiteLLMGateway)

    def test_create_gateway_with_fallbacks(self):
        """Test create_gateway with fallback models."""
        gateway = create_gateway(
            providers=["openai"], default_model="gpt-4", fallbacks=["gpt-3.5-turbo", "claude-3"]
        )

        assert isinstance(gateway, LiteLLMGateway)
        assert gateway.config.fallbacks is not None

    def test_create_gateway_defaults(self):
        """Test create_gateway with default parameters."""
        gateway = create_gateway()

        assert isinstance(gateway, LiteLLMGateway)

    def test_configure_gateway(self):
        """Test configure_gateway factory function."""
        config = configure_gateway(
            model_list=[{"model_name": "gpt-4"}],
            fallbacks=["gpt-3.5-turbo"],
            timeout=60.0,
            max_retries=3,
            retry_delay=1.0,
        )

        assert isinstance(config, GatewayConfig)
        assert config.timeout == 60.0
        assert config.max_retries == 3


class TestConvenienceFunctions:
    """Test high-level convenience functions."""

    @pytest.fixture
    def mock_gateway(self):
        """Create a mock gateway."""
        gateway = Mock(spec=LiteLLMGateway)
        gateway.generate = Mock(return_value=Mock(text="Generated text", model="gpt-4"))
        gateway.generate_async = AsyncMock(
            return_value=Mock(text="Async generated text", model="gpt-4")
        )
        gateway.stream = Mock(return_value=[Mock(text="Hello "), Mock(text="World")])
        gateway.generate_embeddings = Mock(
            return_value=Mock(embeddings=[[0.1] * 1536, [0.2] * 1536])
        )
        gateway.generate_embeddings_async = AsyncMock(return_value=Mock(embeddings=[[0.1] * 1536]))
        return gateway

    def test_generate_text(self, mock_gateway):
        """Test generate_text convenience function."""
        result = generate_text(gateway=mock_gateway, prompt="What is AI?", model="gpt-4")

        assert result == "Generated text"
        mock_gateway.generate.assert_called_once()

    def test_generate_text_with_messages(self, mock_gateway):
        """Test generate_text with messages parameter."""
        messages = [{"role": "user", "content": "Hello"}]

        result = generate_text(
            gateway=mock_gateway, prompt="Test", model="gpt-4", messages=messages
        )

        assert result == "Generated text"

    @pytest.mark.asyncio
    async def test_generate_text_async(self, mock_gateway):
        """Test generate_text_async convenience function."""
        result = await generate_text_async(
            gateway=mock_gateway, prompt="What is AI?", model="gpt-4"
        )

        assert result.text == "Async generated text"
        mock_gateway.generate_async.assert_called_once()

    def test_stream_text(self, mock_gateway):
        """Test stream_text convenience function."""
        chunks = list(stream_text(gateway=mock_gateway, prompt="Hello", model="gpt-4"))

        assert len(chunks) == 2
        assert chunks[0].text == "Hello "
        assert chunks[1].text == "World"

    def test_generate_embeddings(self, mock_gateway):
        """Test generate_embeddings convenience function."""
        texts = ["Hello", "World"]
        embeddings = generate_embeddings(
            gateway=mock_gateway, texts=texts, model="text-embedding-3-small"
        )

        assert len(embeddings) == 2
        assert len(embeddings[0]) == 1536
        mock_gateway.generate_embeddings.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_embeddings_async(self, mock_gateway):
        """Test generate_embeddings_async convenience function."""
        texts = ["Hello"]
        embeddings = await generate_embeddings_async(
            gateway=mock_gateway, texts=texts, model="text-embedding-3-small"
        )

        assert len(embeddings) == 1
        assert len(embeddings[0]) == 1536
        mock_gateway.generate_embeddings_async.assert_called_once()


class TestUtilityFunctions:
    """Test utility functions."""

    @pytest.fixture
    def mock_gateway(self):
        """Create a mock gateway."""
        gateway = Mock(spec=LiteLLMGateway)
        gateway.generate_async = AsyncMock(
            side_effect=[Mock(text="Response 1"), Mock(text="Response 2"), Mock(text="Response 3")]
        )
        return gateway

    @pytest.mark.asyncio
    async def test_batch_generate(self, mock_gateway):
        """Test batch_generate utility function."""
        prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]

        results = await batch_generate(gateway=mock_gateway, prompts=prompts, model="gpt-4")

        assert len(results) == 3
        assert results[0].text == "Response 1"
        assert results[1].text == "Response 2"
        assert results[2].text == "Response 3"
        assert mock_gateway.generate_async.call_count == 3

    @pytest.mark.asyncio
    async def test_batch_generate_empty(self, mock_gateway):
        """Test batch_generate with empty prompt list."""
        results = await batch_generate(gateway=mock_gateway, prompts=[], model="gpt-4")

        assert results == []
        mock_gateway.generate_async.assert_not_called()

    @pytest.mark.asyncio
    async def test_batch_generate_with_exceptions(self, mock_gateway):
        """Test batch_generate with exceptions."""
        mock_gateway.generate_async = AsyncMock(
            side_effect=[Mock(text="Response 1"), Exception("Error"), Mock(text="Response 3")]
        )

        prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]
        results = await batch_generate(gateway=mock_gateway, prompts=prompts, model="gpt-4")

        # Should handle exceptions gracefully
        assert len(results) == 3
        assert isinstance(results[0], Mock)
        assert isinstance(results[1], Exception)
        assert isinstance(results[2], Mock)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
