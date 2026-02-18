"""
Schema Registry for CODEC Integration

Manages schema definitions, versions, and validation for message encoding/decoding.
"""

import logging
from typing import Any, Dict, List, Optional

from .exceptions import SchemaValidationError, SchemaVersionError

logger = logging.getLogger(__name__)


class SchemaRegistry:
    """
    Registry for managing message schemas and versions.
    
    Provides schema registration, validation, and version management.
    """

    def __init__(self) -> None:
        """Initialize schema registry."""
        self._schemas: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._default_versions: Dict[str, str] = {}

    def register_schema(
        self,
        schema_name: str,
        version: str,
        schema_definition: Dict[str, Any],
        is_default: bool = False,
    ) -> None:
        """
        Register a schema definition.
        
        Args:
            schema_name: Name of the schema (e.g., "agent_message")
            version: Schema version (e.g., "1.0")
            schema_definition: Schema definition dictionary
            is_default: Whether this is the default version for this schema
        """
        if schema_name not in self._schemas:
            self._schemas[schema_name] = {}

        self._schemas[schema_name][version] = schema_definition

        if is_default or schema_name not in self._default_versions:
            self._default_versions[schema_name] = version

        logger.debug(f"Registered schema {schema_name} version {version}")

    def get_schema(self, schema_name: str, version: Optional[str] = None) -> Dict[str, Any]:
        """
        Get schema definition.
        
        Args:
            schema_name: Name of the schema
            version: Schema version (uses default if not provided)
        
        Returns:
            Schema definition dictionary
        
        Raises:
            SchemaVersionError: If schema or version not found
        """
        if schema_name not in self._schemas:
            raise SchemaVersionError(
                f"Schema '{schema_name}' not found",
                schema_name=schema_name,
            )

        if version is None:
            version = self._default_versions.get(schema_name)
            if version is None:
                raise SchemaVersionError(
                    f"No default version for schema '{schema_name}'",
                    schema_name=schema_name,
                )

        if version not in self._schemas[schema_name]:
            available_versions = list(self._schemas[schema_name].keys())
            raise SchemaVersionError(
                f"Version '{version}' not found for schema '{schema_name}'",
                schema_name=schema_name,
                version=version,
                supported_versions=available_versions,
            )

        return self._schemas[schema_name][version]

    def get_default_version(self, schema_name: str) -> Optional[str]:
        """
        Get default version for a schema.
        
        Args:
            schema_name: Name of the schema
        
        Returns:
            Default version string or None
        """
        return self._default_versions.get(schema_name)

    def get_versions(self, schema_name: str) -> List[str]:
        """
        Get all versions for a schema.
        
        Args:
            schema_name: Name of the schema
        
        Returns:
            List of version strings
        """
        if schema_name not in self._schemas:
            return []
        return list(self._schemas[schema_name].keys())

    def validate_envelope(
        self, envelope: Dict[str, Any], schema_name: Optional[str] = None
    ) -> bool:
        """
        Validate envelope against schema.
        
        Args:
            envelope: Envelope dictionary to validate
            schema_name: Schema name (extracted from envelope if not provided)
        
        Returns:
            True if valid, False otherwise
        
        Raises:
            SchemaValidationError: If validation fails with details
        """
        # Extract schema name from envelope if not provided
        if schema_name is None:
            schema_name = envelope.get("message_type")
            if schema_name is None:
                raise SchemaValidationError(
                    "Cannot determine schema name from envelope",
                    validation_errors=["Missing 'message_type' in envelope"],
                )

        # Extract version from envelope
        schema_version = envelope.get("schema_version")
        if schema_version is None:
            raise SchemaValidationError(
                f"Missing 'schema_version' in envelope for schema '{schema_name}'",
                schema_name=schema_name,
                validation_errors=["Missing 'schema_version' field"],
            )

        # Get schema definition
        try:
            schema_def = self.get_schema(schema_name, schema_version)
        except SchemaVersionError as e:
            raise SchemaValidationError(
                f"Schema validation failed: {str(e)}",
                schema_name=schema_name,
                validation_errors=[str(e)],
            ) from e

        # Validate required fields
        validation_errors: List[str] = []
        data = envelope.get("data", {})

        # Basic structure validation
        if not isinstance(data, dict):
            validation_errors.append("'data' field must be a dictionary")

        # Schema-specific validation (simplified - can be enhanced with JSON Schema)
        required_fields = schema_def.get("required", [])
        for field in required_fields:
            if field not in data:
                validation_errors.append(f"Missing required field: {field}")

        if validation_errors:
            raise SchemaValidationError(
                f"Schema validation failed for '{schema_name}'",
                schema_name=schema_name,
                validation_errors=validation_errors,
            )

        return True

    def has_schema(self, schema_name: str, version: Optional[str] = None) -> bool:
        """
        Check if schema exists.
        
        Args:
            schema_name: Name of the schema
            version: Schema version (optional)
        
        Returns:
            True if schema exists
        """
        if schema_name not in self._schemas:
            return False

        if version is None:
            return True

        return version in self._schemas[schema_name]


# Default schema registry instance
_default_registry = SchemaRegistry()


def get_default_registry() -> SchemaRegistry:
    """
    Get default schema registry instance.
    
    Returns:
        Default SchemaRegistry instance
    """
    return _default_registry

