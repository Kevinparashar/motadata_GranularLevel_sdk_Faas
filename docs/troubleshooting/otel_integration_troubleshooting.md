# Motadata OTEL Integration Troubleshooting

## Common Issues and Solutions

### Tracing Issues

#### Problem: Traces Not Appearing

**Symptoms:**
- Traces created but not visible in backend
- No trace data exported

**Possible Causes:**
1. OTEL exporter not configured
2. Exporter endpoint incorrect
3. Network connectivity to collector
4. Trace sampling too aggressive

**Resolution Steps:**

1. **Verify Exporter Configuration:**
   ```bash
   # Check environment variables
   echo $OTEL_EXPORTER_OTLP_ENDPOINT
   echo $OTEL_SERVICE_NAME
   ```

2. **Test Exporter Connection:**
   ```python
   # Test OTEL collector connectivity
   import requests
   response = requests.get("http://localhost:4317/health")
   print(response.status_code)
   ```

3. **Check Trace Sampling:**
   ```python
   # Verify sampling configuration
   # Ensure sampling rate is not 0
   ```

4. **Enable Debug Logging:**
   ```python
   import logging
   logging.getLogger("opentelemetry").setLevel(logging.DEBUG)
   ```

---

#### Problem: Incomplete Traces

**Symptoms:**
- Traces missing spans
- Child spans not appearing
- Trace context lost

**Possible Causes:**
1. Trace context not propagated
2. Spans not properly nested
3. Async context issues

**Resolution Steps:**

1. **Verify Trace Propagation:**
   ```python
   # Ensure trace context is passed between components
   trace_context = otel_tracer.get_context()
   # Pass context to next component
   ```

2. **Check Span Nesting:**
   ```python
   # Ensure parent span is passed correctly
   with otel_tracer.start_span("child", parent=parent_span) as child:
       # Child operations
       pass
   ```

3. **Handle Async Context:**
   ```python
   # Use async-compatible tracing
   async with otel_tracer.start_trace("operation") as trace:
       # Async operations
       pass
   ```

---

### Metrics Issues

#### Problem: Metrics Not Recorded

**Symptoms:**
- Metrics calls succeed but data not visible
- No metrics in dashboard

**Possible Causes:**
1. Metrics exporter not configured
2. Metric names not registered
3. Aggregation interval too long

**Resolution Steps:**

1. **Verify Metrics Exporter:**
   ```python
   # Check metrics exporter configuration
   # Ensure exporter is initialized
   ```

2. **Check Metric Names:**
   ```python
   # Use consistent metric naming
   # Follow naming conventions
   otel_metrics.increment_counter("gateway.requests.total", {
       "model": "gpt-4"
   })
   ```

3. **Force Metric Export:**
   ```python
   # Manually flush metrics
   otel_metrics.flush()
   ```

---

#### Problem: High Metrics Overhead

**Symptoms:**
- Performance degradation with metrics enabled
- High CPU usage from metrics collection

**Possible Causes:**
1. Too many metrics
2. High-frequency metric updates
3. Inefficient metric recording

**Resolution Steps:**

1. **Reduce Metric Frequency:**
   ```python
   # Batch metric updates
   # Update metrics periodically, not on every operation
   ```

2. **Use Efficient Metric Types:**
   ```python
   # Prefer counters over histograms for high-frequency events
   otel_metrics.increment_counter("events.total")
   # Use histograms only for latency measurements
   otel_metrics.record_histogram("operation.duration", duration)
   ```

3. **Disable Unnecessary Metrics:**
   ```python
   # Only record metrics that are actually used
   # Remove debug metrics in production
   ```

---

### Performance Issues

#### Problem: High Tracing Overhead

**Symptoms:**
- Operations slower with tracing enabled
- Overhead > 5% of operation time

**Possible Causes:**
1. Too many spans
2. Excessive attributes
3. Synchronous exporter

**Resolution Steps:**

1. **Reduce Span Count:**
   ```python
   # Combine related operations into single span
   # Only create spans for significant operations
   ```

2. **Limit Attributes:**
   ```python
   # Only set essential attributes
   span.set_attribute("key", "value")  # Essential only
   # Avoid setting large data as attributes
   ```

3. **Use Async Exporter:**
   ```python
   # Configure async/batch exporter
   # Reduces blocking on trace export
   ```

---

#### Problem: Trace Export Slow

**Symptoms:**
- Traces take long to appear
- Export queue backing up

**Possible Causes:**
1. Exporter endpoint slow
2. Large trace payloads
3. Network latency

**Resolution Steps:**

1. **Batch Exports:**
   ```python
   # Configure batch exporter
   # Export traces in batches, not individually
   ```

2. **Reduce Trace Size:**
   ```python
   # Limit attributes and events per span
   # Remove unnecessary trace data
   ```

3. **Use Local Collector:**
   ```python
   # Use local OTEL collector
   # Collector handles export to backend
   ```

---

### Logging Issues

#### Problem: Logs Not Appearing

**Symptoms:**
- Log statements execute but logs not visible
- Logs missing context

**Possible Causes:**
1. Log level too high
2. Log handler not configured
3. Trace context not in logs

**Resolution Steps:**

1. **Check Log Level:**
   ```python
   import logging
   logging.getLogger().setLevel(logging.INFO)
   ```

2. **Configure Structured Logging:**
   ```python
   # Use structured logging with trace context
   logger.info("Operation completed", extra={
       "trace_id": trace_context.trace_id,
       "span_id": trace_context.span_id
   })
   ```

3. **Verify Log Handler:**
   ```python
   # Ensure log handler is configured
   # Check log output destination
   ```

---

## Best Practices

1. **Tracing:**
   - Keep span count reasonable
   - Use meaningful span names
   - Propagate trace context correctly

2. **Metrics:**
   - Use appropriate metric types
   - Follow naming conventions
   - Batch metric updates when possible

3. **Performance:**
   - Monitor overhead
   - Use async exporters
   - Sample traces in high-volume scenarios

4. **Error Handling:**
   - Don't let tracing errors break operations
   - Log tracing errors separately
   - Implement fallback behavior

---

## See Also

- [OTEL Integration Guide](../../integration_guides/otel_integration_guide.md)
- [CORE_COMPONENTS_INTEGRATION_STORY.md](../../../CORE_COMPONENTS_INTEGRATION_STORY.md)
- Core SDK OTEL bootstrap documentation

