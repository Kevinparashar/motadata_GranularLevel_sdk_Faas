"""
ML Service - Main service implementation.

Handles model training, inference, and model management.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException, status

from ....core.machine_learning.ml_framework import create_ml_system
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
    ModelResponse,
    PredictionResponse,
    PredictRequest,
    TrainingResponse,
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
            config: Service configuration
            db_connection: Database connection
            nats_client: NATS client (optional)
            otel_tracer: OTEL tracer (optional)
            codec_manager: Codec manager (optional)
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

        # Register routes
        self._register_routes()

    def _get_ml_system(self, tenant_id: str) -> MLSystem:
        """
        Create ML system for tenant (stateless - created on-demand).

        Args:
            tenant_id: Tenant ID

        Returns:
            MLSystem instance
        """
        # Create ML system on-demand (stateless)
        ml_system = create_ml_system(
            db=self.db,
            tenant_id=tenant_id,
        )
        return ml_system

    def _register_routes(self):
        """Register FastAPI routes."""

        @self.app.post(
            "/api/v1/ml/models/train",
            response_model=ServiceResponse,
            status_code=status.HTTP_202_ACCEPTED,
        )
        async def train_model(
            request: TrainModelRequest,
            headers: dict = Header(...),
        ):
            """Train a model."""
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
                training_id = f"training_{standard_headers.request_id[:8]}"
                model_id = f"model_{standard_headers.request_id[:8]}"

                # TODO: SDK-SVC-001 - Implement actual training
                # Placeholder - replace with actual ML training implementation
                # result = await ml_system.train_model_async(
                #     model_type=request.model_type,
                #     training_data=request.training_data,
                #     hyperparameters=request.hyperparameters,
                #     validation_split=request.validation_split,
                # )

                # Publish event via NATS
                if self.nats_client:
                    event = {
                        "event_type": "ml.training.started",
                        "training_id": training_id,
                        "model_id": model_id,
                        "tenant_id": standard_headers.tenant_id,
                    }
                    await self.nats_client.publish(
                        f"ml.events.{standard_headers.tenant_id}",
                        self.codec_manager.encode(event),
                    )

                return ServiceResponse(
                    success=True,
                    data={
                        "training_id": training_id,
                        "model_id": model_id,
                        "status": "started",
                    },
                    message="Model training started",
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

        @self.app.post("/api/v1/ml/models/{model_id}/predict", response_model=ServiceResponse)
        async def predict(
            model_id: str,
            request: PredictRequest,
            headers: dict = Header(...),
        ):
            """Make a prediction with a model."""
            standard_headers = extract_headers(**headers)

            span = None
            if self.otel_tracer:
                span = self.otel_tracer.start_span("ml_predict")
                span.set_attribute("model.id", model_id)
                span.set_attribute("tenant.id", standard_headers.tenant_id)

            try:
                # Get ML system
                ml_system = self._get_ml_system(standard_headers.tenant_id)

                # Make prediction
                # TODO: SDK-SVC-001 - Implement actual prediction
                # Placeholder - replace with actual ML prediction implementation
                # result = await ml_system.predict_async(
                #     model_id=model_id,
                #     features=request.features,
                # )

                # Placeholder response
                result = {"prediction": "placeholder", "confidence": 0.95}

                return ServiceResponse(
                    success=True,
                    data={
                        "prediction": result["prediction"],
                        "confidence": result.get("confidence"),
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

        @self.app.post("/api/v1/ml/models/{model_id}/predict/batch", response_model=ServiceResponse)
        async def batch_predict(
            model_id: str,
            request: BatchPredictRequest,
            headers: dict = Header(...),
        ):
            """Make batch predictions."""
            standard_headers = extract_headers(**headers)

            try:
                # Get ML system
                ml_system = self._get_ml_system(standard_headers.tenant_id)

                # Make batch predictions
                # TODO: SDK-SVC-001 - Implement actual batch prediction
                # Placeholder - replace with actual ML batch prediction implementation
                # results = await ml_system.predict_batch_async(
                #     model_id=model_id,
                #     features_list=request.features_list,
                # )

                # Placeholder response
                results = [{"prediction": "placeholder"} for _ in request.features_list]

                return ServiceResponse(
                    success=True,
                    data={
                        "predictions": results,
                        "count": len(results),
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

        @self.app.get("/api/v1/ml/models", response_model=ServiceResponse)
        async def list_models(
            headers: dict = Header(...),
            limit: int = 100,
            offset: int = 0,
        ):
            """List models."""
            standard_headers = extract_headers(**headers)

            # TODO: SDK-SVC-001 - Implement model listing from database
            # Placeholder - replace with actual database query implementation
            return ServiceResponse(
                success=True,
                data={"models": [], "total": 0},
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )

        @self.app.get("/api/v1/ml/models/{model_id}", response_model=ServiceResponse)
        async def get_model(
            model_id: str,
            headers: dict = Header(...),
        ):
            """Get model by ID."""
            standard_headers = extract_headers(**headers)

            # TODO: SDK-SVC-001 - Implement model retrieval from database
            # Placeholder - replace with actual database query implementation
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Model retrieval not yet implemented",
            )

        @self.app.post("/api/v1/ml/models/{model_id}/deploy", response_model=ServiceResponse)
        async def deploy_model(
            model_id: str,
            request: DeployModelRequest,
            headers: dict = Header(...),
        ):
            """Deploy a model."""
            standard_headers = extract_headers(**headers)

            try:
                # Get ML system
                ml_system = self._get_ml_system(standard_headers.tenant_id)

                # Deploy model
                # TODO: SDK-SVC-001 - Implement actual deployment
                # Placeholder - replace with actual ML model deployment implementation
                # await ml_system.deploy_model_async(model_id, request.version)

                return ServiceResponse(
                    success=True,
                    data={"model_id": model_id, "status": "deployed"},
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

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
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
    otel_tracer = create_otel_tracer(config.service_name) if config.enable_otel else None

    # Create service
    service = MLService(
        config=config,
        db_connection=db_connection,
        nats_client=nats_client,
        otel_tracer=otel_tracer,
    )

    logger.info(f"ML Service created: {service_name}")
    return service
