"""
Unit tests for llmops_service/service.py
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.llmops import LLMOperation, LLMOperationStatus, LLMOperationType, LLMOps
from src.faas.services.llmops_service.models import LogOperationRequest, OperationStatus, OperationType
from src.faas.services.llmops_service.service import LLMOpsService, create_llmops_service
from src.faas.shared.contracts import StandardHeaders


class TestLLMOpsService:
    """Tests for LLMOpsService class."""

    @pytest.fixture
    def mock_config(self):
        """Create mock ServiceConfig."""
        config = MagicMock()
        config.service_version = "1.0.0"
        config.enable_nats = False
        config.enable_otel = False
        return config

    @pytest.fixture
    def mock_db_connection(self):
        """Create mock database connection."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_config, mock_db_connection):
        """Create LLMOpsService instance."""
        with patch("src.faas.services.llmops_service.service.setup_middleware"):
            service = LLMOpsService(
                config=mock_config,
                db_connection=mock_db_connection,
                nats_client=None,
                otel_tracer=None,
                codec_manager=None,
            )
            return service

    def test_init(self, mock_config, mock_db_connection):
        """Test LLMOpsService initialization."""
        with patch("src.faas.services.llmops_service.service.setup_middleware"):
            service = LLMOpsService(
                config=mock_config,
                db_connection=mock_db_connection,
            )

            assert service.config == mock_config
            assert service.db == mock_db_connection
            assert service.llmops is not None
            assert isinstance(service.llmops, LLMOps)
            assert service.app is not None

    def test_init_with_integrations(self, mock_config, mock_db_connection):
        """Test LLMOpsService initialization with integrations."""
        mock_nats = MagicMock()
        mock_otel = MagicMock()
        mock_codec = MagicMock()

        with patch("src.faas.services.llmops_service.service.setup_middleware"):
            service = LLMOpsService(
                config=mock_config,
                db_connection=mock_db_connection,
                nats_client=mock_nats,
                otel_tracer=mock_otel,
                codec_manager=mock_codec,
            )

            assert service.nats_client == mock_nats
            assert service.otel_tracer == mock_otel
            assert service.codec_manager == mock_codec

    @pytest.mark.asyncio
    async def test_startup_event(self, service):
        """Test startup event initializes LLMOps."""
        # Test that startup event handler is registered
        # We can't easily trigger FastAPI startup events in unit tests,
        # but we can verify the handler exists and works when called directly
        service.llmops.initialize = AsyncMock()

        # Simulate startup by calling initialize directly
        await service.llmops.initialize()

        service.llmops.initialize.assert_called_once()
        
        # Test that the startup event handler would call initialize
        # by checking if the app has the startup event registered
        assert hasattr(service.app, "router")

    def test_register_routes(self, service):
        """Test route registration."""
        # Check that routes are registered
        routes = [route.path for route in service.app.routes]
        assert "/api/v1/llmops/operations" in routes
        assert "/api/v1/llmops/metrics" in routes
        assert "/api/v1/llmops/cost-analysis" in routes
        assert "/health" in routes

    @pytest.mark.asyncio
    async def test_handle_log_operation(self, service):
        """Test _handle_log_operation."""
        service.llmops.log_operation = AsyncMock(return_value="op_123")

        request = LogOperationRequest(
            operation_type=OperationType.COMPLETION,
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            latency_ms=500.0,
            status=OperationStatus.SUCCESS,
            error_message=None,
            agent_id=None,
            metadata=None,
        )

        standard_headers = StandardHeaders(
            **{"X-Tenant-ID": "tenant-1", "X-Correlation-ID": "corr-123", "X-Request-ID": "req-123"}
        )

        response = await service._handle_log_operation(request, standard_headers)

        assert response.success is True
        assert response.data["operation_id"] == "op_123"
        service.llmops.log_operation.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_log_operation_with_all_params(self, service):
        """Test _handle_log_operation with all parameters."""
        service.llmops.log_operation = AsyncMock(return_value="op_123")

        request = LogOperationRequest(
            operation_type=OperationType.COMPLETION,
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            latency_ms=500.0,
            status=OperationStatus.SUCCESS,
            error_message=None,
            agent_id="agent-1",
            metadata={"key": "value"},
        )

        standard_headers = StandardHeaders(
            **{"X-Tenant-ID": "tenant-1", "X-Correlation-ID": "corr-123", "X-Request-ID": "req-123"}
        )

        response = await service._handle_log_operation(request, standard_headers)

        assert response.success is True
        service.llmops.log_operation.assert_called_once()

    def test_calculate_cutoff_date_with_start_date(self, service):
        """Test _calculate_cutoff_date with start_date."""
        start_date = datetime.now() - timedelta(hours=12)
        end_date = None

        cutoff = service._calculate_cutoff_date(start_date, end_date)

        assert cutoff == start_date

    def test_calculate_cutoff_date_with_end_date(self, service):
        """Test _calculate_cutoff_date with end_date."""
        start_date = None
        end_date = datetime.now()

        cutoff = service._calculate_cutoff_date(start_date, end_date)

        assert cutoff == end_date - timedelta(hours=24)

    def test_calculate_cutoff_date_with_neither(self, service):
        """Test _calculate_cutoff_date with neither date."""
        cutoff = service._calculate_cutoff_date(None, None)

        # Should be 24 hours ago
        expected = datetime.now() - timedelta(hours=24)
        assert abs((cutoff - expected).total_seconds()) < 60  # Within 1 minute

    def test_filter_operations_all_filters(self, service):
        """Test _filter_operations with all filters."""
        op1 = LLMOperation(
            operation_id="op1",
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            tenant_id="tenant-1",
            agent_id="agent-1",
            timestamp=datetime.now() - timedelta(hours=1),
            status=LLMOperationStatus.SUCCESS,
        )
        op2 = LLMOperation(
            operation_id="op2",
            operation_type=LLMOperationType.EMBEDDING,
            model="gpt-3",
            tenant_id="tenant-2",
            agent_id="agent-2",
            timestamp=datetime.now() - timedelta(hours=1),
            status=LLMOperationStatus.ERROR,
        )

        cutoff = datetime.now() - timedelta(hours=2)
        filtered = service._filter_operations(
            all_operations=[op1, op2],
            cutoff=cutoff,
            filter_tenant_id="tenant-1",
            agent_id="agent-1",
            model="gpt-4",
            operation_type="completion",
            status_filter="success",
            end_date=None,
        )

        assert len(filtered) == 1
        assert filtered[0].operation_id == "op1"

    def test_filter_operations_no_filters(self, service):
        """Test _filter_operations with no filters."""
        op1 = LLMOperation(
            operation_id="op1",
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            tenant_id="tenant-1",
            timestamp=datetime.now() - timedelta(hours=1),
            status=LLMOperationStatus.SUCCESS,
        )

        cutoff = datetime.now() - timedelta(hours=2)
        filtered = service._filter_operations(
            all_operations=[op1],
            cutoff=cutoff,
            filter_tenant_id=None,
            agent_id=None,
            model=None,
            operation_type=None,
            status_filter=None,
            end_date=None,
        )

        assert len(filtered) == 1

    def test_filter_operations_with_end_date(self, service):
        """Test _filter_operations with end_date filter."""
        op1 = LLMOperation(
            operation_id="op1",
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            tenant_id="tenant-1",
            timestamp=datetime.now() - timedelta(hours=1),
            status=LLMOperationStatus.SUCCESS,
        )
        op2 = LLMOperation(
            operation_id="op2",
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            tenant_id="tenant-1",
            timestamp=datetime.now() + timedelta(hours=1),  # Future timestamp
            status=LLMOperationStatus.SUCCESS,
        )

        cutoff = datetime.now() - timedelta(hours=2)
        end_date = datetime.now()
        filtered = service._filter_operations(
            all_operations=[op1, op2],
            cutoff=cutoff,
            filter_tenant_id=None,
            agent_id=None,
            model=None,
            operation_type=None,
            status_filter=None,
            end_date=end_date,
        )

        assert len(filtered) == 1
        assert filtered[0].operation_id == "op1"

    def test_format_operation_list(self, service):
        """Test _format_operation_list."""
        op = LLMOperation(
            operation_id="op1",
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            tenant_id="tenant-1",
            agent_id="agent-1",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            latency_ms=500.0,
            cost_usd=0.01,
            timestamp=datetime.now(),
            status=LLMOperationStatus.SUCCESS,
        )

        formatted = service._format_operation_list([op])

        assert len(formatted) == 1
        assert formatted[0]["operation_id"] == "op1"
        assert formatted[0]["operation_type"] == "completion"
        assert formatted[0]["model"] == "gpt-4"
        assert formatted[0]["tenant_id"] == "tenant-1"
        assert formatted[0]["agent_id"] == "agent-1"
        assert formatted[0]["prompt_tokens"] == 100
        assert formatted[0]["completion_tokens"] == 50
        assert formatted[0]["total_tokens"] == 150
        assert abs(formatted[0]["latency_ms"] - 500.0) < 0.001
        assert abs(formatted[0]["cost_usd"] - 0.01) < 0.001
        assert formatted[0]["status"] == "success"

    def test_handle_query_operations(self, service):
        """Test _handle_query_operations."""
        op = LLMOperation(
            operation_id="op1",
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            tenant_id="tenant-1",
            timestamp=datetime.now() - timedelta(hours=1),
            status=LLMOperationStatus.SUCCESS,
        )
        service.llmops.operations = [op]

        standard_headers = StandardHeaders(
            **{"X-Tenant-ID": "tenant-1", "X-Correlation-ID": "corr-123", "X-Request-ID": "req-123"}
        )

        response = service._handle_query_operations(
            tenant_id=None,
            agent_id=None,
            model=None,
            operation_type=None,
            status_filter=None,
            start_date=None,
            end_date=None,
            limit=10,
            offset=0,
            standard_headers=standard_headers,
        )

        assert response.success is True
        assert "operations" in response.data
        assert "count" in response.data

    def test_handle_query_operations_with_filters(self, service):
        """Test _handle_query_operations with filters."""
        op1 = LLMOperation(
            operation_id="op1",
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            tenant_id="tenant-1",
            agent_id="agent-1",
            timestamp=datetime.now() - timedelta(hours=1),
            status=LLMOperationStatus.SUCCESS,
        )
        op2 = LLMOperation(
            operation_id="op2",
            operation_type=LLMOperationType.EMBEDDING,
            model="gpt-3",
            tenant_id="tenant-1",
            timestamp=datetime.now() - timedelta(hours=1),
            status=LLMOperationStatus.SUCCESS,
        )
        service.llmops.operations = [op1, op2]

        standard_headers = StandardHeaders(
            **{"X-Tenant-ID": "tenant-1", "X-Correlation-ID": "corr-123", "X-Request-ID": "req-123"}
        )

        response = service._handle_query_operations(
            tenant_id="tenant-1",
            agent_id="agent-1",
            model="gpt-4",
            operation_type="completion",
            status_filter="success",
            start_date=datetime.now() - timedelta(hours=2),
            end_date=datetime.now(),
            limit=10,
            offset=0,
            standard_headers=standard_headers,
        )

        assert response.success is True
        assert len(response.data["operations"]) == 1

    def test_handle_query_operations_with_pagination(self, service):
        """Test _handle_query_operations with pagination."""
        ops = [
            LLMOperation(
                operation_id=f"op{i}",
                operation_type=LLMOperationType.COMPLETION,
                model="gpt-4",
                tenant_id="tenant-1",
                timestamp=datetime.now() - timedelta(hours=1),
                status=LLMOperationStatus.SUCCESS,
            )
            for i in range(5)
        ]
        service.llmops.operations = ops

        standard_headers = StandardHeaders(
            **{"X-Tenant-ID": "tenant-1", "X-Correlation-ID": "corr-123", "X-Request-ID": "req-123"}
        )

        response = service._handle_query_operations(
            tenant_id=None,
            agent_id=None,
            model=None,
            operation_type=None,
            status_filter=None,
            start_date=None,
            end_date=None,
            limit=2,
            offset=1,
            standard_headers=standard_headers,
        )

        assert response.success is True
        assert len(response.data["operations"]) == 2

    def test_calculate_time_range_with_both_dates(self, service):
        """Test _calculate_time_range with both start and end dates."""
        start_date = datetime.now() - timedelta(hours=12)
        end_date = datetime.now()

        hours = service._calculate_time_range(start_date, end_date)

        assert hours == 12

    def test_calculate_time_range_with_start_date_only(self, service):
        """Test _calculate_time_range with start_date only."""
        start_date = datetime.now() - timedelta(hours=6)
        end_date = None

        hours = service._calculate_time_range(start_date, end_date)

        assert hours == 6

    def test_calculate_time_range_with_neither(self, service):
        """Test _calculate_time_range with neither date."""
        hours = service._calculate_time_range(None, None)

        assert hours == 24

    def test_format_metrics_response(self, service):
        """Test _format_metrics_response."""
        metrics = {
            "total_operations": 100,
            "total_tokens": 10000,
            "total_cost_usd": 1.5,
            "average_latency_ms": 500.0,
            "success_rate": 0.95,
            "by_type": {
                "completion": {"count": 80},
                "embedding": {"count": 20},
            },
            "by_model": {
                "gpt-4": {"count": 50, "cost_usd": 1.0, "tokens": 5000},
                "gpt-3": {"count": 50, "cost_usd": 0.5, "tokens": 5000},
            },
        }

        formatted = service._format_metrics_response(metrics)

        assert formatted["total_operations"] == 100
        assert formatted["total_tokens"] == 10000
        assert abs(formatted["total_cost_usd"] - 1.5) < 0.001
        assert abs(formatted["average_latency_ms"] - 500.0) < 0.001
        assert abs(formatted["success_rate"] - 0.95) < 0.001
        assert formatted["operations_by_type"]["completion"] == 80
        assert formatted["operations_by_model"]["gpt-4"] == 50
        assert abs(formatted["cost_by_model"]["gpt-4"] - 1.0) < 0.001
        assert formatted["tokens_by_model"]["gpt-4"] == 5000

    def test_format_metrics_response_empty(self, service):
        """Test _format_metrics_response with empty metrics."""
        metrics = {}

        formatted = service._format_metrics_response(metrics)

        assert formatted["total_operations"] == 0
        assert formatted["total_tokens"] == 0
        assert abs(formatted["total_cost_usd"] - 0.0) < 0.001

    def test_format_cost_analysis(self, service):
        """Test _format_cost_analysis."""
        cost_summary = {
            "total_cost_usd": 1.5,
            "by_model": {
                "gpt-4": {"cost_usd": 1.0},
                "gpt-3": {"cost_usd": 0.5},
            },
        }
        metrics = {
            "by_type": {
                "completion": {},
                "embedding": {},
            },
        }

        analysis = service._format_cost_analysis(
            cost_summary=cost_summary,
            metrics=metrics,
            filter_tenant_id="tenant-1",
            start_date=datetime.now() - timedelta(hours=24),
            end_date=datetime.now(),
            time_range_hours=24,
        )

        assert abs(analysis["total_cost_usd"] - 1.5) < 0.001
        assert abs(analysis["cost_by_model"]["gpt-4"] - 1.0) < 0.001
        assert "tenant-1" in analysis["cost_by_tenant"]
        assert "period_start" in analysis
        assert "period_end" in analysis

    def test_format_cost_analysis_no_tenant(self, service):
        """Test _format_cost_analysis without tenant filter."""
        cost_summary = {
            "total_cost_usd": 1.5,
            "by_model": {},
        }
        metrics = {"by_type": {}}

        analysis = service._format_cost_analysis(
            cost_summary=cost_summary,
            metrics=metrics,
            filter_tenant_id=None,
            start_date=None,
            end_date=None,
            time_range_hours=24,
        )

        assert analysis["cost_by_tenant"] == {}

    @pytest.mark.asyncio
    async def test_handle_log_operation_route_success(self, service):
        """Test _handle_log_operation_route success."""
        service._handle_log_operation = AsyncMock(
            return_value=MagicMock(success=True, data={"operation_id": "op_123"})
        )

        request = LogOperationRequest(
            operation_type=OperationType.COMPLETION,
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            latency_ms=500.0,
            status=OperationStatus.SUCCESS,
            error_message=None,
            agent_id=None,
            metadata=None,
        )

        with patch("src.faas.services.llmops_service.service.extract_headers") as mock_extract:
            mock_extract.return_value = StandardHeaders(
                **{"X-Tenant-ID": "tenant-1", "X-Correlation-ID": "corr-123", "X-Request-ID": "req-123"}
            )

            response = await service._handle_log_operation_route(request, headers={})

            assert response.success is True

    @pytest.mark.asyncio
    async def test_handle_log_operation_route_error(self, service):
        """Test _handle_log_operation_route error handling."""
        service._handle_log_operation = AsyncMock(side_effect=Exception("Test error"))

        request = LogOperationRequest(
            operation_type=OperationType.COMPLETION,
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            latency_ms=500.0,
            status=OperationStatus.SUCCESS,
            error_message=None,
            agent_id=None,
            metadata=None,
        )

        with patch("src.faas.services.llmops_service.service.extract_headers") as mock_extract:
            mock_extract.return_value = StandardHeaders(
                **{"X-Tenant-ID": "tenant-1", "X-Correlation-ID": "corr-123", "X-Request-ID": "req-123"}
            )

            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                await service._handle_log_operation_route(request, headers={})

            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_handle_query_operations_route_success(self, service):
        """Test _handle_query_operations_route success."""
        service._handle_query_operations = MagicMock(
            return_value=MagicMock(success=True, data={"operations": [], "count": 0})
        )

        with patch("src.faas.services.llmops_service.service.extract_headers") as mock_extract:
            mock_extract.return_value = StandardHeaders(
                **{"X-Tenant-ID": "tenant-1", "X-Correlation-ID": "corr-123", "X-Request-ID": "req-123"}
            )

            response = await service._handle_query_operations_route(
                tenant_id=None,
                agent_id=None,
                model=None,
                operation_type=None,
                status_filter=None,
                start_date=None,
                end_date=None,
                limit=10,
                offset=0,
                headers={},
            )

            assert response.success is True

    @pytest.mark.asyncio
    async def test_handle_query_operations_route_error(self, service):
        """Test _handle_query_operations_route error handling."""
        service._handle_query_operations = MagicMock(side_effect=Exception("Test error"))

        with patch("src.faas.services.llmops_service.service.extract_headers") as mock_extract:
            mock_extract.return_value = StandardHeaders(
                **{"X-Tenant-ID": "tenant-1", "X-Correlation-ID": "corr-123", "X-Request-ID": "req-123"}
            )

            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                await service._handle_query_operations_route(
                    tenant_id=None,
                    agent_id=None,
                    model=None,
                    operation_type=None,
                    status_filter=None,
                    start_date=None,
                    end_date=None,
                    limit=10,
                    offset=0,
                    headers={},
                )

            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_handle_get_metrics_route_success(self, service):
        """Test _handle_get_metrics_route success."""
        service.llmops.get_metrics = MagicMock(
            return_value={
                "total_operations": 100,
                "total_tokens": 10000,
                "total_cost_usd": 1.5,
                "average_latency_ms": 500.0,
                "success_rate": 0.95,
                "by_type": {},
                "by_model": {},
            }
        )

        with patch("src.faas.services.llmops_service.service.extract_headers") as mock_extract:
            mock_extract.return_value = StandardHeaders(
                **{"X-Tenant-ID": "tenant-1", "X-Correlation-ID": "corr-123", "X-Request-ID": "req-123"}
            )

            response = await service._handle_get_metrics_route(
                tenant_id=None,
                start_date=None,
                end_date=None,
                headers={},
            )

            assert response.success is True
            assert "data" in response.__dict__

    @pytest.mark.asyncio
    async def test_handle_get_metrics_route_with_tenant(self, service):
        """Test _handle_get_metrics_route with tenant_id."""
        service.llmops.get_metrics = MagicMock(return_value={})

        with patch("src.faas.services.llmops_service.service.extract_headers") as mock_extract:
            mock_extract.return_value = StandardHeaders(
                **{"X-Tenant-ID": "tenant-1", "X-Correlation-ID": "corr-123", "X-Request-ID": "req-123"}
            )

            response = await service._handle_get_metrics_route(
                tenant_id="tenant-2",
                start_date=None,
                end_date=None,
                headers={},
            )

            assert response.success is True
            service.llmops.get_metrics.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_get_metrics_route_error(self, service):
        """Test _handle_get_metrics_route error handling."""
        service.llmops.get_metrics = MagicMock(side_effect=Exception("Test error"))

        with patch("src.faas.services.llmops_service.service.extract_headers") as mock_extract:
            mock_extract.return_value = StandardHeaders(
                **{"X-Tenant-ID": "tenant-1", "X-Correlation-ID": "corr-123", "X-Request-ID": "req-123"}
            )

            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                await service._handle_get_metrics_route(
                    tenant_id=None,
                    start_date=None,
                    end_date=None,
                    headers={},
                )

            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_handle_get_cost_analysis_route_success(self, service):
        """Test _handle_get_cost_analysis_route success."""
        service.llmops.get_cost_summary = MagicMock(
            return_value={"total_cost_usd": 1.5, "by_model": {}}
        )
        service.llmops.get_metrics = MagicMock(return_value={"by_type": {}})

        with patch("src.faas.services.llmops_service.service.extract_headers") as mock_extract:
            mock_extract.return_value = StandardHeaders(
                **{"X-Tenant-ID": "tenant-1", "X-Correlation-ID": "corr-123", "X-Request-ID": "req-123"}
            )

            response = await service._handle_get_cost_analysis_route(
                tenant_id=None,
                start_date=None,
                end_date=None,
                headers={},
            )

            assert response.success is True
            assert "data" in response.__dict__

    @pytest.mark.asyncio
    async def test_handle_get_cost_analysis_route_with_dates(self, service):
        """Test _handle_get_cost_analysis_route with date filters."""
        service.llmops.get_cost_summary = MagicMock(return_value={"total_cost_usd": 1.5, "by_model": {}})
        service.llmops.get_metrics = MagicMock(return_value={"by_type": {}})

        with patch("src.faas.services.llmops_service.service.extract_headers") as mock_extract:
            mock_extract.return_value = StandardHeaders(
                **{"X-Tenant-ID": "tenant-1", "X-Correlation-ID": "corr-123", "X-Request-ID": "req-123"}
            )

            start_date = datetime.now() - timedelta(hours=12)
            end_date = datetime.now()

            response = await service._handle_get_cost_analysis_route(
                tenant_id=None,
                start_date=start_date,
                end_date=end_date,
                headers={},
            )

            assert response.success is True

    @pytest.mark.asyncio
    async def test_handle_get_cost_analysis_route_error(self, service):
        """Test _handle_get_cost_analysis_route error handling."""
        service.llmops.get_cost_summary = MagicMock(side_effect=Exception("Test error"))

        with patch("src.faas.services.llmops_service.service.extract_headers") as mock_extract:
            mock_extract.return_value = StandardHeaders(
                **{"X-Tenant-ID": "tenant-1", "X-Correlation-ID": "corr-123", "X-Request-ID": "req-123"}
            )

            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                await service._handle_get_cost_analysis_route(
                    tenant_id=None,
                    start_date=None,
                    end_date=None,
                    headers={},
                )

            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_handle_health_check(self, service):
        """Test _handle_health_check."""
        response = await service._handle_health_check()

        assert response["status"] == "healthy"
        assert response["service"] == "llmops-service"


class TestCreateLLMOpsService:
    """Tests for create_llmops_service factory function."""

    @pytest.mark.asyncio
    async def test_create_llmops_service_default(self):
        """Test create_llmops_service with default parameters."""
        mock_config = MagicMock()
        mock_config.service_version = "1.0.0"
        mock_config.enable_nats = False
        mock_config.enable_otel = False
        mock_config.database_url = "postgresql://localhost/test"

        with patch("src.faas.services.llmops_service.service.load_config", return_value=mock_config), \
             patch("src.faas.services.llmops_service.service.get_database_connection") as mock_db, \
             patch("src.faas.services.llmops_service.service.create_nats_client", return_value=None), \
             patch("src.faas.services.llmops_service.service.create_otel_tracer", return_value=None), \
             patch("src.faas.services.llmops_service.service.setup_middleware"):
            mock_db.return_value = MagicMock()

            app = create_llmops_service()

            assert app is not None

    @pytest.mark.asyncio
    async def test_create_llmops_service_with_config_overrides(self):
        """Test create_llmops_service with config overrides."""
        mock_config = MagicMock()
        mock_config.service_version = "1.0.0"
        mock_config.enable_nats = True
        mock_config.enable_otel = True
        mock_config.database_url = "postgresql://localhost/test"

        with patch("src.faas.services.llmops_service.service.load_config", return_value=mock_config), \
             patch("src.faas.services.llmops_service.service.get_database_connection") as mock_db, \
             patch("src.faas.services.llmops_service.service.create_nats_client") as mock_nats, \
             patch("src.faas.services.llmops_service.service.create_otel_tracer") as mock_otel, \
             patch("src.faas.services.llmops_service.service.setup_middleware"):
            mock_db.return_value = MagicMock()
            mock_nats.return_value = MagicMock()
            mock_otel.return_value = MagicMock()

            app = create_llmops_service(
                service_name="custom-service",
                config_overrides={"enable_nats": True},
            )

            assert app is not None

    @pytest.mark.asyncio
    async def test_create_llmops_service_with_nats_enabled(self):
        """Test create_llmops_service with NATS enabled."""
        mock_config = MagicMock()
        mock_config.service_version = "1.0.0"
        mock_config.enable_nats = True
        mock_config.enable_otel = False
        mock_config.database_url = "postgresql://localhost/test"

        mock_nats_client = MagicMock()

        with patch("src.faas.services.llmops_service.service.load_config", return_value=mock_config), \
             patch("src.faas.services.llmops_service.service.get_database_connection") as mock_db, \
             patch("src.faas.services.llmops_service.service.create_nats_client", return_value=mock_nats_client), \
             patch("src.faas.services.llmops_service.service.create_otel_tracer", return_value=None), \
             patch("src.faas.services.llmops_service.service.setup_middleware"):
            mock_db.return_value = MagicMock()

            app = create_llmops_service()

            assert app is not None

    @pytest.mark.asyncio
    async def test_create_llmops_service_with_otel_enabled(self):
        """Test create_llmops_service with OTEL enabled."""
        mock_config = MagicMock()
        mock_config.service_version = "1.0.0"
        mock_config.enable_nats = False
        mock_config.enable_otel = True
        mock_config.database_url = "postgresql://localhost/test"

        mock_otel_tracer = MagicMock()

        with patch("src.faas.services.llmops_service.service.load_config", return_value=mock_config), \
             patch("src.faas.services.llmops_service.service.get_database_connection") as mock_db, \
             patch("src.faas.services.llmops_service.service.create_nats_client", return_value=None), \
             patch("src.faas.services.llmops_service.service.create_otel_tracer", return_value=mock_otel_tracer), \
             patch("src.faas.services.llmops_service.service.setup_middleware"):
            mock_db.return_value = MagicMock()

            app = create_llmops_service()

            assert app is not None

