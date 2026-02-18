"""
Unit Tests for CODEC Integration - Registry, Migration, and Edge Cases

Tests for schema registry, migration manager, and edge cases in codec integration.
"""

import pytest

from src.core.codec_integration import (
    create_codec_serializer,
    decode_agent_message,
    decode_llm_response,
    decode_rag_query,
    encode_agent_message,
)
from src.core.codec_integration.exceptions import (
    MigrationError,
    SchemaValidationError,
    SchemaVersionError,
)
from src.core.codec_integration.migration_manager import MigrationManager
from src.core.codec_integration.schema_registry import SchemaRegistry
from src.core.agno_agent_framework import AgentMessage


class TestCodecFunctionsEdgeCases:
    """Tests for edge cases in codec helper functions."""

    @pytest.mark.asyncio
    async def test_encode_agent_message_with_dict_method(self):
        """Test encoding message with dict() method (Pydantic V1 style)."""
        # Create a mock object with dict() method but no model_dump()
        class MockMessageV1:
            def dict(self):
                return {
                    "from_agent": "agent_1",
                    "to_agent": "agent_2",
                    "content": "Hello",
                    "message_type": "text",
                }

        message = MockMessageV1()
        encoded = await encode_agent_message(message)

        assert isinstance(encoded, bytes)
        assert b"agent_1" in encoded

    @pytest.mark.asyncio
    async def test_encode_agent_message_with_plain_object(self):
        """Test encoding message with plain object (else branch)."""
        # Create a plain object without model_dump() or dict()
        class PlainMessage:
            def __init__(self):
                self.from_agent = "agent_1"
                self.to_agent = "agent_2"
                self.content = "Hello"
                self.message_type = "text"

        message = PlainMessage()
        encoded = await encode_agent_message(message)

        assert isinstance(encoded, bytes)
        assert b"agent_1" in encoded

    @pytest.mark.asyncio
    async def test_decode_agent_message_with_migration(self):
        """Test decoding agent message with migration path."""
        codec = create_codec_serializer()
        
        # Register schema version 1.1 first
        codec.schema_registry.register_schema(
            "agent_message",
            "1.1",
            {
                "type": "object",
                "required": ["message_id", "source_agent_id", "target_agent_id", "content"],
                "properties": {
                    "message_id": {"type": "string"},
                    "source_agent_id": {"type": "string"},
                    "target_agent_id": {"type": "string"},
                    "content": {"type": "string"},
                    "new_field": {"type": "string"},
                },
            },
        )
        
        # Register a migration
        def migrate_1_0_to_1_1(envelope):
            data = envelope["data"]
            data["new_field"] = "default_value"
            envelope["schema_version"] = "1.1"
            return envelope

        codec.migration_manager.register_migration(
            "agent_message", "1.0", "1.1", migrate_1_0_to_1_1
        )

        # Create message with version 1.0
        message = AgentMessage(from_agent="a1", to_agent="a2", content="Hello")
        encoded = await encode_agent_message(message, codec=codec, schema_version="1.0")

        # Decode with target version 1.1 (triggers migration)
        decoded = await decode_agent_message(encoded, codec=codec, target_version="1.1")

        assert decoded["content"] == "Hello"

    @pytest.mark.asyncio
    async def test_decode_llm_response_with_migration(self):
        """Test decoding LLM response with migration path."""
        codec = create_codec_serializer()
        
        # Register schema version 1.1 first
        codec.schema_registry.register_schema(
            "llm_response",
            "1.1",
            {
                "type": "object",
                "required": ["request_id", "response", "model"],
                "properties": {
                    "request_id": {"type": "string"},
                    "response": {"type": "string"},
                    "model": {"type": "string"},
                    "enhanced": {"type": "boolean"},
                },
            },
        )
        
        # Register a migration
        def migrate_1_0_to_1_1(envelope):
            data = envelope["data"]
            data["enhanced"] = True
            envelope["schema_version"] = "1.1"
            return envelope

        codec.migration_manager.register_migration(
            "llm_response", "1.0", "1.1", migrate_1_0_to_1_1
        )

        # Create response with version 1.0
        response_envelope = codec.create_envelope(
            "llm_response",
            "1.0",
            {
                "request_id": "req_123",
                "response": "Generated text",
                "model": "gpt-4",
            },
        )
        encoded = await codec.encode(response_envelope)

        # Decode with target version 1.1 (triggers migration)
        decoded = await decode_llm_response(encoded, codec=codec, target_version="1.1")

        assert decoded["request_id"] == "req_123"

    @pytest.mark.asyncio
    async def test_decode_rag_query_with_migration(self):
        """Test decoding RAG query with migration path."""
        codec = create_codec_serializer()
        
        # Register schema version 1.1 first
        codec.schema_registry.register_schema(
            "rag_query",
            "1.1",
            {
                "type": "object",
                "required": ["query_id", "query", "tenant_id"],
                "properties": {
                    "query_id": {"type": "string"},
                    "query": {"type": "string"},
                    "tenant_id": {"type": "string"},
                    "enhanced": {"type": "boolean"},
                },
            },
        )
        
        # Register a migration
        def migrate_1_0_to_1_1(envelope):
            data = envelope["data"]
            data["enhanced"] = True
            envelope["schema_version"] = "1.1"
            return envelope

        codec.migration_manager.register_migration(
            "rag_query", "1.0", "1.1", migrate_1_0_to_1_1
        )

        # Create query with version 1.0
        query_envelope = codec.create_envelope(
            "rag_query",
            "1.0",
            {
                "query_id": "query_123",
                "query": "Test query",
                "tenant_id": "tenant_123",
            },
        )
        encoded = await codec.encode(query_envelope)

        # Decode with target version 1.1 (triggers migration)
        decoded = await decode_rag_query(encoded, codec=codec, target_version="1.1")

        assert decoded["query_id"] == "query_123"


class TestCodecMigrationManager:
    """Tests for migration manager functionality and error handling."""

    def test_migrate_envelope_missing_schema_name(self):
        """Test migrate_envelope when schema_name is None and not in envelope."""
        manager = MigrationManager()
        envelope = {"schema_version": "1.0", "data": {}}

        with pytest.raises(MigrationError, match="Cannot determine schema name"):
            manager.migrate_envelope(envelope, "1.1")

    def test_migrate_envelope_missing_schema_version(self):
        """Test migrate_envelope when schema_version is missing."""
        manager = MigrationManager()
        envelope = {"message_type": "agent_message", "data": {}}

        with pytest.raises(MigrationError, match="Missing 'schema_version'"):
            manager.migrate_envelope(envelope, "1.1", "agent_message")

    def test_migrate_envelope_no_migration_path(self):
        """Test migrate_envelope when no migration path exists."""
        manager = MigrationManager()
        envelope = {
            "schema_version": "1.0",
            "message_type": "agent_message",
            "data": {},
        }

        # Register a migration for 1.0->1.1 but try to migrate to 1.2
        def migrate_func(envelope):
            return envelope

        manager.register_migration("agent_message", "1.0", "1.1", migrate_func)

        with pytest.raises(MigrationError, match="No migration path"):
            manager.migrate_envelope(envelope, "1.2", "agent_message")

    def test_migrate_envelope_migration_exception(self):
        """Test migrate_envelope when migration function raises exception."""
        manager = MigrationManager()

        def failing_migration(envelope):
            raise ValueError("Migration failed")

        manager.register_migration("agent_message", "1.0", "1.1", failing_migration)
        envelope = {
            "schema_version": "1.0",
            "message_type": "agent_message",
            "data": {},
        }

        with pytest.raises(MigrationError, match="Migration failed"):
            manager.migrate_envelope(envelope, "1.1", "agent_message")

    def test_has_migration(self):
        """Test has_migration method."""
        manager = MigrationManager()

        def migrate_func(envelope):
            return envelope

        manager.register_migration("agent_message", "1.0", "1.1", migrate_func)

        assert manager.has_migration("agent_message", "1.0", "1.1") is True
        assert manager.has_migration("agent_message", "1.0", "1.2") is False
        assert manager.has_migration("unknown_schema", "1.0", "1.1") is False


class TestCodecSchemaRegistry:
    """Tests for schema registry functionality and error handling."""

    def test_get_schema_no_default_version(self):
        """Test get_schema when no default version exists."""
        registry = SchemaRegistry()
        
        # Register a schema with is_default=False, but first register another version
        # to ensure 1.0 is not automatically set as default
        registry.register_schema(
            "test_schema",
            "2.0",
            {"type": "object", "required": [], "properties": {}},
            is_default=True,  # Set 2.0 as default
        )
        
        # Register 1.0 without setting as default
        registry.register_schema(
            "test_schema",
            "1.0",
            {"type": "object", "required": [], "properties": {}},
            is_default=False,
        )
        
        # Remove default for test_schema to test the error path
        registry._default_versions.pop("test_schema", None)
        
        # Try to get it without version (should fail because no default)
        with pytest.raises(SchemaVersionError, match="No default version"):
            registry.get_schema("test_schema")

    def test_get_schema_version_not_found(self):
        """Test get_schema when version not found."""
        # Use a codec serializer which has default schemas initialized
        codec = create_codec_serializer()
        registry = codec.schema_registry
        
        with pytest.raises(SchemaVersionError, match="Version '2.0' not found"):
            registry.get_schema("agent_message", "2.0")

    def test_get_default_version(self):
        """Test get_default_version method."""
        # Use a codec serializer which has default schemas initialized
        codec = create_codec_serializer()
        registry = codec.schema_registry
        
        version = registry.get_default_version("agent_message")
        assert version == "1.0"
        
        version = registry.get_default_version("unknown_schema")
        assert version is None

    def test_get_versions(self):
        """Test get_versions method."""
        # Use a codec serializer which has default schemas initialized
        codec = create_codec_serializer()
        registry = codec.schema_registry
        
        versions = registry.get_versions("agent_message")
        assert "1.0" in versions
        
        versions = registry.get_versions("unknown_schema")
        assert versions == []

    def test_validate_envelope_missing_message_type(self):
        """Test validate_envelope when message_type is missing."""
        codec = create_codec_serializer()
        registry = codec.schema_registry
        envelope = {"schema_version": "1.0", "data": {}}

        with pytest.raises(SchemaValidationError, match="Cannot determine schema name"):
            registry.validate_envelope(envelope)

    def test_validate_envelope_missing_schema_version(self):
        """Test validate_envelope when schema_version is missing."""
        codec = create_codec_serializer()
        registry = codec.schema_registry
        envelope = {"message_type": "agent_message", "data": {}}

        with pytest.raises(SchemaValidationError, match="Missing 'schema_version'"):
            registry.validate_envelope(envelope)

    def test_validate_envelope_data_not_dict(self):
        """Test validate_envelope when data is not a dictionary."""
        codec = create_codec_serializer()
        registry = codec.schema_registry
        envelope = {
            "schema_version": "1.0",
            "message_type": "agent_message",
            "data": "not a dict",
        }

        with pytest.raises(SchemaValidationError) as exc_info:
            registry.validate_envelope(envelope)
        # Check that the error message contains the validation error
        assert "'data' field must be a dictionary" in str(exc_info.value.validation_errors)

    def test_has_schema(self):
        """Test has_schema method."""
        # Use a codec serializer which has default schemas initialized
        codec = create_codec_serializer()
        registry = codec.schema_registry
        
        assert registry.has_schema("agent_message") is True
        assert registry.has_schema("agent_message", "1.0") is True
        assert registry.has_schema("agent_message", "2.0") is False
        assert registry.has_schema("unknown_schema") is False
        assert registry.has_schema("unknown_schema", "1.0") is False


class TestFaaSCodecEdgeCases:
    """Tests for FaaS codec manager edge cases and fallback paths."""

    @pytest.mark.asyncio
    async def test_create_envelope(self):
        """Test create_envelope method."""
        from src.faas.integrations.codec import CodecManager

        manager = CodecManager(codec_type="json")
        envelope = manager.create_envelope("test_message", "1.0", {"key": "value"})

        assert envelope["schema_version"] == "1.0"
        assert envelope["message_type"] == "test_message"
        assert envelope["data"] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_create_envelope_fallback(self):
        """Test create_envelope fallback when core codec not available."""
        from src.faas.integrations.codec import CodecManager

        # Mock to simulate core codec not available
        manager = CodecManager(codec_type="json")
        manager._codec = None  # Force fallback

        envelope = manager.create_envelope("test_message", "1.0", {"key": "value"})

        assert envelope["schema_version"] == "1.0"
        assert envelope["message_type"] == "test_message"
        assert envelope["data"] == {"key": "value"}

    def test_validate_schema(self):
        """Test validate_schema method."""
        from src.faas.integrations.codec import CodecManager

        manager = CodecManager(codec_type="json")
        envelope = {
            "schema_version": "1.0",
            "message_type": "agent_message",
            "data": {"message_id": "msg_1", "source_agent_id": "a1", "target_agent_id": "a2", "content": "Hello"},
        }

        result = manager.validate_schema(envelope, "agent_message")
        assert result is True

    def test_validate_schema_fallback(self):
        """Test validate_schema fallback when core codec not available."""
        from src.faas.integrations.codec import CodecManager

        manager = CodecManager(codec_type="json")
        manager._codec = None  # Force fallback

        envelope = {
            "schema_version": "1.0",
            "message_type": "test_message",
            "data": {"key": "value"},
        }

        result = manager.validate_schema(envelope)
        assert result is True

    def test_validate_schema_fallback_errors(self):
        """Test validate_schema fallback error cases."""
        from src.faas.integrations.codec import CodecManager
        from typing import cast, Any

        manager = CodecManager(codec_type="json")
        manager._codec = None  # Force fallback

        # Test not a dictionary - use cast to bypass type checker for test
        with pytest.raises(ValueError, match="Envelope must be a dictionary"):
            manager.validate_schema(cast(Any, "not a dict"))

        # Test missing schema_version
        with pytest.raises(ValueError, match="Envelope missing 'schema_version'"):
            manager.validate_schema({"message_type": "test", "data": {}})

        # Test missing message_type
        with pytest.raises(ValueError, match="Envelope missing 'message_type'"):
            manager.validate_schema({"schema_version": "1.0", "data": {}})

        # Test missing data
        with pytest.raises(ValueError, match="Envelope missing 'data'"):
            manager.validate_schema({"schema_version": "1.0", "message_type": "test"})

    @pytest.mark.asyncio
    async def test_encode_with_existing_envelope(self):
        """Test encode when data is already an envelope."""
        from src.faas.integrations.codec import CodecManager

        manager = CodecManager(codec_type="json")
        envelope = {
            "schema_version": "1.0",
            "message_type": "test_message",
            "data": {"key": "value"},
        }

        encoded = await manager.encode(envelope)
        decoded = await manager.decode(encoded)

        assert decoded["data"] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_encode_fallback_path(self):
        """Test encode fallback when core codec not available."""
        from src.faas.integrations.codec import CodecManager

        manager = CodecManager(codec_type="json")
        manager._codec = None  # Force fallback

        data = {"key": "value"}
        encoded = await manager.encode(data)
        decoded = await manager.decode(encoded)

        assert decoded["data"] == data

    @pytest.mark.asyncio
    async def test_decode_fallback_path(self):
        """Test decode fallback when core codec not available."""
        from src.faas.integrations.codec import CodecManager
        import json

        manager = CodecManager(codec_type="json")
        manager._codec = None  # Force fallback

        envelope = {
            "schema_version": "1.0",
            "message_type": "test_message",
            "data": {"key": "value"},
        }
        encoded = json.dumps(envelope).encode("utf-8")

        decoded = await manager.decode(encoded)
        assert decoded["data"] == {"key": "value"}

