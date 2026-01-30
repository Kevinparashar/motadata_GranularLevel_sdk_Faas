"""
Basic Observability Example

Demonstrates how to use the Evaluation & Observability component
for distributed tracing, logging, and metrics collection.

This is a foundation component with no dependencies.

NOTE: This example is a template. The evaluation_observability module
is currently a placeholder and will be implemented in a future version.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def main():
    """Demonstrate basic observability features."""
    
    print("=" * 70)
    print("OBSERVABILITY EXAMPLE - PLACEHOLDER")
    print("=" * 70)
    print()
    print("⚠️  NOTE: The evaluation_observability module is not yet implemented.")
    print("    This example serves as a template for future implementation.")
    print()
    print("📋 Planned Features:")
    print("  • Structured logging with context")
    print("  • Distributed tracing (OpenTelemetry)")
    print("  • Metrics collection (counters, gauges, histograms)")
    print("  • Error tracking and exception capture")
    print()
    
    # Example placeholder showing what the API would look like
    print("🔮 Example API (Future Implementation):")
    print()
    print("# Initialize observability manager")
    print('observability = ObservabilityManager(service_name="example-service")')
    print()
    print("# Structured logging")
    print('logger = observability.get_logger("example")')
    print('logger.info("Application started", extra={"version": "1.0.0"})')
    print()
    print("# Distributed tracing")
    print('with observability.start_trace("operation") as span:')
    print('    span.set_attribute("operation.type", "example")')
    print()
    print("# Metrics collection")
    print("metrics = observability.get_metrics()")
    print('metrics.increment_counter("requests.total")')
    print()
    
    # Use Python's built-in logging as a basic demonstration
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("example")
    
    logger.info("Using Python's built-in logging as placeholder")
    logger.warning("Evaluation & Observability module coming soon!")

    print()
    print("=" * 70)
    print("✅ Example template displayed successfully!")
    print()
    print("📚 For current SDK observability, consider:")
    print("  • Use Python's logging module for structured logs")
    print("  • Use OpenTelemetry SDK directly for tracing")
    print("  • Use Prometheus client for metrics")
    print("=" * 70)


if __name__ == "__main__":
    main()
