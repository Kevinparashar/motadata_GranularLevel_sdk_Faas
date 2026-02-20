"""
Unit Tests for Codec Bootstrap

Tests schema and migration bootstrap functionality.
"""

from src.core.codec_integration.bootstrap import (
    bootstrap,
    register_all_migrations,
    register_all_schemas,
)
from src.core.codec_integration.migration_manager import (
    MigrationManager,
    get_default_migration_manager,
)
from src.core.codec_integration.schema_registry import (
    SchemaRegistry,
    get_default_registry,
)


class TestRegisterAllSchemas:
    """Tests for register_all_schemas function."""

    def test_register_all_schemas_with_default_registry(self):
        """Test register_all_schemas with default registry."""
        registry = get_default_registry()
        
        # Clear any existing schemas (if any)
        # Note: In practice, schemas may already be registered, so we check if they exist
        register_all_schemas(registry)
        
        # Verify all expected schemas are registered
        expected_schemas = [
            "agent_message",
            "llm_request",
            "llm_response",
            "rag_document",
            "rag_query",
            "rag_result",
            "agent_requirements",
            "tool_requirements",
            "prompt_template",
        ]
        
        for schema_name in expected_schemas:
            schema = registry.get_schema(schema_name, "1.0")
            assert schema is not None
            assert schema["type"] == "object"
            assert "required" in schema
            assert "properties" in schema

    def test_register_all_schemas_with_custom_registry(self):
        """Test register_all_schemas with custom registry."""
        registry = SchemaRegistry()
        
        register_all_schemas(registry)
        
        # Verify schemas are registered
        assert registry.has_schema("agent_message", "1.0")
        assert registry.has_schema("llm_request", "1.0")
        assert registry.has_schema("llm_response", "1.0")
        assert registry.has_schema("rag_document", "1.0")
        assert registry.has_schema("rag_query", "1.0")
        assert registry.has_schema("rag_result", "1.0")
        assert registry.has_schema("agent_requirements", "1.0")
        assert registry.has_schema("tool_requirements", "1.0")
        assert registry.has_schema("prompt_template", "1.0")

    def test_register_all_schemas_idempotent(self):
        """Test that register_all_schemas is idempotent (can be called multiple times)."""
        registry = SchemaRegistry()
        
        # Register twice
        register_all_schemas(registry)
        register_all_schemas(registry)
        
        # Should still have all schemas
        assert registry.has_schema("agent_message", "1.0")
        assert registry.has_schema("llm_request", "1.0")

    def test_register_all_schemas_agent_message_schema(self):
        """Test agent_message schema structure."""
        registry = SchemaRegistry()
        register_all_schemas(registry)
        
        schema = registry.get_schema("agent_message", "1.0")
        
        assert schema["type"] == "object"
        assert "message_id" in schema["required"]
        assert "source_agent_id" in schema["required"]
        assert "target_agent_id" in schema["required"]
        assert "content" in schema["required"]
        assert schema["properties"]["message_id"]["type"] == "string"
        assert schema["properties"]["content"]["type"] == "string"

    def test_register_all_schemas_llm_request_schema(self):
        """Test llm_request schema structure."""
        registry = SchemaRegistry()
        register_all_schemas(registry)
        
        schema = registry.get_schema("llm_request", "1.0")
        
        assert schema["type"] == "object"
        assert "request_id" in schema["required"]
        assert "prompt" in schema["required"]
        assert "model" in schema["required"]
        assert "tenant_id" in schema["required"]
        assert schema["properties"]["prompt"]["type"] == "string"

    def test_register_all_schemas_rag_document_schema(self):
        """Test rag_document schema structure."""
        registry = SchemaRegistry()
        register_all_schemas(registry)
        
        schema = registry.get_schema("rag_document", "1.0")
        
        assert schema["type"] == "object"
        assert "document_id" in schema["required"]
        assert "content" in schema["required"]
        assert "tenant_id" in schema["required"]
        assert schema["properties"]["chunks"]["type"] == "array"

    def test_register_all_schemas_default_versions(self):
        """Test that all schemas have default versions set."""
        registry = SchemaRegistry()
        register_all_schemas(registry)
        
        expected_schemas = [
            "agent_message",
            "llm_request",
            "llm_response",
            "rag_document",
            "rag_query",
            "rag_result",
            "agent_requirements",
            "tool_requirements",
            "prompt_template",
        ]
        
        for schema_name in expected_schemas:
            default_version = registry.get_default_version(schema_name)
            assert default_version == "1.0"


class TestRegisterAllMigrations:
    """Tests for register_all_migrations function."""

    def test_register_all_migrations_with_default_manager(self):
        """Test register_all_migrations with default migration manager."""
        manager = get_default_migration_manager()
        
        # Should not raise
        register_all_migrations(manager)
        
        # Currently no default migrations, so nothing to verify
        # But function should complete successfully

    def test_register_all_migrations_with_custom_manager(self):
        """Test register_all_migrations with custom migration manager."""
        manager = MigrationManager()
        
        register_all_migrations(manager)
        
        # Currently no default migrations, so manager should be empty
        # But function should complete successfully

    def test_register_all_migrations_idempotent(self):
        """Test that register_all_migrations is idempotent."""
        manager = MigrationManager()
        
        # Register twice
        register_all_migrations(manager)
        register_all_migrations(manager)
        
        # Should not raise and should complete successfully


class TestBootstrap:
    """Tests for bootstrap function."""

    def test_bootstrap_with_defaults(self):
        """Test bootstrap with default registry and migration manager."""
        # Should not raise
        bootstrap()
        
        # Verify schemas are registered in default registry
        registry = get_default_registry()
        assert registry.has_schema("agent_message", "1.0")
        assert registry.has_schema("llm_request", "1.0")

    def test_bootstrap_with_custom_registry(self):
        """Test bootstrap with custom registry."""
        registry = SchemaRegistry()
        migration_manager = MigrationManager()
        
        bootstrap(registry=registry, migration_manager=migration_manager)
        
        # Verify schemas are registered
        assert registry.has_schema("agent_message", "1.0")
        assert registry.has_schema("llm_request", "1.0")

    def test_bootstrap_with_custom_migration_manager(self):
        """Test bootstrap with custom migration manager."""
        registry = SchemaRegistry()
        migration_manager = MigrationManager()
        
        bootstrap(registry=registry, migration_manager=migration_manager)
        
        # Should complete successfully
        assert registry.has_schema("agent_message", "1.0")

    def test_bootstrap_idempotent(self):
        """Test that bootstrap is idempotent."""
        registry = SchemaRegistry()
        migration_manager = MigrationManager()
        
        # Bootstrap twice
        bootstrap(registry=registry, migration_manager=migration_manager)
        bootstrap(registry=registry, migration_manager=migration_manager)
        
        # Should still have all schemas
        assert registry.has_schema("agent_message", "1.0")
        assert registry.has_schema("llm_request", "1.0")

    def test_bootstrap_registers_all_schemas(self):
        """Test that bootstrap registers all expected schemas."""
        registry = SchemaRegistry()
        migration_manager = MigrationManager()
        
        bootstrap(registry=registry, migration_manager=migration_manager)
        
        expected_schemas = [
            "agent_message",
            "llm_request",
            "llm_response",
            "rag_document",
            "rag_query",
            "rag_result",
            "agent_requirements",
            "tool_requirements",
            "prompt_template",
        ]
        
        for schema_name in expected_schemas:
            assert registry.has_schema(schema_name, "1.0"), f"Schema {schema_name} not registered"


class TestBootstrapIntegration:
    """Integration tests for bootstrap with CodecSerializer."""

    def test_codec_serializer_uses_bootstrap(self):
        """Test that CodecSerializer uses bootstrap for schema registration."""
        from src.core.codec_integration import CodecSerializer
        
        # Create serializer (should call bootstrap internally)
        codec = CodecSerializer()
        
        # Verify schemas are registered
        assert codec.schema_registry.has_schema("agent_message", "1.0")
        assert codec.schema_registry.has_schema("llm_request", "1.0")
        assert codec.schema_registry.has_schema("rag_document", "1.0")

    def test_bootstrap_before_codec_serializer(self):
        """Test that bootstrap can be called before creating CodecSerializer."""
        from src.core.codec_integration import CodecSerializer
        
        # Bootstrap first
        bootstrap()
        
        # Create serializer (should not duplicate schemas)
        codec = CodecSerializer()
        
        # Verify schemas are still registered
        assert codec.schema_registry.has_schema("agent_message", "1.0")

    def test_custom_registry_with_bootstrap(self):
        """Test using custom registry with bootstrap and CodecSerializer."""
        from src.core.codec_integration import CodecSerializer
        
        registry = SchemaRegistry()
        migration_manager = MigrationManager()
        
        # Bootstrap with custom registry
        bootstrap(registry=registry, migration_manager=migration_manager)
        
        # Create serializer with same registry
        codec = CodecSerializer(schema_registry=registry, migration_manager=migration_manager)
        
        # Verify schemas are registered
        assert codec.schema_registry.has_schema("agent_message", "1.0")
        # Verify it's the same registry instance
        assert codec.schema_registry is registry

