# MOTADATA - EVALUATION & OBSERVABILITY TROUBLESHOOTING

**Troubleshooting guide for diagnosing and resolving common issues with the Evaluation & Observability component.**

This guide helps diagnose and resolve common issues encountered when using the Evaluation & Observability component.

## Table of Contents

1. [Tracing Issues](#tracing-issues)
2. [Logging Problems](#logging-problems)
3. [Metrics Collection Issues](#metrics-collection-issues)
4. [Export Failures](#export-failures)
5. [Performance Impact](#performance-impact)
6. [Configuration Problems](#configuration-problems)

## Tracing Issues

### Problem: Traces not being created

**Symptoms:**
- No traces in monitoring system
- Spans not appearing
- Trace context not propagated
- Tracing disabled

**Diagnosis:**
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)
# Check tracer is configured
print(f"Tracer: {tracer}")
```

**Solutions:**

1. **Configure OpenTelemetry:**
   ```python
   from opentelemetry import trace
   from opentelemetry.sdk.trace import TracerProvider
   from opentelemetry.sdk.trace.export import BatchSpanProcessor
   from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

   # Set up tracer
   trace.set_tracer_provider(TracerProvider())
   tracer = trace.get_tracer(__name__)

   # Configure exporter
   otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317")
   span_processor = BatchSpanProcessor(otlp_exporter)
   trace.get_tracer_provider().add_span_processor(span_processor)
   ```

2. **Create Spans:**
   ```python
   with tracer.start_as_current_span("operation_name") as span:
       span.set_attribute("component", "agent")
       # Perform operation
   ```

3. **Check Exporter Configuration:**
   - Verify exporter endpoint
   - Check exporter credentials
   - Test exporter connectivity

4. **Verify Sampling:**
   - Check sampling configuration
   - Ensure sampling is enabled
   - Adjust sampling rate if needed

## Logging Problems

### Problem: Logs not appearing

**Symptoms:**
- No log output
- Logs not formatted correctly
- Missing log context
- Log levels not working

**Diagnosis:**
```python
import structlog

logger = structlog.get_logger()
# Test logging
logger.info("test message", component="test")
```

**Solutions:**

1. **Configure Structured Logging:**
   ```python
   import structlog

   structlog.configure(
       processors=[
           structlog.processors.TimeStamper(fmt="iso"),
           structlog.processors.JSONRenderer()
       ],
       wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
       context_class=dict,
       logger_factory=structlog.PrintLoggerFactory(),
       cache_logger_on_first_use=False,
   )
   ```

2. **Set Log Levels:**
   ```python
   import logging

   logging.basicConfig(level=logging.INFO)
   ```

3. **Check Log Output:**
   - Verify log destination
   - Check log file permissions
   - Test log output

4. **Add Context:**
   ```python
   logger = logger.bind(
       component="agent",
       tenant_id="tenant_123",
       trace_id="trace-123"
   )
   logger.info("message")
   ```

## Metrics Collection Issues

### Problem: Metrics not being collected

**Symptoms:**
- Metrics not appearing
- Counter not incrementing
- Gauge values not updating
- Histogram not recording

**Diagnosis:**
```python
from prometheus_client import Counter

counter = Counter('requests_total', 'Total requests')
# Test counter
counter.inc()
print(f"Counter value: {counter._value.get()}")
```

**Solutions:**

1. **Define Metrics:**
   ```python
   from prometheus_client import Counter, Histogram, Gauge

   request_count = Counter('requests_total', 'Total requests')
   request_duration = Histogram('request_duration_seconds', 'Request duration')
   active_connections = Gauge('active_connections', 'Active connections')
   ```

2. **Record Metrics:**
   ```python
   request_count.inc()
   request_duration.observe(0.15)
   active_connections.set(10)
   ```

3. **Expose Metrics:**
   ```python
   from prometheus_client import start_http_server

   start_http_server(8000)  # Expose metrics on port 8000
   ```

4. **Check Metric Names:**
   - Use valid metric names
   - Follow naming conventions
   - Avoid special characters

## Export Failures

### Problem: Exports not working

**Symptoms:**
- Traces not exported
- Metrics not exported
- Export errors
- Connection failures

**Diagnosis:**
```python
# Test exporter connectivity
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

exporter = OTLPSpanExporter(endpoint="http://localhost:4317")
# Test export
try:
    exporter.export([span])
except Exception as e:
    print(f"Export error: {e}")
```

**Solutions:**

1. **Check Exporter Endpoint:**
   - Verify endpoint URL
   - Test endpoint connectivity
   - Check endpoint credentials

2. **Configure Retry Logic:**
   ```python
   from opentelemetry.sdk.trace.export import BatchSpanProcessor

   processor = BatchSpanProcessor(
       exporter,
       max_queue_size=2048,
       export_timeout_millis=30000,
       schedule_delay_millis=5000
   )
   ```

3. **Handle Export Errors:**
   - Implement error handling
   - Log export failures
   - Use fallback exporters

4. **Verify Backend:**
   - Check backend is running
   - Verify backend configuration
   - Test backend connectivity

## Performance Impact

### Problem: Observability causing performance issues

**Symptoms:**
- High latency
- Increased CPU usage
- Memory usage high
- Slowdown in operations

**Diagnosis:**
```python
import time

# Measure overhead
start = time.time()
# Operation with observability
duration = time.time() - start
print(f"Operation took {duration} seconds")
```

**Solutions:**

1. **Adjust Sampling Rate:**
   ```python
   from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

   sampler = TraceIdRatioBased(0.1)  # Sample 10% of traces
   trace.set_tracer_provider(TracerProvider(sampler=sampler))
   ```

2. **Use Batch Processing:**
   - Use batch exporters
   - Batch span exports
   - Optimize batch size

3. **Reduce Attribute Collection:**
   ```python
   # Only collect essential attributes
   span.set_attribute("essential", "value")
   # Avoid collecting large data
   ```

4. **Optimize Logging:**
   - Use appropriate log levels
   - Avoid logging in hot paths
   - Use async logging

## Configuration Problems

### Problem: Configuration not working

**Symptoms:**
- Configuration not applied
- Default values used
- Configuration errors
- Settings ignored

**Diagnosis:**
```python
# Check configuration
from opentelemetry import trace

tracer_provider = trace.get_tracer_provider()
print(f"Tracer provider: {tracer_provider}")
```

**Solutions:**

1. **Verify Configuration Order:**
   - Configure before creating tracers
   - Set up exporters before use
   - Initialize in correct order

2. **Check Environment Variables:**
   ```python
   import os

   # Check OTEL environment variables
   print(f"OTEL_EXPORTER_OTLP_ENDPOINT: {os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT')}")
   ```

3. **Use Configuration Files:**
   - Create configuration files
   - Load from environment
   - Validate configuration

4. **Test Configuration:**
   - Test with minimal config
   - Verify each setting
   - Check configuration logs

## Best Practices

1. **Minimize Performance Impact:**
   - Use sampling
   - Batch exports
   - Optimize attribute collection

2. **Handle Errors Gracefully:**
   ```python
   try:
       with tracer.start_as_current_span("operation") as span:
           # Operation
   except Exception as e:
       span.record_exception(e)
       raise
   ```

3. **Use Structured Logging:**
   - Include context
   - Use appropriate levels
   - Format consistently

4. **Monitor Observability:**
   - Track observability metrics
   - Monitor export success
   - Check performance impact

5. **Configure Appropriately:**
   - Set sampling rates
   - Configure exporters
   - Optimize settings

## Getting Help

If you continue to experience issues:

1. Check the logs for detailed error messages
2. Review the OpenTelemetry documentation
3. Verify your configuration matches the examples
4. Test with minimal configuration
5. Check exporter connectivity
6. Review OpenTelemetry and Prometheus documentation

