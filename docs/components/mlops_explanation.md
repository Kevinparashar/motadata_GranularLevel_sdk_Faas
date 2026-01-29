# Motadata MLOps Pipeline - Comprehensive Component Explanation

## Overview

The MLOps Pipeline provides end-to-end MLOps capabilities including experiment tracking, model versioning, deployment, monitoring, and drift detection. It ensures reliable, reproducible, and monitored ML operations in production.

## Table of Contents

1. [MLOps Pipeline](#mlops-pipeline)
2. [Experiment Tracking](#experiment-tracking)
3. [Model Versioning](#model-versioning)
4. [Model Deployment](#model-deployment)
5. [Model Monitoring](#model-monitoring)
6. [Drift Detection](#drift-detection)
7. [Exception Handling](#exception-handling)
8. [Functions](#functions)
9. [Workflow](#workflow)
10. [Customization](#customization)

---

## MLOps Pipeline

### Functionality

MLOpsPipeline orchestrates end-to-end MLOps workflows:
- **Pipeline Execution**: Execute complete ML pipelines
- **Stage Management**: Manage pipeline stages (data collection, preprocessing, training, validation, deployment, monitoring)
- **Error Handling**: Handle pipeline failures gracefully
- **Status Tracking**: Track pipeline execution status

### Code Examples

#### Create and Run Pipeline

```python
from src.core.machine_learning.mlops import MLOpsPipeline
from src.core.machine_learning.mlops.mlops_pipeline import PipelineStage

# Create pipeline
pipeline = MLOpsPipeline("ticket_classifier_pipeline", tenant_id="tenant_123")

# Run full pipeline
results = pipeline.run_pipeline(
    stages=[
        PipelineStage.DATA_COLLECTION,
        PipelineStage.DATA_PREPROCESSING,
        PipelineStage.TRAINING,
        PipelineStage.VALIDATION,
        PipelineStage.DEPLOYMENT,
        PipelineStage.MONITORING
    ]
)

# Check status
status = pipeline.get_pipeline_status()
print(f"Pipeline status: {status['status']}")
```

---

## Experiment Tracking

### Functionality

ExperimentTracker provides MLflow integration for experiment tracking:
- **Experiment Creation**: Create and manage experiments
- **Parameter Logging**: Log hyperparameters
- **Metrics Logging**: Log training and validation metrics
- **Artifact Logging**: Log models, plots, and other artifacts
- **Experiment Search**: Search and compare experiments

### Code Examples

#### Track Experiment

```python
from src.core.machine_learning.mlops import ExperimentTracker

# Create tracker
tracker = ExperimentTracker(tracking_uri="./mlruns", tenant_id="tenant_123")

# Create experiment
experiment_id = tracker.create_experiment(
    experiment_name="ticket_classifier_v1",
    tags={"model_type": "classification", "dataset": "tickets_2024"}
)

# Log parameters
tracker.log_params({
    "n_estimators": 100,
    "max_depth": 10,
    "learning_rate": 0.01
})

# Log metrics
tracker.log_metrics({
    "accuracy": 0.95,
    "precision": 0.94,
    "recall": 0.93,
    "f1": 0.935
}, step=1)

# Log artifacts
tracker.log_artifacts({
    "model": "./models/ticket_classifier.joblib",
    "confusion_matrix": "./plots/confusion_matrix.png"
})

# Search experiments
experiments = tracker.search_experiments(filter_string="model_type='classification'")
```

---

## Model Versioning

### Functionality

ModelVersioning manages model version control and lineage:
- **Version Registration**: Register model versions
- **Version Retrieval**: Get specific versions
- **Lineage Tracking**: Track model lineage and dependencies
- **Metadata Management**: Store version metadata

### Code Examples

#### Version Model

```python
from src.core.machine_learning.mlops import ModelVersioning
from src.core.postgresql_database.connection import DatabaseConnection

db = DatabaseConnection(...)
versioning = ModelVersioning(db, tenant_id="tenant_123")

# Version model
version_id = versioning.version_model(
    model_id="ticket_classifier",
    version="1.0.0",
    model_path="./models/ticket_classifier_v1.joblib",
    metadata={
        "training_date": "2024-01-15",
        "dataset_version": "v2.1",
        "accuracy": 0.95
    }
)

# Get lineage
lineage = versioning.get_lineage("ticket_classifier", version="1.0.0")
print(f"Model lineage: {lineage}")
```

---

## Model Deployment

### Functionality

ModelDeployment manages model deployments:
- **Deployment**: Deploy models to different environments (dev, staging, prod)
- **A/B Testing**: Deploy multiple model versions
- **Canary Deployments**: Gradual rollout of new models
- **Rollback**: Rollback to previous versions

### Code Examples

#### Deploy Model

```python
from src.core.machine_learning.mlops import ModelDeployment

deployment = ModelDeployment(tenant_id="tenant_123")

# Deploy to production
deployment_info = deployment.deploy_model(
    model_id="ticket_classifier",
    version="1.0.0",
    environment="production"
)

print(f"Deployment ID: {deployment_info['deployment_id']}")
print(f"Status: {deployment_info['status']}")

# Rollback deployment
deployment.rollback_deployment(deployment_info['deployment_id'])
```

---

## Model Monitoring

### Functionality

ModelMonitoring tracks model performance in production:
- **Performance Tracking**: Track prediction latency, success rates
- **Error Tracking**: Monitor errors and failures
- **Health Checks**: Check model health status
- **Alerting**: Alert on performance degradation

### Code Examples

#### Monitor Model

```python
from src.core.machine_learning.mlops import ModelMonitoring

monitoring = ModelMonitoring(tenant_id="tenant_123")

# Track prediction
monitoring.track_prediction(
    model_id="ticket_classifier",
    prediction_time=0.15,  # seconds
    success=True
)

# Track error
monitoring.track_prediction(
    model_id="ticket_classifier",
    prediction_time=0.05,
    success=False,
    error="Invalid input format"
)

# Get metrics
metrics = monitoring.get_metrics(
    model_id="ticket_classifier",
    time_window=timedelta(hours=1)
)

print(f"Total predictions: {metrics['total_predictions']}")
print(f"Success rate: {metrics['success_rate']}")
print(f"Average latency: {metrics['avg_latency']}s")

# Check health
health = monitoring.check_health("ticket_classifier")
print(f"Model health: {health['status']}")
```

---

## Drift Detection

### Functionality

DriftDetector detects data and model drift:
- **Data Drift**: Detect changes in input data distribution
- **Model Drift**: Detect performance degradation
- **Concept Drift**: Detect changes in data-label relationships
- **Statistical Tests**: Use statistical tests for drift detection

### Code Examples

#### Detect Drift

```python
from src.core.machine_learning.mlops import DriftDetector
import numpy as np

detector = DriftDetector(tenant_id="tenant_123")

# Detect data drift
data_drift = detector.detect_data_drift(
    reference_data=reference_features,
    current_data=current_features,
    threshold=0.05
)

if data_drift['drift_detected']:
    print(f"Data drift detected! P-value: {data_drift['p_value']}")

# Detect model drift
model_drift = detector.detect_model_drift(
    reference_metrics={"accuracy": 0.95, "f1": 0.93},
    current_metrics={"accuracy": 0.88, "f1": 0.85},
    threshold=0.1
)

if model_drift['drift_detected']:
    print(f"Model drift detected! Degradation: {model_drift['degradation']}")

# Check drift
drift_results = detector.check_drift(
    reference_data=reference_features,
    current_data=current_features,
    reference_metrics=ref_metrics,
    current_metrics=curr_metrics
)
```

---

## Exception Handling

### Exception Hierarchy

```python
MLOpsError
├── ExperimentError
├── DeploymentError
├── MonitoringError
└── DriftDetectionError
```

### Code Examples

```python
from src.core.machine_learning.mlops.exceptions import (
    ExperimentError,
    DeploymentError,
    MonitoringError
)

try:
    tracker.log_params(...)
except ExperimentError as e:
    print(f"Experiment tracking failed: {e.message}")

try:
    deployment.deploy_model(...)
except DeploymentError as e:
    print(f"Deployment failed: {e.message}")
```

---

## Functions

### Factory Functions

```python
from src.core.machine_learning.mlops.functions import (
    create_mlops_pipeline,
    create_experiment_tracker,
    create_model_versioning,
    create_model_deployment,
    create_model_monitoring,
    create_drift_detector
)

# Create components
pipeline = create_mlops_pipeline("pipeline_1", tenant_id="tenant_123")
tracker = create_experiment_tracker(tenant_id="tenant_123")
monitoring = create_model_monitoring(tenant_id="tenant_123")
```

---

## Workflow

### Complete MLOps Workflow

1. **Experiment Tracking**: Log experiment parameters and metrics
2. **Model Training**: Train model with tracked hyperparameters
3. **Model Versioning**: Version the trained model
4. **Model Deployment**: Deploy to staging environment
5. **Model Monitoring**: Monitor performance in staging
6. **Drift Detection**: Check for data/model drift
7. **Production Deployment**: Deploy to production if validation passes
8. **Continuous Monitoring**: Monitor production performance

---

## Customization

### Custom Pipeline Stages

```python
from src.core.machine_learning.mlops.mlops_pipeline import PipelineStage

# Add custom stage
class CustomPipelineStage(PipelineStage):
    CUSTOM_STAGE = "custom_stage"

# Use in pipeline
pipeline.run_stage(CustomPipelineStage.CUSTOM_STAGE)
```

### Custom Drift Detection

```python
class CustomDriftDetector(DriftDetector):
    def detect_custom_drift(self, data1, data2):
        # Custom drift detection logic
        return drift_result
```

