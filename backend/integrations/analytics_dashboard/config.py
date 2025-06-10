"""
Analytics Dashboard Configuration

Configuration settings for the analytics dashboard system following
the established Pydantic patterns with environment variable support.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AnalyticsDashboardSettings(BaseSettings):
    """
    Analytics dashboard configuration settings.

    Environment Variables:
        All settings can be configured with the prefix COACHIQ_ANALYTICS__
        For example: COACHIQ_ANALYTICS__ENABLED=true
    """

    model_config = SettingsConfigDict(env_prefix="COACHIQ_ANALYTICS__", case_sensitive=False)

    # Core feature configuration
    enabled: bool = Field(default=True, description="Enable analytics dashboard")

    # Core settings (always available, no persistence required)
    memory_retention_hours: int = Field(
        default=2,
        description="Hours to retain analytics data in memory",
        ge=1,
        le=24,
    )
    insight_generation_interval_seconds: int = Field(
        default=900,
        description="Interval for generating system insights in seconds",
        ge=60,
        le=3600,
    )
    pattern_analysis_interval_seconds: int = Field(
        default=1800,
        description="Interval for pattern analysis in seconds",
        ge=300,
        le=7200,
    )
    max_memory_insights: int = Field(
        default=100,
        description="Maximum number of insights to keep in memory",
        ge=10,
        le=1000,
    )
    max_memory_patterns: int = Field(
        default=50,
        description="Maximum number of patterns to keep in memory",
        ge=5,
        le=500,
    )

    # Persistence settings (only used if persistence feature enabled)
    persistence_retention_days: int = Field(
        default=30,
        description="Days to retain data in SQLite when persistence is enabled",
        ge=1,
        le=365,
    )
    enable_background_persistence: bool = Field(
        default=True,
        description="Enable background tasks for data persistence",
    )
    sqlite_batch_size: int = Field(
        default=100,
        description="Batch size for SQLite operations",
        ge=1,
        le=1000,
    )
    db_path: str = Field(
        default="data/analytics.db",
        description="Path to SQLite database file when persistence is enabled",
    )

    # Background processing settings
    enable_background_cleanup: bool = Field(
        default=True,
        description="Enable automatic cleanup of old data",
    )
    cleanup_interval_seconds: int = Field(
        default=3600,
        description="Interval for cleanup operations in seconds",
        ge=300,
        le=86400,
    )
