"""
Circuit Breaker Pattern Implementation

Provides a circuit breaker pattern for handling external service failures gracefully.
"""


import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests immediately
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5  # Number of failures before opening
    success_threshold: int = 2  # Number of successes to close from half-open
    timeout: float = 60.0  # Time in seconds before attempting half-open
    expected_exception: tuple = (Exception,)  # Exceptions that count as failures


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker."""

    failures: int = 0
    successes: int = 0
    total_calls: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    state_changes: int = 0


class CircuitBreaker:
    """
    Circuit breaker for handling external service failures.

    Prevents cascading failures by stopping requests to failing services
    and allowing them time to recover.
    """

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        """
        Initialize circuit breaker.
        
        Args:
            name (str): Name value.
            config (Optional[CircuitBreakerConfig]): Configuration object or settings.
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()
        self._opened_at: Optional[datetime] = None

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with circuit breaker protection.
        
        Args:
            func (Callable): Input parameter for this operation.
            *args (Any): Input parameter for this operation.
            **kwargs (Any): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            RuntimeError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        async with self._lock:
            # Check if circuit should transition
            self._check_state_transition()

            # If circuit is open, reject immediately
            if self.state == CircuitState.OPEN:
                raise RuntimeError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Service unavailable. Last failure: {self.stats.last_failure_time}"
                )

        # Attempt to execute function
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Success - update stats
            async with self._lock:
                self._on_success()

            return result

        except self.config.expected_exception:
            # Failure - update stats
            async with self._lock:
                self._on_failure()
            raise

    def _check_state_transition(self) -> None:
        """
        Check and perform state transitions.
        
        Returns:
            None: Result of the operation.
        """
        if self.state == CircuitState.OPEN:
            # Check if timeout has passed
            if (
                self._opened_at
                and (datetime.now() - self._opened_at).total_seconds() >= self.config.timeout
            ):
                self.state = CircuitState.HALF_OPEN
                self.stats.state_changes += 1
                self.stats.successes = 0  # Reset success count for half-open

        elif self.state == CircuitState.HALF_OPEN:
            # Already in half-open, no transition needed
            pass

    def _on_success(self) -> None:
        """
        Handle successful call.
        
        Returns:
            None: Result of the operation.
        """
        self.stats.successes += 1
        self.stats.total_calls += 1
        self.stats.last_success_time = datetime.now()

        if self.state == CircuitState.HALF_OPEN:
            # If we have enough successes, close the circuit
            if self.stats.successes >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.stats.state_changes += 1
                self.stats.failures = 0  # Reset failure count
                self._opened_at = None

    def _on_failure(self) -> None:
        """
        Handle failed call.
        
        Returns:
            None: Result of the operation.
        """
        self.stats.failures += 1
        self.stats.total_calls += 1
        self.stats.last_failure_time = datetime.now()

        if self.state == CircuitState.CLOSED:
            # Check if we should open the circuit
            if self.stats.failures >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                self.stats.state_changes += 1
                self._opened_at = datetime.now()

        elif self.state == CircuitState.HALF_OPEN:
            # Any failure in half-open immediately opens circuit
            self.state = CircuitState.OPEN
            self.stats.state_changes += 1
            self._opened_at = datetime.now()
            self.stats.successes = 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get circuit breaker statistics.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        return {
            "name": self.name,
            "state": self.state.value,
            "failures": self.stats.failures,
            "successes": self.stats.successes,
            "total_calls": self.stats.total_calls,
            "last_failure_time": (
                self.stats.last_failure_time.isoformat() if self.stats.last_failure_time else None
            ),
            "last_success_time": (
                self.stats.last_success_time.isoformat() if self.stats.last_success_time else None
            ),
            "state_changes": self.stats.state_changes,
            "opened_at": self._opened_at.isoformat() if self._opened_at else None,
        }

    def reset(self) -> None:
        """
        Manually reset circuit breaker to closed state.
        
        Returns:
            None: Result of the operation.
        """
        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats()
        self._opened_at = None
