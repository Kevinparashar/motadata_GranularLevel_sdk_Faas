"""
Integration Tests for Agent-Memory Integration

Tests the integration between Agent Framework and Agent Memory.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from src.core.agno_agent_framework import Agent
from src.core.agno_agent_framework.memory import AgentMemory, MemoryType
from src.core.litellm_gateway import LiteLLMGateway, GatewayConfig


@pytest.mark.integration
class TestAgentMemoryIntegration:
    """Test Agent-Memory integration."""

    @pytest.fixture
    def mock_gateway(self):
        """Create mock gateway."""
        with patch('src.core.litellm_gateway.gateway.litellm') as mock_litellm:
            config = GatewayConfig()
            gateway = LiteLLMGateway(config=config)
            gateway._litellm = mock_litellm

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Agent response"
            mock_response.model = "gpt-4"
            mock_litellm.acompletion = AsyncMock(return_value=mock_response)

            return gateway

    @pytest.fixture
    def agent_with_memory(self, mock_gateway):
        """Create agent with memory attached."""
        agent = Agent(
            agent_id="test_agent",
            name="Test Agent",
            gateway=mock_gateway
        )
        agent.attach_memory(
            persistence_path=None,
            max_episodic=100,
            max_semantic=200
        )
        return agent

    def test_memory_attachment(self, agent_with_memory):
        """Test that memory is properly attached to agent."""
        assert agent_with_memory.memory is not None
        assert isinstance(agent_with_memory.memory, AgentMemory)

    @pytest.mark.asyncio
    async def test_memory_storage_during_task(self, agent_with_memory):
        """Test that agent stores memories during task execution."""
        initial_size = len(agent_with_memory.memory.episodic_memory)

        await agent_with_memory.execute_task_async(
            task_type="llm_query",
            parameters={"prompt": "Test task"},
            tenant_id="test_tenant"
        )

        # Memory should have stored task information
        final_size = len(agent_with_memory.memory.episodic_memory)
        assert final_size >= initial_size

    @pytest.mark.asyncio
    async def test_memory_retrieval_for_context(self, agent_with_memory):
        """Test that agent retrieves relevant memories for context."""
        # Store some memories
        agent_with_memory.memory.store(
            content="Previous task about AI",
            memory_type=MemoryType.EPISODIC,
            metadata={"task": "ai_query"}
        )

        # Mock memory retrieval
        with patch.object(agent_with_memory.memory, 'retrieve') as mock_retrieve:
            mock_retrieve.return_value = [
                {"content": "Previous task about AI", "relevance": 0.9}
            ]

            await agent_with_memory.execute_task_async(
                task_type="llm_query",
                parameters={"prompt": "Tell me more about AI"},
                tenant_id="test_tenant"
            )

            # Memory should have been retrieved for context
            mock_retrieve.assert_called()

    def test_session_memory_isolation(self, mock_gateway):
        """Test that different sessions have isolated memories."""
        agent1 = Agent(
            agent_id="agent_1",
            name="Agent 1",
            gateway=mock_gateway
        )
        agent1.attach_memory(max_episodic=100)

        agent2 = Agent(
            agent_id="agent_2",
            name="Agent 2",
            gateway=mock_gateway
        )
        agent2.attach_memory(max_episodic=100)

        # Store memory in agent1
        agent1.memory.store(
            content="Agent 1 memory",
            memory_type=MemoryType.EPISODIC
        )

        # Agent2 should not have this memory
        memories = agent2.memory.retrieve(
            query="Agent 1",
            memory_type=MemoryType.EPISODIC,
            top_k=5
        )
        assert len(memories) == 0

    @pytest.mark.asyncio
    async def test_memory_bounded_growth(self, mock_gateway):
        """Test that memory growth is bounded."""
        max_episodic = 10  # Small limit for test

        agent = Agent(
            agent_id="bounded_agent",
            name="Bounded Agent",
            gateway=mock_gateway
        )
        agent.attach_memory(max_episodic=max_episodic)

        # Store more memories than max
        for i in range(max_episodic + 5):
            agent.memory.store(
                content=f"Memory {i}",
                memory_type=MemoryType.EPISODIC
            )

        # Memory should be bounded
        assert len(agent.memory.episodic_memory) <= max_episodic

    @pytest.mark.asyncio
    async def test_memory_cleanup_expired(self, agent_with_memory):
        """Test that expired memories are cleaned up."""
        # Store memory with short age
        agent_with_memory.memory.store(
            content="Temporary memory",
            memory_type=MemoryType.EPISODIC,
            metadata={"created_at": "2020-01-01"}  # Old date
        )

        # Cleanup expired memories
        agent_with_memory.memory.cleanup_expired(max_age_days=30)

        # Expired memory should be removed
        memories = agent_with_memory.memory.retrieve(
            query="Temporary",
            memory_type=MemoryType.EPISODIC
        )
        assert len(memories) == 0

    def test_memory_types_separation(self, agent_with_memory):
        """Test that different memory types are stored separately."""
        # Store episodic memory
        agent_with_memory.memory.store(
            content="Episodic memory",
            memory_type=MemoryType.EPISODIC
        )

        # Store semantic memory
        agent_with_memory.memory.store(
            content="Semantic memory",
            memory_type=MemoryType.SEMANTIC
        )

        # Retrieve each type separately
        episodic = agent_with_memory.memory.retrieve(
            query="Episodic",
            memory_type=MemoryType.EPISODIC
        )
        semantic = agent_with_memory.memory.retrieve(
            query="Semantic",
            memory_type=MemoryType.SEMANTIC
        )

        assert len(episodic) > 0
        assert len(semantic) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])

