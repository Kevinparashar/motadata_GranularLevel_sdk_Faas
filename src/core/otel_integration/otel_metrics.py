"""
OTEL Metrics

OpenTelemetry metrics implementation for collecting and exporting metrics.
"""

import logging
from typing import Any, Dict, Optional

# Initialize _OTEL_AVAILABLE before try/except to avoid constant redefinition warning
_OTEL_AVAILABLE = False

try:
    from opentelemetry import metrics
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter  # type: ignore
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource

    _OTEL_AVAILABLE = True  # pyright: ignore[reportConstantRedefinition]
except ImportError:
    metrics = None

from .exceptions import OTELMetricsError

logger = logging.getLogger(__name__)


class OTELMetrics:
    """
    OpenTelemetry metrics collector.
    
    Provides counter, histogram, and gauge metrics.
    """

    def __init__(
        self,
        service_name: str,
        otlp_endpoint: Optional[str] = None,
        environment: Optional[str] = None,
    ):
        """
        Initialize OTEL metrics.
        
        Args:
            service_name: Name of the service
            otlp_endpoint: OTLP exporter endpoint (optional)
            environment: Environment name (e.g., "production", "development")
        """
        self.service_name = service_name
        self.otlp_endpoint = otlp_endpoint
        self.environment = environment or "development"
        self._counters: Dict[str, Any] = {}
        self._histograms: Dict[str, Any] = {}
        self._gauges: Dict[str, Any] = {}
        
        if _OTEL_AVAILABLE and otlp_endpoint:
            try:
                # Create resource
                resource = Resource.create({
                    "service.name": service_name,
                    "service.environment": self.environment,
                })
                
                # Create metric exporter
                exporter = OTLPMetricExporter(endpoint=otlp_endpoint)
                
                # Create metric reader
                reader = PeriodicExportingMetricReader(exporter, export_interval_millis=5000)
                
                # Create meter provider
                provider = MeterProvider(resource=resource, metric_readers=[reader])
                
                # Set global meter provider
                metrics.set_meter_provider(provider)
                
                # Get meter
                self._meter = metrics.get_meter(service_name)
                self._enabled = True
                logger.info(f"OTEL metrics initialized - service: {service_name}, endpoint: {otlp_endpoint}")
            except Exception as e:
                logger.warning(f"Failed to initialize OTEL metrics: {e}, using no-op implementation")
                self._meter = None
                self._enabled = False
        else:
            if not _OTEL_AVAILABLE:
                logger.debug("OpenTelemetry SDK not available, using no-op implementation")
            self._meter = None
            self._enabled = False

    def increment_counter(
        self,
        name: str,
        amount: float = 1.0,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Increment a counter metric.
        
        Args:
            name: Counter name
            amount: Amount to increment (default: 1.0)
            attributes: Optional attributes/labels
        """
        try:
            if self._enabled and self._meter:
                if name not in self._counters:
                    self._counters[name] = self._meter.create_counter(
                        name=name,
                        description=f"Counter metric: {name}",
                    )
                counter = self._counters[name]
                counter.add(amount, attributes=attributes or {})
            else:
                logger.debug(f"Counter '{name}' incremented by {amount} (no-op)")
        except Exception as e:
            logger.error(f"Failed to increment counter '{name}': {e}")
            raise OTELMetricsError(f"Failed to increment counter: {e}", metric_name=name, original_error=e)

    def record_histogram(
        self,
        name: str,
        value: float,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record a histogram metric.
        
        Args:
            name: Histogram name
            value: Value to record
            attributes: Optional attributes/labels
        """
        try:
            if self._enabled and self._meter:
                if name not in self._histograms:
                    self._histograms[name] = self._meter.create_histogram(
                        name=name,
                        description=f"Histogram metric: {name}",
                    )
                histogram = self._histograms[name]
                histogram.record(value, attributes=attributes or {})
            else:
                logger.debug(f"Histogram '{name}' recorded value {value} (no-op)")
        except Exception as e:
            logger.error(f"Failed to record histogram '{name}': {e}")
            raise OTELMetricsError(f"Failed to record histogram: {e}", metric_name=name, original_error=e)

    def set_gauge(
        self,
        name: str,
        value: float,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Set a gauge metric value.
        
        Args:
            name: Gauge name
            value: Gauge value
            attributes: Optional attributes/labels
        """
        try:
            if self._enabled and self._meter:
                if name not in self._gauges:
                    self._gauges[name] = self._meter.create_up_down_counter(
                        name=name,
                        description=f"Gauge metric: {name}",
                    )
                # For gauge, we use up_down_counter and set the value
                # Note: This is a simplified implementation
                # Store current value for reference
                self._gauge_values = getattr(self, "_gauge_values", {})
                self._gauge_values[name] = value
                # In a real implementation, you'd use an observable gauge
                logger.debug(f"Gauge '{name}' set to {value}")
            else:
                logger.debug(f"Gauge '{name}' set to {value} (no-op)")
        except Exception as e:
            logger.error(f"Failed to set gauge '{name}': {e}")
            raise OTELMetricsError(f"Failed to set gauge: {e}", metric_name=name, original_error=e)

