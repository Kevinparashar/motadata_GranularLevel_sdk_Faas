"""
Migration Manager for CODEC Integration

Handles schema version migration for backward compatibility.
"""

import logging
from typing import Any, Callable, Dict, Optional

from .exceptions import MigrationError

logger = logging.getLogger(__name__)


class MigrationManager:
    """
    Manages schema version migrations.
    
    Provides migration registration and execution for schema version upgrades.
    """

    def __init__(self) -> None:
        """Initialize migration manager."""
        self._migrations: Dict[str, Dict[str, Callable]] = {}

    def register_migration(
        self,
        schema_name: str,
        from_version: str,
        to_version: str,
        migration_function: Callable[[Dict[str, Any]], Dict[str, Any]],
    ) -> None:
        """
        Register a migration function.
        
        Args:
            schema_name: Name of the schema
            from_version: Source version
            to_version: Target version
            migration_function: Function that takes old envelope and returns new envelope
        """
        if schema_name not in self._migrations:
            self._migrations[schema_name] = {}

        migration_key = f"{from_version}->{to_version}"
        self._migrations[schema_name][migration_key] = migration_function

        logger.debug(f"Registered migration for {schema_name}: {from_version} -> {to_version}")

    def migrate_envelope(
        self,
        envelope: Dict[str, Any],
        target_version: str,
        schema_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Migrate envelope to target version.
        
        Args:
            envelope: Envelope dictionary to migrate
            target_version: Target schema version
            schema_name: Schema name (extracted from envelope if not provided)
        
        Returns:
            Migrated envelope dictionary
        
        Raises:
            MigrationError: If migration fails
        """
        # Extract schema name from envelope if not provided
        if schema_name is None:
            schema_name = envelope.get("message_type")
            if schema_name is None:
                raise MigrationError(
                    "Cannot determine schema name from envelope for migration",
                    schema_name=None,
                )

        # Get current version
        current_version = envelope.get("schema_version")
        if current_version is None:
            raise MigrationError(
                f"Missing 'schema_version' in envelope for schema '{schema_name}'",
                schema_name=schema_name,
            )

        # If already at target version, return as-is
        if current_version == target_version:
            return envelope

        # Check if migration exists
        if schema_name not in self._migrations:
            raise MigrationError(
                f"No migrations registered for schema '{schema_name}'",
                schema_name=schema_name,
                from_version=current_version,
                to_version=target_version,
            )

        migration_key = f"{current_version}->{target_version}"
        if migration_key not in self._migrations[schema_name]:
            # Try to find a path through intermediate versions
            # For now, raise error - can be enhanced with path finding
            raise MigrationError(
                f"No migration path from {current_version} to {target_version} for schema '{schema_name}'",
                schema_name=schema_name,
                from_version=current_version,
                to_version=target_version,
            )

        # Execute migration
        try:
            migration_func = self._migrations[schema_name][migration_key]
            migrated_envelope = migration_func(envelope)
            logger.debug(
                f"Migrated {schema_name} from {current_version} to {target_version}"
            )
            return migrated_envelope
        except Exception as e:
            raise MigrationError(
                f"Migration failed for {schema_name} from {current_version} to {target_version}: {str(e)}",
                schema_name=schema_name,
                from_version=current_version,
                to_version=target_version,
                original_error=e,
            ) from e

    def has_migration(
        self, schema_name: str, from_version: str, to_version: str
    ) -> bool:
        """
        Check if migration exists.
        
        Args:
            schema_name: Name of the schema
            from_version: Source version
            to_version: Target version
        
        Returns:
            True if migration exists
        """
        if schema_name not in self._migrations:
            return False

        migration_key = f"{from_version}->{to_version}"
        return migration_key in self._migrations[schema_name]


# Default migration manager instance
_default_migration_manager = MigrationManager()


def get_default_migration_manager() -> MigrationManager:
    """
    Get default migration manager instance.
    
    Returns:
        Default MigrationManager instance
    """
    return _default_migration_manager

