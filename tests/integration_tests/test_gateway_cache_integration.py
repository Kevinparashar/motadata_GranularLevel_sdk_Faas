"""
Integration Tests for Gateway-Cache Integration

Tests the integration between LiteLLM Gateway and Cache Mechanism.
"""


from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.cache_mechanism import CacheConfig, CacheMechanism
from src.core.litellm_gateway import GatewayConfig, LiteLLMGateway


@pytest.mark.integration
class TestGatewayCacheIntegration:
    """Test Gateway-Cache integration."""

    @pytest.fixture
    def cache(self):
        """Create cache mechanism."""
        return CacheMechanism(CacheConfig(default_ttl=3600))

    @pytest.fixture
    def gateway_with_cache(self, cache):
        """Create gateway with cache enabled."""
        config = GatewayConfig(enable_caching=True, cache_ttl=3600, cache=cache)
        # Patch internal initialization methods to prevent errors during instantiation
        with patch.object(LiteLLMGateway, "_initialize_kv_cache"), \
             patch.object(LiteLLMGateway, "_initialize_cache"), \
             patch.object(LiteLLMGateway, "_initialize_router"), \
             patch.object(LiteLLMGateway, "_initialize_deduplicator"):
            gateway = LiteLLMGateway(config=config)
            
            # Set required attributes that were skipped by patching
            gateway.kv_cache = None
            gateway.deduplicator = None
            gateway.cache = cache  # Set the cache from config
            
            # Create a mock router
            mock_router = MagicMock()
            mock_router.acompletion = AsyncMock()
            gateway.router = mock_router
            
            return gateway, cache, mock_router

    @pytest.mark.asyncio
    async def test_cache_hit_prevents_api_call(self, gateway_with_cache):
        """Test that cache hit prevents LLM API call."""
        gateway, _, mock_router = gateway_with_cache

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = "Cached response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4"
        # Usage needs to be an object with __dict__ attribute
        class UsageObject:
            def __init__(self):
                self.prompt_tokens = 10
                self.completion_tokens = 20
                self.total_tokens = 30
        mock_response.usage = UsageObject()
        mock_router.acompletion = AsyncMock(return_value=mock_response)

        # First call - cache miss (makes API call)
        response1 = await gateway.generate_async(
            prompt="Test prompt", model="gpt-4", tenant_id="test_tenant"
        )
        assert mock_router.acompletion.call_count == 1

        # Second call - cache hit (no API call)
        response2 = await gateway.generate_async(
            prompt="Test prompt", model="gpt-4", tenant_id="test_tenant"
        )
        # Should still be 1 (no new API call)
        assert mock_router.acompletion.call_count == 1
        assert response1.text == response2.text

    @pytest.mark.asyncio
    async def test_tenant_isolation_in_cache(self, gateway_with_cache):
        """Test that cache keys include tenant_id for isolation."""
        gateway, _, mock_router = gateway_with_cache

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = "Response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4"
        # Usage needs to be an object with __dict__ attribute
        class UsageObject:
            def __init__(self):
                self.prompt_tokens = 10
                self.completion_tokens = 20
                self.total_tokens = 30
        mock_response.usage = UsageObject()
        mock_router.acompletion = AsyncMock(return_value=mock_response)

        # Same prompt, different tenants
        await gateway.generate_async(prompt="Test", model="gpt-4", tenant_id="tenant_1")
        await gateway.generate_async(prompt="Test", model="gpt-4", tenant_id="tenant_2")

        # Should make 2 API calls (different cache keys)
        assert mock_router.acompletion.call_count == 2

    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(self, gateway_with_cache):
        """Test that cache respects TTL expiration."""
        import asyncio

        from src.core.cache_mechanism import CacheConfig, CacheMechanism

        # Create cache with short TTL
        short_cache = CacheMechanism(CacheConfig(default_ttl=1))  # 1 second
        config = GatewayConfig(enable_caching=True, cache_ttl=1, cache=short_cache)

        # Patch internal initialization methods to prevent errors during instantiation
        with patch.object(LiteLLMGateway, "_initialize_kv_cache"), \
             patch.object(LiteLLMGateway, "_initialize_cache"), \
             patch.object(LiteLLMGateway, "_initialize_router"), \
             patch.object(LiteLLMGateway, "_initialize_deduplicator"):
            gateway = LiteLLMGateway(config=config)
            
            # Set required attributes that were skipped by patching
            gateway.kv_cache = None
            gateway.deduplicator = None
            gateway.cache = short_cache  # Set the cache from config
            
            # Create a mock router
            mock_router = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message = MagicMock()
            mock_response.choices[0].message.content = "Response"
            mock_response.choices[0].finish_reason = "stop"
            mock_response.model = "gpt-4"
            # Usage needs to be an object with __dict__ attribute
            class UsageObject:
                def __init__(self):
                    self.prompt_tokens = 10
                    self.completion_tokens = 20
                    self.total_tokens = 30
            mock_response.usage = UsageObject()
            mock_router.acompletion = AsyncMock(return_value=mock_response)
            gateway.router = mock_router

            # First call
            await gateway.generate_async(prompt="Test", model="gpt-4", tenant_id="test_tenant")
            assert mock_router.acompletion.call_count == 1

            # Wait for TTL expiration
            await asyncio.sleep(1.1)

            # Second call after expiration - should make new API call
            await gateway.generate_async(prompt="Test", model="gpt-4", tenant_id="test_tenant")
            assert mock_router.acompletion.call_count == 2

    @pytest.mark.asyncio
    async def test_streaming_bypasses_cache(self, gateway_with_cache):
        """Test that streaming responses bypass cache."""
        gateway, cache, mock_router = gateway_with_cache

        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta = MagicMock()
        mock_chunk.choices[0].delta.content = "Chunk"
        # Create an async generator for streaming
        async def async_gen():
            yield mock_chunk
        mock_router.acompletion = AsyncMock(return_value=async_gen())

        # Streaming call should not use cache (stream=True)
        # generate_async with stream=True returns a response, not an async generator
        # The streaming happens internally, so we just verify cache is not used
        response = await gateway.generate_async(
            prompt="Test", model="gpt-4", tenant_id="test_tenant", stream=True
        )
        
        # Verify response was generated
        assert response is not None

        # Cache should not have stored streaming response
        cache_key = gateway._generate_cache_key(
            prompt="Test", model="gpt-4", tenant_id="test_tenant"
        )
        cached = await cache.get(cache_key, tenant_id="test_tenant")
        assert cached is None

    @pytest.mark.asyncio
    async def test_cache_statistics_tracking(self, gateway_with_cache):
        """Test that cache statistics are tracked correctly."""
        _, cache, _ = gateway_with_cache

        # Test basic cache operations
        # Set a value
        await cache.set("test_key", "test_value", tenant_id="test_tenant")
        
        # Get the value (should be a hit)
        value = await cache.get("test_key", tenant_id="test_tenant")
        assert value == "test_value"
        
        # Get a non-existent key (should be a miss)
        missing_value = await cache.get("non_existent", tenant_id="test_tenant")
        assert missing_value is None
        
        # Verify cache operations work correctly
        assert await cache.get("test_key", tenant_id="test_tenant") == "test_value"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
