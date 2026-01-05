"""
Basic Observability Example

Demonstrates how to use the Evaluation & Observability component
for distributed tracing, logging, and metrics collection.

This is a foundation component with no dependencies.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.evaluation_observability import (
    ObservabilityManager,
    TraceContext,
    MetricCollector,
    StructuredLogger
)


def main():
    """Demonstrate basic observability features."""
    
    # Initialize observability manager
    observability = ObservabilityManager(
        service_name="example-service",
        environment="development"
    )
    
    # 1. Structured Logging
    logger = observability.get_logger("example")
    logger.info("Application started", extra={"version": "1.0.0"})
    logger.warning("This is a warning message", extra={"component": "example"})
    logger.error("This is an error message", extra={"error_code": "E001"})
    
    # 2. Distributed Tracing
    with observability.start_trace("example_operation") as span:
        span.set_attribute("operation.type", "example")
        span.set_attribute("operation.id", "12345")
        
        # Simulate some work
        import time
        time.sleep(0.1)
        
        # Nested span
        with observability.start_span("nested_operation", parent=span) as nested_span:
            nested_span.set_attribute("nested.value", "test")
            time.sleep(0.05)
    
    # 3. Metrics Collection
    metrics = observability.get_metrics()
    
    # Counter metric
    metrics.increment_counter("requests.total", tags={"endpoint": "/example"})
    metrics.increment_counter("requests.total", amount=5)
    
    # Gauge metric
    metrics.set_gauge("active.connections", 42, tags={"type": "database"})
    
    # Histogram metric
    metrics.record_histogram("request.duration", 0.125, tags={"endpoint": "/example"})
    
    # 4. Error Tracking
    try:
        raise ValueError("Example error for tracking")
    except Exception as e:
        observability.capture_exception(e, context={"user_id": "user123"})
    
    print("✅ Observability example completed successfully!")
    print("Check your observability backend (e.g., Jaeger, Prometheus) for traces and metrics.")


if __name__ == "__main__":
    main()

