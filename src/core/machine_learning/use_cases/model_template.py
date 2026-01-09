"""
Model Template

Template for creating new ML use case models.
Copy this file to your use case folder and implement the methods.
"""

from typing import Any, Dict, Optional
from .base_model import BaseMLModel
import logging

logger = logging.getLogger(__name__)


class UseCaseModelTemplate(BaseMLModel):
    """
    Template for creating new ML use case models.
    
    Instructions:
    1. Copy this file to your use case folder (e.g., ticket_classifier.py)
    2. Rename the class to match your use case
    3. Implement all abstract methods from BaseMLModel
    4. Add use case-specific logic
    """
    
    def __init__(
        self,
        model_id: str,
        tenant_id: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize use case model.
        
        Args:
            model_id: Unique model identifier
            tenant_id: Optional tenant ID
            **kwargs: Additional model-specific parameters
        """
        super().__init__(model_id, tenant_id, **kwargs)
        
        # Initialize your model here
        # Example: self.model = SomeMLModel()
    
    def train(
        self,
        training_data: Any,
        validation_data: Optional[Any] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Train the model.
        
        Implement your training logic here.
        """
        # TODO: Implement training logic
        # 1. Preprocess training data
        # 2. Initialize/configure model with hyperparameters
        # 3. Train model
        # 4. Evaluate on validation data if provided
        # 5. Return metrics and training results
        
        self.is_trained = True
        return {
            'model_id': self.model_id,
            'metrics': {},
            'status': 'completed'
        }
    
    def predict(
        self,
        input_data: Any,
        **kwargs
    ) -> Any:
        """
        Make predictions.
        
        Implement your prediction logic here.
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # TODO: Implement prediction logic
        # 1. Preprocess input data
        # 2. Make prediction using self.model
        # 3. Postprocess results
        # 4. Return predictions
        
        return None
    
    def evaluate(
        self,
        test_data: Any,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Evaluate model performance.
        
        Implement your evaluation logic here.
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation")
        
        # TODO: Implement evaluation logic
        # 1. Preprocess test data
        # 2. Make predictions
        # 3. Calculate metrics (accuracy, precision, recall, etc.)
        # 4. Return metrics dictionary
        
        return {
            'accuracy': 0.0,
            'precision': 0.0,
            'recall': 0.0,
            'f1': 0.0
        }
    
    def save(
        self,
        filepath: str,
        **kwargs
    ) -> str:
        """
        Save model to file.
        
        Implement your save logic here.
        """
        # TODO: Implement save logic
        # Use joblib or pickle to save self.model
        
        import joblib
        joblib.dump(self.model, filepath)
        logger.info(f"Model saved: {filepath}")
        return filepath
    
    def load(
        self,
        filepath: str,
        **kwargs
    ) -> None:
        """
        Load model from file.
        
        Implement your load logic here.
        """
        # TODO: Implement load logic
        # Load model using joblib or pickle
        
        import joblib
        self.model = joblib.load(filepath)
        self.is_trained = True
        logger.info(f"Model loaded: {filepath}")


