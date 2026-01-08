# LiteLLM Gateway Troubleshooting Guide

This guide helps diagnose and resolve common issues encountered when using the LiteLLM Gateway.

## Table of Contents

1. [Connection Failures](#connection-failures)
2. [Rate Limiting Issues](#rate-limiting-issues)
3. [Circuit Breaker Problems](#circuit-breaker-problems)
4. [Provider Failures](#provider-failures)
5. [Request Deduplication Issues](#request-deduplication-issues)
6. [Request Batching Problems](#request-batching-problems)
7. [Health Check Failures](#health-check-failures)
8. [Validation Errors](#validation-errors)
9. [Performance Issues](#performance-issues)

## Connection Failures

### Problem: Cannot connect to LLM providers

**Symptoms:**
- Connection timeout errors
- Network errors
- API key authentication failures
- Provider unavailable errors

**Diagnosis:**
1. Check gateway health:
```python
health = await gateway.get_health()
print(health)
```

2. Test provider connectivity:
```python
try:
    response = await gateway.generate_async(
        prompt="Test",
        model="gpt-4"
    )
except Exception as e:
    print(f"Error: {e}")
```

**Solutions:**

1. **API Key Issues:**
   - Verify API keys are set in environment variables
   - Check key format: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.
   - Ensure keys are not expired or revoked
   - Verify key permissions and quotas

2. **Network Issues:**
   - Check internet connectivity
   - Verify firewall rules allow outbound connections
   - Test with different network
   - Check DNS resolution

3. **Provider Configuration:**
   - Verify provider is in `model_list`
   - Check provider endpoint URLs
   - Verify provider-specific configuration

4. **Timeout Configuration:**
   ```python
   config = GatewayConfig(
       timeout=120.0,  # Increase timeout
       max_retries=5   # Increase retries
   )
   gateway = LiteLLMGateway(config=config)
   ```

## Rate Limiting Issues

### Problem: Rate limit errors (429)

**Symptoms:**
- `429 Too Many Requests` errors
- Rate limit exceeded messages
- Requests being queued indefinitely
- High latency during rate limiting

**Diagnosis:**
```python
# Check rate limiter status
rate_limiter = gateway._get_rate_limiter(tenant_id="tenant_123")
if rate_limiter:
    stats = rate_limiter.get_stats()
    print(f"Rate limit status: {stats}")
```

**Solutions:**

1. **Enable Request Queuing:**
   ```python
   from src.core.litellm_gateway.rate_limiter import RateLimitConfig

   config = GatewayConfig(
       enable_rate_limiting=True,
       rate_limit_config=RateLimitConfig(
           requests_per_minute=60,
           enable_queuing=True,
           queue_timeout=300.0
       )
   )
   ```

2. **Adjust Rate Limits:**
   ```python
   rate_limit_config = RateLimitConfig(
       requests_per_minute=30,  # Reduce rate
       burst_size=5,
       enable_queuing=True
   )
   ```

3. **Use Request Deduplication:**
   ```python
   config = GatewayConfig(
       enable_request_deduplication=True
   )
   ```

4. **Implement Exponential Backoff:**
   - Gateway automatically implements exponential backoff
   - Adjust retry configuration if needed

## Circuit Breaker Problems

### Problem: Circuit breaker is OPEN

**Symptoms:**
- All requests rejected immediately
- Error: "Circuit breaker is OPEN"
- Service unavailable errors
- No requests reaching providers

**Diagnosis:**
```python
if gateway.circuit_breaker:
    stats = gateway.circuit_breaker.get_stats()
    print(f"Circuit state: {stats['state']}")
    print(f"Failures: {stats['failures']}")
    print(f"Last failure: {stats['last_failure_time']}")
```

**Solutions:**

1. **Wait for Automatic Recovery:**
   - Circuit breaker transitions to HALF_OPEN after timeout
   - Default timeout is 60 seconds
   - Monitor circuit breaker state

2. **Manual Reset (if safe):**
   ```python
   if gateway.circuit_breaker:
       gateway.circuit_breaker.reset()
   ```

3. **Adjust Circuit Breaker Configuration:**
   ```python
   from src.core.utils.circuit_breaker import CircuitBreakerConfig

   config = GatewayConfig(
       enable_circuit_breaker=True,
       circuit_breaker_config=CircuitBreakerConfig(
           failure_threshold=10,  # Increase threshold
           success_threshold=3,   # Require more successes
           timeout=120.0          # Longer recovery time
       )
   )
   ```

4. **Check Underlying Issues:**
   - Verify provider is operational
   - Check network connectivity
   - Verify API keys and quotas
   - Review error logs for root cause

## Provider Failures

### Problem: Provider health is unhealthy

**Symptoms:**
- Provider health status is "unhealthy"
- Requests failing for specific provider
- Automatic fallback not working

**Diagnosis:**
```python
health = await gateway.get_health()
print(f"Provider health: {health.get('provider_health', {})}")
```

**Solutions:**

1. **Check Provider Status:**
   - Visit provider status page
   - Check provider API documentation
   - Verify provider is operational

2. **Configure Fallback Providers:**
   ```python
   config = GatewayConfig(
       model_list=[
           {"model_name": "gpt-4", "litellm_params": {"model": "gpt-4"}},
           {"model_name": "claude-3", "litellm_params": {"model": "claude-3-opus"}}
       ],
       fallbacks=["claude-3", "gpt-3.5-turbo"]
   )
   ```

3. **Manual Provider Selection:**
   ```python
   # Use specific provider
   response = await gateway.generate_async(
       prompt="Test",
       model="claude-3-opus"  # Specify fallback model
   )
   ```

4. **Reset Provider Health:**
   - Restart gateway to reset health status
   - Or wait for automatic health check recovery

## Request Deduplication Issues

### Problem: Deduplication not working

**Symptoms:**
- Duplicate requests being sent
- Cache not being used
- High API costs

**Diagnosis:**
```python
if gateway.deduplicator:
    stats = gateway.deduplicator.get_stats()
    print(f"Deduplication stats: {stats}")
```

**Solutions:**

1. **Enable Deduplication:**
   ```python
   config = GatewayConfig(
       enable_request_deduplication=True
   )
   ```

2. **Adjust TTL:**
   ```python
   from src.core.litellm_gateway.rate_limiter import RequestDeduplicator

   deduplicator = RequestDeduplicator(ttl=600.0)  # 10 minutes
   ```

3. **Check Request Uniqueness:**
   - Ensure requests have unique identifiers
   - Verify prompt and model combination
   - Check tenant_id is included

## Request Batching Problems

### Problem: Batching not working as expected

**Symptoms:**
- Requests not being batched
- High latency with batching
- Batch size too large or too small

**Diagnosis:**
```python
if gateway.batcher:
    stats = gateway.batcher.get_stats()
    print(f"Batching stats: {stats}")
```

**Solutions:**

1. **Enable Batching:**
   ```python
   config = GatewayConfig(
       enable_request_batching=True
   )
   ```

2. **Adjust Batch Configuration:**
   ```python
   from src.core.litellm_gateway.rate_limiter import RequestBatcher

   batcher = RequestBatcher(
       max_batch_size=10,
       batch_timeout=2.0
   )
   ```

3. **Optimize Batch Size:**
   - Increase `max_batch_size` for better throughput
   - Decrease for lower latency
   - Balance based on use case

## Health Check Failures

### Problem: Health check reports unhealthy

**Symptoms:**
- Health status is "unhealthy"
- Gateway operations failing
- Degraded performance

**Diagnosis:**
```python
health = await gateway.get_health()
print(health)
```

**Solutions:**

1. **Check Provider Health:**
   - Verify all providers are operational
   - Check provider API status
   - Test provider connectivity

2. **Review Health Check Configuration:**
   ```python
   config = GatewayConfig(
       enable_health_monitoring=True
   )
   ```

3. **Check Error Rates:**
   - Review error logs
   - Check error rates in health metrics
   - Identify failing operations

4. **Reset Health Status:**
   - Restart gateway
   - Clear health check cache
   - Wait for automatic recovery

## Validation Errors

### Problem: Validation failures

**Symptoms:**
- `ValidationError` exceptions
- Output validation failures
- Content filtering errors

**Diagnosis:**
```python
# Check validation configuration
config = gateway.config
print(f"Validation level: {config.validation_level}")
print(f"Validation enabled: {config.enable_validation}")
```

**Solutions:**

1. **Adjust Validation Level:**
   ```python
   from src.core.validation import ValidationLevel

   config = GatewayConfig(
       enable_validation=True,
       validation_level=ValidationLevel.MODERATE  # or STRICT, LENIENT
   )
   ```

2. **Disable Validation (if needed):**
   ```python
   config = GatewayConfig(
       enable_validation=False
   )
   ```

3. **Custom Validation Rules:**
   ```python
   from src.core.validation import ValidationManager

   validator = ValidationManager(
       validation_level=ValidationLevel.MODERATE
   )
   # Add custom rules
   ```

## Performance Issues

### Problem: Gateway is slow

**Symptoms:**
- High latency
- Slow response times
- Timeout errors
- High resource usage

**Diagnosis:**
1. Check response times:
```python
import time
start = time.time()
response = await gateway.generate_async(prompt="Test")
duration = time.time() - start
print(f"Response time: {duration} seconds")
```

2. Check health metrics:
```python
health = await gateway.get_health()
print(f"Metrics: {health.get('metrics', {})}")
```

**Solutions:**

1. **Enable Caching:**
   - Use cache for repeated queries
   - Configure appropriate TTL
   - Monitor cache hit rates

2. **Optimize Model Selection:**
   - Use faster models for simple tasks
   - Use smaller models when appropriate
   - Balance quality vs. speed

3. **Enable Request Deduplication:**
   ```python
   config = GatewayConfig(
       enable_request_deduplication=True
   )
   ```

4. **Use Request Batching:**
   ```python
   config = GatewayConfig(
       enable_request_batching=True
   )
   ```

5. **Optimize Configuration:**
   - Reduce timeout for faster failures
   - Adjust retry counts
   - Optimize connection pooling

## Best Practices

1. **Monitor Health:**
   ```python
   health = await gateway.get_health()
   if health['status'] != 'healthy':
       # Handle unhealthy state
   ```

2. **Handle Errors Gracefully:**
   ```python
   try:
       response = await gateway.generate_async(prompt="Test")
   except Exception as e:
       # Handle error
       logger.error(f"Gateway error: {e}")
   ```

3. **Use Circuit Breaker:**
   ```python
   if gateway.circuit_breaker:
       stats = gateway.circuit_breaker.get_stats()
       if stats['state'] == 'open':
           # Handle open circuit
   ```

4. **Monitor Rate Limits:**
   - Track rate limit usage
   - Adjust rate limits based on usage
   - Use queuing for better handling

5. **Enable Observability:**
   - Use LLMOps for tracking
   - Monitor costs and usage
   - Track performance metrics

## Getting Help

If you continue to experience issues:

1. Check the logs for detailed error messages
2. Review the LiteLLM Gateway documentation
3. Verify your configuration matches the examples
4. Test with minimal configuration to isolate issues
5. Check provider status pages
6. Review GitHub issues for known problems

