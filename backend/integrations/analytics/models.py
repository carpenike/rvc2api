"""
Performance Analytics Data Models

Pydantic models for performance analytics data structures following
the established patterns from diagnostics and other modules.
"""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ProtocolType(str, Enum):
    """Supported protocol types for performance analytics."""

    RVC = "rvc"
    J1939 = "j1939"
    FIREFLY = "firefly"
    SPARTAN_K2 = "spartan_k2"
    UNKNOWN = "unknown"


class OptimizationLevel(str, Enum):
    """Optimization recommendation levels."""

    IMMEDIATE = "immediate"  # Apply immediately - safe optimizations
    SCHEDULED = "scheduled"  # Schedule during maintenance window
    MANUAL = "manual"  # Requires manual review and approval
    INFORMATIONAL = "informational"  # For information only


class AlertSeverity(str, Enum):
    """Performance alert severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ResourceType(str, Enum):
    """System resource types for monitoring."""

    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    CAN_INTERFACE = "can_interface"


class MetricType(str, Enum):
    """Performance metric types."""

    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    NETWORK_USAGE = "network_usage"
    CAN_UTILIZATION = "can_utilization"
    MESSAGE_RATE = "message_rate"
    PROCESSING_TIME = "processing_time"
    QUEUE_SIZE = "queue_size"


class TrendDirection(str, Enum):
    """Trend direction classifications."""

    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"
    VOLATILE = "volatile"


class PerformanceMetric(BaseModel):
    """Individual performance metric measurement."""

    timestamp: float = Field(description="Measurement timestamp")
    protocol: ProtocolType = Field(description="Protocol this metric applies to")
    metric_type: MetricType = Field(description="Type of metric")
    value: float = Field(description="Metric value")
    labels: dict[str, str] = Field(default={}, description="Additional metric labels")
    source: str = Field(description="Source of the metric")

    class Config:
        use_enum_values = True


@dataclass
class TelemetryDataPoint:
    """Individual telemetry data point with timestamp."""

    timestamp: float
    protocol: ProtocolType
    metric_name: str
    value: float
    labels: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "timestamp": self.timestamp,
            "protocol": self.protocol.value,
            "metric_name": self.metric_name,
            "value": self.value,
            "labels": self.labels,
        }


class PerformanceBaseline(BaseModel):
    """Performance baseline for anomaly detection."""

    protocol: ProtocolType = Field(description="Protocol this baseline applies to")
    metric_name: str = Field(description="Name of the performance metric")
    mean_value: float = Field(description="Mean baseline value")
    std_deviation: float = Field(description="Standard deviation of baseline")
    min_value: float = Field(description="Minimum observed value")
    max_value: float = Field(description="Maximum observed value")
    percentile_95: float = Field(description="95th percentile value")
    percentile_99: float = Field(description="99th percentile value")
    sample_count: int = Field(description="Number of samples used for baseline", ge=1)
    calculated_at: float = Field(
        default_factory=time.time, description="When baseline was calculated"
    )
    valid_until: float = Field(description="When baseline expires")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence in this baseline")

    def is_expired(self) -> bool:
        """Check if this baseline has expired."""
        return time.time() > self.valid_until

    def is_anomaly(self, value: float, threshold_std_dev: float = 2.0) -> bool:
        """Check if a value is anomalous compared to this baseline."""
        if self.std_deviation == 0:
            return False

        z_score = abs(value - self.mean_value) / self.std_deviation
        return z_score > threshold_std_dev

    def get_deviation_percentage(self, value: float) -> float:
        """Get percentage deviation from baseline mean."""
        if self.mean_value == 0:
            return 0.0

        return ((value - self.mean_value) / self.mean_value) * 100.0


class PerformanceTrend(BaseModel):
    """Performance trend analysis result."""

    metric_type: MetricType = Field(description="Type of metric analyzed")
    protocol: ProtocolType = Field(description="Protocol this trend applies to")
    direction: TrendDirection = Field(description="Direction of the trend")
    slope: float = Field(description="Linear regression slope")
    r_squared: float = Field(ge=0.0, le=1.0, description="R-squared value of trend line")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in trend analysis")
    sample_count: int = Field(ge=1, description="Number of samples analyzed")
    analyzed_at: float = Field(default_factory=time.time, description="When analysis was performed")
    projected_change_24h: float = Field(description="Projected change in next 24 hours")
    projected_change_7d: float = Field(description="Projected change in next 7 days")

    class Config:
        use_enum_values = True


class OptimizationRecommendation(BaseModel):
    """Performance optimization recommendation."""

    id: str = Field(description="Unique recommendation ID")
    protocol: ProtocolType = Field(description="Protocol this recommendation applies to")
    optimization_type: str = Field(description="Type of optimization")
    level: OptimizationLevel = Field(description="Optimization urgency level")
    title: str = Field(description="Short description of the optimization")
    description: str = Field(description="Detailed optimization description")
    expected_improvement: float = Field(
        ge=0.0, le=100.0, description="Expected performance improvement percentage"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in this recommendation")
    implementation_effort: str = Field(description="Effort required to implement")
    impact_area: str = Field(description="Area of system that will be impacted")
    prerequisites: list[str] = Field(default=[], description="Prerequisites for implementation")
    estimated_downtime_minutes: int = Field(
        ge=0, description="Estimated downtime for implementation"
    )
    created_at: float = Field(
        default_factory=time.time, description="When recommendation was created"
    )
    expires_at: float = Field(description="When recommendation expires")
    applied: bool = Field(default=False, description="Whether recommendation has been applied")
    applied_at: float | None = Field(default=None, description="When recommendation was applied")

    def is_expired(self) -> bool:
        """Check if this recommendation has expired."""
        return time.time() > self.expires_at

    def can_auto_apply(self) -> bool:
        """Check if this recommendation can be automatically applied."""
        return (
            self.level == OptimizationLevel.IMMEDIATE
            and self.confidence >= 0.9
            and self.estimated_downtime_minutes == 0
            and not self.applied
        )


class PerformanceAlert(BaseModel):
    """Performance alert for anomalies and issues."""

    id: str = Field(description="Unique alert ID")
    protocol: ProtocolType = Field(description="Protocol that triggered the alert")
    alert_type: str = Field(description="Type of alert")
    severity: AlertSeverity = Field(description="Alert severity level")
    title: str = Field(description="Short alert title")
    message: str = Field(description="Detailed alert message")
    metric_name: str = Field(description="Metric that triggered the alert")
    current_value: float = Field(description="Current metric value")
    baseline_value: float | None = Field(default=None, description="Expected baseline value")
    deviation_percentage: float | None = Field(
        default=None, description="Percentage deviation from baseline"
    )
    triggered_at: float = Field(default_factory=time.time, description="When alert was triggered")
    acknowledged: bool = Field(default=False, description="Whether alert has been acknowledged")
    acknowledged_at: float | None = Field(default=None, description="When alert was acknowledged")
    resolved: bool = Field(default=False, description="Whether alert has been resolved")
    resolved_at: float | None = Field(default=None, description="When alert was resolved")
    metadata: dict[str, Any] = Field(default={}, description="Additional alert metadata")

    def acknowledge(self) -> None:
        """Mark this alert as acknowledged."""
        self.acknowledged = True
        self.acknowledged_at = time.time()

    def resolve(self) -> None:
        """Mark this alert as resolved."""
        self.resolved = True
        self.resolved_at = time.time()


class TrendAnalysis(BaseModel):
    """Statistical trend analysis results."""

    protocol: ProtocolType = Field(description="Protocol analyzed")
    metric_name: str = Field(description="Metric analyzed")
    time_window_hours: int = Field(description="Analysis time window in hours")
    sample_count: int = Field(description="Number of samples analyzed")
    slope: float = Field(description="Trend slope coefficient")
    intercept: float = Field(description="Trend intercept")
    r_squared: float = Field(ge=0.0, le=1.0, description="R-squared correlation coefficient")
    p_value: float = Field(ge=0.0, le=1.0, description="Statistical significance p-value")
    trend_direction: str = Field(description="Trend direction: increasing, decreasing, stable")
    confidence_interval_lower: float = Field(description="Lower bound of confidence interval")
    confidence_interval_upper: float = Field(description="Upper bound of confidence interval")
    forecast_24h: float | None = Field(default=None, description="24-hour forecast value")
    forecast_7d: float | None = Field(default=None, description="7-day forecast value")
    analyzed_at: float = Field(default_factory=time.time, description="When analysis was performed")

    def is_significant(self, threshold: float = 0.05) -> bool:
        """Check if trend is statistically significant."""
        return self.p_value < threshold

    def is_concerning(self, slope_threshold: float = 0.1) -> bool:
        """Check if trend is concerning (steep degradation)."""
        return (
            self.trend_direction == "decreasing"
            and abs(self.slope) > slope_threshold
            and self.is_significant()
        )


class ResourceMetrics(BaseModel):
    """System resource utilization metrics."""

    resource_type: ResourceType = Field(description="Type of resource")
    timestamp: float = Field(default_factory=time.time, description="Measurement timestamp")

    # CPU metrics
    cpu_usage_percent: float | None = Field(
        default=None, ge=0.0, le=100.0, description="CPU usage percentage"
    )
    cpu_load_1m: float | None = Field(default=None, ge=0.0, description="1-minute load average")
    cpu_load_5m: float | None = Field(default=None, ge=0.0, description="5-minute load average")
    cpu_load_15m: float | None = Field(default=None, ge=0.0, description="15-minute load average")

    # Memory metrics
    memory_total_bytes: int | None = Field(default=None, ge=0, description="Total memory in bytes")
    memory_used_bytes: int | None = Field(default=None, ge=0, description="Used memory in bytes")
    memory_available_bytes: int | None = Field(
        default=None, ge=0, description="Available memory in bytes"
    )
    memory_usage_percent: float | None = Field(
        default=None, ge=0.0, le=100.0, description="Memory usage percentage"
    )

    # Disk metrics
    disk_total_bytes: int | None = Field(
        default=None, ge=0, description="Total disk space in bytes"
    )
    disk_used_bytes: int | None = Field(default=None, ge=0, description="Used disk space in bytes")
    disk_available_bytes: int | None = Field(
        default=None, ge=0, description="Available disk space in bytes"
    )
    disk_usage_percent: float | None = Field(
        default=None, ge=0.0, le=100.0, description="Disk usage percentage"
    )

    # Network metrics
    network_bytes_sent: int | None = Field(default=None, ge=0, description="Total bytes sent")
    network_bytes_received: int | None = Field(
        default=None, ge=0, description="Total bytes received"
    )
    network_packets_sent: int | None = Field(default=None, ge=0, description="Total packets sent")
    network_packets_received: int | None = Field(
        default=None, ge=0, description="Total packets received"
    )
    network_errors: int | None = Field(default=None, ge=0, description="Network errors")

    # CAN interface metrics
    can_interface_name: str | None = Field(default=None, description="CAN interface name")
    can_utilization_percent: float | None = Field(
        default=None, ge=0.0, le=100.0, description="CAN utilization percentage"
    )
    can_messages_per_second: float | None = Field(
        default=None, ge=0.0, description="CAN messages per second"
    )
    can_errors_per_second: float | None = Field(
        default=None, ge=0.0, description="CAN errors per second"
    )
    can_queue_depth: int | None = Field(default=None, ge=0, description="CAN queue depth")


class PerformanceSnapshot(BaseModel):
    """Complete performance snapshot at a point in time."""

    timestamp: float = Field(default_factory=time.time, description="Snapshot timestamp")
    protocols: dict[str, dict[str, float]] = Field(
        default={}, description="Protocol-specific performance metrics"
    )
    resources: ResourceMetrics = Field(description="System resource metrics")
    active_alerts: list[PerformanceAlert] = Field(
        default=[], description="Active performance alerts"
    )
    recent_optimizations: list[OptimizationRecommendation] = Field(
        default=[], description="Recent optimization recommendations"
    )
    system_health_score: float = Field(ge=0.0, le=1.0, description="Overall system health score")

    def get_protocol_health(self, protocol: ProtocolType) -> float:
        """Get health score for a specific protocol."""
        protocol_data = self.protocols.get(protocol.value, {})
        if not protocol_data:
            return 1.0  # Unknown protocols assumed healthy

        # Simple health calculation based on error rates and latency
        error_rate = protocol_data.get("error_rate", 0.0)
        latency_ms = protocol_data.get("avg_latency_ms", 0.0)

        # Lower is better for both metrics
        error_score = max(0.0, 1.0 - (error_rate / 10.0))  # 10% error rate = 0 health
        latency_score = max(0.0, 1.0 - (latency_ms / 1000.0))  # 1000ms latency = 0 health

        return (error_score + latency_score) / 2.0
