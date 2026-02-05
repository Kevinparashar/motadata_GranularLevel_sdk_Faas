"""
Shared Error Handling Utilities

Provides consistent error handling patterns across all SDK components.
"""


import asyncio
import logging
from functools import wraps
from typing import Any, Awaitable, Callable, Optional, Type, TypeVar, cast

from ..exceptions import SDKError

logger = logging.getLogger(__name__)

T = TypeVar("T")
E = TypeVar("E", bound=Exception)


def _log_retry_attempt(func_name: str, attempt: int, max_retries: int, exception: Exception) -> None:
    """
    Log retry attempt.
    
    Args:
        func_name (str): Input parameter for this operation.
        attempt (int): Input parameter for this operation.
        max_retries (int): Input parameter for this operation.
        exception (Exception): Input parameter for this operation.
    
    Returns:
        None: Result of the operation.
    """
    logger.warning(
        f"Attempt {attempt}/{max_retries} failed for {func_name}: {str(exception)}. Retrying..."
    )


def _handle_retry_delay(attempt: int, retry_delay: float) -> None:
    """
    Handle retry delay with exponential backoff.
    
    Args:
        attempt (int): Input parameter for this operation.
        retry_delay (float): Input parameter for this operation.
    
    Returns:
        None: Result of the operation.
    """
    import time
    time.sleep(retry_delay * attempt)


def _handle_max_retries_exceeded(func_name: str, max_retries: int, exception: Exception) -> None:
    """
    Log when max retries exceeded.
    
    Args:
        func_name (str): Input parameter for this operation.
        max_retries (int): Input parameter for this operation.
        exception (Exception): Input parameter for this operation.
    
    Returns:
        None: Result of the operation.
    """
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
    """
    Execute function with retry logic (synchronous).
    
    Args:
        func (Callable[..., T]): Input parameter for this operation.
        args (tuple): Input parameter for this operation.
        kwargs (dict): Input parameter for this operation.
        max_retries (int): Input parameter for this operation.
        retry_delay (float): Input parameter for this operation.
        retryable_exceptions (tuple[Type[Exception], ...]): Input parameter for this operation.
        on_retry (Optional[Callable[[int, Exception], None]]): Input parameter for this operation.
    
    Returns:
        T: Result of the operation.
    
    Raises:
        RuntimeError: Raised when this function detects an invalid state or when an underlying call fails.
        last_exception: Raised when this function detects an invalid state or when an underlying call fails.
    """
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


async def _call_on_retry_async(
    on_retry: Callable[[int, Exception], None], attempt: int, exception: Exception
) -> None:
    """Call on_retry callback, handling both sync and async callbacks."""
    if asyncio.iscoroutinefunction(on_retry):
        await on_retry(attempt, exception)
    else:
        on_retry(attempt, exception)


async def _handle_retryable_exception_async(
    func: Callable[..., Any],
    exception: Exception,
    attempt: int,
    max_retries: int,
    retry_delay: float,
    on_retry: Optional[Callable[[int, Exception], None]],
) -> None:
    """Handle retryable exception in async context."""
    if attempt < max_retries - 1:
        _log_retry_attempt(func.__name__, attempt + 1, max_retries, exception)
        if on_retry:
            await _call_on_retry_async(on_retry, attempt + 1, exception)
        await asyncio.sleep(retry_delay * (attempt + 1))
    else:
        _handle_max_retries_exceeded(func.__name__, max_retries, exception)


async def _execute_with_retry_async(
    func: Callable[..., Any],
    args: tuple,
    kwargs: dict,
    max_retries: int,
    retry_delay: float,
    retryable_exceptions: tuple[Type[Exception], ...],
    on_retry: Optional[Callable[[int, Exception], None]],
) -> Any:
    """
    Execute async function with retry logic.
    
    Args:
        func (Callable[..., Any]): Input parameter for this operation.
        args (tuple): Input parameter for this operation.
        kwargs (dict): Input parameter for this operation.
        max_retries (int): Input parameter for this operation.
        retry_delay (float): Input parameter for this operation.
        retryable_exceptions (tuple[Type[Exception], ...]): Input parameter for this operation.
        on_retry (Optional[Callable[[int, Exception], None]]): Input parameter for this operation.
    
    Returns:
        Any: Result of the operation.
    
    Raises:
        RuntimeError: Raised when this function detects an invalid state or when an underlying call fails.
        last_exception: Raised when this function detects an invalid state or when an underlying call fails.
    """
    last_exception: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except retryable_exceptions as e:
            last_exception = e
            await _handle_retryable_exception_async(
                func, e, attempt, max_retries, retry_delay, on_retry
            )
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
        Supports both sync and async functions.
        
        Args:
            func (Callable[..., T]): Input parameter for this operation.
            max_retries (int): Input parameter for this operation.
            retry_delay (float): Input parameter for this operation.
            retryable_exceptions (tuple[Type[Exception], ...]): Input parameter for this operation.
            on_retry (Optional[Callable[[int, Exception], None]]): Input parameter for this operation.
        
        Returns:
            Callable[..., T]: Result of the operation.
        """
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                return await _execute_with_retry_async(
                    func, args, kwargs, max_retries, retry_delay, retryable_exceptions, on_retry
                )
            return async_wrapper  # type: ignore[return-value]
        else:
            @wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> T:
                return _execute_with_retry(
                    func, args, kwargs, max_retries, retry_delay, retryable_exceptions, on_retry
                )
            return sync_wrapper

    @staticmethod
    def _create_async_fallback_wrapper(
        func: Callable[..., T],
        fallback_value: T,
        fallback_exceptions: tuple[Type[Exception], ...],
        log_error: bool,
    ) -> Callable[..., Awaitable[T]]:
        """Create async wrapper for fallback decorator."""
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                async_func = cast(Callable[..., Awaitable[T]], func)
                return await async_func(*args, **kwargs)
            except fallback_exceptions as e:
                if log_error:
                    logger.warning(f"Error in {func.__name__}: {str(e)}. Using fallback value.")
                return fallback_value
        return async_wrapper

    @staticmethod
    def _create_sync_fallback_wrapper(
        func: Callable[..., T],
        fallback_value: T,
        fallback_exceptions: tuple[Type[Exception], ...],
        log_error: bool,
    ) -> Callable[..., T]:
        """Create sync wrapper for fallback decorator."""
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except fallback_exceptions as e:
                if log_error:
                    logger.warning(f"Error in {func.__name__}: {str(e)}. Using fallback value.")
                return fallback_value
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
        Supports both sync and async functions.
        
        Args:
            func (Callable[..., T]): Input parameter for this operation.
            fallback_value (T): Input parameter for this operation.
            fallback_exceptions (tuple[Type[Exception], ...]): Input parameter for this operation.
            log_error (bool): Input parameter for this operation.
        
        Returns:
            Callable[..., T]: Result of the operation.
        """
        if asyncio.iscoroutinefunction(func):
            return cast(Callable[..., T], ErrorHandler._create_async_fallback_wrapper(
                func, fallback_value, fallback_exceptions, log_error
            ))
        else:
            return ErrorHandler._create_sync_fallback_wrapper(
                func, fallback_value, fallback_exceptions, log_error
            )

    @staticmethod
    def _wrap_exception(
        error_class: Type[SDKError], error_message: str, exception: Exception, **error_kwargs: Any
    ) -> SDKError:
        """Wrap an exception in SDK error hierarchy."""
        return error_class(
            message=f"{error_message}: {str(exception)}", original_error=exception, **error_kwargs
        )

    @staticmethod
    def _create_async_error_wrapper(
        func: Callable[..., T], error_class: Type[SDKError], error_message: str, **error_kwargs: Any
    ) -> Callable[..., Awaitable[T]]:
        """Create async wrapper for error wrapping decorator."""
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                async_func = cast(Callable[..., Awaitable[T]], func)
                return await async_func(*args, **kwargs)
            except SDKError:
                # Re-raise SDK errors as-is
                raise
            except Exception as e:
                # Wrap other exceptions
                raise ErrorHandler._wrap_exception(error_class, error_message, e, **error_kwargs)
        return async_wrapper

    @staticmethod
    def _create_sync_error_wrapper(
        func: Callable[..., T], error_class: Type[SDKError], error_message: str, **error_kwargs: Any
    ) -> Callable[..., T]:
        """Create sync wrapper for error wrapping decorator."""
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except SDKError:
                # Re-raise SDK errors as-is
                raise
            except Exception as e:
                # Wrap other exceptions
                raise ErrorHandler._wrap_exception(error_class, error_message, e, **error_kwargs)
        return sync_wrapper

    @staticmethod
    def wrap_sdk_error(
        func: Callable[..., T], error_class: Type[SDKError], error_message: str, **error_kwargs: Any
    ) -> Callable[..., T]:
        """
        Wrap exceptions in SDK error hierarchy.
        Supports both sync and async functions.
        
        Args:
            func (Callable[..., T]): Input parameter for this operation.
            error_class (Type[SDKError]): Input parameter for this operation.
            error_message (str): Input parameter for this operation.
            **error_kwargs (Any): Input parameter for this operation.
        
        Returns:
            Callable[..., T]: Result of the operation.
        
        Raises:
            error_class: Raised when this function detects an invalid state or when an underlying call fails.
        """
        if asyncio.iscoroutinefunction(func):
            return cast(Callable[..., T], ErrorHandler._create_async_error_wrapper(
                func, error_class, error_message, **error_kwargs
            ))
        else:
            return ErrorHandler._create_sync_error_wrapper(
                func, error_class, error_message, **error_kwargs
            )


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
