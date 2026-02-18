"""
LLMOps Service - Main service implementation.

Handles LLM operations logging, monitoring, metrics, and cost tracking.
"""


import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException, Query, status

from ....core.llmops import LLMOperationStatus, LLMOperationType, LLMOps
from ...integrations.codec import create_codec_manager
from ...integrations.nats import create_nats_client
from ...integrations.otel import create_otel_tracer
from ...shared.config import ServiceConfig, load_config
from ...shared.contracts import ServiceResponse, extract_headers
from ...shared.database import get_database_connection
from ...shared.middleware import setup_middleware
from .models import LogOperationRequest

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

        # Register startup event to initialize LLMOps
        @self.app.on_event("startup")
        async def startup_event():
            """Initialize LLMOps on service startup."""
            await self.llmops.initialize()

        # Register routes
        self._register_routes()

    async def _handle_log_operation(
        self, request: LogOperationRequest, standard_headers: Any
    ) -> ServiceResponse:
        """
        Handle log operation business logic asynchronously.
        
        Args:
            request (LogOperationRequest): Request payload object.
            standard_headers (Any): Input parameter for this operation.
        
        Returns:
            ServiceResponse: Result of the operation.
        """
        operation_id = await self.llmops.log_operation(
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
        """
        Calculate cutoff date for filtering operations.
        
        Args:
            start_date (Optional[datetime]): Input parameter for this operation.
            end_date (Optional[datetime]): Input parameter for this operation.
        
        Returns:
            datetime: Result of the operation.
        """
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
        """
        Filter operations based on criteria.
        
        Args:
            all_operations (List[Any]): Input parameter for this operation.
            cutoff (datetime): Input parameter for this operation.
            filter_tenant_id (Optional[str]): Input parameter for this operation.
            agent_id (Optional[str]): Input parameter for this operation.
            model (Optional[str]): Model name or identifier to use.
            operation_type (Optional[str]): Input parameter for this operation.
            status_filter (Optional[str]): Input parameter for this operation.
            end_date (Optional[datetime]): Input parameter for this operation.
        
        Returns:
            List[Any]: List result of the operation.
        """
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
        """
        Format operations list for response.
        
        Args:
            operations (List[Any]): Input parameter for this operation.
        
        Returns:
            List[Dict[str, Any]]: Dictionary result of the operation.
        """
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
        """
        Handle query operations business logic.
        
        Args:
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
            agent_id (Optional[str]): Input parameter for this operation.
            model (Optional[str]): Model name or identifier to use.
            operation_type (Optional[str]): Input parameter for this operation.
            status_filter (Optional[str]): Input parameter for this operation.
            start_date (Optional[datetime]): Input parameter for this operation.
            end_date (Optional[datetime]): Input parameter for this operation.
            limit (int): Input parameter for this operation.
            offset (int): Input parameter for this operation.
            standard_headers (Any): Input parameter for this operation.
        
        Returns:
            ServiceResponse: Result of the operation.
        """
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
        """
        Calculate time range in hours.
        
        Args:
            start_date (Optional[datetime]): Input parameter for this operation.
            end_date (Optional[datetime]): Input parameter for this operation.
        
        Returns:
            int: Result of the operation.
        """
        if start_date and end_date:
            return int((end_date - start_date).total_seconds() / 3600)
        elif start_date:
            return int((datetime.now() - start_date).total_seconds() / 3600)
        else:
            return 24

    def _format_metrics_response(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format metrics for response.
        
        Args:
            metrics (Dict[str, Any]): Input parameter for this operation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
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
        """
        Format cost analysis for response.
        
        Args:
            cost_summary (Dict[str, Any]): Input parameter for this operation.
            metrics (Dict[str, Any]): Input parameter for this operation.
            filter_tenant_id (Optional[str]): Input parameter for this operation.
            start_date (Optional[datetime]): Input parameter for this operation.
            end_date (Optional[datetime]): Input parameter for this operation.
            time_range_hours (int): Input parameter for this operation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        return {
            "total_cost_usd": cost_summary.get("total_cost_usd", 0.0),
            "cost_by_model": {
                k: v.get("cost_usd", 0.0) for k, v in cost_summary.get("by_model", {}).items()
            },
            "cost_by_operation_type": dict.fromkeys(metrics.get("by_type", {}).keys(), 0.0),
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
        self.app.post(
            "/api/v1/llmops/operations",
            response_model=ServiceResponse,
            status_code=status.HTTP_201_CREATED,
        )(self._handle_log_operation_route)

        self.app.get("/api/v1/llmops/operations", response_model=ServiceResponse)(
            self._handle_query_operations_route
        )

        self.app.get("/api/v1/llmops/metrics", response_model=ServiceResponse)(
            self._handle_get_metrics_route
        )

        self.app.get("/api/v1/llmops/cost-analysis", response_model=ServiceResponse)(
            self._handle_get_cost_analysis_route
        )

        self.app.get("/health")(self._handle_health_check)

    async def _handle_log_operation_route(  # noqa: S7503
        self, request: LogOperationRequest, headers: dict = Header(...)
    ):
        """
        Log an LLM operation. Async required for FastAPI route handler.
        
        Args:
            request (LogOperationRequest): Request payload object.
            headers (dict): HTTP headers passed from the caller.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            HTTPException: Raised when this function detects an invalid state or when an underlying call fails.
        """
        standard_headers = extract_headers(**headers)
        try:
            return await self._handle_log_operation(request, standard_headers)
        except Exception as e:
            logger.error(f"Error logging operation: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to log operation: {str(e)}",
            )

    async def _handle_query_operations_route(  # noqa: S7503
        self,
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
        """
        Query LLM operations. Async required for FastAPI route handler.
        
        Args:
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
            agent_id (Optional[str]): Input parameter for this operation.
            model (Optional[str]): Model name or identifier to use.
            operation_type (Optional[str]): Input parameter for this operation.
            status_filter (Optional[str]): Input parameter for this operation.
            start_date (Optional[datetime]): Input parameter for this operation.
            end_date (Optional[datetime]): Input parameter for this operation.
            limit (int): Input parameter for this operation.
            offset (int): Input parameter for this operation.
            headers (dict): HTTP headers passed from the caller.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            HTTPException: Raised when this function detects an invalid state or when an underlying call fails.
        """
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

    async def _handle_get_metrics_route(  # noqa: S7503
        self,
        tenant_id: Optional[str] = Query(None, alias="tenant_id"),
        start_date: Optional[datetime] = Query(None, alias="start_date"),
        end_date: Optional[datetime] = Query(None, alias="end_date"),
        headers: dict = Header(...),
    ):
        """
        Get LLM operations metrics. Async required for FastAPI route handler.
        
        Args:
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
            start_date (Optional[datetime]): Input parameter for this operation.
            end_date (Optional[datetime]): Input parameter for this operation.
            headers (dict): HTTP headers passed from the caller.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            HTTPException: Raised when this function detects an invalid state or when an underlying call fails.
        """
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

    async def _handle_get_cost_analysis_route(  # noqa: S7503
        self,
        tenant_id: Optional[str] = Query(None, alias="tenant_id"),
        start_date: Optional[datetime] = Query(None, alias="start_date"),
        end_date: Optional[datetime] = Query(None, alias="end_date"),
        headers: dict = Header(...),
    ):
        """
        Get cost analysis. Async required for FastAPI route handler.
        
        Args:
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
            start_date (Optional[datetime]): Input parameter for this operation.
            end_date (Optional[datetime]): Input parameter for this operation.
            headers (dict): HTTP headers passed from the caller.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            HTTPException: Raised when this function detects an invalid state or when an underlying call fails.
        """
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

    async def _handle_health_check(self):  # noqa: S7503
        """
        Health check endpoint. Async required for FastAPI route handler.
        
        Returns:
            Any: Result of the operation.
        """
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
    config = load_config(service_name, **(config_overrides or {}))
    db_connection = get_database_connection(config.database_url)

    # Initialize integrations
    nats_client = create_nats_client() if config.enable_nats else None
    otel_tracer = create_otel_tracer() if config.enable_otel else None

    # Create service
    service = LLMOpsService(
        config=config,
        db_connection=db_connection,
        nats_client=nats_client,
        otel_tracer=otel_tracer,
    )

    return service.app
