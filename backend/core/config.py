"""
RVC2API Configuration Management

This module provides centralized configuration management for the RVC2API application
using Pydantic Settings with comprehensive environment variable support.

Environment variables follow the pattern: RVC2API_<SECTION>__<SETTING>
For backward compatibility, legacy environment variables are also supported.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerSettings(BaseSettings):
    """Server configuration settings."""

    model_config = SettingsConfigDict(env_prefix="RVC2API_SERVER__", case_sensitive=False)

    host: str = Field(default="127.0.0.1", description="Server host address")
    port: int = Field(default=8000, description="Server port", ge=1, le=65535)
    reload: bool = Field(default=False, description="Enable auto-reload in development")
    workers: int = Field(default=1, description="Number of worker processes", ge=1, le=32)
    access_log: bool = Field(default=True, description="Enable access logging")
    debug: bool = Field(default=False, description="Enable server debug mode")
    root_path: str = Field(default="", description="Root path for the application")

    # Uvicorn-specific settings
    keep_alive_timeout: int = Field(default=5, description="Keep alive timeout in seconds", ge=1)
    timeout_keep_alive: int = Field(default=5, description="Timeout keep alive in seconds", ge=1)
    timeout_graceful_shutdown: int = Field(
        default=30, description="Graceful shutdown timeout", ge=1
    )
    timeout_notify: int = Field(default=30, description="Timeout notify in seconds", ge=1)

    # Performance settings
    limit_concurrency: int | None = Field(default=None, description="Limit concurrency")
    limit_max_requests: int | None = Field(default=None, description="Limit max requests")

    # SSL/TLS settings
    ssl_keyfile: str | None = Field(default=None, description="SSL key file path")
    ssl_certfile: str | None = Field(default=None, description="SSL certificate file path")
    ssl_ca_certs: str | None = Field(default=None, description="SSL CA certificates file path")
    ssl_cert_reqs: int = Field(default=0, description="SSL certificate requirements level")

    # Worker settings
    worker_class: str = Field(default="uvicorn.workers.UvicornWorker", description="Worker class")
    worker_connections: int = Field(default=1000, description="Worker connections", ge=1)

    # Server headers
    server_header: bool = Field(default=True, description="Include server header")
    date_header: bool = Field(default=True, description="Include date header")


class CORSSettings(BaseSettings):
    """CORS configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="RVC2API_CORS__",
        case_sensitive=False,
        # Disable JSON parsing for list fields to allow custom parsing
        env_parse_none_str="",
        env_parse_enums=True,
    )

    enabled: bool = Field(default=True, description="Enable CORS middleware")
    allow_origins: str | list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed origins for CORS (comma-separated string or list)",
    )
    allow_credentials: bool = Field(default=True, description="Allow credentials in CORS")
    allow_methods: str | list[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="Allowed HTTP methods (comma-separated string or list)",
    )
    allow_headers: str | list[str] = Field(
        default=["*"], description="Allowed headers (comma-separated string or list)"
    )

    @field_validator("allow_origins", mode="before")
    @classmethod
    def parse_origins(cls, v):
        """Parse comma-separated origins from environment variable."""
        if isinstance(v, str):
            # Handle comma-separated format
            v = v.strip()
            if not v:
                return []
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return v
        return v

    @field_validator("allow_methods", mode="before")
    @classmethod
    def parse_methods(cls, v):
        """Parse comma-separated methods from environment variable."""
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            return [method.strip().upper() for method in v.split(",") if method.strip()]
        elif isinstance(v, list):
            return [method.strip().upper() for method in v if method.strip()]
        return v

    @field_validator("allow_headers", mode="before")
    @classmethod
    def parse_headers(cls, v):
        """Parse comma-separated headers from environment variable."""
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            return [header.strip() for header in v.split(",") if header.strip()]
        elif isinstance(v, list):
            return v
        return v


class SecuritySettings(BaseSettings):
    """Security configuration settings."""

    model_config = SettingsConfigDict(env_prefix="RVC2API_SECURITY__", case_sensitive=False)

    secret_key: SecretStr = Field(
        default=SecretStr("your-secret-key-change-in-production"),
        description="Secret key for session management",
    )
    api_key: SecretStr | None = Field(default=None, description="API key for authentication")
    allowed_ips: list[str] = Field(default=[], description="Allowed IP addresses")
    rate_limit_enabled: bool = Field(default=False, description="Enable rate limiting")
    rate_limit_requests: int = Field(default=100, description="Rate limit requests per minute")

    @field_validator("allowed_ips", mode="before")
    @classmethod
    def parse_ips(cls, v):
        """Parse comma-separated IP addresses from environment variable."""
        if isinstance(v, str):
            return [ip.strip() for ip in v.split(",") if ip.strip()]
        return v


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""

    model_config = SettingsConfigDict(env_prefix="RVC2API_LOGGING__", case_sensitive=False)

    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string",
    )
    file: Path | None = Field(default=None, description="Log file path")
    log_to_file: bool = Field(default=False, description="Enable logging to file")
    log_file: Path | None = Field(default=None, description="Log file path (alias for file)")
    colorize: bool = Field(default=True, description="Enable colored logging output")
    max_bytes: int = Field(default=10485760, description="Maximum log file size in bytes")
    backup_count: int = Field(default=5, description="Number of backup log files")

    @field_validator("level", mode="before")
    @classmethod
    def validate_level(cls, v):
        """Validate logging level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if isinstance(v, str):
            v = v.upper()
            if v not in valid_levels:
                raise ValueError(f"Invalid logging level: {v}. Must be one of {valid_levels}")
        return v

    @field_validator("file", mode="before")
    @classmethod
    def parse_file_path(cls, v):
        """Parse file path from string."""
        if isinstance(v, str) and v.strip():
            return Path(v.strip())
        return v


class CANSettings(BaseSettings):
    """CAN bus configuration settings."""

    model_config = SettingsConfigDict(env_prefix="RVC2API_CAN__", case_sensitive=False)

    interface: str = Field(default="vcan0", description="CAN interface name")
    bustype: str = Field(default="socketcan", description="CAN bus type")
    bitrate: int = Field(default=250000, description="CAN bus bitrate")
    timeout: float = Field(default=1.0, description="CAN timeout in seconds", gt=0)
    buffer_size: int = Field(default=1000, description="Message buffer size", ge=1)
    auto_reconnect: bool = Field(default=True, description="Auto-reconnect on CAN failure")
    filters: list[str] = Field(default=[], description="CAN message filters")

    @field_validator("filters", mode="before")
    @classmethod
    def parse_filters(cls, v):
        """Parse comma-separated filters from environment variable."""
        if isinstance(v, str):
            return [f.strip() for f in v.split(",") if f.strip()]
        return v


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    model_config = SettingsConfigDict(env_prefix="RVC2API_DATABASE__", case_sensitive=False)

    url: str = Field(default="sqlite:///./rvc2api.db", description="Database URL")
    echo: bool = Field(default=False, description="Enable SQL query logging")
    pool_size: int = Field(default=5, description="Database connection pool size", ge=1)
    max_overflow: int = Field(default=10, description="Maximum overflow connections", ge=0)


class WebSocketSettings(BaseSettings):
    """WebSocket configuration settings."""

    model_config = SettingsConfigDict(env_prefix="RVC2API_WEBSOCKET__", case_sensitive=False)

    enabled: bool = Field(default=True, description="Enable WebSocket server")
    max_connections: int = Field(
        default=100, description="Maximum concurrent WebSocket connections"
    )
    ping_interval: int = Field(default=20, description="WebSocket ping interval in seconds")
    ping_timeout: int = Field(default=10, description="WebSocket ping timeout in seconds")
    heartbeat_interval: int = Field(default=30, description="Heartbeat interval in seconds", ge=1)


class MaintenanceSettings(BaseSettings):
    """Maintenance tracking configuration."""

    model_config = SettingsConfigDict(env_prefix="RVC2API_MAINTENANCE__", case_sensitive=False)

    check_interval: int = Field(default=3600, description="Check interval in seconds", ge=60)
    notification_threshold_days: int = Field(
        default=7, description="Notification threshold in days", ge=1
    )
    database_path: Path | None = Field(default=None, description="Maintenance database path")

    @field_validator("database_path", mode="before")
    @classmethod
    def parse_database_path(cls, v):
        """Parse path from string."""
        if isinstance(v, str) and v.strip():
            return Path(v.strip())
        return v


class NotificationsSettings(BaseSettings):
    """Notification services configuration."""

    model_config = SettingsConfigDict(env_prefix="RVC2API_NOTIFICATIONS__", case_sensitive=False)

    # Pushover settings
    pushover_user_key: SecretStr | None = Field(default=None, description="Pushover user key")
    pushover_api_token: SecretStr | None = Field(default=None, description="Pushover API token")
    pushover_device: str | None = Field(default=None, description="Pushover device name")
    pushover_priority: int = Field(default=0, description="Pushover priority level", ge=-2, le=2)

    # UptimeRobot settings
    uptimerobot_api_key: SecretStr | None = Field(default=None, description="UptimeRobot API key")


class FeaturesSettings(BaseSettings):
    """Feature flags configuration."""

    model_config = SettingsConfigDict(env_prefix="RVC2API_FEATURES__", case_sensitive=False)

    enable_maintenance_tracking: bool = Field(
        default=False, description="Enable maintenance tracking"
    )
    enable_notifications: bool = Field(default=False, description="Enable notifications")
    enable_vector_search: bool = Field(default=True, description="Enable vector search feature")
    enable_uptimerobot: bool = Field(default=False, description="Enable UptimeRobot integration")
    enable_pushover: bool = Field(default=False, description="Enable Pushover notifications")
    enable_api_docs: bool = Field(default=True, description="Enable API documentation")
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    message_queue_size: int = Field(default=1000, description="Message queue size", ge=1)


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="RVC2API_",
        case_sensitive=False,
        env_nested_delimiter="__",
        extra="ignore",
    )

    # Application info
    app_name: str = Field(default="RVC2API", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    app_description: str = Field(
        default="API for RV-C CANbus", description="Application description"
    )
    app_title: str = Field(default="RV-C API", description="API title for documentation")

    # Environment and deployment
    environment: str = Field(default="development", description="Application environment")
    debug: bool = Field(default=False, description="Enable debug mode")
    testing: bool = Field(default=False, description="Enable testing mode")

    # File paths and directories
    static_dir: str = Field(default="static", description="Static files directory")

    # RVC-specific paths
    rvc_spec_path: Path | None = Field(default=None, description="Path to RVC spec JSON file")
    rvc_coach_mapping_path: Path | None = Field(
        default=None, description="Path to RVC coach mapping YAML file"
    )

    # External integrations
    github_update_repo: str | None = Field(
        default=None, description="GitHub repository for update checks (owner/repo)"
    )
    controller_source_addr: str = Field(default="0xF9", description="Controller source address")

    # Nested settings
    server: ServerSettings = Field(default_factory=ServerSettings)
    cors: CORSSettings = Field(default_factory=CORSSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    can: CANSettings = Field(default_factory=CANSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    websocket: WebSocketSettings = Field(default_factory=WebSocketSettings)
    maintenance: MaintenanceSettings = Field(default_factory=MaintenanceSettings)
    notifications: NotificationsSettings = Field(default_factory=NotificationsSettings)
    features: FeaturesSettings = Field(default_factory=FeaturesSettings)

    @field_validator("environment", mode="before")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment name."""
        valid_envs = {"development", "testing", "staging", "production"}
        if isinstance(v, str) and v.lower() not in valid_envs:
            raise ValueError(f"Invalid environment: {v}. Must be one of {valid_envs}")
        return v.lower() if isinstance(v, str) else v

    @field_validator("rvc_spec_path", "rvc_coach_mapping_path", mode="before")
    @classmethod
    def parse_path(cls, v):
        """Parse path from string."""
        if isinstance(v, str) and v.strip():
            return Path(v.strip())
        return v

    def get_config_dict(self, hide_secrets: bool = True) -> dict[str, Any]:
        """
        Get configuration as dictionary with optional secret hiding.

        Args:
            hide_secrets: If True, replace sensitive values with '***'

        Returns:
            Dictionary representation of configuration
        """
        config = self.model_dump()

        if hide_secrets and "security" in config:
            # Hide sensitive values
            for key in ["secret_key", "api_key"]:
                if key in config["security"] and config["security"][key]:
                    config["security"][key] = "***"

        return config

    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"

    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.testing or self.environment == "testing"

    def get_uvicorn_config(self) -> dict[str, Any]:
        """Get configuration dict for Uvicorn server."""
        config = {
            "host": self.server.host,
            "port": self.server.port,
            "reload": self.server.reload and self.is_development(),
            "workers": 1 if self.server.reload else self.server.workers,
            "access_log": self.server.access_log,
            "log_level": self.logging.level.lower(),
        }

        # Don't use reload in production
        if self.is_production():
            config["reload"] = False

        return config

    @classmethod
    def create_with_legacy_support(cls) -> "Settings":
        """
        Create settings instance with legacy environment variable support.

        This method handles backward compatibility with old environment variable names.
        """
        # Legacy mappings: old_var -> new_var
        legacy_mappings = {
            # Server settings
            "HOST": "RVC2API_SERVER__HOST",
            "PORT": "RVC2API_SERVER__PORT",
            "RELOAD": "RVC2API_SERVER__RELOAD",
            "WORKERS": "RVC2API_SERVER__WORKERS",
            "RVC2API_HOST": "RVC2API_SERVER__HOST",
            "RVC2API_PORT": "RVC2API_SERVER__PORT",
            # Logging settings
            "LOG_LEVEL": "RVC2API_LOGGING__LEVEL",
            # CAN settings (both CAN_ and CANBUS_ prefixes for compatibility)
            "CAN_INTERFACE": "RVC2API_CAN__INTERFACE",
            "CAN_BITRATE": "RVC2API_CAN__BITRATE",
            "CAN_CHANNELS": "RVC2API_CAN__INTERFACE",  # Map to interface for simplicity
            "CAN_BUSTYPE": "RVC2API_CAN__BUSTYPE",
            # Security settings
            "SECRET_KEY": "RVC2API_SECURITY__SECRET_KEY",
            "API_KEY": "RVC2API_SECURITY__API_KEY",
            # Application settings
            "DEBUG": "RVC2API_DEBUG",
            "ENVIRONMENT": "RVC2API_ENVIRONMENT",
            # Database settings
            "DATABASE_URL": "RVC2API_DATABASE__URL",
            # CORS settings
            "CORS_ORIGINS": "RVC2API_CORS__ALLOW_ORIGINS",
            # Notification settings (legacy)
            "PUSHOVER_USER_KEY": "RVC2API_NOTIFICATIONS__PUSHOVER_USER_KEY",
            "PUSHOVER_API_TOKEN": "RVC2API_NOTIFICATIONS__PUSHOVER_API_TOKEN",
            "UPTIMEROBOT_API_KEY": "RVC2API_NOTIFICATIONS__UPTIMEROBOT_API_KEY",
            # OpenAI API Key for vector search
            "OPENAI_API_KEY": "OPENAI_API_KEY",  # Keep as-is, commonly used directly
        }

        # Apply legacy mappings if new variables don't exist
        for old_var, new_var in legacy_mappings.items():
            if old_var in os.environ and new_var not in os.environ:
                os.environ[new_var] = os.environ[old_var]

        return cls()


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance with legacy support.

    Returns:
        Settings instance
    """
    return Settings.create_with_legacy_support()


# Convenience functions for getting specific setting sections
def get_server_settings() -> ServerSettings:
    """Get server settings."""
    return get_settings().server


def get_cors_settings() -> CORSSettings:
    """Get CORS settings."""
    return get_settings().cors


def get_security_settings() -> SecuritySettings:
    """Get security settings."""
    return get_settings().security


def get_logging_settings() -> LoggingSettings:
    """Get logging settings."""
    return get_settings().logging


def get_can_settings() -> CANSettings:
    """Get CAN settings."""
    return get_settings().can


def get_database_settings() -> DatabaseSettings:
    """Get database settings."""
    return get_settings().database


def get_websocket_settings() -> WebSocketSettings:
    """Get WebSocket settings."""
    return get_settings().websocket


def get_maintenance_settings() -> MaintenanceSettings:
    """Get maintenance settings."""
    return get_settings().maintenance


def get_notifications_settings() -> NotificationsSettings:
    """Get notifications settings."""
    return get_settings().notifications


def get_features_settings() -> FeaturesSettings:
    """Get features settings."""
    return get_settings().features


# Create a global settings instance
settings = get_settings()
