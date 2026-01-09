# ML Framework Models

## Overview

The `models/` folder contains framework-level model components that support ML operations. These are **not** use case models (those go in `use_cases/`), but rather base classes, wrappers, factories, and utilities that enable the ML framework to work with various ML libraries.

## Purpose

This folder provides:
1. **Base Model Wrapper**: Common interface for integrating different ML model types (scikit-learn, XGBoost, etc.)
2. **Model Factory**: Factory pattern for creating model instances based on type and configuration
3. **Model Configuration**: Structured configuration classes for models

## Components

### BaseModelWrapper (`base_model_wrapper.py`)

Wraps ML models (scikit-learn, etc.) to provide a common interface:

```python
from src.core.machine_learning.ml_framework.models import BaseModelWrapper
from sklearn.ensemble import RandomForestClassifier

# Wrap a scikit-learn model
model = RandomForestClassifier(n_estimators=100)
wrapped = BaseModelWrapper(model, model_type="classification")

# Use common interface
wrapped.fit(X_train, y_train)
predictions = wrapped.predict(X_test)
```

### ModelFactory (`model_factory.py`)

Factory for creating model instances:

```python
from src.core.machine_learning.ml_framework.models import ModelFactory

# Create a classification model
model = ModelFactory.create_model(
    model_type="classification",
    hyperparameters={"n_estimators": 100}
)

# Create a wrapped model
wrapped = ModelFactory.create_model_wrapper(
    model_type="regression",
    hyperparameters={"max_depth": 10}
)
```

### ModelConfig (`model_config.py`)

Structured configuration for models:

```python
from src.core.machine_learning.ml_framework.models import ModelConfig

# Create configuration
config = ModelConfig(
    model_type="classification",
    hyperparameters={"n_estimators": 100, "max_depth": 10},
    model_id="ticket_classifier",
    version="1.0.0"
)

# Use configuration
model = ModelFactory.create_model(
    config.model_type,
    config.hyperparameters
)
```

## Supported Model Types

### Classification
- `classification` - RandomForestClassifier
- `logistic_regression` - LogisticRegression
- `svm_classification` - SVC

### Regression
- `regression` - RandomForestRegressor
- `linear_regression` - LinearRegression
- `svm_regression` - SVR

### Clustering
- `kmeans` - KMeans

## Relationship to Use Cases

- **This folder (`models/`)**: Framework-level components, base classes, utilities
- **`use_cases/` folder**: Actual use case models (TicketClassifier, PriorityPredictor, etc.)

When creating a new use case model:
1. Inherit from `BaseMLModel` in `use_cases/base_model.py`
2. Use `ModelFactory` or `BaseModelWrapper` if needed
3. Implement use case-specific logic in your use case folder

## Extension

To add support for new model types:

1. **Add to ModelFactory**:
```python
elif model_type == "xgboost_classification":
    from xgboost import XGBClassifier
    return XGBClassifier(**hyperparameters)
```

2. **Extend BaseModelWrapper** if needed for special handling

3. **Update ModelConfig** if new configuration options are needed

## Best Practices

1. **Use ModelFactory**: Prefer using ModelFactory over directly instantiating models
2. **Use ModelConfig**: Use ModelConfig for structured configuration
3. **Extend BaseModelWrapper**: If creating custom model wrappers, inherit from BaseModelWrapper
4. **Keep Framework-Level**: This folder should contain framework components, not use case logic

