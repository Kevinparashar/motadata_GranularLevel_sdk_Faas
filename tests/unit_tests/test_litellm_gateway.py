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
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_deduplicator"):
            gateway = LiteLLMGateway(config=gateway_config)
            setattr(gateway, 'kv_cache', None)
            setattr(gateway, 'router', None)
            setattr(gateway, 'cache', None)
            setattr(gateway, 'deduplicator', None)
            return gateway

    def test_initialization(self, gateway_config):
        """Test gateway initialization."""
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"):
            gateway = LiteLLMGateway(config=gateway_config)
            assert gateway.config is not None
            assert isinstance(gateway.config, GatewayConfig)

    @pytest.mark.asyncio
    async def test_generate(self, mock_gateway):
        """Test text generation."""
        gateway = mock_gateway

        mock_response = MagicMock(spec=['choices', 'model'])
        mock_choice = MagicMock()
        mock_choice.message.content = "Generated text"
        mock_choice.finish_reason = "stop"
        mock_response.choices = [mock_choice]
        mock_response.model = "gpt-4"
        
        with patch("src.core.litellm_gateway.gateway.completion") as mock_completion:
            mock_completion.return_value = mock_response
            response = await gateway.generate(prompt="Test prompt", model="gpt-4")

            assert response.text == "Generated text"
            assert response.model == "gpt-4"
            mock_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_async(self, mock_gateway):
        """Test async text generation."""
        gateway = mock_gateway

        mock_response = MagicMock(spec=['choices', 'model'])
        mock_choice = MagicMock()
        mock_choice.message.content = "Async generated text"
        mock_choice.finish_reason = "stop"
        mock_response.choices = [mock_choice]
        mock_response.model = "gpt-4"
        
        # generate_async uses acompletion internally
        with patch("src.core.litellm_gateway.gateway.acompletion", new_callable=AsyncMock) as mock_acompletion:
            mock_acompletion.return_value = mock_response
            response = await gateway.generate_async(prompt="Test prompt", model="gpt-4")

            assert response.text == "Async generated text"
            mock_acompletion.assert_called_once()

    @pytest.mark.asyncio
    async def test_stream(self, mock_gateway):
        """Test streaming generation."""
        gateway = mock_gateway

        mock_chunk1 = MagicMock()
        mock_chunk1.choices = [MagicMock()]
        mock_chunk1.choices[0].delta.content = "Hello "

        mock_chunk2 = MagicMock()
        mock_chunk2.choices = [MagicMock()]
        mock_chunk2.choices[0].delta.content = "World"

        async def mock_stream_generator():
            yield mock_chunk1
            yield mock_chunk2

        with patch("src.core.litellm_gateway.gateway.completion") as mock_completion:
            mock_completion.return_value = mock_stream_generator()
            response = await gateway.generate(prompt="Test prompt", model="gpt-4", stream=True)
            
            chunks = []
            async for chunk in response:
                chunks.append(chunk)

            assert len(chunks) == 2

    def test_embed(self, mock_gateway):
        """Test embedding generation."""
        gateway = mock_gateway

        mock_response = MagicMock(spec=['data', 'model'])
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
        mock_response.model = "text-embedding-3-small"
        with patch("src.core.litellm_gateway.gateway.embedding") as mock_embedding:
            mock_embedding.return_value = mock_response
            response = gateway.embed(texts=["Hello", "World"], model="text-embedding-3-small")

            assert len(response.embeddings) == 1
            assert len(response.embeddings[0]) == 1536
            mock_embedding.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling(self, mock_gateway):
        """Test error handling."""
        gateway = mock_gateway

        with patch("src.core.litellm_gateway.gateway.completion") as mock_completion:
            mock_completion.side_effect = Exception("API Error")

            with pytest.raises(Exception):
                await gateway.generate(prompt="Test", model="gpt-4")

    def test_provider_switching(self):
        """Test provider switching with model_list configuration."""
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"):
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

        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_deduplicator"), \
             patch("src.core.litellm_gateway.gateway.acompletion", new_callable=AsyncMock) as mock_acompletion:
            gateway = LiteLLMGateway(config=config)
            setattr(gateway, 'kv_cache', None)
            setattr(gateway, 'router', None)
            setattr(gateway, 'deduplicator', None)

            mock_response = MagicMock(spec=['choices', 'model'])
            mock_choice = MagicMock()
            mock_choice.message.content = "Cached response"
            mock_choice.finish_reason = "stop"
            mock_response.choices = [mock_choice]
            mock_response.model = "gpt-4"
            mock_acompletion.return_value = mock_response

            # First call - cache miss (makes API call)
            response1 = await gateway.generate_async(
                prompt="Cache test", model="gpt-4", tenant_id="test_tenant"
            )
            assert mock_acompletion.call_count == 1

            # Second call - cache hit (no API call)
            response2 = await gateway.generate_async(
                prompt="Cache test", model="gpt-4", tenant_id="test_tenant"
            )
            # Should still be 1 (no new API call)
            assert mock_acompletion.call_count == 1
            assert response1.text == response2.text

    @pytest.mark.asyncio
    async def test_cache_key_generation(self):
        """Test cache key generation with tenant isolation."""
        from src.core.cache_mechanism import CacheConfig, CacheMechanism

        cache = CacheMechanism(CacheConfig(default_ttl=3600))
        config = GatewayConfig(enable_caching=True, cache=cache)

        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_deduplicator"), \
             patch("src.core.litellm_gateway.gateway.acompletion", new_callable=AsyncMock) as mock_acompletion:
            gateway = LiteLLMGateway(config=config)
            setattr(gateway, 'kv_cache', None)
            setattr(gateway, 'router', None)
            setattr(gateway, 'deduplicator', None)

            mock_response = MagicMock(spec=['choices', 'model'])
            mock_choice = MagicMock()
            mock_choice.message.content = "Response"
            mock_choice.finish_reason = "stop"
            mock_response.choices = [mock_choice]
            mock_response.model = "gpt-4"
            mock_acompletion.return_value = mock_response

            # Same prompt, different tenants
            await gateway.generate_async(prompt="Test", model="gpt-4", tenant_id="tenant_1")
            await gateway.generate_async(prompt="Test", model="gpt-4", tenant_id="tenant_2")

            # Should make 2 API calls (different cache keys)
            assert mock_acompletion.call_count == 2

    @pytest.mark.asyncio
    async def test_cache_disabled(self):
        """Test gateway behavior when cache is disabled."""
        config = GatewayConfig(enable_caching=False)

        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_deduplicator"), \
             patch("src.core.litellm_gateway.gateway.acompletion", new_callable=AsyncMock) as mock_acompletion:
            gateway = LiteLLMGateway(config=config)
            setattr(gateway, 'kv_cache', None)
            setattr(gateway, 'router', None)
            setattr(gateway, 'deduplicator', None)

            mock_response = MagicMock(spec=['choices', 'model'])
            mock_choice = MagicMock()
            mock_choice.message.content = "Response"
            mock_choice.finish_reason = "stop"
            mock_response.choices = [mock_choice]
            mock_response.model = "gpt-4"
            mock_acompletion.return_value = mock_response

            # Multiple calls should all make API calls
            for _ in range(3):
                await gateway.generate_async(prompt="Test", model="gpt-4", tenant_id="test_tenant")

            # Should make 3 API calls (no caching)
            assert mock_acompletion.call_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
