"""
Rate Limiter and Request Queue

Advanced rate limiting with queuing for LiteLLM Gateway.
"""


import asyncio
import hashlib
import json
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..exceptions import SDKError


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    max_queue_size: int = 100
    queue_timeout: float = 30.0
    burst_size: int = 10  # Allow burst of requests


class RateLimiter:
    """
    Advanced rate limiter with queuing and burst support.

    Implements token bucket algorithm with request queuing.
    """

    def __init__(self, config: Optional[RateLimitConfig] = None, tenant_id: Optional[str] = None):
        """
        Initialize rate limiter.
        
        Args:
            config (Optional[RateLimitConfig]): Configuration object or settings.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        """
        self.config = config or RateLimitConfig()
        self.tenant_id = tenant_id

        # Token bucket state
        self.tokens_per_minute = self.config.requests_per_minute
        self.tokens = float(self.config.burst_size)
        self.last_refill = datetime.now()

        # Request queue
        self.queue: deque = deque()
        self.queue_lock = asyncio.Lock()

        # Request tracking
        self.request_times: deque = deque()
        self.hourly_requests: deque = deque()

    async def acquire(self) -> None:
        """
        Acquire a rate limit token.
        
        Waits in queue if necessary until token is available.
        
        Returns:
            None: Result of the operation.
        
        Raises:
            create_error_with_suggestion: Raised when this function detects an invalid state or when an underlying call fails.
        """
        # Refill tokens
        await self._refill_tokens()

        # Check if we can proceed immediately
        if self.tokens >= 1.0 and len(self.queue) == 0:
            self.tokens -= 1.0
            self._record_request()
            return

        # Need to queue
        future: asyncio.Future[None] = asyncio.Future()
        async with self.queue_lock:
            if len(self.queue) >= self.config.max_queue_size:
                from ..utils.error_handler import create_error_with_suggestion

                raise create_error_with_suggestion(
                    SDKError,
                    message=f"Rate limit queue full (max: {self.config.max_queue_size})",
                    suggestion="Consider:\n  - Increasing max_queue_size in rate limit config\n  - Reducing request rate\n  - Using request batching to reduce queue pressure\n  - Implementing client-side rate limiting",
                )
            self.queue.append((future, datetime.now()))

        # Wait for token with timeout
        try:
            await asyncio.wait_for(future, timeout=self.config.queue_timeout)
        except asyncio.TimeoutError:
            async with self.queue_lock:
                # Remove from queue if still there
                self.queue = deque([(f, t) for f, t in self.queue if f != future])
            from ..utils.error_handler import create_error_with_suggestion

            raise create_error_with_suggestion(
                SDKError,
                message="Rate limit queue timeout exceeded",
                suggestion="Consider:\n  - Increasing queue_timeout in rate limit config\n  - Reducing request rate\n  - Using request batching\n  - Implementing exponential backoff on client side\n  - Checking if rate limits are too restrictive",
                original_error=asyncio.TimeoutError("Rate limit queue timeout exceeded"),
            )

    async def _refill_tokens(self) -> None:
        """
        Refill tokens based on elapsed time.
        
        Returns:
            None: Result of the operation.
        """
        now = datetime.now()
        elapsed = (now - self.last_refill).total_seconds()

        if elapsed >= 60.0:  # Refill every minute
            # Calculate tokens to add
            tokens_to_add = (elapsed / 60.0) * self.tokens_per_minute
            self.tokens = min(self.config.burst_size, self.tokens + tokens_to_add)
            self.last_refill = now

            # Process queue
            await self._process_queue()

    async def _process_queue(self) -> None:
        """
        Process queued requests.
        
        Returns:
            None: Result of the operation.
        """
        async with self.queue_lock:
            while self.queue and self.tokens >= 1.0:
                future, _ = self.queue.popleft()
                if not future.done():
                    self.tokens -= 1.0
                    self._record_request()
                    future.set_result(None)

    def _record_request(self) -> None:
        """
        Record a request for tracking.
        
        Returns:
            None: Result of the operation.
        """
        now = datetime.now()
        self.request_times.append(now)

        # Clean old requests (older than 1 minute)
        while self.request_times and (now - self.request_times[0]).total_seconds() > 60:
            self.request_times.popleft()

        # Track hourly requests
        self.hourly_requests.append(now)
        while self.hourly_requests and (now - self.hourly_requests[0]).total_seconds() > 3600:
            self.hourly_requests.popleft()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get rate limiter statistics.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        return {
            "tenant_id": self.tenant_id,
            "tokens_available": self.tokens,
            "queue_size": len(self.queue),
            "requests_last_minute": len(self.request_times),
            "requests_last_hour": len(self.hourly_requests),
            "config": {
                "requests_per_minute": self.config.requests_per_minute,
                "requests_per_hour": self.config.requests_per_hour,
                "max_queue_size": self.config.max_queue_size,
            },
        }


class RequestDeduplicator:
    """
    Request deduplicator to avoid processing identical requests.

    Uses request content hashing to identify duplicates.
    """

    def __init__(self, ttl: float = 300.0):
        """
        Initialize deduplicator.
        
        Args:
            ttl (float): Input parameter for this operation.
        """
        self.ttl = ttl
        self.cache: Dict[str, tuple[Any, datetime]] = {}
        self.lock = asyncio.Lock()

    def _hash_request(self, **kwargs: Any) -> str:
        """
        Generate hash for request.
        
        Args:
            **kwargs (Any): Input parameter for this operation.
        
        Returns:
            str: Returned text value.
        """
        # Create deterministic hash from request parameters
        request_data = json.dumps(kwargs, sort_keys=True, default=str)
        return hashlib.sha256(request_data.encode()).hexdigest()

    async def get_or_execute(self, func: Callable, **kwargs: Any) -> Any:
        """
        Execute function or return cached result if duplicate.
        
        Args:
            func (Callable): Input parameter for this operation.
            **kwargs (Any): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        """
        request_hash = self._hash_request(**kwargs)

        async with self.lock:
            # Check cache
            if request_hash in self.cache:
                result, cached_at = self.cache[request_hash]
                # Check if still valid
                if (datetime.now() - cached_at).total_seconds() < self.ttl:
                    return result
                else:
                    # Expired, remove
                    del self.cache[request_hash]

        # Execute function
        if asyncio.iscoroutinefunction(func):
            result = await func(**kwargs)
        else:
            result = func(**kwargs)

        # Cache result
        async with self.lock:
            self.cache[request_hash] = (result, datetime.now())

        return result

    def clear_cache(self) -> None:
        """
        Clear deduplication cache.
        
        Returns:
            None: Result of the operation.
        """
        self.cache.clear()


class RequestBatcher:
    """
    Request batcher for grouping similar requests.

    Batches requests and executes them together for efficiency.
    """

    def __init__(self, batch_size: int = 10, batch_timeout: float = 0.5):
        """
        Initialize batcher.
        
        Args:
            batch_size (int): Input parameter for this operation.
            batch_timeout (float): Input parameter for this operation.
        """
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.pending_batches: Dict[str, List[Tuple[asyncio.Future[Any], tuple, dict]]] = {}
        self.batch_lock = asyncio.Lock()
        self.batch_tasks: Dict[str, asyncio.Task] = {}

    async def batch_execute(self, batch_key: str, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execute function in batch.
        
        Args:
            batch_key (str): Input parameter for this operation.
            func (Callable): Input parameter for this operation.
            *args (Any): Input parameter for this operation.
            **kwargs (Any): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        """
        future: asyncio.Future[Any] = asyncio.Future()

        async with self.batch_lock:
            if batch_key not in self.pending_batches:
                self.pending_batches[batch_key] = []
                # Start batch task
                self.batch_tasks[batch_key] = asyncio.create_task(
                    self._process_batch(batch_key, func)
                )

            self.pending_batches[batch_key].append((future, args, kwargs))

            # Trigger batch if full
            if len(self.pending_batches[batch_key]) >= self.batch_size:
                self.batch_tasks[batch_key].cancel()
                self.batch_tasks[batch_key] = asyncio.create_task(
                    self._process_batch(batch_key, func)
                )

        return await future

    async def _execute_async_batch(self, batch: List[Tuple], func: Callable) -> List[Any]:
        """
        Execute batch of async function calls.
        
        Args:
            batch (List[Tuple]): Input parameter for this operation.
            func (Callable): Input parameter for this operation.
        
        Returns:
            List[Any]: List result of the operation.
        """
        tasks = [func(*args, **kwargs) for _, args, kwargs in batch]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def _execute_sync_batch(self, batch: List[Tuple], func: Callable) -> List[Any]:
        """
        Execute batch of sync function calls.
        
        Args:
            batch (List[Tuple]): Input parameter for this operation.
            func (Callable): Input parameter for this operation.
        
        Returns:
            List[Any]: List result of the operation.
        """
        results = []
        for _, args, kwargs in batch:
            try:
                result = func(*args, **kwargs)
                results.append(result)
            except Exception as e:
                results.append(e)
        return results

    def _set_batch_results(self, batch: List[Tuple], results: List[Any]) -> None:
        """
        Set results for all futures in batch.
        
        Args:
            batch (List[Tuple]): Input parameter for this operation.
            results (List[Any]): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        """
        for (future, _, _), result in zip(batch, results):
            if not future.done():
                if isinstance(result, Exception):
                    future.set_exception(result)
                else:
                    future.set_result(result)

    async def _process_batch(self, batch_key: str, func: Callable) -> None:
        """
        Process a batch of requests.
        
        Args:
            batch_key (str): Input parameter for this operation.
            func (Callable): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        """
        try:
            # Wait for batch timeout or batch size
            await asyncio.sleep(self.batch_timeout)

            async with self.batch_lock:
                if batch_key not in self.pending_batches:
                    return

                batch = self.pending_batches.pop(batch_key, [])
                if batch_key in self.batch_tasks:
                    del self.batch_tasks[batch_key]

            if not batch:
                return

            # Execute batch
            if asyncio.iscoroutinefunction(func):
                results = await self._execute_async_batch(batch, func)
            else:
                results = self._execute_sync_batch(batch, func)

            # Set results for futures
            self._set_batch_results(batch, results)

        except asyncio.CancelledError:
            # Batch was cancelled (triggered early) - cleanup and re-raise
            async with self.batch_lock:
                if batch_key in self.pending_batches:
                    del self.pending_batches[batch_key]
                if batch_key in self.batch_tasks:
                    del self.batch_tasks[batch_key]
            raise
