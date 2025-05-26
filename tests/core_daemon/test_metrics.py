"""
Tests for the Prometheus metrics defined in `core_daemon.metrics`.

This module verifies:
- The correct instantiation type (Counter, Gauge, Histogram) of each metric.
- The presence and correctness of labels for labeled metrics.
- The absence of labels for unlabeled metrics.
"""

# Import the metrics from the module to be tested
from core_daemon import metrics
from prometheus_client import Counter, Gauge, Histogram


def test_metric_definitions():
    """Test that all defined Prometheus metrics are instantiated with the correct types.

    Ensures that counters are `Counter`, gauges are `Gauge`, and histograms are `Histogram`.
    """
    assert isinstance(metrics.FRAME_COUNTER, Counter), "FRAME_COUNTER should be a Counter"
    assert isinstance(metrics.DECODE_ERRORS, Counter), "DECODE_ERRORS should be a Counter"
    assert isinstance(metrics.LOOKUP_MISSES, Counter), "LOOKUP_MISSES should be a Counter"
    assert isinstance(metrics.SUCCESSFUL_DECODES, Counter), "SUCCESSFUL_DECODES should be a Counter"
    assert isinstance(metrics.WS_CLIENTS, Gauge), "WS_CLIENTS should be a Gauge"
    assert isinstance(metrics.WS_MESSAGES, Counter), "WS_MESSAGES should be a Counter"
    assert isinstance(metrics.ENTITY_COUNT, Gauge), "ENTITY_COUNT should be a Gauge"
    assert isinstance(metrics.HISTORY_SIZE_GAUGE, Gauge), "HISTORY_SIZE_GAUGE should be a Gauge"
    assert isinstance(metrics.FRAME_LATENCY, Histogram), "FRAME_LATENCY should be a Histogram"
    assert isinstance(metrics.HTTP_REQUESTS, Counter), "HTTP_REQUESTS should be a Counter"
    assert isinstance(metrics.HTTP_LATENCY, Histogram), "HTTP_LATENCY should be a Histogram"
    assert isinstance(
        metrics.GENERATOR_COMMAND_COUNTER, Counter
    ), "GENERATOR_COMMAND_COUNTER should be a Counter"
    assert isinstance(
        metrics.GENERATOR_STATUS_1_COUNTER, Counter
    ), "GENERATOR_STATUS_1_COUNTER should be a Counter"
    assert isinstance(
        metrics.GENERATOR_STATUS_2_COUNTER, Counter
    ), "GENERATOR_STATUS_2_COUNTER should be a Counter"
    assert isinstance(
        metrics.GENERATOR_DEMAND_COMMAND_COUNTER, Counter
    ), "GENERATOR_DEMAND_COMMAND_COUNTER should be a Counter"
    assert isinstance(metrics.PGN_USAGE_COUNTER, Counter), "PGN_USAGE_COUNTER should be a Counter"
    assert isinstance(metrics.INST_USAGE_COUNTER, Counter), "INST_USAGE_COUNTER should be a Counter"
    assert isinstance(metrics.DGN_TYPE_GAUGE, Gauge), "DGN_TYPE_GAUGE should be a Gauge"
    assert isinstance(metrics.CAN_TX_QUEUE_LENGTH, Gauge), "CAN_TX_QUEUE_LENGTH should be a Gauge"
    assert isinstance(
        metrics.CAN_TX_ENQUEUE_TOTAL, Counter
    ), "CAN_TX_ENQUEUE_TOTAL should be a Counter"
    assert isinstance(
        metrics.CAN_TX_ENQUEUE_LATENCY, Histogram
    ), "CAN_TX_ENQUEUE_LATENCY should be a Histogram"


def test_metric_labels():
    """Test that Prometheus metrics are defined with correct labels.

    Verifies that metrics intended to be labeled have the correct `_labelnames`
    attribute and that metrics intended to be unlabeled do not have this attribute
    or it is empty.
    """
    # For Counters and Gauges, labelnames are stored in _labelnames
    # For Histograms, they are also in _labelnames
    assert (
        hasattr(metrics.HISTORY_SIZE_GAUGE, "_labelnames")
        and "entity_id" in metrics.HISTORY_SIZE_GAUGE._labelnames
    ), "HISTORY_SIZE_GAUGE should have 'entity_id' label"
    assert hasattr(metrics.HTTP_REQUESTS, "_labelnames") and all(
        label in metrics.HTTP_REQUESTS._labelnames
        for label in ["method", "endpoint", "status_code"]
    ), "HTTP_REQUESTS should have 'method', 'endpoint', and 'status_code' labels"
    assert hasattr(metrics.HTTP_LATENCY, "_labelnames") and all(
        label in metrics.HTTP_LATENCY._labelnames for label in ["method", "endpoint"]
    ), "HTTP_LATENCY should have 'method' and 'endpoint' labels"
    assert (
        hasattr(metrics.PGN_USAGE_COUNTER, "_labelnames")
        and "pgn" in metrics.PGN_USAGE_COUNTER._labelnames
    ), "PGN_USAGE_COUNTER should have 'pgn' label"
    assert hasattr(metrics.INST_USAGE_COUNTER, "_labelnames") and all(
        label in metrics.INST_USAGE_COUNTER._labelnames for label in ["dgn", "instance"]
    ), "INST_USAGE_COUNTER should have 'dgn' and 'instance' labels"
    assert (
        hasattr(metrics.DGN_TYPE_GAUGE, "_labelnames")
        and "device_type" in metrics.DGN_TYPE_GAUGE._labelnames
    ), "DGN_TYPE_GAUGE should have 'device_type' label"

    # Check that metrics without labels don't have _labelnames or it's empty
    assert not metrics.FRAME_COUNTER._labelnames, "FRAME_COUNTER should not have labels"
    assert not metrics.DECODE_ERRORS._labelnames, "DECODE_ERRORS should not have labels"
    assert not metrics.LOOKUP_MISSES._labelnames, "LOOKUP_MISSES should not have labels"
    assert not metrics.SUCCESSFUL_DECODES._labelnames, "SUCCESSFUL_DECODES should not have labels"
    assert not metrics.WS_CLIENTS._labelnames, "WS_CLIENTS should not have labels"
    assert not metrics.WS_MESSAGES._labelnames, "WS_MESSAGES should not have labels"
    assert not metrics.ENTITY_COUNT._labelnames, "ENTITY_COUNT should not have labels"
    assert (
        not metrics.FRAME_LATENCY._labelnames
    ), "FRAME_LATENCY should not have labels (histograms handle labels differently)"
    assert (
        not metrics.GENERATOR_COMMAND_COUNTER._labelnames
    ), "GENERATOR_COMMAND_COUNTER should not have labels"
    assert (
        not metrics.GENERATOR_STATUS_1_COUNTER._labelnames
    ), "GENERATOR_STATUS_1_COUNTER should not have labels"
    assert (
        not metrics.GENERATOR_STATUS_2_COUNTER._labelnames
    ), "GENERATOR_STATUS_2_COUNTER should not have labels"
    assert (
        not metrics.GENERATOR_DEMAND_COMMAND_COUNTER._labelnames
    ), "GENERATOR_DEMAND_COMMAND_COUNTER should not have labels"
    assert not metrics.CAN_TX_QUEUE_LENGTH._labelnames, "CAN_TX_QUEUE_LENGTH should not have labels"
    assert (
        not metrics.CAN_TX_ENQUEUE_TOTAL._labelnames
    ), "CAN_TX_ENQUEUE_TOTAL should not have labels"
    assert (
        not metrics.CAN_TX_ENQUEUE_LATENCY._labelnames
    ), "CAN_TX_ENQUEUE_LATENCY should not have labels (histograms handle labels differently)"
