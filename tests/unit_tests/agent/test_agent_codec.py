"""
Unit Tests for Agent Codec Integration

Tests codec encoding/decoding for agent messages.
"""

from unittest.mock import MagicMock

import pytest

from src.core.agno_agent_framework import Agent, AgentMessage
from src.core.codec_integration import create_codec_serializer


class TestAgentCodecIntegration:
    """Tests for Agent codec integration."""

    @pytest.fixture
    def agent(self):
        """Create a test agent."""
        gateway = MagicMock()
        return Agent(agent_id="test-agent", name="Test Agent", gateway=gateway)

    @pytest.fixture
    def codec(self):
        """Create a test codec serializer."""
        return create_codec_serializer()

    @pytest.mark.asyncio
    async def test_encode_message_with_codec(self, agent, codec):
        """Test encoding message with codec serializer."""
        agent.codec_serializer = codec
        message = AgentMessage(
            from_agent="agent_1",
            to_agent="agent_2",
            content="Hello",
            message_type="text",
        )

        encoded = await agent.encode_message(message)

        assert isinstance(encoded, bytes)
        assert b"agent_1" in encoded
        assert b"agent_2" in encoded

    @pytest.mark.asyncio
    async def test_encode_message_without_codec(self, agent):
        """Test encoding message without codec serializer (should use default)."""
        message = AgentMessage(
            from_agent="agent_1",
            to_agent="agent_2",
            content="Hello",
        )

        # Should work with default codec from import
        encoded = await agent.encode_message(message)

        assert isinstance(encoded, bytes)

    @pytest.mark.asyncio
    async def test_decode_message_with_codec(self, agent, codec):
        """Test decoding message with codec serializer."""
        agent.codec_serializer = codec
        original_message = AgentMessage(
            from_agent="agent_1",
            to_agent="agent_2",
            content="Hello",
            message_type="text",
        )

        encoded = await agent.encode_message(original_message)
        decoded = await agent.decode_message(encoded)

        assert decoded.from_agent == original_message.from_agent
        assert decoded.to_agent == original_message.to_agent
        assert decoded.content == original_message.content

    @pytest.mark.asyncio
    async def test_decode_message_without_codec(self, agent):
        """Test decoding message without codec serializer (should use default)."""
        message = AgentMessage(from_agent="agent_1", to_agent="agent_2", content="Hello")
        encoded = await agent.encode_message(message)

        # Should work with default codec from import
        decoded = await agent.decode_message(encoded)

        assert decoded.from_agent == message.from_agent
        assert decoded.content == message.content

    @pytest.mark.asyncio
    async def test_encode_decode_roundtrip(self, agent, codec):
        """Test encode/decode roundtrip."""
        agent.codec_serializer = codec
        original = AgentMessage(
            from_agent="agent_1",
            to_agent="agent_2",
            content="Test message",
            message_type="text",
            metadata={"key": "value"},
        )

        encoded = await agent.encode_message(original)
        decoded = await agent.decode_message(encoded)

        assert decoded.from_agent == original.from_agent
        assert decoded.to_agent == original.to_agent
        assert decoded.content == original.content
        assert decoded.message_type == original.message_type
        assert decoded.metadata == original.metadata

    @pytest.mark.asyncio
    async def test_send_message_with_codec(self, agent, codec):
        """Test send_message still works with codec configured."""
        agent.codec_serializer = codec

        await agent.send_message(to_agent="agent_2", content="Hello")

        assert len(agent.message_queue) == 1
        assert agent.message_queue[0].to_agent == "agent_2"
        assert agent.message_queue[0].content == "Hello"

