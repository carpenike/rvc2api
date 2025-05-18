"""
Defines Prometheus metrics for monitoring the rvc2api application.

This module centralizes the definition of all Counter, Gauge, and Histogram
metrics used to track various aspects of the application's performance and behavior,
including CAN frame processing, API requests, WebSocket connections, and system health.
"""

from prometheus_client import Counter, Gauge, Histogram

# Define Prometheus metrics
FRAME_COUNTER = Counter("rvc2api_frames_total", "Total CAN frames received")
DECODE_ERRORS = Counter("rvc2api_decode_errors_total", "Total decode errors")
LOOKUP_MISSES = Counter("rvc2api_lookup_misses_total", "Total device-lookup misses")
SUCCESSFUL_DECODES = Counter("rvc2api_successful_decodes_total", "Total successful decodes")
WS_CLIENTS = Gauge("rvc2api_ws_clients", "Active WebSocket clients")
WS_MESSAGES = Counter("rvc2api_ws_messages_total", "Total WebSocket messages sent")
ENTITY_COUNT = Gauge("rvc2api_entity_count", "Number of entities in current state")
HISTORY_SIZE_GAUGE = Gauge(
    "rvc2api_history_size", "Number of stored historical samples per entity", ["entity_id"]
)
FRAME_LATENCY = Histogram(
    "rvc2api_frame_latency_seconds", "Time spent decoding & dispatching frames"
)
HTTP_REQUESTS = Counter(
    "rvc2api_http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"]
)
HTTP_LATENCY = Histogram(
    "rvc2api_http_request_latency_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)
GENERATOR_COMMAND_COUNTER = Counter(
    "rvc2api_generator_command_total", "Total GENERATOR_COMMAND messages received"
)
GENERATOR_STATUS_1_COUNTER = Counter(
    "rvc2api_generator_status_1_total", "Total GENERATOR_STATUS_1 messages received"
)
GENERATOR_STATUS_2_COUNTER = Counter(
    "rvc2api_generator_status_2_total", "Total GENERATOR_STATUS_2 messages received"
)
GENERATOR_DEMAND_COMMAND_COUNTER = Counter(
    "rvc2api_generator_demand_command_total", "Total GENERATOR_DEMAND_COMMAND messages received"
)
PGN_USAGE_COUNTER = Counter("rvc2api_pgn_usage_total", "PGN usage by frame count", ["pgn"])
INST_USAGE_COUNTER = Counter(
    "rvc2api_instance_usage_total", "Instance usage by DGN", ["dgn", "instance"]
)
DGN_TYPE_GAUGE = Gauge(
    "rvc2api_dgn_type_present", "Number of DGNs seen per type/class", ["device_type"]
)
CAN_TX_QUEUE_LENGTH = Gauge(
    "rvc2api_can_tx_queue_length", "Number of pending messages in the CAN transmit queue"
)
CAN_TX_ENQUEUE_TOTAL = Counter(
    "rvc2api_can_tx_enqueue_total", "Total number of messages enqueued to the CAN transmit queue"
)
CAN_TX_ENQUEUE_LATENCY = Histogram(
    "rvc2api_can_tx_enqueue_latency_seconds", "Latency for enqueueing CAN control messages"
)
