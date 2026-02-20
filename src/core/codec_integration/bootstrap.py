"""
Schema and Migration Bootstrap

Centralized registration point for all schemas and migrations.
This ensures consistent schema registration at startup and prevents regressions.
"""

import logging
from typing import Optional

from .migration_manager import MigrationManager
from .schema_registry import SchemaRegistry

logger = logging.getLogger(__name__)


def register_all_schemas(registry: Optional[SchemaRegistry] = None) -> None:
    """
    Register all default schemas in the registry.
    
    This function registers all standard schemas used by the SDK:
    - agent_message
    - llm_request, llm_response
    - rag_document, rag_query, rag_result
    - agent_requirements, tool_requirements
    - prompt_template
    
    Args:
        registry: Schema registry instance (uses default if not provided)
        
    Example:
        >>> from src.core.codec_integration.bootstrap import register_all_schemas
        >>> from src.core.codec_integration.schema_registry import get_default_registry
        >>> register_all_schemas(get_default_registry())
    """
    from .schema_registry import get_default_registry
    
    if registry is None:
        registry = get_default_registry()
    
    logger.info("Registering all default schemas")
    
    # Agent Message Schema
    registry.register_schema(
        schema_name="agent_message",
        version="1.0",
        schema_definition={
            "type": "object",
            "required": ["message_id", "source_agent_id", "target_agent_id", "content"],
            "properties": {
                "message_id": {"type": "string"},
                "source_agent_id": {"type": "string"},
                "target_agent_id": {"type": "string"},
                "content": {"type": "string"},
                "message_type": {"type": "string"},
                "timestamp": {"type": "string"},
                "metadata": {"type": "object"},
            },
        },
        is_default=True,
    )

    # LLM Request Schema
    registry.register_schema(
        schema_name="llm_request",
        version="1.0",
        schema_definition={
            "type": "object",
            "required": ["request_id", "prompt", "model", "tenant_id"],
            "properties": {
                "request_id": {"type": "string"},
                "prompt": {"type": "string"},
                "model": {"type": "string"},
                "tenant_id": {"type": "string"},
                "parameters": {"type": "object"},
                "timestamp": {"type": "string"},
            },
        },
        is_default=True,
    )

    # LLM Response Schema
    registry.register_schema(
        schema_name="llm_response",
        version="1.0",
        schema_definition={
            "type": "object",
            "required": ["request_id", "response", "model"],
            "properties": {
                "request_id": {"type": "string"},
                "response": {"type": "string"},
                "model": {"type": "string"},
                "tokens": {"type": "object"},
                "cost": {"type": "number"},
                "timestamp": {"type": "string"},
            },
        },
        is_default=True,
    )

    # RAG Document Schema
    registry.register_schema(
        schema_name="rag_document",
        version="1.0",
        schema_definition={
            "type": "object",
            "required": ["document_id", "content", "tenant_id"],
            "properties": {
                "document_id": {"type": "string"},
                "content": {"type": "string"},
                "metadata": {"type": "object"},
                "chunks": {"type": "array"},
                "tenant_id": {"type": "string"},
                "timestamp": {"type": "string"},
            },
        },
        is_default=True,
    )

    # RAG Query Schema
    registry.register_schema(
        schema_name="rag_query",
        version="1.0",
        schema_definition={
            "type": "object",
            "required": ["query_id", "query", "tenant_id"],
            "properties": {
                "query_id": {"type": "string"},
                "query": {"type": "string"},
                "tenant_id": {"type": "string"},
                "parameters": {"type": "object"},
                "timestamp": {"type": "string"},
            },
        },
        is_default=True,
    )

    # RAG Result Schema
    registry.register_schema(
        schema_name="rag_result",
        version="1.0",
        schema_definition={
            "type": "object",
            "required": ["query_id", "answer"],
            "properties": {
                "query_id": {"type": "string"},
                "answer": {"type": "string"},
                "sources": {"type": "array"},
                "metadata": {"type": "object"},
                "timestamp": {"type": "string"},
            },
        },
        is_default=True,
    )

    # Agent Requirements Schema
    registry.register_schema(
        schema_name="agent_requirements",
        version="1.0",
        schema_definition={
            "type": "object",
            "required": ["name", "description", "system_prompt"],
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "capabilities": {"type": "array", "items": {"type": "string"}},
                "system_prompt": {"type": "string"},
                "required_tools": {"type": "array", "items": {"type": "string"}},
                "memory_config": {"type": "object"},
                "max_context_tokens": {"type": "integer"},
                "enable_tool_calling": {"type": "boolean"},
                "metadata": {"type": "object"},
            },
        },
        is_default=True,
    )

    # Tool Requirements Schema
    registry.register_schema(
        schema_name="tool_requirements",
        version="1.0",
        schema_definition={
            "type": "object",
            "required": ["name", "description", "function_name"],
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "function_name": {"type": "string"},
                "parameters": {"type": "array"},
                "return_type": {"type": "string"},
                "code_template": {"type": ["string", "null"]},
                "metadata": {"type": "object"},
            },
        },
        is_default=True,
    )

    # Prompt Template Schema
    registry.register_schema(
        schema_name="prompt_template",
        version="1.0",
        schema_definition={
            "type": "object",
            "required": ["name", "version", "content"],
            "properties": {
                "name": {"type": "string"},
                "version": {"type": "string"},
                "content": {"type": "string"},
                "tenant_id": {"type": ["string", "null"]},
                "metadata": {"type": "object"},
            },
        },
        is_default=True,
    )
    
    logger.info("All default schemas registered successfully")


def register_all_migrations(migration_manager: Optional[MigrationManager] = None) -> None:
    """
    Register all default migrations in the migration manager.
    
    This function registers all standard migrations for schema version upgrades.
    Currently, no default migrations are defined, but this function provides
    a centralized point for future migration registration.
    
    Args:
        migration_manager: Migration manager instance (uses default if not provided)
        
    Example:
        >>> from src.core.codec_integration.bootstrap import register_all_migrations
        >>> from src.core.codec_integration.migration_manager import get_default_migration_manager
        >>> register_all_migrations(get_default_migration_manager())
        
    Note:
        To register a migration, use the following pattern:
        
        >>> def migrate_v1_to_v2(old_envelope: Dict[str, Any]) -> Dict[str, Any]:
        ...     # Migration logic here
        ...     return new_envelope
        ...
        >>> migration_manager.register_migration(
        ...     schema_name="agent_message",
        ...     from_version="1.0",
        ...     to_version="2.0",
        ...     migration_function=migrate_v1_to_v2
        ... )
    """
    from .migration_manager import get_default_migration_manager
    
    if migration_manager is None:
        migration_manager = get_default_migration_manager()
    
    logger.info("Registering all default migrations")
    
    # Currently no default migrations are defined
    # This function provides a centralized point for future migration registration
    # Example migration registration:
    #
    # def migrate_agent_message_v1_to_v2(old_envelope: Dict[str, Any]) -> Dict[str, Any]:
    #     """Migrate agent_message from v1.0 to v2.0."""
    #     old_data = old_envelope["data"]
    #     return {
    #         "schema_version": "2.0",
    #         "message_type": "agent_message",
    #         "data": {
    #             # Transform old_data to new format
    #             **old_data,
    #             "new_field": "default_value",
    #         }
    #     }
    #
    # migration_manager.register_migration(
    #     schema_name="agent_message",
    #     from_version="1.0",
    #     to_version="2.0",
    #     migration_function=migrate_agent_message_v1_to_v2
    # )
    
    logger.info("All default migrations registered successfully")


def bootstrap(
    registry: Optional[SchemaRegistry] = None,
    migration_manager: Optional[MigrationManager] = None,
) -> None:
    """
    Bootstrap all schemas and migrations.
    
    This is a convenience function that calls both register_all_schemas()
    and register_all_migrations() to ensure everything is initialized.
    
    Args:
        registry: Schema registry instance (uses default if not provided)
        migration_manager: Migration manager instance (uses default if not provided)
        
    Example:
        >>> from src.core.codec_integration.bootstrap import bootstrap
        >>> bootstrap()  # Uses default registry and migration manager
    """
    logger.info("Bootstrapping codec integration (schemas and migrations)")
    register_all_schemas(registry)
    register_all_migrations(migration_manager)
    logger.info("Codec integration bootstrap complete")

