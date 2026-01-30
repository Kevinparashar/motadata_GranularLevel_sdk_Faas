"""
Model Serving Factory and Convenience Functions

High-level convenience functions for model serving operations.
"""

from typing import Any, Optional

from .batch_predictor import BatchPredictor
from .model_server import ModelServer
from .realtime_predictor import RealtimePredictor


def create_model_server(
    model_manager: Any, host: str = "0.0.0.0", port: int = 8000, tenant_id: Optional[str] = None
) -> ModelServer:
    """Create model server."""
    return ModelServer(model_manager=model_manager, host=host, port=port, tenant_id=tenant_id)


def create_batch_predictor(model_manager: Any, tenant_id: Optional[str] = None) -> BatchPredictor:
    """Create batch predictor."""
    return BatchPredictor(model_manager=model_manager, tenant_id=tenant_id)


def create_realtime_predictor(
    model_manager: Any, cache: Optional[Any] = None, tenant_id: Optional[str] = None
) -> RealtimePredictor:
    """Create realtime predictor."""
    return RealtimePredictor(model_manager=model_manager, cache=cache, tenant_id=tenant_id)
