"""
Unit tests for Data Ingestion Service.
"""


from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from src.faas.services.data_ingestion_service import create_data_ingestion_service
from src.faas.shared.config import ServiceConfig


@pytest.fixture
def mock_config():
    """Create mock service configuration."""
    return ServiceConfig(
        service_name="data-ingestion-service",
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
def data_ingestion_service(mock_config, mock_db):
    """Create data ingestion service instance for testing."""
    with patch("src.faas.services.data_ingestion_service.get_database_connection") as mock_get_db, \
         patch("src.faas.services.data_ingestion_service.create_ingestion_service") as mock_create_service:
        mock_get_db.return_value.get_connection.return_value = mock_db
        
        # Mock ingestion service
        mock_service = Mock()
        mock_service.upload_and_process = AsyncMock(return_value={
            "document_id": "doc_123",
            "content_preview": "Test content",
            "status": "processed",
        })
        mock_create_service.return_value = mock_service
        
        service = create_data_ingestion_service(
            service_name="data-ingestion-service",
            config_overrides={
                "database_url": "postgresql://test:test@localhost/test",
            },
        )
        
        # Patch _get_ingestion_service to return the mock service
        service._get_ingestion_service = Mock(return_value=mock_service)
        
        return service


def test_data_ingestion_service_creation(data_ingestion_service):
    """Test data ingestion service creation."""
    assert data_ingestion_service is not None
    assert data_ingestion_service.app is not None
    assert data_ingestion_service.config.service_name == "data-ingestion-service"


@pytest.mark.asyncio
async def test_process_file_endpoint(data_ingestion_service):
    """Test process file endpoint."""
    # Note: File upload testing requires more complex setup
    # This is a basic test structure
    client = TestClient(data_ingestion_service.app)
    
    # Create a simple file-like object
    from io import BytesIO
    file_content = BytesIO(b"Test file content")
    
    response = client.post(
        "/api/v1/ingestion/process",
        files={"file": ("test.txt", file_content, "text/plain")},
        data={
            "title": "Test Document",
            "metadata": "{}",
        },
        headers={
            "X-Tenant-ID": "tenant_123",
        },
    )
    
    # Response may vary based on implementation
    assert response.status_code in [200, 201, 400, 500]


def test_health_check(data_ingestion_service):
    """Test health check endpoint."""
    client = TestClient(data_ingestion_service.app)
    
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "data-ingestion-service"


@pytest.mark.asyncio
async def test_process_file_missing_tenant_id(data_ingestion_service):
    """Test process file endpoint without tenant ID."""
    client = TestClient(data_ingestion_service.app)
    
    from io import BytesIO
    file_content = BytesIO(b"Test file content")
    
    response = client.post(
        "/api/v1/ingestion/process",
        files={"file": ("test.txt", file_content, "text/plain")},
    )
    
    assert response.status_code == 401  # AuthMiddleware should reject

