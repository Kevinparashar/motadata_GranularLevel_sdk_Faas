# Motadata Machine Learning Components

## Overview

The Machine Learning components provide comprehensive ML capabilities for ITSM SaaS platforms, including training, inference, MLOps, data management, and model serving. These components are designed for use cases that are better served by traditional ML algorithms rather than LLM/Agent-based approaches.

## Components

### 1. ML Framework (`ml_framework/`)
Core ML system for training, inference, and model management.
- **MLSystem**: Main orchestrator
- **ModelManager**: Model lifecycle management
- **Trainer**: Training orchestration
- **Predictor**: Inference engine
- **DataProcessor**: Data preprocessing
- **ModelRegistry**: Model versioning

### 2. MLOps Pipeline (`mlops/`)
End-to-end MLOps capabilities.
- **MLOpsPipeline**: Pipeline orchestrator
- **ExperimentTracker**: MLflow integration
- **ModelVersioning**: Version control
- **ModelDeployment**: Deployment management
- **ModelMonitoring**: Performance monitoring
- **DriftDetector**: Drift detection

### 3. Data Management (`ml_data_management/`)
Data lifecycle and feature store.
- **DataManager**: Data lifecycle
- **DataLoader**: Load from various sources
- **DataValidator**: Data validation
- **FeatureStore**: Centralized feature storage
- **DataPipeline**: ETL pipelines

### 4. Model Serving (`model_serving/`)
Model serving infrastructure.
- **ModelServer**: REST API server
- **BatchPredictor**: Batch predictions
- **RealtimePredictor**: Real-time inference

### 5. Use Cases (`use_cases/`)
Template structure for ITSM-specific ML models.
- **BaseMLModel**: Base class for all use case models
- **ModelTemplate**: Template for creating new models

## Quick Start

```python
from src.core.machine_learning.ml_framework import MLSystem
from src.core.postgresql_database.connection import DatabaseConnection

# Initialize
ml_system = MLSystem(db, tenant_id="tenant_123")

# Train model
result = ml_system.train_model(
    model_id="ticket_classifier",
    model_type="classification",
    training_data=(X_train, y_train)
)

# Make predictions
predictions = ml_system.predict("ticket_classifier", input_data)
```

## Integration with Existing Components

- **PostgreSQL Database**: Model metadata and data storage
- **Cache Mechanism**: Prediction caching
- **Evaluation & Observability**: Logging and metrics
- **API Backend Services**: Expose ML endpoints

## Creating New Use Cases

See `use_cases/README.md` for instructions on creating new ITSM-specific ML models.

## Documentation

- **ML Framework**: `ml_framework/README.md`
- **MLOps**: `mlops/README.md`
- **Data Management**: `ml_data_management/README.md`
- **Model Serving**: `model_serving/README.md`
- **Use Cases**: `use_cases/README.md`

## Related Documentation

- Component explanations: `docs/components/`
- Troubleshooting guides: `docs/troubleshooting/`


