"""
CoachIQ Configuration Management

This module provides centralized configuration management for the CoachIQ application
using Pydantic Settings.

Environment Variable Patterns:
- For top-level settings: `COACHIQ_SETTING` (e.g., `COACHIQ_APP_NAME`)
- For nested settings: `COACHIQ_SECTION__SETTING` (e.g., `COACHIQ_SERVER__HOST`)

The loading order for configuration values is:
1. Default values specified in the Settings classes
2. Values from .env file (if present)
3. Environment variables (which override any previous values)

All settings are strongly typed and validated using Pydantic.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerSettings(BaseSettings):
    """
    Server configuration settings.

    Environment Variables:
        All settings can be configured with the prefix COACHIQ_SERVER__
        For example: COACHIQ_SERVER__HOST=0.0.0.0
    """

    model_config = SettingsConfigDict(env_prefix="COACHIQ_SERVER__", case_sensitive=False)

    host: str = Field(default="127.0.0.1", description="Server host address")
    port: int = Field(default=8000, description="Server port", ge=1, le=65535)
    reload: bool = Field(default=False, description="Enable auto-reload in development")
    workers: int = Field(default=1, description="Number of worker processes", ge=1, le=32)
    access_log: bool = Field(default=True, description="Enable access logging")
    debug: bool = Field(default=False, description="Enable server debug mode")
    root_path: str = Field(default="", description="Root path for the application")

    # Advanced server settings
    keep_alive_timeout: int = Field(default=5, description="Keep-alive timeout in seconds")
    timeout_graceful_shutdown: int = Field(default=30, description="Graceful shutdown timeout")
    limit_concurrency: int | None = Field(
        default=None, description="Maximum number of concurrent connections"
    )
    limit_max_requests: int | None = Field(
        default=None, description="Maximum number of requests before worker restart"
    )
    timeout_notify: int = Field(default=30, description="Timeout for worker startup notification")
    worker_class: str = Field(
        default="uvicorn.workers.UvicornWorker", description="Worker class to use"
    )
    worker_connections: int = Field(
        default=1000, description="Maximum number of simultaneous clients"
    )
    server_header: bool = Field(default=True, description="Include server header in responses")
    date_header: bool = Field(default=True, description="Include date header in responses")

    # SSL/TLS settings
    ssl_keyfile: Path | None = Field(default=None, description="SSL private key file path")
    ssl_certfile: Path | None = Field(default=None, description="SSL certificate file path")
    ssl_ca_certs: Path | None = Field(default=None, description="SSL CA certificates file path")
    ssl_cert_reqs: int = Field(
        default=0,
        description="SSL certificate verification mode (0=CERT_NONE, 1=CERT_OPTIONAL, 2=CERT_REQUIRED)",
    )

    @field_validator("ssl_keyfile", "ssl_certfile", "ssl_ca_certs", mode="before")
    @classmethod
    def parse_ssl_path(cls, v):
        """Parse SSL file paths from strings."""
        if isinstance(v, str) and v.strip():
            return Path(v.strip())
        return v


class CORSSettings(BaseSettings):
    """
    CORS configuration settings.

    Environment Variables:
        All settings can be configured with the prefix COACHIQ_CORS__
        For example: COACHIQ_CORS__ALLOW_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

    Notes:
        - Comma-separated strings will be parsed into lists automatically
        - Use empty string or omit the variable to use defaults
    """

    model_config = SettingsConfigDict(
        env_prefix="COACHIQ_CORS__",
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

    model_config = SettingsConfigDict(env_prefix="COACHIQ_SECURITY__", case_sensitive=False)

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

    model_config = SettingsConfigDict(env_prefix="COACHIQ_LOGGING__", case_sensitive=False)

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

    model_config = SettingsConfigDict(env_prefix="COACHIQ_CAN__", case_sensitive=False)

    interface: str = Field(
        default="can0", description="CAN interface name (deprecated, use interfaces)"
    )
    interfaces: list[str] = Field(default=["can0"], description="CAN interface names")
    bustype: str = Field(default="socketcan", description="CAN bus type")
    bitrate: int = Field(default=250000, description="CAN bus bitrate")
    timeout: float = Field(default=1.0, description="CAN timeout in seconds", gt=0)
    buffer_size: int = Field(default=1000, description="Message buffer size", ge=1)
    auto_reconnect: bool = Field(default=True, description="Auto-reconnect on CAN failure")
    filters: list[str] = Field(default=[], description="CAN message filters")

    @field_validator("interfaces", mode="before")
    @classmethod
    def parse_interfaces(cls, v):
        """Parse comma-separated interfaces from environment variable."""
        if isinstance(v, str):
            return [f.strip() for f in v.split(",") if f.strip()]
        return v

    @field_validator("filters", mode="before")
    @classmethod
    def parse_filters(cls, v):
        """Parse comma-separated filters from environment variable."""
        if isinstance(v, str):
            return [f.strip() for f in v.split(",") if f.strip()]
        return v

    @property
    def all_interfaces(self) -> list[str]:
        """Get all CAN interfaces, supporting both old and new configuration."""
        # If interfaces is explicitly set to non-default, use it
        if self.interfaces != ["can0"]:
            return self.interfaces
        # Otherwise, if interface (singular) is set to non-default, use it
        if self.interface != "can0":
            return [self.interface]
        # Use interfaces default
        return self.interfaces


class FeaturesSettings(BaseSettings):
    """Feature flags configuration."""

    model_config = SettingsConfigDict(env_prefix="COACHIQ_FEATURES__", case_sensitive=False)

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
    """
    Main application settings.

    Environment Variable Patterns:
        - Top-level settings: COACHIQ_SETTING (e.g., `COACHIQ_APP_NAME`)
        - Nested settings: COACHIQ_SECTION__SETTING (e.g., `COACHIQ_SERVER__HOST`)

    Configuration Loading Order:
        1. Default values specified in this class
        2. Values from .env file (if present)
        3. Environment variables (which override any previous values)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="COACHIQ_",
        case_sensitive=False,
        env_nested_delimiter="__",
        env_parse_none_str="",
        # Disable explode_env_vars to prevent automatic JSON parsing of nested fields
        # This allows nested BaseSettings classes to handle their own environment variables
        explode_env_vars=False,
        extra="ignore",
    )

    # Application info
    app_name: str = Field(default="CoachIQ", description="Application name")
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

    def get_uvicorn_ssl_config(self) -> dict[str, Any]:
        """
        Get SSL/TLS configuration dict for Uvicorn server.

        Returns SSL configuration if SSL certificates are provided,
        otherwise returns empty dict for HTTP mode.
        """
        ssl_config = {}

        # Only add SSL config if both keyfile and certfile are provided
        if self.server.ssl_keyfile and self.server.ssl_certfile:
            ssl_config["ssl_keyfile"] = str(self.server.ssl_keyfile)
            ssl_config["ssl_certfile"] = str(self.server.ssl_certfile)

            # Optional SSL settings
            if self.server.ssl_ca_certs:
                ssl_config["ssl_ca_certs"] = str(self.server.ssl_ca_certs)

            # SSL certificate verification mode
            # 0 = CERT_NONE, 1 = CERT_OPTIONAL, 2 = CERT_REQUIRED
            ssl_config["ssl_cert_reqs"] = self.server.ssl_cert_reqs

        return ssl_config


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance. Uses lru_cache to ensure settings are only loaded once.

    For development or testing scenarios where you need to reload settings,
    you can access the uncached settings with `Settings()` directly.

    Returns:
        Settings instance
    """
    return Settings()


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


def get_features_settings() -> FeaturesSettings:
    """Get features settings."""
    return get_settings().features


# Create a global settings instance
settings = get_settings()
