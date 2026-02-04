"""
Configuration management for FaaS services.
"""


import os
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ServiceConfig(BaseModel):
    """Service configuration model."""

    # Service Identity
    service_name: str = Field(..., description="Service name")
    service_version: str = Field(default="1.0.0", description="Service version")
    service_port: int = Field(default=8080, description="Service port")

    # Dependencies
    gateway_service_url: Optional[str] = Field(None, description="Gateway service URL")
    cache_service_url: Optional[str] = Field(None, description="Cache service URL")
    rag_service_url: Optional[str] = Field(None, description="RAG service URL")
    agent_service_url: Optional[str] = Field(None, description="Agent service URL")
    ml_service_url: Optional[str] = Field(None, description="ML service URL")
    prompt_service_url: Optional[str] = Field(None, description="Prompt service URL")
    data_ingestion_service_url: Optional[str] = Field(
        None, description="Data ingestion service URL"
    )
    prompt_generator_service_url: Optional[str] = Field(
        None, description="Prompt Generator service URL"
    )
    llmops_service_url: Optional[str] = Field(None, description="LLMOps service URL")

    # Database
    database_url: str = Field(..., description="Database connection URL")
    redis_url: Optional[str] = Field(None, description="Redis connection URL")

    # Integrations
    nats_url: Optional[str] = Field(None, description="NATS server URL")
    otel_exporter_otlp_endpoint: Optional[str] = Field(
        None, description="OTEL OTLP exporter endpoint"
    )
    codec_type: str = Field(default="json", description="CODEC type (json, msgpack, protobuf)")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")

    # Feature Flags
    enable_nats: bool = Field(default=False, description="Enable NATS integration")
    enable_otel: bool = Field(default=False, description="Enable OTEL integration")
    enable_codec: bool = Field(default=False, description="Enable CODEC integration")

    model_config = ConfigDict(
        extra="ignore",
    )


_config: Optional[ServiceConfig] = None


def load_config(service_name: str, **overrides: Any) -> ServiceConfig:
    """
    Load service configuration from environment variables.

    Args:
        service_name: Name of the service
        **overrides: Configuration overrides

    Returns:
        ServiceConfig instance
    """
    global _config

    config_dict = {
        "service_name": service_name,
        "service_version": os.getenv("SERVICE_VERSION", "1.0.0"),
        "service_port": int(os.getenv("SERVICE_PORT", "8080")),
        "gateway_service_url": os.getenv("GATEWAY_SERVICE_URL"),
        "cache_service_url": os.getenv("CACHE_SERVICE_URL"),
        "rag_service_url": os.getenv("RAG_SERVICE_URL"),
        "agent_service_url": os.getenv("AGENT_SERVICE_URL"),
        "ml_service_url": os.getenv("ML_SERVICE_URL"),
        "prompt_service_url": os.getenv("PROMPT_SERVICE_URL"),
        "data_ingestion_service_url": os.getenv("DATA_INGESTION_SERVICE_URL"),
        "prompt_generator_service_url": os.getenv("PROMPT_GENERATOR_SERVICE_URL"),
        "llmops_service_url": os.getenv("LLMOPS_SERVICE_URL"),
        "database_url": os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/db"),
        "redis_url": os.getenv("REDIS_URL"),
        "nats_url": os.getenv("NATS_URL"),
        "otel_exporter_otlp_endpoint": os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
        "codec_type": os.getenv("CODEC_TYPE", "json"),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "enable_nats": os.getenv("ENABLE_NATS", "false").lower() == "true",
        "enable_otel": os.getenv("ENABLE_OTEL", "false").lower() == "true",
        "enable_codec": os.getenv("ENABLE_CODEC", "false").lower() == "true",
    }

    # Apply overrides
    config_dict.update(overrides)

    _config = ServiceConfig(**config_dict)
    return _config


def get_config() -> ServiceConfig:
    """
    Get current service configuration.

    Returns:
        ServiceConfig instance

    Raises:
        RuntimeError: If config is not loaded
    """
    if _config is None:
        raise RuntimeError("Configuration not loaded. Call load_config() first.")

    return _config
