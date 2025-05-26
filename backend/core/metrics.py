"""
Backend metrics module with collision avoidance.

This module provides Prometheus metrics for the backend with safeguards
against duplicate registration when legacy code is also imported.
"""

import logging
from typing import TypeVar

from prometheus_client import REGISTRY, Counter, Gauge, Histogram

logger = logging.getLogger(__name__)

# Type variable for metric types
MetricType = TypeVar("MetricType", Counter, Gauge, Histogram)

__all__ = [
    "get_can_tx_enqueue_latency",
    "get_can_tx_enqueue_total",
    "get_can_tx_queue_length",
    "get_http_latency",
    "get_http_requests",
    "initialize_backend_metrics",
]

# Flag to track if we've already set up metrics
_METRICS_INITIALIZED = False

# Backend-specific metrics - only created if not already registered
CAN_TX_QUEUE_LENGTH: Gauge | None = None
CAN_TX_ENQUEUE_TOTAL: Counter | None = None
CAN_TX_ENQUEUE_LATENCY: Histogram | None = None
HTTP_REQUESTS: Counter | None = None
HTTP_LATENCY: Histogram | None = None


def _safe_create_metric(
    metric_type: type[MetricType], name: str, description: str, labelnames=None, registry=REGISTRY
) -> MetricType | None:
    """
    Safely create a Prometheus metric, checking for existing registration.

    Args:
        metric_type: The Prometheus metric class (Counter, Gauge, Histogram)
        name: Metric name
        description: Metric description
        labelnames: Optional list of label names
        registry: Prometheus registry to use

    Returns:
        The metric instance or None if already exists
    """
    try:
        # Check if metric already exists by trying to get it from registry
        for collector in registry._collector_to_names:
            # Use getattr with default to safely check for _name attribute
            collector_name = getattr(collector, "_name", None)
            if collector_name == name:
                logger.info(f"Metric '{name}' already exists, reusing existing metric")
                # Type assertion since we know this collector matches our MetricType
                return collector  # type: ignore[return-value]

        # Create new metric if it doesn't exist
        if labelnames:
            metric = metric_type(name, description, labelnames, registry=registry)
        else:
            metric = metric_type(name, description, registry=registry)

        logger.debug(f"Created new metric: {name}")
        return metric

    except ValueError as e:
        if "Duplicated timeseries" in str(e):
            logger.warning(f"Metric '{name}' already registered, skipping: {e}")
            return None
        else:
            raise


def initialize_backend_metrics():
    """
    Initialize backend-specific metrics with collision avoidance.
    """
    global _METRICS_INITIALIZED, CAN_TX_QUEUE_LENGTH, CAN_TX_ENQUEUE_TOTAL, CAN_TX_ENQUEUE_LATENCY
    global HTTP_REQUESTS, HTTP_LATENCY

    if _METRICS_INITIALIZED:
        logger.debug("Backend metrics already initialized")
        return

    logger.info("Initializing backend metrics with collision avoidance...")

    try:
        # Try to create metrics safely
        global CAN_TX_QUEUE_LENGTH, CAN_TX_ENQUEUE_TOTAL, CAN_TX_ENQUEUE_LATENCY
        global HTTP_REQUESTS, HTTP_LATENCY

        CAN_TX_QUEUE_LENGTH = _safe_create_metric(
            Gauge,
            "rvc2api_can_tx_queue_length",
            "Number of pending messages in the CAN transmit queue",
        )

        CAN_TX_ENQUEUE_TOTAL = _safe_create_metric(
            Counter,
            "rvc2api_can_tx_enqueue_total",
            "Total number of messages enqueued to the CAN transmit queue",
        )

        CAN_TX_ENQUEUE_LATENCY = _safe_create_metric(
            Histogram,
            "rvc2api_can_tx_enqueue_latency_seconds",
            "Latency for enqueueing CAN control messages",
        )

        HTTP_REQUESTS = _safe_create_metric(
            Counter,
            "rvc2api_http_requests_total",
            "Total HTTP requests processed",
            labelnames=["method", "endpoint", "status_code"],
        )

        HTTP_LATENCY = _safe_create_metric(
            Histogram,
            "rvc2api_http_request_duration_seconds",
            "HTTP request latency in seconds",
            labelnames=["method", "endpoint"],
        )

        _METRICS_INITIALIZED = True
        logger.info("Backend metrics initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize backend metrics: {e}")
        # Set to None if failed
        CAN_TX_QUEUE_LENGTH = None
        CAN_TX_ENQUEUE_TOTAL = None
        CAN_TX_ENQUEUE_LATENCY = None
        HTTP_REQUESTS = None
        HTTP_LATENCY = None


def get_can_tx_queue_length() -> Gauge:
    """Get the CAN TX queue length metric, initializing if needed."""
    if not _METRICS_INITIALIZED:
        initialize_backend_metrics()
    if CAN_TX_QUEUE_LENGTH is None:
        raise RuntimeError("CAN TX queue length metric failed to initialize")
    return CAN_TX_QUEUE_LENGTH


def get_can_tx_enqueue_total() -> Counter:
    """Get the CAN TX enqueue total metric, initializing if needed."""
    if not _METRICS_INITIALIZED:
        initialize_backend_metrics()
    if CAN_TX_ENQUEUE_TOTAL is None:
        raise RuntimeError("CAN TX enqueue total metric failed to initialize")
    return CAN_TX_ENQUEUE_TOTAL


def get_can_tx_enqueue_latency() -> Histogram:
    """Get the CAN TX enqueue latency metric, initializing if needed."""
    if not _METRICS_INITIALIZED:
        initialize_backend_metrics()
    if CAN_TX_ENQUEUE_LATENCY is None:
        raise RuntimeError("CAN TX enqueue latency metric failed to initialize")
    return CAN_TX_ENQUEUE_LATENCY


def get_http_requests() -> Counter:
    """Get the HTTP requests metric, initializing if needed."""
    if not _METRICS_INITIALIZED:
        initialize_backend_metrics()
    if HTTP_REQUESTS is None:
        raise RuntimeError("HTTP requests metric failed to initialize")
    return HTTP_REQUESTS


def get_http_latency() -> Histogram:
    """Get the HTTP latency metric, initializing if needed."""
    if not _METRICS_INITIALIZED:
        initialize_backend_metrics()
    if HTTP_LATENCY is None:
        raise RuntimeError("HTTP latency metric failed to initialize")
    return HTTP_LATENCY


# Initialize metrics when module is imported
initialize_backend_metrics()
