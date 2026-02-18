"""
Type Helper Utilities

Provides type aliases and helpers to reduce Any usage and improve type safety.
"""


from typing import Any, Dict, Optional, TypeVar

from typing_extensions import Protocol

# Type aliases for common patterns
ConfigDict = Dict[str, Any]
MetadataDict = Dict[str, Any]
ParametersDict = Dict[str, Any]
ResultDict = Dict[str, Any]


# Gateway type (avoiding circular import)
class GatewayProtocol(Protocol):
    """Protocol for LiteLLM Gateway interface."""

    async def generate_async(self, prompt: str, **kwargs: Any) -> Any:
        """
        Generate text asynchronously.
        
        Args:
            prompt (str): Prompt text sent to the model.
            **kwargs (Any): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        """
        ...

    def generate(self, prompt: str, **kwargs: Any) -> Any:
        """
        Generate text synchronously.
        
        Args:
            prompt (str): Prompt text sent to the model.
            **kwargs (Any): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        """
        ...


# Agent type
class AgentProtocol(Protocol):
    """Protocol for Agent interface."""

    agent_id: str
    tenant_id: Optional[str]
    name: str
    description: str


# Tool type
class ToolProtocol(Protocol):
    """Protocol for Tool interface."""

    tool_id: str
    name: str
    description: str

    async def execute(self, **kwargs: Any) -> Any:
        """
        Execute the tool asynchronously.
        
        Args:
            **kwargs (Any): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        """
        ...


# Cache type
class CacheProtocol(Protocol):
    """Protocol for Cache interface."""

    async def get(self, key: str, tenant_id: Optional[str] = None) -> Optional[Any]:
        """
        Get value from cache asynchronously.
        
        Args:
            key (str): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            Optional[Any]: Result if available, else None.
        """
        ...

    async def set(
        self, key: str, value: Any, tenant_id: Optional[str] = None, ttl: Optional[int] = None
    ) -> None:
        """
        Set value in cache asynchronously.
        
        Args:
            key (str): Input parameter for this operation.
            value (Any): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
            ttl (Optional[int]): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        """
        ...

    async def delete(self, key: str, tenant_id: Optional[str] = None) -> None:
        """
        Delete key from cache asynchronously.
        
        Args:
            key (str): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            None: Result of the operation.
        """
        ...

    async def invalidate_pattern(self, pattern: str, tenant_id: Optional[str] = None) -> None:
        """
        Invalidate cache keys matching pattern asynchronously.
        
        Args:
            pattern (str): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            None: Result of the operation.
        """
        ...


# Type helpers
T = TypeVar("T")


def ensure_type(value: Any, expected_type: type[T], error_message: str = "Type mismatch") -> T:
    """
    Ensure value is of expected type, raise TypeError if not.

    Args:
        value: Value to check
        expected_type: Expected type
        error_message: Error message if type mismatch

    Returns:
        Value if type matches

    Raises:
        TypeError: If type doesn't match
    """
    if not isinstance(value, expected_type):
        raise TypeError(
            f"{error_message}: expected {expected_type.__name__}, got {type(value).__name__}"
        )
    return value


def optional_type(value: Optional[Any], expected_type: type[T], default: T) -> T:
    """
    Return value if it matches expected type, otherwise return default.

    Args:
        value: Value to check
        expected_type: Expected type
        default: Default value if type doesn't match

    Returns:
        Value if type matches, default otherwise
    """
    if value is None:
        return default
    if isinstance(value, expected_type):
        return value
    return default
