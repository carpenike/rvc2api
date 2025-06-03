"""
Application configuration settings module.

This module defines Pydantic settings models for configuration management,
with environment variable integration and typed configuration options.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings


class LoggingSettings(BaseModel):
    """Logging configuration settings."""

    level: str = Field(default="INFO")
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_to_file: bool = False
    log_file: Path | None = None


class CANBusSettings(BaseModel):
    """CAN bus configuration settings."""

    bustype: str = Field(default="socketcan")
    channels: list[str] = Field(default=["vcan0"])
    bitrate: int = Field(default=500000)

    @field_validator("channels", mode="before")
    @classmethod
    def parse_channels(cls, v):
        """Parse comma-separated channels from environment variable."""
        if isinstance(v, str):
            return [channel.strip() for channel in v.split(",")]
        return v


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
    rvc_spec_path: Path | None = Field(default=None, alias="RVC_SPEC_PATH")
    rvc_coach_mapping_path: Path | None = Field(default=None, alias="RVC_COACH_MAPPING_PATH")
    static_dir: Path = Path("static")

    # CAN bus settings
    canbus: CANBusSettings = Field(default_factory=CANBusSettings)

    # CAN bus environment variable overrides
    can_channels: str | None = Field(default=None, alias="CAN_CHANNELS")
    can_bustype: str | None = Field(default=None, alias="CAN_BUSTYPE")
    can_bitrate: int | None = Field(default=None, alias="CAN_BITRATE")

    # Logging environment variable overrides
    log_level: str | None = Field(default=None, alias="LOG_LEVEL")

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

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "env_nested_delimiter": "__",
        "extra": "ignore",  # Allow extra fields without validation errors
    }

    # Example: FEATURES__ENABLE_MAINTENANCE_TRACKING=1

    @model_validator(mode="after")
    def setup_derived_settings(self) -> "Settings":
        """
        Set up settings that depend on other settings.

        Returns:
            Updated settings instance
        """
        # Configure maintenance settings if feature is enabled
        if self.features and self.features.enable_maintenance_tracking and not self.maintenance:
            self.maintenance = MaintenanceSettings()

        # Override CAN bus settings from environment variables
        canbus_overrides = {}
        if self.can_channels is not None:
            canbus_overrides["channels"] = [
                channel.strip() for channel in self.can_channels.split(",")
            ]
        if self.can_bustype is not None:
            canbus_overrides["bustype"] = self.can_bustype
        if self.can_bitrate is not None:
            canbus_overrides["bitrate"] = self.can_bitrate

        if canbus_overrides:
            # Create new CANBusSettings with overrides
            current_canbus = self.canbus.model_dump()
            current_canbus.update(canbus_overrides)
            self.canbus = CANBusSettings(**current_canbus)

        # Override logging settings from environment variables
        if self.log_level is not None:
            # Create new LoggingSettings with override
            current_logging = self.logging.model_dump()
            current_logging["level"] = self.log_level
            self.logging = LoggingSettings(**current_logging)

        return self


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
