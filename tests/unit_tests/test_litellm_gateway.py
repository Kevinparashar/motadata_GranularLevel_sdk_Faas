"""
Unit Tests for LiteLLM Gateway Component

Tests LLM operations across multiple providers.
"""


from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.litellm_gateway import GatewayConfig, LiteLLMGateway


class TestLiteLLMGateway:
    """Test LiteLLMGateway."""

    @pytest.fixture
    def gateway_config(self):
        """Gateway configuration fixture."""
        return GatewayConfig()

    @pytest.fixture
    def mock_gateway(self, gateway_config):
        """Mock gateway with patched litellm."""
        with patch("src.core.litellm_gateway.gateway.litellm") as mock_litellm:
            gateway = LiteLLMGateway(config=gateway_config)
            gateway._litellm = mock_litellm  # type: ignore[attr-defined]
            return gateway, mock_litellm

    def test_initialization(self, gateway_config):
        """Test gateway initialization."""
        gateway = LiteLLMGateway(config=gateway_config)
        assert gateway.config is not None
        assert isinstance(gateway.config, GatewayConfig)

    def test_generate(self, mock_gateway):
        """Test text generation."""
        gateway, mock_litellm = mock_gateway

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated text"
        mock_response.model = "gpt-4"
        mock_litellm.completion.return_value = mock_response

        response = gateway.generate(prompt="Test prompt", model="gpt-4")

        assert response.text == "Generated text"
        assert response.model == "gpt-4"
        mock_litellm.completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_async(self, mock_gateway):
        """Test async text generation."""
        gateway, mock_litellm = mock_gateway

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Async generated text"
        mock_response.model = "gpt-4"
        mock_litellm.acompletion.return_value = mock_response

        response = await gateway.generate_async(prompt="Test prompt", model="gpt-4")

        assert response.text == "Async generated text"
        mock_litellm.acompletion.assert_called_once()

    def test_stream(self, mock_gateway):
        """Test streaming generation."""
        gateway, mock_litellm = mock_gateway

        mock_chunk1 = MagicMock()
        mock_chunk1.choices = [MagicMock()]
        mock_chunk1.choices[0].delta.content = "Hello "

        mock_chunk2 = MagicMock()
        mock_chunk2.choices = [MagicMock()]
        mock_chunk2.choices[0].delta.content = "World"

        mock_litellm.completion.return_value = [mock_chunk1, mock_chunk2]

        chunks = list(gateway.stream(prompt="Test prompt", model="gpt-4"))

        assert len(chunks) == 2

    def test_embed(self, mock_gateway):
        """Test embedding generation."""
        gateway, mock_litellm = mock_gateway

        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
        mock_litellm.embedding.return_value = mock_response

        response = gateway.embed(texts=["Hello", "World"], model="text-embedding-3-small")

        assert len(response.embeddings) == 1
        assert len(response.embeddings[0]) == 1536
        mock_litellm.embedding.assert_called_once()

    def test_error_handling(self, mock_gateway):
        """Test error handling."""
        gateway, mock_litellm = mock_gateway

        mock_litellm.completion.side_effect = Exception("API Error")

        with pytest.raises(Exception):
            gateway.generate(prompt="Test", model="gpt-4")

    def test_provider_switching(self):
        """Test provider switching with model_list configuration."""
        config_openai = GatewayConfig(model_list=[{"model_name": "gpt-4", "litellm_params": {"model": "gpt-4"}}])
        gateway_openai = LiteLLMGateway(config=config_openai)
        assert gateway_openai.config.model_list is not None

        config_anthropic = GatewayConfig(model_list=[{"model_name": "claude-3", "litellm_params": {"model": "claude-3"}}])
        gateway_anthropic = LiteLLMGateway(config=config_anthropic)
        assert gateway_anthropic.config.model_list is not None

    @pytest.mark.asyncio
    async def test_cache_integration(self):
        """Test Gateway cache integration."""
        from src.core.cache_mechanism import CacheConfig, CacheMechanism

        cache = CacheMechanism(CacheConfig(default_ttl=3600))
        config = GatewayConfig(enable_caching=True, cache_ttl=3600, cache=cache)

        with patch("src.core.litellm_gateway.gateway.litellm") as mock_litellm:
            gateway = LiteLLMGateway(config=config)
            gateway._litellm = mock_litellm  # type: ignore[attr-defined]

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Cached response"
            mock_response.model = "gpt-4"
            mock_litellm.acompletion = AsyncMock(return_value=mock_response)

            # First call - cache miss (makes API call)
            response1 = await gateway.generate_async(
                prompt="Cache test", model="gpt-4", tenant_id="test_tenant"
            )
            assert mock_litellm.acompletion.call_count == 1

            # Second call - cache hit (no API call)
            response2 = await gateway.generate_async(
                prompt="Cache test", model="gpt-4", tenant_id="test_tenant"
            )
            # Should still be 1 (no new API call)
            assert mock_litellm.acompletion.call_count == 1
            assert response1.text == response2.text

    @pytest.mark.asyncio
    async def test_cache_key_generation(self):
        """Test cache key generation with tenant isolation."""
        from src.core.cache_mechanism import CacheConfig, CacheMechanism

        cache = CacheMechanism(CacheConfig(default_ttl=3600))
        config = GatewayConfig(enable_caching=True, cache=cache)

        with patch("src.core.litellm_gateway.gateway.litellm") as mock_litellm:
            gateway = LiteLLMGateway(config=config)
            gateway._litellm = mock_litellm  # type: ignore[attr-defined]

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Response"
            mock_response.model = "gpt-4"
            mock_litellm.acompletion = AsyncMock(return_value=mock_response)

            # Same prompt, different tenants
            await gateway.generate_async(prompt="Test", model="gpt-4", tenant_id="tenant_1")
            await gateway.generate_async(prompt="Test", model="gpt-4", tenant_id="tenant_2")

            # Should make 2 API calls (different cache keys)
            assert mock_litellm.acompletion.call_count == 2

    @pytest.mark.asyncio
    async def test_cache_disabled(self):
        """Test gateway behavior when cache is disabled."""
        config = GatewayConfig(enable_caching=False)

        with patch("src.core.litellm_gateway.gateway.litellm") as mock_litellm:
            gateway = LiteLLMGateway(config=config)
            gateway._litellm = mock_litellm  # type: ignore[attr-defined]

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Response"
            mock_response.model = "gpt-4"
            mock_litellm.acompletion = AsyncMock(return_value=mock_response)

            # Multiple calls should all make API calls
            for _ in range(3):
                await gateway.generate_async(prompt="Test", model="gpt-4", tenant_id="test_tenant")

            # Should make 3 API calls (no caching)
            assert mock_litellm.acompletion.call_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
