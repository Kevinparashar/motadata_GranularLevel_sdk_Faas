# Motadata ML Use Cases

## Overview

This directory contains the template structure and base classes for creating ITSM-specific ML use case models. When a use case is defined, create a new folder here and implement the model following the `BaseMLModel` interface.

## Structure

```
use_cases/
├── __init__.py              # Exports BaseMLModel
├── base_model.py            # Base class interface for all ML models
├── model_template.py        # Template for creating new models
└── README.md                # This file
```

## Creating a New Use Case

### Step 1: Create Use Case Folder

Create a new folder for your use case (e.g., `ticket_classifier/`):

```bash
mkdir -p src/core/machine_learning/use_cases/ticket_classifier
```

### Step 2: Copy Template

Copy `model_template.py` to your use case folder:

```bash
cp src/core/machine_learning/use_cases/model_template.py \
   src/core/machine_learning/use_cases/ticket_classifier/ticket_classifier.py
```

### Step 3: Implement Your Model

1. Rename the class to match your use case
2. Implement all abstract methods from `BaseMLModel`:
   - `train()`: Training logic
   - `predict()`: Prediction logic
   - `evaluate()`: Evaluation logic
   - `save()`: Model serialization
   - `load()`: Model deserialization
3. Add use case-specific logic and features

### Step 4: Create Supporting Files

Create additional files as needed:
- `__init__.py`: Export your model class
- `README.md`: Document your use case
- `config.py`: Configuration for your model
- `preprocessing.py`: Data preprocessing specific to your use case

## Example: Ticket Classifier

```python
from ..use_cases.base_model import BaseMLModel
from sklearn.ensemble import RandomForestClassifier
import joblib

class TicketClassifier(BaseMLModel):
    def __init__(self, model_id: str, tenant_id: Optional[str] = None):
        super().__init__(model_id, tenant_id)
        self.model = RandomForestClassifier()
    
    def train(self, training_data, validation_data=None, hyperparameters=None, **kwargs):
        X_train, y_train = training_data
        self.model.fit(X_train, y_train)
        # ... evaluation logic ...
        self.is_trained = True
        return {'metrics': {...}}
    
    def predict(self, input_data, **kwargs):
        return self.model.predict(input_data)
    
    # ... implement other methods ...
```

## Integration with ML Framework

Your use case model can be integrated with the ML Framework:

```python
from src.core.machine_learning.ml_framework import MLSystem
from src.core.machine_learning.use_cases.ticket_classifier import TicketClassifier

# Create ML system
ml_system = MLSystem(db, tenant_id="tenant_123")

# Train your model
classifier = TicketClassifier("ticket_classifier_v1", tenant_id="tenant_123")
training_result = classifier.train(training_data, hyperparameters={...})

# Save model
model_path = classifier.save("./models/ticket_classifier.joblib")

# Register with ML system
ml_system.model_manager.register_model(
    model_id="ticket_classifier",
    model_type="classification",
    model_path=model_path,
    version="1.0.0"
)
```

## Best Practices

1. **Follow Base Interface**: Always inherit from `BaseMLModel`
2. **Document Your Use Case**: Create a README.md explaining the use case
3. **Handle Errors**: Implement proper error handling
4. **Log Operations**: Use logging for important operations
5. **Support Multi-Tenancy**: Use tenant_id for data isolation
6. **Version Your Models**: Track model versions
7. **Test Your Model**: Create unit tests for your use case

## Available Use Cases

When use cases are implemented, they will be listed here:

- (No use cases implemented yet)

## Next Steps

1. Define your use case requirements
2. Create the use case folder
3. Implement the model following the template
4. Test and validate
5. Integrate with ML Framework
6. Document your use case


