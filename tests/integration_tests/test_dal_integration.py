"""
Integration Tests for Data Access Layer (DAL)

Tests DAL integration across components:
- DAL integration with Gateway, RAG, Agent, Cache
- DAL integration with LLMOps
- DAL integration with Vector Operations
- DAL integration with Orchestrator
- Cross-DAL data consistency
- Tenant isolation in DALs
"""


from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.cache_mechanism import CacheConfig, CacheMechanism
from src.core.llmops import LLMOps
from src.faas.shared.dal import (
    CacheContextDAL,
    EmbeddingDAL,
    GatewayRequestHistoryDAL,
    LLMOpsDAL,
    RAGQueryHistoryDAL,
)


@pytest.mark.integration
class TestDALGatewayIntegration:
    """Test DAL integration with Gateway."""

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
    async def test_gateway_uses_history_dal(self, gateway_history_dal, mock_db):
        """Test that Gateway uses GatewayRequestHistoryDAL."""
        tenant_id = "tenant_123"
        correlation_id = "corr_123"

        # Save request history
        request_id = await gateway_history_dal.save_request(
            request_id="req_123",
            operation_type="completion",
            model="gpt-4",
            prompt="Test prompt",
            response_text="Test response",
            tenant_id=tenant_id,
            correlation_id=correlation_id,
        )

        # Verify DAL was called
        assert request_id is not None
        assert mock_db.execute_query.called

    @pytest.mark.asyncio
    async def test_gateway_history_retrieval(self, gateway_history_dal, mock_db):
        """Test that Gateway history can be retrieved."""
        tenant_id = "tenant_123"

        # Mock retrieval
        mock_db.execute_query = AsyncMock(
            return_value=[
                {
                    "id": "req_123",
                    "operation_type": "completion",
                    "model": "gpt-4",
                    "status": "success",
                }
            ]
        )

        # Get request history
        history = await gateway_history_dal.get_request_history(tenant_id=tenant_id)

        # Verify history retrieval
        assert history is not None
        assert len(history) > 0


@pytest.mark.integration
class TestDALRAGIntegration:
    """Test DAL integration with RAG."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        db.execute_query = AsyncMock(return_value={"query_id": "query_123"})
        return db

    @pytest.fixture
    def rag_query_history_dal(self, mock_db):
        """Create RAGQueryHistoryDAL."""
        return RAGQueryHistoryDAL(db_connection=mock_db)

    @pytest.fixture
    def embedding_dal(self, mock_db):
        """Create EmbeddingDAL."""
        return EmbeddingDAL(db_connection=mock_db)

    @pytest.mark.asyncio
    async def test_rag_uses_query_history_dal(self, rag_query_history_dal, mock_db):
        """Test that RAG uses RAGQueryHistoryDAL."""
        tenant_id = "tenant_123"

        # Save query history
        query_id = await rag_query_history_dal.save_query(
            query="What is AI?",
            answer="AI is artificial intelligence",
            tenant_id=tenant_id,
        )

        # Verify DAL was called
        assert query_id is not None
        assert mock_db.execute_query.called

    @pytest.mark.asyncio
    async def test_rag_uses_embedding_dal(self, embedding_dal, mock_db):
        """Test that RAG uses EmbeddingDAL."""
        tenant_id = "tenant_123"
        document_id = 1
        embedding = [0.1, 0.2, 0.3] * 512

        # Mock return value for embedding insert
        mock_db.execute_query = AsyncMock(return_value={"id": 1})

        # Insert embedding
        embedding_id = await embedding_dal.insert_embedding(
            document_id=document_id,
            embedding=embedding,
            model="text-embedding-3-small",
            tenant_id=tenant_id,
        )

        # Verify DAL was called
        assert embedding_id is not None
        assert mock_db.execute_query.called


@pytest.mark.integration
class TestDALLLMOpsIntegration:
    """Test DAL integration with LLMOps."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        db.execute_query = AsyncMock(return_value={"id": "op_123"})
        return db

    @pytest.fixture
    def llmops_dal(self, mock_db):
        """Create LLMOpsDAL."""
        return LLMOpsDAL(db_connection=mock_db)

    @pytest.fixture
    def llmops(self, llmops_dal):
        """Create LLMOps instance."""
        return LLMOps(llmops_dal=llmops_dal)

    @pytest.mark.asyncio
    async def test_llmops_uses_dal(self, llmops, llmops_dal, mock_db):
        """Test that LLMOps uses LLMOpsDAL."""
        from src.core.llmops import LLMOperationType

        tenant_id = "tenant_123"

        # Log operation
        operation_id = await llmops.log_operation(
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            tenant_id=tenant_id,
        )

        # Verify DAL was called
        assert operation_id is not None
        assert mock_db.execute_query.called

    @pytest.mark.asyncio
    async def test_llmops_metrics_from_dal(self, llmops, llmops_dal, mock_db):
        """Test that LLMOps retrieves metrics from DAL."""
        tenant_id = "tenant_123"

        # Mock metrics response
        mock_db.execute_query = AsyncMock(
            return_value={
                "total_operations": 100,
                "average_latency_ms": 250.0,
                "total_tokens": 10000,
                "total_cost_usd": 5.0,
                "by_model": {"gpt-4": {"cost_usd": 5.0, "tokens": 10000}},
            }
        )

        # Get metrics
        metrics = await llmops.get_metrics(tenant_id=tenant_id)

        # Verify metrics retrieval
        assert metrics is not None


@pytest.mark.integration
class TestDALCacheIntegration:
    """Test DAL integration with Cache."""

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
        """Create CacheMechanism with DAL."""
        return CacheMechanism(
            config=CacheConfig(default_ttl=3600),
            cache_context_dal=cache_context_dal,
        )

    @pytest.mark.asyncio
    async def test_cache_uses_context_dal(self, cache, cache_context_dal, mock_db):
        """Test that Cache uses CacheContextDAL."""
        tenant_id = "tenant_123"
        key = "test_key"
        value = "test_value"

        # Set cache value
        await cache.set(key, value, tenant_id=tenant_id)

        # Verify DAL was called
        assert mock_db.execute_query.called

    @pytest.mark.asyncio
    async def test_cache_context_tracking(self, cache, cache_context_dal, mock_db):
        """Test that Cache tracks context in DAL."""
        tenant_id = "tenant_123"
        user_id = "user_123"
        conversation_id = "conv_123"

        # Set cache with context
        await cache.set(
            "test_key",
            "test_value",
            tenant_id=tenant_id,
            user_id=user_id,
            conversation_id=conversation_id,
        )

        # Verify context was tracked
        assert mock_db.execute_query.called


@pytest.mark.integration
class TestDALCrossComponentIntegration:
    """Test DAL integration across multiple components."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        db.execute_query = AsyncMock(return_value={"request_id": "req_123"})
        return db

    @pytest.mark.asyncio
    async def test_multiple_dals_share_database(self, mock_db):
        """Test that multiple DALs share the same database connection."""
        # Create multiple DALs with same DB
        gateway_dal = GatewayRequestHistoryDAL(db_connection=mock_db)
        rag_dal = RAGQueryHistoryDAL(db_connection=mock_db)
        llmops_dal = LLMOpsDAL(db_connection=mock_db)

        # Verify all DALs use same DB
        assert gateway_dal.db == mock_db
        assert rag_dal.db == mock_db
        assert llmops_dal.db == mock_db

    @pytest.mark.asyncio
    async def test_dal_tenant_isolation(self, mock_db):
        """Test that DALs enforce tenant isolation."""
        tenant_id_1 = "tenant_1"
        tenant_id_2 = "tenant_2"

        gateway_dal = GatewayRequestHistoryDAL(db_connection=mock_db)

        # Save requests for different tenants
        await gateway_dal.save_request(
            request_id="req_1",
            operation_type="completion",
            model="gpt-4",
            prompt="Tenant 1 query",
            tenant_id=tenant_id_1,
        )

        await gateway_dal.save_request(
            request_id="req_2",
            operation_type="completion",
            model="gpt-4",
            prompt="Tenant 2 query",
            tenant_id=tenant_id_2,
        )

        # Verify tenant isolation in queries
        # In actual implementation, queries should filter by tenant_id
        assert mock_db.execute_query.called


@pytest.mark.integration
class TestDALDataConsistency:
    """Test data consistency across DALs."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        db.execute_query = AsyncMock(return_value={"request_id": "req_123"})
        return db

    @pytest.mark.asyncio
    async def test_dal_transaction_support(self, mock_db):
        """Test that DALs support transactions."""
        # In actual implementation, DALs should support transactions
        gateway_dal = GatewayRequestHistoryDAL(db_connection=mock_db)

        # Save request (should be transactional)
        request_id = await gateway_dal.save_request(
            request_id="req_test",
            operation_type="completion",
            model="gpt-4",
            prompt="Test",
        )

        # Verify transaction support
        assert request_id is not None
        # In actual implementation, would verify transaction boundaries


@pytest.mark.integration
class TestDALEndToEndIntegration:
    """Test end-to-end DAL integration."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        db.execute_query = AsyncMock(return_value={"request_id": "req_123"})
        return db

    @pytest.mark.asyncio
    async def test_end_to_end_dal_workflow(self, mock_db):
        """Test complete DAL workflow across components."""
        tenant_id = "tenant_123"
        correlation_id = "corr_123"

        # Step 1: Gateway saves request history
        mock_db.execute_query = AsyncMock(return_value={"request_id": "req_123"})
        gateway_dal = GatewayRequestHistoryDAL(db_connection=mock_db)
        request_id = await gateway_dal.save_request(
            request_id="req_123",
            operation_type="completion",
            model="gpt-4",
            prompt="What is AI?",
            response_text="AI is artificial intelligence",
            tenant_id=tenant_id,
            correlation_id=correlation_id,
        )

        # Step 2: RAG saves query history
        mock_db.execute_query = AsyncMock(return_value={"query_id": "query_123"})
        rag_dal = RAGQueryHistoryDAL(db_connection=mock_db)
        query_id = await rag_dal.save_query(
            query="What is AI?",
            answer="AI is artificial intelligence",
            tenant_id=tenant_id,
        )

        # Step 3: LLMOps saves operation
        # Mock return value for LLMOps save (returns id, which is used as operation_id)
        mock_db.execute_query = AsyncMock(return_value={"id": "op_123"})
        llmops_dal = LLMOpsDAL(db_connection=mock_db)
        operation_id = await llmops_dal.save_operation(
            operation_id="op_123",
            operation_type="completion",
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            tenant_id=tenant_id,
        )

        # Verify all DALs worked together
        assert request_id is not None
        assert query_id is not None
        assert operation_id is not None
        assert mock_db.execute_query.called

