"""
Application configuration settings module.

This module defines Pydantic settings models for configuration management,
with environment variable integration and typed configuration options.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field, root_validator
from pydantic_settings import BaseSettings


class LoggingSettings(BaseModel):
    """Logging configuration settings."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_to_file: bool = False
    log_file: Path | None = None


class CANBusSettings(BaseModel):
    """CAN bus configuration settings."""

    bustype: str = "socketcan"
    channels: list[str] = ["vcan0"]
    bitrate: int = 250000


class MaintenanceSettings(BaseModel):
    """Maintenance tracking configuration settings."""

    check_interval: int = 3600  # Check for due items every hour
    notification_threshold_days: int = 7  # Notify X days before due
    database_path: Path | None = None


class FeatureFlags(BaseModel):
    """Feature flag configuration."""

    enable_maintenance_tracking: bool = False
    enable_notifications: bool = False
    enable_uptimerobot: bool = False
    enable_pushover: bool = False
    enable_vector_search: bool = True


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    This class provides typed configuration options with default values.
    Values can be overridden using environment variables.
    """

    # App metadata
    app_name: str = "rvc2api"
    app_version: str = "0.0.0"
    app_description: str = "API for RV-C CANbus"

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    root_path: str = ""

    # File paths
    can_spec_path: Path | None = None
    can_map_path: Path | None = None
    static_dir: Path = Path("static")

    # CAN bus settings
    canbus: CANBusSettings = Field(default_factory=CANBusSettings)

    # Feature flags
    features: FeatureFlags = Field(default_factory=FeatureFlags)

    # Logging
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    # Maintenance settings
    maintenance: MaintenanceSettings | None = None

    # Notification settings
    pushover_user_key: str | None = None
    pushover_api_token: str | None = None

    # UptimeRobot settings
    uptimerobot_api_key: str | None = None

    # CORS settings
    cors_origins: list[str] = ["*"]

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"

        # Example: FEATURES__ENABLE_MAINTENANCE_TRACKING=1

    @root_validator(pre=False)
    def setup_derived_settings(self, values: dict) -> dict:
        """
        Set up settings that depend on other settings.

        Args:
            values: Current settings values

        Returns:
            Updated settings values
        """
        # Configure maintenance settings if feature is enabled
        if (
            values.get("features")
            and values["features"].enable_maintenance_tracking
            and not values.get("maintenance")
        ):
            values["maintenance"] = MaintenanceSettings()

        return values


# Create cached singleton settings instance
@lru_cache
def get_settings() -> Settings:
    """
    Get application settings singleton.

    This function is cached to avoid parsing environment variables
    multiple times.

    Returns:
        Settings instance
    """
    return Settings()
