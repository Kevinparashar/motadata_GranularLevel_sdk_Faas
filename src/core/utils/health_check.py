"""
Health Check System

Provides health check functionality for monitoring component performance and availability.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional



class HealthStatus(str, Enum):
    """Health status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    status: HealthStatus
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    response_time_ms: Optional[float] = None


def _normalize_check_result(result: Any) -> HealthCheckResult:
    """Normalize check result to HealthCheckResult."""
    if isinstance(result, bool):
        return HealthCheckResult(
            status=HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY,
            message="Check passed" if result else "Check failed",
        )
    elif not isinstance(result, HealthCheckResult):
        return HealthCheckResult(status=HealthStatus.HEALTHY, message="Check completed")
    return result


def _determine_overall_status(results: List[HealthCheckResult]) -> tuple[HealthStatus, str]:
    """Determine overall health status from individual results."""
    if not results:
        return HealthStatus.UNKNOWN, "No health checks configured"
    
    # Worst status wins
    status_priority = {
        HealthStatus.UNHEALTHY: 3,
        HealthStatus.DEGRADED: 2,
        HealthStatus.HEALTHY: 1,
        HealthStatus.UNKNOWN: 0,
    }
    worst_result = max(results, key=lambda r: status_priority.get(r.status, 0))
    return worst_result.status, worst_result.message


def _create_error_result(exception: Exception) -> HealthCheckResult:
    """Create error health check result from exception."""
    return HealthCheckResult(
        status=HealthStatus.UNHEALTHY,
        message=f"Check failed: {str(exception)}",
        details={"error": str(exception)},
    )


class HealthCheck:
    """
    Health check for monitoring component health.

    Tracks health status, response times, and provides detailed health information.
    """

    def __init__(self, name: str):
        """
        Initialize health check.

        Args:
            name: Name of the component being monitored
        """
        self.name = name
        self.status = HealthStatus.UNKNOWN
        self.last_check: Optional[datetime] = None
        self.last_result: Optional[HealthCheckResult] = None
        self.check_history: List[HealthCheckResult] = []
        self.max_history = 100
        self._check_functions: List[Callable] = []

    def add_check(self, check_func: Callable) -> None:
        """
        Add a health check function.

        Args:
            check_func: Function that returns HealthCheckResult or bool
        """
        self._check_functions.append(check_func)

    async def _run_single_check(self, check_func: Callable) -> HealthCheckResult:
        """Run a single health check function."""
        try:
            if asyncio.iscoroutinefunction(check_func):
                result = await check_func()
            else:
                result = check_func()
            return _normalize_check_result(result)
        except Exception as e:
            return _create_error_result(e)

    async def check(self) -> HealthCheckResult:
        """
        Perform health check.

        Returns:
            HealthCheckResult with current health status
        """
        import time

        start_time = time.time()

        # Run all check functions
        results = [await self._run_single_check(check_func) for check_func in self._check_functions]

        # Determine overall status
        status, message = _determine_overall_status(results)
        response_time_ms = (time.time() - start_time) * 1000

        result = HealthCheckResult(
            status=status,
            message=message,
            details={"checks": [r.details for r in results]},
            response_time_ms=response_time_ms,
        )

        self.status = status
        self.last_check = datetime.now()
        self.last_result = result

        # Add to history
        self.check_history.append(result)
        if len(self.check_history) > self.max_history:
            self.check_history.pop(0)

        return result

    def _format_last_result(self) -> Optional[Dict[str, Any]]:
        """Format last result for health status response."""
        if not self.last_result:
            return None
        
        return {
            "status": self.last_result.status.value,
            "message": self.last_result.message,
            "response_time_ms": self.last_result.response_time_ms,
            "details": self.last_result.details,
        }

    def get_health(self) -> Dict[str, Any]:
        """Get current health status."""
        return {
            "name": self.name,
            "status": self.status.value,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "last_result": self._format_last_result(),
            "history_count": len(self.check_history),
        }
