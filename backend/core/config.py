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
from importlib import resources
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

    @field_validator("root_path", mode="before")
    @classmethod
    def parse_root_path(cls, v):
        """Handle None values for root_path."""
        if v is None:
            return ""
        return v

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
        env_parse_none_str="",
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
    """CAN bus configuration settings with interface mapping."""

    model_config = SettingsConfigDict(
        env_prefix="COACHIQ_CAN__", case_sensitive=False, env_parse_none_str=""
    )

    interface: str = Field(
        default="can0", description="CAN interface name (deprecated, use interfaces)"
    )
    interfaces: Any = Field(default=["can0"], description="CAN interface names")
    bustype: str = Field(default="socketcan", description="CAN bus type")
    bitrate: int = Field(default=500000, description="CAN bus bitrate")
    timeout: float = Field(default=1.0, description="CAN timeout in seconds", gt=0)
    buffer_size: int = Field(default=1000, description="Message buffer size", ge=1)
    auto_reconnect: bool = Field(default=True, description="Auto-reconnect on CAN failure")
    filters: Any = Field(default=[], description="CAN message filters")

    # New interface mapping - stored as Any to avoid auto-JSON parsing, validated to dict
    interface_mappings: Any = Field(
        default={"house": "can0", "chassis": "can1"},
        description="Logical to physical interface mapping",
        json_schema_extra={
            "examples": [
                {"house": "can0", "chassis": "can1"},
                "house:can0,chassis:can1",
                "house=can0,chassis=can1",
            ]
        },
    )

    @field_validator("interfaces", mode="before")
    @classmethod
    def parse_interfaces(cls, v) -> list[str]:
        """Parse comma-separated interfaces from environment variable."""
        if isinstance(v, str):
            return [f.strip() for f in v.split(",") if f.strip()]
        elif isinstance(v, list):
            return v
        # Return default if unable to parse
        return ["can0"]

    @field_validator("filters", mode="before")
    @classmethod
    def parse_filters(cls, v) -> list[str]:
        """Parse comma-separated filters from environment variable."""
        if isinstance(v, str):
            return [f.strip() for f in v.split(",") if f.strip()]
        elif isinstance(v, list):
            return v
        # Return default if unable to parse
        return []

    @field_validator("interface_mappings", mode="before")
    @classmethod
    def parse_interface_mappings(cls, v) -> dict[str, str]:
        """
        Parse interface mappings from environment variable or dict.

        Supports multiple formats:
        - Dictionary: {"house": "can0", "chassis": "can1"} (primary format)
        - JSON string: '{"house": "can0", "chassis": "can1"}' (from NixOS)
        - Colon-separated: "house:can0,chassis:can1" (fallback)
        - Equals-separated: "house=can0,chassis=can1" (fallback)

        Examples:
            COACHIQ_CAN__INTERFACE_MAPPINGS='{"house": "can0", "chassis": "can1"}'
            COACHIQ_CAN__INTERFACE_MAPPINGS="house:can0,chassis:can1"
            COACHIQ_CAN__INTERFACE_MAPPINGS="house=can0,chassis=can1"
        """
        if isinstance(v, str):
            # First try to parse as JSON (primary format from NixOS)
            import json

            try:
                parsed = json.loads(v)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass

            # Fallback to string parsing for manual configuration
            mappings = {}
            # Support both : and = as separators
            for pair in v.split(","):
                pair = pair.strip()
                if ":" in pair:
                    logical, physical = pair.split(":", 1)
                elif "=" in pair:
                    logical, physical = pair.split("=", 1)
                else:
                    continue  # Skip invalid pairs

                logical = logical.strip()
                physical = physical.strip()

                if logical and physical:
                    mappings[logical] = physical

            return mappings
        elif isinstance(v, dict):
            return v
        # Return default value if unable to parse
        return {"house": "can0", "chassis": "can1"}

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


class RVCSettings(BaseSettings):
    """RV-C configuration settings."""

    model_config = SettingsConfigDict(env_prefix="COACHIQ_RVC__", case_sensitive=False)

    config_dir: Path | None = Field(
        default=None, description="RVC configuration directory override"
    )
    spec_path: Path | None = Field(default=None, description="Path to RVC spec JSON file override")
    coach_mapping_path: Path | None = Field(
        default=None, description="Path to RVC coach mapping YAML file override"
    )
    coach_model: str | None = Field(
        default=None, description="Coach model to use for mapping selection"
    )

    @field_validator("config_dir", "spec_path", "coach_mapping_path", mode="before")
    @classmethod
    def parse_path(cls, v):
        """Parse path from string."""
        if isinstance(v, str) and v.strip():
            return Path(v.strip())
        return v

    def get_config_dir(self) -> Path:
        """Get the RVC configuration directory."""
        if self.config_dir:
            return self.config_dir

        # Search paths in order of preference
        search_paths = [
            # 1. Top-level config directory (for development)
            Path.cwd() / "config",
            # 2. Try to find bundled config files using importlib.resources
            self._get_bundled_config_dir(),
            # 3. System package locations
            Path("/usr/share/coachiq/config"),
            Path("/usr/local/share/coachiq/config"),
            Path("/etc/coachiq"),
        ]

        for path in search_paths:
            if path and path.exists() and path.is_dir():
                return path

        # Default to top-level config
        return Path.cwd() / "config"

    def _get_bundled_config_dir(self) -> Path | None:
        """Try to locate bundled config files using importlib.resources."""
        try:
            # Try to find config files relative to the backend package
            import backend

            backend_pkg = resources.files(backend)

            # Check if config directory exists relative to backend package
            config_candidates = [
                backend_pkg.parent / "config",  # ../config from backend/
                backend_pkg / "config",  # backend/config/
            ]

            for candidate in config_candidates:
                try:
                    if candidate.is_dir() and candidate.joinpath("rvc.json").is_file():
                        return Path(str(candidate))
                except (AttributeError, OSError):
                    continue

        except Exception:
            pass
        return None

    def get_spec_path(self) -> Path:
        """Get the RVC spec JSON file path."""
        if self.spec_path:
            return self.spec_path

        # Try bundled resources first for Nix compatibility
        bundled_path = self._get_bundled_file("rvc.json")
        if bundled_path and bundled_path.exists():
            return bundled_path

        # Fall back to config directory
        config_dir = self.get_config_dir()
        spec_file = config_dir / "rvc.json"
        return spec_file

    def get_coach_mapping_path(self) -> Path:
        """Get the coach mapping YAML file path."""
        if self.coach_mapping_path:
            return self.coach_mapping_path

        # If coach_model is specified, try to find that specific mapping first in bundled resources
        if self.coach_model:
            bundled_model_path = self._get_bundled_file(f"{self.coach_model}.yml")
            if bundled_model_path and bundled_model_path.exists():
                return bundled_model_path

            # Then try in config directory
            config_dir = self.get_config_dir()
            coach_file = config_dir / f"{self.coach_model}.yml"
            if coach_file.exists():
                return coach_file

        # Try bundled default mapping first for Nix compatibility
        bundled_path = self._get_bundled_file("coach_mapping.default.yml")
        if bundled_path and bundled_path.exists():
            return bundled_path

        # Fall back to config directory
        config_dir = self.get_config_dir()
        default_file = config_dir / "coach_mapping.default.yml"
        return default_file

    def _get_bundled_file(self, filename: str) -> Path | None:
        """Try to locate a specific bundled config file using importlib.resources."""
        try:
            # First try to find config files relative to the backend package
            import backend

            backend_pkg = resources.files(backend)

            # Check if file exists relative to backend package
            file_candidates = [
                backend_pkg.parent / "config" / filename,  # ../config/filename from backend/
                backend_pkg / "config" / filename,  # backend/config/filename
            ]

            for candidate in file_candidates:
                try:
                    if candidate.is_file():
                        return Path(str(candidate))
                except (AttributeError, OSError):
                    continue

            # If not found, try using importlib.resources directly for bundled resources
            # This works better in packaged environments like Nix
            try:
                # Try to access as a direct package resource
                config_resource = resources.files("config")
                if config_resource:
                    config_file = config_resource / filename
                    if config_file.is_file():
                        return Path(str(config_file))
            except (ImportError, FileNotFoundError, AttributeError):
                pass

        except Exception:
            pass
        return None


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

    # Enhanced frontend features
    enable_dashboard_aggregation: bool = Field(
        default=True, description="Enable aggregated dashboard endpoints"
    )
    enable_bulk_operations: bool = Field(default=True, description="Enable bulk entity operations")
    enable_system_analytics: bool = Field(
        default=True, description="Enable system analytics and alerting"
    )
    enable_activity_tracking: bool = Field(
        default=True, description="Enable activity feed tracking"
    )

    # Performance and optimization settings
    dashboard_cache_ttl: int = Field(
        default=30, description="Dashboard data cache TTL in seconds", ge=1
    )
    bulk_operation_limit: int = Field(
        default=50, description="Maximum entities per bulk operation", ge=1, le=200
    )
    activity_feed_limit: int = Field(
        default=100, description="Maximum activity feed entries", ge=10, le=1000
    )


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
    rvc: RVCSettings = Field(default_factory=RVCSettings)
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
        # Only allow reload in explicit development mode to prevent file watchers in production
        allow_reload = self.server.reload and self.is_development() and not self.is_production()

        config = {
            "host": self.server.host,
            "port": self.server.port,
            "reload": allow_reload,
            "workers": 1 if allow_reload else self.server.workers,
            "access_log": self.server.access_log,
            "log_level": self.logging.level.lower(),
        }

        # Ensure reload is disabled in any non-development environment
        if not self.is_development() or self.is_production():
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


def get_rvc_settings() -> RVCSettings:
    """Get RVC settings."""
    return get_settings().rvc


def get_features_settings() -> FeaturesSettings:
    """Get features settings."""
    return get_settings().features


# Note: Use get_settings() function instead of a global instance
# to ensure environment variables are read correctly
