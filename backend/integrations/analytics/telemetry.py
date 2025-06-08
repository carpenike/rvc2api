"""
Telemetry Collector

Real-time performance data collection from all protocols and system resources.
Provides comprehensive telemetry gathering with configurable intervals and targets.
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from typing import Any

import psutil

from backend.integrations.analytics.config import PerformanceAnalyticsSettings
from backend.integrations.analytics.models import (
    MetricType,
    PerformanceMetric,
    ResourceType,
    ResourceUtilization,
)

logger = logging.getLogger(__name__)


class TelemetryCollector:
    """
    Real-time telemetry data collector for comprehensive performance monitoring.

    Collects performance data from:
    - Protocol message processing (RV-C, J1939, Firefly, Spartan K2)
    - System resources (CPU, memory, network)
    - CAN interface utilization
    - API and WebSocket performance
    """

    def __init__(self, settings: PerformanceAnalyticsSettings):
        """Initialize the telemetry collector."""
        self.settings = settings

        # Data storage
        self._metrics: dict[MetricType, deque] = defaultdict(lambda: deque(maxlen=10000))
        self._resource_data: dict[ResourceType, deque] = defaultdict(lambda: deque(maxlen=1000))

        # Protocol-specific counters
        self._protocol_counters = {
            "rvc": {"messages": 0, "processing_time": 0.0, "last_reset": time.time()},
            "j1939": {"messages": 0, "processing_time": 0.0, "last_reset": time.time()},
            "firefly": {"messages": 0, "processing_time": 0.0, "last_reset": time.time()},
            "spartan_k2": {"messages": 0, "processing_time": 0.0, "last_reset": time.time()},
        }

        # System resource tracking
        self._resource_history: dict[ResourceType, list[tuple[float, float]]] = defaultdict(list)

        # Background tasks
        self._collection_tasks: list[asyncio.Task] = []
        self._running = False

        # Performance targets
        self._performance_targets = self._initialize_performance_targets()

        # Collection statistics
        self._collection_stats = {
            "collections_performed": 0,
            "metrics_collected": 0,
            "collection_time_ms": 0.0,
            "last_collection": 0.0,
        }

        logger.info("Telemetry collector initialized")

    def _initialize_performance_targets(self) -> dict[MetricType, tuple[float, float]]:
        """Initialize performance targets from configuration."""
        return {
            # Message processing targets (optimal, acceptable)
            MetricType.RVC_THROUGHPUT: (
                self.settings.target_rvc_message_rate,
                self.settings.target_rvc_message_rate * 0.8,
            ),
            MetricType.J1939_THROUGHPUT: (
                self.settings.target_j1939_message_rate,
                self.settings.target_j1939_message_rate * 0.8,
            ),
            MetricType.API_RESPONSE_TIME: (
                self.settings.target_api_response_time_ms,
                self.settings.target_api_response_time_ms * 1.5,
            ),
            MetricType.WEBSOCKET_LATENCY: (
                self.settings.target_websocket_latency_ms,
                self.settings.target_websocket_latency_ms * 2.0,
            ),
            # Resource utilization targets
            MetricType.CPU_USAGE: (50.0, self.settings.cpu_warning_threshold_percent),
            MetricType.MEMORY_USAGE: (50.0, self.settings.memory_warning_threshold_percent),
            MetricType.CAN_BUS_LOAD: (30.0, self.settings.can_bus_load_warning_threshold_percent),
            # Processing latency targets
            MetricType.PROCESSING_LATENCY: (1.0, 5.0),  # milliseconds
            MetricType.DECODE_TIME: (0.5, 2.0),  # milliseconds
            MetricType.ENCODE_TIME: (0.5, 2.0),  # milliseconds
        }

    async def startup(self) -> None:
        """Start telemetry collection tasks."""
        if not self.settings.enabled or not self.settings.enable_telemetry_collection:
            logger.info("Telemetry collection disabled")
            return

        self._running = True

        # Start performance data collection
        if self.settings.enable_protocol_telemetry:
            telemetry_task = asyncio.create_task(self._telemetry_collection_loop())
            self._collection_tasks.append(telemetry_task)

        # Start resource monitoring
        if self.settings.enable_resource_monitoring:
            resource_task = asyncio.create_task(self._resource_monitoring_loop())
            self._collection_tasks.append(resource_task)

        # Start CAN interface monitoring
        if self.settings.enable_can_interface_monitoring:
            can_task = asyncio.create_task(self._can_interface_monitoring_loop())
            self._collection_tasks.append(can_task)

        logger.info(f"Telemetry collection started with {len(self._collection_tasks)} tasks")

    async def shutdown(self) -> None:
        """Shutdown telemetry collection."""
        self._running = False

        # Cancel all collection tasks
        for task in self._collection_tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        if self._collection_tasks:
            await asyncio.gather(*self._collection_tasks, return_exceptions=True)

        self._collection_tasks.clear()
        logger.info("Telemetry collection shutdown complete")

    def record_protocol_message(
        self,
        protocol: str,
        processing_time_ms: float,
        message_size: int = 0,
        interface: str | None = None,
    ) -> None:
        """
        Record protocol message processing performance.

        Args:
            protocol: Protocol name (rvc, j1939, firefly, spartan_k2)
            processing_time_ms: Time taken to process message
            message_size: Message size in bytes
            interface: CAN interface name
        """
        if protocol.lower() in self._protocol_counters:
            counter = self._protocol_counters[protocol.lower()]
            counter["messages"] += 1
            counter["processing_time"] += processing_time_ms

            # Record processing time metric
            metric = PerformanceMetric(
                metric_type=MetricType.PROCESSING_LATENCY,
                value=processing_time_ms,
                protocol=protocol,
                interface=interface,
                optimal_range=self._performance_targets.get(MetricType.PROCESSING_LATENCY),
                unit="ms",
            )
            self._metrics[MetricType.PROCESSING_LATENCY].append(metric)

            # Record decode time (estimated as portion of processing time)
            decode_time = processing_time_ms * 0.7  # Estimate decode as 70% of processing
            decode_metric = PerformanceMetric(
                metric_type=MetricType.DECODE_TIME,
                value=decode_time,
                protocol=protocol,
                interface=interface,
                optimal_range=self._performance_targets.get(MetricType.DECODE_TIME),
                unit="ms",
            )
            self._metrics[MetricType.DECODE_TIME].append(decode_metric)

    def record_api_request(
        self, endpoint: str, response_time_ms: float, status_code: int = 200
    ) -> None:
        """
        Record API request performance.

        Args:
            endpoint: API endpoint
            response_time_ms: Response time in milliseconds
            status_code: HTTP status code
        """
        metric = PerformanceMetric(
            metric_type=MetricType.API_RESPONSE_TIME,
            value=response_time_ms,
            component=endpoint,
            optimal_range=self._performance_targets.get(MetricType.API_RESPONSE_TIME),
            unit="ms",
            metadata={"status_code": status_code},
        )
        self._metrics[MetricType.API_RESPONSE_TIME].append(metric)

    def record_websocket_latency(self, latency_ms: float, connection_id: str | None = None) -> None:
        """
        Record WebSocket latency.

        Args:
            latency_ms: WebSocket message latency
            connection_id: Connection identifier
        """
        metric = PerformanceMetric(
            metric_type=MetricType.WEBSOCKET_LATENCY,
            value=latency_ms,
            component=connection_id,
            optimal_range=self._performance_targets.get(MetricType.WEBSOCKET_LATENCY),
            unit="ms",
        )
        self._metrics[MetricType.WEBSOCKET_LATENCY].append(metric)

    def record_can_interface_load(
        self, interface: str, load_percent: float, message_rate: float
    ) -> None:
        """
        Record CAN interface load.

        Args:
            interface: CAN interface name
            load_percent: Bus load percentage
            message_rate: Messages per second
        """
        load_metric = PerformanceMetric(
            metric_type=MetricType.CAN_BUS_LOAD,
            value=load_percent,
            interface=interface,
            optimal_range=self._performance_targets.get(MetricType.CAN_BUS_LOAD),
            unit="%",
        )
        self._metrics[MetricType.CAN_BUS_LOAD].append(load_metric)

        rate_metric = PerformanceMetric(
            metric_type=MetricType.MESSAGE_RATE,
            value=message_rate,
            interface=interface,
            unit="msg/s",
        )
        self._metrics[MetricType.MESSAGE_RATE].append(rate_metric)

    def get_current_metrics(
        self, metric_type: MetricType | None = None, time_window_seconds: float = 60.0
    ) -> list[PerformanceMetric]:
        """
        Get current performance metrics.

        Args:
            metric_type: Specific metric type to retrieve
            time_window_seconds: Time window for metrics

        Returns:
            List of performance metrics
        """
        current_time = time.time()
        cutoff_time = current_time - time_window_seconds

        if metric_type:
            metrics = self._metrics.get(metric_type, deque())
            return [m for m in metrics if m.timestamp >= cutoff_time]

        all_metrics = []
        for metrics_deque in self._metrics.values():
            all_metrics.extend([m for m in metrics_deque if m.timestamp >= cutoff_time])

        return sorted(all_metrics, key=lambda m: m.timestamp)

    def get_resource_utilization(self) -> dict[ResourceType, ResourceUtilization]:
        """Get current resource utilization."""
        utilization = {}

        try:
            # CPU utilization
            cpu_percent = psutil.cpu_percent(interval=0.1)
            utilization[ResourceType.CPU] = ResourceUtilization(
                resource_type=ResourceType.CPU,
                current_usage=cpu_percent,
                usage_percent=cpu_percent,
                capacity=100.0,
                warning_threshold=self.settings.cpu_warning_threshold_percent,
                critical_threshold=self.settings.cpu_critical_threshold_percent,
                unit="%",
            )

            # Memory utilization
            memory = psutil.virtual_memory()
            memory_mb = memory.used / (1024 * 1024)
            memory_capacity_mb = memory.total / (1024 * 1024)
            utilization[ResourceType.MEMORY] = ResourceUtilization(
                resource_type=ResourceType.MEMORY,
                current_usage=memory_mb,
                usage_percent=memory.percent,
                capacity=memory_capacity_mb,
                warning_threshold=self.settings.memory_warning_threshold_percent,
                critical_threshold=self.settings.memory_critical_threshold_percent,
                unit="MB",
            )

            # Network utilization (basic)
            net_io = psutil.net_io_counters()
            if hasattr(net_io, "bytes_sent") and hasattr(net_io, "bytes_recv"):
                # Calculate network utilization as a basic estimate
                network_mbps = (
                    (net_io.bytes_sent + net_io.bytes_recv) / (1024 * 1024) / 60
                )  # Rough estimate
                utilization[ResourceType.NETWORK] = ResourceUtilization(
                    resource_type=ResourceType.NETWORK,
                    current_usage=network_mbps,
                    usage_percent=min(network_mbps / 10.0 * 100, 100.0),  # Assume 10 Mbps capacity
                    capacity=10.0,  # Assume 10 Mbps capacity
                    unit="Mbps",
                )

        except Exception as e:
            logger.error(f"Error collecting resource utilization: {e}")

        return utilization

    def get_protocol_throughput(self) -> dict[str, float]:
        """Get current protocol throughput in messages per second."""
        current_time = time.time()
        throughput = {}

        for protocol, counter in self._protocol_counters.items():
            time_elapsed = current_time - counter["last_reset"]
            if time_elapsed > 0:
                throughput[protocol] = counter["messages"] / time_elapsed
            else:
                throughput[protocol] = 0.0

        return throughput

    def get_collection_statistics(self) -> dict[str, Any]:
        """Get telemetry collection statistics."""
        return {
            "enabled": self.settings.enabled and self.settings.enable_telemetry_collection,
            "running": self._running,
            "active_tasks": len([t for t in self._collection_tasks if not t.done()]),
            "collection_stats": self._collection_stats.copy(),
            "metric_counts": {
                metric_type.value: len(metrics) for metric_type, metrics in self._metrics.items()
            },
            "protocol_counters": {
                protocol: {
                    "messages": data["messages"],
                    "avg_processing_time": data["processing_time"] / max(data["messages"], 1),
                }
                for protocol, data in self._protocol_counters.items()
            },
        }

    def reset_protocol_counters(self) -> None:
        """Reset protocol message counters."""
        current_time = time.time()
        for counter in self._protocol_counters.values():
            counter["messages"] = 0
            counter["processing_time"] = 0.0
            counter["last_reset"] = current_time

    # Background collection tasks

    async def _telemetry_collection_loop(self) -> None:
        """Background task for telemetry data collection."""
        while self._running:
            try:
                start_time = time.perf_counter()

                # Collect protocol throughput
                await self._collect_protocol_throughput()

                # Update collection statistics
                collection_time = (time.perf_counter() - start_time) * 1000
                self._collection_stats["collections_performed"] += 1
                self._collection_stats["collection_time_ms"] += collection_time
                self._collection_stats["last_collection"] = time.time()

                await asyncio.sleep(self.settings.telemetry_collection_interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in telemetry collection: {e}")
                await asyncio.sleep(5.0)

    async def _resource_monitoring_loop(self) -> None:
        """Background task for resource monitoring."""
        while self._running:
            try:
                # Collect system resource metrics
                await self._collect_system_resources()

                await asyncio.sleep(self.settings.resource_monitoring_interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
                await asyncio.sleep(10.0)

    async def _can_interface_monitoring_loop(self) -> None:
        """Background task for CAN interface monitoring."""
        while self._running:
            try:
                # Collect CAN interface metrics
                await self._collect_can_interface_metrics()

                await asyncio.sleep(self.settings.resource_monitoring_interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in CAN interface monitoring: {e}")
                await asyncio.sleep(10.0)

    async def _collect_protocol_throughput(self) -> None:
        """Collect protocol throughput metrics."""
        throughput = self.get_protocol_throughput()

        for protocol, rate in throughput.items():
            if protocol == "rvc":
                metric_type = MetricType.RVC_THROUGHPUT
            elif protocol == "j1939":
                metric_type = MetricType.J1939_THROUGHPUT
            elif protocol == "firefly":
                metric_type = MetricType.FIREFLY_THROUGHPUT
            elif protocol == "spartan_k2":
                metric_type = MetricType.SPARTAN_THROUGHPUT
            else:
                continue

            metric = PerformanceMetric(
                metric_type=metric_type,
                value=rate,
                protocol=protocol,
                optimal_range=self._performance_targets.get(metric_type),
                unit="msg/s",
            )
            self._metrics[metric_type].append(metric)
            self._collection_stats["metrics_collected"] += 1

        # Reset counters after collection
        self.reset_protocol_counters()

    async def _collect_system_resources(self) -> None:
        """Collect system resource metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_metric = PerformanceMetric(
                metric_type=MetricType.CPU_USAGE,
                value=cpu_percent,
                optimal_range=self._performance_targets.get(MetricType.CPU_USAGE),
                unit="%",
            )
            self._metrics[MetricType.CPU_USAGE].append(cpu_metric)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_metric = PerformanceMetric(
                metric_type=MetricType.MEMORY_USAGE,
                value=memory.percent,
                optimal_range=self._performance_targets.get(MetricType.MEMORY_USAGE),
                unit="%",
                metadata={"memory_mb": memory.used / (1024 * 1024)},
            )
            self._metrics[MetricType.MEMORY_USAGE].append(memory_metric)

            self._collection_stats["metrics_collected"] += 2

        except Exception as e:
            logger.error(f"Error collecting system resources: {e}")

    async def _collect_can_interface_metrics(self) -> None:
        """Collect CAN interface metrics."""
        try:
            # This would typically interface with actual CAN interfaces
            # For now, simulate basic metrics

            interfaces = ["can0", "can1", "vcan0"]  # Common CAN interface names

            for interface in interfaces:
                # Simulate CAN bus load (would come from actual interface stats)
                # This would be replaced with real CAN interface monitoring
                load_percent = 25.0  # Placeholder

                metric = PerformanceMetric(
                    metric_type=MetricType.CAN_BUS_LOAD,
                    value=load_percent,
                    interface=interface,
                    optimal_range=self._performance_targets.get(MetricType.CAN_BUS_LOAD),
                    unit="%",
                )
                self._metrics[MetricType.CAN_BUS_LOAD].append(metric)
                self._collection_stats["metrics_collected"] += 1

        except Exception as e:
            logger.error(f"Error collecting CAN interface metrics: {e}")
