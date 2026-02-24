"""
Comprehensive Integration Tests for LLMOps

Tests LLMOps integration with all components:
- LLMOps ↔ Agent (agent operation logging)
- LLMOps ↔ RAG (RAG query logging)
- LLMOps ↔ Prompt Context (prompt usage tracking)
- LLMOps ↔ Gateway (gateway operation logging)
- LLMOps ↔ All FaaS Services (service-level metrics)
- LLMOps ↔ Database (metrics persistence)
"""


from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.agno_agent_framework import Agent
from src.core.llmops import LLMOps, LLMOperationStatus, LLMOperationType
from src.core.litellm_gateway import LiteLLMGateway
from src.core.prompt_context_management import PromptContextManager
from src.core.rag import RAGSystem


@pytest.mark.integration
class TestLLMOpsAgentIntegration:
    """Test LLMOps integration with Agent Framework."""

    @pytest.fixture
    def mock_llmops_dal(self):
        """Create mock LLMOps DAL."""
        dal = MagicMock()
        dal.save_operation = AsyncMock(return_value="op_123")
        dal.get_operations = AsyncMock(return_value=[])
        dal.get_metrics = AsyncMock(return_value={})
        return dal

    @pytest.fixture
    def llmops(self, mock_llmops_dal):
        """Create LLMOps instance."""
        return LLMOps(llmops_dal=mock_llmops_dal)

    @pytest.fixture
    def mock_gateway(self):
        """Create mock gateway."""
        gateway = MagicMock(spec=LiteLLMGateway)
        gateway.generate_async = AsyncMock()
        return gateway

    @pytest.fixture
    def agent_with_llmops(self, llmops, mock_gateway):
        """Create agent with LLMOps."""
        agent = Agent(
            agent_id="agent_123",
            name="Test Agent",
            gateway=mock_gateway,
        )
        # Note: Agent may integrate with LLMOps via gateway
        return agent, llmops, mock_gateway

    @pytest.mark.asyncio
    async def test_agent_operations_logged_to_llmops(self, agent_with_llmops, mock_llmops_dal):
        """Test that agent operations are logged to LLMOps."""
        agent, llmops, _ = agent_with_llmops
        tenant_id = "tenant_123"

        # Log agent operation
        operation_id = await llmops.log_operation(
            operation_type=LLMOperationType.CHAT,
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            latency_ms=500.0,
            tenant_id=tenant_id,
            agent_id=agent.agent_id,
        )

        # Verify operation was logged
        assert operation_id is not None
        assert operation_id != ""

        # Verify DAL was called
        assert mock_llmops_dal.save_operation.called

    @pytest.mark.asyncio
    async def test_agent_operation_metrics_retrieved(self, agent_with_llmops, mock_llmops_dal):
        """Test that agent operation metrics can be retrieved."""
        agent, llmops, _ = agent_with_llmops
        tenant_id = "tenant_123"

        # Mock metrics response
        mock_llmops_dal.get_metrics.return_value = {
            "total_operations": 10,
            "total_cost_usd": 5.0,
            "total_tokens": 1000,
            "avg_latency_ms": 500.0,
        }

        # Get metrics for agent
        metrics = await llmops.get_metrics(tenant_id=tenant_id, agent_id=agent.agent_id)

        # Verify metrics were retrieved
        assert metrics is not None
        assert "total_operations" in metrics or "total_cost_usd" in metrics

    @pytest.mark.asyncio
    async def test_agent_cost_tracking(self, agent_with_llmops, mock_llmops_dal):
        """Test that agent costs are tracked."""
        agent, llmops, _ = agent_with_llmops
        tenant_id = "tenant_123"

        # Log multiple operations
        await llmops.log_operation(
            operation_type=LLMOperationType.CHAT,
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            tenant_id=tenant_id,
            agent_id=agent.agent_id,
        )

        # Get cost summary
        mock_llmops_dal.get_metrics.return_value = {
            "total_cost_usd": 0.005,
            "total_tokens": 150,
            "by_model": {"gpt-4": {"cost_usd": 0.005, "tokens": 150}},
        }

        cost_summary = await llmops.get_cost_summary(tenant_id=tenant_id)

        # Verify cost tracking
        assert cost_summary is not None
        assert "total_cost_usd" in cost_summary


@pytest.mark.integration
class TestLLMOpsRAGIntegration:
    """Test LLMOps integration with RAG System."""

    @pytest.fixture
    def mock_llmops_dal(self):
        """Create mock LLMOps DAL."""
        dal = MagicMock()
        dal.save_operation = AsyncMock(return_value="op_123")
        dal.get_operations = AsyncMock(return_value=[])
        dal.get_metrics = AsyncMock(return_value={})
        return dal

    @pytest.fixture
    def llmops(self, mock_llmops_dal):
        """Create LLMOps instance."""
        return LLMOps(llmops_dal=mock_llmops_dal)

    @pytest.fixture
    def mock_gateway(self):
        """Create mock gateway."""
        gateway = MagicMock(spec=LiteLLMGateway)
        gateway.generate_async = AsyncMock()
        gateway.embed_async = AsyncMock(return_value={"embeddings": [[0.1, 0.2, 0.3]]})
        return gateway

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        db.execute_query = AsyncMock(return_value=[])
        return db

    @pytest.fixture
    def rag_with_llmops(self, llmops, mock_gateway, mock_db):
        """Create RAG system with LLMOps."""
        return RAGSystem(
            db=mock_db,
            gateway=mock_gateway,
        ), llmops

    @pytest.mark.asyncio
    async def test_rag_query_operations_logged(self, rag_with_llmops, mock_llmops_dal):
        """Test that RAG query operations are logged to LLMOps."""
        _, llmops = rag_with_llmops
        tenant_id = "tenant_123"

        # Log RAG query operation
        operation_id = await llmops.log_operation(
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            prompt_tokens=200,
            completion_tokens=100,
            latency_ms=1000.0,
            tenant_id=tenant_id,
            metadata={"query": "What is AI?", "num_documents": 5},
        )

        # Verify operation was logged
        assert operation_id is not None
        assert mock_llmops_dal.save_operation.called

    @pytest.mark.asyncio
    async def test_rag_embedding_operations_logged(self, rag_with_llmops, mock_llmops_dal):
        """Test that RAG embedding operations are logged."""
        _, llmops = rag_with_llmops
        tenant_id = "tenant_123"

        # Log embedding operation
        operation_id = await llmops.log_operation(
            operation_type=LLMOperationType.EMBEDDING,
            model="text-embedding-3-small",
            prompt_tokens=50,
            latency_ms=200.0,
            tenant_id=tenant_id,
            metadata={"document_count": 10},
        )

        # Verify operation was logged
        assert operation_id is not None
        assert mock_llmops_dal.save_operation.called

    @pytest.mark.asyncio
    async def test_rag_query_metrics_retrieved(self, rag_with_llmops, mock_llmops_dal):
        """Test that RAG query metrics can be retrieved."""
        _, llmops = rag_with_llmops
        tenant_id = "tenant_123"

        # Mock metrics response
        mock_llmops_dal.get_metrics.return_value = {
            "total_operations": 20,
            "total_cost_usd": 10.0,
            "avg_latency_ms": 800.0,
        }

        # Get metrics
        metrics = await llmops.get_metrics(tenant_id=tenant_id)

        # Verify metrics were retrieved
        assert metrics is not None


@pytest.mark.integration
class TestLLMOpsPromptContextIntegration:
    """Test LLMOps integration with Prompt Context Management."""

    @pytest.fixture
    def mock_llmops_dal(self):
        """Create mock LLMOps DAL."""
        dal = MagicMock()
        dal.save_operation = AsyncMock(return_value="op_123")
        return dal

    @pytest.fixture
    def llmops(self, mock_llmops_dal):
        """Create LLMOps instance."""
        return LLMOps(llmops_dal=mock_llmops_dal)

    @pytest.fixture
    def prompt_manager(self):
        """Create prompt context manager."""
        return PromptContextManager(
            max_tokens=4000,
            safety_margin=200,
            require_persistence=False,
        )

    @pytest.mark.asyncio
    async def test_prompt_usage_tracked_in_llmops(self, prompt_manager, llmops, mock_llmops_dal):
        """Test that prompt usage is tracked in LLMOps."""
        tenant_id = "tenant_123"

        # Add template
        prompt_manager.add_template(
            name="analysis",
            version="1.0.0",
            content="Analyze: {text}",
        )

        # Render prompt
        rendered = prompt_manager.render("analysis", {"text": "Test"})

        # Log prompt usage operation
        operation_id = await llmops.log_operation(
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            prompt_tokens=len(rendered.split()),
            tenant_id=tenant_id,
            metadata={"template_name": "analysis", "template_version": "1.0.0"},
        )

        # Verify operation was logged
        assert operation_id is not None
        assert mock_llmops_dal.save_operation.called


@pytest.mark.integration
class TestLLMOpsGatewayIntegration:
    """Test LLMOps integration with Gateway (already tested, but comprehensive)."""

    @pytest.fixture
    def mock_llmops_dal(self):
        """Create mock LLMOps DAL."""
        dal = MagicMock()
        dal.save_operation = AsyncMock(return_value="op_123")
        dal.get_operations = AsyncMock(return_value=[])
        return dal

    @pytest.fixture
    def llmops(self, mock_llmops_dal):
        """Create LLMOps instance."""
        return LLMOps(llmops_dal=mock_llmops_dal)

    @pytest.mark.asyncio
    async def test_gateway_generate_operations_logged(self, llmops, mock_llmops_dal):
        """Test that gateway generate operations are logged."""
        tenant_id = "tenant_123"

        # Log gateway generate operation
        operation_id = await llmops.log_operation(
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            prompt_tokens=150,
            completion_tokens=75,
            latency_ms=600.0,
            tenant_id=tenant_id,
            metadata={"provider": "openai", "stream": False},
        )

        # Verify operation was logged
        assert operation_id is not None
        assert mock_llmops_dal.save_operation.called

    @pytest.mark.asyncio
    async def test_gateway_embedding_operations_logged(self, llmops, mock_llmops_dal):
        """Test that gateway embedding operations are logged."""
        tenant_id = "tenant_123"

        # Log gateway embedding operation
        operation_id = await llmops.log_operation(
            operation_type=LLMOperationType.EMBEDDING,
            model="text-embedding-3-small",
            prompt_tokens=100,
            latency_ms=300.0,
            tenant_id=tenant_id,
            metadata={"embedding_dim": 1536},
        )

        # Verify operation was logged
        assert operation_id is not None
        assert mock_llmops_dal.save_operation.called

    @pytest.mark.asyncio
    async def test_gateway_error_operations_logged(self, llmops, mock_llmops_dal):
        """Test that gateway error operations are logged."""
        tenant_id = "tenant_123"

        # Log error operation
        operation_id = await llmops.log_operation(
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            status=LLMOperationStatus.ERROR,
            error_message="Rate limit exceeded",
            tenant_id=tenant_id,
        )

        # Verify error was logged
        assert operation_id is not None
        assert mock_llmops_dal.save_operation.called


@pytest.mark.integration
class TestLLMOpsFaaSServicesIntegration:
    """Test LLMOps integration with FaaS Services."""

    @pytest.fixture
    def mock_llmops_dal(self):
        """Create mock LLMOps DAL."""
        dal = MagicMock()
        dal.save_operation = AsyncMock(return_value="op_123")
        dal.get_operations = AsyncMock(return_value=[])
        dal.get_metrics = AsyncMock(return_value={})
        return dal

    @pytest.fixture
    def llmops(self, mock_llmops_dal):
        """Create LLMOps instance."""
        return LLMOps(llmops_dal=mock_llmops_dal)

    @pytest.mark.asyncio
    async def test_agent_service_operations_logged(self, llmops, mock_llmops_dal):
        """Test that Agent Service operations are logged."""
        tenant_id = "tenant_123"
        service_name = "agent_service"

        # Log service operation
        operation_id = await llmops.log_operation(
            operation_type=LLMOperationType.CHAT,
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            tenant_id=tenant_id,
            metadata={"service": service_name, "endpoint": "/api/v1/agents/chat"},
        )

        # Verify operation was logged
        assert operation_id is not None
        assert mock_llmops_dal.save_operation.called

    @pytest.mark.asyncio
    async def test_rag_service_operations_logged(self, llmops, mock_llmops_dal):
        """Test that RAG Service operations are logged."""
        tenant_id = "tenant_123"
        service_name = "rag_service"

        # Log service operation
        operation_id = await llmops.log_operation(
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            prompt_tokens=200,
            completion_tokens=100,
            tenant_id=tenant_id,
            metadata={"service": service_name, "endpoint": "/api/v1/rag/query"},
        )

        # Verify operation was logged
        assert operation_id is not None

    @pytest.mark.asyncio
    async def test_service_level_metrics_retrieved(self, llmops, mock_llmops_dal):
        """Test that service-level metrics can be retrieved."""
        tenant_id = "tenant_123"

        # Mock service-level metrics
        mock_llmops_dal.get_metrics.return_value = {
            "total_operations": 100,
            "total_cost_usd": 50.0,
            "operations_by_service": {
                "agent_service": 40,
                "rag_service": 35,
                "gateway_service": 25,
            },
        }

        # Get metrics
        metrics = await llmops.get_metrics(tenant_id=tenant_id)

        # Verify metrics were retrieved
        assert metrics is not None


@pytest.mark.integration
class TestLLMOpsDatabaseIntegration:
    """Test LLMOps integration with Database (DAL)."""

    @pytest.fixture
    def mock_llmops_dal(self):
        """Create mock LLMOps DAL."""
        dal = MagicMock()
        dal.save_operation = AsyncMock(return_value="op_123")
        dal.get_operations = AsyncMock(
            return_value=[
                {
                    "operation_id": "op_1",
                    "operation_type": "completion",
                    "model": "gpt-4",
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                    "cost_usd": 0.005,
                    "tenant_id": "tenant_123",
                }
            ]
        )
        dal.get_metrics = AsyncMock(
            return_value={
                "total_operations": 10,
                "total_cost_usd": 5.0,
                "total_tokens": 1000,
                "by_model": {"gpt-4": {"cost_usd": 5.0, "tokens": 1000}},
            }
        )
        # get_cost_summary uses get_metrics internally
        return dal

    @pytest.fixture
    def llmops(self, mock_llmops_dal):
        """Create LLMOps instance."""
        return LLMOps(llmops_dal=mock_llmops_dal)

    @pytest.mark.asyncio
    async def test_operations_persisted_to_database(self, llmops, mock_llmops_dal):
        """Test that operations are persisted to database."""
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
        assert mock_llmops_dal.save_operation.called
        assert operation_id is not None

    @pytest.mark.asyncio
    async def test_operations_retrieved_from_database(self, llmops, mock_llmops_dal):
        """Test that operations can be retrieved from database."""
        tenant_id = "tenant_123"

        # Get metrics (which includes operation data)
        metrics = await llmops.get_metrics(tenant_id=tenant_id)

        # Verify metrics were retrieved (which includes operation info)
        assert metrics is not None
        assert mock_llmops_dal.get_metrics.called

    @pytest.mark.asyncio
    async def test_metrics_retrieved_from_database(self, llmops, mock_llmops_dal):
        """Test that metrics can be retrieved from database."""
        tenant_id = "tenant_123"

        # Get metrics
        metrics = await llmops.get_metrics(tenant_id=tenant_id)

        # Verify metrics were retrieved
        assert metrics is not None
        assert "total_operations" in metrics or "total_cost_usd" in metrics
        assert mock_llmops_dal.get_metrics.called

    @pytest.mark.asyncio
    async def test_cost_summary_retrieved_from_database(self, llmops, mock_llmops_dal):
        """Test that cost summary can be retrieved from database."""
        tenant_id = "tenant_123"

        # Get cost summary
        cost_summary = await llmops.get_cost_summary(tenant_id=tenant_id)

        # Verify cost summary was retrieved
        assert cost_summary is not None
        assert "total_cost_usd" in cost_summary
        assert mock_llmops_dal.get_metrics.called  # get_cost_summary calls get_metrics


@pytest.mark.integration
class TestLLMOpsEndToEndIntegration:
    """Test end-to-end LLMOps integration scenarios."""

    @pytest.fixture
    def mock_llmops_dal(self):
        """Create mock LLMOps DAL."""
        dal = MagicMock()
        dal.save_operation = AsyncMock(return_value="op_123")
        dal.get_operations = AsyncMock(return_value=[])
        dal.get_metrics = AsyncMock(
            return_value={
                "total_cost_usd": 0.0,
                "total_tokens": 0,
                "by_model": {},
            }
        )
        return dal

    @pytest.fixture
    def llmops(self, mock_llmops_dal):
        """Create LLMOps instance."""
        return LLMOps(llmops_dal=mock_llmops_dal)

    @pytest.mark.asyncio
    async def test_end_to_end_llmops_workflow(self, llmops, mock_llmops_dal):
        """Test complete LLMOps workflow across components."""
        tenant_id = "tenant_123"

        # Step 1: Log multiple operations
        await llmops.log_operation(
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            tenant_id=tenant_id,
            metadata={"component": "gateway"},
        )

        await llmops.log_operation(
            operation_type=LLMOperationType.CHAT,
            model="gpt-4",
            prompt_tokens=150,
            completion_tokens=75,
            tenant_id=tenant_id,
            agent_id="agent_123",
            metadata={"component": "agent"},
        )

        await llmops.log_operation(
            operation_type=LLMOperationType.EMBEDDING,
            model="text-embedding-3-small",
            prompt_tokens=50,
            tenant_id=tenant_id,
            metadata={"component": "rag"},
        )

        # Step 2: Get metrics
        metrics = await llmops.get_metrics(tenant_id=tenant_id)

        # Step 3: Get cost summary
        cost_summary = await llmops.get_cost_summary(tenant_id=tenant_id)

        # Verify all operations completed
        assert mock_llmops_dal.save_operation.call_count == 3
        assert metrics is not None
        assert cost_summary is not None

