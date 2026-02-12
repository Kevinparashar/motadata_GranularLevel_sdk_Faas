"""
Unit tests for nats.py
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from src.faas.integrations.nats import NATSClient, create_nats_client


class TestNATSClient:
    """Tests for NATSClient class."""

    def test_init(self):
        """Test NATSClient initialization."""
        client = NATSClient(nats_url="nats://localhost:4222")

        assert client.nats_url == "nats://localhost:4222"
        assert client._connected is False

    @pytest.mark.asyncio
    async def test_connect(self):
        """Test connect() method."""
        client = NATSClient(nats_url="nats://localhost:4222")

        await client.connect()

        assert client._connected is True

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnect() method."""
        client = NATSClient(nats_url="nats://localhost:4222")
        client._connected = True

        await client.disconnect()

        assert client._connected is False

    @pytest.mark.asyncio
    async def test_publish_not_connected(self):
        """Test publish() when not connected."""
        client = NATSClient(nats_url="nats://localhost:4222")
        client._connected = False

        await client.publish(subject="test.subject", payload=b"test data")

        assert client._connected is True

    @pytest.mark.asyncio
    async def test_publish_already_connected(self):
        """Test publish() when already connected."""
        client = NATSClient(nats_url="nats://localhost:4222")
        client._connected = True

        await client.publish(subject="test.subject", payload=b"test data")

        assert client._connected is True

    @pytest.mark.asyncio
    async def test_publish_with_reply(self):
        """Test publish() with reply subject."""
        client = NATSClient(nats_url="nats://localhost:4222")
        client._connected = True

        await client.publish(subject="test.subject", payload=b"test data", reply="reply.subject")

        # Should complete without error

    @pytest.mark.asyncio
    async def test_subscribe_not_connected(self):
        """Test subscribe() when not connected."""
        client = NATSClient(nats_url="nats://localhost:4222")
        client._connected = False

        async def callback(msg):
            """Empty callback for testing subscription."""
            pass  # noqa: ARG001

        await client.subscribe(subject="test.subject", callback=callback)

        assert client._connected is True

    @pytest.mark.asyncio
    async def test_subscribe_already_connected(self):
        """Test subscribe() when already connected."""
        client = NATSClient(nats_url="nats://localhost:4222")
        client._connected = True

        async def callback(msg):
            """Empty callback for testing subscription."""
            pass  # noqa: ARG001

        await client.subscribe(subject="test.subject", callback=callback)

        assert client._connected is True

    @pytest.mark.asyncio
    async def test_subscribe_with_queue(self):
        """Test subscribe() with queue group."""
        client = NATSClient(nats_url="nats://localhost:4222")
        client._connected = True

        def sync_callback(msg):
            """Empty sync callback for testing subscription."""
            pass

        await client.subscribe(subject="test.subject", callback=sync_callback, queue="queue_group")

        # Should complete without error

    @pytest.mark.asyncio
    async def test_subscribe_with_async_callback(self):
        """Test subscribe() with async callback."""
        client = NATSClient(nats_url="nats://localhost:4222")
        client._connected = True

        async def async_callback(msg):
            """Async callback for testing subscription."""
            await asyncio.sleep(0)

        await client.subscribe(subject="test.subject", callback=async_callback)

        # Should complete without error

    @pytest.mark.asyncio
    async def test_request_not_connected(self):
        """Test request() when not connected."""
        client = NATSClient(nats_url="nats://localhost:4222")
        client._connected = False

        response = await client.request(subject="test.subject", payload=b"test data")

        assert client._connected is True
        assert response == b"{}"

    @pytest.mark.asyncio
    async def test_request_already_connected(self):
        """Test request() when already connected."""
        client = NATSClient(nats_url="nats://localhost:4222")
        client._connected = True

        response = await client.request(subject="test.subject", payload=b"test data")

        assert response == b"{}"

    @pytest.mark.asyncio
    async def test_request_with_timeout(self):
        """Test request() with custom timeout."""
        client = NATSClient(nats_url="nats://localhost:4222")
        client._connected = True

        response = await client.request(subject="test.subject", payload=b"test data", timeout=10.0)

        assert response == b"{}"


class TestCreateNATSClient:
    """Tests for create_nats_client factory function."""

    @pytest.mark.asyncio
    async def test_create_nats_client_with_url(self):
        """Test create_nats_client() with explicit URL."""
        # Ensure get_config raises RuntimeError to test the fallback path
        with patch("src.faas.shared.config.get_config", side_effect=RuntimeError("Config not loaded")):
            client = create_nats_client(nats_url="nats://localhost:4222")

            assert client is not None
            assert isinstance(client, NATSClient)
            assert client.nats_url == "nats://localhost:4222"

    @pytest.mark.asyncio
    async def test_create_nats_client_with_config_enabled(self):
        """Test create_nats_client() with config when NATS is enabled."""
        mock_config = MagicMock()
        mock_config.enable_nats = True
        mock_config.nats_url = "nats://config:4222"

        with patch("src.faas.shared.config.get_config", return_value=mock_config):
            client = create_nats_client()

            assert client is not None
            assert isinstance(client, NATSClient)
            assert client.nats_url == "nats://config:4222"

    @pytest.mark.asyncio
    async def test_create_nats_client_with_config_disabled(self):
        """Test create_nats_client() with config when NATS is disabled."""
        mock_config = MagicMock()
        mock_config.enable_nats = False

        with patch("src.faas.shared.config.get_config", return_value=mock_config):
            client = create_nats_client()

            assert client is None

    @pytest.mark.asyncio
    async def test_create_nats_client_with_config_no_url(self):
        """Test create_nats_client() with config but no URL configured."""
        mock_config = MagicMock()
        mock_config.enable_nats = True
        mock_config.nats_url = None

        with patch("src.faas.shared.config.get_config", return_value=mock_config):
            client = create_nats_client()

            assert client is None

    @pytest.mark.asyncio
    async def test_create_nats_client_with_config_empty_url(self):
        """Test create_nats_client() with config but empty URL."""
        mock_config = MagicMock()
        mock_config.enable_nats = True
        mock_config.nats_url = ""

        with patch("src.faas.shared.config.get_config", return_value=mock_config):
            client = create_nats_client()

            assert client is None

    @pytest.mark.asyncio
    async def test_create_nats_client_config_not_loaded_with_url(self):
        """Test create_nats_client() when config not loaded but URL provided."""
        with patch("src.faas.shared.config.get_config", side_effect=RuntimeError("Config not loaded")):
            client = create_nats_client(nats_url="nats://fallback:4222")

            assert client is not None
            assert isinstance(client, NATSClient)
            assert client.nats_url == "nats://fallback:4222"

    @pytest.mark.asyncio
    async def test_create_nats_client_config_not_loaded_no_url(self):
        """Test create_nats_client() when config not loaded and no URL provided."""
        with patch("src.faas.shared.config.get_config", side_effect=RuntimeError("Config not loaded")):
            client = create_nats_client()

            assert client is None

