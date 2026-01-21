"""
HTTP Client Utilities for Service-to-Service Communication

Provides retry logic, circuit breakers, and standardized HTTP client for
inter-service communication in FaaS architecture.
"""

import asyncio
import logging
from typing import Any, Dict, Optional, List
from datetime import datetime

import httpx
import asyncio

from ...core.utils.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState
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
            service_name: Name of the target service (for logging/circuit breaker)
            service_url: Base URL of the target service
            config: Service configuration (optional)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            circuit_breaker_config: Circuit breaker configuration
        """
        self.service_name = service_name
        self.service_url = service_url.rstrip('/')
        self.config = config
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Initialize circuit breaker
        self.circuit_breaker = CircuitBreaker(
            name=f"http_client_{service_name}",
            config=circuit_breaker_config or CircuitBreakerConfig(
                failure_threshold=5,
                success_threshold=2,
                timeout=60.0
            )
        )
        
        # Create HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.service_url,
            timeout=timeout,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
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
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (relative to base URL)
            headers: Additional headers
            json_data: JSON request body
            params: Query parameters
            
        Returns:
            HTTP response
            
        Raises:
            ServiceUnavailableError: If circuit breaker is open
            ServiceTimeoutError: If request times out
            ServiceClientError: For other errors
        """
        # Prepare headers
        request_headers = headers or {}
        
        # Prepare URL
        url = endpoint if endpoint.startswith('http') else f"{self.service_url}{endpoint}"
        
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
                raise ServiceClientError(f"Service {self.service_name} HTTP error: {e.response.status_code}")
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
            endpoint: API endpoint
            headers: Additional headers
            params: Query parameters
            
        Returns:
            Response JSON as dictionary
        """
        # Retry logic is handled in _make_request via circuit breaker
        # Additional retry can be added here if needed
        max_retries = self.max_retries
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = await self._make_request("GET", endpoint, headers=headers, params=params)
                return response.json()
            except (ServiceTimeoutError, ServiceClientError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Exponential backoff
                    import asyncio
                    wait_time = 2 ** attempt
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
            endpoint: API endpoint
            json_data: JSON request body
            headers: Additional headers
            params: Query parameters
            
        Returns:
            Response JSON as dictionary
        """
        max_retries = self.max_retries
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = await self._make_request("POST", endpoint, headers=headers, json_data=json_data, params=params)
                return response.json()
            except ServiceUnavailableError:
                # Circuit breaker is open, don't retry
                raise
            except (ServiceTimeoutError, ServiceClientError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = min(2 ** attempt, 10)  # Cap at 10 seconds
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
            endpoint: API endpoint
            json_data: JSON request body
            headers: Additional headers
            params: Query parameters
            
        Returns:
            Response JSON as dictionary
        """
        max_retries = self.max_retries
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = await self._make_request("PUT", endpoint, headers=headers, json_data=json_data, params=params)
                return response.json()
            except ServiceUnavailableError:
                # Circuit breaker is open, don't retry
                raise
            except (ServiceTimeoutError, ServiceClientError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = min(2 ** attempt, 10)  # Cap at 10 seconds
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
            endpoint: API endpoint
            headers: Additional headers
            params: Query parameters
            
        Returns:
            Response JSON as dictionary
        """
        max_retries = self.max_retries
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = await self._make_request("DELETE", endpoint, headers=headers, params=params)
                return response.json()
            except ServiceUnavailableError:
                # Circuit breaker is open, don't retry
                raise
            except (ServiceTimeoutError, ServiceClientError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = min(2 ** attempt, 10)  # Cap at 10 seconds
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
            tenant_id: Tenant ID
            user_id: User ID (optional)
            correlation_id: Correlation ID (optional)
            request_id: Request ID (optional)
            
        Returns:
            Dictionary of headers
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
        try:
            asyncio.create_task(self.close())
        except Exception:
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
            config: Service configuration with service URLs
        """
        self.config = config
        self._clients: Dict[str, ServiceHTTPClient] = {}
    
    def get_client(self, service_name: str) -> Optional[ServiceHTTPClient]:
        """
        Get or create service client.
        
        Args:
            service_name: Name of the service (e.g., "gateway", "rag", "cache")
            
        Returns:
            ServiceHTTPClient instance or None if service URL not configured
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

