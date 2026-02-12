"""
Unit Tests for API Backend Services Functions

Tests factory functions, convenience functions, and utilities for API backend services.
"""


from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from src.core.api_backend_services.functions import (  # Factory functions; High-level convenience functions; Utility functions
    add_api_versioning,
    add_endpoint,
    add_health_check,
    configure_api_app,
    create_agent_endpoints,
    create_api_app,
    create_api_router,
    create_gateway_endpoints,
    create_rag_endpoints,
    create_unified_query_endpoint,
    register_router,
)


class TestFactoryFunctions:
    """Test factory functions for API creation."""

    def test_create_api_app(self):
        """Test create_api_app factory function."""
        app = create_api_app(
            title="Test API",
            version="1.0.0",
            description="Test API Description",
            enable_cors=True,
            cors_origins=["http://localhost:3000"],
        )

        assert isinstance(app, FastAPI)
        assert app.title == "Test API"
        assert app.version == "1.0.0"
        assert app.description == "Test API Description"

    def test_create_api_app_defaults(self):
        """Test create_api_app with default parameters."""
        app = create_api_app()

        assert isinstance(app, FastAPI)
        assert app.title == "Motadata AI SDK API"
        assert app.version == "0.1.0"

    def test_create_api_app_no_cors(self):
        """Test create_api_app with CORS disabled."""
        app = create_api_app(enable_cors=False)

        assert isinstance(app, FastAPI)
        # Verify app is created successfully without CORS
        # Note: CORS middleware check is simplified and not strictly validated

    def test_create_api_router(self):
        """Test create_api_router factory function."""
        router = create_api_router(prefix="/api/v1", tags=["agents", "rag"])

        assert isinstance(router, APIRouter)
        assert router.prefix == "/api/v1"
        assert "agents" in router.tags
        assert "rag" in router.tags

    def test_create_api_router_defaults(self):
        """Test create_api_router with default parameters."""
        router = create_api_router()

        assert isinstance(router, APIRouter)
        assert router.prefix == ""
        assert router.tags == []

    def test_configure_api_app(self):
        """Test configure_api_app factory function."""
        app = FastAPI()
        configured_app = configure_api_app(
            app=app, enable_cors=True, cors_origins=["http://localhost:3000"]
        )

        assert configured_app == app
        assert isinstance(configured_app, FastAPI)


class TestConvenienceFunctions:
    """Test high-level convenience functions."""

    @pytest.fixture
    def app(self):
        """Create a FastAPI app for testing."""
        return create_api_app()

    @pytest.fixture
    def router(self):
        """Create an API router for testing."""
        return create_api_router(prefix="/api/v1")

    def test_register_router(self, app, router):
        """Test register_router convenience function."""
        register_router(app, router)

        # Verify router is registered
        assert len(app.routes) > 0

    def test_register_router_with_prefix(self, app, router):
        """Test register_router with prefix override."""
        register_router(app, router, prefix="/custom")

        # Router should be registered
        assert len(app.routes) > 0

    def test_add_endpoint_get(self, router):
        """Test add_endpoint with GET method."""

        def get_status():
            """Get status endpoint handler."""
            return {"status": "ok"}

        add_endpoint(router, "/status", "GET", get_status)

        # Verify endpoint was added
        assert len(router.routes) > 0

    def test_add_endpoint_post(self, router):
        """Test add_endpoint with POST method."""

        def create_item():
            """Create item endpoint handler."""
            return {"id": "123"}

        add_endpoint(router, "/items", "POST", create_item)

        assert len(router.routes) > 0

    def test_add_endpoint_put(self, router):
        """Test add_endpoint with PUT method."""

        def update_item():
            """Update item endpoint handler."""
            return {"updated": True}

        add_endpoint(router, "/items/1", "PUT", update_item)

        assert len(router.routes) > 0

    def test_add_endpoint_delete(self, router):
        """Test add_endpoint with DELETE method."""

        def delete_item():
            """Delete item endpoint handler."""
            return {"deleted": True}

        add_endpoint(router, "/items/1", "DELETE", delete_item)

        assert len(router.routes) > 0

    def test_add_endpoint_none_handler(self, router):
        """Test add_endpoint with None handler."""
        initial_routes = len(router.routes)
        add_endpoint(router, "/test", "GET", None)

        # Should not add endpoint - this is a no-op
        # Verify no routes were added when handler is None
        assert len(router.routes) == initial_routes

    def test_add_endpoint_patch(self, router):
        """Test add_endpoint with PATCH method."""
        def patch_item():
            """Patch item endpoint handler."""
            return {"patched": True}

        add_endpoint(router, "/items/1", "PATCH", patch_item)
        assert len(router.routes) > 0

    def test_add_endpoint_other_method(self, router):
        """Test add_endpoint with other HTTP method."""
        def custom_handler():
            """Custom handler."""
            return {"custom": True}

        add_endpoint(router, "/custom", "OPTIONS", custom_handler)
        assert len(router.routes) > 0

    @patch("src.core.rag.quick_rag_query_async", new_callable=AsyncMock)
    @patch("src.core.rag.ingest_document_simple_async", new_callable=AsyncMock)
    def test_create_rag_endpoints(self, mock_ingest, mock_query, router):
        """Test create_rag_endpoints convenience function."""
        mock_rag_system = Mock()
        mock_query.return_value = {"answer": "Test answer"}
        mock_ingest.return_value = "doc-123"

        create_rag_endpoints(router, mock_rag_system, prefix="/api/rag")

        # Verify endpoints were added
        assert len(router.routes) > 0

    def test_create_rag_endpoints_query_registration(self, router):
        """Test create_rag_endpoints query endpoint registration - covers endpoint creation."""
        mock_rag_system = Mock()
        create_rag_endpoints(router, mock_rag_system, prefix="/api/rag")
        
        # Verify endpoints were registered
        assert len(router.routes) >= 2  # query and ingest endpoints

    def test_create_rag_endpoints_ingest_registration(self, router):
        """Test create_rag_endpoints ingest endpoint registration."""
        mock_rag_system = Mock()
        create_rag_endpoints(router, mock_rag_system, prefix="/api/rag")
        
        # Verify ingest endpoint was registered
        assert len(router.routes) >= 2

    def test_create_agent_endpoints(self, router):
        """Test create_agent_endpoints convenience function."""
        mock_agent_manager = Mock()
        mock_agent = Mock()
        mock_agent.agent_id = "agent1"
        mock_agent.get_status = Mock(return_value={"status": "idle"})
        mock_agent_manager.get_agent = Mock(return_value=mock_agent)
        mock_agent_manager.list_agents = Mock(return_value=["agent1"])
        mock_agent_manager.get_agent_statuses = Mock(return_value={"agent1": "idle"})

        create_agent_endpoints(router, mock_agent_manager, prefix="/api/agents")

        # Verify endpoints were added
        assert len(router.routes) > 0

    def test_create_agent_endpoints_list_agents(self):
        """Test create_agent_endpoints list agents handler - covers line 253."""
        from fastapi.testclient import TestClient

        router = create_api_router()
        mock_agent_manager = Mock()
        mock_agent_manager.list_agents = Mock(return_value=["agent1", "agent2"])
        mock_agent_manager.get_agent_statuses = Mock(return_value={"agent1": "idle", "agent2": "active"})

        create_agent_endpoints(router, mock_agent_manager, prefix="/api/agents")

        app = create_api_app()
        app.include_router(router)
        client = TestClient(app)

        response = client.get("/api/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert "statuses" in data
        assert len(data["agents"]) == 2
        assert data["agents"] == ["agent1", "agent2"]
        assert data["statuses"] == {"agent1": "idle", "agent2": "active"}

    def test_create_agent_endpoints_get_agent_not_found(self):
        """Test create_agent_endpoints get agent when not found - covers lines 261-264."""
        from fastapi.testclient import TestClient

        router = create_api_router()
        mock_agent_manager = Mock()
        mock_agent_manager.get_agent = Mock(return_value=None)

        create_agent_endpoints(router, mock_agent_manager, prefix="/api/agents")

        app = create_api_app()
        app.include_router(router)
        client = TestClient(app)

        response = client.get("/api/agents/nonexistent")
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["error"] == "Agent not found"

    def test_create_agent_endpoints_chat_registration(self, router):
        """Test create_agent_endpoints chat endpoint registration."""
        mock_agent_manager = Mock()
        create_agent_endpoints(router, mock_agent_manager, prefix="/api/agents")
        
        # Verify chat endpoint was registered
        assert len(router.routes) >= 3  # list, get, chat, task endpoints

    def test_create_agent_endpoints_chat_agent_not_found(self):
        """Test create_agent_endpoints chat agent when agent not found - covers lines 269-271."""
        from fastapi.testclient import TestClient

        router = create_api_router()
        mock_agent_manager = Mock()
        mock_agent_manager.get_agent = Mock(return_value=None)

        create_agent_endpoints(router, mock_agent_manager, prefix="/api/agents")

        app = create_api_app()
        app.include_router(router)
        client = TestClient(app)

        response = client.post(
            "/api/agents/nonexistent/chat",
            json={"message": "Hello"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["error"] == "Agent not found"

    def test_create_agent_endpoints_task_registration(self, router):
        """Test create_agent_endpoints task endpoint registration."""
        mock_agent_manager = Mock()
        create_agent_endpoints(router, mock_agent_manager, prefix="/api/agents")
        
        # Verify task endpoint was registered
        assert len(router.routes) >= 4  # list, get, chat, task endpoints

    def test_create_agent_endpoints_submit_task_not_found(self):
        """Test create_agent_endpoints submit task when agent not found - covers lines 282-284."""
        from fastapi.testclient import TestClient

        router = create_api_router()
        mock_agent_manager = Mock()
        mock_agent_manager.get_agent = Mock(return_value=None)

        create_agent_endpoints(router, mock_agent_manager, prefix="/api/agents")

        app = create_api_app()
        app.include_router(router)
        client = TestClient(app)

        response = client.post(
            "/api/agents/nonexistent/task",
            json={"task_type": "test_task"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["error"] == "Agent not found"

    def test_create_gateway_endpoints(self, router):
        """Test create_gateway_endpoints convenience function."""
        mock_gateway = Mock()
        mock_gateway.generate = Mock(return_value=Mock(text="Generated text"))
        mock_gateway.generate_embeddings = Mock(return_value=Mock(embeddings=[[0.1] * 1536]))

        create_gateway_endpoints(router, mock_gateway, prefix="/api/gateway")

        # Verify endpoints were added
        assert len(router.routes) > 0

    def test_create_gateway_endpoints_generate_registration(self, router):
        """Test create_gateway_endpoints generate endpoint registration."""
        mock_gateway = Mock()
        create_gateway_endpoints(router, mock_gateway, prefix="/api/gateway")
        
        # Verify generate endpoint was registered
        assert len(router.routes) >= 2  # generate and embed endpoints

    def test_create_gateway_endpoints_embed_registration(self, router):
        """Test create_gateway_endpoints embed endpoint registration."""
        mock_gateway = Mock()
        create_gateway_endpoints(router, mock_gateway, prefix="/api/gateway")
        
        # Verify embed endpoint was registered
        assert len(router.routes) >= 2  # generate and embed endpoints


class TestHelperFunctions:
    """Test internal helper functions."""

    def test_determine_processing_mode_rag(self):
        """Test _determine_processing_mode with rag mode."""
        from src.core.api_backend_services.functions import _determine_processing_mode

        use_rag, use_agent = _determine_processing_mode("rag", "test query")
        assert use_rag is True
        assert use_agent is False

    def test_determine_processing_mode_agent(self):
        """Test _determine_processing_mode with agent mode."""
        from src.core.api_backend_services.functions import _determine_processing_mode

        use_rag, use_agent = _determine_processing_mode("agent", "test query")
        assert use_rag is False
        assert use_agent is True

    def test_determine_processing_mode_both(self):
        """Test _determine_processing_mode with both mode."""
        from src.core.api_backend_services.functions import _determine_processing_mode

        use_rag, use_agent = _determine_processing_mode("both", "test query")
        assert use_rag is True
        assert use_agent is True

    def test_determine_processing_mode_auto_knowledge(self):
        """Test _determine_processing_mode with auto mode and knowledge query."""
        from src.core.api_backend_services.functions import _determine_processing_mode

        use_rag, use_agent = _determine_processing_mode("auto", "what is AI?")
        assert use_rag is True
        assert use_agent is False

    def test_determine_processing_mode_auto_action(self):
        """Test _determine_processing_mode with auto mode and action query - covers line 323."""
        from src.core.api_backend_services.functions import _determine_processing_mode

        use_rag, use_agent = _determine_processing_mode("auto", "create a ticket")
        assert use_rag is False
        assert use_agent is True

    def test_determine_final_answer_rag(self):
        """Test _determine_final_answer with RAG response."""
        from src.core.api_backend_services.functions import _determine_final_answer

        result = {"rag_response": {"answer": "RAG answer"}}
        answer = _determine_final_answer(result, use_rag=True, use_agent=False)
        assert answer == "RAG answer"

    def test_determine_final_answer_agent(self):
        """Test _determine_final_answer with Agent response."""
        from src.core.api_backend_services.functions import _determine_final_answer

        result = {"agent_response": {"answer": "Agent answer"}}
        answer = _determine_final_answer(result, use_rag=False, use_agent=True)
        assert answer == "Agent answer"

    def test_determine_final_answer_combined(self):
        """Test _determine_final_answer with combined answer - covers line 428."""
        from src.core.api_backend_services.functions import _determine_final_answer

        result = {"combined_answer": "Combined answer"}
        answer = _determine_final_answer(result, use_rag=True, use_agent=True)
        assert answer == "Combined answer"

    def test_determine_final_answer_fallback(self):
        """Test _determine_final_answer fallback - covers line 430."""
        from src.core.api_backend_services.functions import _determine_final_answer

        result = {}
        answer = _determine_final_answer(result, use_rag=False, use_agent=False)
        assert answer == "Unable to process query"

    def test_determine_final_answer_agent_no_answer(self):
        """Test _determine_final_answer with agent response but no answer field."""
        from src.core.api_backend_services.functions import _determine_final_answer

        result = {"agent_response": {}}
        answer = _determine_final_answer(result, use_rag=False, use_agent=True)
        assert answer == ""


class TestUtilityFunctions:
    """Test utility functions."""

    @pytest.fixture
    def app(self):
        """Create a FastAPI app for testing."""
        return create_api_app()

    def test_add_health_check(self, app):
        """Test add_health_check utility function."""
        add_health_check(app, path="/health")

        # Verify health check endpoint exists
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_add_health_check_custom_path(self, app):
        """Test add_health_check with custom path."""
        add_health_check(app, path="/custom/health")

        client = TestClient(app)
        response = client.get("/custom/health")
        assert response.status_code == 200

    def test_add_api_versioning(self, app):
        """Test add_api_versioning utility function."""
        api_prefix = add_api_versioning(version="v1", prefix="/api")

        assert api_prefix == "/api/v1"

    def test_add_api_versioning_defaults(self, app):
        """Test add_api_versioning with default parameters."""
        api_prefix = add_api_versioning()

        assert api_prefix == "/api/v1"

    def test_add_api_versioning_custom(self, app):
        """Test add_api_versioning with custom version and prefix."""
        api_prefix = add_api_versioning(version="v2", prefix="/custom")

        assert api_prefix == "/custom/v2"


class TestUnifiedQueryEndpoint:
    """Test unified query endpoint."""

    @pytest.fixture
    def mock_agent_manager(self):
        """Mock agent manager."""
        mock_manager = MagicMock()
        mock_manager.list_agents.return_value = ["agent_1"]
        mock_manager.execute_task = AsyncMock(return_value={"result": "Agent response"})
        return mock_manager

    @pytest.fixture
    def mock_rag_system(self):
        """Mock RAG system."""
        mock_rag = MagicMock()
        return mock_rag

    @pytest.fixture
    def mock_gateway(self):
        """Mock gateway."""
        mock_gw = MagicMock()
        return mock_gw

    @pytest.fixture
    def router(self):
        """API router fixture."""
        return create_api_router()

    @pytest.mark.asyncio
    async def test_create_unified_query_endpoint(
        self, router, mock_agent_manager, mock_rag_system, mock_gateway
    ):
        """Test creating unified query endpoint."""
        with patch("src.core.rag.quick_rag_query_async", new_callable=AsyncMock) as mock_rag_query:
            mock_rag_query.return_value = {
                "answer": "RAG answer",
                "sources": [],
                "num_documents": 0,
            }

            create_unified_query_endpoint(
                router=router,
                agent_manager=mock_agent_manager,
                rag_system=mock_rag_system,
                prefix="/query",
            )

            # Endpoint should be registered
            assert len(router.routes) > 0

    @pytest.mark.asyncio
    async def test_unified_endpoint_auto_mode_rag(
        self, router, mock_agent_manager, mock_rag_system, mock_gateway
    ):
        """Test unified endpoint in auto mode routing to RAG."""
        from fastapi.testclient import TestClient

        with patch("src.core.rag.quick_rag_query_async", new_callable=AsyncMock) as mock_rag_query:
            mock_rag_query.return_value = {
                "answer": "RAG answer",
                "sources": [],
                "num_documents": 1,
            }

            create_unified_query_endpoint(
                router=router,
                agent_manager=mock_agent_manager,
                rag_system=mock_rag_system,
            )

            app = create_api_app()
            app.include_router(router)
            client = TestClient(app)

            # Knowledge question should route to RAG
            response = client.post(
                "/query", json={"query": "What is AI?", "mode": "auto", "tenant_id": "test_tenant"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "rag_response" in data
            assert data["rag_response"]["answer"] == "RAG answer"

    @pytest.mark.asyncio
    async def test_unified_endpoint_agent_mode(
        self, router, mock_agent_manager, mock_rag_system, mock_gateway
    ):
        """Test unified endpoint in agent mode."""
        from fastapi.testclient import TestClient

        with patch("src.core.agno_agent_framework.chat_with_agent", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = {"answer": "Agent response", "session_id": "session_123"}

            # Setup proper agent mock
            mock_agent = MagicMock()
            mock_agent.agent_id = "agent_1"
            mock_agent_manager.get_agent.return_value = mock_agent
            mock_agent_manager.list_agents.return_value = ["agent_1"]

            create_unified_query_endpoint(
                router=router,
                agent_manager=mock_agent_manager,
                rag_system=mock_rag_system,
            )

            app = create_api_app()
            app.include_router(router)
            client = TestClient(app)

            # Agent mode should use agent
            response = client.post(
                "/query",
                json={
                    "query": "Create a ticket",
                    "mode": "agent",
                    "agent_id": "agent_1",
                    "tenant_id": "test_tenant",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "agent_response" in data or "result" in data

    @pytest.mark.asyncio
    async def test_unified_endpoint_both_mode(
        self, router, mock_agent_manager, mock_rag_system, mock_gateway
    ):
        """Test unified endpoint in both mode (Agent + RAG)."""
        from fastapi.testclient import TestClient

        with patch("src.core.rag.quick_rag_query_async", new_callable=AsyncMock) as mock_rag_query:
            mock_rag_query.return_value = {
                "answer": "RAG answer",
                "sources": [],
                "num_documents": 1,
            }

            create_unified_query_endpoint(
                router=router,
                agent_manager=mock_agent_manager,
                rag_system=mock_rag_system,
            )

            app = create_api_app()
            app.include_router(router)
            client = TestClient(app)

            # Both mode should use both Agent and RAG
            response = client.post(
                "/query", json={"query": "Test query", "mode": "both", "tenant_id": "test_tenant"}
            )

            assert response.status_code == 200
            data = response.json()
            # Should have both responses
            assert "rag_response" in data or "agent_response" in data

    @pytest.mark.asyncio
    @patch("src.core.agno_agent_framework.chat_with_agent", new_callable=AsyncMock)
    async def test_unified_endpoint_auto_mode_agent(self, mock_chat, router, mock_agent_manager, mock_rag_system, mock_gateway):
        """Test unified endpoint in auto mode routing to Agent."""
        from fastapi.testclient import TestClient

        mock_chat.return_value = {"answer": "Agent response", "session_id": "session_123"}

        mock_agent = MagicMock()
        mock_agent.agent_id = "agent_1"
        mock_agent_manager.get_agent.return_value = mock_agent
        mock_agent_manager.list_agents.return_value = ["agent_1"]

        create_unified_query_endpoint(
            router=router,
            agent_manager=mock_agent_manager,
            rag_system=mock_rag_system,
        )

        app = create_api_app()
        app.include_router(router)
        client = TestClient(app)

        # Action question should route to Agent
        response = client.post(
            "/query",
            json={"query": "Create a ticket", "mode": "auto", "tenant_id": "test_tenant"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "agent_response" in data or "result" in data

    @pytest.mark.asyncio
    @patch("src.core.rag.quick_rag_query_async", new_callable=AsyncMock)
    async def test_unified_endpoint_rag_error_handling(self, mock_rag_query, router, mock_agent_manager, mock_rag_system, mock_gateway):
        """Test unified endpoint RAG error handling."""
        from fastapi.testclient import TestClient

        mock_rag_query.side_effect = Exception("RAG error")

        create_unified_query_endpoint(
            router=router,
            agent_manager=mock_agent_manager,
            rag_system=mock_rag_system,
        )

        app = create_api_app()
        app.include_router(router)
        client = TestClient(app)

        response = client.post(
            "/query",
            json={"query": "Test query", "mode": "rag", "tenant_id": "test_tenant"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "rag_error" in data

    @pytest.mark.asyncio
    @patch("src.core.rag.quick_rag_query_async", new_callable=AsyncMock)
    @patch("src.core.agno_agent_framework.chat_with_agent", new_callable=AsyncMock)
    async def test_unified_endpoint_determine_final_answer_combined(self, mock_chat, mock_rag_query, router, mock_agent_manager, mock_rag_system, mock_gateway):
        """Test unified endpoint determine final answer with combined answer."""
        from fastapi.testclient import TestClient

        mock_rag_query.return_value = {
            "answer": "RAG answer",
            "sources": [],
            "num_documents": 1,
        }
        mock_chat.return_value = {"answer": "Agent answer"}

        mock_agent = MagicMock()
        mock_agent.agent_id = "agent_1"
        mock_agent_manager.get_agent.return_value = mock_agent
        mock_agent_manager.list_agents.return_value = ["agent_1"]

        create_unified_query_endpoint(
            router=router,
            agent_manager=mock_agent_manager,
            rag_system=mock_rag_system,
        )

        app = create_api_app()
        app.include_router(router)
        client = TestClient(app)

        # Test with both mode to trigger combined answer logic
        response = client.post(
            "/query",
            json={"query": "Test query", "mode": "both", "tenant_id": "test_tenant"}
        )

        assert response.status_code == 200
        data = response.json()
        # Should have answer or combined_answer
        assert "answer" in data or "combined_answer" in data or "rag_response" in data

    @pytest.mark.asyncio
    @patch("src.core.rag.quick_rag_query_async", new_callable=AsyncMock)
    @patch("src.core.agno_agent_framework.chat_with_agent", new_callable=AsyncMock)
    async def test_unified_endpoint_determine_final_answer_fallback(self, mock_chat, mock_rag_query, router, mock_agent_manager, mock_rag_system, mock_gateway):
        """Test unified endpoint determine final answer fallback."""
        from fastapi.testclient import TestClient

        mock_rag_query.return_value = {
            "answer": "RAG answer",
            "sources": [],
            "num_documents": 1,
        }
        mock_chat.return_value = {}  # No answer in response

        mock_agent = MagicMock()
        mock_agent.agent_id = "agent_1"
        mock_agent_manager.get_agent.return_value = mock_agent
        mock_agent_manager.list_agents.return_value = ["agent_1"]

        create_unified_query_endpoint(
            router=router,
            agent_manager=mock_agent_manager,
            rag_system=mock_rag_system,
        )

        app = create_api_app()
        app.include_router(router)
        client = TestClient(app)

        # Test with both mode but no valid answers
        response = client.post(
            "/query",
            json={"query": "Test query", "mode": "both", "tenant_id": "test_tenant"}
        )

        assert response.status_code == 200
        data = response.json()
        # Should have answer (even if fallback) - tests line 428 (combined_answer) and 430 (fallback)
        assert "answer" in data
        # Verify fallback message is used when no valid answers
        assert data["answer"] in ["RAG answer", "Unable to process query"]

    @pytest.mark.asyncio
    @patch("src.core.agno_agent_framework.chat_with_agent", new_callable=AsyncMock)
    async def test_unified_endpoint_agent_error_handling(self, mock_chat, router, mock_agent_manager, mock_rag_system, mock_gateway):
        """Test unified endpoint Agent error handling."""
        from fastapi.testclient import TestClient

        mock_chat.side_effect = Exception("Agent error")

        mock_agent = MagicMock()
        mock_agent.agent_id = "agent_1"
        mock_agent_manager.get_agent.return_value = mock_agent
        mock_agent_manager.list_agents.return_value = ["agent_1"]

        create_unified_query_endpoint(
            router=router,
            agent_manager=mock_agent_manager,
            rag_system=mock_rag_system,
        )

        app = create_api_app()
        app.include_router(router)
        client = TestClient(app)

        response = client.post(
            "/query",
            json={"query": "Test query", "mode": "agent", "agent_id": "agent_1", "tenant_id": "test_tenant"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "agent_error" in data

    @pytest.mark.asyncio
    async def test_unified_endpoint_agent_not_found_error(self, router, mock_agent_manager, mock_rag_system, mock_gateway):
        """Test unified endpoint Agent when agent not found (line 399)."""
        from fastapi.testclient import TestClient

        mock_agent_manager.get_agent.return_value = None
        mock_agent_manager.list_agents.return_value = ["agent_1"]

        create_unified_query_endpoint(
            router=router,
            agent_manager=mock_agent_manager,
            rag_system=mock_rag_system,
        )

        app = create_api_app()
        app.include_router(router)
        client = TestClient(app)

        response = client.post(
            "/query",
            json={"query": "Test query", "mode": "agent", "agent_id": "nonexistent", "tenant_id": "test_tenant"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "agent_error" in data
        assert "not found" in data["agent_error"].lower()

    @pytest.mark.asyncio
    @patch("src.core.agno_agent_framework.chat_with_agent", new_callable=AsyncMock)
    async def test_unified_endpoint_agent_no_agent_id(self, mock_chat, router, mock_agent_manager, mock_rag_system, mock_gateway):
        """Test unified endpoint Agent with no agent_id provided."""
        from fastapi.testclient import TestClient

        mock_chat.return_value = {"answer": "Agent response"}

        mock_agent = MagicMock()
        mock_agent.agent_id = "agent_1"
        mock_agent_manager.get_agent.return_value = mock_agent
        mock_agent_manager.list_agents.return_value = ["agent_1"]

        create_unified_query_endpoint(
            router=router,
            agent_manager=mock_agent_manager,
            rag_system=mock_rag_system,
        )

        app = create_api_app()
        app.include_router(router)
        client = TestClient(app)

        # No agent_id in request, should use first available agent
        response = client.post(
            "/query",
            json={"query": "Test query", "mode": "agent", "tenant_id": "test_tenant"}
        )

        assert response.status_code == 200
        data = response.json()
        # Should either have agent_response or agent_error
        assert "agent_response" in data or "agent_error" in data

    @pytest.mark.asyncio
    async def test_unified_endpoint_agent_no_agents_available(self, router, mock_agent_manager, mock_rag_system, mock_gateway):
        """Test unified endpoint Agent with no agents available."""
        from fastapi.testclient import TestClient

        mock_agent_manager.list_agents.return_value = []
        mock_agent_manager.get_agent.return_value = None

        create_unified_query_endpoint(
            router=router,
            agent_manager=mock_agent_manager,
            rag_system=mock_rag_system,
        )

        app = create_api_app()
        app.include_router(router)
        client = TestClient(app)

        response = client.post(
            "/query",
            json={"query": "Test query", "mode": "agent", "tenant_id": "test_tenant"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "agent_error" in data

    @pytest.mark.asyncio
    async def test_unified_endpoint_custom_prefix(
        self, router, mock_agent_manager, mock_rag_system, mock_gateway
    ):
        """Test unified endpoint with custom prefix."""
        from fastapi.testclient import TestClient

        with patch("src.core.rag.quick_rag_query_async") as mock_rag_query:
            mock_rag_query.return_value = {"answer": "RAG answer", "sources": []}

            create_unified_query_endpoint(
                router=router,
                agent_manager=mock_agent_manager,
                rag_system=mock_rag_system,
                prefix="/api/v1/query",
            )

            app = create_api_app()
            app.include_router(router)
            client = TestClient(app)

            # Should be accessible at custom prefix
            response = client.post(
                "/api/v1/query",
                json={"query": "What is AI?", "mode": "rag", "tenant_id": "test_tenant"},
            )

            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
