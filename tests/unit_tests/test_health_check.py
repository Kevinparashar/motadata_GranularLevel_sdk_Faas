"""
Unit Tests for Health Check System

Tests health check functionality for monitoring component performance.
"""

import asyncio
from datetime import datetime

import pytest

from src.core.utils.health_check import (
    HealthCheck,
    HealthCheckResult,
    HealthStatus,
    _create_error_result,
    _determine_overall_status,
    _normalize_check_result,
)


class TestHealthStatus:
    """Test HealthStatus enum."""

    def test_health_status_values(self):
        """Test HealthStatus enum values."""
        assert HealthStatus.HEALTHY == "healthy"
        assert HealthStatus.DEGRADED == "degraded"
        assert HealthStatus.UNHEALTHY == "unhealthy"
        assert HealthStatus.UNKNOWN == "unknown"


class TestHealthCheckResult:
    """Test HealthCheckResult dataclass."""

    def test_health_check_result_defaults(self):
        """Test HealthCheckResult with default values."""
        result = HealthCheckResult(status=HealthStatus.HEALTHY)
        assert result.status == HealthStatus.HEALTHY
        assert result.message == ""
        assert result.details == {}
        assert isinstance(result.timestamp, datetime)
        assert result.response_time_ms is None

    def test_health_check_result_custom(self):
        """Test HealthCheckResult with custom values."""
        now = datetime.now()
        result = HealthCheckResult(
            status=HealthStatus.DEGRADED,
            message="Service is slow",
            details={"latency": 500},
            timestamp=now,
            response_time_ms=250.5,
        )
        assert result.status == HealthStatus.DEGRADED
        assert result.message == "Service is slow"
        assert result.details == {"latency": 500}
        assert result.timestamp == now
        assert abs(result.response_time_ms - 250.5) < 0.001


class TestNormalizeCheckResult:
    """Test _normalize_check_result function."""

    def test_normalize_check_result_bool_true(self):
        """Test _normalize_check_result with True."""
        result = _normalize_check_result(True)
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "Check passed"

    def test_normalize_check_result_bool_false(self):
        """Test _normalize_check_result with False."""
        result = _normalize_check_result(False)
        assert result.status == HealthStatus.UNHEALTHY
        assert result.message == "Check failed"

    def test_normalize_check_result_health_check_result(self):
        """Test _normalize_check_result with HealthCheckResult."""
        original = HealthCheckResult(
            status=HealthStatus.DEGRADED, message="Custom message", details={"key": "value"}
        )
        result = _normalize_check_result(original)
        assert result is original

    def test_normalize_check_result_other_type(self):
        """Test _normalize_check_result with other type."""
        result = _normalize_check_result("some value")
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "Check completed"


class TestDetermineOverallStatus:
    """Test _determine_overall_status function."""

    def test_determine_overall_status_empty(self):
        """Test _determine_overall_status with empty results."""
        status, message = _determine_overall_status([])
        assert status == HealthStatus.UNKNOWN
        assert message == "No health checks configured"

    def test_determine_overall_status_healthy(self):
        """Test _determine_overall_status with all healthy."""
        results = [
            HealthCheckResult(status=HealthStatus.HEALTHY, message="OK"),
            HealthCheckResult(status=HealthStatus.HEALTHY, message="OK"),
        ]
        status, message = _determine_overall_status(results)
        assert status == HealthStatus.HEALTHY
        assert message == "OK"

    def test_determine_overall_status_degraded(self):
        """Test _determine_overall_status with degraded."""
        results = [
            HealthCheckResult(status=HealthStatus.HEALTHY, message="OK"),
            HealthCheckResult(status=HealthStatus.DEGRADED, message="Slow"),
        ]
        status, message = _determine_overall_status(results)
        assert status == HealthStatus.DEGRADED
        assert message == "Slow"

    def test_determine_overall_status_unhealthy(self):
        """Test _determine_overall_status with unhealthy."""
        results = [
            HealthCheckResult(status=HealthStatus.HEALTHY, message="OK"),
            HealthCheckResult(status=HealthStatus.DEGRADED, message="Slow"),
            HealthCheckResult(status=HealthStatus.UNHEALTHY, message="Failed"),
        ]
        status, message = _determine_overall_status(results)
        assert status == HealthStatus.UNHEALTHY
        assert message == "Failed"

    def test_determine_overall_status_unknown(self):
        """Test _determine_overall_status with unknown."""
        results = [
            HealthCheckResult(status=HealthStatus.UNKNOWN, message="Unknown"),
        ]
        status, message = _determine_overall_status(results)
        assert status == HealthStatus.UNKNOWN
        assert message == "Unknown"


class TestCreateErrorResult:
    """Test _create_error_result function."""

    def test_create_error_result(self):
        """Test _create_error_result with exception."""
        exception = ValueError("Test error")
        result = _create_error_result(exception)
        assert result.status == HealthStatus.UNHEALTHY
        assert "Test error" in result.message
        assert result.details["error"] == "Test error"


class TestHealthCheck:
    """Test HealthCheck class."""

    def test_health_check_init(self):
        """Test HealthCheck initialization."""
        check = HealthCheck("test_service")
        assert check.name == "test_service"
        assert check.status == HealthStatus.UNKNOWN
        assert check.last_check is None
        assert check.last_result is None
        assert check.check_history == []
        assert check.max_history == 100
        assert check._check_functions == []

    def test_add_check(self):
        """Test add_check method."""
        check = HealthCheck("test_service")

        def check_func() -> bool:
            return True

        check.add_check(check_func)
        assert len(check._check_functions) == 1
        assert check._check_functions[0] == check_func

    @pytest.mark.asyncio
    async def test_run_single_check_sync_success(self):
        """Test _run_single_check with successful sync function."""
        check = HealthCheck("test_service")

        def check_func() -> bool:
            return True

        result = await check._run_single_check(check_func)
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "Check passed"

    @pytest.mark.asyncio
    async def test_run_single_check_sync_failure(self):
        """Test _run_single_check with failing sync function."""
        check = HealthCheck("test_service")

        def check_func() -> bool:
            return False

        result = await check._run_single_check(check_func)
        assert result.status == HealthStatus.UNHEALTHY
        assert result.message == "Check failed"

    @pytest.mark.asyncio
    async def test_run_single_check_async_success(self):
        """Test _run_single_check with successful async function."""
        check = HealthCheck("test_service")

        async def check_func() -> HealthCheckResult:
            await asyncio.sleep(0)
            return HealthCheckResult(status=HealthStatus.HEALTHY, message="OK")

        result = await check._run_single_check(check_func)
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "OK"

    @pytest.mark.asyncio
    async def test_run_single_check_async_failure(self):
        """Test _run_single_check with failing async function."""
        check = HealthCheck("test_service")

        async def check_func() -> HealthCheckResult:
            await asyncio.sleep(0)
            return HealthCheckResult(status=HealthStatus.UNHEALTHY, message="Failed")

        result = await check._run_single_check(check_func)
        assert result.status == HealthStatus.UNHEALTHY
        assert result.message == "Failed"

    @pytest.mark.asyncio
    async def test_run_single_check_exception(self):
        """Test _run_single_check with exception."""
        check = HealthCheck("test_service")

        def check_func() -> bool:
            raise ValueError("Test error")

        result = await check._run_single_check(check_func)
        assert result.status == HealthStatus.UNHEALTHY
        assert "Test error" in result.message
        assert result.details["error"] == "Test error"

    @pytest.mark.asyncio
    async def test_check_no_functions(self):
        """Test check with no check functions."""
        check = HealthCheck("test_service")
        result = await check.check()

        assert result.status == HealthStatus.UNKNOWN
        assert result.message == "No health checks configured"
        assert check.status == HealthStatus.UNKNOWN
        assert check.last_check is not None
        assert check.last_result == result
        assert len(check.check_history) == 1

    @pytest.mark.asyncio
    async def test_check_single_function_success(self):
        """Test check with single successful function."""
        check = HealthCheck("test_service")

        def check_func() -> bool:
            return True

        check.add_check(check_func)
        result = await check.check()

        assert result.status == HealthStatus.HEALTHY
        assert result.message == "Check passed"
        assert result.response_time_ms is not None
        assert check.status == HealthStatus.HEALTHY
        assert check.last_check is not None
        assert len(check.check_history) == 1

    @pytest.mark.asyncio
    async def test_check_multiple_functions(self):
        """Test check with multiple functions."""
        check = HealthCheck("test_service")

        def check_func1() -> bool:
            return True

        def check_func2() -> bool:
            return True

        check.add_check(check_func1)
        check.add_check(check_func2)
        result = await check.check()

        assert result.status == HealthStatus.HEALTHY
        assert len(result.details["checks"]) == 2
        assert check.status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_check_with_mixed_results(self):
        """Test check with mixed results."""
        check = HealthCheck("test_service")

        def check_func1() -> bool:
            return True

        def check_func2() -> bool:
            return False

        check.add_check(check_func1)
        check.add_check(check_func2)
        result = await check.check()

        assert result.status == HealthStatus.UNHEALTHY
        assert check.status == HealthStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_check_history_limit(self):
        """Test check history limit."""
        check = HealthCheck("test_service")
        check.max_history = 2

        def check_func() -> bool:
            return True

        check.add_check(check_func)

        # Run checks to exceed history limit
        for _ in range(3):
            await check.check()

        assert len(check.check_history) == 2
        assert check.check_history[0].status == HealthStatus.HEALTHY
        assert check.check_history[1].status == HealthStatus.HEALTHY

    def test_format_last_result_with_result(self):
        """Test _format_last_result with last result."""
        check = HealthCheck("test_service")
        check.last_result = HealthCheckResult(
            status=HealthStatus.HEALTHY,
            message="OK",
            response_time_ms=100.5,
            details={"key": "value"},
        )

        formatted = check._format_last_result()
        assert formatted is not None
        assert formatted["status"] == "healthy"
        assert formatted["message"] == "OK"
        assert abs(formatted["response_time_ms"] - 100.5) < 0.001
        assert formatted["details"] == {"key": "value"}

    def test_format_last_result_without_result(self):
        """Test _format_last_result without last result."""
        check = HealthCheck("test_service")
        formatted = check._format_last_result()
        assert formatted is None

    def test_get_health_with_result(self):
        """Test get_health with last result."""
        check = HealthCheck("test_service")
        check.status = HealthStatus.HEALTHY
        check.last_check = datetime.now()
        check.last_result = HealthCheckResult(
            status=HealthStatus.HEALTHY, message="OK", response_time_ms=100.0
        )
        check.check_history.append(check.last_result)

        health = check.get_health()
        assert health["name"] == "test_service"
        assert health["status"] == "healthy"
        assert health["last_check"] is not None
        assert health["last_result"] is not None
        assert health["history_count"] == 1

    def test_get_health_without_result(self):
        """Test get_health without last result."""
        check = HealthCheck("test_service")
        health = check.get_health()
        assert health["name"] == "test_service"
        assert health["status"] == "unknown"
        assert health["last_check"] is None
        assert health["last_result"] is None
        assert health["history_count"] == 0

