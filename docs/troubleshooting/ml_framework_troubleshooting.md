# Motadata ML Framework Troubleshooting Guide

This guide helps diagnose and resolve common issues encountered when using the ML Framework.

## Table of Contents

1. [Training Failures](#training-failures)
2. [Prediction Errors](#prediction-errors)
3. [Model Loading Issues](#model-loading-issues)
4. [Memory Management Problems](#memory-management-problems)
5. [Data Processing Errors](#data-processing-errors)
6. [Model Registration Issues](#model-registration-issues)
7. [Performance Issues](#performance-issues)

## Training Failures

### Problem: Training fails with errors

**Symptoms:**
- `TrainingError` exceptions
- Training hangs or times out
- Model not saved after training
- Validation errors during training

**Diagnosis:**
1. Check training data:
```python
try:
    result = ml_system.train_model(
        model_id="ticket_classifier",
        model_type="classification",
        training_data=(X_train, y_train)
    )
except TrainingError as e:
    print(f"Error: {e.message}")
    print(f"Model ID: {e.model_id}")
    print(f"Stage: {e.stage}")
    print(f"Hyperparameters: {e.hyperparameters}")
```

2. Validate data format:
```python
# Check data shapes
print(f"X_train shape: {X_train.shape}")
print(f"y_train shape: {y_train.shape}")

# Check for NaN values
print(f"NaN in X_train: {X_train.isnull().sum().sum()}")
print(f"NaN in y_train: {y_train.isnull().sum()}")
```

**Solutions:**

1. **Invalid Data Format:**
   - Ensure training data is in correct format (tuple of (X, y))
   - Check data types match model requirements
   - Validate feature count matches training data

2. **Missing Values:**
   - Handle missing values before training
   - Use data processor to preprocess data
   - Fill or drop missing values appropriately

3. **Hyperparameter Issues:**
   - Validate hyperparameters match model type
   - Check hyperparameter ranges
   - Use default hyperparameters first

4. **Memory Issues:**
   - Reduce training data size
   - Use batch training
   - Increase available memory

## Prediction Errors

### Problem: Predictions fail or return incorrect results

**Symptoms:**
- `PredictionError` exceptions
- Predictions return None or empty results
- Incorrect prediction types
- Model not found errors

**Diagnosis:**
1. Check model exists:
```python
try:
    model_info = ml_system.get_model_info("ticket_classifier")
    print(f"Model found: {model_info}")
except ModelNotFoundError as e:
    print(f"Model not found: {e.model_id}")
```

2. Validate input data:
```python
# Check input shape
print(f"Input shape: {input_data.shape}")

# Check input type
print(f"Input type: {type(input_data)}")

# Check for NaN
print(f"NaN in input: {pd.DataFrame(input_data).isnull().sum().sum()}")
```

**Solutions:**

1. **Model Not Loaded:**
   - Load model explicitly: `ml_system.load_model("model_id")`
   - Check model is registered
   - Verify model path exists

2. **Input Format Mismatch:**
   - Ensure input matches training data format
   - Use data processor to preprocess input
   - Check feature count matches

3. **Model Version Issues:**
   - Specify correct model version
   - Check version exists in registry
   - Use latest version if not specified

4. **Cache Issues:**
   - Clear cache if predictions are stale
   - Disable cache for debugging
   - Check cache TTL settings

## Model Loading Issues

### Problem: Models fail to load

**Symptoms:**
- `ModelLoadError` exceptions
- Model file not found
- Corrupted model files
- Memory errors during loading

**Diagnosis:**
1. Check model file exists:
```python
import os
model_path = "./models/ticket_classifier_v1.joblib"
if os.path.exists(model_path):
    print(f"Model file exists: {model_path}")
else:
    print(f"Model file not found: {model_path}")
```

2. Check file integrity:
```python
import joblib
try:
    model = joblib.load(model_path)
    print("Model loaded successfully")
except Exception as e:
    print(f"Error loading model: {e}")
```

**Solutions:**

1. **File Not Found:**
   - Verify model path is correct
   - Check model was saved successfully
   - Verify file permissions

2. **Corrupted Model File:**
   - Retrain and save model
   - Check disk space
   - Verify file wasn't corrupted during transfer

3. **Memory Issues:**
   - Increase available memory
   - Unload other models
   - Use smaller models

4. **Version Mismatch:**
   - Check joblib version compatibility
   - Re-save model with current version
   - Verify model format

## Memory Management Problems

### Problem: Memory limit exceeded

**Symptoms:**
- Memory errors during model loading
- Models automatically unloaded
- System runs out of memory
- Performance degradation

**Diagnosis:**
1. Check memory usage:
```python
# Check loaded models
print(f"Loaded models: {list(ml_system._loaded_models.keys())}")
print(f"Memory usage: {ml_system._model_memory_usage}")
```

2. Check memory limit:
```python
print(f"Max memory (MB): {ml_system.max_memory_mb}")
current_memory = sum(ml_system._model_memory_usage.values())
print(f"Current memory (MB): {current_memory}")
```

**Solutions:**

1. **Increase Memory Limit:**
   ```python
   ml_system = MLSystem(
       db=db,
       max_memory_mb=4096  # Increase limit
   )
   ```

2. **Unload Unused Models:**
   ```python
   ml_system.unload_model("unused_model_id")
   ```

3. **Use Smaller Models:**
   - Use simpler model architectures
   - Reduce model complexity
   - Use model compression

4. **Optimize Model Loading:**
   - Load models on-demand
   - Use lazy loading
   - Implement model pooling

## Data Processing Errors

### Problem: Data preprocessing fails

**Symptoms:**
- `DataProcessingError` exceptions
- Preprocessed data has wrong format
- Missing features after preprocessing
- Type conversion errors

**Diagnosis:**
1. Check input data:
```python
processor = DataProcessor()
try:
    processed = processor.preprocess(data)
except DataProcessingError as e:
    print(f"Error: {e.message}")
    print(f"Operation: {e.operation}")
    print(f"Data type: {e.data_type}")
```

**Solutions:**

1. **Invalid Data Type:**
   - Convert to pandas DataFrame or numpy array
   - Check data format matches expected type
   - Use appropriate data loader

2. **Missing Features:**
   - Check feature extraction configuration
   - Verify all required columns present
   - Handle missing columns appropriately

3. **Type Conversion Errors:**
   - Validate data types before processing
   - Convert types explicitly
   - Handle mixed types

## Model Registration Issues

### Problem: Models fail to register

**Symptoms:**
- Registration errors
- Models not appearing in registry
- Duplicate model errors
- Metadata not saved

**Diagnosis:**
1. Check database connection:
```python
# Test database connection
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
```

2. Check model metadata:
```python
model_info = model_manager.get_model("ticket_classifier")
print(f"Model info: {model_info}")
```

**Solutions:**

1. **Database Connection Issues:**
   - Verify database is accessible
   - Check connection pool configuration
   - Test database connectivity

2. **Duplicate Model Errors:**
   - Use different model IDs
   - Use versioning for same model
   - Check existing models before registration

3. **Metadata Issues:**
   - Validate metadata format (must be JSON-serializable)
   - Check metadata size limits
   - Use appropriate metadata structure

## Performance Issues

### Problem: Slow training or prediction

**Symptoms:**
- Training takes too long
- Predictions are slow
- High memory usage
- CPU/GPU underutilization

**Solutions:**

1. **Optimize Data Processing:**
   - Use batch processing
   - Preprocess data in parallel
   - Cache preprocessed data

2. **Optimize Model:**
   - Use simpler models
   - Reduce feature count
   - Use feature selection

3. **Use Caching:**
   ```python
   # Enable prediction caching
   prediction = ml_system.predict(
       model_id="ticket_classifier",
       input_data=data,
       use_cache=True
   )
   ```

4. **Batch Predictions:**
   ```python
   # Use batch predictions for multiple inputs
   predictions = ml_system.predict_batch(
       model_id="ticket_classifier",
       input_batch=batch_data,
       batch_size=32
   )
   ```

