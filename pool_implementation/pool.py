"""
Connection Pool Implementation

Resource pooling and management for connections and threads.
"""

import asyncio
import time
from typing import Optional, Callable, Awaitable, Any, Dict
from collections import deque
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod


class PoolConfig(BaseModel):
    """Configuration for connection pool."""
    min_size: int = Field(default=5, ge=1)
    max_size: int = Field(default=20, ge=1)
    timeout: float = Field(default=30.0, ge=0)
    idle_timeout: float = Field(default=300.0, ge=0)
    max_lifetime: Optional[float] = Field(default=None, ge=0)


class Connection(ABC):
    """Abstract connection interface."""
    
    @abstractmethod
    def is_valid(self) -> bool:
        """Check if connection is valid."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close the connection."""
        pass


class ConnectionPool:
    """
    Generic connection pool for managing connections.
    
    Provides efficient connection reuse and resource management.
    """
    
    def __init__(
        self,
        config: PoolConfig,
        create_connection: Callable[[], Awaitable[Connection]],
    ):
        """
        Initialize connection pool.
        
        Args:
            config: Pool configuration
            create_connection: Async function to create a new connection
        """
        self.config = config
        self.create_connection = create_connection
        
        self._pool: deque[Connection] = deque()
        self._active: set[Connection] = set()
        self._waiting: deque[asyncio.Future] = deque()
        
        self._stats = {
            "total_connections": 0,
            "active_connections": 0,
            "idle_connections": 0,
            "waiting_requests": 0,
            "total_acquired": 0,
            "total_released": 0,
        }
        self._lock = asyncio.Lock()
        self._closed = False
        
        # Track connection creation times
        self._connection_times: dict[Connection, float] = {}
    
    async def _initialize(self) -> None:
        """Initialize pool with minimum connections."""
        async with self._lock:
            for _ in range(self.config.min_size):
                try:
                    conn = await self.create_connection()
                    self._pool.append(conn)
                    self._connection_times[conn] = time.time()
                    self._stats["total_connections"] += 1
                except Exception:
                    pass
    
    async def acquire(self, timeout: Optional[float] = None) -> Connection:
        """
        Acquire a connection from the pool.
        
        Args:
            timeout: Optional timeout for acquisition
        
        Returns:
            Connection instance
        
        Raises:
            TimeoutError: If connection cannot be acquired within timeout
        """
        if self._closed:
            raise RuntimeError("Pool is closed")
        
        timeout = timeout or self.config.timeout
        start_time = time.time()
        
        while True:
            async with self._lock:
                # Check if we have an available connection
                if self._pool:
                    conn = self._pool.popleft()
                    
                    # Check if connection is still valid
                    if not conn.is_valid():
                        try:
                            await conn.close()
                        except Exception:
                            pass
                        try:
                            conn = await self.create_connection()
                            self._connection_times[conn] = time.time()
                            self._stats["total_connections"] += 1
                        except Exception:
                            continue
                    
                    # Check max_lifetime
                    if self.config.max_lifetime:
                        conn_age = time.time() - self._connection_times.get(conn, 0)
                        if conn_age > self.config.max_lifetime:
                            try:
                                await conn.close()
                            except Exception:
                                pass
                            try:
                                conn = await self.create_connection()
                                self._connection_times[conn] = time.time()
                                self._stats["total_connections"] += 1
                            except Exception:
                                continue
                    
                    self._active.add(conn)
                    self._stats["active_connections"] = len(self._active)
                    self._stats["idle_connections"] = len(self._pool)
                    self._stats["total_acquired"] += 1
                    return conn
                
                # No available connection, try to create a new one
                if len(self._active) < self.config.max_size:
                    try:
                        conn = await self.create_connection()
                        self._connection_times[conn] = time.time()
                        self._active.add(conn)
                        self._stats["total_connections"] += 1
                        self._stats["active_connections"] = len(self._active)
                        self._stats["total_acquired"] += 1
                        return conn
                    except Exception:
                        pass
                
                # Pool is full, wait for a connection to be released
                if time.time() - start_time >= timeout:
                    raise TimeoutError(f"Could not acquire connection within {timeout} seconds")
                
                # Create a future to wait for a connection
                future = asyncio.Future()
                self._waiting.append(future)
                self._stats["waiting_requests"] = len(self._waiting)
            
            # Wait for a connection to be released
            try:
                await asyncio.wait_for(future, timeout=timeout - (time.time() - start_time))
            except asyncio.TimeoutError:
                async with self._lock:
                    if future in self._waiting:
                        self._waiting.remove(future)
                        self._stats["waiting_requests"] = len(self._waiting)
                raise TimeoutError(f"Could not acquire connection within {timeout} seconds")
    
    async def release(self, conn: Connection) -> None:
        """
        Release a connection back to the pool.
        
        Args:
            conn: Connection to release
        """
        async with self._lock:
            if conn not in self._active:
                return
            
            self._active.remove(conn)
            self._stats["active_connections"] = len(self._active)
            
            # Check if connection is still valid
            if conn.is_valid():
                self._pool.append(conn)
                self._stats["idle_connections"] = len(self._pool)
            else:
                # Connection is invalid, close it
                try:
                    await conn.close()
                except Exception:
                    pass
            
            self._stats["total_released"] += 1
            
            # Notify waiting requests
            if self._waiting:
                future = self._waiting.popleft()
                self._stats["waiting_requests"] = len(self._waiting)
                if not future.done():
                    future.set_result(None)
    
    async def close(self) -> None:
        """Close the pool and all connections."""
        async with self._lock:
            if self._closed:
                return
            
            self._closed = True
            
            # Close all active connections
            for conn in list(self._active):
                try:
                    await conn.close()
                except Exception:
                    pass
            
            self._active.clear()
            
            # Close all idle connections
            while self._pool:
                conn = self._pool.popleft()
                try:
                    await conn.close()
                except Exception:
                    pass
            
            # Cancel waiting requests
            while self._waiting:
                future = self._waiting.popleft()
                if not future.done():
                    future.cancel()
            
            self._stats["active_connections"] = 0
            self._stats["idle_connections"] = 0
            self._stats["waiting_requests"] = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get pool statistics.
        
        Returns:
            Dictionary with pool statistics
        """
        return self._stats.copy()
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


class ThreadPool:
    """Thread pool for parallel execution."""
    
    def __init__(self, max_workers: int = 10):
        """
        Initialize thread pool.
        
        Args:
            max_workers: Maximum number of worker threads
        """
        self.max_workers = max_workers
        self._executor: Optional[Any] = None
    
    def submit(self, fn: Callable, *args, **kwargs) -> Any:
        """
        Submit a task to the thread pool.
        
        Args:
            fn: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
        
        Returns:
            Future object
        """
        from concurrent.futures import ThreadPoolExecutor
        
        if self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        return self._executor.submit(fn, *args, **kwargs)
    
    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown the thread pool.
        
        Args:
            wait: Whether to wait for tasks to complete
        """
        if self._executor:
            self._executor.shutdown(wait=wait)
            self._executor = None

