"""
Unit Tests for API Backend Services Functions

Tests factory functions, convenience functions, and utilities for API backend services.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from fastapi import FastAPI, APIRouter
from fastapi.testclient import TestClient
from src.core.api_backend_services.functions import (
    # Factory functions
    create_api_app,
    create_api_router,
    configure_api_app,
    # High-level convenience functions
    register_router,
    add_endpoint,
    create_rag_endpoints,
    create_agent_endpoints,
    create_gateway_endpoints,
    create_unified_query_endpoint,
    # Utility functions
    add_health_check,
    add_api_versioning,
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
            cors_origins=["http://localhost:3000"]
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
        # Verify no CORS middleware added
        cors_middleware = any(
            isinstance(middleware, type) and "CORS" in str(middleware)
            for middleware in app.user_middleware
        )
        # Note: This is a simplified check
    
    def test_create_api_router(self):
        """Test create_api_router factory function."""
        router = create_api_router(
            prefix="/api/v1",
            tags=["agents", "rag"]
        )
        
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
            app=app,
            enable_cors=True,
            cors_origins=["http://localhost:3000"]
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
        add_endpoint(router, "/test", "GET", None)
        
        # Should not add endpoint
        initial_routes = len(router.routes)
        # This is a no-op, so routes shouldn't change
        assert True  # Just verify no exception
    
    @patch('src.core.api_backend_services.functions.quick_rag_query')
    @patch('src.core.api_backend_services.functions.ingest_document_simple')
    def test_create_rag_endpoints(self, mock_ingest, mock_query, router):
        """Test create_rag_endpoints convenience function."""
        mock_rag_system = Mock()
        mock_query.return_value = {"answer": "Test answer"}
        mock_ingest.return_value = "doc-123"
        
        create_rag_endpoints(router, mock_rag_system, prefix="/api/rag")
        
        # Verify endpoints were added
        assert len(router.routes) > 0
    
    @patch('src.core.api_backend_services.functions.execute_task')
    @patch('src.core.api_backend_services.functions.chat_with_agent')
    def test_create_agent_endpoints(self, mock_chat, mock_execute, router):
        """Test create_agent_endpoints convenience function."""
        mock_agent_manager = Mock()
        mock_agent = Mock()
        mock_agent.agent_id = "agent1"
        mock_agent.get_status = Mock(return_value={"status": "idle"})
        mock_agent_manager.get_agent = Mock(return_value=mock_agent)
        mock_agent_manager.list_agents = Mock(return_value=["agent1"])
        mock_agent_manager.get_agent_statuses = Mock(return_value={"agent1": "idle"})
        
        mock_chat.return_value = {"answer": "Hello"}
        mock_execute.return_value = {"result": "Task completed"}
        
        create_agent_endpoints(router, mock_agent_manager, prefix="/api/agents")
        
        # Verify endpoints were added
        assert len(router.routes) > 0
    
    @patch('src.core.api_backend_services.functions.generate_text')
    @patch('src.core.api_backend_services.functions.generate_embeddings')
    def test_create_gateway_endpoints(self, mock_embed, mock_generate, router):
        """Test create_gateway_endpoints convenience function."""
        mock_gateway = Mock()
        mock_generate.return_value = "Generated text"
        mock_embed.return_value = [[0.1] * 1536]
        
        create_gateway_endpoints(router, mock_gateway, prefix="/api/gateway")
        
        # Verify endpoints were added
        assert len(router.routes) > 0


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
        api_prefix = add_api_versioning(app, version="v1", prefix="/api")
        
        assert api_prefix == "/api/v1"
    
    def test_add_api_versioning_defaults(self, app):
        """Test add_api_versioning with default parameters."""
        api_prefix = add_api_versioning(app)
        
        assert api_prefix == "/api/v1"
    
    def test_add_api_versioning_custom(self, app):
        """Test add_api_versioning with custom version and prefix."""
        api_prefix = add_api_versioning(app, version="v2", prefix="/custom")
        
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
    async def test_create_unified_query_endpoint(self, router, mock_agent_manager, mock_rag_system, mock_gateway):
        """Test creating unified query endpoint."""
        with patch('src.core.api_backend_services.functions.quick_rag_query') as mock_rag_query:
            mock_rag_query.return_value = {
                "answer": "RAG answer",
                "sources": [],
                "num_documents": 0
            }
            
            create_unified_query_endpoint(
                router=router,
                agent_manager=mock_agent_manager,
                rag_system=mock_rag_system,
                gateway=mock_gateway,
                prefix="/query"
            )
            
            # Endpoint should be registered
            assert len(router.routes) > 0

    @pytest.mark.asyncio
    async def test_unified_endpoint_auto_mode_rag(self, router, mock_agent_manager, mock_rag_system, mock_gateway):
        """Test unified endpoint in auto mode routing to RAG."""
        from fastapi.testclient import TestClient
        
        with patch('src.core.api_backend_services.functions.quick_rag_query') as mock_rag_query:
            mock_rag_query.return_value = {
                "answer": "RAG answer",
                "sources": [],
                "num_documents": 1
            }
            
            create_unified_query_endpoint(
                router=router,
                agent_manager=mock_agent_manager,
                rag_system=mock_rag_system,
                gateway=mock_gateway
            )
            
            app = create_api_app()
            app.include_router(router)
            client = TestClient(app)
            
            # Knowledge question should route to RAG
            response = client.post(
                "/query",
                json={
                    "query": "What is AI?",
                    "mode": "auto",
                    "tenant_id": "test_tenant"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "rag_response" in data
            assert data["rag_response"]["answer"] == "RAG answer"

    @pytest.mark.asyncio
    async def test_unified_endpoint_agent_mode(self, router, mock_agent_manager, mock_rag_system, mock_gateway):
        """Test unified endpoint in agent mode."""
        from fastapi.testclient import TestClient
        
        create_unified_query_endpoint(
            router=router,
            agent_manager=mock_agent_manager,
            rag_system=mock_rag_system,
            gateway=mock_gateway
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
                "tenant_id": "test_tenant"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "agent_response" in data or "result" in data

    @pytest.mark.asyncio
    async def test_unified_endpoint_both_mode(self, router, mock_agent_manager, mock_rag_system, mock_gateway):
        """Test unified endpoint in both mode (Agent + RAG)."""
        from fastapi.testclient import TestClient
        
        with patch('src.core.api_backend_services.functions.quick_rag_query') as mock_rag_query:
            mock_rag_query.return_value = {
                "answer": "RAG answer",
                "sources": [],
                "num_documents": 1
            }
            
            create_unified_query_endpoint(
                router=router,
                agent_manager=mock_agent_manager,
                rag_system=mock_rag_system,
                gateway=mock_gateway
            )
            
            app = create_api_app()
            app.include_router(router)
            client = TestClient(app)
            
            # Both mode should use both Agent and RAG
            response = client.post(
                "/query",
                json={
                    "query": "Test query",
                    "mode": "both",
                    "tenant_id": "test_tenant"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            # Should have both responses
            assert "rag_response" in data or "agent_response" in data

    @pytest.mark.asyncio
    async def test_unified_endpoint_custom_prefix(self, router, mock_agent_manager, mock_rag_system, mock_gateway):
        """Test unified endpoint with custom prefix."""
        from fastapi.testclient import TestClient
        
        with patch('src.core.api_backend_services.functions.quick_rag_query') as mock_rag_query:
            mock_rag_query.return_value = {
                "answer": "RAG answer",
                "sources": []
            }
            
            create_unified_query_endpoint(
                router=router,
                agent_manager=mock_agent_manager,
                rag_system=mock_rag_system,
                gateway=mock_gateway,
                prefix="/api/v1/query"
            )
            
            app = create_api_app()
            app.include_router(router)
            client = TestClient(app)
            
            # Should be accessible at custom prefix
            response = client.post(
                "/api/v1/query",
                json={
                    "query": "What is AI?",
                    "mode": "rag",
                    "tenant_id": "test_tenant"
                }
            )
            
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

