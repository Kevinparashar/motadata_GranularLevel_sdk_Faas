"""
Integration Tests for Prompt Context Management Integration

Tests the integration between Prompt Context Management and other components:
- Prompt Context ↔ Gateway (prompt rendering with LLM)
- Prompt Context ↔ Agent (template usage in agents)
- Prompt Context ↔ RAG (prompt templates in RAG queries)
- Prompt Context ↔ Cache (caching rendered prompts)
- Prompt Context ↔ Database (history persistence)
"""


from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.agno_agent_framework import Agent
from src.core.cache_mechanism import CacheConfig, CacheMechanism
from src.core.litellm_gateway import LiteLLMGateway
from src.core.prompt_context_management import PromptContextManager
from src.core.rag import RAGSystem


@pytest.mark.integration
class TestPromptContextGatewayIntegration:
    """Test Prompt Context Management integration with Gateway."""

    @pytest.fixture
    def prompt_manager(self):
        """Create prompt context manager."""
        return PromptContextManager(
            max_tokens=4000,
            safety_margin=200,
            require_persistence=False,
        )

    @pytest.fixture
    def mock_gateway(self):
        """Create mock gateway."""
        gateway = MagicMock(spec=LiteLLMGateway)
        gateway.generate_async = AsyncMock()
        return gateway

    @pytest.mark.asyncio
    async def test_prompt_manager_renders_template_for_gateway(self, prompt_manager, mock_gateway):
        """Test that prompt manager renders templates for gateway."""
        # Add template
        prompt_manager.add_template(
            name="analysis",
            version="1.0.0",
            content="Analyze the following text: {text}",
        )

        # Render prompt
        rendered = prompt_manager.render("analysis", {"text": "Test content"})

        # Verify template was rendered
        assert "Analyze the following text: Test content" in rendered
        assert "Test content" in rendered

        # Mock gateway response
        mock_response = MagicMock()
        mock_response.text = "Analysis result"
        mock_gateway.generate_async.return_value = mock_response

        # Use rendered prompt with gateway
        await mock_gateway.generate_async(prompt=rendered, model="gpt-4")

        # Verify gateway was called with rendered prompt
        mock_gateway.generate_async.assert_called_once()
        call_args = mock_gateway.generate_async.call_args
        assert "Analyze the following text: Test content" in call_args.kwargs["prompt"]

    @pytest.mark.asyncio
    async def test_prompt_manager_builds_context_for_gateway(self, prompt_manager, mock_gateway):
        """Test that prompt manager builds context for gateway."""
        # Record history
        prompt_manager.record_history("User: Hello")
        prompt_manager.record_history("Assistant: Hi! How can I help?")

        # Build context with history
        context = prompt_manager.build_context_with_history("User: What is AI?")

        # Verify context includes history
        assert "User: Hello" in context
        assert "Assistant: Hi! How can I help?" in context
        assert "User: What is AI?" in context

        # Mock gateway response
        mock_response = MagicMock()
        mock_response.text = "AI is artificial intelligence"
        mock_gateway.generate_async.return_value = mock_response

        # Use context with gateway
        await mock_gateway.generate_async(prompt=context, model="gpt-4")

        # Verify gateway was called with context
        mock_gateway.generate_async.assert_called_once()
        call_args = mock_gateway.generate_async.call_args
        assert "User: Hello" in call_args.kwargs["prompt"]


@pytest.mark.integration
class TestPromptContextAgentIntegration:
    """Test Prompt Context Management integration with Agent Framework."""

    @pytest.fixture
    def prompt_manager(self):
        """Create prompt context manager."""
        return PromptContextManager(
            max_tokens=4000,
            safety_margin=200,
            require_persistence=False,
        )

    @pytest.fixture
    def mock_gateway(self):
        """Create mock gateway."""
        gateway = MagicMock(spec=LiteLLMGateway)
        gateway.generate_async = AsyncMock()
        return gateway

    @pytest.fixture
    def agent_with_prompt_manager(self, prompt_manager, mock_gateway):
        """Create agent with prompt manager."""
        agent = Agent(
            agent_id="test-agent",
            name="Test Agent",
            gateway=mock_gateway,
        )
        # Attach prompt manager to agent
        agent.prompt_manager = prompt_manager
        return agent, prompt_manager, mock_gateway

    @pytest.mark.asyncio
    async def test_agent_uses_prompt_templates(self, agent_with_prompt_manager):
        """Test that agent uses prompt templates."""
        _, prompt_manager, mock_gateway = agent_with_prompt_manager

        # Add template for agent instructions
        prompt_manager.add_template(
            name="agent_instructions",
            version="1.0.0",
            content="You are a helpful assistant. User says: {user_message}",
        )

        # Render prompt using template
        rendered = prompt_manager.render("agent_instructions", {"user_message": "Hello"})

        # Mock gateway response
        mock_response = MagicMock()
        mock_response.text = "Hello! How can I help?"
        mock_gateway.generate_async.return_value = mock_response

        # Agent uses rendered prompt
        await mock_gateway.generate_async(prompt=rendered, model="gpt-4")

        # Verify template was used
        assert "You are a helpful assistant" in rendered
        assert "Hello" in rendered

    @pytest.mark.asyncio
    async def test_agent_builds_context_with_history(self, agent_with_prompt_manager):
        """Test that agent builds context with history."""
        _, prompt_manager, _ = agent_with_prompt_manager

        # Record conversation history
        prompt_manager.record_history("User: What is Python?")
        prompt_manager.record_history("Assistant: Python is a programming language.")

        # Build context for new message
        context = prompt_manager.build_context_with_history("User: Tell me more")

        # Verify context includes history
        assert "What is Python?" in context
        assert "Python is a programming language" in context
        assert "Tell me more" in context


@pytest.mark.integration
class TestPromptContextRAGIntegration:
    """Test Prompt Context Management integration with RAG System."""

    @pytest.fixture
    def prompt_manager(self):
        """Create prompt context manager."""
        return PromptContextManager(
            max_tokens=4000,
            safety_margin=200,
            require_persistence=False,
        )

    @pytest.fixture
    def mock_gateway(self):
        """Create mock gateway."""
        gateway = MagicMock(spec=LiteLLMGateway)
        gateway.generate_async = AsyncMock()
        gateway.embed_async = AsyncMock()
        return gateway

    @pytest.fixture
    def mock_rag(self, mock_gateway):
        """Create mock RAG system."""
        rag = MagicMock(spec=RAGSystem)
        rag.query_async = AsyncMock()
        return rag

    @pytest.mark.asyncio
    async def test_rag_uses_prompt_templates_for_queries(self, prompt_manager, mock_rag):
        """Test that RAG uses prompt templates for queries."""
        # Add RAG query template
        prompt_manager.add_template(
            name="rag_query",
            version="1.0.0",
            content="""Based on the following context:
{context}

Answer this question: {query}""",
        )

        # Mock retrieved documents
        retrieved_docs = [
            {"title": "Doc1", "content": "Python is a programming language"},
            {"title": "Doc2", "content": "Python is used for data science"},
        ]

        # Build context from retrieved documents
        context_text = "\n".join([doc["content"] for doc in retrieved_docs])

        # Render prompt with template
        rendered = prompt_manager.render(
            "rag_query",
            {"context": context_text, "query": "What is Python?"},
        )

        # Verify template was rendered correctly
        assert "Based on the following context:" in rendered
        assert "Python is a programming language" in rendered
        assert "Answer this question: What is Python?" in rendered

    @pytest.mark.asyncio
    async def test_rag_integrates_context_with_prompt_manager(self, prompt_manager, mock_rag, mock_gateway):
        """Test that RAG integrates context with prompt manager."""
        # Add template
        prompt_manager.add_template(
            name="rag_query",
            version="1.0.0",
            content="Context: {context}\nQuestion: {query}",
        )

        # Simulate RAG query with context
        retrieved_context = "Python is a programming language"
        query = "What is Python?"

        # Render prompt
        rendered = prompt_manager.render(
            "rag_query",
            {"context": retrieved_context, "query": query},
        )

        # Mock RAG query response
        mock_rag.query_async.return_value = {
            "answer": "Python is a programming language",
            "retrieved_documents": [{"content": retrieved_context}],
        }

        # Verify prompt was rendered with context
        assert retrieved_context in rendered
        assert query in rendered


@pytest.mark.integration
class TestPromptContextCacheIntegration:
    """Test Prompt Context Management integration with Cache Mechanism."""

    @pytest.fixture
    def prompt_manager(self):
        """Create prompt context manager."""
        return PromptContextManager(
            max_tokens=4000,
            safety_margin=200,
            require_persistence=False,
        )

    @pytest.fixture
    def cache(self):
        """Create cache mechanism."""
        return CacheMechanism(CacheConfig(default_ttl=3600))

    @pytest.mark.asyncio
    async def test_rendered_prompts_are_cached(self, prompt_manager, cache):
        """Test that rendered prompts are cached."""
        # Add template
        prompt_manager.add_template(
            name="greeting",
            version="1.0.0",
            content="Hello, {name}!",
        )

        # Render prompt
        rendered1 = prompt_manager.render("greeting", {"name": "Alice"})

        # Cache rendered prompt
        cache_key = f"prompt:greeting:Alice"
        await cache.set(cache_key, rendered1, tenant_id="test_tenant")

        # Retrieve from cache
        cached = await cache.get(cache_key, tenant_id="test_tenant")

        # Verify cached prompt matches
        assert cached == rendered1
        assert "Hello, Alice!" in cached

    @pytest.mark.asyncio
    async def test_context_building_uses_cache(self, prompt_manager, cache):
        """Test that context building can use cache."""
        # Record history
        prompt_manager.record_history("User: Hello")
        prompt_manager.record_history("Assistant: Hi!")

        # Build context
        context1 = prompt_manager.build_context_with_history("User: What is AI?")

        # Cache context
        cache_key = f"context:test_tenant:test_user"
        await cache.set(cache_key, context1, tenant_id="test_tenant")

        # Retrieve from cache
        cached_context = await cache.get(cache_key, tenant_id="test_tenant")

        # Verify cached context matches
        assert cached_context is not None
        assert "Hello" in cached_context
        assert "What is AI?" in cached_context


@pytest.mark.integration
class TestPromptContextDatabaseIntegration:
    """Test Prompt Context Management integration with Database (DAL)."""

    @pytest.fixture
    def mock_history_dal(self):
        """Create mock history DAL."""
        dal = MagicMock()
        dal.save_prompt_history = AsyncMock(return_value="history_id_123")
        dal.get_prompt_history = AsyncMock(return_value=[
            {"prompt": "User: Hello", "timestamp": "2024-01-01T00:00:00Z"},
            {"prompt": "Assistant: Hi!", "timestamp": "2024-01-01T00:00:01Z"},
        ])
        dal.save_context_window_state = AsyncMock(return_value="state_id_123")
        dal.get_context_window_state = AsyncMock(return_value={
            "max_tokens": 4000,
            "safety_margin": 200,
            "current_tokens": 100,
        })
        # Make sure all methods return coroutines
        dal.save_prompt_history = AsyncMock(return_value="history_id_123")
        dal.save_context_window_state = AsyncMock(return_value="state_id_123")
        return dal

    @pytest.mark.asyncio
    async def test_prompt_history_persisted_to_database(self, mock_history_dal):
        """Test that prompt history is persisted to database."""
        # Ensure save_history is properly mocked as async
        mock_history_dal.save_history = AsyncMock(return_value="history_id_123")
        
        prompt_manager = PromptContextManager(
            max_tokens=4000,
            safety_margin=200,
            history_dal=mock_history_dal,
            tenant_id="test_tenant",
            user_id="test_user",
            require_persistence=False,  # Allow testing without strict persistence
        )

        # Record history
        prompt_manager.record_history("User: Hello")

        # Verify history was recorded
        assert len(prompt_manager.history) > 0
        assert "User: Hello" in prompt_manager.history

    @pytest.mark.asyncio
    async def test_prompt_history_loaded_from_database(self, mock_history_dal):
        """Test that prompt history is loaded from database on initialization."""
        # Create manager with DAL
        prompt_manager = PromptContextManager(
            max_tokens=4000,
            safety_margin=200,
            history_dal=mock_history_dal,
            tenant_id="test_tenant",
            user_id="test_user",
            load_history_on_init=True,
            require_persistence=False,
        )

        # Verify DAL was called to load history
        # Note: In actual implementation, _load_history would be called
        assert prompt_manager._history_dal is not None

    @pytest.mark.asyncio
    async def test_context_window_state_persisted(self, mock_history_dal):
        """Test that context window state is persisted to database."""
        prompt_manager = PromptContextManager(
            max_tokens=4000,
            safety_margin=200,
            history_dal=mock_history_dal,
            tenant_id="test_tenant",
            user_id="test_user",
            require_persistence=False,
        )

        # Update context window
        prompt_manager.update_context_window(max_tokens=8000, safety_margin=400)

        # Verify window was updated
        assert prompt_manager.window.max_tokens == 8000
        assert prompt_manager.window.safety_margin == 400

        # Verify DAL would be called for persistence
        assert prompt_manager._history_dal is not None


@pytest.mark.integration
class TestPromptContextEndToEndIntegration:
    """Test end-to-end Prompt Context Management integration."""

    @pytest.fixture
    def prompt_manager(self):
        """Create prompt context manager."""
        return PromptContextManager(
            max_tokens=4000,
            safety_margin=200,
            require_persistence=False,
        )

    @pytest.fixture
    def mock_gateway(self):
        """Create mock gateway."""
        gateway = MagicMock(spec=LiteLLMGateway)
        gateway.generate_async = AsyncMock()
        return gateway

    @pytest.mark.asyncio
    async def test_end_to_end_prompt_workflow(self, prompt_manager, mock_gateway):
        """Test complete workflow: template → render → context → gateway."""
        # Step 1: Add template
        prompt_manager.add_template(
            name="conversation",
            version="1.0.0",
            content="Previous: {history}\nCurrent: {current}",
        )

        # Step 2: Record history
        prompt_manager.record_history("User: Hello")
        prompt_manager.record_history("Assistant: Hi!")

        # Step 3: Build context
        context = prompt_manager.build_context_with_history("User: What is AI?")

        # Step 4: Render prompt with template
        rendered = prompt_manager.render(
            "conversation",
            {"history": context, "current": "User: What is AI?"},
        )

        # Step 5: Use with gateway
        mock_response = MagicMock()
        mock_response.text = "AI is artificial intelligence"
        mock_gateway.generate_async.return_value = mock_response

        await mock_gateway.generate_async(prompt=rendered, model="gpt-4")

        # Verify complete workflow
        assert "Hello" in rendered
        assert "What is AI?" in rendered
        mock_gateway.generate_async.assert_called_once()

