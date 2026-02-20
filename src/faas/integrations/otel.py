# Copyright (c) 2024. All rights reserved.
# This source code is licensed under the MIT license and a copy
# of the license can be found in the LICENSE file in the root directory.

"""
OpenTelemetry Integration for FaaS services.

This module re-exports the core OTEL implementation for use in FaaS services.
All OTEL functionality is provided by src.core.otel_integration.
"""


import logging
from typing import Optional

# Re-export core OTEL implementation
from src.core.otel_integration.functions import create_otel_tracer as _create_otel_tracer
from src.core.otel_integration.otel_tracer import OTELTracer, OTELSpan

logger = logging.getLogger(__name__)

__all__ = ["OTELTracer", "OTELSpan", "create_otel_tracer"]


def create_otel_tracer(
    service_name: Optional[str] = None,
    otlp_endpoint: Optional[str] = None,
    environment: Optional[str] = None,
    service_version: Optional[str] = None,
) -> Optional[OTELTracer]:
    """
    Create OTEL tracer instance using core implementation.
    
    This function wraps the core create_otel_tracer to integrate with FaaS config.
    It reads configuration from FaaS ServiceConfig if available, otherwise uses
    provided parameters.

    Args:
        service_name: Service name (optional if config is loaded)
        otlp_endpoint: OTLP exporter endpoint (optional if config is loaded)
        environment: Environment name (optional if config is loaded)
        service_version: Service version (optional if config is loaded)

    Returns:
        OTELTracer instance or None if OTEL is disabled
        
    Example:
        >>> tracer = create_otel_tracer()
        >>> with tracer.start_trace("operation") as span:
        ...     span.set_attribute("key", "value")
    """
    from ..shared.config import get_config

    try:
        config = get_config()
        if not config.enable_otel:
            logger.info("OTEL integration is disabled")
            return None

        # Use config values if parameters not provided
        if service_name is None:
            service_name = config.service_name

        if otlp_endpoint is None:
            otlp_endpoint = config.otel_exporter_otlp_endpoint

        if environment is None:
            environment = getattr(config, "environment", "development")

        if service_version is None:
            service_version = getattr(config, "service_version", None)

        # Delegate to core implementation
        return _create_otel_tracer(
            service_name=service_name,
            otlp_endpoint=otlp_endpoint,
            environment=environment,
            service_version=service_version,
        )
    except RuntimeError:
        # Config not loaded, use provided values or defaults
        final_service_name = service_name or "faas-service"
        return _create_otel_tracer(
            service_name=final_service_name,
            otlp_endpoint=otlp_endpoint,
            environment=environment,
            service_version=service_version,
        )
