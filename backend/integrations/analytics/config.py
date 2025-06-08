"""
Performance Analytics Configuration

Configuration settings for the performance analytics system following
the established Pydantic patterns with environment variable support.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PerformanceAnalyticsSettings(BaseSettings):
    """
    Performance analytics configuration settings.

    Environment Variables:
        All settings can be configured with the prefix COACHIQ_PERFORMANCE_ANALYTICS__
        For example: COACHIQ_PERFORMANCE_ANALYTICS__ENABLED=true
    """

    model_config = SettingsConfigDict(
        env_prefix="COACHIQ_PERFORMANCE_ANALYTICS__", case_sensitive=False
    )

    # Core feature configuration
    enabled: bool = Field(default=False, description="Enable performance analytics processing")

    # Telemetry collection settings
    enable_telemetry_collection: bool = Field(
        default=True, description="Enable real-time telemetry collection from all protocols"
    )
    telemetry_collection_interval_seconds: float = Field(
        default=1.0, description="Interval for telemetry collection in seconds", ge=0.1, le=60.0
    )
    telemetry_buffer_size: int = Field(
        default=10000, description="Maximum number of telemetry samples to buffer", ge=100
    )

    # Benchmarking and baseline settings
    enable_benchmarking: bool = Field(
        default=True, description="Enable performance benchmarking and baseline establishment"
    )
    baseline_calculation_interval_hours: int = Field(
        default=24,
        description="Interval for recalculating performance baselines in hours",
        ge=1,
        le=168,
    )
    baseline_sample_size: int = Field(
        default=10000, description="Number of samples to use for baseline calculation", ge=100
    )
    deviation_threshold_percent: float = Field(
        default=20.0,
        description="Percentage deviation from baseline to trigger alerts",
        ge=1.0,
        le=100.0,
    )

    # Resource monitoring settings
    enable_resource_monitoring: bool = Field(
        default=True, description="Enable system resource utilization monitoring"
    )
    resource_monitoring_interval_seconds: float = Field(
        default=5.0, description="Interval for resource monitoring in seconds", ge=1.0, le=300.0
    )
    cpu_warning_threshold_percent: float = Field(
        default=80.0, description="CPU usage percentage to trigger warnings", ge=10.0, le=100.0
    )
    memory_warning_threshold_percent: float = Field(
        default=85.0, description="Memory usage percentage to trigger warnings", ge=10.0, le=100.0
    )
    disk_warning_threshold_percent: float = Field(
        default=90.0, description="Disk usage percentage to trigger warnings", ge=10.0, le=100.0
    )

    # CAN interface monitoring settings
    enable_can_monitoring: bool = Field(
        default=True, description="Enable CAN interface performance monitoring"
    )
    can_utilization_warning_threshold_percent: float = Field(
        default=75.0, description="CAN interface utilization to trigger warnings", ge=10.0, le=100.0
    )
    can_error_rate_threshold_per_second: float = Field(
        default=10.0, description="CAN error rate per second to trigger warnings", ge=0.1
    )

    # Trend analysis settings
    enable_trend_analysis: bool = Field(
        default=True, description="Enable statistical trend analysis"
    )
    trend_analysis_window_hours: int = Field(
        default=168,
        description="Time window for trend analysis in hours (default: 7 days)",
        ge=1,
        le=8760,
    )
    trend_analysis_min_samples: int = Field(
        default=100, description="Minimum samples required for trend analysis", ge=10
    )
    trend_significance_threshold: float = Field(
        default=0.05,
        description="Statistical significance threshold for trend detection",
        ge=0.001,
        le=0.1,
    )

    # Optimization settings
    enable_optimization_recommendations: bool = Field(
        default=True, description="Enable automated optimization recommendations"
    )
    optimization_confidence_threshold: float = Field(
        default=0.8,
        description="Confidence threshold for optimization recommendations",
        ge=0.1,
        le=1.0,
    )
    auto_apply_optimizations: bool = Field(
        default=False, description="Automatically apply safe optimizations"
    )

    # Protocol-specific settings
    protocol_priorities: dict[str, int] = Field(
        default={"rvc": 1, "j1939": 1, "firefly": 2, "spartan_k2": 1},
        description="Priority levels for protocol monitoring (1=critical, 2=high, 3=normal)",
    )

    # Data retention settings
    metrics_retention_days: int = Field(
        default=30, description="Number of days to retain detailed metrics", ge=1, le=365
    )
    summary_retention_days: int = Field(
        default=365, description="Number of days to retain summary metrics", ge=7, le=3650
    )

    # Alert settings
    enable_alerting: bool = Field(default=True, description="Enable performance alerting")
    alert_cooldown_minutes: int = Field(
        default=15, description="Cooldown period between similar alerts in minutes", ge=1, le=1440
    )
    critical_alert_threshold_multiplier: float = Field(
        default=2.0, description="Multiplier for critical alert thresholds", ge=1.1, le=10.0
    )

    # Performance settings
    max_concurrent_analyses: int = Field(
        default=4, description="Maximum number of concurrent performance analyses", ge=1, le=16
    )
    analysis_timeout_seconds: int = Field(
        default=30, description="Timeout for individual performance analyses", ge=1, le=300
    )

    # Integration settings
    enable_prometheus_export: bool = Field(
        default=True, description="Enable Prometheus metrics export"
    )
    enable_websocket_updates: bool = Field(
        default=True, description="Enable real-time WebSocket updates"
    )
    websocket_update_interval_seconds: float = Field(
        default=2.0, description="Interval for WebSocket performance updates", ge=0.5, le=60.0
    )

    # Debug and development settings
    enable_debug_logging: bool = Field(
        default=False, description="Enable debug logging for performance analytics"
    )
    enable_performance_profiling: bool = Field(
        default=False, description="Enable performance profiling of the analytics system itself"
    )
    export_raw_data: bool = Field(
        default=False, description="Export raw performance data for analysis (development only)"
    )


# Convenience function to get performance analytics settings
def get_performance_analytics_settings() -> PerformanceAnalyticsSettings:
    """Get performance analytics settings instance."""
    return PerformanceAnalyticsSettings()
