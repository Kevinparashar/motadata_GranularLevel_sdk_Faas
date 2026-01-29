# Motadata Model Serving Troubleshooting Guide

This guide helps diagnose and resolve common issues encountered when using Model Serving.

## Table of Contents

1. [Server Startup Issues](#server-startup-issues)
2. [API Request Failures](#api-request-failures)
3. [Batch Processing Problems](#batch-processing-problems)
4. [Real-time Prediction Issues](#real-time-prediction-issues)
5. [Performance Problems](#performance-problems)

## Server Startup Issues

### Problem: Server fails to start

**Symptoms:**
- `ServerError` exceptions
- Port already in use
- Server not responding
- Health check fails

**Diagnosis:**
1. Check port availability:
```python
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(('localhost', 8000))
if result == 0:
    print("Port is in use")
else:
    print("Port is available")
sock.close()
```

2. Check server configuration:
```python
server = ModelServer(
    model_manager=model_manager,
    host="0.0.0.0",
    port=8000
)
```

**Solutions:**

1. **Port Already in Use:**
   - Use different port
   - Stop existing server
   - Check for other processes using port

2. **Model Manager Issues:**
   - Verify model manager is initialized
   - Check database connection
   - Validate model manager configuration

3. **Host Configuration:**
   - Use "0.0.0.0" for all interfaces
   - Use "127.0.0.1" for local only
   - Check firewall settings

## API Request Failures

### Problem: API requests fail

**Symptoms:**
- 500 errors
- Timeout errors
- Invalid response format
- Model not found errors

**Diagnosis:**
1. Check API endpoint:
```python
import requests
try:
    response = requests.post(
        "http://localhost:8000/predict/ticket_classifier",
        json={"input_data": [1, 2, 3, 4, 5]},
        timeout=10
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except requests.exceptions.RequestException as e:
    print(f"Request error: {e}")
```

2. Check model exists:
```python
model_info = model_manager.get_model("ticket_classifier")
if not model_info:
    print("Model not found")
```

**Solutions:**

1. **Model Not Found:**
   - Verify model is registered
   - Check model ID is correct
   - Ensure model is loaded

2. **Input Format Issues:**
   - Validate input data format
   - Check input shape matches model
   - Verify data types

3. **Timeout Issues:**
   - Increase timeout
   - Optimize model inference
   - Check system resources

## Batch Processing Problems

### Problem: Batch jobs fail or hang

**Symptoms:**
- `BatchJobError` exceptions
- Jobs stuck in pending
- Results not available
- Job status not updating

**Diagnosis:**
1. Check job status:
```python
status = batch_predictor.get_batch_status(job_id)
print(f"Status: {status['status']}")
print(f"Input count: {status['input_count']}")
```

2. Check batch input:
```python
if len(input_batch) == 0:
    print("Empty batch")
```

**Solutions:**

1. **Empty Batch:**
   - Verify input batch is not empty
   - Check batch format
   - Validate input data

2. **Job Stuck:**
   - Check job processing
   - Verify model is loaded
   - Review error logs

3. **Results Not Available:**
   - Wait for job completion
   - Check job status
   - Verify results storage

## Real-time Prediction Issues

### Problem: Real-time predictions fail or are slow

**Symptoms:**
- `InferenceError` exceptions
- High latency
- Predictions timeout
- Cache misses

**Diagnosis:**
1. Check prediction latency:
```python
import time
start = time.time()
prediction = realtime_predictor.predict(...)
latency = time.time() - start
print(f"Latency: {latency}s")
```

2. Check cache:
```python
if cache:
    cache_key = f"realtime_pred:{model_id}:{hash(str(input_data))}"
    cached = cache.get(cache_key)
    if cached:
        print("Cache hit")
    else:
        print("Cache miss")
```

**Solutions:**

1. **High Latency:**
   - Optimize model
   - Use caching
   - Reduce input size
   - Use faster models

2. **Cache Issues:**
   - Enable caching
   - Check cache configuration
   - Verify cache is working

3. **Model Loading:**
   - Pre-load models
   - Use model pooling
   - Optimize model size

## Performance Problems

### Problem: Slow serving performance

**Symptoms:**
- High response times
- Low throughput
- Resource exhaustion
- Timeout errors

**Solutions:**

1. **Optimize Model:**
   - Use smaller models
   - Reduce feature count
   - Use model compression

2. **Use Caching:**
   ```python
   realtime_predictor = RealtimePredictor(
       model_manager=model_manager,
       cache=cache  # Enable caching
   )
   ```

3. **Batch Processing:**
   - Use batch predictions for multiple requests
   - Process in parallel
   - Optimize batch size

4. **Resource Management:**
   - Increase server resources
   - Use load balancing
   - Implement connection pooling

