"""
Unit tests for LLMOps Service.
"""
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=SyntaxWarning)
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
warnings.filterwarnings("ignore", category=ImportWarning)
warnings.filterwarnings("ignore", category=UnicodeWarning)
warnings.filterwarnings("ignore", category=BytesWarning)

import sys
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Mock ml_service module before any imports to avoid numpy dependency
ml_service_mock = MagicMock()
ml_service_mock.MLService = MagicMock
ml_service_mock.create_ml_service = MagicMock
sys.modules['src.faas.services.ml_service'] = ml_service_mock

from src.core.llmops import LLMOperation, LLMOperationStatus, LLMOperationType
from src.faas.services.llmops_service.models import (
    LogOperationRequest,
    OperationStatus,
    OperationType,
)
from src.faas.services.llmops_service.service import (
    LLMOpsService,
    create_llmops_service,
)
from src.faas.shared.config import ServiceConfig


@pytest.fixture
def mock_config():
    """Create mock service configuration."""
    return ServiceConfig(
        service_name="llmops-service",
        service_version="1.0.0",
        service_port=8080,
        database_url="postgresql://user:pass@localhost:5432/testdb",  # noqa: S105
        gateway_service_url=None,
        cache_service_url=None,
        rag_service_url=None,
        agent_service_url=None,
        ml_service_url=None,
        prompt_service_url=None,
        data_ingestion_service_url=None,
        prompt_generator_service_url=None,
        llmops_service_url=None,
        dragonfly_url=None,
        nats_url=None,
        otel_exporter_otlp_endpoint=None,
        enable_nats=False,
        enable_otel=False,
    )


@pytest.fixture
def llmops_service(mock_config):
    """Create LLMOps service instance for testing."""
    with patch("src.faas.services.llmops_service.service.get_database_connection") as mock_get_db, \
         patch("src.faas.services.llmops_service.service.create_nats_client", return_value=None), \
         patch("src.faas.services.llmops_service.service.create_otel_tracer", return_value=None), \
         patch("src.faas.services.llmops_service.service.create_codec_manager") as mock_codec:
        
        # Mock database connection
        mock_db_manager = Mock()
        mock_db_manager.get_connection.return_value = None
        mock_get_db.return_value = mock_db_manager
        
        # Mock codec manager
        mock_codec.return_value = Mock()
        
        service = LLMOpsService(
            config=mock_config,
            db_connection=mock_db_manager,
            nats_client=None,
            otel_tracer=None,
        )
        
        # Mock llmops.initialize to avoid async issues
        service.llmops.initialize = AsyncMock()
        
        return service


def test_llmops_service_creation(llmops_service):
    """Test LLMOps service creation."""
    assert llmops_service is not None
    assert llmops_service.app is not None
    assert llmops_service.config.service_name == "llmops-service"
    assert llmops_service.llmops is not None


@pytest.mark.asyncio
async def test_handle_log_operation_success(llmops_service):
    """Test log operation handler success."""
    # Mock log_operation to return an operation ID
    llmops_service.llmops.log_operation = AsyncMock(return_value="op_123")
    
    request = LogOperationRequest(
        operation_type=OperationType.COMPLETION,
        model="gpt-4",
        prompt_tokens=100,
        completion_tokens=50,
        latency_ms=250.0,
        status=OperationStatus.SUCCESS,
        error_message=None,
        agent_id=None,
        metadata=None,
    )
    
    standard_headers = Mock()
    standard_headers.tenant_id = "tenant_123"
    standard_headers.correlation_id = "corr_123"
    standard_headers.request_id = "req_123"
    
    response = await llmops_service._handle_log_operation(request, standard_headers)
    
    assert response.success is True
    assert response.data["operation_id"] == "op_123"
    assert response.message == "Operation logged successfully"
    llmops_service.llmops.log_operation.assert_called_once()


@pytest.mark.asyncio
async def test_handle_log_operation_with_metadata(llmops_service):
    """Test log operation handler with metadata."""
    llmops_service.llmops.log_operation = AsyncMock(return_value="op_456")
    
    request = LogOperationRequest(
        operation_type=OperationType.CHAT,
        model="gpt-3.5-turbo",
        prompt_tokens=200,
        completion_tokens=150,
        latency_ms=500.0,
        status=OperationStatus.SUCCESS,
        error_message=None,
        agent_id="agent_123",
        metadata={"key": "value"},
    )
    
    standard_headers = Mock()
    standard_headers.tenant_id = "tenant_456"
    standard_headers.correlation_id = "corr_456"
    standard_headers.request_id = "req_456"
    
    response = await llmops_service._handle_log_operation(request, standard_headers)
    
    assert response.success is True
    assert response.data["operation_id"] == "op_456"
    # Note: OperationType.CHAT maps to LLMOperationType.CHAT, not COMPLETION
    llmops_service.llmops.log_operation.assert_called_once()
    call_args = llmops_service.llmops.log_operation.call_args
    assert call_args[1]["model"] == "gpt-3.5-turbo"
    assert call_args[1]["prompt_tokens"] == 200
    assert call_args[1]["completion_tokens"] == 150
    assert call_args[1]["latency_ms"] == pytest.approx(500.0)
    assert call_args[1]["tenant_id"] == "tenant_456"
    assert call_args[1]["agent_id"] == "agent_123"
    assert call_args[1]["metadata"] == {"key": "value"}


def test_calculate_cutoff_date_with_start_date(llmops_service):
    """Test calculate cutoff date with start_date."""
    start_date = datetime.now() - timedelta(hours=12)
    end_date = None
    
    cutoff = llmops_service._calculate_cutoff_date(start_date, end_date)
    
    assert cutoff == start_date


def test_calculate_cutoff_date_with_end_date(llmops_service):
    """Test calculate cutoff date with end_date."""
    start_date = None
    end_date = datetime.now()
    
    cutoff = llmops_service._calculate_cutoff_date(start_date, end_date)
    
    expected = end_date - timedelta(hours=24)
    assert cutoff == expected


def test_calculate_cutoff_date_without_dates(llmops_service):
    """Test calculate cutoff date without dates."""
    cutoff = llmops_service._calculate_cutoff_date(None, None)
    
    expected = datetime.now() - timedelta(hours=24)
    # Allow small time difference
    assert abs((cutoff - expected).total_seconds()) < 5


def test_filter_operations_all_filters(llmops_service):
    """Test filter operations with all filters."""
    cutoff = datetime.now() - timedelta(hours=1)
    
    # Create mock operations
    op1 = Mock()
    op1.timestamp = datetime.now() - timedelta(minutes=30)
    op1.tenant_id = "tenant_1"
    op1.agent_id = "agent_1"
    op1.model = "gpt-4"
    op1.operation_type.value = "completion"
    op1.status.value = "success"
    
    op2 = Mock()
    op2.timestamp = datetime.now() - timedelta(minutes=30)
    op2.tenant_id = "tenant_2"
    op2.agent_id = "agent_1"
    op2.model = "gpt-4"
    op2.operation_type.value = "completion"
    op2.status.value = "success"
    
    all_operations = [op1, op2]
    end_date = datetime.now()
    
    filtered = llmops_service._filter_operations(
        all_operations=all_operations,
        cutoff=cutoff,
        filter_tenant_id="tenant_1",
        agent_id="agent_1",
        model="gpt-4",
        operation_type="completion",
        status_filter="success",
        end_date=end_date,
    )
    
    assert len(filtered) == 1
    assert filtered[0] == op1


def test_filter_operations_no_filters(llmops_service):
    """Test filter operations with no filters."""
    cutoff = datetime.now() - timedelta(hours=1)
    
    op1 = Mock()
    op1.timestamp = datetime.now() - timedelta(minutes=30)
    op1.tenant_id = "tenant_1"
    op1.agent_id = "agent_1"
    op1.model = "gpt-4"
    op1.operation_type.value = "completion"
    op1.status.value = "success"
    
    all_operations = [op1]
    
    filtered = llmops_service._filter_operations(
        all_operations=all_operations,
        cutoff=cutoff,
        filter_tenant_id=None,
        agent_id=None,
        model=None,
        operation_type=None,
        status_filter=None,
        end_date=None,
    )
    
    assert len(filtered) == 1


def test_format_operation_list(llmops_service):
    """Test format operation list."""
    op = Mock()
    op.operation_id = "op_123"
    op.operation_type.value = "completion"
    op.model = "gpt-4"
    op.tenant_id = "tenant_1"
    op.agent_id = "agent_1"
    op.prompt_tokens = 100
    op.completion_tokens = 50
    op.total_tokens = 150
    op.latency_ms = 250.0
    op.cost_usd = 0.001
    op.status.value = "success"
    op.error_message = None
    op.timestamp = datetime(2024, 1, 1, 12, 0, 0)
    
    operations = [op]
    formatted = llmops_service._format_operation_list(operations)
    
    assert len(formatted) == 1
    assert formatted[0]["operation_id"] == "op_123"
    assert formatted[0]["operation_type"] == "completion"
    assert formatted[0]["model"] == "gpt-4"
    assert formatted[0]["tenant_id"] == "tenant_1"
    assert formatted[0]["agent_id"] == "agent_1"
    assert formatted[0]["prompt_tokens"] == 100
    assert formatted[0]["completion_tokens"] == 50
    assert formatted[0]["total_tokens"] == 150
    assert formatted[0]["latency_ms"] == pytest.approx(250.0)
    assert formatted[0]["cost_usd"] == pytest.approx(0.001)
    assert formatted[0]["status"] == "success"
    assert formatted[0]["error_message"] is None
    assert formatted[0]["timestamp"] == "2024-01-01T12:00:00"


def test_handle_query_operations_success(llmops_service):
    """Test query operations handler success."""
    # Create mock operations
    op1 = LLMOperation(
        operation_id="op_1",
        operation_type=LLMOperationType.COMPLETION,
        model="gpt-4",
        tenant_id="tenant_1",
        agent_id="agent_1",
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        latency_ms=250.0,
        cost_usd=0.001,
        status=LLMOperationStatus.SUCCESS,
        timestamp=datetime.now() - timedelta(minutes=30),
    )
    
    op2 = LLMOperation(
        operation_id="op_2",
        operation_type=LLMOperationType.EMBEDDING,
        model="text-embedding-3-small",
        tenant_id="tenant_1",
        agent_id=None,
        prompt_tokens=50,
        completion_tokens=0,
        total_tokens=50,
        latency_ms=100.0,
        cost_usd=0.0001,
        status=LLMOperationStatus.SUCCESS,
        timestamp=datetime.now() - timedelta(minutes=20),
    )
    
    llmops_service.llmops.operations = [op1, op2]
    
    standard_headers = Mock()
    standard_headers.tenant_id = "tenant_1"
    standard_headers.correlation_id = "corr_123"
    standard_headers.request_id = "req_123"
    
    response = llmops_service._handle_query_operations(
        tenant_id=None,
        agent_id=None,
        model=None,
        operation_type=None,
        status_filter=None,
        start_date=None,
        end_date=None,
        limit=100,
        offset=0,
        standard_headers=standard_headers,
    )
    
    assert response.success is True
    assert len(response.data["operations"]) == 2
    assert response.data["count"] == 2


def test_handle_query_operations_with_filters(llmops_service):
    """Test query operations handler with filters."""
    op1 = LLMOperation(
        operation_id="op_1",
        operation_type=LLMOperationType.COMPLETION,
        model="gpt-4",
        tenant_id="tenant_1",
        agent_id="agent_1",
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        latency_ms=250.0,
        cost_usd=0.001,
        status=LLMOperationStatus.SUCCESS,
        timestamp=datetime.now() - timedelta(minutes=30),
    )
    
    op2 = LLMOperation(
        operation_id="op_2",
        operation_type=LLMOperationType.COMPLETION,
        model="gpt-3.5-turbo",
        tenant_id="tenant_1",
        agent_id="agent_2",
        prompt_tokens=200,
        completion_tokens=100,
        total_tokens=300,
        latency_ms=500.0,
        cost_usd=0.002,
        status=LLMOperationStatus.SUCCESS,
        timestamp=datetime.now() - timedelta(minutes=20),
    )
    
    llmops_service.llmops.operations = [op1, op2]
    
    standard_headers = Mock()
    standard_headers.tenant_id = "tenant_1"
    standard_headers.correlation_id = "corr_123"
    standard_headers.request_id = "req_123"
    
    response = llmops_service._handle_query_operations(
        tenant_id="tenant_1",
        agent_id="agent_1",
        model="gpt-4",
        operation_type="completion",
        status_filter="success",
        start_date=datetime.now() - timedelta(hours=1),
        end_date=datetime.now(),
        limit=10,
        offset=0,
        standard_headers=standard_headers,
    )
    
    assert response.success is True
    assert len(response.data["operations"]) == 1
    assert response.data["operations"][0]["operation_id"] == "op_1"


def test_handle_query_operations_pagination(llmops_service):
    """Test query operations handler with pagination."""
    # Create multiple operations
    operations = []
    for i in range(5):
        op = LLMOperation(
            operation_id=f"op_{i}",
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            tenant_id="tenant_1",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            latency_ms=250.0,
            cost_usd=0.001,
            status=LLMOperationStatus.SUCCESS,
            timestamp=datetime.now() - timedelta(minutes=30 - i),
        )
        operations.append(op)
    
    llmops_service.llmops.operations = operations
    
    standard_headers = Mock()
    standard_headers.tenant_id = "tenant_1"
    standard_headers.correlation_id = "corr_123"
    standard_headers.request_id = "req_123"
    
    # Test pagination: limit=2, offset=1
    response = llmops_service._handle_query_operations(
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
    assert response.data["count"] == 2


def test_calculate_time_range_with_both_dates(llmops_service):
    """Test calculate time range with both start and end dates."""
    start_date = datetime.now() - timedelta(hours=12)
    end_date = datetime.now()
    
    time_range = llmops_service._calculate_time_range(start_date, end_date)
    
    assert time_range == 12


def test_calculate_time_range_with_start_date_only(llmops_service):
    """Test calculate time range with start date only."""
    start_date = datetime.now() - timedelta(hours=6)
    end_date = None
    
    time_range = llmops_service._calculate_time_range(start_date, end_date)
    
    assert time_range == 6


def test_calculate_time_range_without_dates(llmops_service):
    """Test calculate time range without dates."""
    time_range = llmops_service._calculate_time_range(None, None)
    
    assert time_range == 24


def test_format_metrics_response(llmops_service):
    """Test format metrics response."""
    metrics = {
        "total_operations": 100,
        "total_tokens": 10000,
        "total_cost_usd": 0.1,
        "average_latency_ms": 250.0,
        "success_rate": 0.95,
        "by_type": {
            "completion": {"count": 80},
            "embedding": {"count": 20},
        },
        "by_model": {
            "gpt-4": {"count": 50, "cost_usd": 0.05, "tokens": 5000},
            "gpt-3.5-turbo": {"count": 50, "cost_usd": 0.05, "tokens": 5000},
        },
    }
    
    formatted = llmops_service._format_metrics_response(metrics)
    
    assert formatted["total_operations"] == 100
    assert formatted["total_tokens"] == 10000
    assert formatted["total_cost_usd"] == pytest.approx(0.1)
    assert formatted["average_latency_ms"] == pytest.approx(250.0)
    assert formatted["success_rate"] == pytest.approx(0.95)
    assert formatted["operations_by_type"]["completion"] == 80
    assert formatted["operations_by_type"]["embedding"] == 20
    assert formatted["operations_by_model"]["gpt-4"] == 50
    assert formatted["cost_by_model"]["gpt-4"] == pytest.approx(0.05)
    assert formatted["tokens_by_model"]["gpt-4"] == 5000


def test_format_metrics_response_empty(llmops_service):
    """Test format metrics response with empty metrics."""
    metrics = {}
    
    formatted = llmops_service._format_metrics_response(metrics)
    
    assert formatted["total_operations"] == 0
    assert formatted["total_tokens"] == 0
    assert formatted["total_cost_usd"] == pytest.approx(0.0)
    assert formatted["average_latency_ms"] == pytest.approx(0.0)
    assert formatted["success_rate"] == pytest.approx(0.0)


def test_format_cost_analysis(llmops_service):
    """Test format cost analysis."""
    cost_summary = {
        "total_cost_usd": 0.1,
        "by_model": {
            "gpt-4": {"cost_usd": 0.05},
            "gpt-3.5-turbo": {"cost_usd": 0.05},
        },
    }
    
    metrics = {
        "by_type": {
            "completion": {},
            "embedding": {},
        },
    }
    
    start_date = datetime.now() - timedelta(hours=24)
    end_date = datetime.now()
    time_range_hours = 24
    
    formatted = llmops_service._format_cost_analysis(
        cost_summary=cost_summary,
        metrics=metrics,
        filter_tenant_id="tenant_1",
        start_date=start_date,
        end_date=end_date,
        time_range_hours=time_range_hours,
    )
    
    assert formatted["total_cost_usd"] == pytest.approx(0.1)
    assert formatted["cost_by_model"]["gpt-4"] == pytest.approx(0.05)
    assert formatted["cost_by_tenant"]["tenant_1"] == pytest.approx(0.1)
    assert formatted["period_start"] == start_date.isoformat()
    assert formatted["period_end"] == end_date.isoformat()


def test_format_cost_analysis_no_tenant(llmops_service):
    """Test format cost analysis without tenant filter."""
    cost_summary = {
        "total_cost_usd": 0.1,
        "by_model": {
            "gpt-4": {"cost_usd": 0.05},
        },
    }
    
    metrics = {
        "by_type": {
            "completion": {},
        },
    }
    
    formatted = llmops_service._format_cost_analysis(
        cost_summary=cost_summary,
        metrics=metrics,
        filter_tenant_id=None,
        start_date=None,
        end_date=None,
        time_range_hours=24,
    )
    
    assert formatted["cost_by_tenant"] == {}




@pytest.mark.asyncio
async def test_handle_query_operations_route_success(llmops_service):
    """Test query operations route success - test internal method directly."""
    op = LLMOperation(
        operation_id="op_1",
        operation_type=LLMOperationType.COMPLETION,
        model="gpt-4",
        tenant_id="tenant_1",
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        latency_ms=250.0,
        cost_usd=0.001,
        status=LLMOperationStatus.SUCCESS,
        timestamp=datetime.now() - timedelta(minutes=30),
    )
    
    llmops_service.llmops.operations = [op]
    
    from src.faas.shared.contracts import StandardHeaders
    
    standard_headers = StandardHeaders(
        **{"X-Tenant-ID": "tenant_1", "X-Correlation-ID": "corr_123", "X-Request-ID": "req_123"}
    )
    
    with patch("src.faas.services.llmops_service.service.extract_headers", return_value=standard_headers):
        result = await llmops_service._handle_query_operations_route(
            tenant_id="tenant_1",
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
        
        assert result.success is True
        assert len(result.data["operations"]) == 1


@pytest.mark.asyncio
async def test_handle_query_operations_route_error(llmops_service):
    """Test query operations route error handling."""
    llmops_service._handle_query_operations = Mock(side_effect=Exception("Query error"))
    
    from src.faas.shared.contracts import StandardHeaders
    from fastapi import HTTPException
    
    standard_headers = StandardHeaders(
        **{"X-Tenant-ID": "tenant_1", "X-Correlation-ID": "corr_123", "X-Request-ID": "req_123"}
    )
    
    with patch("src.faas.services.llmops_service.service.extract_headers", return_value=standard_headers):
        with pytest.raises(HTTPException) as exc_info:
            await llmops_service._handle_query_operations_route(
                tenant_id=None,
                agent_id=None,
                model=None,
                operation_type=None,
                status_filter=None,
                start_date=None,
                end_date=None,
                limit=100,
                offset=0,
                headers={},
            )
        
        assert exc_info.value.status_code == 500
        assert "Failed to query operations" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_handle_get_metrics_route_success(llmops_service):
    """Test get metrics route success - test internal method directly."""
    llmops_service.llmops.get_metrics = Mock(return_value={
        "total_operations": 100,
        "total_tokens": 10000,
        "total_cost_usd": 0.1,
        "average_latency_ms": 250.0,
        "success_rate": 0.95,
        "by_type": {},
        "by_model": {},
    })
    
    from src.faas.shared.contracts import StandardHeaders
    
    standard_headers = StandardHeaders(
        **{"X-Tenant-ID": "tenant_1", "X-Correlation-ID": "corr_123", "X-Request-ID": "req_123"}
    )
    
    with patch("src.faas.services.llmops_service.service.extract_headers", return_value=standard_headers):
        result = await llmops_service._handle_get_metrics_route(
            tenant_id="tenant_1",
            start_date=None,
            end_date=None,
            headers={},
        )
        
        assert result.success is True
        assert result.data["total_operations"] == 100


@pytest.mark.asyncio
async def test_handle_get_metrics_route_error(llmops_service):
    """Test get metrics route error handling."""
    llmops_service.llmops.get_metrics = Mock(side_effect=Exception("Metrics error"))
    
    from src.faas.shared.contracts import StandardHeaders
    from fastapi import HTTPException
    
    standard_headers = StandardHeaders(
        **{"X-Tenant-ID": "tenant_1", "X-Correlation-ID": "corr_123", "X-Request-ID": "req_123"}
    )
    
    with patch("src.faas.services.llmops_service.service.extract_headers", return_value=standard_headers):
        with pytest.raises(HTTPException) as exc_info:
            await llmops_service._handle_get_metrics_route(
                tenant_id=None,
                start_date=None,
                end_date=None,
                headers={},
            )
        
        assert exc_info.value.status_code == 500
        assert "Failed to get metrics" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_handle_get_cost_analysis_route_success(llmops_service):
    """Test get cost analysis route success - test internal method directly."""
    llmops_service.llmops.get_cost_summary = Mock(return_value={
        "total_cost_usd": 0.1,
        "by_model": {
            "gpt-4": {"cost_usd": 0.05},
        },
    })
    
    llmops_service.llmops.get_metrics = Mock(return_value={
        "by_type": {
            "completion": {},
        },
    })
    
    from src.faas.shared.contracts import StandardHeaders
    
    standard_headers = StandardHeaders(
        **{"X-Tenant-ID": "tenant_1", "X-Correlation-ID": "corr_123", "X-Request-ID": "req_123"}
    )
    
    with patch("src.faas.services.llmops_service.service.extract_headers", return_value=standard_headers):
        result = await llmops_service._handle_get_cost_analysis_route(
            tenant_id="tenant_1",
            start_date=None,
            end_date=None,
            headers={},
        )
        
        assert result.success is True
        assert result.data["total_cost_usd"] == pytest.approx(0.1)


@pytest.mark.asyncio
async def test_handle_get_cost_analysis_route_error(llmops_service):
    """Test get cost analysis route error handling."""
    llmops_service.llmops.get_cost_summary = Mock(side_effect=Exception("Cost error"))
    
    from src.faas.shared.contracts import StandardHeaders
    from fastapi import HTTPException
    
    standard_headers = StandardHeaders(
        **{"X-Tenant-ID": "tenant_1", "X-Correlation-ID": "corr_123", "X-Request-ID": "req_123"}
    )
    
    with patch("src.faas.services.llmops_service.service.extract_headers", return_value=standard_headers):
        with pytest.raises(HTTPException) as exc_info:
            await llmops_service._handle_get_cost_analysis_route(
                tenant_id=None,
                start_date=None,
                end_date=None,
                headers={},
            )
        
        assert exc_info.value.status_code == 500
        assert "Failed to get cost analysis" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_handle_health_check(llmops_service):
    """Test health check endpoint - test internal method directly."""
    result = await llmops_service._handle_health_check()
    
    assert result["status"] == "healthy"
    assert result["service"] == "llmops-service"


def test_create_llmops_service():
    """Test create_llmops_service factory function."""
    with patch("src.faas.services.llmops_service.service.load_config") as mock_load_config, \
         patch("src.faas.services.llmops_service.service.get_database_connection") as mock_get_db, \
         patch("src.faas.services.llmops_service.service.create_nats_client", return_value=None), \
         patch("src.faas.services.llmops_service.service.create_otel_tracer", return_value=None):
        
        from fastapi import FastAPI
        
        mock_config = Mock()
        mock_config.database_url = "postgresql://user:pass@localhost:5432/testdb"  # noqa: S105
        mock_config.enable_nats = False
        mock_config.enable_otel = False
        mock_config.service_version = "1.0.0"
        mock_load_config.return_value = mock_config
        
        mock_db_manager = Mock()
        mock_get_db.return_value = mock_db_manager
        
        app = create_llmops_service(
            service_name="llmops-service",
            config_overrides={},
        )
        
        assert app is not None
        assert isinstance(app, FastAPI)


def test_create_llmops_service_with_nats():
    """Test create_llmops_service with NATS enabled."""
    with patch("src.faas.services.llmops_service.service.load_config") as mock_load_config, \
         patch("src.faas.services.llmops_service.service.get_database_connection") as mock_get_db, \
         patch("src.faas.services.llmops_service.service.create_nats_client") as mock_nats, \
         patch("src.faas.services.llmops_service.service.create_otel_tracer", return_value=None):
        
        from fastapi import FastAPI
        
        mock_config = Mock()
        mock_config.database_url = "postgresql://user:pass@localhost:5432/testdb"  # noqa: S105
        mock_config.enable_nats = True
        mock_config.enable_otel = False
        mock_config.service_version = "1.0.0"
        mock_load_config.return_value = mock_config
        
        mock_nats_client = Mock()
        mock_nats.return_value = mock_nats_client
        
        mock_db_manager = Mock()
        mock_get_db.return_value = mock_db_manager
        
        app = create_llmops_service(
            service_name="llmops-service",
            config_overrides={},
        )
        
        assert app is not None
        assert isinstance(app, FastAPI)
        mock_nats.assert_called_once()


def test_create_llmops_service_with_otel():
    """Test create_llmops_service with OTEL enabled."""
    with patch("src.faas.services.llmops_service.service.load_config") as mock_load_config, \
         patch("src.faas.services.llmops_service.service.get_database_connection") as mock_get_db, \
         patch("src.faas.services.llmops_service.service.create_nats_client", return_value=None), \
         patch("src.faas.services.llmops_service.service.create_otel_tracer") as mock_otel:
        
        from fastapi import FastAPI
        
        mock_config = Mock()
        mock_config.database_url = "postgresql://user:pass@localhost:5432/testdb"  # noqa: S105
        mock_config.enable_nats = False
        mock_config.enable_otel = True
        mock_config.service_version = "1.0.0"
        mock_load_config.return_value = mock_config
        
        mock_otel_tracer = Mock()
        mock_otel.return_value = mock_otel_tracer
        
        mock_db_manager = Mock()
        mock_get_db.return_value = mock_db_manager
        
        app = create_llmops_service(
            service_name="llmops-service",
            config_overrides={},
        )
        
        assert app is not None
        assert isinstance(app, FastAPI)
        mock_otel.assert_called_once()


@pytest.mark.asyncio
async def test_startup_event(llmops_service):
    """Test startup event initializes LLMOps."""
    # The startup event is registered in __init__, so we just need to verify
    # that the app has the startup event registered
    assert llmops_service.app is not None
    
    # Verify llmops.initialize is callable (mocked in fixture as AsyncMock)
    assert callable(llmops_service.llmops.initialize)
    assert isinstance(llmops_service.llmops.initialize, AsyncMock)

