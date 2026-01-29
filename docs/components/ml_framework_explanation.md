# Motadata ML Framework - Comprehensive Component Explanation

## Overview

The ML Framework is a comprehensive machine learning system for training, inference, and model management. It provides a unified interface for ML operations with support for multi-tenancy, memory management, and integration with existing SDK components.

## Table of Contents

1. [ML System](#ml-system)
2. [Model Management](#model-management)
3. [Training](#training)
4. [Inference](#inference)
5. [Data Processing](#data-processing)
6. [Model Registry](#model-registry)
7. [Exception Handling](#exception-handling)
8. [Functions](#functions)
9. [Workflow](#workflow)
10. [Customization](#customization)

---

## ML System

### Functionality

The MLSystem is the main orchestrator that provides a unified interface for all ML operations:
- **Model Training**: Complete training pipeline with hyperparameter management
- **Model Inference**: Single and batch predictions with preprocessing/postprocessing
- **Model Lifecycle**: Create, update, delete, archive, and version models
- **Memory Management**: Intelligent model loading/unloading with configurable limits
- **Multi-Tenancy**: Full tenant isolation for SaaS deployments
- **Caching**: Integration with cache mechanism for prediction caching

### Code Examples

#### Initialize ML System

```python
from src.core.machine_learning.ml_framework import MLSystem
from src.core.postgresql_database.connection import DatabaseConnection
from src.core.cache_mechanism import CacheMechanism, CacheConfig

# Initialize dependencies
db = DatabaseConnection(...)
cache = CacheMechanism(CacheConfig())

# Create ML system
ml_system = MLSystem(
    db=db,
    cache=cache,
    max_memory_mb=2048,
    tenant_id="tenant_123"
)
```

#### Train a Model

```python
import pandas as pd
from sklearn.model_selection import train_test_split

# Load and prepare data
df = pd.read_csv("tickets.csv")
X = df.drop("category", axis=1)
y = df["category"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Train model
result = ml_system.train_model(
    model_id="ticket_classifier",
    model_type="classification",
    training_data=(X_train, y_train),
    validation_data=(X_test, y_test),
    hyperparameters={
        "n_estimators": 100,
        "max_depth": 10,
        "random_state": 42
    }
)

print(f"Training completed: {result['metrics']}")
print(f"Model path: {result['model_path']}")
```

#### Make Predictions

```python
# Single prediction
prediction = ml_system.predict(
    model_id="ticket_classifier",
    input_data=new_ticket_features,
    use_cache=True
)

# Batch predictions
predictions = ml_system.predict_batch(
    model_id="ticket_classifier",
    input_batch=[ticket1_features, ticket2_features],
    batch_size=32
)

# Async prediction
import asyncio
prediction = await ml_system.predict_async(
    model_id="ticket_classifier",
    input_data=new_ticket_features
)
```

---

## Model Management

### Functionality

ModelManager handles the complete lifecycle of ML models:
- **Registration**: Register models with metadata
- **Storage**: Save models to disk with versioning
- **Loading**: Load models from storage
- **Versioning**: Track multiple versions of models
- **Metadata**: Store and update model metadata
- **Archival**: Soft delete old models
- **Deletion**: Remove models completely

### Code Examples

#### Register Model

```python
from src.core.machine_learning.ml_framework import ModelManager

model_manager = ModelManager(db, storage_path="./models", tenant_id="tenant_123")

# Register a trained model
model_id = model_manager.register_model(
    model_id="ticket_classifier",
    model_type="classification",
    model_path="./models/ticket_classifier_v1.joblib",
    metadata={
        "description": "Ticket category classifier",
        "accuracy": 0.95,
        "training_date": "2024-01-15"
    },
    version="1.0.0"
)
```

#### List Models

```python
# List all models
all_models = model_manager.list_models()

# List models by type
classification_models = model_manager.list_models(model_type="classification")

# Get specific model
model_info = model_manager.get_model("ticket_classifier", version="1.0.0")
```

#### Update and Archive

```python
# Update model metadata
model_manager.update_model(
    model_id="ticket_classifier",
    metadata={"accuracy": 0.96, "updated_date": "2024-01-20"}
)

# Archive old version
model_manager.archive_model("ticket_classifier", version="1.0.0")

# Delete model
model_manager.delete_model("ticket_classifier", version="1.0.0")
```

---

## Training

### Functionality

Trainer orchestrates the model training process:
- **Training Execution**: Execute training pipeline
- **Hyperparameter Management**: Handle model hyperparameters
- **Validation**: Validate models on validation data
- **Metrics Calculation**: Calculate training and validation metrics
- **Checkpointing**: Save training checkpoints
- **Model Creation**: Create model instances based on type

### Code Examples

#### Train with Custom Configuration

```python
from src.core.machine_learning.ml_framework import Trainer

trainer = Trainer(db, tenant_id="tenant_123")

# Train model
result = trainer.train(
    model_id="ticket_classifier",
    model_type="classification",
    training_data=(X_train, y_train),
    validation_data=(X_val, y_val),
    hyperparameters={
        "n_estimators": 200,
        "max_depth": 15,
        "min_samples_split": 5
    }
)

print(f"Training metrics: {result['metrics']['train']}")
print(f"Validation metrics: {result['metrics']['validation']}")
```

#### Save and Load Checkpoints

```python
# Save checkpoint during training
checkpoint_path = trainer.save_checkpoint(
    model=trained_model,
    model_id="ticket_classifier",
    epoch=10
)

# Load checkpoint
model = trainer.load_checkpoint(checkpoint_path)
```

---

## Inference

### Functionality

Predictor handles model inference:
- **Single Predictions**: Make predictions on single inputs
- **Batch Predictions**: Process batches efficiently
- **Probability Predictions**: Get prediction probabilities for classification
- **Caching**: Integration with cache for frequent predictions

### Code Examples

#### Basic Prediction

```python
from src.core.machine_learning.ml_framework import Predictor, ModelManager

model_manager = ModelManager(db, tenant_id="tenant_123")
predictor = Predictor(model_manager, cache=cache, tenant_id="tenant_123")

# Load model
model = model_manager.load_model("ticket_classifier")

# Make prediction
prediction = predictor.predict(model, input_data)

# Get probabilities
probabilities = predictor.predict_proba(model, input_data)
```

#### Batch Prediction

```python
# Batch predictions
batch_results = predictor.predict_batch(
    model=model,
    input_batch=[input1, input2, input3]
)
```

---

## Data Processing

### Functionality

DataProcessor handles data preprocessing and feature engineering:
- **Preprocessing**: Clean and normalize data
- **Feature Extraction**: Extract features from raw data
- **Feature Transformation**: Scale, normalize, encode features
- **Data Splitting**: Split data into train/validation/test sets
- **Postprocessing**: Convert predictions to desired formats

### Code Examples

#### Preprocess Data

```python
from src.core.machine_learning.ml_framework import DataProcessor

processor = DataProcessor(tenant_id="tenant_123")

# Preprocess training data
processed_data = processor.preprocess(
    data=raw_data,
    model_type="classification",
    is_training=True
)

# Preprocess inference data
processed_input = processor.preprocess(
    data=new_data,
    is_training=False
)
```

#### Feature Engineering

```python
# Extract features
features = processor.extract_features(
    data=raw_data,
    feature_config={
        "include_text_features": True,
        "include_datetime_features": True
    }
)

# Transform features
transformed = processor.transform_features(
    features=features,
    transform_type="standard"  # or "minmax"
)
```

#### Split Data

```python
# Split into train/val/test
X_train, X_val, X_test, y_train, y_val, y_test = processor.split_data(
    X=features,
    y=labels,
    test_size=0.2,
    val_size=0.1,
    random_state=42
)
```

---

## Model Registry

### Functionality

ModelRegistry manages model versioning and lineage:
- **Version Registration**: Register model versions with metadata
- **Version Retrieval**: Get specific or latest versions
- **Version Listing**: List all versions of a model
- **Version Promotion**: Promote versions to environments
- **Version Comparison**: Compare different versions
- **Lineage Tracking**: Track model lineage and dependencies

### Code Examples

#### Register Version

```python
from src.core.machine_learning.ml_framework import ModelRegistry

registry = ModelRegistry(db, tenant_id="tenant_123")

# Register model version
version_id = registry.register_version(
    model_id="ticket_classifier",
    version="1.0.0",
    model_path="./models/ticket_classifier_v1.joblib",
    metrics={
        "accuracy": 0.95,
        "precision": 0.94,
        "recall": 0.93,
        "f1": 0.935
    },
    hyperparameters={
        "n_estimators": 100,
        "max_depth": 10
    }
)
```

#### Version Management

```python
# Get version
version_info = registry.get_model_version("ticket_classifier", version="1.0.0")

# List all versions
versions = registry.list_versions("ticket_classifier")

# Promote to production
registry.promote_version(
    model_id="ticket_classifier",
    version="1.0.0",
    environment="production"
)

# Compare versions
comparison = registry.compare_versions(
    model_id="ticket_classifier",
    version1="1.0.0",
    version2="1.1.0"
)
```

---

## Exception Handling

### Exception Hierarchy

```python
MLFrameworkError
├── TrainingError
├── PredictionError
├── ModelLoadError
├── ModelSaveError
├── DataProcessingError
└── ModelNotFoundError
```

### Code Examples

```python
from src.core.machine_learning.ml_framework.exceptions import (
    TrainingError,
    PredictionError,
    ModelNotFoundError
)

try:
    result = ml_system.train_model(...)
except TrainingError as e:
    print(f"Training failed: {e.message}")
    print(f"Model ID: {e.model_id}")
    print(f"Stage: {e.stage}")

try:
    prediction = ml_system.predict(...)
except ModelNotFoundError as e:
    print(f"Model not found: {e.model_id}")
except PredictionError as e:
    print(f"Prediction failed: {e.message}")
```

---

## Functions

### Factory Functions

```python
from src.core.machine_learning.ml_framework.functions import (
    create_ml_system,
    create_model_manager,
    create_trainer,
    create_predictor,
    create_data_processor,
    create_model_registry
)

# Create components
ml_system = create_ml_system(db, tenant_id="tenant_123")
model_manager = create_model_manager(db, tenant_id="tenant_123")
trainer = create_trainer(db, tenant_id="tenant_123")
```

---

## Workflow

### Training Workflow

1. **Data Preparation**: Load and preprocess data
2. **Model Configuration**: Define model type and hyperparameters
3. **Training**: Execute training pipeline
4. **Validation**: Validate on validation set
5. **Registration**: Register model with metadata
6. **Versioning**: Create model version

### Inference Workflow

1. **Model Loading**: Load model from storage (lazy loading)
2. **Input Preprocessing**: Preprocess input data
3. **Prediction**: Make prediction
4. **Postprocessing**: Postprocess results
5. **Caching**: Cache result if enabled

---

## Customization

### Custom Model Types

Extend ModelFactory to support custom model types:

```python
from src.core.machine_learning.ml_framework.models.model_factory import ModelFactory

# Add custom model type
def create_custom_model(hyperparameters):
    from custom_ml_library import CustomModel
    return CustomModel(**hyperparameters)

# Register in factory
ModelFactory.create_model = lambda model_type, hyperparameters: (
    create_custom_model(hyperparameters) if model_type == "custom"
    else ModelFactory._create_standard_model(model_type, hyperparameters)
)
```

### Custom Data Processing

Extend DataProcessor for custom preprocessing:

```python
class CustomDataProcessor(DataProcessor):
    def preprocess(self, data, model_type=None, is_training=True):
        # Custom preprocessing logic
        processed = super().preprocess(data, model_type, is_training)
        # Additional custom processing
        return processed
```

---

## Integration Points

### With PostgreSQL Database
- Model metadata storage
- Training data storage
- Prediction history

### With Cache Mechanism
- Prediction caching
- Feature caching
- Model metadata caching

### With Evaluation & Observability
- ML operation logging
- Performance metrics
- Distributed tracing

### With MLOps Pipeline
- Experiment tracking
- Model versioning
- Model deployment
- Model monitoring

