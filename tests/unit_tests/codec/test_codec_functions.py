"""
Unit Tests for CODEC Integration Functions

Tests helper functions for component integration.
"""

from datetime import datetime

import pytest

from src.core.agno_agent_framework import AgentMessage
from src.core.codec_integration import (
    create_codec_serializer,
    decode_agent_message,
    decode_llm_response,
    decode_rag_query,
    encode_agent_message,
    encode_llm_request,
    encode_rag_document,
)


class TestEncodeAgentMessage:
    """Tests for encode_agent_message function."""

    @pytest.mark.asyncio
    async def test_encode_agent_message_pydantic(self):
        """Test encoding AgentMessage Pydantic model."""
        message = AgentMessage(
            from_agent="agent_1",
            to_agent="agent_2",
            content="Hello",
            message_type="text",
        )

        encoded = await encode_agent_message(message)

        assert isinstance(encoded, bytes)
        assert b"agent_1" in encoded
        assert b"agent_2" in encoded
        assert b"Hello" in encoded

    @pytest.mark.asyncio
    async def test_encode_agent_message_dict(self):
        """Test encoding agent message dictionary."""
        message_dict = {
            "from_agent": "agent_1",
            "to_agent": "agent_2",
            "content": "Hello",
        }

        encoded = await encode_agent_message(message_dict)

        assert isinstance(encoded, bytes)

    @pytest.mark.asyncio
    async def test_encode_agent_message_with_codec(self):
        """Test encoding with custom codec."""
        codec = create_codec_serializer()
        message = AgentMessage(from_agent="a1", to_agent="a2", content="Hello")

        encoded = await encode_agent_message(message, codec=codec)

        assert isinstance(encoded, bytes)

    @pytest.mark.asyncio
    async def test_encode_agent_message_custom_version(self):
        """Test encoding with custom schema version."""
        message = AgentMessage(from_agent="a1", to_agent="a2", content="Hello")

        encoded = await encode_agent_message(message, schema_version="1.0")

        assert isinstance(encoded, bytes)


class TestDecodeAgentMessage:
    """Tests for decode_agent_message function."""

    @pytest.mark.asyncio
    async def test_decode_agent_message(self):
        """Test decoding agent message."""
        message = AgentMessage(from_agent="a1", to_agent="a2", content="Hello")
        encoded = await encode_agent_message(message)

        decoded = await decode_agent_message(encoded)

        assert decoded["source_agent_id"] == "a1"
        assert decoded["target_agent_id"] == "a2"
        assert decoded["content"] == "Hello"

    @pytest.mark.asyncio
    async def test_decode_agent_message_with_codec(self):
        """Test decoding with custom codec."""
        codec = create_codec_serializer()
        message = AgentMessage(from_agent="a1", to_agent="a2", content="Hello")
        encoded = await encode_agent_message(message, codec=codec)

        decoded = await decode_agent_message(encoded, codec=codec)

        assert decoded["content"] == "Hello"

    @pytest.mark.asyncio
    async def test_decode_agent_message_roundtrip(self):
        """Test encode/decode roundtrip."""
        original = AgentMessage(
            from_agent="agent_1",
            to_agent="agent_2",
            content="Test message",
            message_type="text",
            metadata={"key": "value"},
        )

        encoded = await encode_agent_message(original)
        decoded = await decode_agent_message(encoded)

        assert decoded["source_agent_id"] == original.from_agent
        assert decoded["target_agent_id"] == original.to_agent
        assert decoded["content"] == original.content


class TestEncodeLLMRequest:
    """Tests for encode_llm_request function."""

    @pytest.mark.asyncio
    async def test_encode_llm_request(self):
        """Test encoding LLM request."""
        encoded = await encode_llm_request(
            request_id="req_123",
            prompt="Hello",
            model="gpt-4",
            tenant_id="tenant_123",
        )

        assert isinstance(encoded, bytes)
        assert b"req_123" in encoded
        assert b"Hello" in encoded
        assert b"gpt-4" in encoded

    @pytest.mark.asyncio
    async def test_encode_llm_request_with_parameters(self):
        """Test encoding LLM request with parameters."""
        encoded = await encode_llm_request(
            request_id="req_123",
            prompt="Hello",
            model="gpt-4",
            tenant_id="tenant_123",
            parameters={"temperature": 0.7, "max_tokens": 100},
        )

        assert isinstance(encoded, bytes)
        # Verify encoding contains the parameters
        assert b"temperature" in encoded
        assert b"0.7" in encoded


class TestDecodeLLMResponse:
    """Tests for decode_llm_response function."""

    @pytest.mark.asyncio
    async def test_decode_llm_response(self):
        """Test decoding LLM response."""
        # Create a response envelope
        from src.core.codec_integration import create_codec_serializer

        codec = create_codec_serializer()
        response_envelope = codec.create_envelope(
            "llm_response",
            "1.0",
            {
                "request_id": "req_123",
                "response": "Generated text",
                "model": "gpt-4",
                "tokens": {"prompt": 10, "completion": 5, "total": 15},
                "cost": 0.01,
            },
        )
        encoded_response = await codec.encode(response_envelope)

        decoded = await decode_llm_response(encoded_response)

        assert decoded["request_id"] == "req_123"
        assert decoded["response"] == "Generated text"
        assert decoded["model"] == "gpt-4"


class TestEncodeRAGDocument:
    """Tests for encode_rag_document function."""

    @pytest.mark.asyncio
    async def test_encode_rag_document(self):
        """Test encoding RAG document."""
        encoded = await encode_rag_document(
            document_id="doc_123",
            content="Document content",
            tenant_id="tenant_123",
        )

        assert isinstance(encoded, bytes)
        assert b"doc_123" in encoded
        assert b"Document content" in encoded

    @pytest.mark.asyncio
    async def test_encode_rag_document_with_metadata(self):
        """Test encoding RAG document with metadata."""
        encoded = await encode_rag_document(
            document_id="doc_123",
            content="Document content",
            tenant_id="tenant_123",
            metadata={"title": "Test", "author": "Author"},
            chunks=[{"chunk_id": "chunk_1", "content": "Chunk content"}],
        )

        assert isinstance(encoded, bytes)
        # Verify encoding contains the metadata and chunks
        assert b"title" in encoded
        assert b"Test" in encoded
        assert b"chunk_1" in encoded


class TestDecodeRAGQuery:
    """Tests for decode_rag_query function."""

    @pytest.mark.asyncio
    async def test_decode_rag_query(self):
        """Test decoding RAG query."""
        from src.core.codec_integration import create_codec_serializer

        codec = create_codec_serializer()
        query_envelope = codec.create_envelope(
            "rag_query",
            "1.0",
            {
                "query_id": "query_123",
                "query": "Test query",
                "tenant_id": "tenant_123",
                "parameters": {"top_k": 5},
            },
        )
        encoded = await codec.encode(query_envelope)

        decoded = await decode_rag_query(encoded)

        assert decoded["query_id"] == "query_123"
        assert decoded["query"] == "Test query"
        assert decoded["tenant_id"] == "tenant_123"

