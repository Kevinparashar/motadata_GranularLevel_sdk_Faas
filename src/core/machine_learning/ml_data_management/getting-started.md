# MOTADATA - GETTING STARTED WITH ML DATA MANAGEMENT

**Complete guide for getting started with ML Data Management, from data ingestion to feature retrieval.**

## Overview

The ML Data Management component handles data lifecycle, feature store, and ETL pipelines for ML operations. This guide explains the complete workflow from data ingestion to feature retrieval.

## Entry Point

The primary entry point for data management:

```python
from src.core.machine_learning.ml_data_management import (
    create_data_manager,
    create_feature_store,
    create_data_loader,
    create_data_validator
)
```

## Input Requirements

### Required Inputs

1. **Database Connection**: PostgreSQL database for data storage
2. **Tenant ID**: Optional tenant ID for multi-tenancy

## Process Flow

### Step 1: Data Manager Creation

**What Happens:**
1. Data manager is initialized
2. Database connection is validated
3. Data storage is configured

**Code:**
```python
data_manager = create_data_manager(db, tenant_id="tenant_123")
```

### Step 2: Data Ingestion

**What Happens:**
1. Data is validated
2. Data is stored in database
3. Metadata is recorded
4. Dataset ID is returned

**Code:**
```python
dataset_id = data_manager.ingest_data(
    data=ticket_data,
    dataset_name="tickets_2024",
    metadata={"source": "ticket_system", "date": "2024-01-15"},
    tenant_id="tenant_123"
)
```

**Input:**
- `data`: Data to ingest (DataFrame, list, dict)
- `dataset_name`: Name for the dataset
- `metadata`: Optional metadata dictionary
- `tenant_id`: Optional tenant ID

**Internal Process:**
```
ingest_data()
  ├─> Validate data format
  ├─> Store in database
  ├─> Record metadata
  └─> Return dataset ID
```

### Step 3: Feature Store Creation

**What Happens:**
1. Feature store is initialized
2. Feature registry is created
3. Storage is configured

**Code:**
```python
feature_store = create_feature_store(db, tenant_id="tenant_123")
```

### Step 4: Feature Registration

**What Happens:**
1. Features are validated
2. Features are stored
3. Version is assigned
4. Metadata is recorded

**Code:**
```python
feature_store.register_feature(
    feature_name="ticket_features",
    feature_data={
        "ticket_id": [1, 2, 3],
        "priority": [1, 2, 1],
        "category": [0, 1, 0]
    },
    version="1.0.0",
    metadata={"description": "Ticket classification features"}
)
```

## Output

### Data Ingestion Output

```python
{
    "dataset_id": "dataset_123",
    "status": "success",
    "rows_ingested": 1000,
    "columns": ["ticket_id", "priority", "category"]
}
```

### Feature Retrieval Output

```python
{
    "features": {
        "ticket_id": [1, 2, 3],
        "priority": [1, 2, 1],
        "category": [0, 1, 0]
    },
    "version": "1.0.0",
    "metadata": {...}
}
```

## Where Output is Used

### 1. Training Data

```python
# Retrieve data for training
data = data_manager.get_dataset("tickets_2024", tenant_id="tenant_123")
X = data.drop("category", axis=1)
y = data["category"]
```

### 2. Feature Engineering

```python
# Get features from feature store
features = feature_store.get_feature(
    feature_name="ticket_features",
    version="1.0.0",
    tenant_id="tenant_123"
)
```

## Complete Example

```python
import pandas as pd
from src.core.machine_learning.ml_data_management import (
    create_data_manager,
    create_feature_store,
    create_data_loader
)
from src.core.postgresql_database import DatabaseConnection

# Step 1: Initialize (Entry Point)
db = DatabaseConnection(...)
data_manager = create_data_manager(db, tenant_id="tenant_123")
feature_store = create_feature_store(db, tenant_id="tenant_123")

# Step 2: Ingest Data (Input)
df = pd.read_csv("tickets.csv")
dataset_id = data_manager.ingest_data(
    data=df,
    dataset_name="tickets_2024",
    tenant_id="tenant_123"
)

# Step 3: Register Features (Process)
feature_store.register_feature(
    feature_name="ticket_features",
    feature_data=df[["ticket_id", "priority", "category"]],
    version="1.0.0",
    tenant_id="tenant_123"
)

# Step 4: Retrieve Features (Output)
features = feature_store.get_feature(
    feature_name="ticket_features",
    version="1.0.0",
    tenant_id="tenant_123"
)
```

## Next Steps

- See [README.md](README.md) for detailed component documentation
- Check [docs/components/ml_data_management_explanation.md](../../../../docs/components/ml_data_management_explanation.md) for comprehensive guide
- Review [troubleshooting guide](../../../../docs/troubleshooting/ml_data_management_troubleshooting.md) for common issues

