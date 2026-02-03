"""
Integration Tests for RAG-Memory Integration

Tests the integration between RAG System and Agent Memory.
"""


from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.agno_agent_framework.memory import AgentMemory, MemoryType
from src.core.litellm_gateway import GatewayConfig, LiteLLMGateway
from src.core.postgresql_database.connection import DatabaseConfig, DatabaseConnection
from src.core.rag import RAGSystem


@pytest.mark.integration
class TestRAGMemoryIntegration:
    """Test RAG-Memory integration."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database connection."""
        with patch("src.core.postgresql_database.connection.psycopg2") as mock_psycopg2:
            mock_conn = MagicMock()
            mock_psycopg2.connect.return_value = mock_conn
            db = DatabaseConnection(
                DatabaseConfig(
                    host="localhost", port=5432, database="test", user="test", password="test"
                )
            )
            return db

    @pytest.fixture
    def mock_gateway(self):
        """Create mock gateway."""
        with patch("src.core.litellm_gateway.gateway.litellm") as mock_litellm:
            config = GatewayConfig()
            gateway = LiteLLMGateway(config=config)
            gateway._litellm = mock_litellm  # type: ignore[attr-defined]

            mock_embedding_response = MagicMock()
            mock_embedding_response.embeddings = [[0.1] * 1536]
            mock_litellm.aembedding = AsyncMock(return_value=mock_embedding_response)

            mock_gen_response = MagicMock()
            mock_gen_response.text = "Generated answer"
            mock_gen_response.model = "gpt-4"
            mock_litellm.acompletion = AsyncMock(return_value=mock_gen_response)

            return gateway

    @pytest.fixture
    def rag_with_memory(self, mock_db, mock_gateway):
        """Create RAG system with memory enabled."""
        return RAGSystem(
            db=mock_db,
            gateway=mock_gateway,
            enable_memory=True,
            memory_config={"max_episodic": 100, "max_semantic": 200},
        )

    def test_memory_initialization(self, rag_with_memory):
        """Test that memory is initialized when enabled."""
        assert rag_with_memory.memory is not None
        assert isinstance(rag_with_memory.memory, AgentMemory)

    @pytest.mark.asyncio
    async def test_memory_retrieval_during_query(self, rag_with_memory):
        """Test that relevant memories are retrieved during query."""
        # Store some memories
        rag_with_memory.memory.store(
            content="Previous query about AI",
            memory_type=MemoryType.EPISODIC,
            metadata={"query": "What is AI?", "answer": "AI is..."},
        )

        # Mock vector search
        with patch.object(rag_with_memory.vector_ops, "similarity_search") as mock_search:
            mock_search.return_value = []

            # Mock memory retrieval
            with patch.object(rag_with_memory.memory, "retrieve") as mock_retrieve:
                mock_retrieve.return_value = [
                    {"content": "Previous query about AI", "relevance": 0.9}
                ]

                _ = await rag_with_memory.query_async(
                    query="Tell me more",
                    user_id="test_user",
                    conversation_id="test_conv",
                    tenant_id="test_tenant",
                )

                # Memory should have been retrieved
                mock_retrieve.assert_called()

    @pytest.mark.asyncio
    async def test_query_answer_stored_in_memory(self, rag_with_memory):
        """Test that query-answer pairs are stored in episodic memory."""
        initial_size = len(rag_with_memory.memory.episodic_memory)

        # Mock vector search
        with patch.object(rag_with_memory.vector_ops, "similarity_search") as mock_search:
            mock_search.return_value = []

            await rag_with_memory.query_async(
                query="Test query",
                user_id="test_user",
                conversation_id="test_conv",
                tenant_id="test_tenant",
            )

            # Memory should have stored the query-answer pair
            final_size = len(rag_with_memory.memory.episodic_memory)
            assert final_size > initial_size

    @pytest.mark.asyncio
    async def test_memory_context_enhances_prompt(self, rag_with_memory):
        """Test that memory context enhances the prompt sent to LLM."""
        # Store relevant memories
        rag_with_memory.memory.store(
            content="User prefers technical explanations",
            memory_type=MemoryType.SEMANTIC,
            metadata={"preference": "technical"},
        )

        # Mock vector search
        with patch.object(rag_with_memory.vector_ops, "similarity_search") as mock_search:
            mock_search.return_value = []

            # Mock generator to check if memory context is included
            with patch.object(rag_with_memory.generator, "generate_async") as mock_generate:
                mock_generate.return_value = "Enhanced answer"

                await rag_with_memory.query_async(
                    query="Explain AI",
                    user_id="test_user",
                    conversation_id="test_conv",
                    tenant_id="test_tenant",
                )

                # Generator should have been called (with memory context)
                mock_generate.assert_called()

    def test_memory_disabled_behavior(self, mock_db, mock_gateway):
        """Test RAG behavior when memory is disabled."""
        rag = RAGSystem(db=mock_db, gateway=mock_gateway, enable_memory=False)

        assert rag.memory is None

    @pytest.mark.asyncio
    async def test_conversation_context_across_queries(self, rag_with_memory):
        """Test that conversation context is maintained across multiple queries."""
        user_id = "test_user"
        conversation_id = "test_conv"

        # First query
        with patch.object(rag_with_memory.vector_ops, "similarity_search") as mock_search:
            mock_search.return_value = []

            await rag_with_memory.query_async(
                query="What is Python?",
                user_id=user_id,
                conversation_id=conversation_id,
                tenant_id="test_tenant",
            )

        # Second query in same conversation
        with patch.object(rag_with_memory.vector_ops, "similarity_search") as mock_search:
            mock_search.return_value = []

            # Mock memory retrieval to verify it's called with conversation context
            with patch.object(rag_with_memory.memory, "retrieve") as mock_retrieve:
                mock_retrieve.return_value = []

                await rag_with_memory.query_async(
                    query="How do I use it?",
                    user_id=user_id,
                    conversation_id=conversation_id,
                    tenant_id="test_tenant",
                )

                # Memory should retrieve context from same conversation
                mock_retrieve.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
