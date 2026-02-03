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
        with patch("src.core.litellm_gateway.gateway.litellm") as mock_litellm:
            gateway = LiteLLMGateway(config=config)
            gateway._litellm = mock_litellm  # type: ignore[attr-defined]
            return gateway, cache, mock_litellm

    @pytest.mark.asyncio
    async def test_cache_hit_prevents_api_call(self, gateway_with_cache):
        """Test that cache hit prevents LLM API call."""
        gateway, _, mock_litellm = gateway_with_cache

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Cached response"
        mock_response.model = "gpt-4"
        mock_litellm.acompletion = AsyncMock(return_value=mock_response)

        # First call - cache miss (makes API call)
        response1 = await gateway.generate_async(
            prompt="Test prompt", model="gpt-4", tenant_id="test_tenant"
        )
        assert mock_litellm.acompletion.call_count == 1

        # Second call - cache hit (no API call)
        response2 = await gateway.generate_async(
            prompt="Test prompt", model="gpt-4", tenant_id="test_tenant"
        )
        # Should still be 1 (no new API call)
        assert mock_litellm.acompletion.call_count == 1
        assert response1.text == response2.text

    @pytest.mark.asyncio
    async def test_tenant_isolation_in_cache(self, gateway_with_cache):
        """Test that cache keys include tenant_id for isolation."""
        gateway, _, mock_litellm = gateway_with_cache

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
    async def test_cache_ttl_expiration(self, gateway_with_cache):
        """Test that cache respects TTL expiration."""
        import asyncio

        from src.core.cache_mechanism import CacheConfig, CacheMechanism

        # Create cache with short TTL
        short_cache = CacheMechanism(CacheConfig(default_ttl=1))  # 1 second
        config = GatewayConfig(enable_caching=True, cache_ttl=1, cache=short_cache)

        with patch("src.core.litellm_gateway.gateway.litellm") as mock_litellm:
            gateway = LiteLLMGateway(config=config)
            gateway._litellm = mock_litellm  # type: ignore[attr-defined]

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Response"
            mock_response.model = "gpt-4"
            mock_litellm.acompletion = AsyncMock(return_value=mock_response)

            # First call
            await gateway.generate_async(prompt="Test", model="gpt-4", tenant_id="test_tenant")
            assert mock_litellm.acompletion.call_count == 1

            # Wait for TTL expiration
            import asyncio
            await asyncio.sleep(1.1)

            # Second call after expiration - should make new API call
            await gateway.generate_async(prompt="Test", model="gpt-4", tenant_id="test_tenant")
            assert mock_litellm.acompletion.call_count == 2

    @pytest.mark.asyncio
    async def test_streaming_bypasses_cache(self, gateway_with_cache):
        """Test that streaming responses bypass cache."""
        gateway, cache, mock_litellm = gateway_with_cache

        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta.content = "Chunk"
        mock_litellm.acompletion = AsyncMock(return_value=[mock_chunk])

        # Streaming call should not use cache
        async for _ in gateway.stream_async(
            prompt="Test", model="gpt-4", tenant_id="test_tenant"
        ):
            # Stream chunks without processing (testing cache bypass)
            continue

        # Cache should not have stored streaming response
        cache_key = gateway._generate_cache_key(
            prompt="Test", model="gpt-4", tenant_id="test_tenant"
        )
        cached = cache.get(cache_key, tenant_id="test_tenant")
        assert cached is None

    def test_cache_statistics_tracking(self, gateway_with_cache):
        """Test that cache statistics are tracked correctly."""
        _, cache, _ = gateway_with_cache

        # Check initial cache stats
        stats = cache.get_stats()
        initial_hits = stats.get("hits", 0)
        initial_misses = stats.get("misses", 0)

        # Make calls that will hit/miss cache
        # This would require actual async execution, so we'll test the cache directly
        cache.set("test_key", "test_value", tenant_id="test_tenant")
        cache.get("test_key", tenant_id="test_tenant")  # Hit
        cache.get("non_existent", tenant_id="test_tenant")  # Miss

        stats = cache.get_stats()
        assert stats.get("hits", 0) > initial_hits
        assert stats.get("misses", 0) > initial_misses


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
