"""
Unit tests for codec.py
"""

from unittest.mock import MagicMock, patch

import pytest

from src.faas.integrations.codec import CodecManager, create_codec_manager


class TestCodecManager:
    """Tests for CodecManager class."""

    def test_init_default(self):
        """Test CodecManager initialization with default codec type."""
        manager = CodecManager()

        assert manager.codec_type == "json"

    def test_init_with_type(self):
        """Test CodecManager initialization with codec type."""
        manager = CodecManager(codec_type="msgpack")

        assert manager.codec_type == "msgpack"

    @pytest.mark.asyncio
    async def test_encode_json(self):
        """Test encode with JSON codec."""
        manager = CodecManager(codec_type="json")
        data = {"key": "value", "number": 123}

        result = await manager.encode(data)

        assert isinstance(result, bytes)
        decoded = await manager.decode(result)
        # Decode returns envelope, extract data
        assert decoded.get("data") == data
        assert "schema_version" in decoded
        assert "message_type" in decoded

    @pytest.mark.asyncio
    async def test_encode_json_complex(self):
        """Test encode with JSON codec and complex data."""
        manager = CodecManager(codec_type="json")
        data = {
            "string": "test",
            "number": 123,
            "float": 45.67,
            "bool": True,
            "list": [1, 2, 3],
            "nested": {"key": "value"},
        }

        result = await manager.encode(data)

        assert isinstance(result, bytes)
        decoded = await manager.decode(result)
        # Decode returns envelope, extract data
        assert decoded.get("data") == data

    @pytest.mark.asyncio
    async def test_encode_msgpack_fallback(self):
        """Test encode with msgpack codec (falls back to JSON)."""
        manager = CodecManager(codec_type="msgpack")
        data = {"key": "value"}

        result = await manager.encode(data)

        assert isinstance(result, bytes)
        # Should fall back to JSON
        decoded = await manager.decode(result)
        assert decoded.get("data") == data

    @pytest.mark.asyncio
    async def test_encode_protobuf_fallback(self):
        """Test encode with protobuf codec (falls back to JSON)."""
        manager = CodecManager(codec_type="protobuf")
        data = {"key": "value"}

        result = await manager.encode(data)

        assert isinstance(result, bytes)
        # Should fall back to JSON
        decoded = await manager.decode(result)
        assert decoded.get("data") == data

    @pytest.mark.asyncio
    async def test_encode_unsupported_type(self):
        """Test encode with unsupported codec type."""
        manager = CodecManager(codec_type="unsupported")

        with pytest.raises(ValueError, match="Unsupported codec type"):
            await manager.encode({"key": "value"})

    @pytest.mark.asyncio
    async def test_decode_json(self):
        """Test decode with JSON codec."""
        manager = CodecManager(codec_type="json")
        data = {"key": "value", "number": 123}
        # Encode first to get proper envelope structure
        encoded = await manager.encode(data)
        decoded = await manager.decode(encoded)

        # Decode returns envelope, extract data
        assert decoded.get("data") == data

    @pytest.mark.asyncio
    async def test_decode_json_complex(self):
        """Test decode with JSON codec and complex data."""
        manager = CodecManager(codec_type="json")
        data = {
            "string": "test",
            "number": 123,
            "float": 45.67,
            "bool": True,
            "list": [1, 2, 3],
            "nested": {"key": "value"},
        }
        # Encode first to get proper envelope structure
        encoded = await manager.encode(data)
        result = await manager.decode(encoded)

        # Decode returns envelope, extract data
        assert result.get("data") == data

    @pytest.mark.asyncio
    async def test_decode_msgpack_fallback(self):
        """Test decode with msgpack codec (falls back to JSON)."""
        manager = CodecManager(codec_type="msgpack")
        data = {"key": "value"}
        # Encode first to get proper envelope structure
        encoded = await manager.encode(data)
        result = await manager.decode(encoded)

        # Decode returns envelope, extract data
        assert result.get("data") == data

    @pytest.mark.asyncio
    async def test_decode_protobuf_fallback(self):
        """Test decode with protobuf codec (falls back to JSON)."""
        manager = CodecManager(codec_type="protobuf")
        data = {"key": "value"}
        # Encode first to get proper envelope structure
        encoded = await manager.encode(data)
        result = await manager.decode(encoded)

        # Decode returns envelope, extract data
        assert result.get("data") == data

    @pytest.mark.asyncio
    async def test_decode_unsupported_type(self):
        """Test decode with unsupported codec type."""
        manager = CodecManager(codec_type="unsupported")

        with pytest.raises(ValueError, match="Unsupported codec type"):
            await manager.decode(b"test data")

    @pytest.mark.asyncio
    async def test_encode_decode_roundtrip(self):
        """Test encode and decode roundtrip."""
        manager = CodecManager(codec_type="json")
        original_data = {"key": "value", "number": 123, "nested": {"inner": "data"}}

        encoded = await manager.encode(original_data)
        decoded = await manager.decode(encoded)

        # Decode returns envelope, extract data
        assert decoded.get("data") == original_data


class TestCreateCodecManager:
    """Tests for create_codec_manager factory function."""

    def test_create_codec_manager_with_type(self):
        """Test create_codec_manager with explicit codec type."""
        manager = create_codec_manager(codec_type="msgpack")

        assert isinstance(manager, CodecManager)
        assert manager.codec_type == "msgpack"

    def test_create_codec_manager_with_config(self):
        """Test create_codec_manager with config."""
        mock_config = MagicMock()
        mock_config.codec_type = "protobuf"

        with patch("src.faas.shared.config.get_config", return_value=mock_config):
            manager = create_codec_manager()

            assert isinstance(manager, CodecManager)
            assert manager.codec_type == "protobuf"

    def test_create_codec_manager_with_config_override(self):
        """Test create_codec_manager with config and override."""
        mock_config = MagicMock()
        mock_config.codec_type = "protobuf"

        with patch("src.faas.shared.config.get_config", return_value=mock_config):
            manager = create_codec_manager(codec_type="msgpack")

            assert isinstance(manager, CodecManager)
            assert manager.codec_type == "msgpack"

    def test_create_codec_manager_config_not_loaded(self):
        """Test create_codec_manager when config not loaded."""
        with patch("src.faas.shared.config.get_config", side_effect=RuntimeError("Config not loaded")):
            manager = create_codec_manager()

            assert isinstance(manager, CodecManager)
            assert manager.codec_type == "json"  # Default

    def test_create_codec_manager_config_not_loaded_with_type(self):
        """Test create_codec_manager when config not loaded but type provided."""
        with patch("src.faas.shared.config.get_config", side_effect=RuntimeError("Config not loaded")):
            manager = create_codec_manager(codec_type="msgpack")

            assert isinstance(manager, CodecManager)
            assert manager.codec_type == "msgpack"

