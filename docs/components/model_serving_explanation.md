# Motadata Model Serving - Comprehensive Component Explanation

## Overview

The Model Serving component provides infrastructure for serving ML models in production with REST APIs, batch processing, and real-time inference capabilities.

## Table of Contents

1. [Model Server](#model-server)
2. [Batch Predictor](#batch-predictor)
3. [Realtime Predictor](#realtime-predictor)
4. [Exception Handling](#exception-handling)
5. [Functions](#functions)
6. [Workflow](#workflow)
7. [Customization](#customization)

---

## Model Server

### Functionality

ModelServer provides REST API for model serving:
- **REST API**: FastAPI-based REST endpoints
- **Model Loading**: Load models on-demand
- **Request Handling**: Handle prediction requests
- **Health Endpoints**: Health check endpoints
- **Error Handling**: Graceful error handling

### Code Examples

#### Start Model Server

```python
from src.core.machine_learning.model_serving import ModelServer
from src.core.machine_learning.ml_framework import ModelManager

# Create model manager
model_manager = ModelManager(db, tenant_id="tenant_123")

# Create and start server
server = ModelServer(
    model_manager=model_manager,
    host="0.0.0.0",
    port=8000,
    tenant_id="tenant_123"
)

# Start server (blocking)
server.start_server()
```

#### API Endpoints

The server provides the following endpoints:

- **POST /predict/{model_id}**: Make predictions
  ```json
  {
    "input_data": [1, 2, 3, 4, 5]
  }
  ```

- **GET /health**: Health check
  ```json
  {
    "status": "healthy"
  }
  ```

#### Using the API

```python
import requests

# Make prediction
response = requests.post(
    "http://localhost:8000/predict/ticket_classifier",
    json={"input_data": [1, 2, 3, 4, 5]}
)
prediction = response.json()["prediction"]

# Check health
health = requests.get("http://localhost:8000/health")
print(health.json())
```

---

## Batch Predictor

### Functionality

BatchPredictor handles batch prediction jobs:
- **Job Submission**: Submit batch prediction jobs
- **Job Tracking**: Track job status and progress
- **Result Retrieval**: Retrieve batch results
- **Job Management**: Manage batch jobs

### Code Examples

#### Submit Batch Job

```python
from src.core.machine_learning.model_serving import BatchPredictor
from src.core.machine_learning.ml_framework import ModelManager

model_manager = ModelManager(db, tenant_id="tenant_123")
batch_predictor = BatchPredictor(model_manager, tenant_id="tenant_123")

# Submit batch job
job_id = batch_predictor.submit_batch(
    model_id="ticket_classifier",
    input_batch=[
        [1, 2, 3, 4, 5],
        [6, 7, 8, 9, 10],
        [11, 12, 13, 14, 15]
    ],
    job_id="batch_job_123"
)

# Check job status
status = batch_predictor.get_batch_status(job_id)
print(f"Job status: {status['status']}")
print(f"Input count: {status['input_count']}")

# Get results
results = batch_predictor.get_batch_results(job_id)
print(f"Predictions: {results}")
```

---

## Realtime Predictor

### Functionality

RealtimePredictor provides low-latency inference:
- **Fast Predictions**: Optimized for low latency
- **Caching**: Cache frequent predictions
- **Model Loading**: Efficient model loading
- **Error Handling**: Fast error responses

### Code Examples

#### Real-time Predictions

```python
from src.core.machine_learning.model_serving import RealtimePredictor
from src.core.machine_learning.ml_framework import ModelManager
from src.core.cache_mechanism import CacheMechanism

model_manager = ModelManager(db, tenant_id="tenant_123")
cache = CacheMechanism(...)

realtime_predictor = RealtimePredictor(
    model_manager=model_manager,
    cache=cache,
    tenant_id="tenant_123"
)

# Make real-time prediction
prediction = realtime_predictor.predict(
    model_id="ticket_classifier",
    input_data=[1, 2, 3, 4, 5]
)

print(f"Prediction: {prediction}")
```

---

## Exception Handling

### Exception Hierarchy

```python
ModelServingError
├── ServerError
├── BatchJobError
└── InferenceError
```

### Code Examples

```python
from src.core.machine_learning.model_serving.exceptions import (
    ServerError,
    BatchJobError,
    InferenceError
)

try:
    server.start_server()
except ServerError as e:
    print(f"Server error: {e.message}")

try:
    batch_predictor.submit_batch(...)
except BatchJobError as e:
    print(f"Batch job error: {e.message}")

try:
    realtime_predictor.predict(...)
except InferenceError as e:
    print(f"Inference error: {e.message}")
```

---

## Functions

### Factory Functions

```python
from src.core.machine_learning.model_serving.functions import (
    create_model_server,
    create_batch_predictor,
    create_realtime_predictor
)

# Create components
server = create_model_server(
    model_manager=model_manager,
    host="0.0.0.0",
    port=8000,
    tenant_id="tenant_123"
)

batch_predictor = create_batch_predictor(
    model_manager=model_manager,
    tenant_id="tenant_123"
)

realtime_predictor = create_realtime_predictor(
    model_manager=model_manager,
    cache=cache,
    tenant_id="tenant_123"
)
```

---

## Workflow

### Model Serving Workflow

1. **Model Loading**: Load model into memory
2. **Request Reception**: Receive prediction request
3. **Input Validation**: Validate input data
4. **Preprocessing**: Preprocess input if needed
5. **Prediction**: Make prediction
6. **Postprocessing**: Postprocess result
7. **Response**: Return prediction result

### Batch Processing Workflow

1. **Job Submission**: Submit batch job with input data
2. **Job Queuing**: Queue job for processing
3. **Batch Processing**: Process batch in chunks
4. **Result Storage**: Store results
5. **Result Retrieval**: Retrieve results by job ID

---

## Customization

### Custom Server Endpoints

```python
class CustomModelServer(ModelServer):
    def _setup_routes(self):
        super()._setup_routes()

        @self.app.post("/predict_batch/{model_id}")
        async def predict_batch(model_id: str, input_batch: list):
            # Custom batch endpoint
            pass
```

### Custom Batch Processing

```python
class CustomBatchPredictor(BatchPredictor):
    def process_batch(self, model_id, input_batch):
        # Custom batch processing logic
        return results
```

