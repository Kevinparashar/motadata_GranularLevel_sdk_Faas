"""
Unit Tests for Circuit Breaker

Tests circuit breaker pattern implementation for handling service failures.
"""

import asyncio
from datetime import datetime, timedelta

import pytest

from src.core.utils.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerStats,
    CircuitState,
)


class TestCircuitState:
    """Test CircuitState enum."""

    def test_circuit_state_values(self):
        """Test CircuitState enum values."""
        assert CircuitState.CLOSED == "closed"
        assert CircuitState.OPEN == "open"
        assert CircuitState.HALF_OPEN == "half_open"


class TestCircuitBreakerConfig:
    """Test CircuitBreakerConfig dataclass."""

    def test_circuit_breaker_config_defaults(self):
        """Test CircuitBreakerConfig with default values."""
        config = CircuitBreakerConfig()
        assert config.failure_threshold == 5
        assert config.success_threshold == 2
        assert abs(config.timeout - 60.0) < 0.001
        assert config.expected_exception == (Exception,)

    def test_circuit_breaker_config_custom(self):
        """Test CircuitBreakerConfig with custom values."""
        config = CircuitBreakerConfig(
            failure_threshold=10, success_threshold=3, timeout=30.0, expected_exception=(ValueError, RuntimeError)
        )
        assert config.failure_threshold == 10
        assert config.success_threshold == 3
        assert abs(config.timeout - 30.0) < 0.001
        assert config.expected_exception == (ValueError, RuntimeError)


class TestCircuitBreakerStats:
    """Test CircuitBreakerStats dataclass."""

    def test_circuit_breaker_stats_defaults(self):
        """Test CircuitBreakerStats with default values."""
        stats = CircuitBreakerStats()
        assert stats.failures == 0
        assert stats.successes == 0
        assert stats.total_calls == 0
        assert stats.last_failure_time is None
        assert stats.last_success_time is None
        assert stats.state_changes == 0

    def test_circuit_breaker_stats_custom(self):
        """Test CircuitBreakerStats with custom values."""
        now = datetime.now()
        stats = CircuitBreakerStats(
            failures=5,
            successes=10,
            total_calls=15,
            last_failure_time=now,
            last_success_time=now,
            state_changes=2,
        )
        assert stats.failures == 5
        assert stats.successes == 10
        assert stats.total_calls == 15
        assert stats.last_failure_time == now
        assert stats.last_success_time == now
        assert stats.state_changes == 2


class TestCircuitBreaker:
    """Test CircuitBreaker class."""

    def test_circuit_breaker_init_default(self):
        """Test CircuitBreaker initialization with defaults."""
        breaker = CircuitBreaker("test_breaker")
        assert breaker.name == "test_breaker"
        assert isinstance(breaker.config, CircuitBreakerConfig)
        assert breaker.state == CircuitState.CLOSED
        assert isinstance(breaker.stats, CircuitBreakerStats)
        assert breaker._opened_at is None

    def test_circuit_breaker_init_custom_config(self):
        """Test CircuitBreaker initialization with custom config."""
        config = CircuitBreakerConfig(failure_threshold=10, timeout=30.0)
        breaker = CircuitBreaker("test_breaker", config=config)
        assert breaker.name == "test_breaker"
        assert breaker.config.failure_threshold == 10
        assert abs(breaker.config.timeout - 30.0) < 0.001
        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_call_success_sync_function(self):
        """Test call with successful sync function."""
        breaker = CircuitBreaker("test_breaker")

        def sync_func(x: int) -> int:
            return x * 2

        result = await breaker.call(sync_func, 5)
        assert result == 10
        assert breaker.state == CircuitState.CLOSED
        assert breaker.stats.successes == 1
        assert breaker.stats.total_calls == 1
        assert breaker.stats.failures == 0
        assert breaker.stats.last_success_time is not None

    @pytest.mark.asyncio
    async def test_call_success_async_function(self):
        """Test call with successful async function."""
        breaker = CircuitBreaker("test_breaker")

        async def async_func(x: int) -> int:
            await asyncio.sleep(0)
            return x * 2

        result = await breaker.call(async_func, 5)
        assert result == 10
        assert breaker.state == CircuitState.CLOSED
        assert breaker.stats.successes == 1
        assert breaker.stats.total_calls == 1
        assert breaker.stats.failures == 0

    @pytest.mark.asyncio
    async def test_call_failure_sync_function(self):
        """Test call with failing sync function."""
        breaker = CircuitBreaker("test_breaker")

        def failing_func() -> None:
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await breaker.call(failing_func)

        assert breaker.state == CircuitState.CLOSED
        assert breaker.stats.failures == 1
        assert breaker.stats.total_calls == 1
        assert breaker.stats.successes == 0
        assert breaker.stats.last_failure_time is not None

    @pytest.mark.asyncio
    async def test_call_failure_async_function(self):
        """Test call with failing async function."""
        breaker = CircuitBreaker("test_breaker")

        async def failing_func() -> None:
            await asyncio.sleep(0)
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await breaker.call(failing_func)

        assert breaker.state == CircuitState.CLOSED
        assert breaker.stats.failures == 1
        assert breaker.stats.total_calls == 1

    @pytest.mark.asyncio
    async def test_call_opens_circuit_after_threshold(self):
        """Test circuit opens after failure threshold."""
        config = CircuitBreakerConfig(failure_threshold=3)
        breaker = CircuitBreaker("test_breaker", config=config)

        def failing_func() -> None:
            raise ValueError("Test error")

        # Cause failures up to threshold
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(failing_func)

        assert breaker.state == CircuitState.OPEN
        assert breaker.stats.failures == 3
        assert breaker.stats.state_changes == 1
        assert breaker._opened_at is not None

    @pytest.mark.asyncio
    async def test_call_rejects_when_open(self):
        """Test call rejects immediately when circuit is open."""
        config = CircuitBreakerConfig(failure_threshold=2)
        breaker = CircuitBreaker("test_breaker", config=config)

        def failing_func() -> None:
            raise ValueError("Test error")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_func)

        assert breaker.state == CircuitState.OPEN

        # Try to call when open - should reject immediately
        with pytest.raises(RuntimeError, match="Circuit breaker 'test_breaker' is OPEN"):
            await breaker.call(failing_func)

        # Stats should not change (call was rejected)
        assert breaker.stats.total_calls == 2

    @pytest.mark.asyncio
    async def test_call_transitions_to_half_open_after_timeout(self):
        """Test circuit transitions to half-open after timeout."""
        config = CircuitBreakerConfig(failure_threshold=2, timeout=0.1)
        breaker = CircuitBreaker("test_breaker", config=config)

        def failing_func() -> None:
            raise ValueError("Test error")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_func)

        assert breaker.state == CircuitState.OPEN

        # Wait for timeout
        await asyncio.sleep(0.15)

        # Next call should transition to half-open
        def success_func() -> str:
            return "success"

        result = await breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitState.HALF_OPEN
        assert breaker.stats.state_changes == 2
        assert breaker.stats.successes == 1

    @pytest.mark.asyncio
    async def test_call_closes_from_half_open_after_success_threshold(self):
        """Test circuit closes from half-open after success threshold."""
        config = CircuitBreakerConfig(failure_threshold=2, success_threshold=2, timeout=0.1)
        breaker = CircuitBreaker("test_breaker", config=config)

        def failing_func() -> None:
            raise ValueError("Test error")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_func)

        assert breaker.state == CircuitState.OPEN

        # Wait for timeout
        await asyncio.sleep(0.15)

        # Get to half-open state
        def success_func() -> str:
            return "success"

        await breaker.call(success_func)
        assert breaker.state == CircuitState.HALF_OPEN

        # Second success should close the circuit
        await breaker.call(success_func)
        assert breaker.state == CircuitState.CLOSED
        assert breaker.stats.state_changes == 3
        assert breaker.stats.failures == 0  # Reset on close
        assert breaker._opened_at is None

    @pytest.mark.asyncio
    async def test_call_opens_from_half_open_on_failure(self):
        """Test circuit opens immediately from half-open on any failure."""
        config = CircuitBreakerConfig(failure_threshold=2, success_threshold=2, timeout=0.1)
        breaker = CircuitBreaker("test_breaker", config=config)

        def failing_func() -> None:
            raise ValueError("Test error")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_func)

        assert breaker.state == CircuitState.OPEN

        # Wait for timeout
        await asyncio.sleep(0.15)

        # Get to half-open state
        def success_func() -> str:
            return "success"

        await breaker.call(success_func)
        assert breaker.state == CircuitState.HALF_OPEN
        assert breaker.stats.successes == 1

        # Failure in half-open should immediately open circuit
        with pytest.raises(ValueError):
            await breaker.call(failing_func)

        assert breaker.state == CircuitState.OPEN
        assert breaker.stats.state_changes == 3
        assert breaker.stats.successes == 0  # Reset on open

    @pytest.mark.asyncio
    async def test_call_non_expected_exception_does_not_count_as_failure(self):
        """Test that non-expected exceptions don't count as failures."""
        config = CircuitBreakerConfig(failure_threshold=2, expected_exception=(ValueError,))
        breaker = CircuitBreaker("test_breaker", config=config)

        def raises_runtime_error() -> None:
            raise RuntimeError("Not expected")

        # RuntimeError is not in expected_exception, so it should propagate but not count
        with pytest.raises(RuntimeError, match="Not expected"):
            await breaker.call(raises_runtime_error)

        # Should not count as failure
        assert breaker.stats.failures == 0
        assert breaker.stats.total_calls == 0  # Not counted in total_calls either
        assert breaker.state == CircuitState.CLOSED

    def test_get_stats(self):
        """Test get_stats method."""
        breaker = CircuitBreaker("test_breaker")
        breaker.stats.failures = 5
        breaker.stats.successes = 10
        breaker.stats.total_calls = 15
        breaker.stats.state_changes = 2
        breaker.state = CircuitState.OPEN

        now = datetime.now()
        breaker.stats.last_failure_time = now
        breaker.stats.last_success_time = now
        breaker._opened_at = now

        stats = breaker.get_stats()
        assert stats["name"] == "test_breaker"
        assert stats["state"] == "open"
        assert stats["failures"] == 5
        assert stats["successes"] == 10
        assert stats["total_calls"] == 15
        assert stats["state_changes"] == 2
        assert stats["last_failure_time"] == now.isoformat()
        assert stats["last_success_time"] == now.isoformat()
        assert stats["opened_at"] == now.isoformat()

    def test_get_stats_with_none_times(self):
        """Test get_stats with None times."""
        breaker = CircuitBreaker("test_breaker")
        stats = breaker.get_stats()
        assert stats["last_failure_time"] is None
        assert stats["last_success_time"] is None
        assert stats["opened_at"] is None

    def test_reset(self):
        """Test reset method."""
        breaker = CircuitBreaker("test_breaker")
        breaker.state = CircuitState.OPEN
        breaker.stats.failures = 10
        breaker.stats.successes = 5
        breaker.stats.total_calls = 15
        breaker.stats.state_changes = 3
        breaker._opened_at = datetime.now()

        breaker.reset()

        assert breaker.state == CircuitState.CLOSED
        assert breaker.stats.failures == 0
        assert breaker.stats.successes == 0
        assert breaker.stats.total_calls == 0
        assert breaker.stats.state_changes == 0
        assert breaker._opened_at is None

    @pytest.mark.asyncio
    async def test_call_with_args_and_kwargs(self):
        """Test call with function arguments and keyword arguments."""
        breaker = CircuitBreaker("test_breaker")

        def func_with_args(x: int, y: int, z: int = 0) -> int:
            return x + y + z

        result = await breaker.call(func_with_args, 1, 2, z=3)
        assert result == 6
        assert breaker.stats.successes == 1

    @pytest.mark.asyncio
    async def test_check_state_transition_half_open_no_transition(self):
        """Test _check_state_transition doesn't transition from half-open."""
        breaker = CircuitBreaker("test_breaker")
        breaker.state = CircuitState.HALF_OPEN

        # This should not change state
        breaker._check_state_transition()
        assert breaker.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_check_state_transition_open_before_timeout(self):
        """Test _check_state_transition doesn't transition from open before timeout."""
        config = CircuitBreakerConfig(timeout=1.0)
        breaker = CircuitBreaker("test_breaker", config=config)
        breaker.state = CircuitState.OPEN
        breaker._opened_at = datetime.now()

        # Should not transition yet
        breaker._check_state_transition()
        assert breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_check_state_transition_open_after_timeout(self):
        """Test _check_state_transition transitions from open after timeout."""
        config = CircuitBreakerConfig(timeout=0.1)
        breaker = CircuitBreaker("test_breaker", config=config)
        breaker.state = CircuitState.OPEN
        breaker._opened_at = datetime.now() - timedelta(seconds=0.2)

        breaker._check_state_transition()
        assert breaker.state == CircuitState.HALF_OPEN
        assert breaker.stats.state_changes == 1
        assert breaker.stats.successes == 0  # Reset for half-open

