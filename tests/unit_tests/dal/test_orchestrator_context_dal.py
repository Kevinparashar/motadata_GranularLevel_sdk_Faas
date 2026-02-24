"""
Unit tests for OrchestratorContextDAL.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.faas.shared.dal.orchestrator_context_dal import OrchestratorContextDAL
from src.core.postgresql_database import DatabaseConnection


@pytest.fixture
def mock_db():
    """Create a mock database connection."""
    db = MagicMock(spec=DatabaseConnection)
    db.execute_query = AsyncMock()
    return db


@pytest.fixture
def dal(mock_db):
    """Create an OrchestratorContextDAL instance with mocked database."""
    return OrchestratorContextDAL(mock_db)


class TestOrchestratorContextDAL:
    """Test cases for OrchestratorContextDAL."""

    @pytest.mark.asyncio
    async def test_save_orchestration_request_success(self, dal, mock_db):
        """Test saving successful orchestration request."""
        request_id = "req-123"
        correlation_id = "corr-456"
        query = "Hello, how are you?"
        intent = "agent_chat"
        service_name = "agent"
        endpoint = "/api/v1/agents/agent_123/chat"

        mock_db.execute_query.return_value = {"request_id": request_id}

        result = await dal.save_orchestration_request(
            request_id=request_id,
            correlation_id=correlation_id,
            query=query,
            intent=intent,
            service_name=service_name,
            endpoint=endpoint,
            tenant_id="tenant-123",
            user_id="user-456",
            status="success",
            latency_ms=150.5,
            cached=False,
        )

        assert result == request_id
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        assert params[0] == request_id
        assert params[1] == correlation_id
        assert params[2] == query
        assert params[3] == intent
        assert params[4] == service_name
        assert params[5] == endpoint

    @pytest.mark.asyncio
    async def test_save_orchestration_request_with_all_fields(self, dal, mock_db):
        """Test saving orchestration request with all fields."""
        request_id = "req-123"
        correlation_id = "corr-456"
        query = "Search documents"
        intent = "rag_query"
        service_name = "rag"
        endpoint = "/api/v1/rag/query"
        request_context = {"top_k": 5}
        routing_config = {"service": "rag", "endpoint": endpoint}
        response_data = {"results": []}

        mock_db.execute_query.return_value = {"request_id": request_id}

        result = await dal.save_orchestration_request(
            request_id=request_id,
            correlation_id=correlation_id,
            query=query,
            intent=intent,
            service_name=service_name,
            endpoint=endpoint,
            tenant_id="tenant-123",
            user_id="user-456",
            conversation_id="conv-789",
            session_id="session-abc",
            parent_request_id="parent-req-123",
            request_context=request_context,
            routing_config=routing_config,
            response_data=response_data,
            status="success",
            latency_ms=200.0,
            cached=True,
            metadata={"ip": "192.168.1.1"},
        )

        assert result == request_id
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        assert json.loads(params[11]) == request_context
        assert json.loads(params[12]) == routing_config
        assert json.loads(params[13]) == response_data

    @pytest.mark.asyncio
    async def test_save_orchestration_request_error(self, dal, mock_db):
        """Test saving orchestration request with error."""
        request_id = "req-123"
        error_message = "Service unavailable"

        mock_db.execute_query.return_value = {"request_id": request_id}

        result = await dal.save_orchestration_request(
            request_id=request_id,
            correlation_id="corr-456",
            query="test query",
            intent="unknown",
            service_name="gateway",
            endpoint="/api/v1/gateway/generate",
            status="error",
            error_message=error_message,
            latency_ms=50.0,
        )

        assert result == request_id
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        assert params[14] == "error"  # status is at index 14
        assert params[15] == error_message  # error_message is at index 15

    @pytest.mark.asyncio
    async def test_save_intent_analysis(self, dal, mock_db):
        """Test saving intent analysis."""
        query = "Hello, how are you?"
        intent = "agent_chat"
        confidence = 0.95
        reasoning = "Conversational query"

        analysis_id = "intent_analysis_abc123"
        mock_db.execute_query.return_value = {"analysis_id": analysis_id}

        result = await dal.save_intent_analysis(
            query=query,
            intent=intent,
            confidence=confidence,
            reasoning=reasoning,
            tenant_id="tenant-123",
            user_id="user-456",
            analysis_method="llm",
            cache_hit=False,
        )

        assert result == analysis_id
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        assert params[1] == query
        assert params[2] == intent
        assert params[3] == confidence
        assert params[4] == reasoning

    @pytest.mark.asyncio
    async def test_save_intent_analysis_cached(self, dal, mock_db):
        """Test saving intent analysis from cache."""
        query = "Search documents"
        intent = "rag_query"
        confidence = 0.9

        analysis_id = "intent_analysis_abc123"
        mock_db.execute_query.return_value = {"analysis_id": analysis_id}

        result = await dal.save_intent_analysis(
            query=query,
            intent=intent,
            confidence=confidence,
            analysis_method="cached",
            cache_hit=True,
            tenant_id="tenant-123",
        )

        assert result == analysis_id
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        assert params[10] == "cached"
        assert params[11] is True  # cache_hit

    @pytest.mark.asyncio
    async def test_save_routing_decision(self, dal, mock_db):
        """Test saving routing decision."""
        intent = "agent_chat"
        query = "Hello"
        service_name = "agent"
        endpoint = "/api/v1/agents/agent_123/chat"
        routing_reason = "Agent ID found in context"

        decision_id = "routing_decision_abc123"
        mock_db.execute_query.return_value = {"decision_id": decision_id}

        result = await dal.save_routing_decision(
            intent=intent,
            query=query,
            service_name=service_name,
            endpoint=endpoint,
            routing_reason=routing_reason,
            tenant_id="tenant-123",
            user_id="user-456",
            correlation_id="corr-789",
            request_id="req-123",
            fallback_used=False,
        )

        assert result == decision_id
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        assert params[1] == intent
        assert params[2] == query
        assert params[3] == service_name
        assert params[4] == endpoint
        assert params[5] == routing_reason

    @pytest.mark.asyncio
    async def test_save_routing_decision_fallback(self, dal, mock_db):
        """Test saving routing decision with fallback."""
        intent = "agent_chat"
        query = "Hello"
        service_name = "gateway"
        endpoint = "/api/v1/gateway/generate"
        fallback_service = "gateway"

        decision_id = "routing_decision_abc123"
        mock_db.execute_query.return_value = {"decision_id": decision_id}

        result = await dal.save_routing_decision(
            intent=intent,
            query=query,
            service_name=service_name,
            endpoint=endpoint,
            routing_reason="Fallback used",
            tenant_id="tenant-123",
            fallback_used=True,
            fallback_service=fallback_service,
        )

        assert result == decision_id
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        assert params[10] is True  # fallback_used
        assert params[11] == fallback_service

    @pytest.mark.asyncio
    async def test_save_cross_request_context(self, dal, mock_db):
        """Test saving cross-request context."""
        correlation_id = "corr-456"
        context_key = "conversation_state"
        context_value = {"step": 2, "data": "test"}

        context_id = "orchestrator_context_abc123"
        mock_db.execute_query.return_value = {"context_id": context_id}

        result = await dal.save_cross_request_context(
            correlation_id=correlation_id,
            context_key=context_key,
            context_value=context_value,
            tenant_id="tenant-123",
            user_id="user-456",
            ttl_seconds=3600,
        )

        assert result == context_id
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        assert params[1] == correlation_id
        assert params[2] == context_key
        assert json.loads(params[3]) == context_value
        assert params[8] == 3600  # ttl_seconds

    @pytest.mark.asyncio
    async def test_get_orchestration_request_history(self, dal, mock_db):
        """Test getting orchestration request history."""
        mock_results = [
            {
                "request_id": "req-1",
                "correlation_id": "corr-1",
                "query": "Hello",
                "intent": "agent_chat",
                "service_name": "agent",
                "endpoint": "/api/v1/agents/agent_123/chat",
                "status": "success",
                "latency_ms": 150.0,
                "cached": False,
                "request_context": json.dumps({"agent_id": "agent_123"}),
                "routing_config": json.dumps({"service": "agent"}),
                "response_data": json.dumps({"message": "Hello!"}),
                "metadata": json.dumps({}),
                "created_at": "2024-01-01T00:00:00",
            },
        ]

        mock_db.execute_query.return_value = mock_results

        result = await dal.get_orchestration_request_history(
            tenant_id="tenant-123",
            limit=10,
            offset=0,
        )

        assert len(result) == 1
        assert result[0]["request_id"] == "req-1"
        assert result[0]["intent"] == "agent_chat"
        assert result[0]["request_context"] == {"agent_id": "agent_123"}
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_orchestration_request_history_with_filters(self, dal, mock_db):
        """Test getting orchestration request history with filters."""
        mock_db.execute_query.return_value = []

        result = await dal.get_orchestration_request_history(
            tenant_id="tenant-123",
            user_id="user-456",
            conversation_id="conv-789",
            intent="rag_query",
            service_name="rag",
            status="success",
            time_range_hours=24,
            limit=50,
            offset=10,
        )

        assert result == []
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "tenant_id = $1" in query
        assert "intent = $4" in query  # intent is 4th parameter after tenant_id, user_id, conversation_id
        assert "service_name = $5" in query  # service_name is 5th parameter

    @pytest.mark.asyncio
    async def test_get_intent_analysis_history(self, dal, mock_db):
        """Test getting intent analysis history."""
        mock_results = [
            {
                "analysis_id": "analysis-1",
                "query": "Hello",
                "intent": "agent_chat",
                "confidence": 0.95,
                "reasoning": "Conversational",
                "analysis_method": "llm",
                "cache_hit": False,
                "context_used": json.dumps({}),
                "metadata": json.dumps({}),
                "created_at": "2024-01-01T00:00:00",
            },
        ]

        mock_db.execute_query.return_value = mock_results

        result = await dal.get_intent_analysis_history(
            tenant_id="tenant-123",
            intent="agent_chat",
            limit=10,
            offset=0,
        )

        assert len(result) == 1
        assert result[0]["analysis_id"] == "analysis-1"
        assert result[0]["intent"] == "agent_chat"
        assert result[0]["confidence"] == 0.95
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_routing_decision_history(self, dal, mock_db):
        """Test getting routing decision history."""
        mock_results = [
            {
                "decision_id": "decision-1",
                "intent": "agent_chat",
                "query": "Hello",
                "service_name": "agent",
                "endpoint": "/api/v1/agents/agent_123/chat",
                "routing_reason": "Standard routing",
                "fallback_used": False,
                "routing_config": json.dumps({"service": "agent"}),
                "metadata": json.dumps({}),
                "created_at": "2024-01-01T00:00:00",
            },
        ]

        mock_db.execute_query.return_value = mock_results

        result = await dal.get_routing_decision_history(
            tenant_id="tenant-123",
            intent="agent_chat",
            service_name="agent",
            limit=10,
            offset=0,
        )

        assert len(result) == 1
        assert result[0]["decision_id"] == "decision-1"
        assert result[0]["service_name"] == "agent"
        assert result[0]["fallback_used"] is False
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cross_request_context(self, dal, mock_db):
        """Test getting cross-request context."""
        correlation_id = "corr-456"
        context_key = "conversation_state"
        mock_results = [
            {
                "context_id": "context-1",
                "correlation_id": correlation_id,
                "context_key": context_key,
                "context_value": json.dumps({"step": 2}),
                "tenant_id": "tenant-123",
                "ttl_seconds": 3600,
                "metadata": json.dumps({}),
                "created_at": "2024-01-01T00:00:00",
                "expires_at": "2024-01-01T01:00:00",
            },
        ]

        mock_db.execute_query.return_value = mock_results

        result = await dal.get_cross_request_context(
            correlation_id=correlation_id,
            context_key=context_key,
            tenant_id="tenant-123",
        )

        assert len(result) == 1
        assert result[0]["context_id"] == "context-1"
        assert result[0]["context_key"] == context_key
        assert result[0]["context_value"] == {"step": 2}
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_orchestration_stats(self, dal, mock_db):
        """Test getting orchestration statistics."""
        mock_stats = {
            "total_requests": 100,
            "unique_intents": 5,
            "unique_services": 3,
            "unique_users": 10,
            "avg_latency_ms": 150.5,
            "cached_requests": 20,
            "error_requests": 5,
        }

        mock_db.execute_query.return_value = mock_stats

        result = await dal.get_orchestration_stats(
            tenant_id="tenant-123",
            time_range_hours=24,
        )

        assert result == mock_stats
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        assert call_args[1]["params"][0] == "tenant-123"
        assert call_args[1]["params"][1] == 24

    @pytest.mark.asyncio
    async def test_get_orchestration_stats_empty(self, dal, mock_db):
        """Test getting orchestration statistics when empty."""
        mock_db.execute_query.return_value = None

        result = await dal.get_orchestration_stats()

        assert result == {
            "total_requests": 0,
            "unique_intents": 0,
            "unique_services": 0,
            "unique_users": 0,
            "avg_latency_ms": 0.0,
            "cached_requests": 0,
            "error_requests": 0,
        }

    @pytest.mark.asyncio
    async def test_get_intent_distribution(self, dal, mock_db):
        """Test getting intent distribution."""
        mock_results = [
            {"intent": "agent_chat", "count": 50, "avg_confidence": 0.95},
            {"intent": "rag_query", "count": 30, "avg_confidence": 0.90},
            {"intent": "direct_llm", "count": 20, "avg_confidence": 0.85},
        ]

        mock_db.execute_query.return_value = mock_results

        result = await dal.get_intent_distribution(
            tenant_id="tenant-123",
            time_range_hours=24,
        )

        assert len(result) == 3
        assert result[0]["intent"] == "agent_chat"
        assert result[0]["count"] == 50
        assert result[0]["avg_confidence"] == 0.95
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_old_context(self, dal, mock_db):
        """Test cleaning up old context."""
        days = 90
        deleted_count = 10

        mock_db.execute_query.return_value = deleted_count

        result = await dal.cleanup_old_context(days=days, tenant_id="tenant-123")

        assert result == deleted_count
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert f"{days} days" in query
        assert "tenant_id = $1" in query

    @pytest.mark.asyncio
    async def test_get_orchestration_request_history_empty(self, dal, mock_db):
        """Test getting orchestration request history when empty."""
        mock_db.execute_query.return_value = None

        result = await dal.get_orchestration_request_history(tenant_id="tenant-123")

        assert result == []

    @pytest.mark.asyncio
    async def test_get_intent_analysis_history_empty(self, dal, mock_db):
        """Test getting intent analysis history when empty."""
        mock_db.execute_query.return_value = None

        result = await dal.get_intent_analysis_history(tenant_id="tenant-123")

        assert result == []

    @pytest.mark.asyncio
    async def test_get_routing_decision_history_empty(self, dal, mock_db):
        """Test getting routing decision history when empty."""
        mock_db.execute_query.return_value = None

        result = await dal.get_routing_decision_history(tenant_id="tenant-123")

        assert result == []

    @pytest.mark.asyncio
    async def test_get_cross_request_context_empty(self, dal, mock_db):
        """Test getting cross-request context when empty."""
        mock_db.execute_query.return_value = None

        result = await dal.get_cross_request_context(correlation_id="corr-456")

        assert result == []

    @pytest.mark.asyncio
    async def test_get_intent_distribution_empty(self, dal, mock_db):
        """Test getting intent distribution when empty."""
        mock_db.execute_query.return_value = None

        result = await dal.get_intent_distribution(tenant_id="tenant-123")

        assert result == []

