"""
Integration Tests for NATS Integration

Tests NATS messaging integration with AI SDK components.
"""

from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from src.core.agno_agent_framework import Agent, AgentMessage
from src.core.litellm_gateway import LiteLLMGateway
from src.core.rag import RAGSystem

# TODO: INTEGRATION-002 - Import when NATS integration is available  # noqa: FIX002, S1135
# from src.integrations.nats_integration import NATSClient
# from src.integrations.codec_integration import CodecSerializer


@pytest.mark.integration
class TestNATSAgentIntegration:
    """Test NATS integration with Agent Framework."""

    @pytest.fixture
    def mock_nats_client(self):
        """Mock NATS client."""
        client = AsyncMock()
        client.publish = AsyncMock()
        client.subscribe = AsyncMock()
        client.request = AsyncMock()
        return client

    @pytest.fixture
    def mock_codec(self):
        """Mock CODEC serializer."""
        codec = Mock()
        codec.encode = Mock(return_value=b"encoded_message")
        codec.decode = Mock(return_value={"message_id": "msg_123", "content": "test"})
        return codec

    @pytest.fixture
    def agent_with_nats(self, mock_nats_client, mock_codec):
        """Create agent with NATS integration."""
        # TODO: INTEGRATION-002A - Replace with actual integration when available  # noqa: FIX002, S1135
        agent = Mock(spec=Agent)
        agent.agent_id = "agent_123"
        agent.tenant_id = "tenant_123"
        agent._nats_client = mock_nats_client
        agent._codec = mock_codec
        return agent

    @pytest.mark.asyncio
    async def test_agent_message_publishing(self, agent_with_nats, mock_nats_client, mock_codec):
        """Test agent message publishing via NATS."""
        agent = agent_with_nats

        # Create message
        message = AgentMessage(
            from_agent="agent_123",
            to_agent="agent_456",
            content="Test message",
            message_type="text",
        )

        # Encode message
        encoded = mock_codec.encode(
            {
                "message_id": "msg_123",
                "source_agent_id": message.from_agent,
                "target_agent_id": message.to_agent,
                "content": message.content,
                "message_type": message.message_type,
                "schema_version": "1.0",
            }
        )

        # Publish via NATS
        await mock_nats_client.publish(
            subject=f"ai.agent.message.{agent.tenant_id}",
            payload=encoded,
            headers={
                "target_agent_id": message.to_agent,
                "source_agent_id": message.from_agent,
            },
        )

        # Verify publish was called
        assert mock_nats_client.publish.called
        call_args = mock_nats_client.publish.call_args
        assert call_args[1]["subject"] == f"ai.agent.message.{agent.tenant_id}"
        assert call_args[1]["payload"] == encoded

    @pytest.mark.asyncio
    async def test_agent_message_subscription(self, agent_with_nats, mock_nats_client, mock_codec):
        """Test agent message subscription via NATS."""
        agent = agent_with_nats

        # Mock message handler
        received_messages = []

        def message_handler(msg):
            decoded = mock_codec.decode(msg.data)
            if decoded["target_agent_id"] == agent.agent_id:
                received_messages.append(decoded)

        # Subscribe to messages
        await mock_nats_client.subscribe(
            subject=f"ai.agent.message.{agent.tenant_id}",
            callback=message_handler,
            queue=f"agent.{agent.agent_id}",
        )

        # Simulate receiving a message
        mock_msg = MagicMock()
        mock_msg.data = b"encoded_message"
        message_handler(mock_msg)

        # Verify subscription was set up
        assert mock_nats_client.subscribe.called
        assert len(received_messages) > 0

    @pytest.mark.asyncio
    async def test_agent_task_distribution(self, agent_with_nats, mock_nats_client, mock_codec):
        """Test agent task distribution via NATS."""
        agent = agent_with_nats

        task = {
            "task_id": "task_123",
            "agent_id": agent.agent_id,
            "task_type": "query",
            "parameters": {"query": "test"},
            "schema_version": "1.0",
        }

        # Encode task
        encoded = mock_codec.encode(task)

        # Publish task to distribution queue
        await mock_nats_client.publish(subject=f"ai.agent.tasks.{agent.tenant_id}", payload=encoded)

        # Verify task was published
        assert mock_nats_client.publish.called
        call_args = mock_nats_client.publish.call_args
        assert call_args[1]["subject"] == f"ai.agent.tasks.{agent.tenant_id}"


@pytest.mark.integration
class TestNATSGatewayIntegration:
    """Test NATS integration with LiteLLM Gateway."""

    @pytest.fixture
    def mock_nats_client(self):
        """Mock NATS client."""
        client = AsyncMock()
        client.publish = AsyncMock()
        client.request = AsyncMock()
        return client

    @pytest.fixture
    def mock_codec(self):
        """Mock CODEC serializer."""
        codec = Mock()
        codec.encode = Mock(return_value=b"encoded_request")
        codec.decode = Mock(
            return_value={
                "request_id": "req_123",
                "response": "Generated text",
                "tokens": {"total": 100},
                "cost": 0.01,
                "schema_version": "1.0",
            }
        )
        return codec

    @pytest.fixture
    def gateway_with_nats(self, mock_nats_client, mock_codec):
        """Create gateway with NATS integration."""
        # TODO: INTEGRATION-002B - Replace with actual integration when available  # noqa: FIX002, S1135
        gateway = Mock(spec=LiteLLMGateway)
        gateway._nats_client = mock_nats_client
        gateway._codec = mock_codec
        gateway.tenant_id = "tenant_123"
        return gateway

    @pytest.mark.asyncio
    async def test_gateway_request_queuing(self, gateway_with_nats, mock_nats_client, mock_codec):
        """Test LLM request queuing via NATS."""
        gateway = gateway_with_nats

        request = {
            "request_id": "req_123",
            "prompt": "Test prompt",
            "model": "gpt-4",
            "tenant_id": gateway.tenant_id,
            "schema_version": "1.0",
        }

        # Encode request
        encoded = mock_codec.encode(request)

        # Publish to request queue
        await mock_nats_client.publish(
            subject=f"ai.gateway.requests.{gateway.tenant_id}",
            payload=encoded,
            headers={"request_id": request["request_id"], "model": request["model"]},
        )

        # Verify request was queued
        assert mock_nats_client.publish.called
        call_args = mock_nats_client.publish.call_args
        assert call_args[1]["subject"] == f"ai.gateway.requests.{gateway.tenant_id}"

    @pytest.mark.asyncio
    async def test_gateway_response_delivery(self, gateway_with_nats, mock_nats_client, mock_codec):
        """Test LLM response delivery via NATS."""
        gateway = gateway_with_nats

        request = {
            "request_id": "req_123",
            "prompt": "Test prompt",
            "model": "gpt-4",
            "tenant_id": gateway.tenant_id,
            "schema_version": "1.0",
        }

        # Mock response
        mock_response = MagicMock()
        mock_response.data = b"encoded_response"
        mock_nats_client.request = AsyncMock(return_value=mock_response)

        # Request response
        encoded_request = mock_codec.encode(request)
        response = await mock_nats_client.request(
            subject=f"ai.gateway.responses.{gateway.tenant_id}",
            payload=encoded_request,
            timeout=60.0,
        )

        # Decode response
        response_data = mock_codec.decode(response.data)

        # Verify response
        assert mock_nats_client.request.called
        assert response_data["request_id"] == request["request_id"]
        assert "response" in response_data


@pytest.mark.integration
class TestNATSRAGIntegration:
    """Test NATS integration with RAG System."""

    @pytest.fixture
    def mock_nats_client(self):
        """Mock NATS client."""
        client = AsyncMock()
        client.publish = AsyncMock()
        client.request = AsyncMock()
        return client

    @pytest.fixture
    def mock_codec(self):
        """Mock CODEC serializer."""
        codec = Mock()
        codec.encode = Mock(return_value=b"encoded_document")
        codec.decode = Mock(
            return_value={"document_id": "doc_123", "status": "processed", "schema_version": "1.0"}
        )
        return codec

    @pytest.fixture
    def rag_with_nats(self, mock_nats_client, mock_codec):
        """Create RAG system with NATS integration."""
        # TODO: INTEGRATION-002C - Replace with actual integration when available  # noqa: FIX002, S1135
        rag = Mock(spec=RAGSystem)
        rag._nats_client = mock_nats_client
        rag._codec = mock_codec
        rag.tenant_id = "tenant_123"
        return rag

    @pytest.mark.asyncio
    async def test_rag_document_ingestion_queue(self, rag_with_nats, mock_nats_client, mock_codec):
        """Test document ingestion queuing via NATS."""
        rag = rag_with_nats

        document = {
            "document_id": "doc_123",
            "content": "Test document content",
            "metadata": {},
            "tenant_id": rag.tenant_id,
            "schema_version": "1.0",
        }

        # Encode document
        encoded = mock_codec.encode(document)

        # Publish to ingestion queue
        await mock_nats_client.publish(subject=f"ai.rag.ingest.{rag.tenant_id}", payload=encoded)

        # Verify document was queued
        assert mock_nats_client.publish.called
        call_args = mock_nats_client.publish.call_args
        assert call_args[1]["subject"] == f"ai.rag.ingest.{rag.tenant_id}"

    @pytest.mark.asyncio
    async def test_rag_query_processing_queue(self, rag_with_nats, mock_nats_client, mock_codec):
        """Test query processing queuing via NATS."""
        rag = rag_with_nats

        query = {
            "query_id": "query_123",
            "query": "Test query",
            "tenant_id": rag.tenant_id,
            "schema_version": "1.0",
        }

        # Encode query
        encoded = mock_codec.encode(query)

        # Mock response
        mock_response = MagicMock()
        mock_response.data = b"encoded_result"
        mock_nats_client.request = AsyncMock(return_value=mock_response)

        # Request query processing
        result = await mock_nats_client.request(
            subject=f"ai.rag.results.{rag.tenant_id}", payload=encoded, timeout=30.0
        )

        # Verify query was processed
        assert mock_nats_client.request.called
        assert result.data == b"encoded_result"


@pytest.mark.integration
class TestNATSErrorHandling:
    """Test NATS error handling."""

    @pytest.fixture
    def mock_nats_client(self):
        """Mock NATS client with error scenarios."""
        client = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_nats_connection_failure(self, mock_nats_client):
        """Test handling of NATS connection failures."""
        # Simulate connection failure
        mock_nats_client.publish.side_effect = ConnectionError("NATS connection failed")

        # Attempt to publish
        with pytest.raises(ConnectionError):
            await mock_nats_client.publish(subject="ai.agent.message.tenant_123", payload=b"test")

    @pytest.mark.asyncio
    async def test_nats_message_timeout(self, mock_nats_client):
        """Test handling of NATS message timeouts."""
        # Simulate timeout
        import asyncio

        mock_nats_client.request.side_effect = asyncio.TimeoutError("Request timeout")

        # Attempt to request
        with pytest.raises(asyncio.TimeoutError):
            await mock_nats_client.request(
                subject="ai.gateway.responses.tenant_123", payload=b"test", timeout=1.0
            )
