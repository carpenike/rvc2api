"""
Persistence Models

Pydantic models for persistence-related data structures including
backup information, storage statistics, and user configuration.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class BackupInfo(BaseModel):
    """
    Information about a database backup file.

    Attributes:
        name: Backup file name
        path: Full path to backup file
        size_mb: Size of backup file in megabytes
        created: Creation timestamp
        modified: Last modification timestamp
        database_name: Name of the source database
    """

    name: str = Field(..., description="Backup file name")
    path: str = Field(..., description="Full path to backup file")
    size_mb: float = Field(..., description="Size of backup file in megabytes", ge=0)
    created: datetime = Field(..., description="Creation timestamp")
    modified: datetime = Field(..., description="Last modification timestamp")
    database_name: str | None = Field(None, description="Name of the source database")


class DirectoryInfo(BaseModel):
    """
    Information about a persistence directory.

    Attributes:
        path: Full path to the directory
        size_mb: Total size of directory contents in megabytes
        file_count: Number of files in the directory
        exists: Whether the directory exists
    """

    path: str = Field(..., description="Full path to the directory")
    size_mb: float = Field(..., description="Total size of directory contents in megabytes", ge=0)
    file_count: int | None = Field(None, description="Number of files in the directory", ge=0)
    exists: bool = Field(..., description="Whether the directory exists")


class DiskUsageInfo(BaseModel):
    """
    Disk usage information for the persistence storage.

    Attributes:
        total_gb: Total disk space in gigabytes
        used_gb: Used disk space in gigabytes
        free_gb: Free disk space in gigabytes
        usage_percent: Percentage of disk space used
    """

    total_gb: float = Field(..., description="Total disk space in gigabytes", ge=0)
    used_gb: float = Field(..., description="Used disk space in gigabytes", ge=0)
    free_gb: float = Field(..., description="Free disk space in gigabytes", ge=0)
    usage_percent: float = Field(..., description="Percentage of disk space used", ge=0, le=100)


class BackupSettings(BaseModel):
    """
    Backup configuration settings.

    Attributes:
        enabled: Whether backups are enabled
        retention_days: Number of days to retain backups
        max_size_mb: Maximum backup file size in megabytes
        automatic: Whether backups are created automatically
    """

    enabled: bool = Field(..., description="Whether backups are enabled")
    retention_days: int = Field(..., description="Number of days to retain backups", ge=1, le=365)
    max_size_mb: int = Field(..., description="Maximum backup file size in megabytes", ge=1)
    automatic: bool = Field(default=True, description="Whether backups are created automatically")


class StorageInfo(BaseModel):
    """
    Complete storage information for the persistence system.

    Attributes:
        enabled: Whether persistence is enabled
        data_dir: Base data directory path
        directories: Information about each persistence directory
        disk_usage: Disk usage statistics
        backup_settings: Backup configuration
        error: Error message if storage info retrieval failed
    """

    enabled: bool = Field(..., description="Whether persistence is enabled")
    data_dir: str | None = Field(None, description="Base data directory path")
    directories: dict[str, DirectoryInfo] | None = Field(
        None, description="Information about each persistence directory"
    )
    disk_usage: DiskUsageInfo | None = Field(None, description="Disk usage statistics")
    backup_settings: BackupSettings | None = Field(None, description="Backup configuration")
    error: str | None = Field(None, description="Error message if storage info retrieval failed")


class UserConfiguration(BaseModel):
    """
    User configuration data for themes, preferences, etc.

    Attributes:
        config_name: Name of the configuration
        data: Configuration data
        created: Creation timestamp
        modified: Last modification timestamp
        version: Configuration version for compatibility
    """

    config_name: str = Field(..., description="Name of the configuration", min_length=1)
    data: dict[str, Any] = Field(..., description="Configuration data")
    created: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    modified: datetime = Field(
        default_factory=datetime.now, description="Last modification timestamp"
    )
    version: str = Field(default="1.0", description="Configuration version for compatibility")

    @field_validator("config_name")
    @classmethod
    def validate_config_name(cls, v: str) -> str:
        """Validate configuration name format."""
        # Remove any path separators for security
        clean_name = v.replace("/", "_").replace("\\", "_").replace("..", "_")
        if clean_name != v:
            msg = "Configuration name contains invalid characters"
            raise ValueError(msg)
        return v


class ThemeConfiguration(UserConfiguration):
    """
    Theme configuration extending user configuration.

    Attributes:
        theme_name: Display name of the theme
        primary_color: Primary theme color
        dark_mode: Whether this is a dark mode theme
        css_variables: CSS custom properties for the theme
    """

    theme_name: str = Field(..., description="Display name of the theme", min_length=1)
    primary_color: str | None = Field(
        None, description="Primary theme color", pattern=r"^#[0-9a-fA-F]{6}$"
    )
    dark_mode: bool = Field(default=False, description="Whether this is a dark mode theme")
    css_variables: dict[str, str] | None = Field(
        None, description="CSS custom properties for the theme"
    )


class DashboardConfiguration(UserConfiguration):
    """
    Dashboard configuration extending user configuration.

    Attributes:
        dashboard_name: Display name of the dashboard
        layout: Dashboard layout configuration
        widgets: Widget configurations
        refresh_interval: Auto-refresh interval in seconds
    """

    dashboard_name: str = Field(..., description="Display name of the dashboard", min_length=1)
    layout: dict[str, Any] = Field(..., description="Dashboard layout configuration")
    widgets: list[dict[str, Any]] = Field(default_factory=list, description="Widget configurations")
    refresh_interval: int | None = Field(
        None, description="Auto-refresh interval in seconds", ge=1, le=3600
    )


class DatabaseBackupRequest(BaseModel):
    """
    Request to create a database backup.

    Attributes:
        database_name: Name of the database to backup
        backup_name: Optional custom backup name
        compress: Whether to compress the backup
    """

    database_name: str = Field(..., description="Name of the database to backup", min_length=1)
    backup_name: str | None = Field(None, description="Optional custom backup name")
    compress: bool = Field(default=False, description="Whether to compress the backup")

    @field_validator("backup_name")
    @classmethod
    def validate_backup_name(cls, v: str | None) -> str | None:
        """Validate backup name format."""
        if v is None:
            return v
        # Remove any path separators for security
        clean_name = v.replace("/", "_").replace("\\", "_").replace("..", "_")
        if clean_name != v:
            msg = "Backup name contains invalid characters"
            raise ValueError(msg)
        return v


class DatabaseRestoreRequest(BaseModel):
    """
    Request to restore a database from backup.

    Attributes:
        backup_path: Path to the backup file
        target_database: Target database name
        overwrite: Whether to overwrite existing database
    """

    backup_path: str = Field(..., description="Path to the backup file", min_length=1)
    target_database: str = Field(..., description="Target database name", min_length=1)
    overwrite: bool = Field(default=False, description="Whether to overwrite existing database")

    @field_validator("backup_path")
    @classmethod
    def validate_backup_path(cls, v: str) -> str:
        """Validate backup path exists and is safe."""
        # Basic path validation - actual existence check happens in service
        if not v.endswith(".db"):
            msg = "Backup path must end with .db extension"
            raise ValueError(msg)
        return v


class PersistenceStatus(BaseModel):
    """
    Overall status of the persistence system.

    Attributes:
        enabled: Whether persistence is enabled
        initialized: Whether persistence service is initialized
        health: Health status (healthy, degraded, failed)
        data_dir: Base data directory path
        storage_info: Storage information
        last_backup: Information about the most recent backup
        errors: List of any errors or warnings
    """

    enabled: bool = Field(..., description="Whether persistence is enabled")
    initialized: bool = Field(..., description="Whether persistence service is initialized")
    health: str = Field(..., description="Health status", pattern=r"^(healthy|degraded|failed)$")
    data_dir: str | None = Field(None, description="Base data directory path")
    storage_info: StorageInfo | None = Field(None, description="Storage information")
    last_backup: BackupInfo | None = Field(
        None, description="Information about the most recent backup"
    )
    errors: list[str] = Field(default_factory=list, description="List of any errors or warnings")
