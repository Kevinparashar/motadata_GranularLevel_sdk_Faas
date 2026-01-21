"""
Data Ingestion Service - Main service implementation.

Handles file upload and multi-modal data processing.
"""

import logging
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, HTTPException, Header, UploadFile, File, status

from ....core.data_ingestion import create_ingestion_service
from ....core.data_ingestion.ingestion_service import DataIngestionService as CoreDataIngestionService
from ...shared.config import ServiceConfig, load_config
from ...shared.contracts import ServiceResponse, extract_headers
from ...shared.database import get_database_connection
from ...shared.exceptions import NotFoundError, DependencyError
from ...shared.middleware import setup_middleware
from .models import (
    UploadFileRequest,
    ProcessFileRequest,
    FileResponse,
    ProcessingResponse,
)
from ...integrations.nats import create_nats_client
from ...integrations.otel import create_otel_tracer
from ...integrations.codec import create_codec_manager

logger = logging.getLogger(__name__)


class DataIngestionService:
    """
    Data Ingestion Service for file upload and processing.

    Provides REST API for:
    - File upload
    - File processing
    - File status retrieval
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
        Initialize Data Ingestion Service.

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

        # Ingestion services are created on-demand per request (stateless)
        # No in-memory caching to ensure statelessness

        # Create FastAPI app
        self.app = FastAPI(
            title="Data Ingestion Service",
            description="FaaS service for file upload and multi-modal data processing",
            version=config.service_version,
        )

        # Setup middleware
        setup_middleware(self.app)

        # Register routes
        self._register_routes()

    def _get_ingestion_service(self, tenant_id: str) -> CoreDataIngestionService:
        """
        Get or create ingestion service for tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            DataIngestionService instance
        """
        if tenant_id not in self._ingestion_services:
            # Get RAG service URL for auto-ingestion
            rag_service_url = self.config.rag_service_url

            # Create ingestion service
            # TODO: Get RAG system from RAG Service or create directly
            ingestion_service = create_ingestion_service(
                db=self.db,
                tenant_id=tenant_id,
                enable_auto_ingest=True,
            )
            self._ingestion_services[tenant_id] = ingestion_service

        return self._ingestion_services[tenant_id]

    def _register_routes(self):
        """Register FastAPI routes."""

        @self.app.post("/api/v1/ingestion/upload", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
        async def upload_file(
            file: UploadFile = File(...),
            title: Optional[str] = None,
            metadata: Optional[str] = None,
            auto_ingest: bool = True,
            headers: dict = Header(...),
        ):
            """Upload and process a file."""
            standard_headers = extract_headers(**headers)

            span = None
            if self.otel_tracer:
                span = self.otel_tracer.start_span("upload_file")
                span.set_attribute("file.name", file.filename)
                span.set_attribute("tenant.id", standard_headers.tenant_id)

            try:
                # Save uploaded file temporarily
                import tempfile
                import os

                file_id = f"file_{standard_headers.request_id[:8]}"
                temp_dir = tempfile.gettempdir()
                temp_path = os.path.join(temp_dir, f"{file_id}_{file.filename}")

                # Save file
                with open(temp_path, "wb") as f:
                    content = await file.read()
                    f.write(content)

                # Get ingestion service
                ingestion_service = self._get_ingestion_service(standard_headers.tenant_id)

                # Process file
                result = ingestion_service.upload_and_process(
                    file_path=temp_path,
                    title=title or file.filename,
                    metadata=metadata,
                )

                # If auto-ingest, send to RAG service
                if auto_ingest and self.config.rag_service_url:
                    async with httpx.AsyncClient() as client:
                        await client.post(
                            f"{self.config.rag_service_url}/api/v1/rag/documents",
                            json={
                                "title": title or file.filename,
                                "file_path": temp_path,
                                "metadata": metadata,
                            },
                            headers={"X-Tenant-ID": standard_headers.tenant_id},
                        )

                # Publish event via NATS
                if self.nats_client:
                    event = {
                        "event_type": "ingestion.file.uploaded",
                        "file_id": file_id,
                        "file_name": file.filename,
                        "tenant_id": standard_headers.tenant_id,
                    }
                    await self.nats_client.publish(
                        f"ingestion.events.{standard_headers.tenant_id}",
                        self.codec_manager.encode(event),
                    )

                return ServiceResponse(
                    success=True,
                    data={
                        "file_id": file_id,
                        "file_name": file.filename,
                        "status": "uploaded",
                        "result": result,
                    },
                    message="File uploaded and processed successfully",
                    correlation_id=standard_headers.correlation_id,
                    request_id=standard_headers.request_id,
                )
            except Exception as e:
                logger.error(f"Error uploading file: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to upload file: {str(e)}",
                )
            finally:
                if span:
                    span.end()

        @self.app.get("/api/v1/ingestion/files/{file_id}", response_model=ServiceResponse)
        async def get_file(
            file_id: str,
            headers: dict = Header(...),
        ):
            """Get file status."""
            standard_headers = extract_headers(**headers)

            # TODO: Implement file status retrieval from database
            return ServiceResponse(
                success=True,
                data={"file_id": file_id, "status": "unknown"},
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )

        @self.app.post("/api/v1/ingestion/files/{file_id}/process", response_model=ServiceResponse)
        async def process_file(
            file_id: str,
            request: ProcessFileRequest,
            headers: dict = Header(...),
        ):
            """Process a file."""
            standard_headers = extract_headers(**headers)

            try:
                # Get ingestion service
                ingestion_service = self._get_ingestion_service(standard_headers.tenant_id)

                # Process file
                # TODO: Implement actual processing
                result = {"status": "processed", "file_id": file_id}

                return ServiceResponse(
                    success=True,
                    data=result,
                    message="File processed successfully",
                    correlation_id=standard_headers.correlation_id,
                    request_id=standard_headers.request_id,
                )
            except Exception as e:
                logger.error(f"Error processing file: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to process file: {str(e)}",
                )

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "service": "data-ingestion-service"}


def create_data_ingestion_service(
    service_name: str = "data-ingestion-service",
    config_overrides: Optional[Dict[str, Any]] = None,
) -> DataIngestionService:
    """
    Create Data Ingestion Service instance.

    Args:
        service_name: Service name
        config_overrides: Configuration overrides

    Returns:
        DataIngestionService instance
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
    service = DataIngestionService(
        config=config,
        db_connection=db_connection,
        nats_client=nats_client,
        otel_tracer=otel_tracer,
    )

    logger.info(f"Data Ingestion Service created: {service_name}")
    return service

