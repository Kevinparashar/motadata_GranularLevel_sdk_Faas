"""
Shared Error Handling Utilities

Provides consistent error handling patterns across all SDK components.
"""

import logging
from functools import wraps
from typing import Any, Callable, Optional, Type, TypeVar

from ..exceptions import SDKError

logger = logging.getLogger(__name__)

T = TypeVar("T")
E = TypeVar("E", bound=Exception)


def _log_retry_attempt(func_name: str, attempt: int, max_retries: int, exception: Exception) -> None:
    """Log retry attempt."""
    logger.warning(
        f"Attempt {attempt}/{max_retries} failed for {func_name}: {str(exception)}. Retrying..."
    )


def _handle_retry_delay(attempt: int, retry_delay: float) -> None:
    """Handle retry delay with exponential backoff."""
    import time
    time.sleep(retry_delay * attempt)


def _handle_max_retries_exceeded(func_name: str, max_retries: int, exception: Exception) -> None:
    """Log when max retries exceeded."""
    logger.error(f"All {max_retries} attempts failed for {func_name}: {str(exception)}")


def _execute_with_retry(
    func: Callable[..., T],
    args: tuple,
    kwargs: dict,
    max_retries: int,
    retry_delay: float,
    retryable_exceptions: tuple[Type[Exception], ...],
    on_retry: Optional[Callable[[int, Exception], None]],
) -> T:
    """Execute function with retry logic."""
    last_exception: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except retryable_exceptions as e:
            last_exception = e
            if attempt < max_retries - 1:
                _log_retry_attempt(func.__name__, attempt + 1, max_retries, e)
                if on_retry:
                    on_retry(attempt + 1, e)
                _handle_retry_delay(attempt + 1, retry_delay)
            else:
                _handle_max_retries_exceeded(func.__name__, max_retries, e)
        except Exception as e:
            # Non-retryable exception - re-raise immediately
            logger.error(f"Non-retryable error in {func.__name__}: {str(e)}")
            raise

    # This should never be reached, but type checker needs it
    if last_exception:
        raise last_exception
    raise RuntimeError("Unexpected error in retry logic")


class ErrorHandler:
    """
    Standardized error handler for SDK components.

    Provides consistent error handling, logging, and recovery strategies.
    """

    @staticmethod
    def handle_with_retry(
        func: Callable[..., T],
        max_retries: int = 3,
        retry_delay: float = 1.0,
        retryable_exceptions: tuple[Type[Exception], ...] = (Exception,),
        on_retry: Optional[Callable[[int, Exception], None]] = None,
    ) -> Callable[..., T]:
        """
        Decorator for retry logic with consistent error handling.

        Args:
            func: Function to wrap
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries (seconds)
            retryable_exceptions: Exceptions that should trigger retry
            on_retry: Optional callback on retry (receives attempt number and exception)

        Returns:
            Wrapped function with retry logic
        """

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            return _execute_with_retry(
                func, args, kwargs, max_retries, retry_delay, retryable_exceptions, on_retry
            )

        return sync_wrapper

    @staticmethod
    def handle_with_fallback(
        func: Callable[..., T],
        fallback_value: T,
        fallback_exceptions: tuple[Type[Exception], ...] = (Exception,),
        log_error: bool = True,
    ) -> Callable[..., T]:
        """
        Decorator for fallback value on error.

        Args:
            func: Function to wrap
            fallback_value: Value to return on error
            fallback_exceptions: Exceptions that should trigger fallback
            log_error: Whether to log errors

        Returns:
            Wrapped function with fallback logic
        """

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except fallback_exceptions as e:
                if log_error:
                    logger.warning(f"Error in {func.__name__}: {str(e)}. Using fallback value.")
                return fallback_value

        return wrapper

    @staticmethod
    def wrap_sdk_error(
        func: Callable[..., T], error_class: Type[SDKError], error_message: str, **error_kwargs: Any
    ) -> Callable[..., T]:
        """
        Wrap exceptions in SDK error hierarchy.

        Args:
            func: Function to wrap
            error_class: SDK error class to raise
            error_message: Base error message
            **error_kwargs: Additional error attributes

        Returns:
            Wrapped function that raises SDK errors
        """

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except SDKError:
                # Re-raise SDK errors as-is
                raise
            except Exception as e:
                # Wrap other exceptions
                raise error_class(
                    message=f"{error_message}: {str(e)}", original_error=e, **error_kwargs
                )

        return wrapper


def create_error_with_suggestion(
    error_class: Type[SDKError],
    message: str,
    suggestion: str,
    original_error: Optional[Exception] = None,
    **kwargs: Any,
) -> SDKError:
    """
    Create an error with actionable suggestion.

    Args:
        error_class: SDK error class
        message: Error message
        suggestion: Actionable suggestion for user
        original_error: Original exception
        **kwargs: Additional error attributes

    Returns:
        SDKError instance with suggestion
    """
    full_message = f"{message}\n💡 Suggestion: {suggestion}"
    return error_class(message=full_message, original_error=original_error, **kwargs)
