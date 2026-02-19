"""
Unit Tests for PromptContextManager Codec Integration

Tests codec encoding/decoding for PromptTemplate.
"""

import pytest

from src.core.codec_integration import create_codec_serializer
from src.core.prompt_context_management.prompt_manager import (
    PromptContextManager,
    PromptTemplate,
)


class TestPromptContextManagerCodecIntegration:
    """Tests for PromptContextManager codec integration."""

    @pytest.fixture
    def manager(self):
        """Create a test prompt context manager."""
        return PromptContextManager()

    @pytest.fixture
    def codec(self):
        """Create a test codec serializer."""
        return create_codec_serializer()

    @pytest.fixture
    def template(self):
        """Create test prompt template."""
        return PromptTemplate(
            name="test_template",
            version="1.0",
            content="Hello {name}!",
            tenant_id="tenant_123",
            metadata={"author": "test", "category": "greeting"},
        )

    def test_manager_with_codec_serializer(self, codec):
        """Test prompt context manager initialization with codec serializer."""
        manager = PromptContextManager(codec_serializer=codec)

        assert manager.codec_serializer is not None
        assert manager.codec_serializer == codec

    def test_manager_without_codec(self):
        """Test prompt context manager works without codec configured."""
        manager = PromptContextManager()

        # Codec should be auto-initialized if available
        # But it may be None if codec SDK is not installed
        assert manager is not None

    @pytest.mark.asyncio
    async def test_encode_template_with_codec(self, manager, codec, template):
        """Test encoding template with codec serializer."""
        manager.codec_serializer = codec

        encoded = await manager.encode_template(template)

        assert isinstance(encoded, bytes)
        assert b"test_template" in encoded
        assert b"Hello {name}!" in encoded

    @pytest.mark.asyncio
    async def test_encode_template_without_codec(self, manager, template):
        """Test encoding template without codec serializer (should use default)."""
        # Should work with default codec from import
        encoded = await manager.encode_template(template)

        assert isinstance(encoded, bytes)

    @pytest.mark.asyncio
    async def test_decode_template_with_codec(self, manager, codec, template):
        """Test decoding template with codec serializer."""
        manager.codec_serializer = codec

        encoded = await manager.encode_template(template)
        decoded = await manager.decode_template(encoded)

        assert isinstance(decoded, PromptTemplate)
        assert decoded.name == template.name
        assert decoded.version == template.version
        assert decoded.content == template.content
        assert decoded.tenant_id == template.tenant_id
        assert decoded.metadata == template.metadata

    @pytest.mark.asyncio
    async def test_decode_template_without_codec(self, manager, template):
        """Test decoding template without codec serializer (should use default)."""
        encoded = await manager.encode_template(template)

        # Should work with default codec from import
        decoded = await manager.decode_template(encoded)

        assert isinstance(decoded, PromptTemplate)
        assert decoded.name == template.name
        assert decoded.content == template.content

    @pytest.mark.asyncio
    async def test_encode_decode_template_roundtrip(self, manager, codec, template):
        """Test encode/decode roundtrip for template."""
        manager.codec_serializer = codec

        encoded = await manager.encode_template(template)
        decoded = await manager.decode_template(encoded)

        assert decoded.name == template.name
        assert decoded.version == template.version
        assert decoded.content == template.content
        assert decoded.tenant_id == template.tenant_id
        assert decoded.metadata == template.metadata

    @pytest.mark.asyncio
    async def test_encode_template_custom_version(self, manager, codec, template):
        """Test encoding template with custom schema version."""
        manager.codec_serializer = codec

        encoded = await manager.encode_template(template, schema_version="1.0")

        assert isinstance(encoded, bytes)

    @pytest.mark.asyncio
    async def test_encode_template_without_tenant_id(self, manager, codec):
        """Test encoding template without tenant_id."""
        manager.codec_serializer = codec
        template = PromptTemplate(
            name="test",
            version="1.0",
            content="Hello",
            tenant_id=None,
        )

        encoded = await manager.encode_template(template)
        decoded = await manager.decode_template(encoded)

        assert decoded.tenant_id is None

    @pytest.mark.asyncio
    async def test_encode_template_with_empty_metadata(self, manager, codec):
        """Test encoding template with empty metadata."""
        manager.codec_serializer = codec
        template = PromptTemplate(
            name="test",
            version="1.0",
            content="Hello",
            metadata={},
        )

        encoded = await manager.encode_template(template)
        decoded = await manager.decode_template(encoded)

        assert decoded.metadata == {}

    @pytest.mark.asyncio
    async def test_encode_template_with_complex_content(self, manager, codec):
        """Test encoding template with complex content."""
        manager.codec_serializer = codec
        template = PromptTemplate(
            name="complex_template",
            version="2.0",
            content="Hello {name}! Your age is {age}. Status: {status}",
            tenant_id="tenant_456",
            metadata={"complex": {"nested": {"data": "value"}}},
        )

        encoded = await manager.encode_template(template)
        decoded = await manager.decode_template(encoded)

        assert decoded.content == template.content
        assert decoded.metadata == template.metadata

    @pytest.mark.asyncio
    async def test_decode_template_with_target_version(self, manager, codec, template):
        """Test decoding template with target version."""
        manager.codec_serializer = codec

        encoded = await manager.encode_template(template, schema_version="1.0")
        decoded = await manager.decode_template(encoded, target_version="1.0")

        assert isinstance(decoded, PromptTemplate)
        assert decoded.name == template.name

    @pytest.mark.asyncio
    async def test_encode_prompt_template_without_codec_param(self, template):
        """Test encoding prompt template without codec parameter (creates default)."""
        from src.core.codec_integration import encode_prompt_template

        encoded = await encode_prompt_template(template, codec=None)

        assert isinstance(encoded, bytes)

    @pytest.mark.asyncio
    async def test_decode_prompt_template_without_codec_param(self, template):
        """Test decoding prompt template without codec parameter (creates default)."""
        from src.core.codec_integration import encode_prompt_template, decode_prompt_template

        encoded = await encode_prompt_template(template, codec=None)
        decoded = await decode_prompt_template(encoded, codec=None)

        assert isinstance(decoded, dict)
        assert decoded["name"] == template.name

    @pytest.mark.asyncio
    async def test_decode_prompt_template_with_migration_needed(self, template):
        """Test decoding prompt template when migration is needed."""
        from src.core.codec_integration import encode_prompt_template, decode_prompt_template

        encoded = await encode_prompt_template(template, schema_version="1.0")
        # Request same version - no migration needed, but tests the path
        decoded = await decode_prompt_template(encoded, codec=None, target_version="1.0")

        assert isinstance(decoded, dict)
        assert decoded["name"] == template.name

    @pytest.mark.asyncio
    async def test_encode_template_with_codec_serializer(self, manager, codec, template):
        """Test encoding template with codec_serializer set."""
        manager.codec_serializer = codec

        encoded = await manager.encode_template(template)

        assert isinstance(encoded, bytes)

    @pytest.mark.asyncio
    async def test_decode_template_with_codec_serializer(self, manager, codec, template):
        """Test decoding template with codec_serializer set."""
        manager.codec_serializer = codec

        encoded = await manager.encode_template(template)
        decoded = await manager.decode_template(encoded)

        assert isinstance(decoded, PromptTemplate)
        assert decoded.name == template.name


