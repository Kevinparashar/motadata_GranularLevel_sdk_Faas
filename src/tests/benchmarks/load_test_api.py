"""
Load Testing for API Endpoints

Tests API endpoint performance under load.
"""

import time
from typing import Dict, List

import pytest
from fastapi.testclient import TestClient

from src.core.api_backend_services.functions import create_api_app, create_api_router


class LoadTestResults:
    """Results from load testing."""

    def __init__(self):
        """Initialize results."""
        self.request_times: List[float] = []
        self.success_count = 0
        self.error_count = 0
        self.status_codes: Dict[int, int] = {}

    def record_request(self, latency: float, status_code: int):
        """Record a request."""
        self.request_times.append(latency)
        if status_code == 200:
            self.success_count += 1
        else:
            self.error_count += 1

        if status_code not in self.status_codes:
            self.status_codes[status_code] = 0
        self.status_codes[status_code] += 1

    def get_stats(self) -> Dict[str, float]:
        """Get statistics."""
        if not self.request_times:
            return {}

        sorted_times = sorted(self.request_times)
        return {
            "total_requests": len(self.request_times),
            "success_rate": (self.success_count / len(self.request_times)) * 100,
            "error_rate": (self.error_count / len(self.request_times)) * 100,
            "avg_latency": sum(self.request_times) / len(self.request_times),
            "min_latency": min(self.request_times),
            "max_latency": max(self.request_times),
            "p50": sorted_times[len(sorted_times) // 2],
            "p95": sorted_times[int(len(sorted_times) * 0.95)],
            "p99": sorted_times[int(len(sorted_times) * 0.99)],
            "throughput": len(self.request_times) / sum(self.request_times),
        }


@pytest.mark.benchmark
@pytest.mark.load_test
class TestAPILoadTests:
    """Load tests for API endpoints."""

    @pytest.fixture
    def api_app(self):
        """Create API app for testing."""
        app = create_api_app()
        router = create_api_router(prefix="/api/v1")

        @router.get("/health")
        def health_check():
            """Health check endpoint."""
            return {"status": "ok"}

        @router.post("/generate")
        async def generate(prompt: str):
            """Generate endpoint."""
            return {"text": "Generated response"}

        app.include_router(router)
        return app

    @pytest.fixture
    def client(self, api_app):
        """Test client."""
        return TestClient(api_app)

    def test_health_endpoint_load(self, client):
        """Load test health check endpoint."""
        results = LoadTestResults()
        total_requests = 1000
        _ = 10  # concurrent_requests placeholder

        def make_request():
            """Make a single request."""
            start = time.time()
            response = client.get("/api/v1/health")
            latency = time.time() - start
            results.record_request(latency, response.status_code)

        # Run load test
        start = time.time()
        for _ in range(total_requests):
            make_request()
        elapsed = time.time() - start

        stats = results.get_stats()
        stats["total_time"] = elapsed

        print("\nHealth Endpoint Load Test:")
        print(f"  Total requests: {stats['total_requests']}")
        print(f"  Success rate: {stats['success_rate']:.1f}%")
        print(f"  Avg latency: {stats['avg_latency']*1000:.2f}ms")
        print(f"  P95 latency: {stats['p95']*1000:.2f}ms")
        print(f"  Throughput: {stats['throughput']:.0f} req/sec")

        # Assertions
        assert stats["success_rate"] > 99.0  # > 99% success
        assert stats["avg_latency"] < 0.1  # < 100ms avg
        assert stats["p95"] < 0.2  # P95 < 200ms

    def test_generate_endpoint_load(self, client):
        """Load test generate endpoint."""
        results = LoadTestResults()
        total_requests = 100
        _ = 5  # concurrent_requests placeholder

        def make_request():
            """Make a single request."""
            start = time.time()
            response = client.post("/api/v1/generate", json={"prompt": "Test prompt"})
            latency = time.time() - start
            results.record_request(latency, response.status_code)

        # Run load test
        start = time.time()
        for _ in range(total_requests):
            make_request()
        elapsed = time.time() - start

        stats = results.get_stats()
        stats["total_time"] = elapsed

        print("\nGenerate Endpoint Load Test:")
        print(f"  Total requests: {stats['total_requests']}")
        print(f"  Success rate: {stats['success_rate']:.1f}%")
        print(f"  Avg latency: {stats['avg_latency']*1000:.2f}ms")
        print(f"  P95 latency: {stats['p95']*1000:.2f}ms")

        # Assertions
        assert stats["success_rate"] > 95.0  # > 95% success

    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests."""
        results = LoadTestResults()
        concurrent_requests = 20
        requests_per_thread = 10

        def make_requests():
            """Make multiple requests."""
            for _ in range(requests_per_thread):
                start = time.time()
                response = client.get("/api/v1/health")
                latency = time.time() - start
                results.record_request(latency, response.status_code)

        # Run concurrent requests
        import threading

        threads = []
        start = time.time()

        for _ in range(concurrent_requests):
            thread = threading.Thread(target=make_requests)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        elapsed = time.time() - start
        total_requests = concurrent_requests * requests_per_thread

        stats = results.get_stats()
        stats["total_time"] = elapsed
        stats["concurrent_requests"] = concurrent_requests

        print("\nConcurrent Requests Test:")
        print(f"  Concurrent threads: {concurrent_requests}")
        print(f"  Requests per thread: {requests_per_thread}")
        print(f"  Total requests: {total_requests}")
        print(f"  Success rate: {stats['success_rate']:.1f}%")
        print(f"  Total time: {elapsed:.2f}s")

        assert stats["success_rate"] > 95.0
