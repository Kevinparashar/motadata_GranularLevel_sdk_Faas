"""
Predictor

Inference engine for model predictions with preprocessing, postprocessing, and caching.
"""


# Standard library imports
import logging
from typing import Any, List, Optional

# Local application/library specific imports
from ...cache_mechanism import CacheMechanism
from .model_manager import ModelManager

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
        tenant_id: Optional[str] = None,
    ):
        """
        Initialize predictor.
        
        Args:
            model_manager (ModelManager): Input parameter for this operation.
            cache (Optional[CacheMechanism]): Cache instance used to store and fetch cached results.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        """
        self.model_manager = model_manager
        self.cache = cache
        self.tenant_id = tenant_id

        logger.info(f"Predictor initialized for tenant: {tenant_id}")

    def predict(self, model: Any, input_data: Any) -> Any:
        """
        Make a single prediction.
        
        Args:
            model (Any): Model name or identifier to use.
            input_data (Any): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        """
        try:
            result = model.predict(input_data)
            logger.debug("Prediction completed")
            return result
        except (ValueError, AttributeError) as e:
            logger.error(
                f"Prediction failed due to invalid input or model: {str(e)}", exc_info=True
            )
            raise
        except Exception as e:
            logger.error(f"Unexpected error during prediction: {str(e)}", exc_info=True)
            raise

    def predict_batch(self, model: Any, input_batch: List[Any]) -> List[Any]:
        """
        Make batch predictions.
        
        Args:
            model (Any): Model name or identifier to use.
            input_batch (List[Any]): Input parameter for this operation.
        
        Returns:
            List[Any]: List result of the operation.
        """
        try:
            results = model.predict(input_batch)
            logger.debug(f"Batch prediction completed: {len(results)} predictions")
            return results.tolist() if hasattr(results, "tolist") else list(results)
        except (ValueError, AttributeError) as e:
            logger.error(
                f"Batch prediction failed due to invalid input or model: {str(e)}", exc_info=True
            )
            raise
        except Exception as e:
            logger.error(f"Unexpected error during batch prediction: {str(e)}", exc_info=True)
            raise

    def predict_proba(self, model: Any, input_data: Any) -> Any:
        """
        Get prediction probabilities (for classification models).
        
        Args:
            model (Any): Model name or identifier to use.
            input_data (Any): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        """
        try:
            if hasattr(model, "predict_proba"):
                return model.predict_proba(input_data)
            else:
                logger.warning("Model does not support predict_proba")
                return None
        except (ValueError, AttributeError) as e:
            logger.error(
                f"Probability prediction failed due to invalid input or model: {str(e)}",
                exc_info=True,
            )
            raise
        except Exception as e:
            logger.error(f"Unexpected error during probability prediction: {str(e)}", exc_info=True)
            raise
