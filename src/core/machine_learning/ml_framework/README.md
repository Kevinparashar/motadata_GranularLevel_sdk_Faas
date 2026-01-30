# MOTADATA - ML FRAMEWORK

**Comprehensive machine learning system for training, inference, and model management with multi-tenancy and memory management support.**

## Overview

The ML Framework is a comprehensive machine learning system for training, inference, and model management. It provides a unified interface for ML operations with support for multi-tenancy, memory management, and integration with existing SDK components.

## Purpose and Functionality

The ML Framework enables ITSM SaaS platforms to leverage traditional ML algorithms for use cases that are better served by ML rather than LLM/Agent-based approaches. It provides:

1. **Model Training**: Complete training pipeline with hyperparameter management, validation, and checkpointing
2. **Model Inference**: Single and batch prediction capabilities with preprocessing and postprocessing
3. **Model Management**: Full lifecycle management (create, update, delete, archive, version)
4. **Memory Management**: Intelligent model loading/unloading with configurable memory limits
5. **Multi-Tenancy**: Full tenant isolation for SaaS deployments

## Connection to Other Components

### Integration with PostgreSQL Database

The **PostgreSQL Database** (`src/core/postgresql_database/`) is used for:
- **Model Metadata Storage**: Model information, versions, and metadata
- **Training Data Storage**: Training datasets and data versioning
- **Prediction History**: Historical predictions for monitoring and analysis

### Integration with Cache Mechanism

The **Cache Mechanism** (`src/core/cache_mechanism/`) is used to:
- **Cache Predictions**: Frequently requested predictions to reduce computation
- **Cache Features**: Preprocessed features for faster inference
- **Cache Model Metadata**: Model information for quick access

### Integration with Evaluation & Observability

The **Evaluation & Observability** (`src/core/evaluation_observability/`) provides:
- **ML Operation Logging**: Track training and inference operations
- **Performance Metrics**: Monitor model performance and latency
- **Distributed Tracing**: Trace ML operations across the system

### Integration with MLOps Pipeline

The **MLOps Pipeline** (`src/core/machine_learning/mlops/`) integrates for:
- **Experiment Tracking**: Log training experiments and hyperparameters
- **Model Versioning**: Track model versions and lineage
- **Model Deployment**: Deploy models to different environments
- **Model Monitoring**: Monitor model performance in production

## Key Features

### Unified ML Interface

The ML Framework provides a single interface (`MLSystem`) for all ML operations:

```python
from src.core.machine_learning.ml_framework import MLSystem
from src.core.postgresql_database.connection import DatabaseConnection

# Initialize ML system
ml_system = MLSystem(
    db=db_connection,
    tenant_id="tenant_123",
    max_memory_mb=2048
)

# Train a model
training_result = ml_system.train_model(
    model_id="ticket_classifier",
    model_type="classification",
    training_data=(X_train, y_train),
    hyperparameters={"n_estimators": 100}
)

# Make predictions
predictions = ml_system.predict(
    model_id="ticket_classifier",
    input_data=X_test
)
```

### Memory Management

Intelligent memory management prevents memory overflow:

- **Configurable Limits**: Set maximum memory for loaded models
- **Automatic Unloading**: Unload least recently used models when limit reached
- **Lazy Loading**: Models loaded on-demand for predictions
- **Memory Tracking**: Track memory usage per model

### Model Lifecycle Management

Complete model lifecycle support:

- **Registration**: Register models with metadata
- **Versioning**: Track multiple versions of models
- **Archival**: Soft delete old models
- **Deletion**: Remove models completely

### Data Processing

Comprehensive data preprocessing:

- **Automatic Preprocessing**: Handles pandas DataFrames, numpy arrays, and lists
- **Feature Engineering**: Extract and transform features
- **Data Splitting**: Train/validation/test splits
- **Postprocessing**: Convert predictions to desired formats

## Usage Examples

### Training a Model

```python
from src.core.machine_learning.ml_framework import MLSystem
import pandas as pd
from sklearn.model_selection import train_test_split

# Load data
df = pd.read_csv("tickets.csv")
X = df.drop("category", axis=1)
y = df["category"]

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Initialize ML system
ml_system = MLSystem(db, tenant_id="tenant_123")

# Train model
result = ml_system.train_model(
    model_id="ticket_classifier",
    model_type="classification",
    training_data=(X_train, y_train),
    validation_data=(X_test, y_test),
    hyperparameters={
        "n_estimators": 100,
        "max_depth": 10
    }
)

print(f"Training completed: {result['metrics']}")
```

### Making Predictions

```python
# Single prediction
prediction = ml_system.predict(
    model_id="ticket_classifier",
    input_data=new_ticket_features
)

# Batch predictions
predictions = ml_system.predict_batch(
    model_id="ticket_classifier",
    input_batch=[ticket1_features, ticket2_features, ticket3_features],
    batch_size=32
)
```

### Model Management

```python
# Get model information
model_info = ml_system.get_model_info("ticket_classifier")

# List all models
all_models = ml_system.model_manager.list_models()

# Update model metadata
ml_system.model_manager.update_model(
    model_id="ticket_classifier",
    metadata={"description": "Updated classifier"}
)

# Archive old model
ml_system.model_manager.archive_model("ticket_classifier", version="1.0.0")
```

## Component Structure

- **`ml_system.py`**: Main orchestrator for ML operations
- **`model_manager.py`**: Model lifecycle management
- **`trainer.py`**: Training orchestration
- **`predictor.py`**: Inference engine
- **`data_processor.py`**: Data preprocessing and feature engineering
- **`model_registry.py`**: Model versioning and registry
- **`utils/`**: Utility functions (feature extractors, serialization, metrics)
- **`functions.py`**: Factory and convenience functions

## Error Handling

The ML Framework uses a comprehensive exception hierarchy:

- **`MLFrameworkError`**: Base exception for all ML framework errors
- **`TrainingError`**: Raised when training fails
- **`PredictionError`**: Raised when prediction fails
- **`ModelLoadError`**: Raised when model loading fails
- **`ModelSaveError`**: Raised when model saving fails
- **`ModelNotFoundError`**: Raised when model is not found

## Memory Management

Memory management is critical for SaaS deployments:

- **Per-Tenant Limits**: Configurable memory limits per tenant
- **Automatic Cleanup**: Unload unused models automatically
- **Memory Monitoring**: Track memory usage per model
- **Graceful Degradation**: Handle memory pressure gracefully

## Multi-Tenancy Support

Full tenant isolation:

- **Tenant-Scoped Models**: Models are isolated per tenant
- **Tenant-Scoped Data**: Training data is tenant-specific
- **Tenant-Scoped Storage**: Model storage is tenant-isolated
- **Tenant-Scoped Cache**: Prediction cache is tenant-specific

## Performance Considerations

- **Lazy Loading**: Models loaded only when needed
- **Prediction Caching**: Cache frequent predictions
- **Batch Processing**: Efficient batch predictions
- **Async Support**: Async predictions for concurrent operations

## Integration with Use Cases

The ML Framework integrates with use case models in `use_cases/`:

```python
from src.core.machine_learning.use_cases.base_model import BaseMLModel

# Your use case model inherits from BaseMLModel
class TicketClassifier(BaseMLModel):
    def train(self, training_data, ...):
        # Implementation
        pass
    
    # ... other methods
```

## Best Practices

1. **Use Appropriate Model Types**: Choose the right model type for your use case
2. **Monitor Memory Usage**: Set appropriate memory limits
3. **Version Your Models**: Always version models for tracking
4. **Validate Data**: Preprocess and validate data before training
5. **Cache Predictions**: Use caching for frequently requested predictions
6. **Handle Errors**: Implement proper error handling
7. **Log Operations**: Use logging for debugging and monitoring

## Libraries Used

- **scikit-learn**: ML algorithms and utilities
- **pandas**: Data manipulation
- **numpy**: Numerical operations
- **joblib**: Model serialization

## Related Components

- **MLOps Pipeline** (`src/core/machine_learning/mlops/`): Experiment tracking and deployment
- **Data Management** (`src/core/machine_learning/ml_data_management/`): Data lifecycle management
- **Model Serving** (`src/core/machine_learning/model_serving/`): Model serving infrastructure
- **Use Cases** (`src/core/machine_learning/use_cases/`): ITSM-specific ML models


