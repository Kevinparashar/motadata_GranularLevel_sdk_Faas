"""
Unit tests for rate_limiter.py
"""

import asyncio
from datetime import datetime, timedelta

import pytest

from src.core.litellm_gateway.rate_limiter import (
    RateLimitConfig,
    RateLimiter,
    RequestBatcher,
    RequestDeduplicator,
)


class TestRateLimitConfig:
    """Tests for RateLimitConfig dataclass."""

    def test_rate_limit_config_defaults(self):
        """Test RateLimitConfig with default values."""
        config = RateLimitConfig()

        assert config.requests_per_minute == 60
        assert config.requests_per_hour == 1000
        assert config.max_queue_size == 100
        assert abs(config.queue_timeout - 30.0) < 0.001
        assert config.burst_size == 10

    def test_rate_limit_config_custom(self):
        """Test RateLimitConfig with custom values."""
        config = RateLimitConfig(
            requests_per_minute=120,
            requests_per_hour=2000,
            max_queue_size=200,
            queue_timeout=60.0,
            burst_size=20,
        )

        assert config.requests_per_minute == 120
        assert config.requests_per_hour == 2000
        assert config.max_queue_size == 200
        assert abs(config.queue_timeout - 60.0) < 0.001
        assert config.burst_size == 20


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_init_default(self):
        """Test RateLimiter initialization with default config."""
        limiter = RateLimiter()

        assert limiter.config is not None
        assert limiter.tenant_id is None
        assert limiter.tokens_per_minute == 60
        assert abs(limiter.tokens - 10.0) < 0.001  # burst_size
        assert isinstance(limiter.last_refill, datetime)
        assert len(limiter.queue) == 0
        assert len(limiter.request_times) == 0
        assert len(limiter.hourly_requests) == 0

    def test_init_with_config(self):
        """Test RateLimiter initialization with custom config."""
        config = RateLimitConfig(requests_per_minute=120, burst_size=20)
        limiter = RateLimiter(config=config)

        assert limiter.config == config
        assert limiter.tokens_per_minute == 120
        assert abs(limiter.tokens - 20.0) < 0.001

    def test_init_with_tenant_id(self):
        """Test RateLimiter initialization with tenant_id."""
        limiter = RateLimiter(tenant_id="tenant-1")

        assert limiter.tenant_id == "tenant-1"

    @pytest.mark.asyncio
    async def test_acquire_immediate(self):
        """Test acquire() when tokens available immediately."""
        limiter = RateLimiter()
        limiter.tokens = 5.0

        await limiter.acquire()

        assert abs(limiter.tokens - 4.0) < 0.001
        assert len(limiter.request_times) == 1

    @pytest.mark.asyncio
    async def test_acquire_with_queue(self):
        """Test acquire() with queuing."""
        limiter = RateLimiter()
        limiter.tokens = 0.0  # No tokens available
        limiter.config.queue_timeout = 1.0

        # Mock _refill_tokens to add tokens after a short delay
        async def mock_refill():
            await asyncio.sleep(0.1)
            limiter.tokens = 1.0
            await limiter._process_queue()

        limiter._refill_tokens = mock_refill

        # Start acquire in background
        acquire_task = asyncio.create_task(limiter.acquire())

        # Wait a bit for queue to be set up
        await asyncio.sleep(0.05)

        # Trigger refill and queue processing
        await limiter._refill_tokens()

        # Wait for acquire to complete
        await acquire_task

        assert len(limiter.request_times) == 1

    @pytest.mark.asyncio
    async def test_acquire_queue_full(self):
        """Test acquire() when queue is full."""
        from src.core.exceptions import SDKError

        limiter = RateLimiter()
        limiter.config.max_queue_size = 2
        limiter.tokens = 0.0

        # Fill the queue
        limiter.queue.append((asyncio.Future(), datetime.now()))
        limiter.queue.append((asyncio.Future(), datetime.now()))

        with pytest.raises(SDKError, match="Rate limit queue full"):
            await limiter.acquire()

    @pytest.mark.asyncio
    async def test_acquire_timeout(self):
        """Test acquire() with timeout."""
        from src.core.exceptions import SDKError

        limiter = RateLimiter()
        limiter.config.queue_timeout = 0.1
        limiter.tokens = 0.0

        with pytest.raises(SDKError, match="Rate limit queue timeout exceeded"):
            await limiter.acquire()

    @pytest.mark.asyncio
    async def test_refill_tokens_after_minute(self):
        """Test _refill_tokens() after 1 minute."""
        limiter = RateLimiter()
        limiter.tokens = 0.0
        limiter.last_refill = datetime.now() - timedelta(seconds=120)

        await limiter._refill_tokens()

        # Should have refilled tokens (approximately 2 minutes worth)
        assert limiter.tokens > 0

    @pytest.mark.asyncio
    async def test_refill_tokens_less_than_minute(self):
        """Test _refill_tokens() before 1 minute."""
        limiter = RateLimiter()
        initial_tokens = limiter.tokens
        limiter.last_refill = datetime.now() - timedelta(seconds=30)

        await limiter._refill_tokens()

        # Should not refill yet
        assert limiter.tokens == initial_tokens

    @pytest.mark.asyncio
    async def test_refill_tokens_caps_at_burst(self):
        """Test _refill_tokens() caps tokens at burst_size."""
        limiter = RateLimiter()
        limiter.config.burst_size = 10
        limiter.tokens = 0.0
        limiter.last_refill = datetime.now() - timedelta(seconds=300)  # 5 minutes

        await limiter._refill_tokens()

        # Should be capped at burst_size
        assert limiter.tokens <= limiter.config.burst_size

    @pytest.mark.asyncio
    async def test_process_queue(self):
        """Test _process_queue()."""
        limiter = RateLimiter()
        limiter.tokens = 2.0

        # Add futures to queue
        future1 = asyncio.Future()
        future2 = asyncio.Future()
        limiter.queue.append((future1, datetime.now()))
        limiter.queue.append((future2, datetime.now()))

        await limiter._process_queue()

        # Both futures should be resolved
        assert future1.done()
        assert future2.done()
        assert abs(limiter.tokens - 0.0) < 0.001

    @pytest.mark.asyncio
    async def test_process_queue_partial(self):
        """Test _process_queue() with partial tokens."""
        limiter = RateLimiter()
        limiter.tokens = 1.0

        # Add 2 futures to queue
        future1 = asyncio.Future()
        future2 = asyncio.Future()
        limiter.queue.append((future1, datetime.now()))
        limiter.queue.append((future2, datetime.now()))

        await limiter._process_queue()

        # Only first future should be resolved
        assert future1.done()
        assert not future2.done()
        assert abs(limiter.tokens - 0.0) < 0.001

    @pytest.mark.asyncio
    async def test_process_queue_done_future(self):
        """Test _process_queue() skips already done futures."""
        limiter = RateLimiter()
        limiter.tokens = 1.0

        # Add a done future and a pending future
        future1 = asyncio.Future()
        future1.set_result(None)
        future2 = asyncio.Future()
        limiter.queue.append((future1, datetime.now()))
        limiter.queue.append((future2, datetime.now()))

        await limiter._process_queue()

        # future2 should be resolved, tokens should be 0
        assert future2.done()
        assert abs(limiter.tokens - 0.0) < 0.001

    def test_record_request(self):
        """Test _record_request()."""
        limiter = RateLimiter()

        limiter._record_request()

        assert len(limiter.request_times) == 1
        assert len(limiter.hourly_requests) == 1

    def test_record_request_cleanup_old(self):
        """Test _record_request() cleans up old requests."""
        limiter = RateLimiter()

        # Add old requests (older than cleanup thresholds)
        old_time_minute = datetime.now() - timedelta(seconds=120)  # Older than 1 minute
        old_time_hour = datetime.now() - timedelta(seconds=3700)  # Older than 1 hour
        limiter.request_times.append(old_time_minute)
        limiter.hourly_requests.append(old_time_hour)

        # Add new request
        limiter._record_request()

        # Old requests should be cleaned up
        assert len(limiter.request_times) == 1  # Old minute request cleaned, new one added
        assert len(limiter.hourly_requests) == 1  # Old hour request cleaned, new one added

    def test_get_stats(self):
        """Test get_stats()."""
        limiter = RateLimiter()
        limiter.tokens = 5.0
        limiter._record_request()

        stats = limiter.get_stats()

        assert stats["tenant_id"] is None
        assert abs(stats["tokens_available"] - 5.0) < 0.001
        assert stats["queue_size"] == 0
        assert stats["requests_last_minute"] == 1
        assert stats["requests_last_hour"] == 1
        assert stats["config"]["requests_per_minute"] == 60

    def test_get_stats_with_tenant_id(self):
        """Test get_stats() with tenant_id."""
        limiter = RateLimiter(tenant_id="tenant-1")

        stats = limiter.get_stats()

        assert stats["tenant_id"] == "tenant-1"


class TestRequestDeduplicator:
    """Tests for RequestDeduplicator class."""

    def test_init_default(self):
        """Test RequestDeduplicator initialization with default TTL."""
        dedup = RequestDeduplicator()

        assert abs(dedup.ttl - 300.0) < 0.001
        assert dedup.cache == {}

    def test_init_custom_ttl(self):
        """Test RequestDeduplicator initialization with custom TTL."""
        dedup = RequestDeduplicator(ttl=600.0)

        assert abs(dedup.ttl - 600.0) < 0.001

    def test_hash_request(self):
        """Test _hash_request()."""
        dedup = RequestDeduplicator()

        hash1 = dedup._hash_request(prompt="test", model="gpt-4")
        hash2 = dedup._hash_request(prompt="test", model="gpt-4")
        hash3 = dedup._hash_request(prompt="different", model="gpt-4")

        assert hash1 == hash2
        assert hash1 != hash3

    def test_hash_request_deterministic(self):
        """Test _hash_request() produces deterministic hashes."""
        dedup = RequestDeduplicator()

        hash1 = dedup._hash_request(a=1, b=2, c=3)
        hash2 = dedup._hash_request(c=3, a=1, b=2)  # Different order

        # Should be same due to sort_keys=True
        assert hash1 == hash2

    @pytest.mark.asyncio
    async def test_get_or_execute_cache_hit(self):
        """Test get_or_execute() with cache hit."""
        dedup = RequestDeduplicator(ttl=60.0)

        # First call - execute function
        call_count = 0

        def test_func(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = await dedup.get_or_execute(test_func, x=5)

        # Second call with same params - should use cache
        result2 = await dedup.get_or_execute(test_func, x=5)

        assert result1 == 10
        assert result2 == 10
        assert call_count == 1  # Function called only once

    @pytest.mark.asyncio
    async def test_get_or_execute_cache_miss(self):
        """Test get_or_execute() with cache miss."""
        dedup = RequestDeduplicator(ttl=60.0)

        call_count = 0

        def test_func(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = await dedup.get_or_execute(test_func, x=5)
        result2 = await dedup.get_or_execute(test_func, x=10)  # Different params

        assert result1 == 10
        assert result2 == 20
        assert call_count == 2  # Function called twice

    @pytest.mark.asyncio
    async def test_get_or_execute_cache_expired(self):
        """Test get_or_execute() with expired cache."""
        dedup = RequestDeduplicator(ttl=0.1)  # Very short TTL

        call_count = 0

        def test_func(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = await dedup.get_or_execute(test_func, x=5)

        # Wait for cache to expire
        await asyncio.sleep(0.2)

        result2 = await dedup.get_or_execute(test_func, x=5)

        assert result1 == 10
        assert result2 == 10
        assert call_count == 2  # Function called twice due to expiration

    @pytest.mark.asyncio
    async def test_get_or_execute_async_function(self):
        """Test get_or_execute() with async function."""
        dedup = RequestDeduplicator()

        call_count = 0

        async def async_func(x: int) -> int:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0)
            return x * 2

        result1 = await dedup.get_or_execute(async_func, x=5)
        result2 = await dedup.get_or_execute(async_func, x=5)

        assert result1 == 10
        assert result2 == 10
        assert call_count == 1

    def test_clear_cache(self):
        """Test clear_cache()."""
        dedup = RequestDeduplicator()
        dedup.cache["hash1"] = ("result1", datetime.now())
        dedup.cache["hash2"] = ("result2", datetime.now())

        dedup.clear_cache()

        assert len(dedup.cache) == 0


class TestRequestBatcher:
    """Tests for RequestBatcher class."""

    def test_init_default(self):
        """Test RequestBatcher initialization with default parameters."""
        batcher = RequestBatcher()

        assert batcher.batch_size == 10
        assert abs(batcher.batch_timeout - 0.5) < 0.001
        assert batcher.pending_batches == {}
        assert batcher.batch_tasks == {}

    def test_init_custom(self):
        """Test RequestBatcher initialization with custom parameters."""
        batcher = RequestBatcher(batch_size=20, batch_timeout=1.0)

        assert batcher.batch_size == 20
        assert abs(batcher.batch_timeout - 1.0) < 0.001

    @pytest.mark.asyncio
    async def test_batch_execute_single_request(self):
        """Test batch_execute() with single request."""
        batcher = RequestBatcher(batch_size=2, batch_timeout=0.1)

        def test_func(x: int) -> int:
            return x * 2

        result = await batcher.batch_execute("batch1", test_func, x=5)

        assert result == 10

    @pytest.mark.asyncio
    async def test_batch_execute_full_batch(self):
        """Test batch_execute() when batch is full."""
        batcher = RequestBatcher(batch_size=2, batch_timeout=1.0)

        def test_func(x: int) -> int:
            return x * 2

        # Add requests to fill batch
        result1 = batcher.batch_execute("batch1", test_func, x=5)
        result2 = batcher.batch_execute("batch1", test_func, x=10)

        # Both should complete immediately (batch triggered)
        results = await asyncio.gather(result1, result2)

        assert results[0] == 10
        assert results[1] == 20

    @pytest.mark.asyncio
    async def test_batch_execute_timeout(self):
        """Test batch_execute() with timeout."""
        batcher = RequestBatcher(batch_size=5, batch_timeout=0.1)

        def test_func(x: int) -> int:
            return x * 2

        result = await batcher.batch_execute("batch1", test_func, x=5)

        assert result == 10

    @pytest.mark.asyncio
    async def test_batch_execute_async_function(self):
        """Test batch_execute() with async function."""
        batcher = RequestBatcher(batch_size=2, batch_timeout=0.1)

        async def async_func(x: int) -> int:
            await asyncio.sleep(0)
            return x * 2

        result = await batcher.batch_execute("batch1", async_func, x=5)

        assert result == 10

    @pytest.mark.asyncio
    async def test_execute_async_batch(self):
        """Test _execute_async_batch()."""
        batcher = RequestBatcher()

        async def async_func(x: int) -> int:
            await asyncio.sleep(0)
            return x * 2

        batch = [
            (asyncio.Future(), (5,), {}),
            (asyncio.Future(), (10,), {}),
        ]

        results = await batcher._execute_async_batch(batch, async_func)

        assert results == [10, 20]

    @pytest.mark.asyncio
    async def test_execute_async_batch_with_exceptions(self):
        """Test _execute_async_batch() handles exceptions."""
        batcher = RequestBatcher()

        async def async_func(x: int) -> int:
            if x == 0:
                raise ValueError("Error")
            await asyncio.sleep(0)
            return x * 2

        batch = [
            (asyncio.Future(), (5,), {}),
            (asyncio.Future(), (0,), {}),  # Will raise exception
        ]

        results = await batcher._execute_async_batch(batch, async_func)

        assert results[0] == 10
        assert isinstance(results[1], ValueError)

    @pytest.mark.asyncio
    async def test_execute_sync_batch(self):
        """Test _execute_sync_batch()."""
        batcher = RequestBatcher()

        def sync_func(x: int) -> int:
            return x * 2

        batch = [
            (asyncio.Future(), (5,), {}),
            (asyncio.Future(), (10,), {}),
        ]

        results = batcher._execute_sync_batch(batch, sync_func)

        assert results == [10, 20]

    @pytest.mark.asyncio
    async def test_execute_sync_batch_with_exceptions(self):
        """Test _execute_sync_batch() handles exceptions."""
        batcher = RequestBatcher()

        def sync_func(x: int) -> int:
            if x == 0:
                raise ValueError("Error")
            return x * 2

        batch = [
            (asyncio.Future(), (5,), {}),
            (asyncio.Future(), (0,), {}),  # Will raise exception
        ]

        results = batcher._execute_sync_batch(batch, sync_func)

        assert results[0] == 10
        assert isinstance(results[1], ValueError)

    @pytest.mark.asyncio
    async def test_set_batch_results_success(self):
        """Test _set_batch_results() with successful results."""
        batcher = RequestBatcher()

        future1 = asyncio.Future()
        future2 = asyncio.Future()
        batch = [
            (future1, (), {}),
            (future2, (), {}),
        ]
        results = [10, 20]

        batcher._set_batch_results(batch, results)

        assert future1.done()
        assert future2.done()
        assert future1.result() == 10
        assert future2.result() == 20

    @pytest.mark.asyncio
    async def test_set_batch_results_with_exceptions(self):
        """Test _set_batch_results() with exceptions."""
        batcher = RequestBatcher()

        future1 = asyncio.Future()
        future2 = asyncio.Future()
        batch = [
            (future1, (), {}),
            (future2, (), {}),
        ]
        results = [10, ValueError("Error")]

        batcher._set_batch_results(batch, results)

        assert future1.done()
        assert future2.done()
        assert future1.result() == 10
        with pytest.raises(ValueError):
            future2.result()

    @pytest.mark.asyncio
    async def test_process_batch_success(self):
        """Test _process_batch() success."""
        batcher = RequestBatcher(batch_size=5, batch_timeout=0.1)

        def test_func(x: int) -> int:
            return x * 2

        future1 = asyncio.Future()
        future2 = asyncio.Future()
        batcher.pending_batches["batch1"] = [
            (future1, (5,), {}),
            (future2, (10,), {}),
        ]

        await batcher._process_batch("batch1", test_func)

        assert future1.done()
        assert future2.done()
        assert future1.result() == 10
        assert future2.result() == 20

    @pytest.mark.asyncio
    async def test_process_batch_empty(self):
        """Test _process_batch() with empty batch."""
        batcher = RequestBatcher(batch_size=5, batch_timeout=0.1)

        def test_func(x: int) -> int:
            return x * 2

        # No pending batches
        await batcher._process_batch("batch1", test_func)

        # Should complete without error

    @pytest.mark.asyncio
    async def test_process_batch_cancelled(self):
        """Test _process_batch() handles cancellation."""
        batcher = RequestBatcher(batch_size=5, batch_timeout=1.0)

        def test_func(x: int) -> int:
            return x * 2

        future1 = asyncio.Future()
        batcher.pending_batches["batch1"] = [(future1, (5,), {})]

        # Start batch processing
        task = asyncio.create_task(batcher._process_batch("batch1", test_func))

        # Wait a bit for function to enter try block
        await asyncio.sleep(0.05)

        # Cancel after function has started
        task.cancel()

        # Should handle cancellation gracefully
        with pytest.raises(asyncio.CancelledError):
            await task

        # Batch should be cleaned up (cleanup happens in except block)
        assert "batch1" not in batcher.pending_batches

