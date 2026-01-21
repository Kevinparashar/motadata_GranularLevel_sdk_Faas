# ML Service

## Overview

ML Service is a FaaS implementation of the Machine Learning Framework component. It provides REST API endpoints for model training, inference, batch prediction, and model management operations.

## API Endpoints

### Model Training

- `POST /api/v1/ml/models/train` - Train a new ML model

**Request Body:**
```json
{
  "model_name": "ticket_classifier",
  "dataset_id": "dataset_123",
  "model_type": "classification",
  "hyperparameters": {
    "learning_rate": 0.001,
    "epochs": 100
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Model training initiated",
  "data": {
    "model_id": "model_abc123"
  }
}
```

### Model Inference

- `POST /api/v1/ml/models/{model_id}/predict` - Make a prediction

**Request Body:**
```json
{
  "input_data": {
    "ticket_title": "Server down",
    "ticket_description": "Production server is not responding"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "prediction": "critical",
    "confidence": 0.95
  }
}
```

- `POST /api/v1/ml/models/{model_id}/predict/batch` - Batch prediction

### Model Management

- `GET /api/v1/ml/models` - List all models
- `GET /api/v1/ml/models/{model_id}` - Get model details
- `POST /api/v1/ml/models/{model_id}/deploy` - Deploy a trained model

**Request Body:**
```json
{
  "version": "1.0.0",
  "environment": "production"
}
```

## Service Dependencies

- **Database**: For model storage, training history, and metadata
- **Storage**: For model artifacts (optional, can use database)

## Stateless Architecture

The ML Service is **stateless**:
- ML system instances are created on-demand per request
- No in-memory caching of ML systems
- All models and training data stored in database

## Usage

```python
from src.faas.services.ml_service import create_ml_service

# Create service
service = create_ml_service(
    service_name="ml-service",
    config_overrides={
        "database_url": "postgresql://user:pass@localhost/db",
    }
)

# Run service
# uvicorn service.app:app --host 0.0.0.0 --port 8080
```

## Integration with Other Services

### Using NATS for Events

```python
# Publish model training completion event
event = {
    "event_type": "ml.model.trained",
    "model_id": model_id,
    "tenant_id": tenant_id,
}
await nats_client.publish(
    f"ml.events.{tenant_id}",
    codec_manager.encode(event)
)
```

## Configuration

```bash
SERVICE_NAME=ml-service
SERVICE_PORT=8080
DATABASE_URL=postgresql://user:pass@localhost/db
ENABLE_NATS=true
ENABLE_OTEL=true
```

## Example Request

```bash
# Train a model
curl -X POST http://localhost:8080/api/v1/ml/models/train \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant_123" \
  -d '{
    "model_name": "ticket_classifier",
    "dataset_id": "dataset_123",
    "model_type": "classification"
  }'

# Make a prediction
curl -X POST http://localhost:8080/api/v1/ml/models/model_abc123/predict \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant_123" \
  -d '{
    "input_data": {
      "ticket_title": "Server down"
    }
  }'
```

## Features

- **Model Lifecycle Management**: Create, train, deploy, version models
- **Training Orchestration**: Hyperparameter management and validation
- **Inference Engine**: Preprocessing, postprocessing, and caching
- **Batch Prediction**: Process multiple inputs efficiently
- **Model Versioning**: Track model versions and lineage
- **Multi-Tenant Support**: Full tenant isolation

