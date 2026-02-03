"""
Data Ingestion Service - Main service implementation.

Handles file upload and multi-modal data processing.
"""


import asyncio
import json
import logging
import os
import tempfile
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, File, Header, HTTPException, UploadFile, status

from ....core.data_ingestion import create_ingestion_service
from ....core.data_ingestion.ingestion_service import (
    DataIngestionService as CoreDataIngestionService,
)
from ...integrations.codec import create_codec_manager
from ...integrations.nats import create_nats_client
from ...integrations.otel import create_otel_tracer
from ...shared.config import ServiceConfig, load_config
from ...shared.contracts import ServiceResponse, extract_headers
from ...shared.database import get_database_connection
from ...shared.middleware import setup_middleware
from .models import ProcessFileRequest

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

        # Ingestion services are created on-demand per request (stateless)
        # No in-memory caching to ensure statelessness
        self._ingestion_services: Dict[str, CoreDataIngestionService] = {}

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
            tenant_id (str): Tenant identifier used for tenant isolation.
        
        Returns:
            CoreDataIngestionService: Builder instance (returned for call chaining).
        """
        if tenant_id not in self._ingestion_services:
            # Create ingestion service on-demand (stateless)
            # Note: RAG system integration can be added via RAG service URL if needed
            ingestion_service = create_ingestion_service(
                db=self.db,
                tenant_id=tenant_id,
                enable_auto_ingest=True,
            )
            self._ingestion_services[tenant_id] = ingestion_service

        return self._ingestion_services[tenant_id]

    def _register_routes(self):
        """Register FastAPI routes."""
        self.app.post(
            "/api/v1/ingestion/upload",
            response_model=ServiceResponse,
            status_code=status.HTTP_201_CREATED,
        )(self._handle_upload_file)

        self.app.get("/api/v1/ingestion/files/{file_id}", response_model=ServiceResponse)(
            self._handle_get_file
        )

        self.app.post("/api/v1/ingestion/files/{file_id}/process", response_model=ServiceResponse)(
            self._handle_process_file
        )

        self.app.get("/health")(self._handle_health_check)

    async def _handle_upload_file(
        self,
        file: UploadFile = File(...),
        title: Optional[str] = None,
        metadata: Optional[str] = None,
        auto_ingest: bool = True,
        headers: dict = Header(...),
    ):
        """
        Upload and process a file.
        
        Args:
            file (UploadFile): Input parameter for this operation.
            title (Optional[str]): Input parameter for this operation.
            metadata (Optional[str]): Extra metadata for the operation.
            auto_ingest (bool): Input parameter for this operation.
            headers (dict): HTTP headers passed from the caller.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            HTTPException: Raised when this function detects an invalid state or when an underlying call fails.
        """
        standard_headers = extract_headers(**headers)

        span = None
        if self.otel_tracer:
            span = self.otel_tracer.start_span("upload_file")
            span.set_attribute("file.name", file.filename)
            span.set_attribute("tenant.id", standard_headers.tenant_id)

        try:
            # Save uploaded file temporarily
            file_id = f"file_{standard_headers.request_id[:8]}"
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"{file_id}_{file.filename}")

            # Save file asynchronously using thread pool
            content = await file.read()
            await asyncio.to_thread(self._write_file, temp_path, content)

            # Parse metadata from JSON string if provided
            metadata_dict = self._parse_metadata(metadata)

            # Get ingestion service
            ingestion_service = self._get_ingestion_service(standard_headers.tenant_id)

            # Process file
            result = ingestion_service.upload_and_process(
                file_path=temp_path,
                title=title or file.filename,
                metadata=metadata_dict,
            )

            # If auto-ingest, send to RAG service
            if auto_ingest and self.config.rag_service_url:
                file_title = title or file.filename or f"file_{file_id}"
                await self._send_to_rag_service(
                    temp_path, file_title, metadata_dict, standard_headers.tenant_id
                )

            # Publish event via NATS
            if self.nats_client:
                file_name = file.filename or f"file_{file_id}"
                await self._publish_upload_event(file_id, file_name, standard_headers.tenant_id)

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

    @staticmethod
    def _write_file(file_path: str, content: bytes) -> None:
        """
        Write file content to disk (synchronous helper for thread pool).
        
        Args:
            file_path (str): Path of the input file.
            content (bytes): Content text.
        
        Returns:
            None: Result of the operation.
        """
        with open(file_path, "wb") as f:
            f.write(content)

    def _parse_metadata(self, metadata: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Parse metadata from JSON string if provided.
        
        Args:
            metadata (Optional[str]): Extra metadata for the operation.
        
        Returns:
            Optional[Dict[str, Any]]: Dictionary result of the operation.
        """
        if not metadata:
            return None

        try:
            return json.loads(metadata) if isinstance(metadata, str) else metadata
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON metadata, using as string: {metadata}")
            return {"raw": metadata}

    async def _send_to_rag_service(
        self,
        file_path: str,
        title: str,
        metadata: Optional[Dict[str, Any]],
        tenant_id: str,
    ) -> None:
        """
        Send file to RAG service for auto-ingestion.
        
        Args:
            file_path (str): Path of the input file.
            title (str): Input parameter for this operation.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
            tenant_id (str): Tenant identifier used for tenant isolation.
        
        Returns:
            None: Result of the operation.
        """
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.config.rag_service_url}/api/v1/rag/documents",
                json={
                    "title": title,
                    "file_path": file_path,
                    "metadata": metadata,
                },
                headers={"X-Tenant-ID": tenant_id},
            )

    async def _publish_upload_event(self, file_id: str, file_name: str, tenant_id: str) -> None:
        """
        Publish file upload event via NATS.
        
        Args:
            file_id (str): Input parameter for this operation.
            file_name (str): Input parameter for this operation.
            tenant_id (str): Tenant identifier used for tenant isolation.
        
        Returns:
            None: Result of the operation.
        """
        event = {
            "event_type": "ingestion.file.uploaded",
            "file_id": file_id,
            "file_name": file_name,
            "tenant_id": tenant_id,
        }
        await self.nats_client.publish(
            f"ingestion.events.{tenant_id}",
            self.codec_manager.encode(event),
        )

    async def _handle_get_file(self, file_id: str, headers: dict = Header(...)):  # noqa: S7503
        """
        Get file status. Async required for FastAPI route handler.
        
        Args:
            file_id (str): Input parameter for this operation.
            headers (dict): HTTP headers passed from the caller.
        
        Returns:
            Any: Result of the operation.
        """
        standard_headers = extract_headers(**headers)

        # File status retrieval from database - to be implemented
        # For now, return placeholder response
        return ServiceResponse(
            success=True,
            data={"file_id": file_id, "status": "unknown"},
            correlation_id=standard_headers.correlation_id,
            request_id=standard_headers.request_id,
        )

    async def _handle_process_file(  # noqa: S7503
        self, file_id: str, request: ProcessFileRequest, headers: dict = Header(...)
    ):
        """
        Process a file. Async required for FastAPI route handler.
        
        Args:
            file_id (str): Input parameter for this operation.
            request (ProcessFileRequest): Request payload object.
            headers (dict): HTTP headers passed from the caller.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            HTTPException: Raised when this function detects an invalid state or when an underlying call fails.
        """
        standard_headers = extract_headers(**headers)

        try:
            # Get ingestion service (used for future implementation)
            self._get_ingestion_service(standard_headers.tenant_id)

            # Process file - implementation depends on file_id lookup
            # For now, return placeholder response
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

    async def _handle_health_check(self):  # noqa: S7503
        """
        Health check endpoint. Async required for FastAPI route handler.
        
        Returns:
            Any: Result of the operation.
        """
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
