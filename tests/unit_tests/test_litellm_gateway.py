"""
Unit Tests for LiteLLM Gateway Component

Tests LLM operations across multiple providers.
"""


from typing import List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.litellm_gateway import GatewayConfig, LiteLLMGateway
from src.core.llmops import LLMOperationStatus


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


    def test_initialize_router_with_router(self, gateway_config):
        """Test router initialization with provided router."""
        mock_router = MagicMock()
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"):
            gateway = LiteLLMGateway(config=gateway_config, router=mock_router)
            assert gateway.router == mock_router

    def test_initialize_router_with_model_list(self):
        """Test router initialization with model_list."""
        config = GatewayConfig(
            model_list=[{"model_name": "gpt-4", "litellm_params": {"model": "gpt-4"}}]
        )
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.Router") as mock_router_class:
            LiteLLMGateway(config=config)
            mock_router_class.assert_called_once()

    def test_initialize_router_with_fallbacks(self):
        """Test router initialization with fallbacks."""
        config = GatewayConfig(
            model_list=[{"model_name": "gpt-4", "litellm_params": {"model": "gpt-4"}}],
            fallbacks=["gpt-3.5-turbo"]
        )
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.Router") as mock_router_class:
            LiteLLMGateway(config=config)
            call_kwargs = mock_router_class.call_args[1]
            assert "fallbacks" in call_kwargs

    def test_initialize_circuit_breaker_enabled(self):
        """Test circuit breaker initialization when enabled."""
        config = GatewayConfig(enable_circuit_breaker=True)
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"):
            gateway = LiteLLMGateway(config=config)
            assert gateway.circuit_breaker is not None

    def test_initialize_circuit_breaker_disabled(self):
        """Test circuit breaker initialization when disabled."""
        config = GatewayConfig(enable_circuit_breaker=False)
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"):
            gateway = LiteLLMGateway(config=config)
            assert gateway.circuit_breaker is None

    def test_initialize_deduplicator_enabled(self):
        """Test deduplicator initialization when enabled."""
        config = GatewayConfig(enable_request_deduplication=True)
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"):
            gateway = LiteLLMGateway(config=config)
            assert gateway.deduplicator is not None

    def test_initialize_deduplicator_disabled(self):
        """Test deduplicator initialization when disabled."""
        config = GatewayConfig(enable_request_deduplication=False)
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"):
            gateway = LiteLLMGateway(config=config)
            assert gateway.deduplicator is None

    def test_initialize_batcher_enabled(self):
        """Test batcher initialization when enabled."""
        config = GatewayConfig(enable_request_batching=True, batch_size=5, batch_timeout=1.0)
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"):
            gateway = LiteLLMGateway(config=config)
            assert gateway.batcher is not None

    def test_initialize_batcher_disabled(self):
        """Test batcher initialization when disabled."""
        config = GatewayConfig(enable_request_batching=False)
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"):
            gateway = LiteLLMGateway(config=config)
            assert gateway.batcher is None

    def test_initialize_kv_cache_enabled(self):
        """Test KV cache initialization when enabled."""
        from src.core.cache_mechanism import CacheConfig, CacheMechanism
        cache = CacheMechanism(CacheConfig())
        config = GatewayConfig(enable_kv_cache=True, enable_caching=True, cache=cache)
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"), \
             patch("src.core.litellm_gateway.gateway.create_kv_cache_manager") as mock_create:
            mock_create.return_value = MagicMock()
            # Don't patch _initialize_cache - let it run so cache is set before KV cache
            gateway = LiteLLMGateway(config=config)
            # KV cache is initialized in __init__, verify it was called
            assert mock_create.call_count >= 1
            assert gateway.kv_cache is not None

    def test_initialize_kv_cache_disabled(self):
        """Test KV cache initialization when disabled."""
        config = GatewayConfig(enable_kv_cache=False)
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"):
            gateway = LiteLLMGateway(config=config)
            assert gateway.kv_cache is None

    def test_initialize_health_check_enabled(self):
        """Test health check initialization when enabled."""
        config = GatewayConfig(enable_health_monitoring=True)
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"):
            gateway = LiteLLMGateway(config=config)
            assert gateway.health_check is not None

    def test_initialize_health_check_disabled(self):
        """Test health check initialization when disabled."""
        config = GatewayConfig(enable_health_monitoring=False)
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"):
            gateway = LiteLLMGateway(config=config)
            assert gateway.health_check is None

    def test_initialize_llmops_enabled(self):
        """Test LLMOps initialization when enabled."""
        config = GatewayConfig(enable_llmops=True)
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"):
            gateway = LiteLLMGateway(config=config)
            assert gateway.llmops is not None

    def test_initialize_llmops_disabled(self):
        """Test LLMOps initialization when disabled."""
        config = GatewayConfig(enable_llmops=False)
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"):
            gateway = LiteLLMGateway(config=config)
            assert gateway.llmops is None

    def test_initialize_validation_manager_enabled(self):
        """Test validation manager initialization when enabled."""
        config = GatewayConfig(enable_validation=True)
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"):
            gateway = LiteLLMGateway(config=config)
            assert gateway.validation_manager is not None

    def test_initialize_validation_manager_disabled(self):
        """Test validation manager initialization when disabled."""
        config = GatewayConfig(enable_validation=False)
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"):
            gateway = LiteLLMGateway(config=config)
            assert gateway.validation_manager is None

    def test_initialize_feedback_loop_enabled(self):
        """Test feedback loop initialization when enabled."""
        config = GatewayConfig(enable_feedback_loop=True)
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"):
            gateway = LiteLLMGateway(config=config)
            assert gateway.feedback_loop is not None

    def test_initialize_feedback_loop_disabled(self):
        """Test feedback loop initialization when disabled."""
        config = GatewayConfig(enable_feedback_loop=False)
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"):
            gateway = LiteLLMGateway(config=config)
            assert gateway.feedback_loop is None

    def test_initialize_cache_enabled(self):
        """Test cache initialization when enabled."""
        from src.core.cache_mechanism import CacheConfig, CacheMechanism
        cache = CacheMechanism(CacheConfig())
        config = GatewayConfig(enable_caching=True, cache=cache)
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"):
            gateway = LiteLLMGateway(config=config)
            assert gateway.cache == cache

    def test_initialize_cache_with_config(self):
        """Test cache initialization with cache_config."""
        from src.core.cache_mechanism import CacheConfig
        cache_config = CacheConfig(default_ttl=600)
        config = GatewayConfig(enable_caching=True, cache_config=cache_config)
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"):
            gateway = LiteLLMGateway(config=config)
            assert gateway.cache is not None

    def test_initialize_cache_disabled(self):
        """Test cache initialization when disabled."""
        config = GatewayConfig(enable_caching=False)
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"):
            gateway = LiteLLMGateway(config=config)
            assert gateway.cache is None

    def test_classify_error_rate_limit(self, mock_gateway):
        """Test error classification for rate limit errors."""
        gateway = mock_gateway
        error = Exception("Rate limit exceeded")
        classification = gateway._classify_error(error)
        assert classification["rate_limit_error"] is True
        assert classification["retryable"] is True
        assert classification["category"] == "rate_limit"

    def test_classify_error_timeout(self, mock_gateway):
        """Test error classification for timeout errors."""
        gateway = mock_gateway
        error = Exception("Request timed out")
        classification = gateway._classify_error(error)
        assert classification["timeout_error"] is True
        assert classification["retryable"] is True
        assert classification["category"] == "timeout"

    def test_classify_error_authentication(self, mock_gateway):
        """Test error classification for authentication errors."""
        gateway = mock_gateway
        error = Exception("401 Authentication failed")
        classification = gateway._classify_error(error)
        assert classification["authentication_error"] is True
        assert classification["retryable"] is False
        assert classification["category"] == "authentication"

    def test_classify_error_provider(self, mock_gateway):
        """Test error classification for provider errors."""
        gateway = mock_gateway
        
        class APIError(Exception):
            pass
        
        error = APIError("Provider error")
        classification = gateway._classify_error(error)
        assert classification["provider_error"] is True
        assert classification["retryable"] is True
        assert classification["category"] == "provider"

    def test_classify_error_unknown(self, mock_gateway):
        """Test error classification for unknown errors."""
        gateway = mock_gateway
        error = ValueError("Some other error")
        classification = gateway._classify_error(error)
        assert classification["category"] == "unknown"
        assert classification["retryable"] is False

    def test_get_rate_limiter_new_tenant(self, mock_gateway):
        """Test getting rate limiter for new tenant."""
        gateway = mock_gateway
        limiter = gateway._get_rate_limiter("tenant1")
        assert limiter is not None
        assert "tenant1" in gateway.rate_limiters

    def test_get_rate_limiter_existing_tenant(self, mock_gateway):
        """Test getting rate limiter for existing tenant."""
        gateway = mock_gateway
        limiter1 = gateway._get_rate_limiter("tenant1")
        limiter2 = gateway._get_rate_limiter("tenant1")
        assert limiter1 == limiter2  # Should return same instance

    @pytest.mark.asyncio
    async def test_embed_async(self, mock_gateway):
        """Test async embedding generation."""
        gateway = mock_gateway

        mock_response = MagicMock(spec=['data', 'model'])
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
        mock_response.model = "text-embedding-3-small"
        
        with patch("src.core.litellm_gateway.gateway.aembedding", new_callable=AsyncMock) as mock_aembedding:
            mock_aembedding.return_value = mock_response
            response = await gateway.embed_async(texts=["Hello", "World"], model="text-embedding-3-small")

            assert len(response.embeddings) == 1
            assert len(response.embeddings[0]) == 1536
            mock_aembedding.assert_called_once()

    @pytest.mark.asyncio
    async def test_embed_async_with_router(self, mock_gateway):
        """Test async embedding generation with router."""
        gateway = mock_gateway
        mock_router = MagicMock()
        mock_router.aembedding = AsyncMock(return_value={"data": [{"embedding": [0.1] * 1536}], "model": "text-embedding-3-small"})
        gateway.router = mock_router

        response = await gateway.embed_async(texts=["Hello"], model="text-embedding-3-small")
        assert len(response.embeddings) == 1
        mock_router.aembedding.assert_called_once()

    def test_embed_with_router(self, mock_gateway):
        """Test embedding generation with router."""
        gateway = mock_gateway
        mock_router = MagicMock()
        mock_router.embedding = MagicMock(return_value={"data": [{"embedding": [0.1] * 1536}], "model": "text-embedding-3-small"})
        gateway.router = mock_router

        response = gateway.embed(texts=["Hello"], model="text-embedding-3-small")
        assert len(response.embeddings) == 1
        mock_router.embedding.assert_called_once()

    def test_extract_embeddings_from_dict(self, mock_gateway):
        """Test extracting embeddings from dict response."""
        gateway = mock_gateway
        response = {
            "data": [{"embedding": [0.1, 0.2, 0.3]}],
            "model": "text-embedding-3-small",
            "usage": {"total_tokens": 10}
        }
        embeddings, model, usage = gateway._extract_embeddings_from_dict(response, "default_model")
        assert len(embeddings) == 1
        assert embeddings[0] == [0.1, 0.2, 0.3]
        assert model == "text-embedding-3-small"
        assert usage is not None

    def test_extract_embeddings_from_object(self, mock_gateway):
        """Test extracting embeddings from object response."""
        gateway = mock_gateway
        mock_item = MagicMock()
        mock_item.embedding = [0.1, 0.2, 0.3]
        mock_response = MagicMock()
        mock_response.data = [mock_item]
        mock_response.model = "text-embedding-3-small"
        # Create a simple object with __dict__ attribute
        class UsageObj:
            def __init__(self):
                self.total_tokens = 10
        mock_usage = UsageObj()
        mock_response.usage = mock_usage

        embeddings, model, usage = gateway._extract_embeddings_from_object(mock_response, "default_model")
        assert len(embeddings) == 1
        assert embeddings[0] == [0.1, 0.2, 0.3]
        assert model == "text-embedding-3-small"
        assert usage is not None

    def test_extract_response_data_from_object(self, mock_gateway):
        """Test extracting response data from object."""
        gateway = mock_gateway
        mock_choice = MagicMock()
        mock_choice.message.content = "Response text"
        mock_choice.finish_reason = "stop"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.model = "gpt-4"
        # Create a simple object with __dict__ attribute
        class UsageObj:
            def __init__(self):
                self.prompt_tokens = 10
                self.completion_tokens = 20
        mock_usage = UsageObj()
        mock_response.usage = mock_usage

        text, model, usage, finish_reason, _ = gateway._extract_response_data(mock_response, "gpt-4")
        assert text == "Response text"
        assert model == "gpt-4"
        assert finish_reason == "stop"
        assert usage is not None

    def test_extract_response_data_from_dict(self, mock_gateway):
        """Test extracting response data from dict."""
        gateway = mock_gateway
        response = {
            "choices": [{"message": {"content": "Response text"}, "finish_reason": "stop"}],
            "model": "gpt-4",
            "usage": {"prompt_tokens": 10, "completion_tokens": 20}
        }

        text, model, usage, finish_reason, _ = gateway._extract_response_data(response, "gpt-4")
        assert text == "Response text"
        assert model == "gpt-4"
        assert finish_reason == "stop"
        assert usage is not None

    def test_extract_response_data_fallback(self, mock_gateway):
        """Test extracting response data with fallback to string."""
        gateway = mock_gateway
        response = "Simple string response"

        text, model, usage, finish_reason, _ = gateway._extract_response_data(response, "gpt-4")
        assert text == "Simple string response"
        assert model == "gpt-4"
        assert usage is None
        assert finish_reason is None

    @pytest.mark.asyncio
    async def test_generate_async_error_handling(self, mock_gateway):
        """Test error handling in generate_async with specific exceptions."""
        gateway = mock_gateway
        
        # Test ValueError handling
        with patch("src.core.litellm_gateway.gateway.acompletion", new_callable=AsyncMock) as mock_acompletion:
            mock_acompletion.side_effect = ValueError("Invalid input")
            with pytest.raises(ValueError):
                await gateway.generate_async(prompt="Test", model="gpt-4")

    @pytest.mark.asyncio
    async def test_store_kv_cache_error(self, mock_gateway):
        """Test KV cache storage error handling."""
        gateway = mock_gateway
        mock_kv_cache = MagicMock()
        mock_kv_cache.set_kv_cache = AsyncMock(side_effect=AttributeError("Cache error"))
        gateway.kv_cache = mock_kv_cache

        # Should not raise, just log
        await gateway._store_kv_cache("key", "prompt", "model", "tenant1")

    @pytest.mark.asyncio
    async def test_store_kv_cache_no_cache(self, mock_gateway):
        """Test KV cache storage when cache is None."""
        gateway = mock_gateway
        gateway.kv_cache = None

        # Should not raise
        await gateway._store_kv_cache("key", "prompt", "model", "tenant1")

    @pytest.mark.asyncio
    async def test_get_health(self):
        """Test get_health method."""
        config = GatewayConfig(enable_health_monitoring=True, enable_llmops=True, enable_feedback_loop=True)
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"):
            gateway = LiteLLMGateway(config=config)
            mock_health_check = MagicMock()
            mock_health_check.check = AsyncMock()
            mock_health_check.get_health.return_value = {"status": "healthy"}
            gateway.health_check = mock_health_check
            gateway.circuit_breaker = MagicMock()
            gateway.circuit_breaker.get_stats.return_value = {"state": "closed"}
            gateway.rate_limiters = {}
            gateway.provider_health = {}
            gateway.llmops = MagicMock()
            gateway.llmops.get_metrics.return_value = {"total_requests": 10}
            gateway.feedback_loop = MagicMock()
            gateway.feedback_loop.get_feedback_stats.return_value = {"total": 5}

            health = await gateway.get_health()
            assert "status" in health
            assert "circuit_breaker" in health
            assert "rate_limiters" in health

    def test_get_health_disabled(self, mock_gateway):
        """Test get_health when health monitoring is disabled."""
        gateway = mock_gateway
        gateway.health_check = None
        import asyncio
        health = asyncio.run(gateway.get_health())
        assert health == {"status": "health_monitoring_disabled"}

    @pytest.mark.asyncio
    async def test_setup_health_checks_router_not_configured(self):
        """Test health check setup with router not configured."""
        config = GatewayConfig(enable_health_monitoring=True)
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"):
            gateway = LiteLLMGateway(config=config)
            # Set router to None for testing (router can be None in practice)
            setattr(gateway, 'router', None)
            # Trigger health check setup
            gateway._setup_health_checks()
            # Health check should be set up
            assert gateway.health_check is not None

    @pytest.mark.asyncio
    async def test_setup_health_checks_circuit_breaker_open(self):
        """Test health check setup with circuit breaker open."""
        from src.core.utils.circuit_breaker import CircuitState
        config = GatewayConfig(enable_health_monitoring=True, enable_circuit_breaker=True)
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"):
            gateway = LiteLLMGateway(config=config)
            # Health check is already set up in __init__, just verify it works
            assert gateway.health_check is not None
            # Verify circuit breaker is set
            assert gateway.circuit_breaker is not None
            # Mock get_stats to return OPEN state
            gateway.circuit_breaker.get_stats = MagicMock(return_value={"state": CircuitState.OPEN.value})
            # Health check should still be functional
            assert gateway.health_check is not None

    def test_setup_health_checks_provider_health(self):
        """Test health check setup with provider health data."""
        config = GatewayConfig(enable_health_monitoring=True)
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"):
            gateway = LiteLLMGateway(config=config)
            gateway.provider_health = {
                "gpt-4": {"status": "healthy"},
                "claude-3": {"status": "unhealthy"}
            }
            gateway._setup_health_checks()
            assert gateway.health_check is not None

    def test_setup_health_checks_no_provider_health(self):
        """Test health check setup with no provider health data."""
        config = GatewayConfig(enable_health_monitoring=True)
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"):
            gateway = LiteLLMGateway(config=config)
            gateway.provider_health = {}
            gateway._setup_health_checks()
            assert gateway.health_check is not None

    @pytest.mark.asyncio
    async def test_record_feedback(self, mock_gateway):
        """Test record_feedback method."""
        gateway = mock_gateway
        from src.core.feedback_loop import FeedbackType
        mock_feedback_loop = MagicMock()
        mock_feedback_loop.record_feedback = AsyncMock(return_value="feedback_id_123")
        gateway.feedback_loop = mock_feedback_loop

        # Use a valid FeedbackType value (RATING is one of the valid types)
        result = await gateway.record_feedback(
            query="test query",
            response="test response",
            feedback_type=FeedbackType.RATING,
            content="test content",
            tenant_id="tenant1"
        )
        assert result == "feedback_id_123"
        mock_feedback_loop.record_feedback.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_feedback_disabled(self, mock_gateway):
        """Test record_feedback when feedback loop is disabled."""
        gateway = mock_gateway
        gateway.feedback_loop = None

        result = await gateway.record_feedback(
            query="test query",
            response="test response",
            feedback_type=None,
            content=None
        )
        assert result is None

    def test_get_llmops_metrics(self, mock_gateway):
        """Test get_llmops_metrics method."""
        gateway = mock_gateway
        mock_llmops = MagicMock()
        mock_llmops.get_metrics.return_value = {"total_requests": 100}
        gateway.llmops = mock_llmops

        metrics = gateway.get_llmops_metrics(tenant_id="tenant1", time_range_hours=24)
        assert metrics["total_requests"] == 100
        mock_llmops.get_metrics.assert_called_once_with(tenant_id="tenant1", time_range_hours=24)

    def test_get_llmops_metrics_disabled(self, mock_gateway):
        """Test get_llmops_metrics when LLMOps is disabled."""
        gateway = mock_gateway
        gateway.llmops = None

        metrics = gateway.get_llmops_metrics()
        assert metrics == {"error": "LLMOps not enabled"}

    def test_get_cost_summary(self, mock_gateway):
        """Test get_cost_summary method."""
        gateway = mock_gateway
        mock_llmops = MagicMock()
        mock_llmops.get_cost_summary.return_value = {"total_cost": 10.50}
        gateway.llmops = mock_llmops

        cost = gateway.get_cost_summary(tenant_id="tenant1", time_range_hours=48)
        assert abs(cost["total_cost"] - 10.50) < 0.01  # Use approximate comparison for float
        mock_llmops.get_cost_summary.assert_called_once_with(tenant_id="tenant1", time_range_hours=48)

    def test_get_cost_summary_disabled(self, mock_gateway):
        """Test get_cost_summary when LLMOps is disabled."""
        gateway = mock_gateway
        gateway.llmops = None

        cost = gateway.get_cost_summary()
        assert cost == {"error": "LLMOps not enabled"}

    @pytest.mark.asyncio
    async def test_check_kv_cache_hit(self, mock_gateway):
        """Test _check_kv_cache with cache hit."""
        gateway = mock_gateway
        mock_kv_cache = MagicMock()
        mock_kv_cache.get_kv_cache = AsyncMock(return_value={"keys": [], "values": []})
        gateway.kv_cache = mock_kv_cache

        result = await gateway._check_kv_cache("prompt", "model", [{"role": "user", "content": "test"}], "tenant1")
        assert result is not None
        mock_kv_cache.get_kv_cache.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_kv_cache_miss(self, mock_gateway):
        """Test _check_kv_cache with cache miss."""
        gateway = mock_gateway
        mock_kv_cache = MagicMock()
        mock_kv_cache.get_kv_cache = AsyncMock(return_value=None)
        gateway.kv_cache = mock_kv_cache

        result = await gateway._check_kv_cache("prompt", "model", [{"role": "user", "content": "test"}], "tenant1")
        assert result is not None  # Returns key even on miss

    @pytest.mark.asyncio
    async def test_check_response_cache_hit(self, mock_gateway):
        """Test _check_response_cache with cache hit."""
        gateway = mock_gateway
        from src.core.cache_mechanism import CacheConfig, CacheMechanism
        cache = CacheMechanism(CacheConfig())
        gateway.cache = cache
        gateway.config.enable_caching = True
        
        # Store a cached response using the same key generation logic
        messages = [{"role": "user", "content": "test"}]
        cache_key = gateway._generate_cache_key("test prompt", "gpt-4", messages, "tenant1")
        cached_data = {
            "text": "Cached response",
            "model": "gpt-4",
            "usage": {"prompt_tokens": 10},
            "finish_reason": "stop"
        }
        await cache.set(cache_key, cached_data, ttl=3600, tenant_id="tenant1")

        result = await gateway._check_response_cache(
            "test prompt", "gpt-4", messages, "tenant1", False
        )
        assert result is not None
        assert result.text == "Cached response"

    @pytest.mark.asyncio
    async def test_check_response_cache_miss(self, mock_gateway):
        """Test _check_response_cache with cache miss."""
        gateway = mock_gateway
        from src.core.cache_mechanism import CacheConfig, CacheMechanism
        cache = CacheMechanism(CacheConfig())
        gateway.cache = cache

        result = await gateway._check_response_cache(
            "different prompt", "gpt-4", [{"role": "user", "content": "different"}], "tenant1", False
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_check_response_cache_disabled(self, mock_gateway):
        """Test _check_response_cache when cache is disabled."""
        gateway = mock_gateway
        gateway.cache = None

        result = await gateway._check_response_cache(
            "test prompt", "gpt-4", [{"role": "user", "content": "test"}], "tenant1", False
        )
        assert result is None

    def test_extract_token_usage(self, mock_gateway):
        """Test _extract_token_usage method."""
        gateway = mock_gateway
        mock_response = MagicMock()
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 20
        mock_response.usage = mock_usage

        prompt_tokens = [0]
        completion_tokens = [0]
        gateway._extract_token_usage(mock_response, prompt_tokens, completion_tokens)
        assert prompt_tokens[0] == 10
        assert completion_tokens[0] == 20

    def test_extract_token_usage_no_usage(self, mock_gateway):
        """Test _extract_token_usage with no usage attribute."""
        gateway = mock_gateway
        mock_response = MagicMock()
        mock_response.usage = None

        prompt_tokens = [0]
        completion_tokens = [0]
        gateway._extract_token_usage(mock_response, prompt_tokens, completion_tokens)
        assert prompt_tokens[0] == 0
        assert completion_tokens[0] == 0

    def test_update_provider_health_success(self, mock_gateway):
        """Test _update_provider_health_success method."""
        gateway = mock_gateway
        gateway.provider_health = {}

        gateway._update_provider_health_success("gpt-4")
        # Provider name is extracted from model (uses "default" if no "/" in model)
        assert "default" in gateway.provider_health
        assert gateway.provider_health["default"]["status"] == "healthy"

    def test_determine_error_status_rate_limit(self, mock_gateway):
        """Test _determine_error_status for rate limit errors."""
        gateway = mock_gateway
        from src.core.llmops import LLMOperationStatus
        status = gateway._determine_error_status("Rate limit exceeded")
        assert status == LLMOperationStatus.RATE_LIMITED

    def test_determine_error_status_timeout(self, mock_gateway):
        """Test _determine_error_status for timeout errors."""
        gateway = mock_gateway
        from src.core.llmops import LLMOperationStatus
        status = gateway._determine_error_status("Request timeout")
        assert status == LLMOperationStatus.TIMEOUT

    def test_determine_error_status_generic(self, mock_gateway):
        """Test _determine_error_status for generic errors."""
        gateway = mock_gateway
        from src.core.llmops import LLMOperationStatus
        status = gateway._determine_error_status("Some other error")
        assert status == LLMOperationStatus.ERROR

    @pytest.mark.asyncio
    async def test_generate_async_with_circuit_breaker(self):
        """Test generate_async with circuit breaker enabled."""
        config = GatewayConfig(enable_circuit_breaker=True)
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"), \
             patch("src.core.litellm_gateway.gateway.acompletion", new_callable=AsyncMock) as mock_acompletion:
            gateway = LiteLLMGateway(config=config)
            setattr(gateway, 'kv_cache', None)
            setattr(gateway, 'router', None)
            setattr(gateway, 'cache', None)
            setattr(gateway, 'deduplicator', None)
            setattr(gateway, 'llmops', None)

            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_choice.message.content = "Response"
            mock_choice.finish_reason = "stop"
            mock_response.choices = [mock_choice]
            mock_response.model = "gpt-4"
            mock_acompletion.return_value = mock_response

            gateway.circuit_breaker.call = AsyncMock(return_value=mock_response)
            response = await gateway.generate_async(prompt="Test", model="gpt-4")
            assert response.text == "Response"

    @pytest.mark.asyncio
    async def test_generate_async_streaming(self, mock_gateway):
        """Test generate_async with streaming enabled."""
        gateway = mock_gateway
        gateway.cache = None
        gateway.kv_cache = None
        gateway.llmops = None

        async def mock_stream():
            yield MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello"))])
            yield MagicMock(choices=[MagicMock(delta=MagicMock(content=" World"))])

        with patch("src.core.litellm_gateway.gateway.acompletion", new_callable=AsyncMock) as mock_acompletion:
            mock_acompletion.return_value = mock_stream()
            response = await gateway.generate_async(prompt="Test", model="gpt-4", stream=True)
            # Should return the stream generator
            assert response is not None
            chunks = []
            async for chunk in response:
                chunks.append(chunk)
            assert len(chunks) > 0

    def test_extract_embeddings_from_object_no_data(self, mock_gateway):
        """Test _extract_embeddings_from_object with no data attribute."""
        gateway = mock_gateway
        mock_response = MagicMock()
        mock_response.data = None

        embeddings, model, usage = gateway._extract_embeddings_from_object(mock_response, "default_model")
        assert embeddings == []
        assert model == "default_model"
        assert usage is None

    def test_extract_embeddings_from_object_empty_data(self, mock_gateway):
        """Test _extract_embeddings_from_object with empty data."""
        gateway = mock_gateway
        mock_response = MagicMock()
        mock_response.data = []

        embeddings, model, usage = gateway._extract_embeddings_from_object(mock_response, "default_model")
        assert embeddings == []
        assert model == "default_model"
        assert usage is None

    def test_setup_health_checks_disabled(self, gateway_config):
        """Test _setup_health_checks when health monitoring is disabled."""
        config = GatewayConfig(enable_health_monitoring=False)
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"):
            gateway = LiteLLMGateway(config=config)
            # Health check should not be set up
            assert gateway.health_check is None
            # Calling _setup_health_checks should return early
            gateway._setup_health_checks()
            assert gateway.health_check is None

    def test_get_rate_limiter_disabled(self, gateway_config):
        """Test _get_rate_limiter when rate limiting is disabled."""
        config = GatewayConfig(enable_rate_limiting=False)
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"):
            gateway = LiteLLMGateway(config=config)
            limiter = gateway._get_rate_limiter("tenant-1")
            assert limiter is None

    @pytest.mark.asyncio
    async def test_generate_with_router(self, gateway_config):
        """Test generate with router enabled."""
        config = GatewayConfig()
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"):
            gateway = LiteLLMGateway(config=config)
            mock_router = MagicMock()
            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_choice.message.content = "Test"
            mock_choice.finish_reason = "stop"
            mock_response.choices = [mock_choice]
            mock_response.model = "gpt-4"  # String, not MagicMock
            # generate uses _execute_sync_generation which calls router.completion
            mock_router.completion = MagicMock(return_value=mock_response)
            gateway.router = mock_router
            gateway.cache = None
            gateway.kv_cache = None
            gateway.llmops = None
            gateway.deduplicator = None
            gateway.batcher = None
            gateway.circuit_breaker = None

            response = await gateway.generate(
                prompt="test",
                model="gpt-4",
                messages=[{"role": "user", "content": "test"}],
                stream=False
            )

            assert response is not None
            assert response.text == "Test"
            mock_router.completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_kv_cache_success(self, mock_gateway):
        """Test _store_kv_cache with successful storage."""
        gateway = mock_gateway
        mock_kv_cache = MagicMock()
        mock_kv_cache.set_kv_cache = AsyncMock(return_value=True)
        gateway.kv_cache = mock_kv_cache

        await gateway._store_kv_cache("cache-key", "prompt", "model", "tenant1")

        mock_kv_cache.set_kv_cache.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_kv_cache_attribute_error(self, mock_gateway):
        """Test _store_kv_cache handles AttributeError."""
        gateway = mock_gateway
        mock_kv_cache = MagicMock()
        mock_kv_cache.set_kv_cache = AsyncMock(side_effect=AttributeError("Cache error"))
        gateway.kv_cache = mock_kv_cache

        # Should not raise, just log
        await gateway._store_kv_cache("cache-key", "prompt", "model", "tenant1")

    @pytest.mark.asyncio
    async def test_store_kv_cache_value_error(self, mock_gateway):
        """Test _store_kv_cache handles ValueError."""
        gateway = mock_gateway
        mock_kv_cache = MagicMock()
        mock_kv_cache.set_kv_cache = AsyncMock(side_effect=ValueError("Invalid value"))
        gateway.kv_cache = mock_kv_cache

        # Should not raise, just log
        await gateway._store_kv_cache("cache-key", "prompt", "model", "tenant1")

    @pytest.mark.asyncio
    async def test_store_kv_cache_type_error(self, mock_gateway):
        """Test _store_kv_cache handles TypeError."""
        gateway = mock_gateway
        mock_kv_cache = MagicMock()
        mock_kv_cache.set_kv_cache = AsyncMock(side_effect=TypeError("Type error"))
        gateway.kv_cache = mock_kv_cache

        # Should not raise, just log
        await gateway._store_kv_cache("cache-key", "prompt", "model", "tenant1")

    @pytest.mark.asyncio
    async def test_store_kv_cache_generic_exception(self, mock_gateway):
        """Test _store_kv_cache handles generic Exception."""
        gateway = mock_gateway
        mock_kv_cache = MagicMock()
        mock_kv_cache.set_kv_cache = AsyncMock(side_effect=RuntimeError("Unexpected error"))
        gateway.kv_cache = mock_kv_cache

        # Should not raise, just log
        await gateway._store_kv_cache("cache-key", "prompt", "model", "tenant1")

    @pytest.mark.asyncio
    async def test_check_kv_cache_returns_key(self, mock_gateway):
        """Test _check_kv_cache returns cache key when cache is available."""
        gateway = mock_gateway
        mock_kv_cache = MagicMock()
        mock_entry = MagicMock()
        mock_entry.keys = [[[0.1, 0.2]]]
        mock_entry.values = [[[0.3, 0.4]]]
        mock_kv_cache.get_kv_cache = AsyncMock(return_value=mock_entry)
        mock_kv_cache.generate_cache_key = MagicMock(return_value="cache-key-123")
        gateway.kv_cache = mock_kv_cache

        result = await gateway._check_kv_cache("prompt", "model", [{"role": "user", "content": "test"}], "tenant1")

        assert result == "cache-key-123"
        mock_kv_cache.generate_cache_key.assert_called_once()
        mock_kv_cache.get_kv_cache.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_generation_with_router(self, gateway_config):
        """Test _execute_generation with router enabled."""
        config = GatewayConfig()
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"):
            gateway = LiteLLMGateway(config=config)
            mock_router = MagicMock()
            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_choice.message.content = "Test"
            mock_response.choices = [mock_choice]
            mock_router.acompletion = AsyncMock(return_value=mock_response)
            gateway.router = mock_router
            gateway.llmops = None

            prompt_tokens: List[int] = [0]
            completion_tokens: List[int] = [0]
            error_message: List[Optional[str]] = [None]
            status: List[LLMOperationStatus] = [LLMOperationStatus.SUCCESS]

            response = await gateway._execute_generation(
                model="gpt-4",
                messages=[{"role": "user", "content": "test"}],
                stream=False,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                error_message=error_message,
                status=status
            )

            assert response is not None
            mock_router.acompletion.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_generation_validation_error(self, gateway_config):
        """Test _execute_generation handles ValueError."""
        config = GatewayConfig()
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"), \
             patch("src.core.litellm_gateway.gateway.acompletion", new_callable=AsyncMock) as mock_acompletion:
            gateway = LiteLLMGateway(config=config)
            setattr(gateway, 'router', None)  
            gateway.llmops = None
            mock_acompletion.side_effect = ValueError("Validation error")

            prompt_tokens: List[int] = [0]
            completion_tokens: List[int] = [0]
            error_message: List[Optional[str]] = [None]
            status: List[LLMOperationStatus] = [LLMOperationStatus.SUCCESS]

            with pytest.raises(ValueError):
                await gateway._execute_generation(
                    model="gpt-4",
                    messages=[{"role": "user", "content": "test"}],
                    stream=False,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    error_message=error_message,
                    status=status
                )

            assert error_message[0] is not None
            assert status[0] is not None

    @pytest.mark.asyncio
    async def test_execute_generation_type_error(self, gateway_config):
        """Test _execute_generation handles TypeError."""
        config = GatewayConfig()
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"), \
             patch("src.core.litellm_gateway.gateway.acompletion", new_callable=AsyncMock) as mock_acompletion:
            gateway = LiteLLMGateway(config=config)
            setattr(gateway, 'router', None)  
            gateway.llmops = None
            mock_acompletion.side_effect = TypeError("Type error")

            prompt_tokens: List[int] = [0]
            completion_tokens: List[int] = [0]
            error_message: List[Optional[str]] = [None]
            status: List[LLMOperationStatus] = [LLMOperationStatus.SUCCESS]

            with pytest.raises(TypeError):
                await gateway._execute_generation(
                    model="gpt-4",
                    messages=[{"role": "user", "content": "test"}],
                    stream=False,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    error_message=error_message,
                    status=status
                )

    @pytest.mark.asyncio
    async def test_execute_generation_key_error(self, gateway_config):
        """Test _execute_generation handles KeyError."""
        config = GatewayConfig()
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"), \
             patch("src.core.litellm_gateway.gateway.acompletion", new_callable=AsyncMock) as mock_acompletion:
            gateway = LiteLLMGateway(config=config)
            setattr(gateway, 'router', None)  # typ
            gateway.llmops = None
            mock_acompletion.side_effect = KeyError("Key error")

            prompt_tokens: List[int] = [0]
            completion_tokens: List[int] = [0]
            error_message: List[Optional[str]] = [None]
            status: List[LLMOperationStatus] = [LLMOperationStatus.SUCCESS]

            with pytest.raises(KeyError):
                await gateway._execute_generation(
                    model="gpt-4",
                    messages=[{"role": "user", "content": "test"}],
                    stream=False,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    error_message=error_message,
                    status=status
                )

    @pytest.mark.asyncio
    async def test_execute_generation_attribute_error(self, gateway_config):
        """Test _execute_generation handles AttributeError."""
        config = GatewayConfig()
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"), \
             patch("src.core.litellm_gateway.gateway.acompletion", new_callable=AsyncMock) as mock_acompletion:
            gateway = LiteLLMGateway(config=config)
            setattr(gateway, 'router', None)
            gateway.llmops = None
            mock_acompletion.side_effect = AttributeError("Attribute error")

            prompt_tokens: List[int] = [0]
            completion_tokens: List[int] = [0]
            error_message: List[Optional[str]] = [None]
            status: List[LLMOperationStatus] = [LLMOperationStatus.SUCCESS]

            with pytest.raises(AttributeError):
                await gateway._execute_generation(
                    model="gpt-4",
                    messages=[{"role": "user", "content": "test"}],
                    stream=False,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    error_message=error_message,
                    status=status
                )

    @pytest.mark.asyncio
    async def test_execute_generation_generic_exception(self, gateway_config):
        """Test _execute_generation handles generic Exception."""
        config = GatewayConfig()
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"), \
             patch("src.core.litellm_gateway.gateway.acompletion", new_callable=AsyncMock) as mock_acompletion:
            gateway = LiteLLMGateway(config=config)
            setattr(gateway, 'router', None)
            gateway.llmops = None
            mock_acompletion.side_effect = RuntimeError("Runtime error")

            prompt_tokens: List[int] = [0]
            completion_tokens: List[int] = [0]
            error_message: List[Optional[str]] = [None]
            status: List[LLMOperationStatus] = [LLMOperationStatus.SUCCESS]

            with pytest.raises(RuntimeError):
                await gateway._execute_generation(
                    model="gpt-4",
                    messages=[{"role": "user", "content": "test"}],
                    stream=False,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    error_message=error_message,
                    status=status
                )

    @pytest.mark.asyncio
    async def test_generate_async_with_deduplicator(self, gateway_config):
        """Test generate_async with deduplicator enabled."""
        config = GatewayConfig(enable_request_deduplication=True)
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"):
            gateway = LiteLLMGateway(config=config)
            # Mock deduplicator to avoid kwargs issue
            mock_deduplicator = MagicMock()
            mock_deduplicator.get_or_execute = AsyncMock()
            gateway.deduplicator = mock_deduplicator
            gateway.circuit_breaker = None
            gateway.batcher = None
            gateway.llmops = None
            gateway.kv_cache = None
            gateway.cache = None

            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_choice.message.content = "Response"
            mock_choice.finish_reason = "stop"
            mock_response.choices = [mock_choice]
            mock_response.model = "gpt-4"

            # Mock the response that deduplicator returns
            mock_deduplicator.get_or_execute.return_value = mock_response

            with patch("src.core.litellm_gateway.gateway.acompletion", new_callable=AsyncMock) as mock_acompletion:
                mock_acompletion.return_value = mock_response
                response = await gateway.generate_async(prompt="Test", model="gpt-4", stream=False)
                assert response.text == "Response"
                # Verify deduplicator was called
                mock_deduplicator.get_or_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_async_with_batcher(self, gateway_config):
        """Test generate_async with batcher enabled."""
        config = GatewayConfig(enable_request_batching=True)
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"):
            gateway = LiteLLMGateway(config=config)
            # Mock batcher to avoid kwargs issue
            mock_batcher = MagicMock()
            mock_batcher.batch_execute = AsyncMock()
            gateway.batcher = mock_batcher
            gateway.deduplicator = None
            gateway.circuit_breaker = None
            gateway.llmops = None
            gateway.kv_cache = None
            gateway.cache = None

            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_choice.message.content = "Response"
            mock_choice.finish_reason = "stop"
            mock_response.choices = [mock_choice]
            mock_response.model = "gpt-4"

            # Mock the response that batcher returns
            mock_batcher.batch_execute.return_value = mock_response

            with patch("src.core.litellm_gateway.gateway.acompletion", new_callable=AsyncMock) as mock_acompletion:
                mock_acompletion.return_value = mock_response
                response = await gateway.generate_async(prompt="Test", model="gpt-4", stream=False, tenant_id="tenant-1")
                assert response.text == "Response"
                # Verify batcher was called
                mock_batcher.batch_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_async_direct_call(self, gateway_config):
        """Test generate_async with direct call (no deduplicator, batcher, or circuit breaker)."""
        config = GatewayConfig()
        with patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_kv_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_cache"), \
             patch("src.core.litellm_gateway.gateway.LiteLLMGateway._initialize_router"):
            gateway = LiteLLMGateway(config=config)
            gateway.deduplicator = None
            gateway.batcher = None
            gateway.circuit_breaker = None
            setattr(gateway, 'router', None)  # Explicitly set router to None
            gateway.llmops = None
            gateway.kv_cache = None
            gateway.cache = None

            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_choice.message.content = "Response"
            mock_choice.finish_reason = "stop"
            mock_response.choices = [mock_choice]
            mock_response.model = "gpt-4"

            with patch("src.core.litellm_gateway.gateway.acompletion", new_callable=AsyncMock) as mock_acompletion:
                mock_acompletion.return_value = mock_response
                response = await gateway.generate_async(prompt="Test", model="gpt-4", stream=False)
                assert response.text == "Response"

    @pytest.mark.asyncio
    async def test_embed_async_empty_response(self, mock_gateway):
        """Test embed_async with empty response (no data attribute, not a dict)."""
        gateway = mock_gateway
        setattr(gateway, 'router', None)
        gateway.llmops = None

        # Create a mock response that doesn't have data attribute and isn't a dict
        # This triggers the else branch in embed_async
        class EmptyResponse:
            pass
        
        mock_response = EmptyResponse()

        # Patch aembedding from gateway module (it's imported as aembedding)
        with patch("src.core.litellm_gateway.gateway.aembedding", new_callable=AsyncMock) as mock_aembedding:
            mock_aembedding.return_value = mock_response
            response = await gateway.embed_async(texts=["test"], model="text-embedding-ada-002")

            assert response.embeddings == []
            assert response.model == "text-embedding-ada-002"
            assert response.usage is None
            mock_aembedding.assert_called_once()

    def test_classify_error_retryable_patterns(self, mock_gateway):
        """Test _classify_error with retryable patterns."""
        gateway = mock_gateway
        error = Exception("Connection error occurred")
        classification = gateway._classify_error(error)
        assert classification["retryable"] is True
        assert classification["category"] == "network"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
