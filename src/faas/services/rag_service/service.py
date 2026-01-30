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
from ...shared.exceptions import DependencyError, NotFoundError
from ...shared.middleware import setup_middleware
from .models import (
    DocumentResponse,
    IngestDocumentRequest,
    QueryRequest,
    QueryResponse,
    SearchRequest,
    SearchResponse,
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

    async def _get_rag_system(self, tenant_id: str) -> RAGSystem:
        """
        Create RAG system for tenant (stateless - created on-demand).

        Args:
            tenant_id: Tenant ID

        Returns:
            RAGSystem instance
        """
        # Create RAG system on-demand (stateless)
        # Get gateway client
        gateway = await self._get_gateway_client(tenant_id)

        # Create RAG system
        rag_system = create_rag_system(
            db=self.db,
            gateway=gateway,
            embedding_model="text-embedding-3-small",
            generation_model="gpt-4",
        )

        return rag_system

    async def _get_gateway_client(self, tenant_id: str):
        """
        Get gateway client for LLM calls.

        Args:
            tenant_id: Tenant ID

        Returns:
            Gateway client instance
        """
        if self.config.gateway_service_url:
            # Use Gateway Service
            # For now, create direct gateway (in production, call Gateway Service)
            gateway = create_gateway(api_key="placeholder", provider="openai")
            return gateway
        else:
            # Create direct gateway
            gateway = create_gateway(api_key="placeholder", provider="openai")
            return gateway

    def _register_routes(self):
        """Register FastAPI routes."""

        @self.app.post(
            "/api/v1/rag/documents",
            response_model=ServiceResponse,
            status_code=status.HTTP_201_CREATED,
        )
        async def ingest_document(
            request: IngestDocumentRequest,
            headers: dict = Header(...),
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
                rag_system = await self._get_rag_system(standard_headers.tenant_id)

                # Ingest document
                document_id = await rag_system.ingest_document_async(
                    title=request.title,
                    content=request.content,
                    file_path=request.file_path,
                    tenant_id=standard_headers.tenant_id,
                    source=request.source,
                    metadata=request.metadata,
                )

                # Publish event via NATS
                if self.nats_client:
                    event = {
                        "event_type": "rag.document.ingested",
                        "document_id": document_id,
                        "tenant_id": standard_headers.tenant_id,
                    }
                    await self.nats_client.publish(
                        f"rag.events.{standard_headers.tenant_id}",
                        self.codec_manager.encode(event),
                    )

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

        @self.app.post("/api/v1/rag/query", response_model=ServiceResponse)
        async def query(
            request: QueryRequest,
            headers: dict = Header(...),
        ):
            """Process a RAG query."""
            standard_headers = extract_headers(**headers)

            span = None
            if self.otel_tracer:
                span = self.otel_tracer.start_span("rag_query")
                span.set_attribute("query.length", len(request.query))
                span.set_attribute("tenant.id", standard_headers.tenant_id)

            try:
                # Get RAG system (created on-demand, stateless)
                rag_system = await self._get_rag_system(standard_headers.tenant_id)

                # Process query
                result = await quick_rag_query_async(
                    rag_system=rag_system,
                    query=request.query,
                    top_k=request.top_k,
                    threshold=request.threshold,
                    metadata_filters=request.metadata_filters,
                    tenant_id=standard_headers.tenant_id,
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

        @self.app.post("/api/v1/rag/search", response_model=ServiceResponse)
        async def search(
            request: SearchRequest,
            headers: dict = Header(...),
        ):
            """Perform vector search."""
            standard_headers = extract_headers(**headers)

            try:
                # Get RAG system (created on-demand, stateless)
                rag_system = await self._get_rag_system(standard_headers.tenant_id)

                # Perform search
                if request.query_embedding:
                    # Use provided embedding
                    results = await rag_system.retriever.retrieve_async(
                        query_embedding=request.query_embedding,
                        top_k=request.top_k,
                        threshold=request.threshold,
                        metadata_filters=request.metadata_filters,
                        tenant_id=standard_headers.tenant_id,
                    )
                elif request.query_text:
                    # Generate embedding from text
                    results = await rag_system.retriever.retrieve_async(
                        query_text=request.query_text,
                        top_k=request.top_k,
                        threshold=request.threshold,
                        metadata_filters=request.metadata_filters,
                        tenant_id=standard_headers.tenant_id,
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Either query_embedding or query_text must be provided",
                    )

                return ServiceResponse(
                    success=True,
                    data={
                        "documents": results.get("documents", []),
                        "scores": results.get("scores", []),
                        "count": len(results.get("documents", [])),
                    },
                    correlation_id=standard_headers.correlation_id,
                    request_id=standard_headers.request_id,
                )
            except Exception as e:
                logger.error(f"Error performing search: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to perform search: {str(e)}",
                )

        @self.app.get("/api/v1/rag/documents/{document_id}", response_model=ServiceResponse)
        async def get_document(
            document_id: str,
            headers: dict = Header(...),
        ):
            """Get document by ID."""
            standard_headers = extract_headers(**headers)

            # TODO: SDK-SVC-004 - Implement document retrieval from database
            # Placeholder - replace with actual database query implementation
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Document retrieval not yet implemented",
            )

        @self.app.put("/api/v1/rag/documents/{document_id}", response_model=ServiceResponse)
        async def update_document(
            document_id: str,
            request: UpdateDocumentRequest,
            headers: dict = Header(...),
        ):
            """Update a document."""
            standard_headers = extract_headers(**headers)

            try:
                # Get RAG system (created on-demand, stateless)
                rag_system = await self._get_rag_system(standard_headers.tenant_id)

                # Update document
                await rag_system.update_document_async(
                    document_id=document_id,
                    title=request.title,
                    content=request.content,
                    metadata=request.metadata,
                    reprocess=request.reprocess,
                    tenant_id=standard_headers.tenant_id,
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

        @self.app.delete(
            "/api/v1/rag/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT
        )
        async def delete_document(
            document_id: str,
            headers: dict = Header(...),
        ):
            """Delete a document."""
            standard_headers = extract_headers(**headers)

            try:
                # Get RAG system (created on-demand, stateless)
                rag_system = await self._get_rag_system(standard_headers.tenant_id)

                # Delete document
                await rag_system.delete_document_async(
                    document_id=document_id,
                    tenant_id=standard_headers.tenant_id,
                )

                return None
            except Exception as e:
                logger.error(f"Error deleting document: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to delete document: {str(e)}",
                )

        @self.app.get("/api/v1/rag/documents", response_model=ServiceResponse)
        async def list_documents(
            headers: dict = Header(...),
            limit: int = 100,
            offset: int = 0,
        ):
            """List documents."""
            standard_headers = extract_headers(**headers)

            # TODO: SDK-SVC-004 - Implement document listing from database
            # Placeholder - replace with actual database query implementation
            return ServiceResponse(
                success=True,
                data={"documents": [], "total": 0},
                correlation_id=standard_headers.correlation_id,
                request_id=standard_headers.request_id,
            )

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
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
    otel_tracer = create_otel_tracer(config.service_name) if config.enable_otel else None

    # Create service
    service = RAGService(
        config=config,
        db_connection=db_connection,
        nats_client=nats_client,
        otel_tracer=otel_tracer,
    )

    logger.info(f"RAG Service created: {service_name}")
    return service
