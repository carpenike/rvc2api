"""
Advanced Diagnostics Configuration

Pydantic-based configuration for the advanced diagnostics system with
environment variable support following project patterns.
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class AdvancedDiagnosticsSettings(BaseSettings):
    """Advanced diagnostics configuration settings."""

    # Core feature settings
    enabled: bool = Field(default=False, description="Enable advanced diagnostics processing")

    # DTC Processing Settings
    enable_dtc_processing: bool = Field(
        default=True, description="Enable diagnostic trouble code processing across all protocols"
    )

    enable_fault_correlation: bool = Field(
        default=True, description="Enable fault correlation analysis across systems"
    )

    enable_predictive_maintenance: bool = Field(
        default=True, description="Enable predictive maintenance analysis"
    )

    # Processing Parameters
    correlation_time_window_seconds: float = Field(
        default=60.0,
        description="Time window for fault correlation analysis (seconds)",
        ge=1.0,
        le=3600.0,
    )

    dtc_retention_days: int = Field(
        default=90, description="Number of days to retain historical DTC data", ge=1, le=365
    )

    health_assessment_interval_seconds: float = Field(
        default=300.0,
        description="Interval for system health assessment (seconds)",
        ge=30.0,
        le=3600.0,
    )

    # Predictive Maintenance Settings
    prediction_confidence_threshold: float = Field(
        default=0.7,
        description="Minimum confidence threshold for maintenance predictions",
        ge=0.0,
        le=1.0,
    )

    performance_history_days: int = Field(
        default=30, description="Number of days of performance history to analyze", ge=1, le=365
    )

    trend_analysis_minimum_samples: int = Field(
        default=10,
        description="Minimum number of data points required for trend analysis",
        ge=3,
        le=1000,
    )

    # Severity Thresholds
    critical_dtc_codes: list[int] = Field(
        default=[], description="List of DTC codes that should always be classified as critical"
    )

    high_priority_systems: list[str] = Field(
        default=["engine", "brakes", "steering", "safety"],
        description="Systems that should be prioritized in diagnostics",
    )

    # Integration Settings
    enable_cross_protocol_analysis: bool = Field(
        default=True, description="Enable analysis across multiple protocols (RV-C, J1939, etc.)"
    )

    enable_manufacturer_specific_analysis: bool = Field(
        default=True,
        description="Enable manufacturer-specific diagnostic analysis (Firefly, Spartan, etc.)",
    )

    enable_real_time_alerts: bool = Field(
        default=True, description="Enable real-time diagnostic alerts"
    )

    # Performance Settings
    max_concurrent_analyses: int = Field(
        default=5, description="Maximum number of concurrent diagnostic analyses", ge=1, le=20
    )

    analysis_batch_size: int = Field(
        default=100, description="Batch size for processing diagnostic data", ge=10, le=1000
    )

    memory_limit_mb: int = Field(
        default=50, description="Memory limit for diagnostic data caching (MB)", ge=10, le=500
    )

    # Export and Integration
    enable_export_integration: bool = Field(
        default=False, description="Enable integration with external diagnostic systems"
    )

    export_format: str = Field(
        default="json", description="Format for diagnostic data export (json, csv, xml)"
    )

    enable_maintenance_scheduling: bool = Field(
        default=False, description="Enable integration with maintenance scheduling systems"
    )

    # Logging and Monitoring
    enable_diagnostic_logging: bool = Field(
        default=True, description="Enable detailed diagnostic processing logging"
    )

    log_level: str = Field(default="INFO", description="Logging level for diagnostic operations")

    enable_performance_monitoring: bool = Field(
        default=True, description="Enable performance monitoring of diagnostic operations"
    )

    class Config:
        """Pydantic configuration."""

        env_prefix = "COACHIQ_ADVANCED_DIAGNOSTICS__"
        case_sensitive = False
        extra = "forbid"
