"""
Unit Tests for CODEC Serializer

Tests codec serialization, schema validation, and version migration.
"""

from datetime import datetime

import pytest

from src.core.codec_integration import CodecSerializer, create_codec_serializer
from src.core.codec_integration.exceptions import (
    CodecDecodingError,
    CodecEncodingError,
    MigrationError,
    SchemaValidationError,
)


class TestCodecSerializer:
    """Tests for CodecSerializer class."""

    @pytest.fixture
    def codec(self):
        """Create a test codec serializer."""
        return create_codec_serializer(codec_type="json")

    def test_init_default(self):
        """Test CodecSerializer initialization with defaults."""
        codec = CodecSerializer()

        assert codec.codec_type == "json"
        assert codec.schema_registry is not None
        assert codec.migration_manager is not None

    def test_init_with_type(self):
        """Test CodecSerializer initialization with codec type."""
        codec = CodecSerializer(codec_type="json")

        assert codec.codec_type == "json"

    def test_create_envelope(self, codec):
        """Test envelope creation."""
        data = {"message_id": "msg_123", "content": "Hello"}
        envelope = codec.create_envelope("agent_message", "1.0", data)

        assert envelope["schema_version"] == "1.0"
        assert envelope["message_type"] == "agent_message"
        assert envelope["data"] == data
        assert "created_at" in envelope

    @pytest.mark.asyncio
    async def test_encode_json(self, codec):
        """Test encode with JSON codec."""
        envelope = codec.create_envelope("agent_message", "1.0", {"key": "value"})

        result = await codec.encode(envelope)

        assert isinstance(result, bytes)
        assert b"agent_message" in result
        assert b"key" in result

    @pytest.mark.asyncio
    async def test_encode_complex_data(self, codec):
        """Test encode with complex data structures."""
        envelope = codec.create_envelope(
            "agent_message",
            "1.0",
            {
                "string": "test",
                "number": 123,
                "float": 45.67,
                "bool": True,
                "list": [1, 2, 3],
                "nested": {"key": "value"},
                "timestamp": datetime.now(),
            },
        )

        result = await codec.encode(envelope)

        assert isinstance(result, bytes)
        decoded = await codec.decode(result)
        assert decoded["data"]["string"] == "test"
        assert decoded["data"]["number"] == 123

    @pytest.mark.asyncio
    async def test_encode_error(self, codec):
        """Test encode error handling."""
        # Create envelope with non-serializable data (circular reference)
        data = {}
        data["self"] = data
        envelope = codec.create_envelope("agent_message", "1.0", data)

        with pytest.raises(CodecEncodingError):
            await codec.encode(envelope)

    @pytest.mark.asyncio
    async def test_decode_json(self, codec):
        """Test decode with JSON codec."""
        envelope = codec.create_envelope("agent_message", "1.0", {"key": "value"})
        encoded = await codec.encode(envelope)

        result = await codec.decode(encoded)

        assert result["schema_version"] == "1.0"
        assert result["message_type"] == "agent_message"
        assert result["data"]["key"] == "value"

    @pytest.mark.asyncio
    async def test_decode_invalid_json(self, codec):
        """Test decode with invalid JSON."""
        invalid_payload = b"invalid json {"

        with pytest.raises(CodecDecodingError):
            await codec.decode(invalid_payload)

    @pytest.mark.asyncio
    async def test_decode_unsupported_type(self):
        """Test decode with unsupported codec type."""
        codec = CodecSerializer(codec_type="unsupported")

        with pytest.raises(CodecDecodingError):
            await codec.decode(b"test")

    @pytest.mark.asyncio
    async def test_encode_decode_roundtrip(self, codec):
        """Test encode and decode roundtrip."""
        original_data = {
            "message_id": "msg_123",
            "content": "Hello World",
            "metadata": {"key": "value"},
        }
        envelope = codec.create_envelope("agent_message", "1.0", original_data)

        encoded = await codec.encode(envelope)
        decoded = await codec.decode(encoded)

        assert decoded["data"] == original_data

    def test_validate_schema_valid(self, codec):
        """Test schema validation with valid envelope."""
        envelope = codec.create_envelope(
            "agent_message",
            "1.0",
            {
                "message_id": "msg_123",
                "source_agent_id": "agent_1",
                "target_agent_id": "agent_2",
                "content": "Hello",
            },
        )

        result = codec.validate_schema(envelope, "agent_message")

        assert result is True

    def test_validate_schema_missing_required(self, codec):
        """Test schema validation with missing required fields."""
        envelope = codec.create_envelope(
            "agent_message",
            "1.0",
            {
                "message_id": "msg_123",
                # Missing required fields
            },
        )

        with pytest.raises(SchemaValidationError):
            codec.validate_schema(envelope, "agent_message")

    def test_validate_schema_invalid_type(self, codec):
        """Test schema validation with invalid message type."""
        envelope = codec.create_envelope("unknown_message", "1.0", {})

        with pytest.raises(SchemaValidationError):
            codec.validate_schema(envelope, "unknown_message")

    def test_register_schema(self, codec):
        """Test schema registration."""
        codec.register_schema(
            schema_name="custom_message",
            version="1.0",
            schema_definition={
                "type": "object",
                "required": ["field1"],
                "properties": {"field1": {"type": "string"}},
            },
            is_default=True,
        )

        schema = codec.schema_registry.get_schema("custom_message", "1.0")
        assert schema["type"] == "object"

    def test_migrate_envelope_same_version(self, codec):
        """Test migration when versions are the same."""
        envelope = codec.create_envelope("agent_message", "1.0", {"key": "value"})

        result = codec.migrate_envelope(envelope, "1.0", "agent_message")

        assert result == envelope

    def test_migrate_envelope_no_migration(self, codec):
        """Test migration when no migration function exists."""
        envelope = codec.create_envelope("agent_message", "1.0", {"key": "value"})

        with pytest.raises(MigrationError):
            codec.migrate_envelope(envelope, "2.0", "agent_message")

    def test_migrate_envelope_with_migration(self, codec):
        """Test migration with registered migration function."""
        # Register migration
        def migrate_v1_to_v2(old_envelope: dict) -> dict:
            """Migrate from v1.0 to v2.0."""
            new_data = old_envelope["data"].copy()
            new_data["version"] = "2.0"
            return {
                "schema_version": "2.0",
                "message_type": old_envelope["message_type"],
                "data": new_data,
            }

        codec.register_migration("agent_message", "1.0", "2.0", migrate_v1_to_v2)

        envelope = codec.create_envelope("agent_message", "1.0", {"key": "value"})
        result = codec.migrate_envelope(envelope, "2.0", "agent_message")

        assert result["schema_version"] == "2.0"
        assert result["data"]["version"] == "2.0"


class TestCreateCodecSerializer:
    """Tests for create_codec_serializer factory function."""

    def test_create_codec_serializer_default(self):
        """Test create_codec_serializer with defaults."""
        codec = create_codec_serializer()

        assert isinstance(codec, CodecSerializer)
        assert codec.codec_type == "json"

    def test_create_codec_serializer_with_type(self):
        """Test create_codec_serializer with codec type."""
        codec = create_codec_serializer(codec_type="json")

        assert isinstance(codec, CodecSerializer)
        assert codec.codec_type == "json"

    def test_create_codec_serializer_with_registry(self):
        """Test create_codec_serializer with custom registry."""
        from src.core.codec_integration.schema_registry import SchemaRegistry

        registry = SchemaRegistry()
        codec = create_codec_serializer(schema_registry=registry)

        assert codec.schema_registry == registry

    def test_create_codec_serializer_with_migration_manager(self):
        """Test create_codec_serializer with custom migration manager."""
        from src.core.codec_integration.migration_manager import MigrationManager

        manager = MigrationManager()
        codec = create_codec_serializer(migration_manager=manager)

        assert codec.migration_manager == manager

