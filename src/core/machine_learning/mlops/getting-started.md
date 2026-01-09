# Getting Started with MLOps Pipeline

## Overview

The MLOps Pipeline provides end-to-end MLOps capabilities including experiment tracking, model versioning, deployment, and monitoring. This guide explains the complete workflow from experiment tracking to model deployment.

## Entry Point

The primary entry point for MLOps operations:

```python
from src.core.machine_learning.mlops import (
    create_mlops_pipeline,
    create_experiment_tracker,
    create_model_versioning,
    create_model_deployment,
    create_model_monitoring
)
```

## Input Requirements

### Required Inputs

1. **Tenant ID**: Optional tenant ID for multi-tenancy

### Optional Inputs

- `mlflow_uri`: MLflow tracking server URI
- `experiment_name`: Experiment name
- `storage_path`: Path for storing experiment data

## Process Flow

### Step 1: MLOps Pipeline Creation

**What Happens:**
1. Pipeline is initialized
2. Experiment tracker is configured
3. Model versioning is set up
4. Deployment manager is initialized
5. Monitoring system is configured

**Code:**
```python
pipeline = create_mlops_pipeline(
    pipeline_name="ticket_classifier_pipeline",
    tenant_id="tenant_123"
)
```

**Internal Process:**
```
create_mlops_pipeline()
  ├─> Initialize experiment tracker
  ├─> Set up model versioning
  ├─> Configure deployment manager
  ├─> Initialize monitoring
  └─> Return pipeline instance
```

### Step 2: Experiment Tracking

**What Happens:**
1. Experiment is created
2. Parameters are logged
3. Metrics are logged
4. Artifacts are saved
5. Experiment is finalized

**Code:**
```python
tracker = create_experiment_tracker(tenant_id="tenant_123")

# Start experiment
tracker.start_experiment(
    experiment_name="ticket_classifier_v1",
    tags={"model_type": "classification"}
)

# Log parameters
tracker.log_params({
    "n_estimators": 100,
    "max_depth": 10,
    "learning_rate": 0.1
})

# Log metrics
tracker.log_metrics({
    "accuracy": 0.95,
    "f1_score": 0.93,
    "precision": 0.94
})

# End experiment
tracker.end_experiment()
```

**Input:**
- `experiment_name`: Name of the experiment
- `params`: Dictionary of hyperparameters
- `metrics`: Dictionary of evaluation metrics
- `tags`: Optional tags for organization

**Internal Process:**
```
log_params()
  ├─> Validate parameters
  ├─> Store in experiment database
  └─> Update experiment metadata

log_metrics()
  ├─> Validate metrics
  ├─> Store in experiment database
  └─> Update experiment summary
```

### Step 3: Model Versioning

**What Happens:**
1. Model version is created
2. Model artifacts are stored
3. Version metadata is recorded
4. Version lineage is tracked

**Code:**
```python
versioning = create_model_versioning(tenant_id="tenant_123")

version = versioning.create_version(
    model_id="ticket_classifier",
    model_path="./models/ticket_classifier.pkl",
    metadata={
        "training_data": "tickets_2024.csv",
        "metrics": {"accuracy": 0.95}
    }
)
```

**Input:**
- `model_id`: Model identifier
- `model_path`: Path to model file
- `metadata`: Model metadata dictionary

**Internal Process:**
```
create_version()
  ├─> Generate version number
  ├─> Store model artifacts
  ├─> Record metadata
  ├─> Track lineage
  └─> Return version info
```

### Step 4: Model Deployment

**What Happens:**
1. Model version is selected
2. Deployment environment is configured
3. Model is deployed
4. Deployment status is tracked

**Code:**
```python
deployment = create_model_deployment(tenant_id="tenant_123")

deployment.deploy_model(
    model_id="ticket_classifier",
    version="1.0.0",
    environment="production",
    config={
        "replicas": 3,
        "resources": {"cpu": "2", "memory": "4Gi"}
    }
)
```

**Input:**
- `model_id`: Model identifier
- `version`: Model version
- `environment`: Deployment environment
- `config`: Deployment configuration

**Internal Process:**
```
deploy_model()
  ├─> Load model version
  ├─> Configure deployment
  ├─> Deploy to environment
  ├─> Verify deployment
  └─> Update deployment status
```

### Step 5: Model Monitoring

**What Happens:**
1. Predictions are tracked
2. Performance metrics are collected
3. Drift is detected
4. Alerts are triggered if needed

**Code:**
```python
monitoring = create_model_monitoring(tenant_id="tenant_123")

# Track prediction
monitoring.track_prediction(
    model_id="ticket_classifier",
    prediction_time=0.15,
    success=True,
    input_features={"priority": 1, "category": "technical"}
)

# Check for drift
drift_detected = monitoring.check_drift(
    model_id="ticket_classifier",
    threshold=0.1
)
```

## Output

### Experiment Tracking Output

```python
{
    "experiment_id": "exp_123",
    "run_id": "run_456",
    "status": "completed",
    "metrics": {
        "accuracy": 0.95,
        "f1_score": 0.93
    },
    "params": {
        "n_estimators": 100,
        "max_depth": 10
    }
}
```

### Model Versioning Output

```python
{
    "version": "1.0.0",
    "model_id": "ticket_classifier",
    "created_at": "2024-01-15T10:30:00Z",
    "metadata": {...}
}
```

### Deployment Output

```python
{
    "deployment_id": "deploy_123",
    "status": "deployed",
    "environment": "production",
    "endpoint": "http://api.example.com/models/ticket_classifier"
}
```

### Monitoring Output

```python
{
    "drift_detected": False,
    "drift_score": 0.05,
    "performance_metrics": {
        "avg_latency": 0.15,
        "success_rate": 0.98
    }
}
```

## Where Output is Used

### 1. Experiment Analysis

```python
# Compare experiments
experiments = tracker.list_experiments()
best_experiment = max(experiments, key=lambda e: e["metrics"]["accuracy"])
```

### 2. Model Rollback

```python
# Rollback to previous version
versioning.rollback_model(
    model_id="ticket_classifier",
    target_version="0.9.0"
)
```

### 3. Alerting

```python
# Set up alerts for drift
monitoring.set_alert(
    model_id="ticket_classifier",
    condition="drift_score > 0.1",
    action="notify_team"
)
```

## Complete Example

```python
from src.core.machine_learning.mlops import (
    create_mlops_pipeline,
    create_experiment_tracker,
    create_model_versioning,
    create_model_deployment,
    create_model_monitoring
)

# Step 1: Create Pipeline (Entry Point)
pipeline = create_mlops_pipeline(
    pipeline_name="ticket_classifier_pipeline",
    tenant_id="tenant_123"
)

# Step 2: Track Experiment (Input)
tracker = create_experiment_tracker(tenant_id="tenant_123")

tracker.start_experiment("ticket_classifier_v1")
tracker.log_params({
    "n_estimators": 100,
    "max_depth": 10
})
tracker.log_metrics({
    "accuracy": 0.95,
    "f1_score": 0.93
})
tracker.end_experiment()

# Step 3: Version Model (Process)
versioning = create_model_versioning(tenant_id="tenant_123")
version = versioning.create_version(
    model_id="ticket_classifier",
    model_path="./models/ticket_classifier.pkl"
)

# Step 4: Deploy Model (Process)
deployment = create_model_deployment(tenant_id="tenant_123")
deployment.deploy_model(
    model_id="ticket_classifier",
    version="1.0.0",
    environment="production"
)

# Step 5: Monitor Model (Process)
monitoring = create_model_monitoring(tenant_id="tenant_123")
monitoring.track_prediction(
    model_id="ticket_classifier",
    prediction_time=0.15,
    success=True
)

# Step 6: Use Output
drift_status = monitoring.check_drift("ticket_classifier")
if drift_status["drift_detected"]:
    trigger_retraining()
```

## Important Information

### MLflow Integration

```python
# Use MLflow for experiment tracking
tracker = create_experiment_tracker(
    mlflow_uri="http://mlflow-server:5000",
    experiment_name="ticket_classification"
)
```

### Model Lineage

```python
# Track model lineage
lineage = versioning.get_lineage("ticket_classifier")
# Shows all versions and their relationships
```

### A/B Testing

```python
# Deploy multiple versions for A/B testing
deployment.deploy_model(
    model_id="ticket_classifier",
    version="1.0.0",
    environment="production",
    traffic_percentage=50  # 50% traffic
)

deployment.deploy_model(
    model_id="ticket_classifier",
    version="1.1.0",
    environment="production",
    traffic_percentage=50  # 50% traffic
)
```

## Next Steps

- See [README.md](README.md) for detailed component documentation
- Check [component_explanation/mlops_explanation.md](../../../../component_explanation/mlops_explanation.md) for comprehensive guide
- Review [troubleshooting guide](../../../../docs/troubleshooting/mlops_troubleshooting.md) for common issues

