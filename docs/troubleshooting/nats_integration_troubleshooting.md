# NATS Integration Troubleshooting

## Common Issues and Solutions

### Connection Issues

#### Problem: NATS Connection Failed

**Symptoms:**
- Error: `ConnectionError: NATS connection failed`
- Components unable to publish/subscribe to topics

**Possible Causes:**
1. NATS server not running
2. Incorrect connection URL
3. Network connectivity issues
4. Authentication failures

**Resolution Steps:**

1. **Verify NATS Server Status:**
   ```bash
   # Check if NATS server is running
   nats server check
   ```

2. **Check Connection URL:**
   ```python
   # Verify NATS_URL environment variable
   import os
   print(os.getenv("NATS_URL", "nats://localhost:4222"))
   ```

3. **Test Network Connectivity:**
   ```bash
   # Test NATS server connectivity
   telnet localhost 4222
   ```

4. **Check Authentication:**
   - Verify credentials in connection configuration
   - Check token or username/password

**Prevention:**
- Use connection pooling
- Implement retry logic with exponential backoff
- Monitor connection health

---

#### Problem: NATS Connection Timeout

**Symptoms:**
- Timeout errors when connecting
- Slow connection establishment

**Possible Causes:**
1. NATS server overloaded
2. Network latency
3. Firewall blocking connections

**Resolution Steps:**

1. **Increase Timeout:**
   ```python
   # Configure longer timeout
   nats_client = NATSClient(
       url="nats://localhost:4222",
       connect_timeout=30.0  # 30 seconds
   )
   ```

2. **Check Server Load:**
   ```bash
   # Monitor NATS server metrics
   nats server info
   ```

3. **Verify Firewall Rules:**
   - Ensure port 4222 (or configured port) is open
   - Check security group rules

---

### Message Publishing Issues

#### Problem: Message Not Published

**Symptoms:**
- `publish()` call succeeds but message not received
- No errors but subscribers don't receive messages

**Possible Causes:**
1. Incorrect topic name
2. No active subscribers
3. Message size exceeds limits
4. Topic permissions

**Resolution Steps:**

1. **Verify Topic Name:**
   ```python
   # Check topic naming convention
   topic = f"ai.agent.message.{tenant_id}"
   print(f"Publishing to: {topic}")
   ```

2. **Check Subscribers:**
   ```python
   # Verify subscribers are active
   # Check subscription status
   ```

3. **Check Message Size:**
   ```python
   # Verify message size
   message_size = len(payload)
   if message_size > 1_000_000:  # 1MB limit
       print(f"Message too large: {message_size} bytes")
   ```

4. **Verify Permissions:**
   - Check NATS server permissions
   - Verify tenant isolation

---

#### Problem: Message Publishing Slow

**Symptoms:**
- High latency when publishing messages
- Throughput below expected

**Possible Causes:**
1. NATS server overloaded
2. Large message payloads
3. Network congestion
4. Serialization overhead

**Resolution Steps:**

1. **Monitor NATS Performance:**
   ```bash
   # Check NATS server metrics
   nats server stats
   ```

2. **Optimize Message Size:**
   ```python
   # Use compression for large payloads
   # Consider chunking for very large messages
   ```

3. **Batch Publishing:**
   ```python
   # Publish multiple messages in batch
   await asyncio.gather(*[
       nats_client.publish(topic, msg) for msg in messages
   ])
   ```

---

### Message Subscription Issues

#### Problem: Messages Not Received

**Symptoms:**
- Subscriber registered but no messages received
- Messages published but not consumed

**Possible Causes:**
1. Subscription not active
2. Queue group configuration
3. Message filtering issues
4. Subscription callback errors

**Resolution Steps:**

1. **Verify Subscription:**
   ```python
   # Check subscription is active
   subscription = await nats_client.subscribe(
       subject=f"ai.agent.message.{tenant_id}",
       callback=handler
   )
   print(f"Subscription active: {subscription.is_active()}")
   ```

2. **Check Queue Group:**
   ```python
   # Verify queue group configuration
   # Ensure queue group matches expected behavior
   ```

3. **Debug Callback:**
   ```python
   async def debug_handler(msg):
       try:
           # Process message
           pass
       except Exception as e:
           logger.error(f"Error in handler: {e}", exc_info=True)
   ```

---

#### Problem: Duplicate Messages

**Symptoms:**
- Same message received multiple times
- Message processing duplicated

**Possible Causes:**
1. Multiple subscriptions to same topic
2. Queue group misconfiguration
3. Message replay

**Resolution Steps:**

1. **Check Subscriptions:**
   ```python
   # Ensure only one subscription per topic
   # Use queue groups for load balancing
   ```

2. **Implement Idempotency:**
   ```python
   # Track processed message IDs
   processed_ids = set()
   
   async def handler(msg):
       msg_id = extract_message_id(msg)
       if msg_id in processed_ids:
           return  # Skip duplicate
       processed_ids.add(msg_id)
       # Process message
   ```

---

### Performance Issues

#### Problem: High Latency

**Symptoms:**
- Message round-trip time > 10ms
- Slow request-response patterns

**Possible Causes:**
1. Network latency
2. NATS server performance
3. Serialization overhead
4. Message queue depth

**Resolution Steps:**

1. **Measure Latency:**
   ```python
   start = time.time()
   response = await nats_client.request(topic, payload, timeout=10.0)
   latency = (time.time() - start) * 1000
   print(f"Latency: {latency}ms")
   ```

2. **Optimize Serialization:**
   - Use efficient encoding (e.g., MessagePack)
   - Minimize payload size

3. **Check Queue Depth:**
   ```bash
   # Monitor NATS queue depth
   nats server stats
   ```

---

#### Problem: Low Throughput

**Symptoms:**
- Messages per second below target
- Queue backlog building

**Possible Causes:**
1. Slow message processing
2. Limited NATS server capacity
3. Network bandwidth constraints

**Resolution Steps:**

1. **Increase Workers:**
   ```python
   # Use multiple workers in queue group
   await nats_client.subscribe(
       subject=topic,
       callback=handler,
       queue="workers"  # Multiple workers share load
   )
   ```

2. **Parallel Processing:**
   ```python
   # Process messages concurrently
   async def process_batch(messages):
       await asyncio.gather(*[process(msg) for msg in messages])
   ```

---

### Error Handling

#### Problem: Unhandled NATS Errors

**Symptoms:**
- Exceptions not caught
- Application crashes

**Resolution:**

```python
try:
    await nats_client.publish(topic, payload)
except ConnectionError as e:
    logger.error(f"NATS connection error: {e}")
    # Implement retry logic
except TimeoutError as e:
    logger.error(f"NATS timeout: {e}")
    # Handle timeout
except Exception as e:
    logger.error(f"Unexpected NATS error: {e}", exc_info=True)
    # Handle unexpected errors
```

---

## Best Practices

1. **Connection Management:**
   - Use connection pooling
   - Implement health checks
   - Handle reconnection automatically

2. **Error Handling:**
   - Always wrap NATS operations in try-except
   - Implement retry logic with backoff
   - Log errors with context

3. **Performance:**
   - Batch operations when possible
   - Use queue groups for load balancing
   - Monitor message queue depth

4. **Monitoring:**
   - Track publish/subscribe rates
   - Monitor latency percentiles
   - Alert on connection failures

---

## See Also

- [NATS Integration Guide](../../integration_guides/nats_integration_guide.md)
- [CORE_COMPONENTS_INTEGRATION_STORY.md](../../../CORE_COMPONENTS_INTEGRATION_STORY.md)
- Core SDK NATS wrapper documentation

