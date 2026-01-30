"""
LLMOps Service - Main service implementation.

Handles LLM operations logging, monitoring, metrics, and cost tracking.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException, Query, status

from ....core.llmops import LLMOperation, LLMOperationStatus, LLMOperationType, LLMOps
from ...integrations.codec import create_codec_manager
from ...integrations.nats import create_nats_client
from ...integrations.otel import create_otel_tracer
from ...shared.config import ServiceConfig, load_config
from ...shared.contracts import ServiceResponse, extract_headers
from ...shared.database import get_database_connection
from ...shared.middleware import setup_middleware
from .models import (
    CostAnalysisResponse,
    LogOperationRequest,
    MetricsResponse,
    OperationResponse,
    OperationStatus,
    OperationType,
    QueryOperationsRequest,
)

logger = logging.getLogger(__name__)


class LLMOpsService:
    """
    LLMOps Service for LLM operations monitoring and analytics.

    Provides REST API for:
    - Logging LLM operations
    - Querying operation history
    - Retrieving metrics and analytics
    - Cost analysis and tracking
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
        Initialize LLMOps Service.

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

        # Initialize LLMOps
        self.llmops = LLMOps()

        # Create FastAPI app
        self.app = FastAPI(
            title="LLMOps Service",
            description="FaaS service for LLM operations monitoring and analytics",
            version=config.service_version,
        )

        # Setup middleware
        setup_middleware(self.app)

        # Register routes
        self._register_routes()

    def _handle_log_operation(
        self, request: LogOperationRequest, standard_headers: Any
    ) -> ServiceResponse:
        """Handle log operation business logic."""
        operation_id = self.llmops.log_operation(
            operation_type=LLMOperationType(request.operation_type.value),
            model=request.model,
            prompt_tokens=request.prompt_tokens,
            completion_tokens=request.completion_tokens,
            latency_ms=request.latency_ms,
            status=LLMOperationStatus(request.status.value),
            error_message=request.error_message,
            tenant_id=standard_headers.tenant_id,
            agent_id=request.agent_id,
            metadata=request.metadata,
        )
        return ServiceResponse(
            success=True,
            data={"operation_id": operation_id},
            message="Operation logged successfully",
            correlation_id=standard_headers.correlation_id,
            request_id=standard_headers.request_id,
        )

    def _calculate_cutoff_date(
        self, start_date: Optional[datetime], end_date: Optional[datetime]
    ) -> datetime:
        """Calculate cutoff date for filtering operations."""
        from datetime import timedelta

        if start_date:
            return start_date
        elif end_date:
            return end_date - timedelta(hours=24)
        else:
            return datetime.now() - timedelta(hours=24)

    def _filter_operations(
        self,
        all_operations: List[Any],
        cutoff: datetime,
        filter_tenant_id: Optional[str],
        agent_id: Optional[str],
        model: Optional[str],
        operation_type: Optional[str],
        status_filter: Optional[str],
        end_date: Optional[datetime],
    ) -> List[Any]:
        """Filter operations based on criteria."""
        return [
            op
            for op in all_operations
            if op.timestamp >= cutoff
            and (not filter_tenant_id or op.tenant_id == filter_tenant_id)
            and (not agent_id or op.agent_id == agent_id)
            and (not model or op.model == model)
            and (not operation_type or op.operation_type.value == operation_type)
            and (not status_filter or op.status.value == status_filter)
            and (not end_date or op.timestamp <= end_date)
        ]

    def _format_operation_list(self, operations: List[Any]) -> List[Dict[str, Any]]:
        """Format operations list for response."""
        return [
            {
                "operation_id": op.operation_id,
                "operation_type": op.operation_type.value,
                "model": op.model,
                "tenant_id": op.tenant_id,
                "agent_id": op.agent_id,
                "prompt_tokens": op.prompt_tokens,
                "completion_tokens": op.completion_tokens,
                "total_tokens": op.total_tokens,
                "latency_ms": op.latency_ms,
                "cost_usd": op.cost_usd,
                "status": op.status.value,
                "error_message": op.error_message,
                "timestamp": op.timestamp.isoformat(),
            }
            for op in operations
        ]

    def _handle_query_operations(
        self,
        tenant_id: Optional[str],
        agent_id: Optional[str],
        model: Optional[str],
        operation_type: Optional[str],
        status_filter: Optional[str],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        limit: int,
        offset: int,
        standard_headers: Any,
    ) -> ServiceResponse:
        """Handle query operations business logic."""
        filter_tenant_id = tenant_id or standard_headers.tenant_id
        cutoff = self._calculate_cutoff_date(start_date, end_date)

        all_operations = self.llmops.operations
        filtered = self._filter_operations(
            all_operations=all_operations,
            cutoff=cutoff,
            filter_tenant_id=filter_tenant_id,
            agent_id=agent_id,
            model=model,
            operation_type=operation_type,
            status_filter=status_filter,
            end_date=end_date,
        )

        paginated = filtered[offset : offset + limit]
        operation_list = self._format_operation_list(paginated)

        return ServiceResponse(
            success=True,
            data={"operations": operation_list, "count": len(operation_list)},
            correlation_id=standard_headers.correlation_id,
            request_id=standard_headers.request_id,
        )

    def _calculate_time_range(
        self, start_date: Optional[datetime], end_date: Optional[datetime]
    ) -> int:
        """Calculate time range in hours."""
        from datetime import timedelta

        if start_date and end_date:
            return int((end_date - start_date).total_seconds() / 3600)
        elif start_date:
            return int((datetime.now() - start_date).total_seconds() / 3600)
        else:
            return 24

    def _format_metrics_response(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Format metrics for response."""
        return {
            "total_operations": metrics.get("total_operations", 0),
            "total_tokens": metrics.get("total_tokens", 0),
            "total_cost_usd": metrics.get("total_cost_usd", 0.0),
            "average_latency_ms": metrics.get("average_latency_ms", 0.0),
            "success_rate": metrics.get("success_rate", 0.0),
            "operations_by_type": {
                k: v.get("count", 0) for k, v in metrics.get("by_type", {}).items()
            },
            "operations_by_model": {
                k: v.get("count", 0) for k, v in metrics.get("by_model", {}).items()
            },
            "cost_by_model": {
                k: v.get("cost_usd", 0.0) for k, v in metrics.get("by_model", {}).items()
            },
            "tokens_by_model": {
                k: v.get("tokens", 0) for k, v in metrics.get("by_model", {}).items()
            },
        }

    def _format_cost_analysis(
        self,
        cost_summary: Dict[str, Any],
        metrics: Dict[str, Any],
        filter_tenant_id: Optional[str],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        time_range_hours: int,
    ) -> Dict[str, Any]:
        """Format cost analysis for response."""
        from datetime import timedelta

        return {
            "total_cost_usd": cost_summary.get("total_cost_usd", 0.0),
            "cost_by_model": {
                k: v.get("cost_usd", 0.0) for k, v in cost_summary.get("by_model", {}).items()
            },
            "cost_by_operation_type": {k: 0.0 for k in metrics.get("by_type", {}).keys()},
            "cost_by_tenant": (
                {filter_tenant_id: cost_summary.get("total_cost_usd", 0.0)}
                if filter_tenant_id
                else {}
            ),
            "cost_trend": [],  # Would need historical data
            "period_start": (
                start_date.isoformat()
                if start_date
                else (datetime.now() - timedelta(hours=time_range_hours)).isoformat()
            ),
            "period_end": end_date.isoformat() if end_date else datetime.now().isoformat(),
        }

    def _register_routes(self):
        """Register FastAPI routes."""

        @self.app.post(
            "/api/v1/llmops/operations",
            response_model=ServiceResponse,
            status_code=status.HTTP_201_CREATED,
        )
        async def log_operation(
            request: LogOperationRequest,
            headers: dict = Header(...),
        ):
            """Log an LLM operation."""
            standard_headers = extract_headers(**headers)
            try:
                return self._handle_log_operation(request, standard_headers)
            except Exception as e:
                logger.error(f"Error logging operation: {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to log operation: {str(e)}",
                )

        @self.app.get("/api/v1/llmops/operations", response_model=ServiceResponse)
        async def query_operations(
            tenant_id: Optional[str] = Query(None, alias="tenant_id"),
            agent_id: Optional[str] = Query(None, alias="agent_id"),
            model: Optional[str] = Query(None, alias="model"),
            operation_type: Optional[str] = Query(None, alias="operation_type"),
            status_filter: Optional[str] = Query(None, alias="status"),
            start_date: Optional[datetime] = Query(None, alias="start_date"),
            end_date: Optional[datetime] = Query(None, alias="end_date"),
            limit: int = Query(100, ge=1, le=1000),
            offset: int = Query(0, ge=0),
            headers: dict = Header(...),
        ):
            """Query LLM operations."""
            standard_headers = extract_headers(**headers)
            try:
                return self._handle_query_operations(
                    tenant_id=tenant_id,
                    agent_id=agent_id,
                    model=model,
                    operation_type=operation_type,
                    status_filter=status_filter,
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit,
                    offset=offset,
                    standard_headers=standard_headers,
                )
            except Exception as e:
                logger.error(f"Error querying operations: {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to query operations: {str(e)}",
                )

        @self.app.get("/api/v1/llmops/metrics", response_model=ServiceResponse)
        async def get_metrics(
            tenant_id: Optional[str] = Query(None, alias="tenant_id"),
            start_date: Optional[datetime] = Query(None, alias="start_date"),
            end_date: Optional[datetime] = Query(None, alias="end_date"),
            headers: dict = Header(...),
        ):
            """Get LLM operations metrics."""
            standard_headers = extract_headers(**headers)
            try:
                filter_tenant_id = tenant_id or standard_headers.tenant_id
                time_range_hours = self._calculate_time_range(start_date, end_date)
                metrics = self.llmops.get_metrics(
                    tenant_id=filter_tenant_id,
                    time_range_hours=time_range_hours,
                )
                formatted_metrics = self._format_metrics_response(metrics)
                return ServiceResponse(
                    success=True,
                    data=formatted_metrics,
                    correlation_id=standard_headers.correlation_id,
                    request_id=standard_headers.request_id,
                )
            except Exception as e:
                logger.error(f"Error getting metrics: {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to get metrics: {str(e)}",
                )

        @self.app.get("/api/v1/llmops/cost-analysis", response_model=ServiceResponse)
        async def get_cost_analysis(
            tenant_id: Optional[str] = Query(None, alias="tenant_id"),
            start_date: Optional[datetime] = Query(None, alias="start_date"),
            end_date: Optional[datetime] = Query(None, alias="end_date"),
            headers: dict = Header(...),
        ):
            """Get cost analysis."""
            standard_headers = extract_headers(**headers)
            try:
                filter_tenant_id = tenant_id or standard_headers.tenant_id
                time_range_hours = self._calculate_time_range(start_date, end_date)
                cost_summary = self.llmops.get_cost_summary(
                    tenant_id=filter_tenant_id,
                    time_range_hours=time_range_hours,
                )
                metrics = self.llmops.get_metrics(
                    tenant_id=filter_tenant_id,
                    time_range_hours=time_range_hours,
                )
                cost_analysis = self._format_cost_analysis(
                    cost_summary=cost_summary,
                    metrics=metrics,
                    filter_tenant_id=filter_tenant_id,
                    start_date=start_date,
                    end_date=end_date,
                    time_range_hours=time_range_hours,
                )
                return ServiceResponse(
                    success=True,
                    data=cost_analysis,
                    correlation_id=standard_headers.correlation_id,
                    request_id=standard_headers.request_id,
                )
            except Exception as e:
                logger.error(f"Error getting cost analysis: {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to get cost analysis: {str(e)}",
                )

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "service": "llmops-service"}


def create_llmops_service(
    service_name: str = "llmops-service",
    config_overrides: Optional[Dict[str, Any]] = None,
) -> FastAPI:
    """
    Create and configure LLMOps Service.

    Args:
        service_name: Service name
        config_overrides: Configuration overrides

    Returns:
        Configured FastAPI application
    """
    config = load_config(service_name, config_overrides)
    db_connection = get_database_connection(config.database_url)

    # Initialize integrations
    nats_client = create_nats_client(config.nats_url) if config.enable_nats else None
    otel_tracer = (
        create_otel_tracer(service_name, config.otel_exporter_otlp_endpoint)
        if config.enable_otel
        else None
    )

    # Create service
    service = LLMOpsService(
        config=config,
        db_connection=db_connection,
        nats_client=nats_client,
        otel_tracer=otel_tracer,
    )

    return service.app
