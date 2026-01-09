# Getting Started with Model Serving

## Overview

The Model Serving component provides infrastructure for serving ML models with REST APIs and batch processing. This guide explains the complete workflow from server creation to prediction serving.

## Entry Point

The primary entry point for model serving:

```python
from src.core.machine_learning.model_serving import (
    create_model_server,
    create_batch_predictor,
    create_realtime_predictor
)
```

## Input Requirements

### Required Inputs

1. **Model Manager**: Model manager instance
2. **Server Configuration**:
   - `host`: Server host
   - `port`: Server port

## Process Flow

### Step 1: Model Server Creation

**What Happens:**
1. Server is initialized
2. Model manager is attached
3. API endpoints are configured
4. Server is ready to serve

**Code:**
```python
server = create_model_server(
    model_manager=model_manager,
    host="0.0.0.0",
    port=8000,
    tenant_id="tenant_123"
)
```

### Step 2: Server Start

**What Happens:**
1. Server starts listening
2. Endpoints are registered
3. Models are loaded
4. Server is ready for requests

**Code:**
```python
server.start_server()
```

### Step 3: Prediction Request

**What Happens:**
1. Request is received
2. Model is loaded
3. Prediction is made
4. Response is returned

**Code:**
```python
# Via API
POST http://localhost:8000/predict/ticket_classifier
{
    "input_data": [1, 2, 3, 4, 5]
}

# Response
{
    "prediction": 1,
    "confidence": 0.9
}
```

## Output

### Prediction Response

```python
{
    "prediction": 1,
    "probabilities": [0.1, 0.9],
    "confidence": 0.9,
    "model_id": "ticket_classifier",
    "model_version": "1.0.0"
}
```

## Where Output is Used

### 1. API Integration

```python
import requests

response = requests.post(
    "http://localhost:8000/predict/ticket_classifier",
    json={"input_data": [1, 2, 3, 4, 5]}
)

prediction = response.json()["prediction"]
```

## Complete Example

```python
from src.core.machine_learning.model_serving import create_model_server
from src.core.machine_learning.ml_framework import create_model_manager
from src.core.postgresql_database import DatabaseConnection

# Step 1: Initialize (Entry Point)
db = DatabaseConnection(...)
model_manager = create_model_manager(db, tenant_id="tenant_123")

# Step 2: Create Server (Entry Point)
server = create_model_server(
    model_manager=model_manager,
    host="0.0.0.0",
    port=8000,
    tenant_id="tenant_123"
)

# Step 3: Start Server (Process)
server.start_server()

# Step 4: Use API (Output)
# POST http://localhost:8000/predict/ticket_classifier
# {"input_data": [1, 2, 3, 4, 5]}
```

## Next Steps

- See [README.md](README.md) for detailed component documentation
- Check [component_explanation/model_serving_explanation.md](../../../../component_explanation/model_serving_explanation.md) for comprehensive guide
- Review [troubleshooting guide](../../../../docs/troubleshooting/model_serving_troubleshooting.md) for common issues

