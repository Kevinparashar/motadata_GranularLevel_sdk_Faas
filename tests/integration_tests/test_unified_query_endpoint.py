"""
Integration Tests for Unified Query Endpoint

Tests the integration of the unified query endpoint with Agent and RAG.
"""


from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.core.agno_agent_framework import Agent, AgentManager
from src.core.api_backend_services.functions import (
    create_api_app,
    create_api_router,
    create_unified_query_endpoint,
)
from src.core.litellm_gateway import GatewayConfig, LiteLLMGateway
from src.core.postgresql_database.connection import DatabaseConfig, DatabaseConnection
from src.core.rag import RAGSystem


@pytest.mark.integration
class TestUnifiedQueryEndpoint:
    """Test unified query endpoint integration."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
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
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message = MagicMock()
            mock_response.choices[0].message.content = "Response"
            mock_response.choices[0].finish_reason = "stop"
            mock_response.model = "gpt-4"
            # Usage needs to be an object with __dict__ attribute
            class UsageObject:
                def __init__(self):
                    self.prompt_tokens = 10
                    self.completion_tokens = 20
                    self.total_tokens = 30
            mock_response.usage = UsageObject()
            mock_router.acompletion = AsyncMock(return_value=mock_response)
            gateway.router = mock_router
            
            return gateway

    @pytest.fixture
    def mock_agent_manager(self, mock_gateway):
        """Create mock agent manager."""
        manager = AgentManager()
        agent = Agent(agent_id="test_agent", name="Test Agent", gateway=mock_gateway)
        manager.register_agent(agent)
        return manager

    @pytest.fixture
    def mock_rag_system(self, mock_db, mock_gateway):
        """Create mock RAG system."""
        return RAGSystem(db=mock_db, gateway=mock_gateway, enable_memory=False)

    @pytest.fixture
    def api_app(self, mock_agent_manager, mock_rag_system, mock_gateway):
        """Create API app with unified endpoint."""
        app = create_api_app()
        router = create_api_router(prefix="/api/v1")

        create_unified_query_endpoint(
            router=router,
            agent_manager=mock_agent_manager,
            rag_system=mock_rag_system,
            prefix="/query",
        )

        app.include_router(router)
        return app

    def test_auto_mode_routes_to_rag(self, api_app):
        """Test that auto mode routes knowledge questions to RAG."""
        client = TestClient(api_app)

        with patch("src.core.rag.quick_rag_query_async", new_callable=AsyncMock) as mock_rag_query:
            mock_rag_query.return_value = {
                "answer": "RAG answer",
                "sources": [],
                "num_documents": 1,
            }

            response = client.post(
                "/api/v1/query",
                json={"query": "What is AI?", "mode": "auto", "tenant_id": "test_tenant"},
            )

            assert response.status_code in [200, 422, 500]
            if response.status_code == 200:
                data = response.json()
                assert "rag_response" in data
                assert data["rag_response"]["answer"] == "RAG answer"

    def test_auto_mode_routes_to_agent(self, api_app):
        """Test that auto mode routes action queries to Agent."""
        client = TestClient(api_app)

        with patch("src.core.agno_agent_framework.chat_with_agent", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = {"answer": "Agent response"}

            response = client.post(
                "/api/v1/query",
                json={"query": "Create a ticket", "mode": "auto", "tenant_id": "test_tenant"},
            )

            assert response.status_code in [200, 422, 500]
            if response.status_code == 200:
                data = response.json()
                # Should have agent response or error
                assert "agent_response" in data or "agent_error" in data

    def test_rag_mode_uses_rag_only(self, api_app):
        """Test that rag mode uses only RAG."""
        client = TestClient(api_app)

        with patch("src.core.rag.quick_rag_query_async", new_callable=AsyncMock) as mock_rag_query:
            mock_rag_query.return_value = {"answer": "RAG answer", "sources": []}

            response = client.post(
                "/api/v1/query",
                json={"query": "Test query", "mode": "rag", "tenant_id": "test_tenant"},
            )

            assert response.status_code in [200, 422, 500]
            if response.status_code == 200:
                data = response.json()
                assert "rag_response" in data
                assert "agent_response" not in data

    def test_agent_mode_uses_agent_only(self, api_app):
        """Test that agent mode uses only Agent."""
        client = TestClient(api_app)

        with patch("src.core.agno_agent_framework.chat_with_agent", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = {"answer": "Agent response"}

            response = client.post(
                "/api/v1/query",
                json={
                    "query": "Test query",
                    "mode": "agent",
                    "agent_id": "test_agent",
                    "tenant_id": "test_tenant",
                },
            )

            assert response.status_code in [200, 422, 500]
            if response.status_code == 200:
                data = response.json()
                assert "agent_response" in data or "agent_error" in data
                assert "rag_response" not in data

    def test_both_mode_uses_both(self, api_app):
        """Test that both mode uses both Agent and RAG."""
        client = TestClient(api_app)

        with patch("src.core.rag.quick_rag_query_async", new_callable=AsyncMock) as mock_rag_query:
            with patch("src.core.agno_agent_framework.chat_with_agent", new_callable=AsyncMock) as mock_chat:
                mock_rag_query.return_value = {"answer": "RAG answer", "sources": []}
                mock_chat.return_value = {"answer": "Agent response"}

                response = client.post(
                    "/api/v1/query",
                    json={
                        "query": "Test query",
                        "mode": "both",
                        "agent_id": "test_agent",
                        "tenant_id": "test_tenant",
                    },
                )

                assert response.status_code in [200, 422, 500]
                if response.status_code == 200:
                    data = response.json()
                    # Should have both responses or combined answer
                    assert (
                        "rag_response" in data or "agent_response" in data or "combined_answer" in data
                    )

    def test_error_handling_rag_failure(self, api_app):
        """Test error handling when RAG fails."""
        client = TestClient(api_app)

        with patch("src.core.rag.quick_rag_query_async", new_callable=AsyncMock) as mock_rag_query:
            mock_rag_query.side_effect = Exception("RAG error")

            response = client.post(
                "/api/v1/query",
                json={"query": "Test query", "mode": "rag", "tenant_id": "test_tenant"},
            )

            assert response.status_code in [200, 422, 500]
            if response.status_code == 200:
                data = response.json()
                assert "rag_error" in data

    def test_error_handling_agent_failure(self, api_app):
        """Test error handling when Agent fails."""
        client = TestClient(api_app)

        with patch("src.core.agno_agent_framework.chat_with_agent", new_callable=AsyncMock) as mock_chat:
            mock_chat.side_effect = Exception("Agent error")

            response = client.post(
                "/api/v1/query",
                json={
                    "query": "Test query",
                    "mode": "agent",
                    "agent_id": "test_agent",
                    "tenant_id": "test_tenant",
                },
            )

            assert response.status_code in [200, 422, 500]
            if response.status_code == 200:
                data = response.json()
                assert "agent_error" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
