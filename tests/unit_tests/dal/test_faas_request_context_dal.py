"""
Unit Tests for FaaS Request Context DAL

Tests for cross-service request context and service call chain persistence operations.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.faas.shared.dal.faas_request_context_dal import FaaSRequestContextDAL
from src.core.postgresql_database import DatabaseConnection


class TestFaaSRequestContextDAL:
    """Tests for FaaSRequestContextDAL."""

    @pytest.fixture
    def mock_db(self):
        """Mock database connection."""
        db = MagicMock(spec=DatabaseConnection)
        db.execute_query = AsyncMock()
        return db

    @pytest.fixture
    def dal(self, mock_db):
        """FaaSRequestContextDAL fixture."""
        return FaaSRequestContextDAL(mock_db)

    @pytest.mark.asyncio
    async def test_save_service_call_success(self, dal, mock_db):
        """Test successful service call save."""
        mock_db.execute_query.return_value = {"request_id": "req_123"}

        result = await dal.save_service_call(
            service_name="rag-service",
            endpoint="/query",
            method="POST",
            correlation_id="corr-1",
            request_id="req_123",
            tenant_id="tenant-1",
            status_code=200,
            status="success",
            latency_ms=150.5,
        )

        assert result == "req_123"
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        assert "INSERT INTO faas_request_context" in call_args[0][0]
        params = call_args[1]["params"]
        assert params[0] == "rag-service"
        assert params[1] == "/query"
        assert params[2] == "POST"
        assert params[3] == "corr-1"
        assert params[4] == "req_123"

    @pytest.mark.asyncio
    async def test_save_service_call_with_parent(self, dal, mock_db):
        """Test save service call with parent request."""
        mock_db.execute_query.return_value = {"request_id": "req_child"}

        result = await dal.save_service_call(
            service_name="gateway-service",
            endpoint="/generate",
            method="POST",
            correlation_id="corr-1",
            request_id="req_child",
            parent_request_id="req_parent",
            parent_service="orchestrator-service",
            tenant_id="tenant-1",
            status="success",
        )

        assert result == "req_child"
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        assert params[5] == "req_parent"  # parent_request_id
        assert params[6] == "orchestrator-service"  # parent_service

    @pytest.mark.asyncio
    async def test_save_service_call_with_error(self, dal, mock_db):
        """Test save service call with error."""
        mock_db.execute_query.return_value = {"request_id": "req_error"}

        result = await dal.save_service_call(
            service_name="agent-service",
            endpoint="/chat",
            method="POST",
            correlation_id="corr-1",
            request_id="req_error",
            status_code=500,
            status="error",
            error_message="Internal server error",
            latency_ms=50.0,
        )

        assert result == "req_error"
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        assert params[9] == 500  # status_code
        assert params[10] == "error"  # status
        assert params[11] == "Internal server error"  # error_message

    @pytest.mark.asyncio
    async def test_save_service_call_with_data(self, dal, mock_db):
        """Test save service call with request/response data."""
        mock_db.execute_query.return_value = {"request_id": "req_data"}

        request_data = {"query": "test", "model": "gpt-4"}
        response_data = {"result": "success", "tokens": 100}
        context_state = {"session_id": "session-1", "conversation_id": "conv-1"}
        metadata = {"retry_count": 2, "cache_hit": False}

        result = await dal.save_service_call(
            service_name="rag-service",
            endpoint="/query",
            method="POST",
            correlation_id="corr-1",
            request_id="req_data",
            request_data=request_data,
            response_data=response_data,
            context_state=context_state,
            metadata=metadata,
        )

        assert result == "req_data"
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        assert json.loads(params[13]) == request_data  # request_data
        assert json.loads(params[14]) == response_data  # response_data
        assert json.loads(params[15]) == context_state  # context_state
        assert json.loads(params[16]) == metadata  # metadata

    @pytest.mark.asyncio
    async def test_get_service_call_chain(self, dal, mock_db):
        """Test get service call chain."""
        mock_db.execute_query.return_value = [
            {
                "service_name": "orchestrator-service",
                "endpoint": "/orchestrate",
                "request_id": "req1",
                "parent_request_id": None,
                "correlation_id": "corr-1",
            },
            {
                "service_name": "rag-service",
                "endpoint": "/query",
                "request_id": "req2",
                "parent_request_id": "req1",
                "correlation_id": "corr-1",
            },
        ]

        results = await dal.get_service_call_chain(
            correlation_id="corr-1",
            tenant_id="tenant-1",
        )

        assert len(results) == 2
        assert results[0]["service_name"] == "orchestrator-service"
        assert results[1]["service_name"] == "rag-service"
        assert results[1]["parent_request_id"] == "req1"

    @pytest.mark.asyncio
    async def test_get_service_call_chain_without_tenant(self, dal, mock_db):
        """Test get service call chain without tenant."""
        mock_db.execute_query.return_value = [{"request_id": "req1"}]

        results = await dal.get_service_call_chain("corr-1")

        assert len(results) == 1
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "AND tenant_id" not in query

    @pytest.mark.asyncio
    async def test_get_request_by_id(self, dal, mock_db):
        """Test get request by ID."""
        mock_db.execute_query.return_value = {
            "request_id": "req_123",
            "service_name": "gateway-service",
            "endpoint": "/generate",
            "status": "success",
        }

        result = await dal.get_request_by_id("req_123", tenant_id="tenant-1")

        assert result is not None
        assert result["request_id"] == "req_123"
        assert result["service_name"] == "gateway-service"

    @pytest.mark.asyncio
    async def test_get_request_by_id_not_found(self, dal, mock_db):
        """Test get request by ID when not found."""
        mock_db.execute_query.return_value = None

        result = await dal.get_request_by_id("req_nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_child_calls(self, dal, mock_db):
        """Test get child calls."""
        mock_db.execute_query.return_value = [
            {"request_id": "req_child1", "parent_request_id": "req_parent"},
            {"request_id": "req_child2", "parent_request_id": "req_parent"},
        ]

        results = await dal.get_child_calls("req_parent", tenant_id="tenant-1")

        assert len(results) == 2
        assert all(r["parent_request_id"] == "req_parent" for r in results)

    @pytest.mark.asyncio
    async def test_get_service_history(self, dal, mock_db):
        """Test get service history."""
        mock_db.execute_query.return_value = [
            {
                "service_name": "rag-service",
                "endpoint": "/query",
                "request_id": "req1",
                "status": "success",
            },
            {
                "service_name": "rag-service",
                "endpoint": "/query",
                "request_id": "req2",
                "status": "error",
            },
        ]

        results = await dal.get_service_history(
            service_name="rag-service",
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
    async def test_get_service_history_with_filters(self, dal, mock_db):
        """Test get service history with all filters."""
        mock_db.execute_query.return_value = []

        results = await dal.get_service_history(
            service_name="gateway-service",
            tenant_id="tenant-1",
            user_id="user-1",
            status="success",
            limit=50,
            offset=10,
        )

        assert results == []
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "service_name" in query
        assert "user_id" in query
        assert "status" in query

    @pytest.mark.asyncio
    async def test_get_service_call_stats(self, dal, mock_db):
        """Test get service call statistics."""
        mock_db.execute_query.return_value = {
            "total_calls": 1000,
            "unique_correlations": 100,
            "unique_services": 5,
            "success_calls": 950,
            "error_calls": 50,
            "child_calls": 200,
            "avg_latency_ms": 150.5,
            "max_latency_ms": 500.0,
            "min_latency_ms": 10.0,
        }

        stats = await dal.get_service_call_stats(
            service_name="rag-service",
            tenant_id="tenant-1",
            time_range_hours=24,
        )

        assert stats["total_calls"] == 1000
        assert stats["success_rate"] == pytest.approx(95.0, abs=0.1)
        assert stats["error_rate"] == pytest.approx(5.0, abs=0.1)
        assert stats["avg_latency_ms"] == 150.5

    @pytest.mark.asyncio
    async def test_get_service_call_stats_empty(self, dal, mock_db):
        """Test get service call stats when no data."""
        mock_db.execute_query.return_value = None

        stats = await dal.get_service_call_stats()

        assert stats["total_calls"] == 0
        assert stats["success_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_get_service_dependency_graph(self, dal, mock_db):
        """Test get service dependency graph."""
        mock_db.execute_query.return_value = [
            {
                "service_name": "orchestrator-service",
                "endpoint": "/orchestrate",
                "request_id": "req1",
                "parent_request_id": None,
                "correlation_id": "corr-1",
                "status": "success",
            },
            {
                "service_name": "rag-service",
                "endpoint": "/query",
                "request_id": "req2",
                "parent_request_id": "req1",
                "correlation_id": "corr-1",
                "status": "success",
            },
            {
                "service_name": "gateway-service",
                "endpoint": "/generate",
                "request_id": "req3",
                "parent_request_id": "req2",
                "correlation_id": "corr-1",
                "status": "success",
            },
        ]

        graph = await dal.get_service_dependency_graph("corr-1", tenant_id="tenant-1")

        assert graph["correlation_id"] == "corr-1"
        assert len(graph["services"]) == 3
        assert len(graph["edges"]) == 2
        assert len(graph["root_requests"]) == 1
        assert "orchestrator-service" in graph["services"]
        assert "rag-service" in graph["services"]
        assert "gateway-service" in graph["services"]

    @pytest.mark.asyncio
    async def test_get_service_dependency_graph_edges(self, dal, mock_db):
        """Test service dependency graph edges."""
        mock_db.execute_query.return_value = [
            {
                "service_name": "service-a",
                "request_id": "req1",
                "parent_request_id": None,
                "correlation_id": "corr-1",
                "status": "success",
            },
            {
                "service_name": "service-b",
                "request_id": "req2",
                "parent_request_id": "req1",
                "correlation_id": "corr-1",
                "status": "success",
            },
        ]

        graph = await dal.get_service_dependency_graph("corr-1")

        assert len(graph["edges"]) == 1
        edge = graph["edges"][0]
        assert edge["from"] == "service-a"
        assert edge["to"] == "service-b"
        assert edge["from_request_id"] == "req1"
        assert edge["to_request_id"] == "req2"

    @pytest.mark.asyncio
    async def test_cleanup_old_context(self, dal, mock_db):
        """Test cleanup old context."""
        mock_db.execute_query.return_value = 25

        result = await dal.cleanup_old_context(
            days=90,
            tenant_id="tenant-1",
        )

        assert result == 25
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "DELETE FROM faas_request_context" in query
        assert "INTERVAL" in query

    @pytest.mark.asyncio
    async def test_cleanup_old_context_without_tenant(self, dal, mock_db):
        """Test cleanup old context without tenant."""
        mock_db.execute_query.return_value = 50

        result = await dal.cleanup_old_context(days=30)

        assert result == 50

    @pytest.mark.asyncio
    async def test_get_service_call_chain_with_json_parsing(self, dal, mock_db):
        """Test get service call chain with JSON parsing."""
        mock_db.execute_query.return_value = [
            {
                "request_id": "req1",
                "request_data": json.dumps({"query": "test"}),
                "response_data": json.dumps({"result": "success"}),
                "context_state": json.dumps({"session": "session-1"}),
                "metadata": json.dumps({"retry": 1}),
            }
        ]

        results = await dal.get_service_call_chain("corr-1")

        assert len(results) == 1
        assert isinstance(results[0]["request_data"], dict)
        assert isinstance(results[0]["response_data"], dict)
        assert isinstance(results[0]["context_state"], dict)
        assert isinstance(results[0]["metadata"], dict)

    @pytest.mark.asyncio
    async def test_get_service_call_chain_empty(self, dal, mock_db):
        """Test get service call chain with empty result."""
        mock_db.execute_query.return_value = None

        results = await dal.get_service_call_chain("corr-nonexistent")

        assert results == []

    @pytest.mark.asyncio
    async def test_save_service_call_with_none_values(self, dal, mock_db):
        """Test save service call with None optional values."""
        mock_db.execute_query.return_value = {"request_id": "req_none"}

        result = await dal.save_service_call(
            service_name="test-service",
            endpoint="/test",
            method="GET",
            correlation_id="corr-1",
            request_id="req_none",
        )

        assert result == "req_none"
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        assert params[5] is None  # parent_request_id
        assert params[7] is None  # tenant_id
        assert params[8] is None  # user_id

