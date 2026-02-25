"""
Unit Tests for Cache OTEL Integration

Tests for OpenTelemetry integration within the Cache Mechanism.
"""

import pytest

from src.core.cache_mechanism import CacheConfig, CacheMechanism
from src.core.otel_integration import OTELMetrics, OTELTracer


class TestCacheOTELIntegration:
    """Tests for Cache OTEL integration."""

    def test_cache_with_otel_tracer(self):
        """Test cache initialization with OTEL tracer."""
        tracer = OTELTracer(service_name="test-cache")
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            otel_tracer=tracer,
        )
        
        assert cache.otel_tracer is not None
        assert cache.otel_tracer.service_name == "test-cache"

    def test_cache_with_otel_metrics(self):
        """Test cache initialization with OTEL metrics."""
        metrics = OTELMetrics(service_name="test-cache")
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            otel_metrics=metrics,
        )
        
        assert cache.otel_metrics is not None
        assert cache.otel_metrics.service_name == "test-cache"

    def test_cache_without_otel(self):
        """Test cache works without OTEL configured."""
        cache = CacheMechanism(config=CacheConfig(backend="memory"))
        
        # OTEL should be auto-initialized if available
        # But it may be None if OTEL SDK is not installed
        assert cache is not None

    @pytest.mark.asyncio
    async def test_set_with_otel(self):
        """Test set operation with OTEL tracing."""
        tracer = OTELTracer(service_name="test-cache")
        metrics = OTELMetrics(service_name="test-cache")
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        # Execute set - should not raise exception
        await cache.set("key1", "value1")
        
        assert cache.otel_tracer is not None
        assert cache.otel_metrics is not None

    @pytest.mark.asyncio
    async def test_set_without_otel(self):
        """Test set operation without OTEL."""
        cache = CacheMechanism(config=CacheConfig(backend="memory"))
        
        # Mock OTEL to be None to test non-OTEL path
        cache.otel_tracer = None
        cache.otel_metrics = None
        
        await cache.set("key1", "value1")
        value = await cache.get("key1")
        
        assert value == "value1"

    @pytest.mark.asyncio
    async def test_get_with_otel(self):
        """Test get operation with OTEL tracing."""
        tracer = OTELTracer(service_name="test-cache")
        metrics = OTELMetrics(service_name="test-cache")
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        await cache.set("key1", "value1")
        value = await cache.get("key1")
        
        assert value == "value1"
        assert cache.otel_tracer is not None

    @pytest.mark.asyncio
    async def test_get_without_otel(self):
        """Test get operation without OTEL."""
        cache = CacheMechanism(config=CacheConfig(backend="memory"))
        cache.otel_tracer = None
        cache.otel_metrics = None
        
        await cache.set("key1", "value1")
        value = await cache.get("key1")
        
        assert value == "value1"

    @pytest.mark.asyncio
    async def test_get_miss_with_otel(self):
        """Test get miss with OTEL tracing."""
        tracer = OTELTracer(service_name="test-cache")
        metrics = OTELMetrics(service_name="test-cache")
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        value = await cache.get("nonexistent")
        
        assert value is None
        assert cache.otel_tracer is not None

    @pytest.mark.asyncio
    async def test_delete_with_otel(self):
        """Test delete operation with OTEL tracing."""
        tracer = OTELTracer(service_name="test-cache")
        metrics = OTELMetrics(service_name="test-cache")
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        await cache.set("key1", "value1")
        await cache.delete("key1")
        value = await cache.get("key1")
        
        assert value is None
        assert cache.otel_tracer is not None

    @pytest.mark.asyncio
    async def test_delete_without_otel(self):
        """Test delete operation without OTEL."""
        cache = CacheMechanism(config=CacheConfig(backend="memory"))
        cache.otel_tracer = None
        cache.otel_metrics = None
        
        await cache.set("key1", "value1")
        await cache.delete("key1")
        value = await cache.get("key1")
        
        assert value is None

    @pytest.mark.asyncio
    async def test_invalidate_pattern_with_otel(self):
        """Test invalidate_pattern operation with OTEL tracing."""
        tracer = OTELTracer(service_name="test-cache")
        metrics = OTELMetrics(service_name="test-cache")
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        # Invalidate pattern - note: pattern matching works on the full key including namespace
        await cache.invalidate_pattern("key")
        
        value1 = await cache.get("key1")
        value2 = await cache.get("key2")
        
        assert value1 is None
        assert value2 is None
        assert cache.otel_tracer is not None

    @pytest.mark.asyncio
    async def test_invalidate_pattern_without_otel(self):
        """Test invalidate_pattern operation without OTEL."""
        cache = CacheMechanism(config=CacheConfig(backend="memory"))
        cache.otel_tracer = None
        cache.otel_metrics = None
        
        await cache.set("key1", "value1")
        await cache.invalidate_pattern("key")
        
        value1 = await cache.get("key1")
        assert value1 is None

    @pytest.mark.asyncio
    async def test_clear_with_otel(self):
        """Test clear operation with OTEL tracing."""
        tracer = OTELTracer(service_name="test-cache")
        metrics = OTELMetrics(service_name="test-cache")
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.clear()
        
        value1 = await cache.get("key1")
        value2 = await cache.get("key2")
        
        assert value1 is None
        assert value2 is None
        assert cache.otel_tracer is not None

    @pytest.mark.asyncio
    async def test_clear_without_otel(self):
        """Test clear operation without OTEL."""
        cache = CacheMechanism(config=CacheConfig(backend="memory"))
        cache.otel_tracer = None
        cache.otel_metrics = None
        
        await cache.set("key1", "value1")
        await cache.clear()
        
        value1 = await cache.get("key1")
        assert value1 is None

    @pytest.mark.asyncio
    async def test_set_with_tenant_id_otel(self):
        """Test set operation with tenant_id and OTEL."""
        tracer = OTELTracer(service_name="test-cache")
        metrics = OTELMetrics(service_name="test-cache")
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        await cache.set("key1", "value1", tenant_id="tenant_123")
        value = await cache.get("key1", tenant_id="tenant_123")
        
        assert value == "value1"
        assert cache.otel_tracer is not None

    @pytest.mark.asyncio
    async def test_set_with_ttl_otel(self):
        """Test set operation with TTL and OTEL."""
        tracer = OTELTracer(service_name="test-cache")
        metrics = OTELMetrics(service_name="test-cache")
        
        cache = CacheMechanism(
            config=CacheConfig(backend="memory"),
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        await cache.set("key1", "value1", ttl=60)
        value = await cache.get("key1")
        
        assert value == "value1"
        assert cache.otel_tracer is not None

