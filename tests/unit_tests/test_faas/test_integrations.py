"""
Unit tests for FaaS Integration modules.
"""


import pytest

from src.faas.integrations.codec import CodecManager, create_codec_manager
from src.faas.integrations.nats import NATSClient, create_nats_client
from src.faas.integrations.otel import OTELSpan, OTELTracer, create_otel_tracer


class TestCodecManager:
    """Test CodecManager class."""

    @pytest.mark.asyncio
    async def test_encode_json(self):
        """Test encode with JSON codec."""
        codec = CodecManager(codec_type="json")
        data = {"key": "value", "number": 123}
        result = await codec.encode(data)
        assert isinstance(result, bytes)
        assert b"key" in result
        assert b"value" in result

    @pytest.mark.asyncio
    async def test_decode_json(self):
        """Test decode with JSON codec."""
        codec = CodecManager(codec_type="json")
        data = b'{"key": "value", "number": 123}'
        result = await codec.decode(data)
        assert isinstance(result, dict)
        assert result["key"] == "value"
        assert result["number"] == 123

    def test_init_msgpack_error(self):
        """Test CodecManager initialization with msgpack (should raise error)."""
        with pytest.raises(ValueError, match="Unsupported codec type"):
            CodecManager(codec_type="msgpack")

    def test_init_protobuf_error(self):
        """Test CodecManager initialization with protobuf (should raise error)."""
        with pytest.raises(ValueError, match="Unsupported codec type"):
            CodecManager(codec_type="protobuf")

    @pytest.mark.asyncio
    async def test_encode_unsupported_codec(self):
        """Test encode with unsupported codec type."""
        codec = CodecManager(codec_type="unsupported")
        with pytest.raises(ValueError, match="Unsupported codec type"):
            await codec.encode({"key": "value"})

    @pytest.mark.asyncio
    async def test_decode_unsupported_codec(self):
        """Test decode with unsupported codec type."""
        codec = CodecManager(codec_type="unsupported")
        with pytest.raises(ValueError, match="Unsupported codec type"):
            await codec.decode(b'{"key": "value"}')

    def test_create_codec_manager_default(self):
        """Test create_codec_manager with default."""
        # When config is not loaded, it should use default "json"
        from unittest.mock import patch
        with patch("src.faas.shared.config.get_config", side_effect=RuntimeError("Config not loaded")):
            manager = create_codec_manager(codec_type=None)
            assert isinstance(manager, CodecManager)
            assert manager.codec_type == "json"

    def test_create_codec_manager_with_type(self):
        """Test create_codec_manager with explicit type."""
        manager = create_codec_manager(codec_type="json")
        assert isinstance(manager, CodecManager)
        assert manager.codec_type == "json"


class TestNATSClient:
    """Test NATSClient class."""

    def test_initialization(self):
        """Test NATSClient initialization."""
        client = NATSClient(nats_url="nats://localhost:4222")
        assert client.nats_url == "nats://localhost:4222"
        assert client._connected is False

    @pytest.mark.asyncio
    async def test_connect(self):
        """Test NATSClient connect."""
        client = NATSClient(nats_url="nats://localhost:4222")
        await client.connect()
        assert client._connected is True

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test NATSClient disconnect."""
        client = NATSClient(nats_url="nats://localhost:4222")
        await client.connect()
        await client.disconnect()
        assert client._connected is False

    @pytest.mark.asyncio
    async def test_publish(self):
        """Test NATSClient publish."""
        client = NATSClient(nats_url="nats://localhost:4222")
        await client.connect()
        # Publish should not raise (placeholder implementation)
        await client.publish("test.subject", b"test data")

    @pytest.mark.asyncio
    async def test_subscribe(self):
        """Test NATSClient subscribe."""
        client = NATSClient(nats_url="nats://localhost:4222")
        await client.connect()
        # Subscribe should not raise (placeholder implementation)
        await client.subscribe("test.subject", lambda msg: None)

    def test_create_nats_client(self):
        """Test create_nats_client factory function."""
        from unittest.mock import patch
        with patch("src.faas.shared.config.get_config", side_effect=RuntimeError("Config not loaded")):
            client = create_nats_client(nats_url="nats://localhost:4222")
            assert isinstance(client, NATSClient)


class TestOTELTracer:
    """Test OTELTracer class."""

    def test_initialization(self):
        """Test OTELTracer initialization."""
        tracer = OTELTracer(service_name="test-service")
        assert tracer.service_name == "test-service"
        assert tracer.otlp_endpoint is None

    def test_initialization_with_endpoint(self):
        """Test OTELTracer initialization with endpoint."""
        tracer = OTELTracer(service_name="test-service", otlp_endpoint="http://localhost:4317")
        assert tracer.service_name == "test-service"
        assert tracer.otlp_endpoint == "http://localhost:4317"

    def test_start_span(self):
        """Test OTELTracer start_span."""
        tracer = OTELTracer(service_name="test-service")
        span = tracer.start_span("test-span")
        assert isinstance(span, OTELSpan)
        assert span.name == "test-span"

    def test_get_current_span(self):
        """Test OTELTracer get_current_span."""
        tracer = OTELTracer(service_name="test-service")
        span = tracer.get_current_span()
        # Placeholder returns None
        assert span is None

    def test_create_otel_tracer(self):
        """Test create_otel_tracer factory function."""
        from unittest.mock import patch
        with patch("src.faas.shared.config.get_config", side_effect=RuntimeError("Config not loaded")):
            tracer = create_otel_tracer(service_name="test-service")
            assert isinstance(tracer, OTELTracer)


class TestOTELSpan:
    """Test OTELSpan class."""

    def test_initialization(self):
        """Test OTELSpan initialization."""
        span = OTELSpan("test-span")
        assert span.name == "test-span"

    def test_set_attribute(self):
        """Test OTELSpan set_attribute."""                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      
        span = OTELSpan("test-span")
        span.set_attribute("key", "value")
        # Placeholder implementation, should not raise

    def test_add_event(self):
        """Test OTELSpan add_event."""
        span = OTELSpan("test-span")
        span.add_event("test-event")
        # Placeholder implementation, should not raise

    def test_end(self):
        """Test OTELSpan end."""
        span = OTELSpan("test-span")
        span.end()
        # Placeholder implementation, should not raise

    def test_context_manager(self):
        """Test OTELSpan as context manager."""
        span = OTELSpan("test-span")
        with span:
            # Context manager should work
            assert span.name == "test-span"

