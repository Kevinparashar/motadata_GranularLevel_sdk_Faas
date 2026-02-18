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
        mock_pool = MagicMock()
        mock_pool.close = AsyncMock()
        mock_conn = AsyncMock()
        
        # Set up async context manager for pool.acquire()
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_pool.acquire = MagicMock(return_value=mock_context)
        
        mock_asyncpg_patcher = patch("src.core.postgresql_database.connection.asyncpg")
        mock_asyncpg = mock_asyncpg_patcher.start()
        mock_asyncpg.create_pool = AsyncMock(return_value=mock_pool)
        # Mock PostgresError for exception handling
        mock_asyncpg.PostgresError = Exception
        
        # Mock connection methods - create a dict-like object for fetchrow
        class MockRow:
            def __init__(self, data):
                self._data = data
            def __getitem__(self, key):
                return self._data[key]
            def keys(self):
                return self._data.keys()
            def __iter__(self):
                return iter(self._data)
        
        # Mock transaction context manager
        mock_transaction = MagicMock()
        mock_transaction.__aenter__ = AsyncMock(return_value=None)
        mock_transaction.__aexit__ = AsyncMock(return_value=None)
        mock_conn.transaction = MagicMock(return_value=mock_transaction)
        
        mock_conn.fetchrow = AsyncMock(return_value=MockRow({"id": 1, "title": "Test Document"}))
        mock_conn.fetch = AsyncMock(return_value=[])
        mock_conn.execute = AsyncMock(return_value="INSERT 0 1")

        db = DatabaseConnection(
            DatabaseConfig(
                host="localhost", port=5432, database="test", user="test", password="test"
            )
        )
        yield db
        mock_asyncpg_patcher.stop()

    @pytest.fixture
    def mock_gateway(self):
        """Create mock gateway."""
        config = GatewayConfig()
        # Patch internal initialization methods to prevent errors during instantiation
        with patch.object(LiteLLMGateway, "_initialize_kv_cache"), \
             patch.object(LiteLLMGateway, "_initialize_cache"), \
             patch.object(LiteLLMGateway, "_initialize_router"), \
             patch.object(LiteLLMGateway, "_initialize_deduplicator"):
            gateway = LiteLLMGateway(config=config)
            
            # Set required attributes that were skipped by patching
            gateway.kv_cache = None
            gateway.cache = None
            gateway.deduplicator = None
            
            # Create a mock router
            mock_router = MagicMock()
            
            # Mock embedding response - use a simple object with string model
            class EmbeddingDataItem:
                def __init__(self):
                    self.embedding = [0.1] * 1536
            
            class EmbeddingResponse:
                def __init__(self):
                    self.data = [EmbeddingDataItem()]
                    # Ensure model is a string, not a MagicMock
                    self._model = "text-embedding-3-small"
                
                @property
                def model(self):
                    return self._model
            
            mock_embedding_response = EmbeddingResponse()
            # Mock both async and sync embedding methods
            mock_router.aembedding = AsyncMock(return_value=mock_embedding_response)
            mock_router.embedding = MagicMock(return_value=mock_embedding_response)
            
            # Mock generation response
            mock_gen_response = MagicMock()
            mock_gen_response.choices = [MagicMock()]
            mock_gen_response.choices[0].message = MagicMock()
            mock_gen_response.choices[0].message.content = "Generated answer"
            mock_gen_response.choices[0].finish_reason = "stop"
            mock_gen_response.model = "gpt-4"
            # Usage needs to be an object with __dict__ attribute
            class UsageObject:
                def __init__(self):
                    self.prompt_tokens = 10
                    self.completion_tokens = 20
                    self.total_tokens = 30
            mock_gen_response.usage = UsageObject()
            mock_router.acompletion = AsyncMock(return_value=mock_gen_response)
            
            gateway.router = mock_router
            
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
        await rag_with_memory.memory.store(
            content="Previous query about AI",
            memory_type=MemoryType.EPISODIC,
            metadata={"query": "What is AI?", "answer": "AI is..."},
        )

        # Mock vector search
        with patch.object(rag_with_memory.vector_ops, "similarity_search") as mock_search:
            mock_search.return_value = []

            # Mock memory retrieval
            from src.core.agno_agent_framework.memory import MemoryItem
            with patch.object(rag_with_memory.memory, "retrieve", new_callable=AsyncMock) as mock_retrieve:
                mock_memory_item = MemoryItem(
                    memory_id="mem_1",
                    agent_id="rag_system",
                    memory_type=MemoryType.EPISODIC,
                    content="Previous query about AI",
                )
                mock_retrieve.return_value = [mock_memory_item]

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
        # Get initial memory count
        initial_memories = await rag_with_memory.memory.retrieve(
            memory_type=MemoryType.EPISODIC, limit=1000
        )
        initial_size = len(initial_memories)

        # Mock vector search - patch retriever.retrieve directly to avoid asyncio.run() issue
        with patch.object(rag_with_memory.retriever, "retrieve") as mock_retrieve:
            mock_retrieve.return_value = []

            await rag_with_memory.query_async(
                query="Test query",
                user_id="test_user",
                conversation_id="test_conv",
                tenant_id="test_tenant",
            )

            # Memory should have stored the query-answer pair
            final_memories = await rag_with_memory.memory.retrieve(
                memory_type=MemoryType.EPISODIC, limit=1000
            )
            final_size = len(final_memories)
            assert final_size > initial_size

    @pytest.mark.asyncio
    async def test_memory_context_enhances_prompt(self, rag_with_memory):
        """Test that memory context enhances the prompt sent to LLM."""
        # Store relevant memories
        await rag_with_memory.memory.store(
            content="User prefers technical explanations",
            memory_type=MemoryType.SEMANTIC,
            metadata={"preference": "technical"},
        )

        # Mock vector search - patch retriever.retrieve directly to avoid asyncio.run() issue
        with patch.object(rag_with_memory.retriever, "retrieve") as mock_retrieve:
            mock_retrieve.return_value = []

            # Mock generator to check if memory context is included
            with patch.object(rag_with_memory.generator, "generate_async", new_callable=AsyncMock) as mock_generate:
                mock_generate.return_value = {"response": "Enhanced answer", "model": "gpt-4", "usage": None}

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
        with patch.object(rag_with_memory.retriever, "retrieve") as mock_retrieve:
            mock_retrieve.return_value = []

            await rag_with_memory.query_async(
                query="What is Python?",
                user_id=user_id,
                conversation_id=conversation_id,
                tenant_id="test_tenant",
            )

        # Second query in same conversation
        with patch.object(rag_with_memory.retriever, "retrieve") as mock_retrieve:
            mock_retrieve.return_value = []

            # Mock memory retrieval to verify it's called with conversation context
            with patch.object(rag_with_memory.memory, "retrieve", new_callable=AsyncMock) as mock_memory_retrieve:
                mock_memory_retrieve.return_value = []

                await rag_with_memory.query_async(
                    query="How do I use it?",
                    user_id=user_id,
                    conversation_id=conversation_id,
                    tenant_id="test_tenant",
                )

                # Memory should retrieve context from same conversation
                mock_memory_retrieve.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
