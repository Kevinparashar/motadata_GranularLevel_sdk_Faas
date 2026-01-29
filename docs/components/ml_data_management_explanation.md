# Motadata ML Data Management - Comprehensive Component Explanation

## Overview

The ML Data Management component handles data lifecycle management, feature store, and ETL pipelines for ML operations. It ensures data quality, versioning, and efficient feature serving.

## Table of Contents

1. [Data Manager](#data-manager)
2. [Data Loader](#data-loader)
3. [Data Validator](#data-validator)
4. [Feature Store](#feature-store)
5. [Data Pipeline](#data-pipeline)
6. [Exception Handling](#exception-handling)
7. [Functions](#functions)
8. [Workflow](#workflow)
9. [Customization](#customization)

---

## Data Manager

### Functionality

DataManager handles the complete data lifecycle:
- **Data Ingestion**: Ingest data from various sources
- **Data Validation**: Validate data quality and schema
- **Data Storage**: Store data with metadata
- **Data Archival**: Archive old data
- **Data Versioning**: Track dataset versions

### Code Examples

#### Ingest Data

```python
from src.core.machine_learning.ml_data_management import DataManager
from src.core.postgresql_database.connection import DatabaseConnection

db = DatabaseConnection(...)
data_manager = DataManager(db, tenant_id="tenant_123")

# Ingest data
dataset_id = data_manager.ingest_data(
    data=ticket_data,
    dataset_name="tickets_2024",
    metadata={
        "source": "ticket_system",
        "date_range": "2024-01-01 to 2024-01-31",
        "record_count": 10000
    }
)

# Validate data
is_valid = data_manager.validate_data(
    data=ticket_data,
    schema={
        "ticket_id": "string",
        "category": "string",
        "priority": "integer",
        "created_at": "datetime"
    }
)

# Archive old data
data_manager.archive_data(dataset_id="old_dataset_123")
```

---

## Data Loader

### Functionality

DataLoader loads data from various sources:
- **CSV Files**: Load from CSV files
- **JSON Files**: Load from JSON files
- **Database**: Load from database queries
- **Multiple Formats**: Support for various data formats

### Code Examples

#### Load from Different Sources

```python
from src.core.machine_learning.ml_data_management import DataLoader
import pandas as pd

loader = DataLoader()

# Load from CSV
df_csv = loader.load_from_csv("tickets.csv")

# Load from JSON
json_data = loader.load_from_json("tickets.json")

# Load from database
df_db = loader.load_from_database(
    db=db_connection,
    query="SELECT * FROM tickets WHERE created_at > %s",
    params=("2024-01-01",)
)
```

---

## Data Validator

### Functionality

DataValidator validates data quality and schema:
- **Schema Validation**: Validate data against schemas
- **Quality Checks**: Check for missing values, duplicates
- **Type Validation**: Validate data types
- **Constraint Validation**: Validate business rules

### Code Examples

#### Validate Data

```python
from src.core.machine_learning.ml_data_management import DataValidator
import pandas as pd

validator = DataValidator()

# Validate DataFrame
validation_result = validator.validate(
    data=df,
    schema={
        "ticket_id": {"type": "string", "required": True},
        "category": {"type": "string", "required": True, "values": ["incident", "request", "problem"]},
        "priority": {"type": "integer", "required": True, "min": 1, "max": 5},
        "created_at": {"type": "datetime", "required": True}
    }
)

if validation_result['valid']:
    print("Data is valid")
else:
    print(f"Validation errors: {validation_result['errors']}")
```

---

## Feature Store

### Functionality

FeatureStore provides centralized feature storage and retrieval:
- **Feature Registration**: Register features with versioning
- **Feature Retrieval**: Retrieve features (online/offline)
- **Feature Versioning**: Track feature versions
- **Feature Serving**: Serve features for training and inference

### Code Examples

#### Register and Retrieve Features

```python
from src.core.machine_learning.ml_data_management import FeatureStore
from src.core.postgresql_database.connection import DatabaseConnection

db = DatabaseConnection(...)
feature_store = FeatureStore(db, tenant_id="tenant_123")

# Register feature
feature_id = feature_store.register_feature(
    feature_name="ticket_features",
    feature_data={
        "ticket_id": [1, 2, 3],
        "category_encoded": [0, 1, 0],
        "priority_normalized": [0.2, 0.8, 0.5],
        "created_at_features": [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    },
    version="1.0.0",
    metadata={
        "description": "Encoded ticket features",
        "feature_count": 10,
        "created_at": "2024-01-15"
    }
)

# Retrieve feature
feature = feature_store.get_feature("ticket_features", version="1.0.0")
print(f"Feature data: {feature['feature_data']}")

# List all features
all_features = feature_store.list_features()
```

---

## Data Pipeline

### Functionality

DataPipeline provides ETL capabilities:
- **Extract**: Extract data from sources
- **Transform**: Transform and clean data
- **Load**: Load data to destinations
- **Pipeline Orchestration**: Execute complete ETL pipelines

### Code Examples

#### Run ETL Pipeline

```python
from src.core.machine_learning.ml_data_management import DataPipeline

pipeline = DataPipeline("ticket_etl_pipeline", tenant_id="tenant_123")

# Run complete pipeline
results = pipeline.run(
    source="ticket_database",
    destination="feature_store",
    transformations=[
        {"type": "clean", "remove_duplicates": True},
        {"type": "encode", "columns": ["category", "priority"]},
        {"type": "normalize", "columns": ["priority", "response_time"]},
        {"type": "feature_extraction", "extract_datetime_features": True}
    ]
)

# Or run stages separately
raw_data = pipeline.extract(source="ticket_database")
transformed_data = pipeline.transform(
    data=raw_data,
    transformations=[...]
)
pipeline.load(data=transformed_data, destination="feature_store")
```

---

## Exception Handling

### Exception Hierarchy

```python
DataManagementError
├── DataLoadError
├── DataValidationError
└── FeatureStoreError
```

### Code Examples

```python
from src.core.machine_learning.ml_data_management.exceptions import (
    DataLoadError,
    DataValidationError,
    FeatureStoreError
)

try:
    data = loader.load_from_csv("tickets.csv")
except DataLoadError as e:
    print(f"Data loading failed: {e.message}")

try:
    validator.validate(data, schema)
except DataValidationError as e:
    print(f"Validation failed: {e.message}")
```

---

## Functions

### Factory Functions

```python
from src.core.machine_learning.ml_data_management.functions import (
    create_data_manager,
    create_data_loader,
    create_data_validator,
    create_feature_store,
    create_data_pipeline
)

# Create components
data_manager = create_data_manager(db, tenant_id="tenant_123")
loader = create_data_loader()
validator = create_data_validator()
feature_store = create_feature_store(db, tenant_id="tenant_123")
pipeline = create_data_pipeline("pipeline_1", tenant_id="tenant_123")
```

---

## Workflow

### Data Management Workflow

1. **Data Ingestion**: Load data from sources
2. **Data Validation**: Validate data quality and schema
3. **Data Transformation**: Transform and clean data
4. **Feature Engineering**: Extract and engineer features
5. **Feature Storage**: Store features in feature store
6. **Data Archival**: Archive old data

---

## Customization

### Custom Data Loader

```python
class CustomDataLoader(DataLoader):
    def load_from_api(self, api_url, params):
        # Custom API loading logic
        response = requests.get(api_url, params=params)
        return pd.DataFrame(response.json())
```

### Custom Validator

```python
class CustomDataValidator(DataValidator):
    def validate_business_rules(self, data, rules):
        # Custom business rule validation
        return validation_result
```

