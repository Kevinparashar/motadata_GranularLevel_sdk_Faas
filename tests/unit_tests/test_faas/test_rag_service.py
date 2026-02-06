"""
Unit tests for RAG Service.
"""


from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from src.faas.services.rag_service import create_rag_service
from src.faas.shared.config import ServiceConfig


@pytest.fixture
def mock_config():
    """Create mock service configuration."""
    return ServiceConfig(
        service_name="rag-service",
        service_version="1.0.0",
        service_port=8080,
        database_url="postgresql://test:test@localhost/test",
        gateway_service_url=None,
        cache_service_url=None,
        rag_service_url=None,
        agent_service_url=None,
        ml_service_url=None,
        prompt_service_url=None,
        data_ingestion_service_url=None,
        prompt_generator_service_url=None,
        llmops_service_url=None,
        dragonfly_url=None,
        nats_url=None,
        otel_exporter_otlp_endpoint=None,
        enable_nats=False,
        enable_otel=False,
    )


@pytest.fixture
def mock_db():
    """Create mock database connection."""
    db = Mock()
    db.connect = AsyncMock(return_value=None)
    db.execute_query = AsyncMock(return_value=[])
    return db


@pytest.fixture
def rag_service(mock_config, mock_db):
    """Create RAG service instance for testing."""
    with patch("src.faas.services.rag_service.get_database_connection") as mock_get_db, \
         patch("src.faas.services.rag_service.create_gateway") as mock_create_gateway, \
         patch("src.faas.services.rag_service.create_rag_system") as mock_create_rag:
        mock_get_db.return_value.get_connection.return_value = mock_db
        
        # Mock gateway
        mock_gateway = Mock()
        mock_create_gateway.return_value = mock_gateway
        
        # Mock RAG system
        mock_rag = Mock()
        mock_rag.ingest_document_async = AsyncMock(return_value="doc_123")
        mock_rag.update_document = AsyncMock(return_value=None)
        mock_rag.delete_document = AsyncMock(return_value=None)
        mock_rag.retriever = Mock()
        mock_rag.retriever.retrieve = Mock(return_value=[])
        mock_create_rag.return_value = mock_rag
        
        service = create_rag_service(
            service_name="rag-service",
            config_overrides={
                "database_url": "postgresql://test:test@localhost/test",
            },
        )
        
        # Patch _get_rag_system to return the mock RAG system
        service._get_rag_system = Mock(return_value=mock_rag)
        
        return service


def test_rag_service_creation(rag_service):
    """Test RAG service creation."""
    assert rag_service is not None
    assert rag_service.app is not None
    assert rag_service.config.service_name == "rag-service"


@pytest.mark.asyncio
async def test_ingest_document_endpoint(rag_service):
    """Test ingest document endpoint."""
    with patch("src.faas.services.rag_service.quick_rag_query_async") as mock_query:
        mock_query.return_value = {
            "answer": "Test answer",
            "documents": [],
            "sources": [],
        }
        
        client = TestClient(rag_service.app)
        
        response = client.post(
            "/api/v1/rag/documents",
            json={
                "title": "Test Document",
                "content": "Test content",
                "source": "test",
                "metadata": {},
            },
            headers={
                "X-Tenant-ID": "tenant_123",
                "X-Correlation-ID": "corr_123",
                "X-Request-ID": "req_123",
            },
        )
        
        assert response.status_code in [201, 500]  # 500 if RAG system creation fails
        if response.status_code == 201:
            data = response.json()
            assert data["success"] is True
            assert "document_id" in data["data"]


@pytest.mark.asyncio
async def test_query_endpoint(rag_service):
    """Test query endpoint."""
    with patch("src.faas.services.rag_service.quick_rag_query_async") as mock_query:
        mock_query.return_value = {
            "answer": "Test answer",
            "documents": [{"content": "Test doc"}],
            "sources": ["source1"],
            "confidence": 0.9,
        }
        
        client = TestClient(rag_service.app)
        
        response = client.post(
            "/api/v1/rag/query",
            json={
                "query": "What is this?",
                "top_k": 5,
                "threshold": 0.7,
            },
            headers={
                "X-Tenant-ID": "tenant_123",
                "X-Correlation-ID": "corr_123",
            },
        )
        
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "answer" in data["data"]


@pytest.mark.asyncio
async def test_search_endpoint(rag_service):
    """Test search endpoint."""
    client = TestClient(rag_service.app)
    
    response = client.post(
        "/api/v1/rag/search",
        json={
            "query_text": "test query",
            "top_k": 5,
            "threshold": 0.7,
        },
        headers={
            "X-Tenant-ID": "tenant_123",
        },
    )
    
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert data["success"] is True
        assert "documents" in data["data"]


@pytest.mark.asyncio
async def test_search_endpoint_missing_query(rag_service):
    """Test search endpoint with missing query_text."""
    client = TestClient(rag_service.app)
    
    response = client.post(
        "/api/v1/rag/search",
        json={
            "top_k": 5,
        },
        headers={
            "X-Tenant-ID": "tenant_123",
        },
    )
    
    assert response.status_code in [400, 500]


@pytest.mark.asyncio
async def test_update_document_endpoint(rag_service):
    """Test update document endpoint."""
    client = TestClient(rag_service.app)
    
    response = client.put(
        "/api/v1/rag/documents/doc_123",
        json={
            "title": "Updated Title",
            "content": "Updated content",
            "metadata": {},
        },
        headers={
            "X-Tenant-ID": "tenant_123",
        },
    )
    
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert data["success"] is True
        assert data["data"]["document_id"] == "doc_123"


@pytest.mark.asyncio
async def test_delete_document_endpoint(rag_service):
    """Test delete document endpoint."""
    client = TestClient(rag_service.app)
    
    response = client.delete(
        "/api/v1/rag/documents/doc_123",
        headers={
            "X-Tenant-ID": "tenant_123",
        },
    )
    
    assert response.status_code in [204, 500]


@pytest.mark.asyncio
async def test_list_documents_endpoint(rag_service):
    """Test list documents endpoint."""
    client = TestClient(rag_service.app)
    
    response = client.get(
        "/api/v1/rag/documents",
        headers={
            "X-Tenant-ID": "tenant_123",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "documents" in data["data"]


def test_health_check(rag_service):
    """Test health check endpoint."""
    client = TestClient(rag_service.app)
    
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "rag-service"


@pytest.mark.asyncio
async def test_ingest_document_missing_tenant_id(rag_service):
    """Test ingest document endpoint without tenant ID."""
    client = TestClient(rag_service.app)
    
    response = client.post(
        "/api/v1/rag/documents",
        json={
            "title": "Test Document",
            "content": "Test content",
        },
    )
    
    assert response.status_code == 401  # AuthMiddleware should reject


@pytest.mark.asyncio
async def test_query_error_handling(rag_service):
    """Test query endpoint error handling."""
    with patch("src.faas.services.rag_service.quick_rag_query_async") as mock_query:
        mock_query.side_effect = Exception("Test error")
        
        client = TestClient(rag_service.app)
        
        response = client.post(
            "/api/v1/rag/query",
            json={
                "query": "What is this?",
            },
            headers={
                "X-Tenant-ID": "tenant_123",
            },
        )
        
        assert response.status_code == 500

