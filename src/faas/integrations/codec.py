# Copyright (c) 2024. All rights reserved.
# This source code is licensed under the MIT license and a copy
# of the license can be found in the LICENSE file in the root directory.

"""
CODEC Integration for FaaS services.

Provides message serialization/deserialization for efficient data encoding.
"""


import logging
from typing import Any, Dict, Optional

# Import core codec integration (required)
from ...core.codec_integration import create_codec_serializer

logger = logging.getLogger(__name__)


class CodecManager:
    """
    Codec manager for message serialization/deserialization.

    Wraps core CodecSerializer for FaaS services with envelope support.
    """

    def __init__(self, codec_type: str = "json"):
        """
        Initialize codec manager.
        
        Args:
            codec_type (str): Codec type ("json" only - other types are not supported)
            
        Raises:
            ValueError: If codec_type is not "json"
        """
        if codec_type != "json":
            raise ValueError(
                f"Unsupported codec type: {codec_type}. Only 'json' is supported."
            )
        self.codec_type = codec_type
        # Core codec serializer is required
        self._codec = create_codec_serializer(codec_type=codec_type)
        logger.info(f"Codec manager initialized with core serializer - type: {codec_type}")

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
            Envelope dictionary
        """
        return self._codec.create_envelope(message_type, schema_version, data)

    async def encode(self, data: Dict[str, Any]) -> bytes:
        """
        Encode data to bytes asynchronously.
        
        If data is already an envelope (has schema_version and message_type),
        encodes it directly. Otherwise, wraps it in a basic envelope.
        
        Args:
            data (Dict[str, Any]): Data dictionary or envelope dictionary
        
        Returns:
            bytes: Result of the operation.
        
        Raises:
            ValueError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        # Check if data is already an envelope
        if isinstance(data, dict) and "schema_version" in data and "message_type" in data:
            envelope = data
        else:
            # Wrap in basic envelope
            envelope = self.create_envelope("generic_message", "1.0", data)
        
        # Use core codec (required)
        try:
            return await self._codec.encode(envelope)
        except Exception as e:
            # Convert CodecEncodingError to ValueError for backward compatibility
            if "Unsupported codec type" in str(e) or "unsupported" in str(e).lower():
                raise ValueError(f"Unsupported codec type: {self.codec_type}") from e
            raise

    async def decode(self, data: bytes) -> Dict[str, Any]:
        """
        Decode bytes to envelope dictionary asynchronously.
        
        Args:
            data (bytes): Encoded bytes to decode
        
        Returns:
            Dict[str, Any]: Envelope dictionary with schema_version, message_type, and data
        
        Raises:
            ValueError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        # Use core codec (required)
        try:
            return await self._codec.decode(data)
        except Exception as e:
            # Convert CodecDecodingError to ValueError for backward compatibility
            if "Unsupported codec type" in str(e) or "unsupported" in str(e).lower():
                raise ValueError(f"Unsupported codec type: {self.codec_type}") from e
            raise
    
    def validate_schema(self, envelope: Dict[str, Any], schema_name: Optional[str] = None) -> bool:
        """
        Validate envelope against schema.
        
        Args:
            envelope: Envelope dictionary to validate
            schema_name: Optional schema name (extracted from envelope if not provided)
        
        Returns:
            True if valid
        
        Raises:
            ValueError: If validation fails
        """
        return self._codec.validate_schema(envelope, schema_name)


def create_codec_manager(codec_type: Optional[str] = None) -> CodecManager:
    """
    Create codec manager instance.

    Args:
        codec_type: Codec type (optional if config is loaded)

    Returns:
        CodecManager instance
    """
    from ..shared.config import get_config

    try:
        config = get_config()
        if codec_type is None:
            codec_type = config.codec_type
    except RuntimeError:
        # Config not loaded, use default
        if codec_type is None:
            codec_type = "json"

    return CodecManager(codec_type)
