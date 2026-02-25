"""
Unit Tests for Error Handler Utilities

Tests error handling, retry logic, and fallback mechanisms.
"""

import asyncio
from unittest.mock import patch

import pytest

from src.core.exceptions import SDKError
from src.core.utils.error_handler import (
    ErrorHandler,
    create_error_with_suggestion,
)


class TestLogRetryAttempt:
    """Test _log_retry_attempt function."""

    @patch("src.core.utils.error_handler.logger")
    def test_log_retry_attempt(self, mock_logger):
        """Test _log_retry_attempt logs warning."""
        from src.core.utils.error_handler import _log_retry_attempt

        exception = ValueError("Test error")
        _log_retry_attempt("test_func", 2, 3, exception)

        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        assert "Attempt 2/3" in call_args
        assert "test_func" in call_args
        assert "Test error" in call_args


class TestHandleRetryDelay:
    """Test _handle_retry_delay function."""

    @patch("time.sleep")
    def test_handle_retry_delay(self, mock_sleep):
        """Test _handle_retry_delay with exponential backoff."""
        from src.core.utils.error_handler import _handle_retry_delay

        _handle_retry_delay(2, 1.0)

        mock_sleep.assert_called_once_with(2.0)  # retry_delay * attempt

    @patch("time.sleep")
    def test_handle_retry_delay_custom_delay(self, mock_sleep):
        """Test _handle_retry_delay with custom delay."""
        from src.core.utils.error_handler import _handle_retry_delay

        _handle_retry_delay(3, 0.5)

        mock_sleep.assert_called_once_with(1.5)  # 0.5 * 3


class TestHandleMaxRetriesExceeded:
    """Test _handle_max_retries_exceeded function."""

    @patch("src.core.utils.error_handler.logger")
    def test_handle_max_retries_exceeded(self, mock_logger):
        """Test _handle_max_retries_exceeded logs error."""
        from src.core.utils.error_handler import _handle_max_retries_exceeded

        exception = ValueError("Test error")
        _handle_max_retries_exceeded("test_func", 3, exception)

        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        assert "All 3 attempts failed" in call_args
        assert "test_func" in call_args
        assert "Test error" in call_args


class TestExecuteWithRetry:
    """Test _execute_with_retry function."""

    def test_execute_with_retry_success(self):
        """Test _execute_with_retry with successful execution."""
        from src.core.utils.error_handler import _execute_with_retry

        def test_func(x: int) -> int:
            return x * 2

        result = _execute_with_retry(
            test_func, (5,), {}, max_retries=3, retry_delay=0.01, retryable_exceptions=(ValueError,), on_retry=None
        )

        assert result == 10

    @patch("src.core.utils.error_handler._handle_retry_delay")
    @patch("src.core.utils.error_handler._log_retry_attempt")
    def test_execute_with_retry_retries_then_succeeds(self, mock_log, mock_delay):
        """Test _execute_with_retry with retries then success."""
        from src.core.utils.error_handler import _execute_with_retry

        call_count = 0

        def flaky_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"

        result = _execute_with_retry(
            flaky_func, (), {}, max_retries=3, retry_delay=0.01, retryable_exceptions=(ValueError,), on_retry=None
        )

        assert result == "success"
        assert call_count == 2
        mock_log.assert_called_once()

    @patch("src.core.utils.error_handler._handle_max_retries_exceeded")
    def test_execute_with_retry_max_retries_exceeded(self, mock_max_retries):
        """Test _execute_with_retry when max retries exceeded."""
        from src.core.utils.error_handler import _execute_with_retry

        def always_fails() -> str:
            raise ValueError("Always fails")

        with pytest.raises(ValueError, match="Always fails"):
            _execute_with_retry(
                always_fails, (), {}, max_retries=2, retry_delay=0.01, retryable_exceptions=(ValueError,), on_retry=None
            )

        mock_max_retries.assert_called_once()

    @patch("src.core.utils.error_handler.logger")
    def test_execute_with_retry_non_retryable_exception(self, mock_logger):
        """Test _execute_with_retry with non-retryable exception."""
        from src.core.utils.error_handler import _execute_with_retry

        def raises_runtime_error() -> str:
            raise RuntimeError("Non-retryable")

        with pytest.raises(RuntimeError, match="Non-retryable"):
            _execute_with_retry(
                raises_runtime_error,
                (),
                {},
                max_retries=3,
                retry_delay=0.01,
                retryable_exceptions=(ValueError,),
                on_retry=None,
            )

        mock_logger.error.assert_called_once()

    @patch("src.core.utils.error_handler._handle_retry_delay")
    def test_execute_with_retry_with_on_retry_callback(self, mock_delay):
        """Test _execute_with_retry with on_retry callback."""
        from src.core.utils.error_handler import _execute_with_retry

        call_count = 0
        retry_calls = []

        def on_retry(attempt: int, exception: Exception) -> None:
            retry_calls.append((attempt, exception))

        def flaky_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"

        result = _execute_with_retry(
            flaky_func,
            (),
            {},
            max_retries=3,
            retry_delay=0.01,
            retryable_exceptions=(ValueError,),
            on_retry=on_retry,
        )

        assert result == "success"
        assert len(retry_calls) == 1
        assert retry_calls[0][0] == 1


class TestCallOnRetryAsync:
    """Test _call_on_retry_async function."""

    @pytest.mark.asyncio
    async def test_call_on_retry_async_sync_callback(self):
        """Test _call_on_retry_async with sync callback."""
        from src.core.utils.error_handler import _call_on_retry_async

        callback_called = False

        def sync_callback(attempt: int, exception: Exception) -> None:
            nonlocal callback_called
            callback_called = True

        exception = ValueError("Test error")
        await _call_on_retry_async(sync_callback, 1, exception)

        assert callback_called is True

    @pytest.mark.asyncio
    async def test_call_on_retry_async_async_callback(self):
        """Test _call_on_retry_async with async callback."""
        from src.core.utils.error_handler import _call_on_retry_async

        callback_called = False

        async def async_callback(attempt: int, exception: Exception) -> None:
            nonlocal callback_called
            await asyncio.sleep(0)
            callback_called = True

        exception = ValueError("Test error")
        # Type ignore: _call_on_retry_async handles both sync and async callbacks at runtime
        await _call_on_retry_async(async_callback, 1, exception)  # type: ignore[arg-type]

        assert callback_called is True


class TestHandleRetryableExceptionAsync:
    """Test _handle_retryable_exception_async function."""

    @pytest.mark.asyncio
    @patch("src.core.utils.error_handler._log_retry_attempt")
    async def test_handle_retryable_exception_async_with_retry(self, mock_log):
        """Test _handle_retryable_exception_async when retrying."""
        from src.core.utils.error_handler import _handle_retryable_exception_async

        async def test_func() -> str:
            await asyncio.sleep(0)
            return "test"

        exception = ValueError("Test error")
        await _handle_retryable_exception_async(
            test_func, exception, attempt=0, max_retries=3, retry_delay=0.01, on_retry=None
        )

        mock_log.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.core.utils.error_handler._handle_max_retries_exceeded")
    async def test_handle_retryable_exception_async_max_retries(self, mock_max):
        """Test _handle_retryable_exception_async when max retries reached."""
        from src.core.utils.error_handler import _handle_retryable_exception_async

        async def test_func() -> str:
            await asyncio.sleep(0)
            return "test"

        exception = ValueError("Test error")
        await _handle_retryable_exception_async(
            test_func, exception, attempt=2, max_retries=3, retry_delay=0.01, on_retry=None
        )

        mock_max.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_retryable_exception_async_with_on_retry(self):
        """Test _handle_retryable_exception_async with on_retry callback."""
        from src.core.utils.error_handler import _handle_retryable_exception_async

        callback_called = False

        async def on_retry(attempt: int, exception: Exception) -> None:
            nonlocal callback_called
            await asyncio.sleep(0)
            callback_called = True

        async def test_func() -> str:
            await asyncio.sleep(0)
            return "test"

        exception = ValueError("Test error")
        # Type ignore: _handle_retryable_exception_async handles both sync and async callbacks at runtime
        await _handle_retryable_exception_async(
            test_func, exception, attempt=0, max_retries=3, retry_delay=0.01, on_retry=on_retry  # type: ignore[arg-type]
        )

        assert callback_called is True


class TestExecuteWithRetryAsync:
    """Test _execute_with_retry_async function."""

    @pytest.mark.asyncio
    async def test_execute_with_retry_async_success(self):
        """Test _execute_with_retry_async with successful execution."""
        from src.core.utils.error_handler import _execute_with_retry_async

        async def test_func(x: int) -> int:
            await asyncio.sleep(0)
            return x * 2

        result = await _execute_with_retry_async(
            test_func, (5,), {}, max_retries=3, retry_delay=0.01, retryable_exceptions=(ValueError,), on_retry=None
        )

        assert result == 10

    @pytest.mark.asyncio
    async def test_execute_with_retry_async_retries_then_succeeds(self):
        """Test _execute_with_retry_async with retries then success."""
        from src.core.utils.error_handler import _execute_with_retry_async

        call_count = 0

        async def flaky_func() -> str:
            nonlocal call_count
            await asyncio.sleep(0)
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"

        result = await _execute_with_retry_async(
            flaky_func, (), {}, max_retries=3, retry_delay=0.01, retryable_exceptions=(ValueError,), on_retry=None
        )

        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_execute_with_retry_async_max_retries_exceeded(self):
        """Test _execute_with_retry_async when max retries exceeded."""
        from src.core.utils.error_handler import _execute_with_retry_async

        async def always_fails() -> str:
            await asyncio.sleep(0)
            raise ValueError("Always fails")

        with pytest.raises(ValueError, match="Always fails"):
            await _execute_with_retry_async(
                always_fails, (), {}, max_retries=2, retry_delay=0.01, retryable_exceptions=(ValueError,), on_retry=None
            )

    @pytest.mark.asyncio
    @patch("src.core.utils.error_handler.logger")
    async def test_execute_with_retry_async_non_retryable_exception(self, mock_logger):
        """Test _execute_with_retry_async with non-retryable exception."""
        from src.core.utils.error_handler import _execute_with_retry_async

        async def raises_runtime_error() -> str:
            await asyncio.sleep(0)
            raise RuntimeError("Non-retryable")

        with pytest.raises(RuntimeError, match="Non-retryable"):
            await _execute_with_retry_async(
                raises_runtime_error,
                (),
                {},
                max_retries=3,
                retry_delay=0.01,
                retryable_exceptions=(ValueError,),
                on_retry=None,
            )

        mock_logger.error.assert_called_once()


class TestErrorHandlerHandleWithRetry:
    """Test ErrorHandler.handle_with_retry decorator."""

    def test_handle_with_retry_sync_success(self):
        """Test handle_with_retry with sync function, success."""
        def test_func(x: int) -> int:
            return x * 2

        wrapped_func = ErrorHandler.handle_with_retry(
            test_func, max_retries=3, retry_delay=0.01, retryable_exceptions=(ValueError,)
        )
        result = wrapped_func(5)
        assert result == 10

    def test_handle_with_retry_sync_with_retries(self):
        """Test handle_with_retry with sync function, retries then success."""
        call_count = 0

        def flaky_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"

        wrapped_func = ErrorHandler.handle_with_retry(
            flaky_func, max_retries=3, retry_delay=0.01, retryable_exceptions=(ValueError,)
        )
        result = wrapped_func()
        assert result == "success"
        assert call_count == 2

    def test_handle_with_retry_sync_max_retries(self):
        """Test handle_with_retry with sync function, max retries exceeded."""
        def always_fails() -> str:
            raise ValueError("Always fails")

        wrapped_func = ErrorHandler.handle_with_retry(
            always_fails, max_retries=2, retry_delay=0.01, retryable_exceptions=(ValueError,)
        )
        with pytest.raises(ValueError, match="Always fails"):
            wrapped_func()

    @pytest.mark.asyncio
    async def test_handle_with_retry_async_success(self):
        """Test handle_with_retry with async function, success."""
        async def test_func(x: int) -> int:
            await asyncio.sleep(0)
            return x * 2

        wrapped_func = ErrorHandler.handle_with_retry(
            test_func, max_retries=3, retry_delay=0.01, retryable_exceptions=(ValueError,)
        )
        result = await wrapped_func(5)
        assert result == 10

    @pytest.mark.asyncio
    async def test_handle_with_retry_async_with_retries(self):
        """Test handle_with_retry with async function, retries then success."""
        call_count = 0

        async def flaky_func() -> str:
            nonlocal call_count
            await asyncio.sleep(0)
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"

        wrapped_func = ErrorHandler.handle_with_retry(
            flaky_func, max_retries=3, retry_delay=0.01, retryable_exceptions=(ValueError,)
        )
        result = await wrapped_func()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_handle_with_retry_async_with_on_retry(self):
        """Test handle_with_retry with async function and on_retry callback."""
        call_count = 0
        retry_calls = []

        async def on_retry(attempt: int, exception: Exception) -> None:
            await asyncio.sleep(0)
            retry_calls.append((attempt, exception))

        async def flaky_func() -> str:
            nonlocal call_count
            await asyncio.sleep(0)
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"

        # Type ignore: handle_with_retry handles both sync and async callbacks at runtime
        wrapped_func = ErrorHandler.handle_with_retry(
            flaky_func, max_retries=3, retry_delay=0.01, retryable_exceptions=(ValueError,), on_retry=on_retry  # type: ignore[arg-type]
        )
        result = await wrapped_func()
        assert result == "success"
        assert len(retry_calls) == 1


class TestErrorHandlerHandleWithFallback:
    """Test ErrorHandler.handle_with_fallback decorator."""

    def test_handle_with_fallback_sync_success(self):
        """Test handle_with_fallback with sync function, success."""
        def test_func() -> str:
            return "success"

        wrapped_func = ErrorHandler.handle_with_fallback(
            test_func, fallback_value="fallback", fallback_exceptions=(ValueError,)
        )
        result = wrapped_func()
        assert result == "success"

    def test_handle_with_fallback_sync_uses_fallback(self):
        """Test handle_with_fallback with sync function, uses fallback."""
        def failing_func() -> str:
            raise ValueError("Failed")

        wrapped_func = ErrorHandler.handle_with_fallback(
            failing_func, fallback_value="fallback", fallback_exceptions=(ValueError,)
        )
        result = wrapped_func()
        assert result == "fallback"

    @patch("src.core.utils.error_handler.logger")
    def test_handle_with_fallback_sync_logs_error(self, mock_logger):
        """Test handle_with_fallback logs error when log_error=True."""
        def failing_func() -> str:
            raise ValueError("Failed")

        wrapped_func = ErrorHandler.handle_with_fallback(
            failing_func, fallback_value="fallback", fallback_exceptions=(ValueError,), log_error=True
        )
        result = wrapped_func()
        assert result == "fallback"
        mock_logger.warning.assert_called_once()

    @patch("src.core.utils.error_handler.logger")
    def test_handle_with_fallback_sync_no_log(self, mock_logger):
        """Test handle_with_fallback doesn't log when log_error=False."""
        def failing_func() -> str:
            raise ValueError("Failed")

        wrapped_func = ErrorHandler.handle_with_fallback(
            failing_func, fallback_value="fallback", fallback_exceptions=(ValueError,), log_error=False
        )
        result = wrapped_func()
        assert result == "fallback"
        mock_logger.warning.assert_not_called()

    def test_handle_with_fallback_sync_non_fallback_exception(self):
        """Test handle_with_fallback re-raises non-fallback exceptions."""
        def raises_runtime_error() -> str:
            raise RuntimeError("Non-fallback")

        wrapped_func = ErrorHandler.handle_with_fallback(
            raises_runtime_error, fallback_value="fallback", fallback_exceptions=(ValueError,)
        )
        with pytest.raises(RuntimeError, match="Non-fallback"):
            wrapped_func()

    @pytest.mark.asyncio
    async def test_handle_with_fallback_async_success(self):
        """Test handle_with_fallback with async function, success."""
        async def test_func() -> str:
            await asyncio.sleep(0)
            return "success"

        wrapped_func = ErrorHandler.handle_with_fallback(
            test_func, fallback_value="fallback", fallback_exceptions=(ValueError,)
        )
        # Type ignore: handle_with_fallback returns async wrapper for async functions
        result = await wrapped_func()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_handle_with_fallback_async_uses_fallback(self):
        """Test handle_with_fallback with async function, uses fallback."""
        async def failing_func() -> str:
            await asyncio.sleep(0)
            raise ValueError("Failed")

        wrapped_func = ErrorHandler.handle_with_fallback(
            failing_func, fallback_value="fallback", fallback_exceptions=(ValueError,)
        )
        # Type ignore: handle_with_fallback returns async wrapper for async functions
        result = await wrapped_func() 
        assert result == "fallback"

    @pytest.mark.asyncio
    @patch("src.core.utils.error_handler.logger")
    async def test_handle_with_fallback_async_logs_error(self, mock_logger):
        """Test handle_with_fallback logs error for async function."""
        async def failing_func() -> str:
            await asyncio.sleep(0)
            raise ValueError("Failed")

        wrapped_func = ErrorHandler.handle_with_fallback(
            failing_func, fallback_value="fallback", fallback_exceptions=(ValueError,), log_error=True
        )
        # Type ignore: handle_with_fallback returns async wrapper for async functions
        result = await wrapped_func() 
        assert result == "fallback"
        mock_logger.warning.assert_called_once()


class TestErrorHandlerWrapSDKError:
    """Test ErrorHandler.wrap_sdk_error decorator."""

    def test_wrap_sdk_error_sync_success(self):
        """Test wrap_sdk_error with sync function, success."""
        def test_func() -> str:
            return "success"

        wrapped_func = ErrorHandler.wrap_sdk_error(test_func, SDKError, "Operation failed")
        result = wrapped_func()
        assert result == "success"

    def test_wrap_sdk_error_sync_wraps_exception(self):
        """Test wrap_sdk_error wraps exception in SDK error."""
        def failing_func() -> str:
            raise ValueError("Original error")

        # SDKError only accepts message and original_error, so don't pass kwargs
        wrapped_func = ErrorHandler.wrap_sdk_error(failing_func, SDKError, "Operation failed")
        with pytest.raises(SDKError) as exc_info:
            wrapped_func()

        assert "Operation failed" in str(exc_info.value)
        assert "Original error" in str(exc_info.value)
        assert exc_info.value.original_error is not None
        assert isinstance(exc_info.value.original_error, ValueError)

    def test_wrap_sdk_error_sync_preserves_sdk_error(self):
        """Test wrap_sdk_error re-raises SDK errors as-is."""
        original_error = SDKError("Original SDK error")

        def raises_sdk_error() -> str:
            raise original_error

        wrapped_func = ErrorHandler.wrap_sdk_error(raises_sdk_error, SDKError, "Operation failed")
        with pytest.raises(SDKError) as exc_info:
            wrapped_func()

        assert exc_info.value is original_error

    @pytest.mark.asyncio
    async def test_wrap_sdk_error_async_success(self):
        """Test wrap_sdk_error with async function, success."""
        async def test_func() -> str:
            await asyncio.sleep(0)
            return "success"

        wrapped_func = ErrorHandler.wrap_sdk_error(test_func, SDKError, "Operation failed")
        result = await wrapped_func()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_wrap_sdk_error_async_preserves_sdk_error(self):
        """Test wrap_sdk_error doesn't wrap SDKError exceptions (lines 326-328)."""
        async def raises_sdk_error() -> str:
            await asyncio.sleep(0)
            raise SDKError("Already an SDK error")

        wrapped_func = ErrorHandler.wrap_sdk_error(
            raises_sdk_error, SDKError, "Operation failed"
        )
        with pytest.raises(SDKError, match="Already an SDK error"):
            await wrapped_func()

    def test_wrap_sdk_error_sync_preserves_sdk_error_additional(self):
        """Test wrap_sdk_error doesn't wrap SDKError exceptions (lines 343-345)."""
        def raises_sdk_error() -> str:
            raise SDKError("Already an SDK error")

        wrapped_func = ErrorHandler.wrap_sdk_error(
            raises_sdk_error, SDKError, "Operation failed"
        )
        with pytest.raises(SDKError, match="Already an SDK error"):
            wrapped_func()

    def test_wrap_exception(self):
        """Test _wrap_exception method (lines 308-314)."""
        original_error = ValueError("Original error")
        wrapped = ErrorHandler._wrap_exception(
            SDKError, "Operation failed", original_error
        )
        
        assert isinstance(wrapped, SDKError)
        assert "Operation failed" in wrapped.message
        assert wrapped.original_error == original_error

    def test_handle_with_fallback_sync_no_log(self):
        """Test handle_with_fallback with log_error=False (lines 273-275)."""
        from unittest.mock import patch
        
        def failing_func() -> str:
            raise ValueError("Failed")

        wrapped_func = ErrorHandler.handle_with_fallback(
            failing_func, fallback_value="fallback", fallback_exceptions=(ValueError,), log_error=False
        )
        
        with patch("src.core.utils.error_handler.logger") as mock_logger:
            result = wrapped_func()
            assert result == "fallback"
            mock_logger.warning.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_with_fallback_async_no_log(self):
        """Test handle_with_fallback async with log_error=False (lines 255-257)."""
        from unittest.mock import patch
        
        async def failing_func() -> str:
            await asyncio.sleep(0)
            raise ValueError("Failed")

        wrapped_func = ErrorHandler.handle_with_fallback(
            failing_func, fallback_value="fallback", fallback_exceptions=(ValueError,), log_error=False
        )
        
        # Type assertion: wrapped_func is awaitable for async functions
        from typing import Awaitable, Callable, cast
        wrapped_func_async = cast(Callable[[], Awaitable[str]], wrapped_func)
        
        with patch("src.core.utils.error_handler.logger") as mock_logger:
            result = await wrapped_func_async()
            assert result == "fallback"
            mock_logger.warning.assert_not_called()

    def test_execute_with_retry_unexpected_error_path(self):
        """Test _execute_with_retry success path (lines 97-100)."""
        from src.core.utils.error_handler import _execute_with_retry
        
        def test_func() -> str:
            return "success"
        
        result = _execute_with_retry(
            test_func, (), {}, max_retries=1, retry_delay=0.01, 
            retryable_exceptions=(ValueError,), on_retry=None
        )
        assert result == "success"

    @pytest.mark.asyncio
    async def test_execute_with_retry_async_success_path(self):
        """Test _execute_with_retry_async success path (lines 177-180)."""
        from src.core.utils.error_handler import _execute_with_retry_async
        
        async def test_func() -> str:
            await asyncio.sleep(0)
            return "success"
        
        result = await _execute_with_retry_async(
            test_func, (), {}, max_retries=1, retry_delay=0.01,
            retryable_exceptions=(ValueError,), on_retry=None
        )
        assert result == "success"
        async def failing_func() -> str:
            await asyncio.sleep(0)
            raise ValueError("Original error")

        # SDKError only accepts message and original_error, so don't pass kwargs
        wrapped_func = ErrorHandler.wrap_sdk_error(failing_func, SDKError, "Operation failed")
        with pytest.raises(SDKError) as exc_info:
            await wrapped_func()

        assert "Operation failed" in str(exc_info.value)
        assert "Original error" in str(exc_info.value)
        assert exc_info.value.original_error is not None


class TestCreateErrorWithSuggestion:
    """Test create_error_with_suggestion function."""

    def test_create_error_with_suggestion_basic(self):
        """Test create_error_with_suggestion with basic parameters."""
        error = create_error_with_suggestion(SDKError, "Operation failed", "Try again later")

        assert isinstance(error, SDKError)
        assert "Operation failed" in str(error)
        assert "💡 Suggestion: Try again later" in str(error)
        assert error.original_error is None

    def test_create_error_with_suggestion_with_original_error(self):
        """Test create_error_with_suggestion with original error."""
        original = ValueError("Original error")
        error = create_error_with_suggestion(
            SDKError, "Operation failed", "Try again later", original_error=original
        )

        assert isinstance(error, SDKError)
        assert error.original_error == original
        assert "Operation failed" in str(error)
        assert "💡 Suggestion: Try again later" in str(error)

    def test_create_error_with_suggestion_with_original_error_and_kwargs(self):
        """Test create_error_with_suggestion with original error."""
        original = ValueError("Original error")
        # SDKError only accepts message and original_error, so kwargs are ignored
        error = create_error_with_suggestion(
            SDKError, "Operation failed", "Try again later", original_error=original
        )

        assert isinstance(error, SDKError)
        assert "Operation failed" in str(error)
        assert "💡 Suggestion: Try again later" in str(error)
        assert error.original_error == original

