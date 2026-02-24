"""
CODEC Serializer

Main serializer class for encoding/decoding messages with schema validation and versioning.
"""

import asyncio
import json
import logging
import uuid
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
        codec_context_dal: Optional[Any] = None,
    ) -> None:
        """
        Initialize codec serializer.
        
        Args:
            schema_registry: Schema registry instance (uses default if not provided)
            migration_manager: Migration manager instance (uses default if not provided)
            codec_type: Codec type ("json" only - other types are not supported)
            codec_context_dal: Optional CodecContextDAL for context persistence
            
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
        self.codec_context_dal = codec_context_dal
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

    async def encode(
        self,
        envelope: Dict[str, Any],
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> bytes:
        """
        Encode envelope to bytes.
        
        Args:
            envelope: Envelope dictionary to encode
            tenant_id: Optional tenant identifier.
            user_id: Optional user identifier.
            correlation_id: Optional correlation ID for request tracking.
        
        Returns:
            Encoded bytes
        
        Raises:
            CodecEncodingError: If encoding fails
        """
        operation_id = f"codec_op_{uuid.uuid4().hex[:16]}"
        message_type = envelope.get("message_type", "unknown")
        schema_version = envelope.get("schema_version", "unknown")
        status = "success"
        error_message = None
        error_type = None
        payload_size = None

        try:
            if self.codec_type == "json":
                def _encode_json() -> bytes:
                    """Encode data to JSON bytes."""
                    return json.dumps(envelope, default=str).encode("utf-8")

                encoded = await asyncio.to_thread(_encode_json)
                payload_size = len(encoded)

                # Save codec context (non-blocking)
                if self.codec_context_dal:
                    try:
                        await self.codec_context_dal.save_codec_operation(
                            operation_id=operation_id,
                            operation_type="encode",
                            message_type=message_type,
                            schema_version=schema_version,
                            codec_type=self.codec_type,
                            tenant_id=tenant_id,
                            user_id=user_id,
                            correlation_id=correlation_id,
                            payload_size=payload_size,
                            status=status,
                            validation_performed=False,
                            context_state={"envelope_keys": list(envelope.keys())},
                            metadata={"data_keys": list(envelope.get("data", {}).keys()) if isinstance(envelope.get("data"), dict) else None},
                        )
                    except Exception as e:
                        logger.debug(f"Failed to save codec encode context (non-critical): {e}")

                return encoded
            else:
                raise CodecEncodingError(
                    f"Unsupported codec type: {self.codec_type}. Only 'json' is supported.",
                    message_type=envelope.get("message_type"),
                )
        except Exception as e:
            status = "error"
            error_message = str(e)
            error_type = type(e).__name__

            # Save error context (non-blocking)
            if self.codec_context_dal:
                try:
                    await self.codec_context_dal.save_codec_operation(
                        operation_id=operation_id,
                        operation_type="encode",
                        message_type=message_type,
                        schema_version=schema_version,
                        codec_type=self.codec_type,
                        tenant_id=tenant_id,
                        user_id=user_id,
                        correlation_id=correlation_id,
                        payload_size=payload_size,
                        status=status,
                        error_message=error_message,
                        error_type=error_type,
                        validation_performed=False,
                        metadata={"error_category": "encoding_error"},
                    )
                except Exception as hist_e:
                    logger.debug(f"Failed to save codec encode error context (non-critical): {hist_e}")

            raise CodecEncodingError(
                f"Failed to encode envelope: {str(e)}",
                message_type=envelope.get("message_type"),
                data=envelope.get("data"),
                original_error=e,
            ) from e

    async def decode(
        self,
        payload: bytes,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        validate: bool = False,
        target_version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Decode bytes to envelope.
        
        Args:
            payload: Encoded bytes to decode
            tenant_id: Optional tenant identifier.
            user_id: Optional user identifier.
            correlation_id: Optional correlation ID for request tracking.
            validate: Whether to validate schema after decoding.
            target_version: Optional target schema version (for migration).
        
        Returns:
            Decoded envelope dictionary
        
        Raises:
            CodecDecodingError: If decoding fails
        """
        operation_id = f"codec_op_{uuid.uuid4().hex[:16]}"
        payload_size = len(payload)
        status = "success"
        error_message = None
        error_type = None
        message_type = "unknown"
        schema_version = "unknown"
        migration_used = False
        source_version = None
        validation_performed = False
        validation_passed = None

        try:
            if self.codec_type == "json":
                def _decode_json() -> Dict[str, Any]:
                    """Decode JSON bytes to dictionary."""
                    return json.loads(payload.decode("utf-8"))

                envelope = await asyncio.to_thread(_decode_json)
                message_type = envelope.get("message_type", "unknown")
                schema_version = envelope.get("schema_version", "unknown")
                source_version = schema_version

                # Perform migration if target version specified
                if target_version and target_version != schema_version:
                    try:
                        envelope = self.migrate_envelope(envelope, target_version, message_type)
                        migration_used = True
                        schema_version = target_version
                    except Exception as mig_e:
                        logger.debug(f"Migration failed (non-critical): {mig_e}")

                # Perform validation if requested
                if validate:
                    try:
                        validation_performed = True
                        validation_passed = self.validate_schema(envelope, message_type)
                    except Exception as val_e:
                        validation_performed = True
                        validation_passed = False
                        logger.debug(f"Validation failed: {val_e}")

                # Save codec context (non-blocking)
                if self.codec_context_dal:
                    try:
                        await self.codec_context_dal.save_codec_operation(
                            operation_id=operation_id,
                            operation_type="decode",
                            message_type=message_type,
                            schema_version=schema_version,
                            codec_type=self.codec_type,
                            tenant_id=tenant_id,
                            user_id=user_id,
                            correlation_id=correlation_id,
                            payload_size=payload_size,
                            status=status,
                            migration_used=migration_used,
                            source_version=source_version,
                            target_version=target_version,
                            validation_performed=validation_performed,
                            validation_passed=validation_passed,
                            context_state={"envelope_keys": list(envelope.keys())},
                            metadata={"data_keys": list(envelope.get("data", {}).keys()) if isinstance(envelope.get("data"), dict) else None},
                        )
                    except Exception as e:
                        logger.debug(f"Failed to save codec decode context (non-critical): {e}")

                return envelope
            else:
                raise CodecDecodingError(
                    f"Unsupported codec type: {self.codec_type}. Only 'json' is supported.",
                    payload=payload[:100] if len(payload) > 100 else payload,
                )
        except json.JSONDecodeError as e:
            status = "error"
            error_message = str(e)
            error_type = "JSONDecodeError"

            # Save error context (non-blocking)
            if self.codec_context_dal:
                try:
                    await self.codec_context_dal.save_codec_operation(
                        operation_id=operation_id,
                        operation_type="decode",
                        message_type=message_type,
                        schema_version=schema_version,
                        codec_type=self.codec_type,
                        tenant_id=tenant_id,
                        user_id=user_id,
                        correlation_id=correlation_id,
                        payload_size=payload_size,
                        status=status,
                        error_message=error_message,
                        error_type=error_type,
                        validation_performed=validation_performed,
                        metadata={"error_category": "json_decode_error"},
                    )
                except Exception as hist_e:
                    logger.debug(f"Failed to save codec decode error context (non-critical): {hist_e}")

            raise CodecDecodingError(
                f"Failed to decode JSON payload: {str(e)}",
                payload=payload[:100] if len(payload) > 100 else payload,
                original_error=e,
            ) from e
        except Exception as e:
            status = "error"
            error_message = str(e)
            error_type = type(e).__name__

            # Save error context (non-blocking)
            if self.codec_context_dal:
                try:
                    await self.codec_context_dal.save_codec_operation(
                        operation_id=operation_id,
                        operation_type="decode",
                        message_type=message_type,
                        schema_version=schema_version,
                        codec_type=self.codec_type,
                        tenant_id=tenant_id,
                        user_id=user_id,
                        correlation_id=correlation_id,
                        payload_size=payload_size,
                        status=status,
                        error_message=error_message,
                        error_type=error_type,
                        validation_performed=validation_performed,
                        metadata={"error_category": "decode_error"},
                    )
                except Exception as hist_e:
                    logger.debug(f"Failed to save codec decode error context (non-critical): {hist_e}")

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

