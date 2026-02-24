"""
Integration Tests for Context Preservation

Tests context preservation across components:
- Cache context preservation
- Gateway request history context
- FaaS service request context
- OTEL trace context persistence
- Codec context preservation
- Tenant context metadata
- Orchestrator context preservation
- Prompt context history preservation
"""


from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.cache_mechanism import CacheConfig, CacheMechanism
from src.faas.shared.dal import (
    CacheContextDAL,
    CodecContextDAL,
    FaaSRequestContextDAL,
    GatewayRequestHistoryDAL,
    OTELTraceContextDAL,
    OrchestratorContextDAL,
    PromptHistoryDAL,
    TenantContextMetadataDAL,
)


@pytest.mark.integration
class TestCacheContextPreservation:
    """Test Cache context preservation."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        db.execute_query = AsyncMock(return_value={"id": "cache_op_123"})
        return db

    @pytest.fixture
    def cache_context_dal(self, mock_db):
        """Create CacheContextDAL."""
        return CacheContextDAL(db_connection=mock_db)

    @pytest.fixture
    def cache(self, cache_context_dal):
        """Create CacheMechanism with context DAL."""
        return CacheMechanism(
            config=CacheConfig(default_ttl=3600),
            cache_context_dal=cache_context_dal,
        )

    @pytest.mark.asyncio
    async def test_cache_preserves_context_metadata(self, cache, cache_context_dal, mock_db):
        """Test that Cache preserves context metadata."""
        tenant_id = "tenant_123"
        user_id = "user_123"
        conversation_id = "conv_123"
        session_id = "session_123"

        # Set cache with context
        await cache.set(
            "test_key",
            "test_value",
            tenant_id=tenant_id,
            user_id=user_id,
            conversation_id=conversation_id,
            session_id=session_id,
            reason="user_request",
        )

        # Verify context was preserved
        assert mock_db.execute_query.called

    @pytest.mark.asyncio
    async def test_cache_context_aware_invalidation(self, cache, cache_context_dal, mock_db):
        """Test that Cache supports context-aware invalidation."""
        tenant_id = "tenant_123"
        conversation_id = "conv_123"

        # Invalidate by conversation
        await cache.invalidate_conversation(conversation_id=conversation_id, tenant_id=tenant_id)

        # Verify context-aware invalidation
        assert mock_db.execute_query.called


@pytest.mark.integration
class TestGatewayContextPreservation:
    """Test Gateway context preservation."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        db.execute_query = AsyncMock(return_value={"request_id": "req_123"})
        return db

    @pytest.fixture
    def gateway_history_dal(self, mock_db):
        """Create GatewayRequestHistoryDAL."""
        return GatewayRequestHistoryDAL(db_connection=mock_db)

    @pytest.mark.asyncio
    async def test_gateway_preserves_request_history(self, gateway_history_dal, mock_db):
        """Test that Gateway preserves request history."""
        tenant_id = "tenant_123"
        user_id = "user_123"
        conversation_id = "conv_123"
        correlation_id = "corr_123"

        # Save request history
        request_id = await gateway_history_dal.save_request(
            request_id="req_123",
            operation_type="completion",
            model="gpt-4",
            prompt="Test prompt",
            response_text="Test response",
            tenant_id=tenant_id,
            user_id=user_id,
            conversation_id=conversation_id,
            correlation_id=correlation_id,
        )

        # Verify history was preserved
        assert request_id is not None
        assert mock_db.execute_query.called

    @pytest.mark.asyncio
    async def test_gateway_preserves_model_selection_history(self, gateway_history_dal, mock_db):
        """Test that Gateway preserves model selection history."""
        tenant_id = "tenant_123"

        # Mock model selection patterns (returns list with request_count, not count)
        mock_db.execute_query = AsyncMock(
            return_value=[
                {
                    "model": "gpt-4",
                    "operation_type": "completion",
                    "request_count": 10,
                    "success_count": 9,
                    "error_count": 1,
                    "avg_latency_ms": 250.0,
                    "fallback_count": 0,
                    "cache_hit_count": 2,
                    "avg_retry_count": 0.1,
                }
            ]
        )

        # Get model selection patterns
        patterns = await gateway_history_dal.get_model_selection_patterns(tenant_id=tenant_id)

        # Verify patterns are retrieved
        assert patterns is not None
        assert isinstance(patterns, list)
        if len(patterns) > 0:
            assert "model" in patterns[0]


@pytest.mark.integration
class TestFaaSServiceContextPreservation:
    """Test FaaS Service context preservation."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        db.execute_query = AsyncMock(return_value={"id": "service_call_123"})
        return db

    @pytest.fixture
    def faas_request_context_dal(self, mock_db):
        """Create FaaSRequestContextDAL."""
        return FaaSRequestContextDAL(db_connection=mock_db)

    @pytest.mark.asyncio
    async def test_faas_preserves_service_call_chain(self, faas_request_context_dal, mock_db):
        """Test that FaaS preserves service call chain."""
        tenant_id = "tenant_123"
        correlation_id = "corr_123"
        request_id = "req_123"
        parent_request_id = "parent_req_123"

        # Mock return value for service call (returns request_id)
        mock_db.execute_query = AsyncMock(return_value={"request_id": request_id})

        # Save service call
        call_id = await faas_request_context_dal.save_service_call(
            service_name="gateway",
            endpoint="/api/v1/gateway/generate",
            method="POST",
            correlation_id=correlation_id,
            request_id=request_id,
            parent_request_id=parent_request_id,
            parent_service="orchestrator",
            tenant_id=tenant_id,
        )

        # Verify call chain was preserved
        assert call_id is not None
        assert mock_db.execute_query.called

    @pytest.mark.asyncio
    async def test_faas_preserves_cross_service_context(self, faas_request_context_dal, mock_db):
        """Test that FaaS preserves cross-service context."""
        correlation_id = "corr_123"
        tenant_id = "tenant_123"

        # Mock service call chain retrieval
        mock_db.execute_query = AsyncMock(
            return_value=[
                {
                    "service_name": "gateway",
                    "endpoint": "/api/v1/gateway/generate",
                    "status": "success",
                }
            ]
        )

        # Get service call chain
        chain = await faas_request_context_dal.get_service_call_chain(
            correlation_id=correlation_id, tenant_id=tenant_id
        )

        # Verify chain is retrieved
        assert chain is not None


@pytest.mark.integration
class TestOTELContextPreservation:
    """Test OTEL context preservation."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        db.execute_query = AsyncMock(return_value={"id": "trace_123"})
        return db

    @pytest.fixture
    def otel_trace_context_dal(self, mock_db):
        """Create OTELTraceContextDAL."""
        return OTELTraceContextDAL(db_connection=mock_db)

    @pytest.mark.asyncio
    async def test_otel_preserves_trace_context(self, otel_trace_context_dal, mock_db):
        """Test that OTEL preserves trace context."""
        trace_id = "trace_123"
        span_id = "span_123"
        correlation_id = "corr_123"
        tenant_id = "tenant_123"

        # Mock return value for trace context (returns trace_id)
        mock_db.execute_query = AsyncMock(return_value={"trace_id": "trace_123"})

        # Save trace context
        context_id = await otel_trace_context_dal.save_trace_context(
            trace_id=trace_id,
            span_id=span_id,
            correlation_id=correlation_id,
            tenant_id=tenant_id,
        )

        # Verify trace context was preserved
        assert context_id is not None
        assert mock_db.execute_query.called

    @pytest.mark.asyncio
    async def test_otel_preserves_trace_chain(self, otel_trace_context_dal, mock_db):
        """Test that OTEL preserves trace chain."""
        trace_id = "trace_123"
        tenant_id = "tenant_123"

        # Mock trace chain retrieval
        mock_db.execute_query = AsyncMock(
            return_value=[
                {
                    "span_id": "span_123",
                    "parent_span_id": None,
                    "span_name": "root_span",
                }
            ]
        )

        # Get trace chain
        chain = await otel_trace_context_dal.get_trace_chain(trace_id=trace_id, tenant_id=tenant_id)

        # Verify chain is retrieved
        assert chain is not None


@pytest.mark.integration
class TestCodecContextPreservation:
    """Test Codec context preservation."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        db.execute_query = AsyncMock(return_value={"id": "codec_op_123"})
        return db

    @pytest.fixture
    def codec_context_dal(self, mock_db):
        """Create CodecContextDAL."""
        return CodecContextDAL(db_connection=mock_db)

    @pytest.mark.asyncio
    async def test_codec_preserves_encoding_history(self, codec_context_dal, mock_db):
        """Test that Codec preserves encoding history."""
        tenant_id = "tenant_123"
        correlation_id = "corr_123"

        # Mock return value for codec operation (returns operation_id)
        mock_db.execute_query = AsyncMock(return_value={"operation_id": "codec_op_123"})

        # Save codec operation
        operation_id = await codec_context_dal.save_codec_operation(
            operation_id="codec_op_123",
            operation_type="encode",
            message_type="AgentMessage",
            schema_version="1.0.0",
            payload_size=1024,
            status="success",
            tenant_id=tenant_id,
            correlation_id=correlation_id,
        )

        # Verify encoding history was preserved
        assert operation_id is not None
        assert mock_db.execute_query.called

    @pytest.mark.asyncio
    async def test_codec_preserves_schema_version_context(self, codec_context_dal, mock_db):
        """Test that Codec preserves schema version context."""
        tenant_id = "tenant_123"

        # Mock schema version stats (returns list with usage_count, not count)
        mock_db.execute_query = AsyncMock(
            return_value=[
                {
                    "schema_version": "1.0.0",
                    "usage_count": 100,
                    "encode_count": 50,
                    "decode_count": 50,
                    "success_count": 95,
                    "error_count": 5,
                    "migration_count": 10,
                    "avg_payload_size": 1024.0,
                }
            ]
        )

        # Get schema version stats
        stats = await codec_context_dal.get_schema_version_stats(tenant_id=tenant_id)

        # Verify stats are retrieved
        assert stats is not None
        assert isinstance(stats, list)
        if len(stats) > 0:
            assert "schema_version" in stats[0]


@pytest.mark.integration
class TestTenantContextPreservation:
    """Test Tenant context preservation."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        db.execute_query = AsyncMock(return_value={"id": "tenant_meta_123"})
        return db

    @pytest.fixture
    def tenant_context_dal(self, mock_db):
        """Create TenantContextMetadataDAL."""
        return TenantContextMetadataDAL(db_connection=mock_db)

    @pytest.mark.asyncio
    async def test_tenant_preserves_metadata(self, tenant_context_dal, mock_db):
        """Test that Tenant preserves metadata."""
        tenant_id = "tenant_123"

        # Mock return value for tenant metadata (returns tenant_id)
        mock_db.execute_query = AsyncMock(return_value={"tenant_id": tenant_id})

        # Save tenant metadata
        meta_id = await tenant_context_dal.save_tenant_metadata(
            tenant_id=tenant_id,
            tenant_tier="premium",
            configuration={"max_requests": 1000},
        )

        # Verify metadata was preserved
        assert meta_id is not None
        assert mock_db.execute_query.called

    @pytest.mark.asyncio
    async def test_tenant_preserves_activity_history(self, tenant_context_dal, mock_db):
        """Test that Tenant preserves activity history."""
        tenant_id = "tenant_123"
        user_id = "user_123"

        # Mock return value for tenant activity (returns activity_id)
        mock_db.execute_query = AsyncMock(return_value={"activity_id": "activity_123"})

        # Save tenant activity
        activity_id = await tenant_context_dal.save_tenant_activity(
            tenant_id=tenant_id,
            activity_type="api_call",
            component="gateway",
            user_id=user_id,
        )

        # Verify activity was preserved
        assert activity_id is not None
        assert mock_db.execute_query.called


@pytest.mark.integration
class TestOrchestratorContextPreservation:
    """Test Orchestrator context preservation."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        db.execute_query = AsyncMock(return_value={"id": "orch_req_123"})
        return db

    @pytest.fixture
    def orchestrator_context_dal(self, mock_db):
        """Create OrchestratorContextDAL."""
        return OrchestratorContextDAL(db_connection=mock_db)

    @pytest.mark.asyncio
    async def test_orchestrator_preserves_request_history(self, orchestrator_context_dal, mock_db):
        """Test that Orchestrator preserves request history."""
        tenant_id = "tenant_123"
        correlation_id = "corr_123"
        request_id = "req_123"

        # Mock return value for orchestration request (returns request_id)
        mock_db.execute_query = AsyncMock(return_value={"request_id": request_id})

        # Save orchestration request
        req_id = await orchestrator_context_dal.save_orchestration_request(
            request_id=request_id,
            correlation_id=correlation_id,
            query="What is AI?",
            intent="question",
            service_name="agent",
            endpoint="/api/v1/agent/chat",
            tenant_id=tenant_id,
        )

        # Verify request history was preserved
        assert req_id is not None
        assert mock_db.execute_query.called

    @pytest.mark.asyncio
    async def test_orchestrator_preserves_intent_analysis(self, orchestrator_context_dal, mock_db):
        """Test that Orchestrator preserves intent analysis."""
        tenant_id = "tenant_123"
        correlation_id = "corr_123"

        # Mock return value for intent analysis (returns analysis_id)
        mock_db.execute_query = AsyncMock(return_value={"analysis_id": "analysis_123"})

        # Save intent analysis
        analysis_id = await orchestrator_context_dal.save_intent_analysis(
            query="What is AI?",
            intent="question",
            confidence=0.95,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
        )

        # Verify intent analysis was preserved
        assert analysis_id is not None
        assert mock_db.execute_query.called


@pytest.mark.integration
class TestPromptContextPreservation:
    """Test Prompt Context preservation."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        # Return state_id for context window state, id for history
        db.execute_query = AsyncMock(side_effect=[
            {"id": "prompt_hist_123"},
            {"state_id": "state_123"}
        ])
        return db

    @pytest.fixture
    def prompt_history_dal(self, mock_db):
        """Create PromptHistoryDAL."""
        return PromptHistoryDAL(db_connection=mock_db)

    @pytest.mark.asyncio
    async def test_prompt_preserves_history(self, prompt_history_dal, mock_db):
        """Test that Prompt preserves history."""
        tenant_id = "tenant_123"
        user_id = "user_123"
        context_id = "conv_123"

        # Save prompt history
        history_id = await prompt_history_dal.save_history(
            prompt="Test prompt",
            tenant_id=tenant_id,
            user_id=user_id,
            context_id=context_id,
            metadata={"rendered_prompt": "Rendered test prompt", "template_name": "test_template"},
        )

        # Verify history was preserved
        assert history_id is not None
        assert mock_db.execute_query.called

    @pytest.mark.asyncio
    async def test_prompt_preserves_context_window_state(self, prompt_history_dal, mock_db):
        """Test that Prompt preserves context window state."""
        tenant_id = "tenant_123"
        user_id = "user_123"
        context_id = "conv_123"

        # Mock return value for context window state (returns state_id)
        mock_db.execute_query = AsyncMock(return_value={"state_id": "state_123"})

        # Save context window state
        state_id = await prompt_history_dal.save_context_window_state(
            tenant_id=tenant_id,
            user_id=user_id,
            context_id=context_id,
            max_tokens=4000,
            safety_margin=200,
            current_tokens=1000,
            window_state={"status": "active"},
        )

        # Verify context window state was preserved
        assert state_id is not None
        assert mock_db.execute_query.called


@pytest.mark.integration
class TestContextPreservationEndToEnd:
    """Test end-to-end context preservation."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        db.execute_query = AsyncMock(return_value={"id": "context_123"})
        return db

    @pytest.mark.asyncio
    async def test_end_to_end_context_preservation_workflow(self, mock_db):
        """Test complete context preservation workflow."""
        tenant_id = "tenant_123"
        user_id = "user_123"
        conversation_id = "conv_123"
        correlation_id = "corr_123"
        request_id = "req_123"

        # Create separate mock DBs for each DAL to avoid conflicts
        cache_db = MagicMock()
        cache_db.execute_query = AsyncMock(return_value={"id": "cache_op_123"})
        cache_context_dal = CacheContextDAL(db_connection=cache_db)
        cache = CacheMechanism(
            config=CacheConfig(default_ttl=3600),
            cache_context_dal=cache_context_dal,
        )
        await cache.set(
            "test_key",
            "test_value",
            tenant_id=tenant_id,
            user_id=user_id,
            conversation_id=conversation_id,
        )

        gateway_db = MagicMock()
        gateway_db.execute_query = AsyncMock(return_value={"request_id": request_id})
        gateway_dal = GatewayRequestHistoryDAL(db_connection=gateway_db)
        await gateway_dal.save_request(
            request_id=request_id,
            operation_type="completion",
            model="gpt-4",
            prompt="Test",
            tenant_id=tenant_id,
            correlation_id=correlation_id,
        )

        faas_db = MagicMock()
        faas_db.execute_query = AsyncMock(return_value={"request_id": request_id})
        faas_dal = FaaSRequestContextDAL(db_connection=faas_db)
        await faas_dal.save_service_call(
            service_name="gateway",
            endpoint="/api/v1/gateway/generate",
            method="POST",
            correlation_id=correlation_id,
            request_id=request_id,
            tenant_id=tenant_id,
        )

        otel_db = MagicMock()
        otel_db.execute_query = AsyncMock(return_value={"trace_id": "trace_123"})
        otel_dal = OTELTraceContextDAL(db_connection=otel_db)
        await otel_dal.save_trace_context(
            trace_id="trace_123",
            span_id="span_123",
            correlation_id=correlation_id,
            tenant_id=tenant_id,
        )

        orchestrator_db = MagicMock()
        orchestrator_db.execute_query = AsyncMock(return_value={"request_id": request_id})
        orchestrator_dal = OrchestratorContextDAL(db_connection=orchestrator_db)
        await orchestrator_dal.save_orchestration_request(
            request_id=request_id,
            correlation_id=correlation_id,
            query="Test query",
            intent="question",
            service_name="agent",
            endpoint="/api/v1/agent/chat",
            tenant_id=tenant_id,
        )

        # Verify all context was preserved
        assert cache_db.execute_query.called
        assert gateway_db.execute_query.called
        assert faas_db.execute_query.called
        assert otel_db.execute_query.called
        assert orchestrator_db.execute_query.called

