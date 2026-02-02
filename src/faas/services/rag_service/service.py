"""
RAG Service - Main service implementation.

Handles document ingestion, query processing, document management, and vector search.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException, status

from ....core.litellm_gateway import create_gateway
from ....core.rag import create_rag_system, quick_rag_query_async
from ....core.rag.rag_system import RAGSystem
from ...integrations.codec import create_codec_manager
from ...integrations.nats import create_nats_client
from ...integrations.otel import create_otel_tracer
from ...shared.config import ServiceConfig, load_config
from ...shared.contracts import ServiceResponse, extract_headers
from ...shared.database import get_database_connection
from ...shared.middleware import setup_middleware
from .models import (
    IngestDocumentRequest,
    QueryRequest,
    SearchRequest,
    UpdateDocumentRequest,
)

logger = logging.getLogger(__name__)


class RAGService:
    """
    RAG Service for document-based Q&A.

    Provides REST API for:
    - Document ingestion
    - Query processing
    - Document management
    - Vector search
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
        Initialize RAG Service.

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

        # RAG systems are created on-demand per request (stateless)
        # No in-memory caching to ensure statelessness

        # Create FastAPI app
        self.app = FastAPI(
            title="RAG Service",
            description="FaaS service for Retrieval-Augmented Generation",
            version=config.service_version,
        )

        # Setup middleware
        setup_middleware(self.app)

        # Register routes
        self._register_routes()

    def _get_rag_system(self, tenant_id: str) -> RAGSystem:  # noqa: S1172
        """
        Create RAG system for tenant (stateless - created on-demand).

        Args:
            tenant_id: Tenant ID (reserved for future multi-tenant support)

        Returns:
            RAGSystem instance
        """
        # Create RAG system on-demand (stateless)
        # Get gateway client
        gateway = self._get_gateway_client(tenant_id)

        # Create RAG system
        rag_system = create_rag_system(
            db=self.db,
            gateway=gateway,
            embedding_model="text-embedding-3-small",
            generation_model="gpt-4",
        )

        return rag_system

    def _get_gateway_client(self, tenant_id: str):  # noqa: S1172
        """
        Get gateway client for LLM calls.

        Args:
            tenant_id: Tenant ID (reserved for future multi-tenant support)

        Returns:
            Gateway client instance
        """
        # Create direct gateway
        # In production, could call Gateway Service if config.gateway_service_url is set
        import os

        api_key = os.getenv("OPENAI_API_KEY", "")
        return create_gateway(api_keys={"openai": api_key} if api_key else {})

    def _register_routes(self):
        """Register FastAPI routes."""
        self.app.post(
            "/api/v1/rag/documents",
            response_model=ServiceResponse,
            status_code=status.HTTP_201_CREATED,
        )(self._handle_ingest_document)

        self.app.post("/api/v1/rag/query", response_model=ServiceResponse)(self._handle_query)

        self.app.post("/api/v1/rag/search", response_model=ServiceResponse)(self._handle_search)

        # Define document endpoint path constant
        document_path = "/api/v1/rag/documents/{document_id}"
        self.app.get(document_path, response_model=ServiceResponse)(self._handle_get_document)

        self.app.put(document_path, response_model=ServiceResponse)(self._handle_update_document)

        self.app.delete(document_path, status_code=status.HTTP_204_NO_CONTENT)(
            self._handle_delete_document
        )

        self.app.get("/api/v1/rag/documents", response_model=ServiceResponse)(
            self._handle_list_documents
        )

        self.app.get("/health")(self._handle_health_check)

    async def _handle_ingest_document(
        self, request: IngestDocumentRequest, headers: dict = Header(...)
    ):
        """Ingest a document into the RAG system."""
        standard_headers = extract_headers(**headers)

        span = None
        if self.otel_tracer:
            span = self.otel_tracer.start_span("ingest_document")
            span.set_attribute("document.title", request.title)
            span.set_attribute("tenant.id", standard_headers.tenant_id)

        try:
            # Get RAG system (created on-demand, stateless)
            rag_system = self._get_rag_system(standard_headers.tenant_id)

            # Ingest document
            # ingest_document_async takes: title, content, source, metadata
            # content is required, provide default if None
            document_id = await rag_system.ingest_document_async(
                title=request.title,
                content=request.content or "",
                source=request.source,
                metadata=request.metadata,
            )

            # Publish event via NATS
            if self.nats_client:
                await self._publish_ingest_event(document_id, standard_headers.tenant_id)

            return ServiceResponse(
                success=True,
                data={"document_id": document_id, "title": request.title},
                message="Document ingested successfully",
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )
        except Exception as e:
            logger.error(f"Error ingesting document: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to ingest document: {str(e)}",
            )
        finally:
            if span:
                span.end()

    async def _publish_ingest_event(self, document_id: str, tenant_id: str) -> None:
        """Publish document ingestion event via NATS."""
        event = {
            "event_type": "rag.document.ingested",
            "document_id": document_id,
            "tenant_id": tenant_id,
        }
        await self.nats_client.publish(
            f"rag.events.{tenant_id}",
            self.codec_manager.encode(event),
        )

    async def _handle_query(self, request: QueryRequest, headers: dict = Header(...)):
        """Process a RAG query."""
        standard_headers = extract_headers(**headers)

        span = None
        if self.otel_tracer:
            span = self.otel_tracer.start_span("rag_query")
            span.set_attribute("query.length", len(request.query))
            span.set_attribute("tenant.id", standard_headers.tenant_id)

        try:
            # Get RAG system (created on-demand, stateless)
            rag_system = self._get_rag_system(standard_headers.tenant_id)

            # Process query
            # quick_rag_query_async takes: rag_system, query, tenant_id, top_k, threshold, etc.
            # threshold has default 0.7, provide default if None
            result = await quick_rag_query_async(
                rag_system=rag_system,
                query=request.query,
                tenant_id=standard_headers.tenant_id,
                top_k=request.top_k,
                threshold=request.threshold or 0.7,
            )

            return ServiceResponse(
                success=True,
                data={
                    "answer": result.get("answer", ""),
                    "documents": result.get("documents", []),
                    "sources": result.get("sources", []),
                    "confidence": result.get("confidence"),
                },
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process query: {str(e)}",
            )
        finally:
            if span:
                span.end()

    async def _handle_search(self, request: SearchRequest, headers: dict = Header(...)):  # noqa: S7503
        """Perform vector search. Async required for FastAPI route handler."""
        standard_headers = extract_headers(**headers)

        try:
            # Get RAG system (created on-demand, stateless)
            rag_system = self._get_rag_system(standard_headers.tenant_id)

            # Perform search
            # retriever.retrieve() is synchronous and takes: query, tenant_id, top_k, threshold, filters
            if not request.query_text:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="query_text must be provided",
                )

            results = rag_system.retriever.retrieve(
                query=request.query_text,
                tenant_id=standard_headers.tenant_id,
                top_k=request.top_k,
                threshold=request.threshold or 0.7,
                filters=request.metadata_filters,
            )

            # results is a list of dicts, not a dict
            return ServiceResponse(
                success=True,
                data={
                    "documents": results,
                    "count": len(results),
                },
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error performing search: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to perform search: {str(e)}",
            )

    async def _handle_get_document(  # noqa: S7503
        self, document_id: str, headers: dict = Header(...)
    ):
        """Get document by ID. Async required for FastAPI route handler."""
        extract_headers(**headers)  # Extract headers for validation

        # Document retrieval from database - to be implemented
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Document retrieval not yet implemented",
        )

    async def _handle_update_document(  # noqa: S7503
        self, document_id: str, request: UpdateDocumentRequest, headers: dict = Header(...)
    ):
        """Update a document. Async required for FastAPI route handler."""
        standard_headers = extract_headers(**headers)

        try:
            # Get RAG system (created on-demand, stateless)
            rag_system = self._get_rag_system(standard_headers.tenant_id)

            # Update document
            # update_document() is synchronous and takes: document_id, title, content, metadata
            rag_system.update_document(
                document_id=document_id,
                title=request.title,
                content=request.content,
                metadata=request.metadata,
            )

            return ServiceResponse(
                success=True,
                data={"document_id": document_id},
                message="Document updated successfully",
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )
        except Exception as e:
            logger.error(f"Error updating document: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update document: {str(e)}",
            )

    async def _handle_delete_document(  # noqa: S7503
        self, document_id: str, headers: dict = Header(...)
    ):
        """Delete a document. Async required for FastAPI route handler."""
        standard_headers = extract_headers(**headers)

        try:
            # Get RAG system (created on-demand, stateless)
            rag_system = self._get_rag_system(standard_headers.tenant_id)

            # Delete document
            # delete_document() is synchronous and takes: document_id
            rag_system.delete_document(document_id=document_id)

            return None
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete document: {str(e)}",
            )

    async def _handle_list_documents(  # noqa: S7503
        self, headers: dict = Header(...), limit: int = 100, offset: int = 0
    ):
        """List documents. Async required for FastAPI route handler."""
        standard_headers = extract_headers(**headers)

        # Document listing from database - to be implemented
        # For now, return placeholder response
        return ServiceResponse(
            success=True,
            data={"documents": [], "total": 0},
            correlation_id=standard_headers.correlation_id,
            request_id=standard_headers.request_id,
        )

    async def _handle_health_check(self):  # noqa: S7503
        """Health check endpoint. Async required for FastAPI route handler."""
        return {"status": "healthy", "service": "rag-service"}


def create_rag_service(
    service_name: str = "rag-service",
    config_overrides: Optional[Dict[str, Any]] = None,
) -> RAGService:
    """
    Create RAG Service instance.

    Args:
        service_name: Service name
        config_overrides: Configuration overrides

    Returns:
        RAGService instance
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
    service = RAGService(
        config=config,
        db_connection=db_connection,
        nats_client=nats_client,
        otel_tracer=otel_tracer,
    )

    logger.info(f"RAG Service created: {service_name}")
    return service
