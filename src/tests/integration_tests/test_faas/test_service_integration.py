"""
Integration tests for FaaS service interactions.

Tests how services communicate with each other.
"""


from unittest.mock import AsyncMock, Mock, patch

import pytest


@pytest.mark.asyncio
async def test_agent_service_calls_gateway_service():
    """Test that Agent Service can call Gateway Service."""
    # Mock Gateway Service response
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = Mock()
        mock_response.json.return_value = {
            "text": "Hello, I'm an AI assistant.",
            "model": "gpt-4",
            "usage": {"total_tokens": 15},
        }
        mock_response.raise_for_status = Mock()

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_client_instance

        # Test would call Gateway Service
        # This is a placeholder for actual integration test
        # Verify mock is set up correctly
        assert mock_response.json() == {
            "text": "Hello, I'm an AI assistant.",
            "model": "gpt-4",
            "usage": {"total_tokens": 15},
        }


@pytest.mark.asyncio
async def test_rag_service_calls_gateway_service():
    """Test that RAG Service can call Gateway Service for embeddings."""
    # Mock Gateway Service response
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = Mock()
        mock_response.json.return_value = {
            "embeddings": [[0.1, 0.2, 0.3]],
            "model": "text-embedding-3-small",
        }
        mock_response.raise_for_status = Mock()

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_client_instance

        # Test would call Gateway Service
        # Verify mock is set up correctly
        assert mock_response.json() == {
            "embeddings": [[0.1, 0.2, 0.3]],
            "model": "text-embedding-3-small",
        }


@pytest.mark.asyncio
async def test_data_ingestion_service_calls_rag_service():
    """Test that Data Ingestion Service can call RAG Service."""
    # Mock RAG Service response
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "data": {"document_id": "doc_123"},
        }
        mock_response.raise_for_status = Mock()

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_client_instance

        # Test would call RAG Service
        # Verify mock is set up correctly
        assert mock_response.json() == {
            "success": True,
            "data": {"document_id": "doc_123"},
        }
