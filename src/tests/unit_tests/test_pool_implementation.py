"""
Unit Tests for Pool Implementation Component

Tests connection and thread pooling.
"""

import pytest
import time
from unittest.mock import Mock, MagicMock
from pool_implementation import ConnectionPool, ThreadPool


class TestConnectionPool:
    """Test ConnectionPool."""
    
    def test_initialization(self):
        """Test pool initialization."""
        factory = Mock(return_value="connection")
        pool = ConnectionPool(factory=factory, min_size=2, max_size=10)
        assert pool.min_size == 2
        assert pool.max_size == 10
    
    def test_acquire_release(self):
        """Test connection acquire and release."""
        factory = Mock(return_value="connection")
        pool = ConnectionPool(factory=factory, min_size=1, max_size=5)
        
        conn = pool.acquire()
        assert conn == "connection"
        assert pool.size() >= 1
        
        pool.release(conn)
        assert pool.available() >= 1
    
    def test_pool_exhaustion(self):
        """Test pool exhaustion handling."""
        factory = Mock(return_value="connection")
        pool = ConnectionPool(factory=factory, min_size=1, max_size=2)
        
        conn1 = pool.acquire()
        conn2 = pool.acquire()
        
        # Should handle gracefully when pool is exhausted
        assert pool.available() == 0
    
    def test_pool_size_limits(self):
        """Test pool size limits."""
        factory = Mock(return_value="connection")
        pool = ConnectionPool(factory=factory, min_size=2, max_size=5)
        
        assert pool.size() >= 2
        assert pool.size() <= 5
    
    def test_close_pool(self):
        """Test pool closing."""
        factory = Mock(return_value="connection")
        pool = ConnectionPool(factory=factory, min_size=1, max_size=5)
        
        pool.close()
        # Should not raise exception


class TestThreadPool:
    """Test ThreadPool."""
    
    def test_initialization(self):
        """Test thread pool initialization."""
        pool = ThreadPool(max_workers=4)
        assert pool.max_workers == 4
    
    def test_submit_task(self):
        """Test task submission."""
        pool = ThreadPool(max_workers=2)
        
        def task(x):
            return x * 2
        
        future = pool.submit(task, 5)
        result = future.result()
        assert result == 10
    
    def test_multiple_tasks(self):
        """Test multiple task execution."""
        pool = ThreadPool(max_workers=3)
        
        def task(x):
            time.sleep(0.01)
            return x * 2
        
        futures = [pool.submit(task, i) for i in range(5)]
        results = [f.result() for f in futures]
        
        assert len(results) == 5
        assert all(r % 2 == 0 for r in results)
    
    def test_shutdown(self):
        """Test pool shutdown."""
        pool = ThreadPool(max_workers=2)
        pool.shutdown()
        # Should not raise exception
    
    def test_shutdown_wait(self):
        """Test pool shutdown with wait."""
        pool = ThreadPool(max_workers=2)
        
        def task(x):
            time.sleep(0.1)
            return x
        
        future = pool.submit(task, 1)
        pool.shutdown(wait=True)
        
        assert future.result() == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

