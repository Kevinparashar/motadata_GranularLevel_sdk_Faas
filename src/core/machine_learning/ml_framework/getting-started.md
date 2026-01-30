# MOTADATA - GETTING STARTED WITH ML FRAMEWORK

**Complete guide for getting started with the ML Framework, from system creation to model deployment.**

## Overview

The ML Framework provides comprehensive machine learning capabilities for training, inference, and model management. This guide explains the complete workflow from system creation to model deployment.

## Entry Point

The primary entry point for creating ML systems:

```python
from src.core.machine_learning.ml_framework import (
    create_ml_system,
    create_model_manager,
    create_trainer,
    create_predictor
)
```

## Input Requirements

### Required Inputs

1. **Database Connection**: PostgreSQL database for model storage
   ```python
   from src.core.postgresql_database import DatabaseConnection, DatabaseConfig

   config = DatabaseConfig(
       host="localhost",
       port=5432,
       database="mydb",
       user="postgres",
       password="password"
   )
   db = DatabaseConnection(config)
   ```

2. **ML System Configuration**:
   - `db`: Database connection instance
   - `tenant_id`: Optional tenant ID for multi-tenancy

### Optional Inputs

- `max_memory_mb`: Maximum memory usage in MB
- `cache`: Cache mechanism instance
- `enable_gpu`: Enable GPU acceleration

## Process Flow

### Step 1: ML System Creation

**What Happens:**
1. ML system validates database connection
2. Model manager is initialized
3. Trainer is initialized
4. Predictor is initialized
5. Data processor is initialized
6. Model registry is initialized

**Code:**
```python
ml_system = create_ml_system(
    db=db,
    tenant_id="tenant_123",
    max_memory_mb=2048
)
```

**Internal Process:**
```
create_ml_system()
  ├─> Validate database connection
  ├─> Initialize ModelManager
  ├─> Initialize Trainer
  ├─> Initialize Predictor
  ├─> Initialize DataProcessor
  ├─> Initialize ModelRegistry
  └─> Return MLSystem instance
```

### Step 2: Model Training

**What Happens:**
1. Training data is validated
2. Model is initialized
3. Model is trained on training data
4. Model is evaluated on validation data
5. Model metrics are calculated
6. Model is saved to database

**Code:**
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
        "max_depth": 10
    },
    tenant_id="tenant_123"
)
```

**Input:**
- `model_id`: Unique model identifier
- `model_type`: Type of model ("classification", "regression", "clustering")
- `training_data`: Tuple of (X_train, y_train)
- `validation_data`: Tuple of (X_test, y_test)
- `hyperparameters`: Model hyperparameters dictionary
- `tenant_id`: Optional tenant ID

**Internal Process:**
```
train_model()
  ├─> Validate input data
  ├─> Initialize model based on type
  ├─> Preprocess training data
  ├─> Train model
  │   ├─> Fit model on training data
  │   └─> Iterate through epochs/iterations
  ├─> Evaluate on validation data
  ├─> Calculate metrics (accuracy, F1, etc.)
  ├─> Save model to database
  └─> Return training result
```

### Step 3: Model Prediction

**What Happens:**
1. Model is loaded from database
2. Input data is preprocessed
3. Prediction is made
4. Result is returned

**Code:**
```python
prediction = ml_system.predict(
    model_id="ticket_classifier",
    input_data=X_test.iloc[0],
    tenant_id="tenant_123"
)
```

**Input:**
- `model_id`: Model identifier
- `input_data`: Input features (array or dict)
- `tenant_id`: Optional tenant ID

**Internal Process:**
```
predict()
  ├─> Load model from database
  ├─> Validate model exists
  ├─> Preprocess input data
  ├─> Make prediction
  └─> Return prediction result
```

## Output

### Training Output

```python
{
    "model_id": "ticket_classifier",
    "status": "completed",
    "metrics": {
        "accuracy": 0.95,
        "f1_score": 0.93,
        "precision": 0.94,
        "recall": 0.92
    },
    "training_time": 120.5,  # seconds
    "model_version": "1.0.0"
}
```

### Prediction Output

```python
{
    "prediction": 1,  # Class label or value
    "probabilities": [0.1, 0.9],  # Class probabilities (if available)
    "confidence": 0.9,
    "model_id": "ticket_classifier",
    "model_version": "1.0.0"
}
```

## Where Output is Used

### 1. Direct Usage

```python
# Use prediction in application
prediction = ml_system.predict(
    model_id="ticket_classifier",
    input_data=new_ticket_features
)

if prediction["prediction"] == 1:
    route_to_urgent_queue()
else:
    route_to_normal_queue()
```

### 2. Integration with API Backend

```python
# Expose ML predictions via API
@app.post("/api/ml/predict/{model_id}")
def predict_api(model_id: str, input_data: dict):
    prediction = ml_system.predict(
        model_id=model_id,
        input_data=input_data
    )
    return {"prediction": prediction}
```

### 3. Integration with Model Serving

```python
# Use Model Server for production serving
from src.core.machine_learning.model_serving import create_model_server

server = create_model_server(
    model_manager=ml_system.model_manager,
    host="0.0.0.0",
    port=8000
)
# Server uses ML system for predictions
```

### 4. Integration with MLOps

```python
# Track experiments and monitor models
from src.core.machine_learning.mlops import create_experiment_tracker

tracker = create_experiment_tracker(tenant_id="tenant_123")
tracker.log_metrics(result["metrics"])
# Training metrics are tracked automatically
```

## Complete Example

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from src.core.machine_learning.ml_framework import create_ml_system
from src.core.postgresql_database import DatabaseConnection, DatabaseConfig

# Step 1: Initialize Database (Entry Point)
config = DatabaseConfig(
    host="localhost",
    port=5432,
    database="mydb",
    user="postgres",
    password="password"
)
db = DatabaseConnection(config)

# Step 2: Create ML System (Entry Point)
ml_system = create_ml_system(
    db=db,
    tenant_id="tenant_123",
    max_memory_mb=2048
)

# Step 3: Load and Prepare Data (Input)
df = pd.read_csv("tickets.csv")
X = df.drop("category", axis=1)
y = df["category"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Step 4: Train Model (Process)
result = ml_system.train_model(
    model_id="ticket_classifier",
    model_type="classification",
    training_data=(X_train, y_train),
    validation_data=(X_test, y_test),
    hyperparameters={
        "n_estimators": 100,
        "max_depth": 10,
        "learning_rate": 0.1
    },
    tenant_id="tenant_123"
)

print(f"Training completed: {result['metrics']}")

# Step 5: Make Predictions (Process)
prediction = ml_system.predict(
    model_id="ticket_classifier",
    input_data=X_test.iloc[0],
    tenant_id="tenant_123"
)

# Step 6: Use Output
print(f"Prediction: {prediction['prediction']}")
print(f"Confidence: {prediction['confidence']}")

# Use prediction in your application
if prediction["prediction"] == 1:
    handle_urgent_ticket()
```

## Important Information

### Model Types

```python
# Classification
result = ml_system.train_model(
    model_id="classifier",
    model_type="classification",
    ...
)

# Regression
result = ml_system.train_model(
    model_id="regressor",
    model_type="regression",
    ...
)

# Clustering
result = ml_system.train_model(
    model_id="clusterer",
    model_type="clustering",
    ...
)
```

### Model Management

```python
# List all models
models = ml_system.model_manager.list_models(tenant_id="tenant_123")

# Get model info
model_info = ml_system.model_manager.get_model_info(
    model_id="ticket_classifier",
    tenant_id="tenant_123"
)

# Delete model
ml_system.model_manager.delete_model(
    model_id="ticket_classifier",
    tenant_id="tenant_123"
)
```

### Batch Predictions

```python
# Predict on multiple inputs
predictions = ml_system.predict_batch(
    model_id="ticket_classifier",
    input_data=X_test,
    tenant_id="tenant_123"
)
```

### Error Handling

```python
try:
    result = ml_system.train_model(...)
except MLTrainingError as e:
    print(f"Training error: {e.message}")
    print(f"Error type: {e.error_type}")
except ModelNotFoundError as e:
    print(f"Model not found: {e.model_id}")
```

## Next Steps

- See [README.md](README.md) for detailed component documentation
- Check [docs/components/ml_framework_explanation.md](../../../../docs/components/ml_framework_explanation.md) for comprehensive guide
- Review [troubleshooting guide](../../../../docs/troubleshooting/ml_framework_troubleshooting.md) for common issues

