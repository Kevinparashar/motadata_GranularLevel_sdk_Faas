"""
Unit Tests for CodecManager Without Fallback

Tests CodecManager behavior when core codec is required (no fallback).
"""

import pytest

from src.faas.integrations.codec import CodecManager, create_codec_manager


class TestCodecManagerNoFallback:
    """Tests for CodecManager without fallback logic."""

    def test_codec_manager_requires_core_codec(self):
        """Test that CodecManager requires core codec (no fallback)."""
        manager = CodecManager(codec_type="json")
        
        # Should have core codec (not None)
        assert manager._codec is not None
        assert hasattr(manager._codec, "encode")
        assert hasattr(manager._codec, "decode")
        assert hasattr(manager._codec, "create_envelope")

    def test_codec_manager_no_fallback_on_init(self):
        """Test that CodecManager doesn't fallback on initialization."""
        manager = CodecManager(codec_type="json")
        
        # Should directly use core codec, no conditional logic
        assert manager._codec is not None

    @pytest.mark.asyncio
    async def test_encode_uses_core_codec(self):
        """Test that encode uses core codec directly."""
        manager = CodecManager(codec_type="json")
        data = {"key": "value"}
        
        result = await manager.encode(data)
        
        assert isinstance(result, bytes)
        # Should be valid JSON envelope
        decoded = await manager.decode(result)
        assert "schema_version" in decoded
        assert "message_type" in decoded
        assert "data" in decoded

    @pytest.mark.asyncio
    async def test_decode_uses_core_codec(self):
        """Test that decode uses core codec directly."""
        manager = CodecManager(codec_type="json")
        data = {"key": "value"}
        
        # Encode first
        encoded = await manager.encode(data)
        
        # Decode
        decoded = await manager.decode(encoded)
        
        assert isinstance(decoded, dict)
        assert decoded["data"]["key"] == "value"

    def test_create_envelope_uses_core_codec(self):
        """Test that create_envelope uses core codec directly."""
        manager = CodecManager(codec_type="json")
        
        envelope = manager.create_envelope("test_message", "1.0", {"key": "value"})
        
        assert envelope["schema_version"] == "1.0"
        assert envelope["message_type"] == "test_message"
        assert envelope["data"]["key"] == "value"
        assert "created_at" in envelope  # Added by core codec

    def test_validate_schema_uses_core_codec(self):
        """Test that validate_schema uses core codec directly."""
        manager = CodecManager(codec_type="json")
        
        # Create valid envelope
        envelope = manager.create_envelope("agent_message", "1.0", {
            "message_id": "msg_123",
            "source_agent_id": "agent_1",
            "target_agent_id": "agent_2",
            "content": "Hello",
        })
        
        # Should validate successfully
        result = manager.validate_schema(envelope, "agent_message")
        assert result is True

    def test_codec_manager_invalid_type_still_rejected(self):
        """Test that invalid codec_type is still rejected at init."""
        with pytest.raises(ValueError, match="Unsupported codec type"):
            CodecManager(codec_type="msgpack")
        
        with pytest.raises(ValueError, match="Unsupported codec type"):
            CodecManager(codec_type="protobuf")

    @pytest.mark.asyncio
    async def test_encode_decode_roundtrip_no_fallback(self):
        """Test encode/decode roundtrip without fallback."""
        manager = CodecManager(codec_type="json")
        original_data = {
            "message_id": "msg_123",
            "content": "Hello World",
            "metadata": {"key": "value"},
        }
        
        # Encode
        encoded = await manager.encode(original_data)
        assert isinstance(encoded, bytes)
        
        # Decode
        decoded = await manager.decode(encoded)
        
        # Verify data integrity
        assert decoded["data"] == original_data
        assert decoded["schema_version"] == "1.0"
        assert decoded["message_type"] == "generic_message"

    def test_create_codec_manager_with_config(self):
        """Test create_codec_manager with config (no fallback)."""
        from unittest.mock import MagicMock, patch
        
        mock_config = MagicMock()
        mock_config.codec_type = "json"
        
        with patch("src.faas.shared.config.get_config", return_value=mock_config):
            manager = create_codec_manager()
            
            assert isinstance(manager, CodecManager)
            assert manager.codec_type == "json"
            assert manager._codec is not None  # Core codec required

    def test_create_codec_manager_with_invalid_config(self):
        """Test create_codec_manager with invalid codec_type in config."""
        from unittest.mock import MagicMock, patch
        
        # Config validation should catch this before CodecManager init
        # But if it somehow gets through, CodecManager should reject it
        mock_config = MagicMock()
        mock_config.codec_type = "msgpack"
        
        with patch("src.faas.shared.config.get_config", return_value=mock_config):
            # CodecManager should reject invalid type
            with pytest.raises(ValueError, match="Unsupported codec type"):
                create_codec_manager()

