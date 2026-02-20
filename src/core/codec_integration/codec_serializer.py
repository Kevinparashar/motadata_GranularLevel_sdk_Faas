"""
CODEC Serializer

Main serializer class for encoding/decoding messages with schema validation and versioning.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from .exceptions import (
    CodecDecodingError,
    CodecEncodingError,
)
from .bootstrap import register_all_schemas
from .migration_manager import MigrationManager, get_default_migration_manager
from .schema_registry import SchemaRegistry, get_default_registry

logger = logging.getLogger(__name__)


class CodecSerializer:
    """
    Main CODEC serializer for message encoding/decoding.
    
    Provides envelope creation, encoding, decoding, schema validation, and version migration.
    """

    def __init__(
        self,
        schema_registry: Optional[SchemaRegistry] = None,
        migration_manager: Optional[MigrationManager] = None,
        codec_type: str = "json",
    ) -> None:
        """
        Initialize codec serializer.
        
        Args:
            schema_registry: Schema registry instance (uses default if not provided)
            migration_manager: Migration manager instance (uses default if not provided)
            codec_type: Codec type ("json" only - other types are not supported)
            
        Raises:
            ValueError: If codec_type is not "json"
        """
        if codec_type != "json":
            raise ValueError(
                f"Unsupported codec type: {codec_type}. Only 'json' is supported."
            )
        self.schema_registry = schema_registry or get_default_registry()
        self.migration_manager = migration_manager or get_default_migration_manager()
        self.codec_type = codec_type
        # Use bootstrap to ensure consistent schema registration
        register_all_schemas(self.schema_registry)

    def create_envelope(
        self,
        message_type: str,
        schema_version: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create a message envelope.
        
        Args:
            message_type: Type of message (e.g., "agent_message")
            schema_version: Schema version (e.g., "1.0")
            data: Message data dictionary
        
        Returns:
            Envelope dictionary with schema_version, message_type, and data
        """
        return {
            "schema_version": schema_version,
            "message_type": message_type,
            "data": data,
            "created_at": datetime.now().isoformat(),
        }

    async def encode(self, envelope: Dict[str, Any]) -> bytes:
        """
        Encode envelope to bytes.
        
        Args:
            envelope: Envelope dictionary to encode
        
        Returns:
            Encoded bytes
        
        Raises:
            CodecEncodingError: If encoding fails
        """
        try:
            if self.codec_type == "json":
                def _encode_json() -> bytes:
                    """Encode data to JSON bytes."""
                    return json.dumps(envelope, default=str).encode("utf-8")

                return await asyncio.to_thread(_encode_json)
            else:
                raise CodecEncodingError(
                    f"Unsupported codec type: {self.codec_type}. Only 'json' is supported.",
                    message_type=envelope.get("message_type"),
                )
        except Exception as e:
            raise CodecEncodingError(
                f"Failed to encode envelope: {str(e)}",
                message_type=envelope.get("message_type"),
                data=envelope.get("data"),
                original_error=e,
            ) from e

    async def decode(self, payload: bytes) -> Dict[str, Any]:
        """
        Decode bytes to envelope.
        
        Args:
            payload: Encoded bytes to decode
        
        Returns:
            Decoded envelope dictionary
        
        Raises:
            CodecDecodingError: If decoding fails
        """
        try:
            if self.codec_type == "json":
                def _decode_json() -> Dict[str, Any]:
                    """Decode JSON bytes to dictionary."""
                    return json.loads(payload.decode("utf-8"))

                return await asyncio.to_thread(_decode_json)
            else:
                raise CodecDecodingError(
                    f"Unsupported codec type: {self.codec_type}. Only 'json' is supported.",
                    payload=payload[:100] if len(payload) > 100 else payload,
                )
        except json.JSONDecodeError as e:
            raise CodecDecodingError(
                f"Failed to decode JSON payload: {str(e)}",
                payload=payload[:100] if len(payload) > 100 else payload,
                original_error=e,
            ) from e
        except Exception as e:
            raise CodecDecodingError(
                f"Failed to decode payload: {str(e)}",
                payload=payload[:100] if len(payload) > 100 else payload,
                original_error=e,
            ) from e

    def validate_schema(
        self, envelope: Dict[str, Any], schema_name: Optional[str] = None
    ) -> bool:
        """
        Validate envelope against schema.
        
        Args:
            envelope: Envelope dictionary to validate
            schema_name: Schema name (extracted from envelope if not provided)
        
        Returns:
            True if valid
        
        Raises:
            SchemaValidationError: If validation fails
        """
        return self.schema_registry.validate_envelope(envelope, schema_name)

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
        return self.migration_manager.migrate_envelope(
            envelope, target_version, schema_name
        )

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
            schema_name: Name of the schema
            version: Schema version
            schema_definition: Schema definition dictionary
            is_default: Whether this is the default version
        """
        self.schema_registry.register_schema(
            schema_name, version, schema_definition, is_default
        )

    def register_migration(
        self,
        schema_name: str,
        from_version: str,
        to_version: str,
        migration_function: Any,
    ) -> None:
        """
        Register a migration function.
        
        Args:
            schema_name: Name of the schema
            from_version: Source version
            to_version: Target version
            migration_function: Function that performs migration
        """
        self.migration_manager.register_migration(
            schema_name, from_version, to_version, migration_function
        )

