"""
Persistence Service

Manages data persistence, backup operations, and directory structure for CoachIQ.
Provides centralized storage management for SQLite databases, backups, themes,
custom dashboards, and other user-configurable data.
"""

import asyncio
import json
import logging
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from backend.core.config import PersistenceSettings, get_persistence_settings
from backend.models.persistence import (
    BackupInfo,
    BackupSettings,
    DirectoryInfo,
    DiskUsageInfo,
    StorageInfo,
)
from backend.services.database_manager import DatabaseManager
from backend.services.repositories import ConfigRepository, DashboardRepository

logger = logging.getLogger(__name__)


class PersistenceService:
    """
    Service for managing persistent data storage and backup operations.

    Features:
    - Directory structure management
    - Database backup and restore
    - Configuration file persistence
    - Theme and dashboard storage
    - Automated cleanup and retention policies
    """

    def __init__(self, settings: PersistenceSettings | None = None):
        """
        Initialize the persistence service.

        Args:
            settings: Persistence configuration settings. If None, loads from config.
        """
        self._settings = settings or get_persistence_settings()
        self._initialized = False

        # Initialize database components
        self._db_manager: DatabaseManager | None = None
        self._config_repository: ConfigRepository | None = None
        self._dashboard_repository: DashboardRepository | None = None

        # Track created directories for logging
        self._created_directories: list[Path] = []

    @property
    def settings(self) -> PersistenceSettings:
        """Get persistence settings."""
        return self._settings

    @property
    def enabled(self) -> bool:
        """Check if persistence is enabled."""
        # MANDATORY PERSISTENCE: Always enabled in new architecture
        return True

    @property
    def data_dir(self) -> Path:
        """Get the base data directory."""
        return self._settings.data_dir

    @property
    def database_manager(self) -> DatabaseManager | None:
        """Get the database manager."""
        return self._db_manager

    @property
    def config_repository(self) -> ConfigRepository | None:
        """Get the configuration repository."""
        return self._config_repository

    @property
    def dashboard_repository(self) -> DashboardRepository | None:
        """Get the dashboard repository."""
        return self._dashboard_repository

    def set_database_manager(self, db_manager: DatabaseManager) -> None:
        """Set the database manager."""
        self._db_manager = db_manager

    async def initialize(self) -> bool:
        """
        Initialize the persistence service.

        Creates required directories, initializes database components,
        and performs startup checks.

        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized:
            return True

        if not self.enabled:
            logger.info("Persistence service disabled, skipping initialization")
            self._initialized = True
            return True

        try:
            # Ensure all required directories exist
            self._created_directories = self._settings.ensure_directories()

            if self._created_directories:
                logger.info(
                    f"Created persistence directories: {[str(d) for d in self._created_directories]}"
                )

            # Verify directory permissions
            await self._verify_permissions()

            # Initialize database components
            await self._initialize_database_components()

            # Clean up old backups if enabled
            if self._settings.backup_enabled:
                await self._cleanup_old_backups()

            self._initialized = True
            logger.info(f"Persistence service initialized with data directory: {self.data_dir}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize persistence service: {e}")
            return False

    async def _initialize_database_components(self) -> None:
        """Initialize the database manager and repositories."""
        try:
            # Initialize database manager with appropriate configuration
            from backend.services.database_engine import DatabaseSettings

            database_settings = DatabaseSettings()

            # Check if persistence is enabled
            if self.enabled:
                database_settings.sqlite_path = str(await self.get_database_path("coachiq"))
            else:
                # In null backend mode, set sqlite_path to ":null:" to trigger null backend
                database_settings.sqlite_path = ":null:"

            self._db_manager = DatabaseManager(database_settings)
            await self._db_manager.initialize()

            # Initialize repositories (they will handle null backend mode internally)
            self._config_repository = ConfigRepository(self._db_manager)
            self._dashboard_repository = DashboardRepository(self._db_manager)

            if self.enabled:
                logger.info("Database components initialized with persistent storage")
            else:
                logger.info("Database components initialized in memory-only mode (null backend)")

        except Exception as e:
            logger.error(f"Failed to initialize database components: {e}")
            raise

    async def get_configuration(self, key: str, namespace: str = "default") -> str | None:
        """
        Get a configuration value from the database.

        Args:
            key: Configuration key
            namespace: Configuration namespace (defaults to "default")

        Returns:
            Configuration value if found, None otherwise
        """
        if not self._config_repository:
            return None
        return await self._config_repository.get(namespace, key)

    async def set_configuration(self, key: str, value: str, namespace: str = "default") -> bool:
        """
        Set a configuration value in the database.

        Args:
            key: Configuration key
            value: Configuration value
            namespace: Configuration namespace (defaults to "default")

        Returns:
            True if successful, False otherwise
        """
        if not self._config_repository:
            return False
        try:
            return await self._config_repository.set(namespace, key, value)
        except Exception as e:
            logger.error(f"Failed to set configuration {key}: {e}")
            return False

    async def get_dashboard_config(self, dashboard_id: str | None = None) -> dict[str, Any] | None:
        """
        Get dashboard configuration from the database.

        Args:
            dashboard_id: Dashboard ID, defaults to 'default'

        Returns:
            Dashboard configuration if found, None otherwise
        """
        if not self._dashboard_repository:
            return None

        dashboard_id = dashboard_id or "default"
        try:
            # Try to get by name first, then by ID if it's numeric
            dashboard = await self._dashboard_repository.get_by_name(dashboard_id)
            if not dashboard and dashboard_id.isdigit():
                dashboard = await self._dashboard_repository.get_by_id(int(dashboard_id))
            return dashboard
        except Exception as e:
            logger.error(f"Failed to get dashboard config {dashboard_id}: {e}")
            return None

    async def save_dashboard_config(
        self, config: dict[str, Any], dashboard_id: str | None = None
    ) -> bool:
        """
        Save dashboard configuration to the database.

        Args:
            config: Dashboard configuration
            dashboard_id: Dashboard ID, defaults to 'default'

        Returns:
            True if successful, False otherwise
        """
        if not self._dashboard_repository:
            return False

        dashboard_id = dashboard_id or "default"
        try:
            return await self._dashboard_repository.save_config(dashboard_id, config)
        except Exception as e:
            logger.error(f"Failed to save dashboard config {dashboard_id}: {e}")
            return False

    async def _verify_permissions(self) -> None:
        """Verify that we have read/write permissions to data directories."""
        test_file = self.data_dir / ".permission_test"
        try:
            test_file.write_text("test")
            test_file.unlink()
        except (OSError, PermissionError) as e:
            logger.warning(f"Limited permissions for data directory {self.data_dir}: {e}")

    async def get_database_path(self, database_name: str) -> Path:
        """
        Get the path for a database file.

        Args:
            database_name: Name of the database (without .db extension)

        Returns:
            Path to the database file
        """
        if not database_name.endswith(".db"):
            database_name += ".db"
        return self._settings.get_database_dir() / database_name

    async def backup_database(
        self, database_path: Path, backup_name: str | None = None
    ) -> Path | None:
        """
        Create a backup of a SQLite database.

        Args:
            database_path: Path to the source database
            backup_name: Optional custom backup name. If None, uses timestamp.

        Returns:
            Path to the backup file if successful, None otherwise
        """
        if not self.enabled or not self._settings.backup_enabled:
            return None

        if not database_path.exists():
            logger.warning(f"Database file {database_path} does not exist, cannot backup")
            return None

        try:
            # Generate backup filename
            if backup_name is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{database_path.stem}_{timestamp}.db"
            elif not backup_name.endswith(".db"):
                backup_name += ".db"

            backup_path = self._settings.get_backup_dir() / backup_name

            # Check file size before backup
            file_size_mb = database_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self._settings.max_backup_size_mb:
                logger.warning(
                    f"Database {database_path} size ({file_size_mb:.1f}MB) "
                    f"exceeds backup limit ({self._settings.max_backup_size_mb}MB)"
                )
                return None

            # Perform backup using SQLite backup API for consistency
            await self._backup_sqlite_database(database_path, backup_path)

            logger.info(f"Database backup created: {backup_path}")
            return backup_path

        except Exception as e:
            logger.error(f"Failed to backup database {database_path}: {e}")
            return None

    async def _backup_sqlite_database(self, source_path: Path, backup_path: Path) -> None:
        """
        Backup SQLite database using the backup API for consistency.

        Args:
            source_path: Source database path
            backup_path: Backup destination path
        """

        def backup_db():
            # Use SQLite backup API for hot backup
            source_conn = sqlite3.connect(str(source_path))
            backup_conn = sqlite3.connect(str(backup_path))

            try:
                # Perform the backup
                source_conn.backup(backup_conn)
            finally:
                source_conn.close()
                backup_conn.close()

        # Run backup in thread pool to avoid blocking
        await asyncio.get_event_loop().run_in_executor(None, backup_db)

    async def restore_database(self, backup_path: Path, target_path: Path) -> bool:
        """
        Restore a database from backup.

        Args:
            backup_path: Path to the backup file
            target_path: Path where to restore the database

        Returns:
            True if restore successful, False otherwise
        """
        if not self.enabled:
            return False

        if not backup_path.exists():
            logger.error(f"Backup file {backup_path} does not exist")
            return False

        try:
            # Ensure target directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy backup to target location
            shutil.copy2(backup_path, target_path)

            logger.info(f"Database restored from {backup_path} to {target_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to restore database from {backup_path}: {e}")
            return False

    async def save_user_config(self, config_name: str, config_data: dict[str, Any]) -> bool:
        """
        Save user configuration data.

        Args:
            config_name: Name of the configuration file
            config_data: Configuration data to save

        Returns:
            True if save successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            if not config_name.endswith(".json"):
                config_name += ".json"

            config_path = self._settings.get_config_dir() / config_name

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            logger.debug(f"User config saved: {config_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save user config {config_name}: {e}")
            return False

    async def load_user_config(self, config_name: str) -> dict[str, Any] | None:
        """
        Load user configuration data.

        Args:
            config_name: Name of the configuration file

        Returns:
            Configuration data if successful, None otherwise
        """
        if not self.enabled:
            return None

        try:
            if not config_name.endswith(".json"):
                config_name += ".json"

            config_path = self._settings.get_config_dir() / config_name

            if not config_path.exists():
                return None

            with open(config_path, encoding="utf-8") as f:
                return json.load(f)

        except Exception as e:
            logger.error(f"Failed to load user config {config_name}: {e}")
            return None

    async def list_backups(self, database_name: str | None = None) -> list[BackupInfo]:
        """
        List available database backups.

        Args:
            database_name: Optional filter by database name

        Returns:
            List of BackupInfo objects
        """
        if not self.enabled:
            return []

        try:
            backup_dir = self._settings.get_backup_dir()
            if not backup_dir.exists():
                return []

            backups = []
            pattern = f"{database_name}_*.db" if database_name else "*.db"

            for backup_file in backup_dir.glob(pattern):
                stat = backup_file.stat()

                # Extract database name from backup filename
                db_name = None
                if "_" in backup_file.stem:
                    db_name = backup_file.stem.split("_")[0] + ".db"

                backups.append(
                    BackupInfo(
                        name=backup_file.name,
                        path=str(backup_file),
                        size_mb=stat.st_size / (1024 * 1024),
                        created=datetime.fromtimestamp(stat.st_ctime),
                        modified=datetime.fromtimestamp(stat.st_mtime),
                        database_name=db_name,
                    )
                )

            # Sort by creation time, newest first
            backups.sort(key=lambda x: x.created, reverse=True)
            return backups

        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return []

    async def delete_backup(self, backup_name: str) -> bool:
        """
        Delete a specific backup file.

        Args:
            backup_name: Name of the backup file to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            backup_dir = self._settings.get_backup_dir()
            backup_path = backup_dir / backup_name

            if not backup_path.exists():
                logger.warning(f"Backup file {backup_name} not found")
                return False

            if not backup_path.is_file():
                logger.warning(f"Backup path {backup_name} is not a file")
                return False

            backup_path.unlink()
            logger.info(f"Successfully deleted backup: {backup_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete backup {backup_name}: {e}")
            return False

    async def _cleanup_old_backups(self) -> None:
        """Clean up old backup files based on retention policy."""
        if not self._settings.backup_enabled:
            return

        try:
            backup_dir = self._settings.get_backup_dir()
            if not backup_dir.exists():
                return

            cutoff_date = datetime.now() - timedelta(days=self._settings.backup_retention_days)
            deleted_count = 0

            for backup_file in backup_dir.glob("*.db"):
                if backup_file.stat().st_mtime < cutoff_date.timestamp():
                    try:
                        backup_file.unlink()
                        deleted_count += 1
                    except OSError as e:
                        logger.warning(f"Failed to delete old backup {backup_file}: {e}")

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old backup files")

        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")

    async def get_storage_info(self) -> StorageInfo:
        """
        Get storage information and statistics.

        Returns:
            StorageInfo model with storage statistics
        """
        if not self.enabled:
            return StorageInfo(
                enabled=False,
                data_dir=None,
                directories=None,
                disk_usage=None,
                backup_settings=None,
                error="Persistence service not enabled",
            )

        try:
            data_dir = self.data_dir

            # Calculate directory sizes
            def get_dir_size(path: Path) -> int:
                """Get total size of directory in bytes."""
                if not path.exists():
                    return 0
                return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())

            def get_file_count(path: Path) -> int:
                """Get total number of files in directory."""
                if not path.exists():
                    return 0
                return sum(1 for f in path.rglob("*") if f.is_file())

            # Get available disk space
            stat = shutil.disk_usage(data_dir)

            # Create directory info objects
            db_dir = self._settings.get_database_dir()
            backup_dir = self._settings.get_backup_dir()
            config_dir = self._settings.get_config_dir()
            logs_dir = self._settings.get_logs_dir()

            directories = {
                "database": DirectoryInfo(
                    path=str(db_dir),
                    size_mb=get_dir_size(db_dir) / (1024 * 1024),
                    file_count=get_file_count(db_dir),
                    exists=db_dir.exists(),
                ),
                "backups": DirectoryInfo(
                    path=str(backup_dir),
                    size_mb=get_dir_size(backup_dir) / (1024 * 1024),
                    file_count=get_file_count(backup_dir),
                    exists=backup_dir.exists(),
                ),
                "config": DirectoryInfo(
                    path=str(config_dir),
                    size_mb=get_dir_size(config_dir) / (1024 * 1024),
                    file_count=get_file_count(config_dir),
                    exists=config_dir.exists(),
                ),
                "logs": DirectoryInfo(
                    path=str(logs_dir),
                    size_mb=get_dir_size(logs_dir) / (1024 * 1024),
                    file_count=get_file_count(logs_dir),
                    exists=logs_dir.exists(),
                ),
            }

            disk_usage = DiskUsageInfo(
                total_gb=stat.total / (1024 * 1024 * 1024),
                used_gb=(stat.total - stat.free) / (1024 * 1024 * 1024),
                free_gb=stat.free / (1024 * 1024 * 1024),
                usage_percent=((stat.total - stat.free) / stat.total) * 100,
            )

            backup_settings = BackupSettings(
                enabled=self._settings.backup_enabled,
                retention_days=self._settings.backup_retention_days,
                max_size_mb=self._settings.max_backup_size_mb,
            )

            return StorageInfo(
                enabled=True,
                data_dir=str(data_dir),
                directories=directories,
                disk_usage=disk_usage,
                backup_settings=backup_settings,
                error=None,
            )

        except Exception as e:
            logger.error(f"Failed to get storage info: {e}")
            return StorageInfo(
                enabled=True,
                data_dir=None,
                directories=None,
                disk_usage=None,
                backup_settings=None,
                error=str(e),
            )

    async def shutdown(self) -> None:
        """Clean shutdown of the persistence service."""
        if not self._initialized:
            return

        logger.info("Shutting down persistence service")

        # Shutdown database components
        if self._db_manager:
            try:
                # Close any open sessions/connections
                logger.debug("Shutting down database manager")
                # Note: DatabaseManager doesn't have an explicit shutdown method yet
                # but this is where we'd call it
                self._db_manager = None
                self._config_repository = None
                self._dashboard_repository = None
            except Exception as e:
                logger.warning(f"Error during database shutdown: {e}")

        # Perform final backup cleanup if enabled
        if self.enabled and self._settings.backup_enabled:
            await self._cleanup_old_backups()

        self._initialized = False
