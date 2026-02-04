"""
HTTP Client Utilities for Service-to-Service Communication

Provides retry logic, circuit breakers, and standardized HTTP client for
inter-service communication in FaaS architecture.
"""


import asyncio
import logging
from typing import Any, Dict, Optional

import httpx

from ...core.utils.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from .config import ServiceConfig

logger = logging.getLogger(__name__)


class ServiceClientError(Exception):
    """Base exception for service client errors."""

    pass


class ServiceUnavailableError(ServiceClientError):
    """Raised when service is unavailable (circuit breaker open)."""

    pass


class ServiceTimeoutError(ServiceClientError):
    """Raised when service call times out."""

    pass


class ServiceHTTPClient:
    """
    HTTP client for service-to-service communication with retry and circuit breaker.

    Features:
    - Automatic retry with exponential backoff
    - Circuit breaker for fault tolerance
    - Request/response logging
    - Standard header injection
    - Timeout handling
    """

    def __init__(
        self,
        service_name: str,
        service_url: str,
        config: Optional[ServiceConfig] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
    ):
        """
        Initialize service HTTP client.
        
        Args:
            service_name (str): Input parameter for this operation.
            service_url (str): Input parameter for this operation.
            config (Optional[ServiceConfig]): Configuration object or settings.
            timeout (float): Input parameter for this operation.
            max_retries (int): Input parameter for this operation.
            circuit_breaker_config (Optional[CircuitBreakerConfig]): Input parameter for this operation.
        """
        self.service_name = service_name
        self.service_url = service_url.rstrip("/")
        self.config = config
        self.timeout = timeout
        self.max_retries = max_retries

        # Initialize circuit breaker
        self.circuit_breaker = CircuitBreaker(
            name=f"http_client_{service_name}",
            config=circuit_breaker_config
            or CircuitBreakerConfig(failure_threshold=5, success_threshold=2, timeout=60.0),
        )

        # Create HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.service_url,
            timeout=timeout,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        headers: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """
        Make HTTP request with retry and circuit breaker.
        
        Args:
            method (str): Input parameter for this operation.
            endpoint (str): Input parameter for this operation.
            headers (Optional[Dict[str, Any]]): HTTP headers passed from the caller.
            json_data (Optional[Dict[str, Any]]): Input parameter for this operation.
            params (Optional[Dict[str, Any]]): Input parameter for this operation.
        
        Returns:
            httpx.Response: Result of the operation.
        
        Raises:
            ServiceClientError: Raised when this function detects an invalid state or when an underlying call fails.
            ServiceTimeoutError: Raised when this function detects an invalid state or when an underlying call fails.
            ServiceUnavailableError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        # Prepare headers
        request_headers = headers or {}

        # Prepare URL
        url = endpoint if endpoint.startswith("http") else f"{self.service_url}{endpoint}"

        # Define request function for circuit breaker
        async def _execute_request():
            try:
                response = await self.client.request(
                    method=method,
                    url=url,
                    headers=request_headers,
                    json=json_data,
                    params=params,
                )
                response.raise_for_status()
                return response
            except httpx.TimeoutException as e:
                logger.error(f"Timeout calling {self.service_name} {method} {endpoint}: {e}")
                raise ServiceTimeoutError(f"Service {self.service_name} timeout: {e}")
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error calling {self.service_name} {method} {endpoint}: {e}")
                raise ServiceClientError(
                    f"Service {self.service_name} HTTP error: {e.response.status_code}"
                )
            except httpx.RequestError as e:
                logger.error(f"Request error calling {self.service_name} {method} {endpoint}: {e}")
                raise ServiceClientError(f"Service {self.service_name} request error: {e}")

        # Execute with circuit breaker
        try:
            response = await self.circuit_breaker.call(_execute_request)
            return response
        except RuntimeError as e:
            if "is OPEN" in str(e):
                raise ServiceUnavailableError(f"Service {self.service_name} is unavailable: {e}")
            raise ServiceClientError(f"Service {self.service_name} error: {e}")

    async def get(
        self,
        endpoint: str,
        headers: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make GET request with automatic retry.
        
        Args:
            endpoint (str): Input parameter for this operation.
            headers (Optional[Dict[str, Any]]): HTTP headers passed from the caller.
            params (Optional[Dict[str, Any]]): Input parameter for this operation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        
        Raises:
            ServiceClientError: Raised when this function detects an invalid state or when an underlying call fails.
            last_error: Raised when this function detects an invalid state or when an underlying call fails.
        """
        # Retry logic is handled in _make_request via circuit breaker
        # Additional retry can be added here if needed
        max_retries = self.max_retries
        last_error = None

        for attempt in range(max_retries):
            try:
                response = await self._make_request("GET", endpoint, headers=headers, params=params)
                return response.json()
            except ServiceUnavailableError:
                # Circuit breaker is open, don't retry
                raise
            except ServiceClientError as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = 2**attempt
                    await asyncio.sleep(wait_time)
                    continue
                raise

        if last_error:
            raise last_error
        raise ServiceClientError("Failed to make GET request")

    async def post(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make POST request with automatic retry.
        
        Args:
            endpoint (str): Input parameter for this operation.
            json_data (Optional[Dict[str, Any]]): Input parameter for this operation.
            headers (Optional[Dict[str, Any]]): HTTP headers passed from the caller.
            params (Optional[Dict[str, Any]]): Input parameter for this operation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        
        Raises:
            ServiceClientError: Raised when this function detects an invalid state or when an underlying call fails.
            last_error: Raised when this function detects an invalid state or when an underlying call fails.
        """
        max_retries = self.max_retries
        last_error = None

        for attempt in range(max_retries):
            try:
                response = await self._make_request(
                    "POST", endpoint, headers=headers, json_data=json_data, params=params
                )
                return response.json()
            except ServiceUnavailableError:
                # Circuit breaker is open, don't retry
                raise
            except ServiceClientError as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = min(2**attempt, 10)  # Cap at 10 seconds
                    await asyncio.sleep(wait_time)
                    continue
                raise

        if last_error:
            raise last_error
        raise ServiceClientError("Failed to make POST request")

    async def put(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make PUT request with automatic retry.
        
        Args:
            endpoint (str): Input parameter for this operation.
            json_data (Optional[Dict[str, Any]]): Input parameter for this operation.
            headers (Optional[Dict[str, Any]]): HTTP headers passed from the caller.
            params (Optional[Dict[str, Any]]): Input parameter for this operation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        
        Raises:
            ServiceClientError: Raised when this function detects an invalid state or when an underlying call fails.
            last_error: Raised when this function detects an invalid state or when an underlying call fails.
        """
        max_retries = self.max_retries
        last_error = None

        for attempt in range(max_retries):
            try:
                response = await self._make_request(
                    "PUT", endpoint, headers=headers, json_data=json_data, params=params
                )
                return response.json()
            except ServiceUnavailableError:
                # Circuit breaker is open, don't retry
                raise
            except ServiceClientError as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = min(2**attempt, 10)  # Cap at 10 seconds
                    await asyncio.sleep(wait_time)
                    continue
                raise

        if last_error:
            raise last_error
        raise ServiceClientError("Failed to make PUT request")

    async def delete(
        self,
        endpoint: str,
        headers: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make DELETE request with automatic retry.
        
        Args:
            endpoint (str): Input parameter for this operation.
            headers (Optional[Dict[str, Any]]): HTTP headers passed from the caller.
            params (Optional[Dict[str, Any]]): Input parameter for this operation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        
        Raises:
            ServiceClientError: Raised when this function detects an invalid state or when an underlying call fails.
            last_error: Raised when this function detects an invalid state or when an underlying call fails.
        """
        max_retries = self.max_retries
        last_error = None

        for attempt in range(max_retries):
            try:
                response = await self._make_request(
                    "DELETE", endpoint, headers=headers, params=params
                )
                return response.json()
            except ServiceUnavailableError:
                # Circuit breaker is open, don't retry
                raise
            except ServiceClientError as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = min(2**attempt, 10)  # Cap at 10 seconds
                    await asyncio.sleep(wait_time)
                    continue
                raise

        if last_error:
            raise last_error
        raise ServiceClientError("Failed to make DELETE request")

    def get_headers(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Get standard headers for service-to-service calls.
        
        Args:
            tenant_id (str): Tenant identifier used for tenant isolation.
            user_id (Optional[str]): User identifier (used for auditing or personalization).
            correlation_id (Optional[str]): Input parameter for this operation.
            request_id (Optional[str]): Input parameter for this operation.
        
        Returns:
            Dict[str, str]: Dictionary result of the operation.
        """
        headers = {
            "X-Tenant-ID": tenant_id,
        }
        if user_id:
            headers["X-User-ID"] = user_id
        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id
        if request_id:
            headers["X-Request-ID"] = request_id
        return headers

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    def __del__(self):
        """Cleanup on deletion."""
        # Note: Async cleanup in __del__ is not reliable
        # Clients should be explicitly closed using await client.close()
        pass


class ServiceClientManager:
    """
    Manager for multiple service HTTP clients.

    Provides centralized management of service clients with lazy initialization.
    """

    def __init__(self, config: ServiceConfig):
        """
        Initialize service client manager.
        
        Args:
            config (ServiceConfig): Configuration object or settings.
        """
        self.config = config
        self._clients: Dict[str, ServiceHTTPClient] = {}

    def get_client(self, service_name: str) -> Optional[ServiceHTTPClient]:
        """
        Get or create service client.
        
        Args:
            service_name (str): Input parameter for this operation.
        
        Returns:
            Optional[ServiceHTTPClient]: Result if available, else None.
        """
        if service_name in self._clients:
            return self._clients[service_name]

        # Get service URL from config
        url_attr = f"{service_name}_service_url"
        service_url = getattr(self.config, url_attr, None)

        if not service_url:
            logger.warning(f"Service URL for {service_name} not configured")
            return None

        # Create client
        client = ServiceHTTPClient(
            service_name=service_name,
            service_url=service_url,
            config=self.config,
        )
        self._clients[service_name] = client
        return client

    async def close_all(self):
        """Close all service clients."""
        for client in self._clients.values():
            await client.close()
        self._clients.clear()


def create_service_client(
    service_name: str,
    service_url: str,
    config: Optional[ServiceConfig] = None,
) -> ServiceHTTPClient:
    """
    Factory function to create a service HTTP client.

    Args:
        service_name: Name of the target service
        service_url: Base URL of the target service
        config: Service configuration (optional)

    Returns:
        ServiceHTTPClient instance
    """
    return ServiceHTTPClient(
        service_name=service_name,
        service_url=service_url,
        config=config,
    )
