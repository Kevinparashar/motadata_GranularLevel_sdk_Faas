"""
NATS Integration for FaaS services.

Provides message bus functionality for service-to-service communication.
"""

import asyncio
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class NATSClient:
    """
    NATS client for message bus communication.

    This is a placeholder implementation. Replace with actual NATS client
    when NATS integration is implemented.
    """

    def __init__(self, nats_url: str):
        """
        Initialize NATS client.

        Args:
            nats_url: NATS server URL (e.g., "nats://localhost:4222")
        """
        self.nats_url = nats_url
        self._connected = False
        logger.info(f"NATS client initialized (placeholder) - URL: {nats_url}")

    async def connect(self):
        """Connect to NATS server."""
        # TODO: SDK-INT-001 - Implement actual NATS connection  # noqa: FIX002, S1135
        # Placeholder implementation - replace with actual NATS client when integration is ready
        # from nats.aio.client import Client as NATS
        # self._client = NATS()
        # await self._client.connect(self.nats_url)
        await asyncio.sleep(0)  # Make function truly async for placeholder
        self._connected = True
        logger.info("NATS client connected (placeholder)")

    async def disconnect(self):
        """Disconnect from NATS server."""
        # TODO: SDK-INT-001 - Implement actual NATS disconnection  # noqa: FIX002, S1135
        # Placeholder implementation - replace with actual NATS client when integration is ready
        # if self._client:
        #     await self._client.close()
        await asyncio.sleep(0)  # Make function truly async for placeholder
        self._connected = False
        logger.info("NATS client disconnected (placeholder)")

    async def publish(self, subject: str, payload: bytes, reply: Optional[str] = None):
        """
        Publish message to NATS subject.

        Args:
            subject: NATS subject (e.g., "gateway.generate.request")
            payload: Message payload (bytes)
            reply: Optional reply subject
        """
        if not self._connected:
            await self.connect()

        # TODO: SDK-INT-001 - Implement actual NATS publish  # noqa: FIX002, S1135
        # Placeholder implementation - replace with actual NATS client when integration is ready
        # await self._client.publish(subject, payload, reply=reply)
        logger.info(f"NATS publish (placeholder): subject={subject}, payload_size={len(payload)}")

    async def subscribe(self, subject: str, _callback: Callable, queue: Optional[str] = None):
        """
        Subscribe to NATS subject.

        Args:
            subject: NATS subject (e.g., "gateway.generate.request")
            callback: Callback function to handle messages
            queue: Optional queue group name
        """
        if not self._connected:
            await self.connect()

        # TODO: SDK-INT-001 - Implement actual NATS subscribe  # noqa: FIX002, S1135
        # Placeholder implementation - replace with actual NATS client when integration is ready
        # await self._client.subscribe(subject, cb=_callback, queue=queue)
        logger.info(f"NATS subscribe (placeholder): subject={subject}, queue={queue}")

    async def request(self, subject: str, payload: bytes, timeout: float = 5.0) -> bytes:  # noqa: S7483
        """
        Send request and wait for response.

        Args:
            subject: NATS subject
            payload: Request payload (bytes)
            timeout: Request timeout in seconds

        Returns:
            Response payload (bytes)
        """
        if not self._connected:
            await self.connect()

        # TODO: SDK-INT-001 - Implement actual NATS request  # noqa: FIX002, S1135
        # Placeholder implementation - replace with actual NATS client when integration is ready
        # response = await self._client.request(subject, payload, timeout=timeout)
        # return response.data
        logger.info(f"NATS request (placeholder): subject={subject}, timeout={timeout}")
        return b"{}"  # Placeholder response


def create_nats_client(nats_url: Optional[str] = None) -> Optional[NATSClient]:
    """
    Create NATS client instance.

    Args:
        nats_url: NATS server URL (optional if config is loaded)

    Returns:
        NATSClient instance or None if NATS is disabled
    """
    from ..shared.config import get_config

    try:
        config = get_config()
        if not config.enable_nats:
            logger.info("NATS integration is disabled")
            return None

        if nats_url is None:
            nats_url = config.nats_url

        if not nats_url:
            logger.warning("NATS URL not configured")
            return None

        client = NATSClient(nats_url)
        return client
    except RuntimeError:
        # Config not loaded, use provided URL
        if nats_url:
            return NATSClient(nats_url)
        return None
