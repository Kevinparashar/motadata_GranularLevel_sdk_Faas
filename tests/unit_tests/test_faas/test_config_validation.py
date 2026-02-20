"""
Unit Tests for FaaS Config Validation

Tests Pydantic validators and configuration validation.
"""

from pydantic import ValidationError

from src.faas.shared.config import ServiceConfig


class TestCodecTypeValidation:
    """Tests for codec_type field validation."""

    def test_codec_type_valid_json(self):
        """Test that 'json' codec_type is accepted."""
        config = ServiceConfig(
            service_name="test-service",
            database_url="postgresql://user:pass@localhost/db",
            codec_type="json",
            gateway_service_url=None,
            cache_service_url=None,
            rag_service_url=None,
            agent_service_url=None,
            ml_service_url=None,
            prompt_service_url=None,
            data_ingestion_service_url=None,
            prompt_generator_service_url=None,
            llmops_service_url=None,
            dragonfly_url=None,
            nats_url=None,
            otel_exporter_otlp_endpoint=None,
        )
        assert config.codec_type == "json"

    def test_codec_type_invalid_msgpack(self):
        """Test that 'msgpack' codec_type is rejected."""
        try:
            ServiceConfig(
                service_name="test-service",
                database_url="postgresql://user:pass@localhost/db",
                codec_type="msgpack",
                gateway_service_url=None,
                cache_service_url=None,
                rag_service_url=None,
                agent_service_url=None,
                ml_service_url=None,
                prompt_service_url=None,
                data_ingestion_service_url=None,
                prompt_generator_service_url=None,
                llmops_service_url=None,
                dragonfly_url=None,
                nats_url=None,
                otel_exporter_otlp_endpoint=None,
            )
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            assert len(e.errors()) > 0
            error = e.errors()[0]
            assert error["loc"] == ("codec_type",)
            assert "Unsupported codec type" in str(error["msg"]).lower() or "unsupported codec type" in str(e)

    def test_codec_type_invalid_protobuf(self):
        """Test that 'protobuf' codec_type is rejected."""
        try:
            ServiceConfig(
                service_name="test-service",
                database_url="postgresql://user:pass@localhost/db",
                codec_type="protobuf",
                gateway_service_url=None,
                cache_service_url=None,
                rag_service_url=None,
                agent_service_url=None,
                ml_service_url=None,
                prompt_service_url=None,
                data_ingestion_service_url=None,
                prompt_generator_service_url=None,
                llmops_service_url=None,
                dragonfly_url=None,
                nats_url=None,
                otel_exporter_otlp_endpoint=None,
            )
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            assert len(e.errors()) > 0
            error = e.errors()[0]
            assert error["loc"] == ("codec_type",)
            assert "Unsupported codec type" in str(error["msg"]).lower() or "unsupported codec type" in str(e)

    def test_codec_type_invalid_other(self):
        """Test that other invalid codec_type values are rejected."""
        invalid_types = ["yaml", "xml", "binary", "custom", ""]
        for invalid_type in invalid_types:
            try:
                ServiceConfig(
                    service_name="test-service",
                    database_url="postgresql://user:pass@localhost/db",
                    codec_type=invalid_type,
                    gateway_service_url=None,
                    cache_service_url=None,
                    rag_service_url=None,
                    agent_service_url=None,
                    ml_service_url=None,
                    prompt_service_url=None,
                    data_ingestion_service_url=None,
                    prompt_generator_service_url=None,
                    llmops_service_url=None,
                    dragonfly_url=None,
                    nats_url=None,
                    otel_exporter_otlp_endpoint=None,
                )
                assert False, f"Should have raised ValidationError for {invalid_type}"
            except ValidationError as e:
                assert len(e.errors()) > 0
                error = e.errors()[0]
                assert error["loc"] == ("codec_type",)

    def test_codec_type_default(self):
        """Test that default codec_type is 'json'."""
        config = ServiceConfig(
            service_name="test-service",
            database_url="postgresql://user:pass@localhost/db",
            gateway_service_url=None,
            cache_service_url=None,
            rag_service_url=None,
            agent_service_url=None,
            ml_service_url=None,
            prompt_service_url=None,
            data_ingestion_service_url=None,
            prompt_generator_service_url=None,
            llmops_service_url=None,
            dragonfly_url=None,
            nats_url=None,
            otel_exporter_otlp_endpoint=None,
        )
        assert config.codec_type == "json"

    def test_codec_type_case_sensitive(self):
        """Test that codec_type validation is case-sensitive."""
        # "JSON" should be rejected (only "json" is valid)
        try:
            ServiceConfig(
                service_name="test-service",
                database_url="postgresql://user:pass@localhost/db",
                codec_type="JSON",
                gateway_service_url=None,
                cache_service_url=None,
                rag_service_url=None,
                agent_service_url=None,
                ml_service_url=None,
                prompt_service_url=None,
                data_ingestion_service_url=None,
                prompt_generator_service_url=None,
                llmops_service_url=None,
                dragonfly_url=None,
                nats_url=None,
                otel_exporter_otlp_endpoint=None,
            )
            assert False, "Should have raised ValidationError for 'JSON'"
        except ValidationError:
            pass  # Expected

        # "Json" should be rejected
        try:
            ServiceConfig(
                service_name="test-service",
                database_url="postgresql://user:pass@localhost/db",
                codec_type="Json",
                gateway_service_url=None,
                cache_service_url=None,
                rag_service_url=None,
                agent_service_url=None,
                ml_service_url=None,
                prompt_service_url=None,
                data_ingestion_service_url=None,
                prompt_generator_service_url=None,
                llmops_service_url=None,
                dragonfly_url=None,
                nats_url=None,
                otel_exporter_otlp_endpoint=None,
            )
            assert False, "Should have raised ValidationError for 'Json'"
        except ValidationError:
            pass  # Expected


class TestConfigLoadWithCodecType:
    """Tests for load_config with codec_type validation."""

    def test_load_config_valid_codec_type(self):
        """Test load_config with valid codec_type."""
        from src.faas.shared.config import load_config

        config = load_config(
            service_name="test-service",
            codec_type="json",
        )
        assert config.codec_type == "json"

    def test_load_config_invalid_codec_type(self):
        """Test load_config with invalid codec_type."""
        from src.faas.shared.config import load_config

        try:
            load_config(
                service_name="test-service",
                codec_type="msgpack",
            )
            assert False, "Should have raised ValidationError"
        except ValidationError:
            pass  # Expected

    def test_load_config_default_codec_type(self):
        """Test load_config with default codec_type."""
        import os
        from src.faas.shared.config import load_config

        # Save original env var if exists
        original = os.environ.get("CODEC_TYPE")
        try:
            # Remove CODEC_TYPE to test default
            if "CODEC_TYPE" in os.environ:
                del os.environ["CODEC_TYPE"]

            config = load_config(service_name="test-service")
            assert config.codec_type == "json"
        finally:
            # Restore original env var
            if original is not None:
                os.environ["CODEC_TYPE"] = original

