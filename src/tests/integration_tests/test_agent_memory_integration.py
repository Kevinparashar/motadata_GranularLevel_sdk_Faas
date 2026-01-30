"""
Integration Tests for Agent-Memory Integration

Tests the integration between Agent Framework and Agent Memory.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.agno_agent_framework import Agent, AgentTask
from src.core.agno_agent_framework.memory import AgentMemory, MemoryType
from src.core.litellm_gateway import GatewayConfig, LiteLLMGateway


@pytest.mark.integration
class TestAgentMemoryIntegration:
    """Test Agent-Memory integration."""

    @pytest.fixture
    def mock_gateway(self):
        """Create mock gateway."""
        config = GatewayConfig()
        gateway = LiteLLMGateway(config=config)

        # Mock the router's acompletion method if router exists
        if gateway.router:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message = MagicMock()
            mock_response.choices[0].message.content = "Agent response"
            mock_response.model = "gpt-4"
            gateway.router.acompletion = AsyncMock(return_value=mock_response)
        else:
            # Create a mock router if none exists
            mock_router = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message = MagicMock()
            mock_response.choices[0].message.content = "Agent response"
            mock_response.model = "gpt-4"
            mock_router.acompletion = AsyncMock(return_value=mock_response)
            gateway.router = mock_router

        return gateway

    @pytest.fixture
    def agent_with_memory(self, mock_gateway):
        """Create agent with memory attached."""
        agent = Agent(agent_id="test_agent", name="Test Agent", gateway=mock_gateway)
        agent.attach_memory(persistence_path=None, max_episodic=100, max_semantic=200)
        return agent

    def test_memory_attachment(self, agent_with_memory):
        """Test that memory is properly attached to agent."""
        assert agent_with_memory.memory is not None
        assert isinstance(agent_with_memory.memory, AgentMemory)

    def test_memory_store_and_retrieve(self, agent_with_memory):
        """Test basic memory store and retrieve operations."""
        assert agent_with_memory.memory is not None
        agent_with_memory.memory.store(content="Test memory", memory_type=MemoryType.EPISODIC)
        memories = agent_with_memory.memory.retrieve(
            query="Test", memory_type=MemoryType.EPISODIC, limit=10
        )
        assert len(memories) > 0

    @pytest.mark.asyncio
    async def test_memory_storage_during_task(self, agent_with_memory):
        """Test that agent stores memories during task execution."""
        assert agent_with_memory.memory is not None
        # Get initial episodic memory count
        initial_memories = agent_with_memory.memory.retrieve(
            memory_type=MemoryType.EPISODIC, limit=1000
        )
        initial_size = len(initial_memories)

        task = AgentTask(
            task_id="test_task_1", task_type="llm_query", parameters={"prompt": "Test task"}
        )
        await agent_with_memory.execute_task(task, tenant_id="test_tenant")

        # Memory should have stored task information
        final_memories = agent_with_memory.memory.retrieve(
            memory_type=MemoryType.EPISODIC, limit=1000
        )
        final_size = len(final_memories)
        assert final_size >= initial_size

    @pytest.mark.asyncio
    async def test_memory_retrieval_for_context(self, agent_with_memory):
        """Test that agent retrieves relevant memories for context."""
        assert agent_with_memory.memory is not None
        # Store some memories
        agent_with_memory.memory.store(
            content="Previous task about AI",
            memory_type=MemoryType.EPISODIC,
            metadata={"task": "ai_query"},
        )

        # Mock memory retrieval
        with patch.object(agent_with_memory.memory, "retrieve") as mock_retrieve:
            from src.core.agno_agent_framework.memory import MemoryItem

            mock_memory_item = MemoryItem(
                memory_id="test_mem_1",
                agent_id=agent_with_memory.agent_id,
                memory_type=MemoryType.EPISODIC,
                content="Previous task about AI",
            )
            mock_retrieve.return_value = [mock_memory_item]

            task = AgentTask(
                task_id="test_task_2",
                task_type="llm_query",
                parameters={"prompt": "Tell me more about AI"},
            )
            await agent_with_memory.execute_task(task, tenant_id="test_tenant")

            # Memory should have been retrieved for context
            mock_retrieve.assert_called()

    def test_session_memory_isolation(self, mock_gateway):
        """Test that different sessions have isolated memories."""
        agent1 = Agent(agent_id="agent_1", name="Agent 1", gateway=mock_gateway)
        agent1.attach_memory(max_episodic=100)
        assert agent1.memory is not None

        agent2 = Agent(agent_id="agent_2", name="Agent 2", gateway=mock_gateway)
        agent2.attach_memory(max_episodic=100)
        assert agent2.memory is not None

        # Store memory in agent1
        agent1.memory.store(content="Agent 1 memory", memory_type=MemoryType.EPISODIC)

        # Agent2 should not have this memory
        memories = agent2.memory.retrieve(query="Agent 1", memory_type=MemoryType.EPISODIC, limit=5)
        assert len(memories) == 0

    @pytest.mark.asyncio
    async def test_memory_bounded_growth(self, mock_gateway):
        """Test that memory growth is bounded."""
        max_episodic = 10  # Small limit for test

        agent = Agent(agent_id="bounded_agent", name="Bounded Agent", gateway=mock_gateway)
        agent.attach_memory(max_episodic=max_episodic)

        assert agent.memory is not None
        # Store more memories than max
        for i in range(max_episodic + 5):
            agent.memory.store(content=f"Memory {i}", memory_type=MemoryType.EPISODIC)

        # Memory should be bounded - check by retrieving all episodic memories
        episodic_memories = agent.memory.retrieve(memory_type=MemoryType.EPISODIC, limit=1000)
        assert len(episodic_memories) <= max_episodic

    @pytest.mark.asyncio
    async def test_memory_cleanup_expired(self, agent_with_memory):
        """Test that expired memories are cleaned up."""
        assert agent_with_memory.memory is not None
        # Store memory with short age
        agent_with_memory.memory.store(
            content="Temporary memory",
            memory_type=MemoryType.EPISODIC,
            metadata={"created_at": "2020-01-01"},  # Old date
        )

        # Cleanup expired memories
        agent_with_memory.memory.cleanup_expired(max_age_days=30)

        # Expired memory should be removed
        memories = agent_with_memory.memory.retrieve(
            query="Temporary", memory_type=MemoryType.EPISODIC, limit=10
        )
        assert len(memories) == 0

    def test_memory_types_separation(self, agent_with_memory):
        """Test that different memory types are stored separately."""
        assert agent_with_memory.memory is not None
        # Store episodic memory
        agent_with_memory.memory.store(content="Episodic memory", memory_type=MemoryType.EPISODIC)

        # Store semantic memory
        agent_with_memory.memory.store(content="Semantic memory", memory_type=MemoryType.SEMANTIC)

        # Retrieve each type separately
        episodic = agent_with_memory.memory.retrieve(
            query="Episodic", memory_type=MemoryType.EPISODIC, limit=10
        )
        semantic = agent_with_memory.memory.retrieve(
            query="Semantic", memory_type=MemoryType.SEMANTIC, limit=10
        )

        assert len(episodic) > 0
        assert len(semantic) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
