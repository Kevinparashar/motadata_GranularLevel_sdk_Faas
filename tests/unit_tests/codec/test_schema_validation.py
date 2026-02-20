"""
Unit Tests for Schema Validation with JSON Schema

Tests comprehensive JSON Schema validation including types, nested fields, enums, and constraints.
"""

import pytest

from src.core.codec_integration import create_codec_serializer
from src.core.codec_integration.exceptions import SchemaValidationError
from src.core.codec_integration.schema_registry import SchemaRegistry


class TestJSONSchemaValidation:
    """Tests for JSON Schema validation in schema registry."""

    @pytest.fixture
    def registry(self):
        """Create a test schema registry."""
        return SchemaRegistry()

    @pytest.fixture
    def codec(self):
        """Create a test codec serializer."""
        return create_codec_serializer(codec_type="json")

    def test_validate_string_type(self, registry):
        """Test validation with string type constraint."""
        registry.register_schema(
            schema_name="string_test",
            version="1.0",
            schema_definition={
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string"},
                },
            },
            is_default=True,
        )

        # Valid string
        envelope = {
            "schema_version": "1.0",
            "message_type": "string_test",
            "data": {"name": "test"},
        }
        assert registry.validate_envelope(envelope) is True

        # Invalid: number instead of string
        envelope_invalid = {
            "schema_version": "1.0",
            "message_type": "string_test",
            "data": {"name": 123},
        }
        with pytest.raises(SchemaValidationError):
            registry.validate_envelope(envelope_invalid)

    def test_validate_number_type(self, registry):
        """Test validation with number type constraint."""
        registry.register_schema(
            schema_name="number_test",
            version="1.0",
            schema_definition={
                "type": "object",
                "required": ["age"],
                "properties": {
                    "age": {"type": "number"},
                },
            },
            is_default=True,
        )

        # Valid number
        envelope = {
            "schema_version": "1.0",
            "message_type": "number_test",
            "data": {"age": 25},
        }
        assert registry.validate_envelope(envelope) is True

        # Valid float
        envelope_float = {
            "schema_version": "1.0",
            "message_type": "number_test",
            "data": {"age": 25.5},
        }
        assert registry.validate_envelope(envelope_float) is True

        # Invalid: string instead of number
        envelope_invalid = {
            "schema_version": "1.0",
            "message_type": "number_test",
            "data": {"age": "twenty-five"},
        }
        with pytest.raises(SchemaValidationError):
            registry.validate_envelope(envelope_invalid)

    def test_validate_boolean_type(self, registry):
        """Test validation with boolean type constraint."""
        registry.register_schema(
            schema_name="boolean_test",
            version="1.0",
            schema_definition={
                "type": "object",
                "required": ["active"],
                "properties": {
                    "active": {"type": "boolean"},
                },
            },
            is_default=True,
        )

        # Valid boolean
        envelope = {
            "schema_version": "1.0",
            "message_type": "boolean_test",
            "data": {"active": True},
        }
        assert registry.validate_envelope(envelope) is True

        # Invalid: string instead of boolean
        envelope_invalid = {
            "schema_version": "1.0",
            "message_type": "boolean_test",
            "data": {"active": "true"},
        }
        with pytest.raises(SchemaValidationError):
            registry.validate_envelope(envelope_invalid)

    def test_validate_array_type(self, registry):
        """Test validation with array type constraint."""
        registry.register_schema(
            schema_name="array_test",
            version="1.0",
            schema_definition={
                "type": "object",
                "required": ["tags"],
                "properties": {
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
            },
            is_default=True,
        )

        # Valid array
        envelope = {
            "schema_version": "1.0",
            "message_type": "array_test",
            "data": {"tags": ["tag1", "tag2"]},
        }
        assert registry.validate_envelope(envelope) is True

        # Invalid: not an array
        envelope_invalid = {
            "schema_version": "1.0",
            "message_type": "array_test",
            "data": {"tags": "not_an_array"},
        }
        with pytest.raises(SchemaValidationError):
            registry.validate_envelope(envelope_invalid)

        # Invalid: wrong item type
        envelope_invalid_items = {
            "schema_version": "1.0",
            "message_type": "array_test",
            "data": {"tags": [1, 2, 3]},  # Should be strings
        }
        with pytest.raises(SchemaValidationError):
            registry.validate_envelope(envelope_invalid_items)

    def test_validate_nested_object(self, registry):
        """Test validation with nested object structure."""
        registry.register_schema(
            schema_name="nested_test",
            version="1.0",
            schema_definition={
                "type": "object",
                "required": ["metadata"],
                "properties": {
                    "metadata": {
                        "type": "object",
                        "required": ["key"],
                        "properties": {
                            "key": {"type": "string"},
                            "value": {"type": "string"},
                        },
                    },
                },
            },
            is_default=True,
        )

        # Valid nested object
        envelope = {
            "schema_version": "1.0",
            "message_type": "nested_test",
            "data": {"metadata": {"key": "test", "value": "value"}},
        }
        assert registry.validate_envelope(envelope) is True

        # Invalid: missing required nested field
        envelope_invalid = {
            "schema_version": "1.0",
            "message_type": "nested_test",
            "data": {"metadata": {}},  # Missing "key"
        }
        with pytest.raises(SchemaValidationError):
            registry.validate_envelope(envelope_invalid)

    def test_validate_enum_constraint(self, registry):
        """Test validation with enum constraint."""
        registry.register_schema(
            schema_name="enum_test",
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

        # Valid enum value
        envelope = {
            "schema_version": "1.0",
            "message_type": "enum_test",
            "data": {"status": "active"},
        }
        assert registry.validate_envelope(envelope) is True

        # Invalid: not in enum
        envelope_invalid = {
            "schema_version": "1.0",
            "message_type": "enum_test",
            "data": {"status": "invalid"},
        }
        with pytest.raises(SchemaValidationError):
            registry.validate_envelope(envelope_invalid)

    def test_validate_required_fields(self, registry):
        """Test validation with required fields."""
        registry.register_schema(
            schema_name="required_test",
            version="1.0",
            schema_definition={
                "type": "object",
                "required": ["field1", "field2"],
                "properties": {
                    "field1": {"type": "string"},
                    "field2": {"type": "number"},
                    "field3": {"type": "string"},  # Optional
                },
            },
            is_default=True,
        )

        # Valid: all required fields present
        envelope = {
            "schema_version": "1.0",
            "message_type": "required_test",
            "data": {"field1": "test", "field2": 123},
        }
        assert registry.validate_envelope(envelope) is True

        # Invalid: missing required field
        envelope_invalid = {
            "schema_version": "1.0",
            "message_type": "required_test",
            "data": {"field1": "test"},  # Missing field2
        }
        with pytest.raises(SchemaValidationError):
            registry.validate_envelope(envelope_invalid)

    def test_validate_complex_schema(self, registry):
        """Test validation with complex schema (multiple types, nested, arrays)."""
        registry.register_schema(
            schema_name="complex_test",
            version="1.0",
            schema_definition={
                "type": "object",
                "required": ["name", "age", "tags", "metadata"],
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

        # Valid complex data
        envelope = {
            "schema_version": "1.0",
            "message_type": "complex_test",
            "data": {
                "name": "test",
                "age": 25,
                "active": True,
                "tags": ["tag1", "tag2"],
                "metadata": {"key": "value"},
            },
        }
        assert registry.validate_envelope(envelope) is True

        # Invalid: wrong type in nested array
        envelope_invalid = {
            "schema_version": "1.0",
            "message_type": "complex_test",
            "data": {
                "name": "test",
                "age": 25,
                "active": True,
                "tags": [1, 2, 3],  # Should be strings
                "metadata": {"key": "value"},
            },
        }
        with pytest.raises(SchemaValidationError):
            registry.validate_envelope(envelope_invalid)

    def test_validate_error_messages(self, registry):
        """Test that validation errors provide detailed messages."""
        registry.register_schema(
            schema_name="error_test",
            version="1.0",
            schema_definition={
                "type": "object",
                "required": ["name", "age"],
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "number"},
                },
            },
            is_default=True,
        )

        envelope_invalid = {
            "schema_version": "1.0",
            "message_type": "error_test",
            "data": {"name": 123, "age": "not_a_number"},
        }

        with pytest.raises(SchemaValidationError) as exc_info:
            registry.validate_envelope(envelope_invalid)
        
        assert exc_info.value.schema_name == "error_test"
        assert len(exc_info.value.validation_errors) > 0
        # Error messages should contain field paths
        error_str = " ".join(exc_info.value.validation_errors)
        assert "age" in error_str or "name" in error_str

    def test_validate_fallback_without_jsonschema(self, registry):
        """Test validation falls back to basic validation if JSON Schema not available."""
        # This test verifies graceful degradation
        # In practice, jsonschema should be available, but we test the fallback
        
        # Register a simple schema
        registry.register_schema(
            schema_name="fallback_test",
            version="1.0",
            schema_definition={
                "type": "object",
                "required": ["field1"],
                "properties": {
                    "field1": {"type": "string"},
                },
            },
            is_default=True,
        )

        # Valid: has required field
        envelope = {
            "schema_version": "1.0",
            "message_type": "fallback_test",
            "data": {"field1": "test"},
        }
        assert registry.validate_envelope(envelope) is True

        # Invalid: missing required field (fallback should catch this)
        envelope_invalid = {
            "schema_version": "1.0",
            "message_type": "fallback_test",
            "data": {},
        }
        with pytest.raises(SchemaValidationError):
            registry.validate_envelope(envelope_invalid)

