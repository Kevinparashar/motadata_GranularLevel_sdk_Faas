"""
Unit Tests for OTEL Trace Context DAL

Tests for OpenTelemetry trace context persistence operations.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.faas.shared.dal.otel_trace_context_dal import OTELTraceContextDAL
from src.core.postgresql_database import DatabaseConnection


class TestOTELTraceContextDAL:
    """Tests for OTELTraceContextDAL."""

    @pytest.fixture
    def mock_db(self):
        """Mock database connection."""
        db = MagicMock(spec=DatabaseConnection)
        db.execute_query = AsyncMock()
        return db

    @pytest.fixture
    def dal(self, mock_db):
        """OTELTraceContextDAL fixture."""
        return OTELTraceContextDAL(mock_db)

    @pytest.mark.asyncio
    async def test_save_trace_context_basic(self, dal, mock_db):
        """Test basic trace context save."""
        mock_db.execute_query.return_value = {"trace_id": "trace_123"}

        result = await dal.save_trace_context(
            trace_id="trace_123",
            span_id="span_456",
            service_name="test-service",
            span_name="test_operation",
        )

        assert result == "trace_123"
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        assert "INSERT INTO otel_trace_context" in call_args[0][0]
        params = call_args[1]["params"]
        assert params[0] == "trace_123"
        assert params[1] == "span_456"
        assert params[7] == "test-service"
        assert params[8] == "test_operation"

    @pytest.mark.asyncio
    async def test_save_trace_context_with_all_fields(self, dal, mock_db):
        """Test save trace context with all fields."""
        mock_db.execute_query.return_value = {"trace_id": "trace_full"}

        baggage = {"tenant_id": "tenant-1", "user_id": "user-1"}
        metadata = {"environment": "production", "version": "1.0.0"}

        result = await dal.save_trace_context(
            trace_id="trace_full",
            span_id="span_full",
            correlation_id="corr-1",
            parent_span_id="span_parent",
            trace_flags=1,
            trace_state="state=value",
            baggage=baggage,
            service_name="service-1",
            span_name="operation-1",
            tenant_id="tenant-1",
            user_id="user-1",
            operation_name="test_op",
            metadata=metadata,
        )

        assert result == "trace_full"
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        assert params[2] == "corr-1"  # correlation_id
        assert params[3] == "span_parent"  # parent_span_id
        assert params[4] == 1  # trace_flags
        assert params[5] == "state=value"  # trace_state
        assert json.loads(params[6]) == baggage  # baggage
        assert json.loads(params[12]) == metadata  # metadata

    @pytest.mark.asyncio
    async def test_get_trace_context(self, dal, mock_db):
        """Test get trace context."""
        mock_db.execute_query.return_value = {
            "trace_id": "trace_123",
            "span_id": "span_456",
            "service_name": "test-service",
            "baggage": json.dumps({"tenant_id": "tenant-1"}),
            "metadata": json.dumps({"env": "prod"}),
        }

        result = await dal.get_trace_context("trace_123", span_id="span_456")

        assert result is not None
        assert result["trace_id"] == "trace_123"
        assert isinstance(result["baggage"], dict)
        assert isinstance(result["metadata"], dict)

    @pytest.mark.asyncio
    async def test_get_trace_context_not_found(self, dal, mock_db):
        """Test get trace context when not found."""
        mock_db.execute_query.return_value = None

        result = await dal.get_trace_context("trace_nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_trace_by_correlation_id(self, dal, mock_db):
        """Test get traces by correlation ID."""
        mock_db.execute_query.return_value = [
            {"trace_id": "trace1", "correlation_id": "corr-1"},
            {"trace_id": "trace2", "correlation_id": "corr-1"},
        ]

        results = await dal.get_trace_by_correlation_id("corr-1", tenant_id="tenant-1")

        assert len(results) == 2
        assert all(r["correlation_id"] == "corr-1" for r in results)

    @pytest.mark.asyncio
    async def test_get_trace_chain(self, dal, mock_db):
        """Test get trace chain."""
        mock_db.execute_query.return_value = [
            {"trace_id": "trace-1", "span_id": "span1", "parent_span_id": None},
            {"trace_id": "trace-1", "span_id": "span2", "parent_span_id": "span1"},
            {"trace_id": "trace-1", "span_id": "span3", "parent_span_id": "span2"},
        ]

        results = await dal.get_trace_chain("trace-1", tenant_id="tenant-1")

        assert len(results) == 3
        assert all(r["trace_id"] == "trace-1" for r in results)

    @pytest.mark.asyncio
    async def test_get_child_spans(self, dal, mock_db):
        """Test get child spans."""
        mock_db.execute_query.return_value = [
            {"span_id": "child1", "parent_span_id": "parent_span"},
            {"span_id": "child2", "parent_span_id": "parent_span"},
        ]

        results = await dal.get_child_spans("parent_span", trace_id="trace-1")

        assert len(results) == 2
        assert all(r["parent_span_id"] == "parent_span" for r in results)

    @pytest.mark.asyncio
    async def test_get_trace_history(self, dal, mock_db):
        """Test get trace history."""
        mock_db.execute_query.return_value = [
            {"trace_id": "trace1", "service_name": "service-1"},
            {"trace_id": "trace2", "service_name": "service-1"},
        ]

        results = await dal.get_trace_history(
            service_name="service-1",
            tenant_id="tenant-1",
            limit=10,
            offset=0,
        )

        assert len(results) == 2
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "service_name" in query
        assert "tenant_id" in query

    @pytest.mark.asyncio
    async def test_get_trace_history_with_filters(self, dal, mock_db):
        """Test get trace history with all filters."""
        mock_db.execute_query.return_value = []

        results = await dal.get_trace_history(
            service_name="service-1",
            tenant_id="tenant-1",
            user_id="user-1",
            operation_name="operation-1",
            limit=50,
            offset=10,
        )

        assert results == []
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "service_name" in query
        assert "user_id" in query
        assert "operation_name" in query

    @pytest.mark.asyncio
    async def test_get_baggage_context(self, dal, mock_db):
        """Test get baggage context."""
        mock_db.execute_query.return_value = {
            "trace_id": "trace_123",
            "baggage": json.dumps({"tenant_id": "tenant-1", "user_id": "user-1"}),
        }

        baggage = await dal.get_baggage_context("trace_123")

        assert baggage is not None
        assert baggage["tenant_id"] == "tenant-1"
        assert baggage["user_id"] == "user-1"

    @pytest.mark.asyncio
    async def test_get_baggage_context_not_found(self, dal, mock_db):
        """Test get baggage context when trace not found."""
        mock_db.execute_query.return_value = None

        baggage = await dal.get_baggage_context("trace_nonexistent")

        assert baggage is None

    @pytest.mark.asyncio
    async def test_get_baggage_context_no_baggage(self, dal, mock_db):
        """Test get baggage context when no baggage."""
        mock_db.execute_query.return_value = {
            "trace_id": "trace_123",
            "baggage": None,
        }

        baggage = await dal.get_baggage_context("trace_123")

        assert baggage is None

    @pytest.mark.asyncio
    async def test_cleanup_old_traces(self, dal, mock_db):
        """Test cleanup old traces."""
        mock_db.execute_query.return_value = 25

        result = await dal.cleanup_old_traces(days=90, tenant_id="tenant-1")

        assert result == 25
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "DELETE FROM otel_trace_context" in query
        assert "INTERVAL" in query

    @pytest.mark.asyncio
    async def test_cleanup_old_traces_without_tenant(self, dal, mock_db):
        """Test cleanup old traces without tenant."""
        mock_db.execute_query.return_value = 50

        result = await dal.cleanup_old_traces(days=30)

        assert result == 50

    @pytest.mark.asyncio
    async def test_get_trace_chain_with_json_parsing(self, dal, mock_db):
        """Test get trace chain with JSON parsing."""
        mock_db.execute_query.return_value = [
            {
                "trace_id": "trace1",
                "baggage": json.dumps({"tenant_id": "tenant-1"}),
                "metadata": json.dumps({"env": "prod"}),
            }
        ]

        results = await dal.get_trace_chain("trace1")

        assert len(results) == 1
        assert isinstance(results[0]["baggage"], dict)
        assert isinstance(results[0]["metadata"], dict)

    @pytest.mark.asyncio
    async def test_get_trace_chain_empty(self, dal, mock_db):
        """Test get trace chain with empty result."""
        mock_db.execute_query.return_value = None

        results = await dal.get_trace_chain("trace_nonexistent")

        assert results == []

    @pytest.mark.asyncio
    async def test_save_trace_context_with_none_values(self, dal, mock_db):
        """Test save trace context with None optional values."""
        mock_db.execute_query.return_value = {"trace_id": "trace_none"}

        result = await dal.save_trace_context(
            trace_id="trace_none",
            span_id="span_none",
        )

        assert result == "trace_none"
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        assert params[2] is None  # correlation_id
        assert params[3] is None  # parent_span_id
        assert params[9] is None  # tenant_id

    @pytest.mark.asyncio
    async def test_get_trace_by_correlation_id_without_tenant(self, dal, mock_db):
        """Test get trace by correlation ID without tenant."""
        mock_db.execute_query.return_value = [{"trace_id": "trace1"}]

        results = await dal.get_trace_by_correlation_id("corr-1")

        assert len(results) == 1
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "AND tenant_id" not in query

