"""
Basic Pool Implementation Example

Demonstrates how to use connection and thread pooling
for efficient resource management.

This is a foundation component with no dependencies.
"""

import os
import sys
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pool_implementation import ConnectionPool, ThreadPool


def main():
    """Demonstrate basic pooling features."""
    
    # 1. Connection Pool Example
    print("=== Connection Pool Example ===")
    
    pool_config = {
        "min_size": 2,
        "max_size": 10,
        "timeout": 30
    }
    
    connection_pool = ConnectionPool(
        factory=lambda: f"connection-{id({})}",  # Mock connection factory
        **pool_config
    )
    
    # Acquire connections
    conn1 = connection_pool.acquire()
    conn2 = connection_pool.acquire()
    print(f"Acquired connections: {conn1}, {conn2}")
    
    # Use connections
    print(f"Pool size: {connection_pool.size()}")
    print(f"Available: {connection_pool.available()}")
    
    # Release connections
    connection_pool.release(conn1)
    connection_pool.release(conn2)
    print(f"After release - Available: {connection_pool.available()}")
    
    # 2. Thread Pool Example
    print("\n=== Thread Pool Example ===")
    
    thread_pool = ThreadPool(max_workers=4)
    
    def worker_task(task_id: int) -> str:
        """Simulate a worker task."""
        import time
        time.sleep(0.1)
        return f"Task {task_id} completed"
    
    # Submit tasks
    futures = []
    for i in range(5):
        future = thread_pool.submit(worker_task, i)
        futures.append(future)
    
    # Wait for completion
    results = [f.result() for f in futures]
    for result in results:
        print(f"  {result}")
    
    # Cleanup
    thread_pool.shutdown()
    connection_pool.close()
    
    print("\n✅ Pool implementation example completed successfully!")


if __name__ == "__main__":
    main()

