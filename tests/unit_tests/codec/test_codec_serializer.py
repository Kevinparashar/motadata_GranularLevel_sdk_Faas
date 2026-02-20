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

    def test_init_unsupported_codec_type(self):
        """Test CodecSerializer initialization with unsupported codec type."""
        with pytest.raises(ValueError, match="Unsupported codec type"):
            CodecSerializer(codec_type="msgpack")
        
        with pytest.raises(ValueError, match="Unsupported codec type"):
            CodecSerializer(codec_type="protobuf")
        
        with pytest.raises(ValueError, match="Unsupported codec type"):
            CodecSerializer(codec_type="unsupported")

    @pytest.mark.asyncio
    async def test_decode_unsupported_type(self, codec):
        """Test decode with unsupported codec type (should not happen with validation)."""
        # This test is kept for backward compatibility but should not occur
        # since initialization now validates codec_type
        pass

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

    def test_validate_schema_type_validation(self, codec):
        """Test schema validation with type mismatches (JSON Schema validation)."""
        # Register a schema with strict type requirements
        codec.register_schema(
            schema_name="typed_message",
            version="1.0",
            schema_definition={
                "type": "object",
                "required": ["string_field", "number_field", "boolean_field"],
                "properties": {
                    "string_field": {"type": "string"},
                    "number_field": {"type": "number"},
                    "boolean_field": {"type": "boolean"},
                },
            },
            is_default=True,
        )

        # Test with wrong type (string instead of number)
        envelope = codec.create_envelope(
            "typed_message",
            "1.0",
            {
                "string_field": "test",
                "number_field": "not_a_number",  # Should be number
                "boolean_field": True,
            },
        )

        with pytest.raises(SchemaValidationError) as exc_info:
            codec.validate_schema(envelope, "typed_message")
        
        assert "typed_message" in str(exc_info.value)
        assert len(exc_info.value.validation_errors) > 0

    def test_validate_schema_nested_validation(self, codec):
        """Test schema validation with nested objects (JSON Schema validation)."""
        codec.register_schema(
            schema_name="nested_message",
            version="1.0",
            schema_definition={
                "type": "object",
                "required": ["nested"],
                "properties": {
                    "nested": {
                        "type": "object",
                        "required": ["inner_field"],
                        "properties": {
                            "inner_field": {"type": "string"},
                        },
                    },
                },
            },
            is_default=True,
        )

        # Test with missing nested field
        envelope = codec.create_envelope(
            "nested_message",
            "1.0",
            {
                "nested": {},  # Missing inner_field
            },
        )

        with pytest.raises(SchemaValidationError):
            codec.validate_schema(envelope, "nested_message")

    def test_validate_schema_array_validation(self, codec):
        """Test schema validation with arrays (JSON Schema validation)."""
        codec.register_schema(
            schema_name="array_message",
            version="1.0",
            schema_definition={
                "type": "object",
                "required": ["items"],
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
            },
            is_default=True,
        )

        # Test with invalid array item type
        envelope = codec.create_envelope(
            "array_message",
            "1.0",
            {
                "items": [1, 2, 3],  # Should be strings
            },
        )

        with pytest.raises(SchemaValidationError):
            codec.validate_schema(envelope, "array_message")

    def test_validate_schema_enum_validation(self, codec):
        """Test schema validation with enum constraints (JSON Schema validation)."""
        codec.register_schema(
            schema_name="enum_message",
            version="1.0",
            schema_definition={
                "type": "object",
                "required": ["status"],
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["active", "inactive", "pending"],
                    },
                },
            },
            is_default=True,
        )

        # Test with invalid enum value
        envelope = codec.create_envelope(
            "enum_message",
            "1.0",
            {
                "status": "invalid_status",  # Not in enum
            },
        )

        with pytest.raises(SchemaValidationError):
            codec.validate_schema(envelope, "enum_message")

    def test_validate_schema_valid_complex(self, codec):
        """Test schema validation with valid complex data (JSON Schema validation)."""
        codec.register_schema(
            schema_name="complex_message",
            version="1.0",
            schema_definition={
                "type": "object",
                "required": ["name", "age", "active", "tags", "metadata"],
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "number"},
                    "active": {"type": "boolean"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "metadata": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string"},
                        },
                    },
                },
            },
            is_default=True,
        )

        # Test with valid complex data
        envelope = codec.create_envelope(
            "complex_message",
            "1.0",
            {
                "name": "test",
                "age": 25,
                "active": True,
                "tags": ["tag1", "tag2"],
                "metadata": {"key": "value"},
            },
        )

        result = codec.validate_schema(envelope, "complex_message")
        assert result is True

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

