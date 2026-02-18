"""
ML Service - Main service implementation.

Handles model training, inference, and model management.
"""


import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException, status

from ....core.machine_learning.ml_framework.functions import create_ml_system
from ....core.machine_learning.ml_framework.ml_system import MLSystem
from ...integrations.codec import create_codec_manager
from ...integrations.nats import create_nats_client
from ...integrations.otel import create_otel_tracer
from ...shared.config import ServiceConfig, load_config
from ...shared.contracts import ServiceResponse, extract_headers
from ...shared.database import get_database_connection
from ...shared.middleware import setup_middleware
from .models import (
    BatchPredictRequest,
    DeployModelRequest,
    PredictRequest,
    TrainModelRequest,
)

logger = logging.getLogger(__name__)


class MLService:
    """
    ML Service for machine learning operations.

    Provides REST API for:
    - Model training
    - Model inference
    - Model management
    - Batch prediction
    """

    def __init__(
        self,
        config: ServiceConfig,
        db_connection: Any,
        nats_client: Optional[Any] = None,
        otel_tracer: Optional[Any] = None,
        codec_manager: Optional[Any] = None,
    ):
        """
        Initialize ML Service.
        
        Args:
            config (ServiceConfig): Configuration object or settings.
            db_connection (Any): Input parameter for this operation.
            nats_client (Optional[Any]): Input parameter for this operation.
            otel_tracer (Optional[Any]): Input parameter for this operation.
            codec_manager (Optional[Any]): Input parameter for this operation.
        """
        self.config = config
        self.db = db_connection
        self.nats_client = nats_client
        self.otel_tracer = otel_tracer
        self.codec_manager = codec_manager or create_codec_manager()

        # ML systems are created on-demand per request (stateless)
        # No in-memory caching to ensure statelessness

        # Create FastAPI app
        self.app = FastAPI(
            title="ML Service",
            description="FaaS service for machine learning operations",
            version=config.service_version,
        )

        # Setup middleware
        setup_middleware(self.app)

        # Register startup event to ensure database connection is ready
        @self.app.on_event("startup")
        async def startup_event():
            """Ensure database connection is ready on service startup."""
            if hasattr(self.db, "connect"):
                await self.db.connect()

        # Register routes
        self._register_routes()

    def _get_ml_system(self, tenant_id: str) -> MLSystem:
        """
        Create ML system for tenant (stateless - created on-demand).
        
        Args:
            tenant_id (str): Tenant identifier used for tenant isolation.
        
        Returns:
            MLSystem: Result of the operation.
        """
        # Create ML system on-demand (stateless)
        ml_system = create_ml_system(
            db=self.db,
            tenant_id=tenant_id,
        )
        return ml_system

    def _register_routes(self):
        """Register FastAPI routes."""
        self.app.post(
            "/api/v1/ml/models/train",
            response_model=ServiceResponse,
            status_code=status.HTTP_202_ACCEPTED,
        )(self._handle_train_model)

        self.app.post("/api/v1/ml/models/{model_id}/predict", response_model=ServiceResponse)(
            self._handle_predict
        )

        self.app.post(
            "/api/v1/ml/models/{model_id}/predict/batch", response_model=ServiceResponse
        )(self._handle_batch_predict)

        self.app.get("/api/v1/ml/models", response_model=ServiceResponse)(self._handle_list_models)

        self.app.get("/api/v1/ml/models/{model_id}", response_model=ServiceResponse)(
            self._handle_get_model
        )

        self.app.post("/api/v1/ml/models/{model_id}/deploy", response_model=ServiceResponse)(
            self._handle_deploy_model
        )

        self.app.get("/health")(self._handle_health_check)

    async def _handle_train_model(  # noqa: S7503
        self, request: TrainModelRequest, headers: dict = Header(...)
    ):
        """
        Train a model. Async required for FastAPI route handler.
        
        Args:
            request (TrainModelRequest): Request payload object.
            headers (dict): HTTP headers passed from the caller.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            HTTPException: Raised when this function detects an invalid state or when an underlying call fails.
        """
        standard_headers = extract_headers(**headers)

        span = None
        if self.otel_tracer:
            span = self.otel_tracer.start_span("ml_train_model")
            span.set_attribute("model.type", request.model_type)
            span.set_attribute("tenant.id", standard_headers.tenant_id)

        try:
            # Get ML system
            ml_system = self._get_ml_system(standard_headers.tenant_id)

            # Start training (async)
            model_id = f"model_{standard_headers.request_id[:8]}"
            training_result = await ml_system.train_model(
                model_id=model_id,
                model_type=request.model_type,
                training_data=request.training_data,
                hyperparameters=request.hyperparameters,
            )

            training_id = f"training_{standard_headers.request_id[:8]}"

            # Publish event via NATS
            if self.nats_client:
                await self._publish_training_event(
                    training_id, model_id, standard_headers.tenant_id
                )

            return ServiceResponse(
                success=True,
                data={
                    "training_id": training_id,
                    "model_id": training_result["model_id"],
                    "version": training_result.get("version"),
                    "status": "completed",
                    "metrics": training_result.get("metrics", {}),
                },
                message="Model training completed",
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )
        except Exception as e:
            logger.error(f"Error training model: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to train model: {str(e)}",
            )
        finally:
            if span:
                span.end()

    async def _publish_training_event(
        self, training_id: str, model_id: str, tenant_id: str
    ) -> None:
        """
        Publish training event via NATS.
        
        Args:
            training_id (str): Input parameter for this operation.
            model_id (str): Input parameter for this operation.
            tenant_id (str): Tenant identifier used for tenant isolation.
        
        Returns:
            None: Result of the operation.
        """
        event = {
            "event_type": "ml.training.started",
            "training_id": training_id,
            "model_id": model_id,
            "tenant_id": tenant_id,
        }
        await self.nats_client.publish(
            f"ml.events.{tenant_id}",
            await self.codec_manager.encode(event),
        )

    async def _handle_predict(  # noqa: S7503
        self, model_id: str, request: PredictRequest, headers: dict = Header(...)
    ):
        """
        Make a prediction with a model. Async required for FastAPI route handler.
        
        Args:
            model_id (str): Input parameter for this operation.
            request (PredictRequest): Request payload object.
            headers (dict): HTTP headers passed from the caller.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            HTTPException: Raised when this function detects an invalid state or when an underlying call fails.
        """
        standard_headers = extract_headers(**headers)

        span = None
        if self.otel_tracer:
            span = self.otel_tracer.start_span("ml_predict")
            span.set_attribute("model.id", model_id)
            span.set_attribute("tenant.id", standard_headers.tenant_id)

        try:
            # Get ML system
            ml_system = self._get_ml_system(standard_headers.tenant_id)

            # Make prediction (async)
            # Use model_id from path parameter (route parameter takes precedence)
            prediction = await ml_system.predict(
                model_id=model_id,
                input_data=request.features,
            )

            return ServiceResponse(
                success=True,
                data={
                    "prediction": prediction,
                    "model_id": model_id,
                },
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )
        except Exception as e:
            logger.error(f"Error making prediction: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to make prediction: {str(e)}",
            )
        finally:
            if span:
                span.end()

    async def _handle_batch_predict(  # noqa: S7503
        self, model_id: str, request: BatchPredictRequest, headers: dict = Header(...)
    ):
        """
        Make batch predictions. Async required for FastAPI route handler.
        
        Args:
            model_id (str): Input parameter for this operation.
            request (BatchPredictRequest): Request payload object.
            headers (dict): HTTP headers passed from the caller.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            HTTPException: Raised when this function detects an invalid state or when an underlying call fails.
        """
        standard_headers = extract_headers(**headers)

        try:
            # Get ML system
            ml_system = self._get_ml_system(standard_headers.tenant_id)

            # Make batch predictions (async)
            # Use model_id from path parameter (route parameter takes precedence)
            predictions = await ml_system.predict_batch(
                model_id=model_id,
                input_batch=request.features_list,
            )

            return ServiceResponse(
                success=True,
                data={
                    "predictions": predictions,
                    "count": len(predictions),
                    "model_id": model_id,
                },
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )
        except Exception as e:
            logger.error(f"Error making batch predictions: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to make batch predictions: {str(e)}",
            )

    async def _handle_list_models(  # noqa: S7503
        self, headers: dict = Header(...), limit: int = 100, offset: int = 0
    ):
        """
        List models. Async required for FastAPI route handler.
        
        Args:
            headers (dict): HTTP headers passed from the caller.
            limit (int): Input parameter for this operation.
            offset (int): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        """
        standard_headers = extract_headers(**headers)

        try:
            # Get ML system
            ml_system = self._get_ml_system(standard_headers.tenant_id)

            # List models (async)
            all_models = await ml_system.model_manager.list_models(limit=limit)
            
            # Apply pagination
            paginated_models = all_models[offset : offset + limit]

            return ServiceResponse(
                success=True,
                data={"models": paginated_models, "total": len(all_models)},
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list models: {str(e)}",
            )

    async def _handle_get_model(self, model_id: str, headers: dict = Header(...)):  # noqa: S7503
        """
        Get model by ID. Async required for FastAPI route handler.
        
        Args:
            model_id (str): Input parameter for this operation.
            headers (dict): HTTP headers passed from the caller.
        
        Raises:
            HTTPException: Raised when this function detects an invalid state or when an underlying call fails.
        """
        standard_headers = extract_headers(**headers)

        try:
            # Get ML system
            ml_system = self._get_ml_system(standard_headers.tenant_id)

            # Get model info (async)
            model_info = await ml_system.get_model_info(model_id=model_id)

            return ServiceResponse(
                success=True,
                data=model_info,
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )
        except Exception as e:
            logger.error(f"Error getting model: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get model: {str(e)}",
            )

    async def _handle_deploy_model(  # noqa: S7503
        self, model_id: str, request: DeployModelRequest, headers: dict = Header(...)
    ):
        """
        Deploy a model. Async required for FastAPI route handler.
        
        Args:
            model_id (str): Input parameter for this operation.
            request (DeployModelRequest): Request payload object.
            headers (dict): HTTP headers passed from the caller.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            HTTPException: Raised when this function detects an invalid state or when an underlying call fails.
        """
        standard_headers = extract_headers(**headers)

        try:
            # Get ML system
            ml_system = self._get_ml_system(standard_headers.tenant_id)

            # Load model if not already loaded (async)
            await ml_system.load_model(model_id=model_id, version=request.version)

            return ServiceResponse(
                success=True,
                data={"model_id": model_id, "version": request.version, "status": "deployed"},
                message="Model deployed successfully",
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )
        except Exception as e:
            logger.error(f"Error deploying model: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to deploy model: {str(e)}",
            )

    async def _handle_health_check(self):  # noqa: S7503
        """
        Health check endpoint. Async required for FastAPI route handler.
        
        Returns:
            Any: Result of the operation.
        """
        return {"status": "healthy", "service": "ml-service"}


def create_ml_service(
    service_name: str = "ml-service",
    config_overrides: Optional[Dict[str, Any]] = None,
) -> MLService:
    """
    Create ML Service instance.

    Args:
        service_name: Service name
        config_overrides: Configuration overrides

    Returns:
        MLService instance
    """
    # Load configuration
    config = load_config(service_name, **(config_overrides or {}))

    # Get database connection
    db_manager = get_database_connection(config.database_url)
    db_connection = db_manager.get_connection()

    # Initialize integrations
    nats_client = create_nats_client() if config.enable_nats else None
    otel_tracer = create_otel_tracer() if config.enable_otel else None

    # Create service
    service = MLService(
        config=config,
        db_connection=db_connection,
        nats_client=nats_client,
        otel_tracer=otel_tracer,
    )

    logger.info(f"ML Service created: {service_name}")
    return service
