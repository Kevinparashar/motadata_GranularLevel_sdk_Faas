"""
Predictor

Inference engine for model predictions with preprocessing, postprocessing, and caching.
"""

from typing import Any, List, Optional
import logging

from .model_manager import ModelManager
from ...cache_mechanism import CacheMechanism

logger = logging.getLogger(__name__)


class Predictor:
    """
    Handles model inference.
    
    Provides single and batch prediction capabilities with preprocessing,
    postprocessing, and caching support.
    """
    
    def __init__(
        self,
        model_manager: ModelManager,
        cache: Optional[CacheMechanism] = None,
        tenant_id: Optional[str] = None
    ):
        """
        Initialize predictor.
        
        Args:
            model_manager: Model manager instance
            cache: Optional cache mechanism
            tenant_id: Optional tenant ID
        """
        self.model_manager = model_manager
        self.cache = cache
        self.tenant_id = tenant_id
        
        logger.info(f"Predictor initialized for tenant: {tenant_id}")
    
    def predict(
        self,
        model: Any,
        input_data: Any
    ) -> Any:
        """
        Make a single prediction.
        
        Args:
            model: Loaded model instance
            input_data: Preprocessed input data
            
        Returns:
            Prediction result
        """
        try:
            result = model.predict(input_data)
            logger.debug("Prediction completed")
            return result
        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}", exc_info=True)
            raise
    
    def predict_batch(
        self,
        model: Any,
        input_batch: List[Any]
    ) -> List[Any]:
        """
        Make batch predictions.
        
        Args:
            model: Loaded model instance
            input_batch: List of preprocessed input data
            
        Returns:
            List of prediction results
        """
        try:
            results = model.predict(input_batch)
            logger.debug(f"Batch prediction completed: {len(results)} predictions")
            return results.tolist() if hasattr(results, 'tolist') else list(results)
        except Exception as e:
            logger.error(f"Batch prediction failed: {str(e)}", exc_info=True)
            raise
    
    def predict_proba(
        self,
        model: Any,
        input_data: Any
    ) -> Any:
        """
        Get prediction probabilities (for classification models).
        
        Args:
            model: Loaded model instance
            input_data: Preprocessed input data
            
        Returns:
            Prediction probabilities
        """
        try:
            if hasattr(model, 'predict_proba'):
                return model.predict_proba(input_data)
            else:
                logger.warning("Model does not support predict_proba")
                return None
        except Exception as e:
            logger.error(f"Probability prediction failed: {str(e)}", exc_info=True)
            raise


