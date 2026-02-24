"""
Unit Tests for Gateway Request History DAL

Tests for gateway request/response history persistence operations.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.faas.shared.dal.gateway_request_history_dal import GatewayRequestHistoryDAL
from src.core.postgresql_database import DatabaseConnection


class TestGatewayRequestHistoryDAL:
    """Tests for GatewayRequestHistoryDAL."""

    @pytest.fixture
    def mock_db(self):
        """Mock database connection."""
        db = MagicMock(spec=DatabaseConnection)
        db.execute_query = AsyncMock()
        return db

    @pytest.fixture
    def dal(self, mock_db):
        """GatewayRequestHistoryDAL fixture."""
        return GatewayRequestHistoryDAL(mock_db)

    @pytest.mark.asyncio
    async def test_save_request_generate_success(self, dal, mock_db):
        """Test successful generate request save."""
        mock_db.execute_query.return_value = {"request_id": "req_123"}

        result = await dal.save_request(
            request_id="req_123",
            operation_type="generate",
            model="gpt-4",
            tenant_id="tenant-1",
            user_id="user-1",
            conversation_id="conv-1",
            prompt="Test prompt",
            response_text="Test response",
            usage={"prompt_tokens": 10, "completion_tokens": 20},
            latency_ms=150.5,
            status="success",
        )

        assert result == "req_123"
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        assert "INSERT INTO gateway_request_history" in call_args[0][0]
        params = call_args[1]["params"]
        assert params[0] == "req_123"
        assert params[1] == "generate"
        assert params[2] == "gpt-4"
        assert params[3] == "tenant-1"

    @pytest.mark.asyncio
    async def test_save_request_embed_success(self, dal, mock_db):
        """Test successful embed request save."""
        mock_db.execute_query.return_value = {"request_id": "req_456"}

        result = await dal.save_request(
            request_id="req_456",
            operation_type="embed",
            model="text-embedding-3-small",
            tenant_id="tenant-1",
            response_data={"embeddings_count": 5},
            usage={"total_tokens": 100},
            latency_ms=50.0,
            status="success",
        )

        assert result == "req_456"
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        assert params[1] == "embed"
        assert params[2] == "text-embedding-3-small"

    @pytest.mark.asyncio
    async def test_save_request_with_error(self, dal, mock_db):
        """Test save request with error."""
        mock_db.execute_query.return_value = {"request_id": "req_error"}

        result = await dal.save_request(
            request_id="req_error",
            operation_type="generate",
            model="gpt-4",
            status="error",
            error_message="Rate limit exceeded",
            error_type="RateLimitError",
            retry_count=3,
            fallback_used=True,
            fallback_model="gpt-3.5-turbo",
        )

        assert result == "req_error"
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        assert params[14] == "error"
        assert params[15] == "Rate limit exceeded"
        assert params[16] == "RateLimitError"
        assert params[17] == 3  # retry_count
        assert params[18] is True  # fallback_used
        assert params[19] == "gpt-3.5-turbo"  # fallback_model

    @pytest.mark.asyncio
    async def test_save_request_with_all_fields(self, dal, mock_db):
        """Test save request with all optional fields."""
        mock_db.execute_query.return_value = {"request_id": "req_full"}

        messages = [{"role": "user", "content": "Hello"}]
        response_data = {"choices": [{"message": {"content": "Hi"}}]}
        usage = {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15}
        metadata = {"stream": False, "finish_reason": "stop"}

        result = await dal.save_request(
            request_id="req_full",
            operation_type="generate",
            model="gpt-4",
            tenant_id="tenant-1",
            user_id="user-1",
            conversation_id="conv-1",
            session_id="session-1",
            correlation_id="corr-1",
            prompt="Test",
            messages=messages,
            response_text="Response",
            response_data=response_data,
            usage=usage,
            latency_ms=200.0,
            status="success",
            retry_count=1,
            fallback_used=False,
            cache_hit=True,
            metadata=metadata,
        )

        assert result == "req_full"
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        assert json.loads(params[9]) == messages  # messages
        assert json.loads(params[11]) == response_data  # response_data
        assert json.loads(params[12]) == usage  # usage
        assert json.loads(params[21]) == metadata  # metadata

    @pytest.mark.asyncio
    async def test_get_request_history_basic(self, dal, mock_db):
        """Test get request history with basic filters."""
        mock_db.execute_query.return_value = [
            {
                "request_id": "req1",
                "operation_type": "generate",
                "model": "gpt-4",
                "tenant_id": "tenant-1",
                "status": "success",
                "created_at": datetime.now(),
            }
        ]

        results = await dal.get_request_history(
            tenant_id="tenant-1",
            limit=10,
            offset=0,
        )

        assert len(results) == 1
        assert results[0]["operation_type"] == "generate"
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_request_history_with_all_filters(self, dal, mock_db):
        """Test get request history with all filters."""
        mock_db.execute_query.return_value = []

        results = await dal.get_request_history(
            tenant_id="tenant-1",
            user_id="user-1",
            conversation_id="conv-1",
            operation_type="generate",
            model="gpt-4",
            status="success",
            limit=50,
            offset=10,
        )

        assert results == []
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "tenant_id" in query
        assert "user_id" in query
        assert "conversation_id" in query
        assert "operation_type" in query
        assert "model" in query
        assert "status" in query

    @pytest.mark.asyncio
    async def test_get_request_history_with_json_parsing(self, dal, mock_db):
        """Test get request history with JSON parsing."""
        mock_db.execute_query.return_value = [
            {
                "request_id": "req1",
                "messages": json.dumps([{"role": "user", "content": "Hello"}]),
                "response_data": json.dumps({"choices": []}),
                "usage": json.dumps({"total_tokens": 10}),
                "metadata": json.dumps({"stream": False}),
            }
        ]

        results = await dal.get_request_history()

        assert len(results) == 1
        assert isinstance(results[0]["messages"], list)
        assert isinstance(results[0]["response_data"], dict)
        assert isinstance(results[0]["usage"], dict)
        assert isinstance(results[0]["metadata"], dict)

    @pytest.mark.asyncio
    async def test_get_request_by_correlation_id(self, dal, mock_db):
        """Test get requests by correlation ID."""
        mock_db.execute_query.return_value = [
            {"request_id": "req1", "correlation_id": "corr-1"},
            {"request_id": "req2", "correlation_id": "corr-1"},
        ]

        results = await dal.get_request_by_correlation_id(
            correlation_id="corr-1",
            tenant_id="tenant-1",
        )

        assert len(results) == 2
        assert all(r["correlation_id"] == "corr-1" for r in results)
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "correlation_id = $1" in query
        assert "tenant_id = $2" in query

    @pytest.mark.asyncio
    async def test_get_request_by_correlation_id_without_tenant(self, dal, mock_db):
        """Test get requests by correlation ID without tenant."""
        mock_db.execute_query.return_value = [{"request_id": "req1"}]

        results = await dal.get_request_by_correlation_id("corr-1")

        assert len(results) == 1
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        # tenant_id should not be in WHERE clause
        assert "AND tenant_id" not in query

    @pytest.mark.asyncio
    async def test_get_model_selection_patterns(self, dal, mock_db):
        """Test get model selection patterns."""
        mock_db.execute_query.return_value = [
            {
                "model": "gpt-4",
                "operation_type": "generate",
                "request_count": 100,
                "success_count": 95,
                "error_count": 5,
                "avg_latency_ms": 200.5,
                "fallback_count": 2,
                "cache_hit_count": 10,
                "avg_retry_count": 0.5,
            }
        ]

        results = await dal.get_model_selection_patterns(
            tenant_id="tenant-1",
            time_range_hours=24,
            limit=10,
        )

        assert len(results) == 1
        assert results[0]["model"] == "gpt-4"
        assert results[0]["request_count"] == 100
        assert results[0]["success_rate"] == pytest.approx(95.0, abs=0.1)
        assert results[0]["avg_latency_ms"] == 200.5

    @pytest.mark.asyncio
    async def test_get_model_selection_patterns_without_filters(self, dal, mock_db):
        """Test get model selection patterns without filters."""
        mock_db.execute_query.return_value = []

        results = await dal.get_model_selection_patterns(limit=20)

        assert results == []
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "tenant_id" not in query
        assert "INTERVAL" not in query

    @pytest.mark.asyncio
    async def test_get_operation_context_stats(self, dal, mock_db):
        """Test get operation context statistics."""
        mock_db.execute_query.return_value = {
            "total_requests": 1000,
            "requests_with_retries": 50,
            "avg_retry_count": 1.2,
            "max_retry_count": 3,
            "fallback_requests": 20,
            "error_requests": 30,
            "unique_error_types": 5,
            "cache_hits": 200,
            "avg_latency_ms": 150.5,
        }

        stats = await dal.get_operation_context_stats(
            tenant_id="tenant-1",
            time_range_hours=24,
        )

        assert stats["total_requests"] == 1000
        assert stats["retry_rate"] == pytest.approx(5.0, abs=0.1)
        assert stats["fallback_rate"] == pytest.approx(2.0, abs=0.1)
        assert stats["error_rate"] == pytest.approx(3.0, abs=0.1)
        assert stats["cache_hit_rate"] == pytest.approx(20.0, abs=0.1)
        assert stats["avg_latency_ms"] == 150.5

    @pytest.mark.asyncio
    async def test_get_operation_context_stats_empty(self, dal, mock_db):
        """Test get operation context stats when no data."""
        mock_db.execute_query.return_value = None

        stats = await dal.get_operation_context_stats()

        assert stats["total_requests"] == 0
        assert stats["retry_rate"] == 0.0
        assert stats["error_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_get_conversation_history(self, dal, mock_db):
        """Test get conversation history."""
        mock_db.execute_query.return_value = [
            {
                "request_id": "req1",
                "conversation_id": "conv-1",
                "prompt": "Hello",
                "response_text": "Hi",
            },
            {
                "request_id": "req2",
                "conversation_id": "conv-1",
                "prompt": "How are you?",
                "response_text": "I'm fine",
            },
        ]

        results = await dal.get_conversation_history(
            conversation_id="conv-1",
            tenant_id="tenant-1",
            limit=100,
        )

        assert len(results) == 2
        assert all(r["conversation_id"] == "conv-1" for r in results)
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "conversation_id = $1" in query

    @pytest.mark.asyncio
    async def test_get_conversation_history_without_tenant(self, dal, mock_db):
        """Test get conversation history without tenant."""
        mock_db.execute_query.return_value = [{"request_id": "req1"}]

        results = await dal.get_conversation_history("conv-1", limit=50)

        assert len(results) == 1
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        # tenant_id should not be in WHERE clause
        assert "AND tenant_id" not in query

    @pytest.mark.asyncio
    async def test_cleanup_old_history(self, dal, mock_db):
        """Test cleanup old history."""
        mock_db.execute_query.return_value = 25

        result = await dal.cleanup_old_history(
            days=90,
            tenant_id="tenant-1",
        )

        assert result == 25
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "DELETE FROM gateway_request_history" in query
        assert "INTERVAL" in query

    @pytest.mark.asyncio
    async def test_cleanup_old_history_without_tenant(self, dal, mock_db):
        """Test cleanup old history without tenant."""
        mock_db.execute_query.return_value = 50

        result = await dal.cleanup_old_history(days=30)

        assert result == 50

    @pytest.mark.asyncio
    async def test_get_request_history_empty(self, dal, mock_db):
        """Test get request history with empty result."""
        mock_db.execute_query.return_value = None

        results = await dal.get_request_history()

        assert results == []

    @pytest.mark.asyncio
    async def test_save_request_with_none_values(self, dal, mock_db):
        """Test save request with None optional values."""
        mock_db.execute_query.return_value = {"request_id": "req_none"}

        result = await dal.save_request(
            request_id="req_none",
            operation_type="generate",
            model="gpt-4",
        )

        assert result == "req_none"
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        # Check that None values are handled
        assert params[3] is None  # tenant_id
        assert params[4] is None  # user_id
        assert params[5] is None  # conversation_id

    @pytest.mark.asyncio
    async def test_get_model_selection_patterns_zero_requests(self, dal, mock_db):
        """Test get model selection patterns with zero requests."""
        mock_db.execute_query.return_value = [
            {
                "model": "gpt-4",
                "operation_type": "generate",
                "request_count": 0,
                "success_count": 0,
                "error_count": 0,
                "avg_latency_ms": None,
                "fallback_count": 0,
                "cache_hit_count": 0,
                "avg_retry_count": None,
            }
        ]

        results = await dal.get_model_selection_patterns()

        assert len(results) == 1
        assert results[0]["success_rate"] == 0.0
        assert results[0]["avg_latency_ms"] == 0.0

