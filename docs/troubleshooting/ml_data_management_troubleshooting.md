# MOTADATA - ML DATA MANAGEMENT TROUBLESHOOTING

**Troubleshooting guide for diagnosing and resolving common issues with the ML Data Management component.**

This guide helps diagnose and resolve common issues encountered when using ML Data Management.

## Table of Contents

1. [Data Loading Issues](#data-loading-issues)
2. [Data Validation Failures](#data-validation-failures)
3. [Feature Store Problems](#feature-store-problems)
4. [Data Pipeline Errors](#data-pipeline-errors)
5. [Data Ingestion Issues](#data-ingestion-issues)

## Data Loading Issues

### Problem: Data fails to load

**Symptoms:**
- `DataLoadError` exceptions
- Empty data loaded
- Incorrect data format
- File not found errors

**Diagnosis:**
1. Check file exists:
```python
import os
if os.path.exists("tickets.csv"):
    print("File exists")
else:
    print("File not found")
```

2. Check file format:
```python
try:
    df = loader.load_from_csv("tickets.csv")
    print(f"Loaded {len(df)} rows")
except DataLoadError as e:
    print(f"Error: {e.message}")
```

**Solutions:**

1. **File Not Found:**
   - Verify file path is correct
   - Check file permissions
   - Use absolute paths

2. **Format Issues:**
   - Verify file format matches loader
   - Check file encoding
   - Validate CSV structure

3. **Empty Data:**
   - Check file is not empty
   - Verify data is in correct format
   - Check for header rows

## Data Validation Failures

### Problem: Data validation fails

**Symptoms:**
- `DataValidationError` exceptions
- Validation returns invalid
- Schema mismatches
- Type errors

**Diagnosis:**
1. Check validation result:
```python
result = validator.validate(data, schema)
if not result['valid']:
    print(f"Errors: {result['errors']}")
```

2. Check data schema:
```python
print(f"Data columns: {df.columns}")
print(f"Data types: {df.dtypes}")
```

**Solutions:**

1. **Schema Mismatches:**
   - Verify schema matches data
   - Check column names
   - Validate data types

2. **Missing Values:**
   - Handle missing values before validation
   - Use appropriate fill strategies
   - Check required fields

3. **Type Errors:**
   - Convert types explicitly
   - Validate type conversions
   - Check for mixed types

## Feature Store Problems

### Problem: Feature store operations fail

**Symptoms:**
- `FeatureStoreError` exceptions
- Features not registered
- Features not retrieved
- Version conflicts

**Diagnosis:**
1. Check feature registration:
```python
try:
    feature_id = feature_store.register_feature(...)
except FeatureStoreError as e:
    print(f"Error: {e.message}")
```

2. Check feature retrieval:
```python
feature = feature_store.get_feature("ticket_features")
if not feature:
    print("Feature not found")
```

**Solutions:**

1. **Feature Not Found:**
   - Verify feature name is correct
   - Check feature version exists
   - List all features to verify

2. **Version Conflicts:**
   - Use different versions
   - Check existing versions
   - Update version if needed

3. **Data Format Issues:**
   - Ensure feature data is JSON-serializable
   - Validate feature structure
   - Check data types

## Data Pipeline Errors

### Problem: Pipeline execution fails

**Symptoms:**
- Pipeline errors
- Transformations fail
- Data not loaded
- Pipeline hangs

**Diagnosis:**
1. Check pipeline status:
```python
try:
    results = pipeline.run(...)
except Exception as e:
    print(f"Pipeline error: {e}")
```

2. Check individual stages:
```python
data = pipeline.extract(source)
transformed = pipeline.transform(data, transformations)
```

**Solutions:**

1. **Extract Failures:**
   - Verify source is accessible
   - Check source format
   - Validate source configuration

2. **Transform Failures:**
   - Check transformation configuration
   - Validate transformation types
   - Review transformation logic

3. **Load Failures:**
   - Verify destination is accessible
   - Check destination format
   - Validate permissions

## Data Ingestion Issues

### Problem: Data ingestion fails

**Symptoms:**
- Ingestion errors
- Data not stored
- Metadata not saved
- Duplicate data

**Diagnosis:**
1. Check database connection:
```python
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
```

2. Check ingestion result:
```python
dataset_id = data_manager.ingest_data(...)
if not dataset_id:
    print("Ingestion failed")
```

**Solutions:**

1. **Database Issues:**
   - Verify database connection
   - Check table exists
   - Validate permissions

2. **Metadata Issues:**
   - Ensure metadata is JSON-serializable
   - Check metadata size
   - Validate metadata structure

3. **Duplicate Data:**
   - Check for existing datasets
   - Use unique dataset names
   - Implement deduplication

