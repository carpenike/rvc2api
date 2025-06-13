"""
Performance Analytics Prometheus Metrics

Extends the existing backend metrics infrastructure with comprehensive
performance analytics metrics for multi-protocol CAN systems.

Follows the established Prometheus patterns with collision avoidance
and provides protocol-specific metrics for all supported protocols.
"""

import logging
from typing import TypeVar

from prometheus_client import REGISTRY, Counter, Gauge, Histogram

logger = logging.getLogger(__name__)

# Type variable for metric types
MetricType = TypeVar("MetricType", Counter, Gauge, Histogram)

# Flag to track if performance metrics are initialized
_PERFORMANCE_METRICS_INITIALIZED = False

# Protocol-specific message metrics
PROTOCOL_MESSAGE_RATE: Counter | None = None
PROTOCOL_MESSAGE_LATENCY: Histogram | None = None
PROTOCOL_MESSAGE_ERRORS: Counter | None = None

# Resource utilization metrics
RESOURCE_CPU_USAGE: Gauge | None = None
RESOURCE_MEMORY_USAGE: Gauge | None = None
RESOURCE_DISK_USAGE: Gauge | None = None
RESOURCE_NETWORK_USAGE: Gauge | None = None

# CAN interface specific metrics
CAN_INTERFACE_UTILIZATION: Gauge | None = None
CAN_INTERFACE_ERROR_RATE: Counter | None = None
CAN_INTERFACE_QUEUE_DEPTH: Gauge | None = None

# Performance analytics metrics
PERFORMANCE_BASELINE_DEVIATION: Gauge | None = None
PERFORMANCE_ANOMALY_DETECTED: Counter | None = None
PERFORMANCE_OPTIMIZATION_APPLIED: Counter | None = None

# Trend analysis metrics
TREND_ANALYSIS_SLOPE: Gauge | None = None
TREND_ANALYSIS_R_SQUARED: Gauge | None = None


def _safe_create_metric(
    metric_type: type[MetricType],
    name: str,
    description: str,
    labelnames=None,
    registry=REGISTRY,
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
                logger.info(f"Performance metric '{name}' already exists, reusing existing metric")
                # Type assertion since we know this collector matches our MetricType
                return collector  # type: ignore[return-value]

        # Create new metric if it doesn't exist
        if labelnames:
            metric = metric_type(name, description, labelnames, registry=registry)
        else:
            metric = metric_type(name, description, registry=registry)

        logger.debug(f"Created new performance metric: {name}")
        return metric

    except ValueError as e:
        if "Duplicated timeseries" in str(e):
            logger.warning(f"Performance metric '{name}' already registered, skipping: {e}")
            return None
        raise


def initialize_performance_metrics():
    """
    Initialize performance analytics metrics with collision avoidance.

    Creates comprehensive Prometheus metrics for:
    - Protocol-specific message rates, latencies, and errors
    - System resource utilization (CPU, memory, disk, network)
    - CAN interface utilization and performance
    - Performance analytics (baselines, anomalies, optimizations)
    - Trend analysis metrics
    """
    global _PERFORMANCE_METRICS_INITIALIZED
    global PROTOCOL_MESSAGE_RATE, PROTOCOL_MESSAGE_LATENCY, PROTOCOL_MESSAGE_ERRORS
    global RESOURCE_CPU_USAGE, RESOURCE_MEMORY_USAGE, RESOURCE_DISK_USAGE, RESOURCE_NETWORK_USAGE
    global CAN_INTERFACE_UTILIZATION, CAN_INTERFACE_ERROR_RATE, CAN_INTERFACE_QUEUE_DEPTH
    global \
        PERFORMANCE_BASELINE_DEVIATION, \
        PERFORMANCE_ANOMALY_DETECTED, \
        PERFORMANCE_OPTIMIZATION_APPLIED
    global TREND_ANALYSIS_SLOPE, TREND_ANALYSIS_R_SQUARED

    if _PERFORMANCE_METRICS_INITIALIZED:
        logger.debug("Performance analytics metrics already initialized")
        return

    logger.info("Initializing performance analytics metrics with collision avoidance...")

    try:
        # Protocol-specific message metrics
        PROTOCOL_MESSAGE_RATE = _safe_create_metric(
            Counter,
            "coachiq_protocol_messages_total",
            "Total messages processed per protocol",
            labelnames=["protocol", "direction", "status"],
        )

        PROTOCOL_MESSAGE_LATENCY = _safe_create_metric(
            Histogram,
            "coachiq_protocol_message_latency_seconds",
            "Message processing latency per protocol",
            labelnames=["protocol", "operation"],
        )

        PROTOCOL_MESSAGE_ERRORS = _safe_create_metric(
            Counter,
            "coachiq_protocol_errors_total",
            "Total errors per protocol",
            labelnames=["protocol", "error_type"],
        )

        # System resource utilization metrics
        RESOURCE_CPU_USAGE = _safe_create_metric(
            Gauge,
            "coachiq_cpu_usage_percent",
            "CPU usage percentage",
            labelnames=["core"],
        )

        RESOURCE_MEMORY_USAGE = _safe_create_metric(
            Gauge,
            "coachiq_memory_usage_bytes",
            "Memory usage in bytes",
            labelnames=["type"],
        )

        RESOURCE_DISK_USAGE = _safe_create_metric(
            Gauge,
            "coachiq_disk_usage_bytes",
            "Disk usage in bytes",
            labelnames=["mount_point", "type"],
        )

        RESOURCE_NETWORK_USAGE = _safe_create_metric(
            Gauge,
            "coachiq_network_usage_bytes_total",
            "Network usage in bytes",
            labelnames=["interface", "direction"],
        )

        # CAN interface specific metrics
        CAN_INTERFACE_UTILIZATION = _safe_create_metric(
            Gauge,
            "coachiq_can_interface_utilization_percent",
            "CAN interface utilization percentage",
            labelnames=["interface", "protocol"],
        )

        CAN_INTERFACE_ERROR_RATE = _safe_create_metric(
            Counter,
            "coachiq_can_interface_errors_total",
            "CAN interface errors",
            labelnames=["interface", "error_type"],
        )

        CAN_INTERFACE_QUEUE_DEPTH = _safe_create_metric(
            Gauge,
            "coachiq_can_interface_queue_depth",
            "CAN interface queue depth",
            labelnames=["interface", "direction"],
        )

        # Performance analytics metrics
        PERFORMANCE_BASELINE_DEVIATION = _safe_create_metric(
            Gauge,
            "coachiq_performance_baseline_deviation",
            "Deviation from performance baseline",
            labelnames=["metric_type", "protocol", "severity"],
        )

        PERFORMANCE_ANOMALY_DETECTED = _safe_create_metric(
            Counter,
            "coachiq_performance_anomalies_total",
            "Performance anomalies detected",
            labelnames=["anomaly_type", "protocol", "severity"],
        )

        PERFORMANCE_OPTIMIZATION_APPLIED = _safe_create_metric(
            Counter,
            "coachiq_performance_optimizations_total",
            "Performance optimizations applied",
            labelnames=["optimization_type", "protocol"],
        )

        # Trend analysis metrics
        TREND_ANALYSIS_SLOPE = _safe_create_metric(
            Gauge,
            "coachiq_trend_analysis_slope",
            "Trend analysis slope coefficient",
            labelnames=["metric_type", "protocol", "time_window"],
        )

        TREND_ANALYSIS_R_SQUARED = _safe_create_metric(
            Gauge,
            "coachiq_trend_analysis_r_squared",
            "Trend analysis R-squared value",
            labelnames=["metric_type", "protocol", "time_window"],
        )

        _PERFORMANCE_METRICS_INITIALIZED = True
        logger.info("Performance analytics metrics initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize performance analytics metrics: {e}")
        # Set all metrics to None if initialization failed
        PROTOCOL_MESSAGE_RATE = None
        PROTOCOL_MESSAGE_LATENCY = None
        PROTOCOL_MESSAGE_ERRORS = None
        RESOURCE_CPU_USAGE = None
        RESOURCE_MEMORY_USAGE = None
        RESOURCE_DISK_USAGE = None
        RESOURCE_NETWORK_USAGE = None
        CAN_INTERFACE_UTILIZATION = None
        CAN_INTERFACE_ERROR_RATE = None
        CAN_INTERFACE_QUEUE_DEPTH = None
        PERFORMANCE_BASELINE_DEVIATION = None
        PERFORMANCE_ANOMALY_DETECTED = None
        PERFORMANCE_OPTIMIZATION_APPLIED = None
        TREND_ANALYSIS_SLOPE = None
        TREND_ANALYSIS_R_SQUARED = None


# Getter functions for metrics (following backend metrics pattern)


def get_protocol_message_rate() -> Counter:
    """Get the protocol message rate metric, initializing if needed."""
    if not _PERFORMANCE_METRICS_INITIALIZED:
        initialize_performance_metrics()
    if PROTOCOL_MESSAGE_RATE is None:
        msg = "Protocol message rate metric failed to initialize"
        raise RuntimeError(msg)
    return PROTOCOL_MESSAGE_RATE


def get_protocol_latency() -> Histogram:
    """Get the protocol latency metric, initializing if needed."""
    if not _PERFORMANCE_METRICS_INITIALIZED:
        initialize_performance_metrics()
    if PROTOCOL_MESSAGE_LATENCY is None:
        msg = "Protocol latency metric failed to initialize"
        raise RuntimeError(msg)
    return PROTOCOL_MESSAGE_LATENCY


def get_protocol_errors() -> Counter:
    """Get the protocol errors metric, initializing if needed."""
    if not _PERFORMANCE_METRICS_INITIALIZED:
        initialize_performance_metrics()
    if PROTOCOL_MESSAGE_ERRORS is None:
        msg = "Protocol errors metric failed to initialize"
        raise RuntimeError(msg)
    return PROTOCOL_MESSAGE_ERRORS


def get_resource_utilization() -> Gauge:
    """Get the resource utilization metric, initializing if needed."""
    if not _PERFORMANCE_METRICS_INITIALIZED:
        initialize_performance_metrics()
    if RESOURCE_CPU_USAGE is None:
        msg = "Resource utilization metric failed to initialize"
        raise RuntimeError(msg)
    return RESOURCE_CPU_USAGE


def get_can_interface_utilization() -> Gauge:
    """Get the CAN interface utilization metric, initializing if needed."""
    if not _PERFORMANCE_METRICS_INITIALIZED:
        initialize_performance_metrics()
    if CAN_INTERFACE_UTILIZATION is None:
        msg = "CAN interface utilization metric failed to initialize"
        raise RuntimeError(msg)
    return CAN_INTERFACE_UTILIZATION


def get_baseline_deviation() -> Gauge:
    """Get the baseline deviation metric, initializing if needed."""
    if not _PERFORMANCE_METRICS_INITIALIZED:
        initialize_performance_metrics()
    if PERFORMANCE_BASELINE_DEVIATION is None:
        msg = "Baseline deviation metric failed to initialize"
        raise RuntimeError(msg)
    return PERFORMANCE_BASELINE_DEVIATION


def get_anomaly_detection() -> Counter:
    """Get the anomaly detection metric, initializing if needed."""
    if not _PERFORMANCE_METRICS_INITIALIZED:
        initialize_performance_metrics()
    if PERFORMANCE_ANOMALY_DETECTED is None:
        msg = "Anomaly detection metric failed to initialize"
        raise RuntimeError(msg)
    return PERFORMANCE_ANOMALY_DETECTED


def get_optimization_applied() -> Counter:
    """Get the optimization applied metric, initializing if needed."""
    if not _PERFORMANCE_METRICS_INITIALIZED:
        initialize_performance_metrics()
    if PERFORMANCE_OPTIMIZATION_APPLIED is None:
        msg = "Optimization applied metric failed to initialize"
        raise RuntimeError(msg)
    return PERFORMANCE_OPTIMIZATION_APPLIED


def get_trend_analysis_slope() -> Gauge:
    """Get the trend analysis slope metric, initializing if needed."""
    if not _PERFORMANCE_METRICS_INITIALIZED:
        initialize_performance_metrics()
    if TREND_ANALYSIS_SLOPE is None:
        msg = "Trend analysis slope metric failed to initialize"
        raise RuntimeError(msg)
    return TREND_ANALYSIS_SLOPE


def get_trend_analysis_r_squared() -> Gauge:
    """Get the trend analysis R-squared metric, initializing if needed."""
    if not _PERFORMANCE_METRICS_INITIALIZED:
        initialize_performance_metrics()
    if TREND_ANALYSIS_R_SQUARED is None:
        msg = "Trend analysis R-squared metric failed to initialize"
        raise RuntimeError(msg)
    return TREND_ANALYSIS_R_SQUARED


# Convenience functions for recording metrics


def record_protocol_message(protocol: str, direction: str, status: str = "success") -> None:
    """Record a protocol message with the specified labels."""
    try:
        metric = get_protocol_message_rate()
        metric.labels(protocol=protocol, direction=direction, status=status).inc()
    except Exception as e:
        logger.error(f"Failed to record protocol message metric: {e}")


def record_protocol_latency(protocol: str, operation: str, latency: float) -> None:
    """Record protocol operation latency."""
    try:
        metric = get_protocol_latency()
        metric.labels(protocol=protocol, operation=operation).observe(latency)
    except Exception as e:
        logger.error(f"Failed to record protocol latency metric: {e}")


def record_protocol_error(protocol: str, error_type: str) -> None:
    """Record a protocol error."""
    try:
        metric = get_protocol_errors()
        metric.labels(protocol=protocol, error_type=error_type).inc()
    except Exception as e:
        logger.error(f"Failed to record protocol error metric: {e}")


def record_resource_usage(resource_type: str, usage: float, **labels) -> None:
    """Record resource usage metric."""
    try:
        if resource_type == "cpu":
            metric = RESOURCE_CPU_USAGE
            if metric:
                core = labels.get("core", "total")
                metric.labels(core=core).set(usage)
        elif resource_type == "memory":
            metric = RESOURCE_MEMORY_USAGE
            if metric:
                mem_type = labels.get("type", "used")
                metric.labels(type=mem_type).set(usage)
        elif resource_type == "disk":
            metric = RESOURCE_DISK_USAGE
            if metric:
                mount_point = labels.get("mount_point", "/")
                disk_type = labels.get("type", "used")
                metric.labels(mount_point=mount_point, type=disk_type).set(usage)
        elif resource_type == "network":
            metric = RESOURCE_NETWORK_USAGE
            if metric:
                interface = labels.get("interface", "total")
                direction = labels.get("direction", "total")
                metric.labels(interface=interface, direction=direction).set(usage)
    except Exception as e:
        logger.error(f"Failed to record resource usage metric: {e}")


def record_can_interface_utilization(interface: str, protocol: str, utilization: float) -> None:
    """Record CAN interface utilization."""
    try:
        metric = get_can_interface_utilization()
        metric.labels(interface=interface, protocol=protocol).set(utilization)
    except Exception as e:
        logger.error(f"Failed to record CAN interface utilization metric: {e}")


def record_baseline_deviation(
    metric_type: str, protocol: str, severity: str, deviation: float
) -> None:
    """Record baseline deviation."""
    try:
        metric = get_baseline_deviation()
        metric.labels(metric_type=metric_type, protocol=protocol, severity=severity).set(deviation)
    except Exception as e:
        logger.error(f"Failed to record baseline deviation metric: {e}")


def record_anomaly(anomaly_type: str, protocol: str, severity: str) -> None:
    """Record an anomaly detection."""
    try:
        metric = get_anomaly_detection()
        metric.labels(anomaly_type=anomaly_type, protocol=protocol, severity=severity).inc()
    except Exception as e:
        logger.error(f"Failed to record anomaly metric: {e}")


def record_optimization(optimization_type: str, protocol: str) -> None:
    """Record an applied optimization."""
    try:
        metric = get_optimization_applied()
        metric.labels(optimization_type=optimization_type, protocol=protocol).inc()
    except Exception as e:
        logger.error(f"Failed to record optimization metric: {e}")


def record_trend_analysis(
    metric_type: str, protocol: str, time_window: str, slope: float, r_squared: float
) -> None:
    """Record trend analysis results."""
    try:
        slope_metric = get_trend_analysis_slope()
        r_squared_metric = get_trend_analysis_r_squared()

        slope_metric.labels(
            metric_type=metric_type, protocol=protocol, time_window=time_window
        ).set(slope)
        r_squared_metric.labels(
            metric_type=metric_type, protocol=protocol, time_window=time_window
        ).set(r_squared)
    except Exception as e:
        logger.error(f"Failed to record trend analysis metrics: {e}")


# Initialize metrics when module is imported (following backend pattern)
initialize_performance_metrics()
