"""
Integration tests for FaaS service interactions.

Tests how services communicate with each other.
"""


from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.faas.shared.http_client import ServiceHTTPClient


@pytest.mark.asyncio
async def test_agent_service_calls_gateway_service():
    """Test that Agent Service can call Gateway Service."""
    # Mock Gateway Service response
    mock_response_data = {
        "text": "Hello, I'm an AI assistant.",
        "model": "gpt-4",
        "usage": {"total_tokens": 15},
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        # Setup mock response
        mock_response = Mock()
        mock_response.json = Mock(return_value=mock_response_data)
        mock_response.raise_for_status = Mock()
        mock_response.status_code = 200

        # Setup mock client
        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client_instance

        # Create service client
        gateway_client = ServiceHTTPClient(
            service_name="gateway",
            service_url="http://gateway-service:8080",
        )

        # Test async service call
        response = await gateway_client.post(
            "/api/v1/gateway/generate",
            json_data={"prompt": "Hello", "model": "gpt-4"},
        )

        # Verify response
        assert response == mock_response_data
        assert response["text"] == "Hello, I'm an AI assistant."
        assert response["model"] == "gpt-4"


@pytest.mark.asyncio
async def test_rag_service_calls_gateway_service():
    """Test that RAG Service can call Gateway Service for embeddings."""
    # Mock Gateway Service response
    mock_response_data = {
        "embeddings": [[0.1, 0.2, 0.3]],
        "model": "text-embedding-3-small",
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        # Setup mock response
        mock_response = Mock()
        mock_response.json = Mock(return_value=mock_response_data)
        mock_response.raise_for_status = Mock()
        mock_response.status_code = 200

        # Setup mock client
        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client_instance

        # Create service client
        gateway_client = ServiceHTTPClient(
            service_name="gateway",
            service_url="http://gateway-service:8080",
        )

        # Test async service call for embeddings
        response = await gateway_client.post(
            "/api/v1/gateway/embed",
            json_data={"text": "Test document", "model": "text-embedding-3-small"},
        )

        # Verify response
        assert response == mock_response_data
        assert "embeddings" in response
        assert len(response["embeddings"]) > 0
        assert response["model"] == "text-embedding-3-small"


@pytest.mark.asyncio
async def test_data_ingestion_service_calls_rag_service():
    """Test that Data Ingestion Service can call RAG Service."""
    # Mock RAG Service response
    mock_response_data = {
        "success": True,
        "data": {"document_id": "doc_123"},
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        # Setup mock response
        mock_response = Mock()
        mock_response.json = Mock(return_value=mock_response_data)
        mock_response.raise_for_status = Mock()
        mock_response.status_code = 200

        # Setup mock client
        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client_instance

        # Create service client
        rag_client = ServiceHTTPClient(
            service_name="rag",
            service_url="http://rag-service:8080",
        )

        # Test async service call for document ingestion
        response = await rag_client.post(
            "/api/v1/rag/documents",
            json_data={"content": "Test document content", "metadata": {}},
        )

        # Verify response
        assert response == mock_response_data
        assert response["success"] is True
        assert "document_id" in response["data"]
        assert response["data"]["document_id"] == "doc_123"
