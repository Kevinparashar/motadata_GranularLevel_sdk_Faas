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
            gateway = LiteLLMGateway(config=config)
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
            gateway = LiteLLMGateway(config=config)
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

        text, model, usage, finish_reason, raw = gateway._extract_response_data(mock_response, "gpt-4")
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

        text, model, usage, finish_reason, raw = gateway._extract_response_data(response, "gpt-4")
        assert text == "Response text"
        assert model == "gpt-4"
        assert finish_reason == "stop"
        assert usage is not None

    def test_extract_response_data_fallback(self, mock_gateway):
        """Test extracting response data with fallback to string."""
        gateway = mock_gateway
        response = "Simple string response"

        text, model, usage, finish_reason, raw = gateway._extract_response_data(response, "gpt-4")
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
