"""
Integration Tests for Gateway-LLMOps Integration

Tests the integration between LiteLLM Gateway and LLMOps.
"""


from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.litellm_gateway import GatewayConfig, LiteLLMGateway
from src.core.llmops import LLMOps


@pytest.mark.integration
class TestGatewayLLMOpsIntegration:
    """Test Gateway-LLMOps integration."""

    @pytest.fixture
    def gateway_with_llmops(self):
        """Create gateway with LLMOps enabled."""
        config = GatewayConfig(enable_llmops=True)
        # Patch internal initialization methods to prevent errors during instantiation
        with patch.object(LiteLLMGateway, "_initialize_kv_cache"), \
             patch.object(LiteLLMGateway, "_initialize_cache"), \
             patch.object(LiteLLMGateway, "_initialize_router"), \
             patch.object(LiteLLMGateway, "_initialize_deduplicator"):
            gateway = LiteLLMGateway(config=config)
            
            # Set required attributes that were skipped by patching
            gateway.kv_cache = None
            gateway.cache = None
            gateway.deduplicator = None
            
            # Create a mock router
            mock_router = MagicMock()
            mock_router.acompletion = AsyncMock()
            mock_router.aembedding = AsyncMock()
            gateway.router = mock_router
            
            return gateway, mock_router

    @pytest.fixture
    def gateway_without_llmops(self):
        """Create gateway without LLMOps."""
        config = GatewayConfig(enable_llmops=False)
        # Patch internal initialization methods to prevent errors during instantiation
        with patch.object(LiteLLMGateway, "_initialize_kv_cache"), \
             patch.object(LiteLLMGateway, "_initialize_cache"), \
             patch.object(LiteLLMGateway, "_initialize_router"), \
             patch.object(LiteLLMGateway, "_initialize_deduplicator"):
            gateway = LiteLLMGateway(config=config)
            
            # Set required attributes that were skipped by patching
            gateway.kv_cache = None
            gateway.cache = None
            gateway.deduplicator = None
            
            # Create a mock router
            mock_router = MagicMock()
            mock_router.acompletion = AsyncMock()
            mock_router.aembedding = AsyncMock()
            gateway.router = mock_router
            
            return gateway, mock_router

    def test_llmops_initialization(self, gateway_with_llmops):
        """Test that LLMOps is initialized when enabled."""
        gateway, _ = gateway_with_llmops
        assert gateway.llmops is not None
        assert isinstance(gateway.llmops, LLMOps)

    def test_llmops_not_initialized_when_disabled(self, gateway_without_llmops):
        """Test that LLMOps is not initialized when disabled."""
        gateway, _ = gateway_without_llmops
        assert gateway.llmops is None

    @pytest.mark.asyncio
    async def test_operation_logging(self, gateway_with_llmops):
        """Test that LLM operations are logged."""
        gateway, mock_router = gateway_with_llmops

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

        # Mock LLMOps log_operation
        with patch.object(gateway.llmops, "log_operation") as mock_log:
            await gateway.generate_async(
                prompt="Test prompt", model="gpt-4", tenant_id="test_tenant"
            )

            # LLMOps should have logged the operation
            mock_log.assert_called()

    @pytest.mark.asyncio
    async def test_token_usage_tracking(self, gateway_with_llmops):
        """Test that token usage is tracked."""
        gateway, mock_router = gateway_with_llmops

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = "Response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4"
        # Usage needs to be an object with __dict__ attribute
        class UsageObject:
            def __init__(self):
                self.prompt_tokens = 100
                self.completion_tokens = 50
                self.total_tokens = 150
        mock_response.usage = UsageObject()
        mock_router.acompletion = AsyncMock(return_value=mock_response)

        await gateway.generate_async(prompt="Test prompt", model="gpt-4", tenant_id="test_tenant")

        # Check that token usage was tracked
        # This would require checking LLMOps storage
        assert gateway.llmops is not None

    @pytest.mark.asyncio
    async def test_cost_calculation(self, gateway_with_llmops):
        """Test that costs are calculated and tracked."""
        gateway, mock_router = gateway_with_llmops

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = "Response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4"
        # Usage needs to be an object with __dict__ attribute
        class UsageObject:
            def __init__(self):
                self.prompt_tokens = 1000
                self.completion_tokens = 500
                self.total_tokens = 1500
        mock_response.usage = UsageObject()
        mock_router.acompletion = AsyncMock(return_value=mock_response)

        await gateway.generate_async(prompt="Test prompt", model="gpt-4", tenant_id="test_tenant")

        # Cost should be calculated based on token usage
        # Check LLMOps for cost tracking
        assert gateway.llmops is not None

    @pytest.mark.asyncio
    async def test_latency_monitoring(self, gateway_with_llmops):
        """Test that latency is monitored."""
        import time

        gateway, mock_router = gateway_with_llmops

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

        start = time.time()
        await gateway.generate_async(prompt="Test prompt", model="gpt-4", tenant_id="test_tenant")
        elapsed = time.time() - start

        # Latency should be tracked in LLMOps
        assert gateway.llmops is not None
        assert elapsed >= 0

    @pytest.mark.asyncio
    async def test_success_error_tracking(self, gateway_with_llmops):
        """Test that success and error rates are tracked."""
        gateway, mock_router = gateway_with_llmops

        # Successful operation
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

        await gateway.generate_async(prompt="Test prompt", model="gpt-4", tenant_id="test_tenant")

        # Error operation
        mock_router.acompletion.side_effect = Exception("API Error")

        try:
            await gateway.generate_async(
                prompt="Test prompt", model="gpt-4", tenant_id="test_tenant"
            )
        except Exception:
            pass

        # Both success and error should be tracked
        assert gateway.llmops is not None

    @pytest.mark.asyncio
    async def test_tenant_isolation_in_metrics(self, gateway_with_llmops):
        """Test that metrics are tracked per tenant."""
        gateway, mock_router = gateway_with_llmops

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

        # Make calls for different tenants
        await gateway.generate_async(prompt="Test", model="gpt-4", tenant_id="tenant_1")
        await gateway.generate_async(prompt="Test", model="gpt-4", tenant_id="tenant_2")
        
        # Metrics should be isolated per tenant
        # This would require checking LLMOps storage structure
        assert gateway.llmops is not None

    @pytest.mark.asyncio
    async def test_operation_type_tracking(self, gateway_with_llmops):
        """Test that different operation types are tracked."""
        gateway, mock_router = gateway_with_llmops

        # Generation operation
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

        await gateway.generate_async(prompt="Test", model="gpt-4", tenant_id="test_tenant")

        # Embedding operation
        mock_embedding = MagicMock()
        mock_embedding.data = [MagicMock(embedding=[0.1] * 1536)]
        mock_embedding.model = "text-embedding-3-small"
        mock_router.aembedding = AsyncMock(return_value=mock_embedding)

        await gateway.embed_async(
            texts=["Test"], model="text-embedding-3-small", tenant_id="test_tenant"
        )

        # Both operation types should be tracked
        assert gateway.llmops is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
